#!/usr/bin/env python3
"""Emelia sequencer provider — P7: create campaign, push approved, poll stats.

Emelia does the sending job (sequencer, inbox rotation, tracking); this
provider only drives it and keeps the database honest. It writes ONLY the
contract columns of `outreach` (CLAUDE.md): `emelia_campaign_id`,
`sent_at`, `status` (sent → replied), `opened_count`, `replied` — through
db.py, in waves, never row by row.

TWO transports, used where each is PROVEN:
- GraphQL (https://graphql.emelia.io/graphql) — the documented, field-proven
  surface (n8n ships it): createCampaign, duplicateCampaign,
  addContactToCampaignHook (per-contact JSON incl. `custom` variables —
  how our pre-drafted email_1/2/3 travel), startCampaign, all_campaigns
  stats. THE EMAIL LANE OF THE DEMO RUNS ENTIRELY ON THIS.
- REST (https://api.emelia.io) — the newer surface, used for per-contact
  activities (opens/replies) and for ADVANCED (email + LinkedIn)
  campaigns. Advanced payloads are isolated in _REST_PATHS/_push_one; a
  400 surfaces the server's own message verbatim in the receipt so the
  fix is one dict, one morning.

The template trick (zero schema guessing on the critical path): build ONE
campaign in the Emelia UI with the sequence steps — email 1 body `{{email_1}}`
(J0), email 2 `{{email_2}}` (J+3), email 3 `{{email_3}}` (J+7), and for an
advanced template the LinkedIn steps (visit J0, invite J+1 — no note, house
rule) — then save its id as EMELIA_TEMPLATE_ID. Each week `create-campaign`
DUPLICATES it (settings+mails+provider, no contacts) and `push` fills it
with per-contact custom variables. Steps are set once by a human, contacts
and content flow by API forever.

SEED GUARD (hackathon hard rule): `push` refuses any recipient not matching
EMELIA_SEED_INBOXES (comma list of full emails and/or `@domain` suffixes).
Unset/empty → push refuses EVERYTHING and says how to set it. Real sending
after the event: `--no-seed-guard`, explicit, once.

The assumed fallback (auth friction, wifi, anything): `export-csv` writes a
« prêt à importer » CSV of the approved rows (contact fields + the 4 drafts
as custom columns) into the workspace's staging/ — the demo still closes on
a screen-share import.

The P7 loop (driven by /outreach):
    python3 tools/providers/emelia.py test-auth
    python3 tools/providers/emelia.py create-campaign --week 2026-W28
    python3 tools/providers/emelia.py push  --campaign <id> [--week 2026-W28]
    python3 tools/providers/emelia.py start --campaign <id>
    python3 tools/providers/emelia.py stats [--week 2026-W28]   # re-runnable
    python3 tools/providers/emelia.py export-csv [--week 2026-W28]  # fallback

Env (~/.bricks/env, loaded via envfile): EMELIA_API_KEY (Settings → API —
sent as `Authorization: <key>`; on 401 the client retries `Bearer <key>`
once and remembers what worked, so the auth-doc morning risk is absorbed);
EMELIA_TEMPLATE_ID (the UI-built template); EMELIA_SEED_INBOXES;
EMELIA_API_URL / EMELIA_GRAPHQL_URL override endpoints (tests use a stub).

Callable both ways (like every Bricks tool): CLI (JSON receipt on stdout,
errors JSON on stderr + exit 1) or `import emelia; emelia.push(...)`.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

_CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
sys.path.insert(0, os.path.abspath(_CORE))
import envfile  # noqa: E402

envfile.load()  # ~/.bricks/env → EMELIA_API_KEY without shell exports

import db as dbmod  # noqa: E402

DEFAULT_REST_URL = "https://api.emelia.io"
DEFAULT_GRAPHQL_URL = "https://graphql.emelia.io/graphql"
TIMEOUT = 30
HOOK_SLEEP = 0.4          # polite spacing between per-contact hook calls
RETRY_429_SLEEP = 15      # one polite retry per call, then the row fails
_WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")

#: REST paths in ONE place — if a day-J probe shows a different shape,
#: the fix is here and nowhere else.
_REST_PATHS = {
    "advanced_create": "/advanced/campaigns",
    "advanced_add_contact": "/advanced/campaign/contacts",
    "activities": "/campaigns/{id}/activities",
    "advanced_activities": "/advanced/campaigns/{id}/activities",
    "campaigns": "/campaigns",
}

_AUTH_PREFIXES = ("", "Bearer ")   # docs say raw key; self-heal to Bearer
_auth_prefix_cache: str | None = None


class EmeliaError(RuntimeError):
    """Raised on any invalid operation or provider refusal."""


# --------------------------------------------------------------------------
# HTTP plumbing (auth self-heal shared by both transports)
# --------------------------------------------------------------------------

def _key() -> str:
    key = os.environ.get("EMELIA_API_KEY", "").strip()
    if not key:
        raise EmeliaError("EMELIA_API_KEY absent de l'environnement — "
                          "ajoute-la dans ~/.bricks/env (app.emelia.io → "
                          "Settings → API)")
    return key


def _http(url: str, payload: dict | None, headers: dict, method: str) -> tuple[int, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8", "replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        status = exc.code
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, body


def _unauthenticated(status: int, parsed: object) -> bool:
    if status == 401:
        return True
    if isinstance(parsed, dict):        # GraphQL says 400 + UNAUTHENTICATED
        for err in parsed.get("errors") or []:
            code = ((err or {}).get("extensions") or {}).get("code", "")
            if code == "UNAUTHENTICATED" or "logged in" in str((err or {}).get("message", "")):
                return True
    return False


def _call(url: str, payload: dict | None = None, method: str = "GET") -> object:
    """One authenticated call; discovers the working Authorization prefix."""
    global _auth_prefix_cache
    key = _key()
    prefixes = ((_auth_prefix_cache,) if _auth_prefix_cache is not None
                else _AUTH_PREFIXES)
    last: tuple[int, object] = (0, "")
    for prefix in prefixes:
        headers = {"Authorization": f"{prefix}{key}",
                   "Content-Type": "application/json",
                   "User-Agent": "bricks-emelia"}
        for attempt in (1, 2):
            status, parsed = _http(url, payload, headers, method)
            if status == 429 and attempt == 1:      # their limiter — one retry
                time.sleep(RETRY_429_SLEEP)
                continue
            break
        if _unauthenticated(status, parsed):
            last = (status, parsed)
            continue                                 # try the next prefix
        _auth_prefix_cache = prefix
        if status >= 400:
            raise EmeliaError(f"Emelia {method} {url} → HTTP {status}: "
                              f"{json.dumps(parsed, ensure_ascii=False)[:400]}")
        return parsed
    raise EmeliaError(f"authentification refusée (HTTP {last[0]}) — clé "
                      f"EMELIA_API_KEY invalide ? Réponse: "
                      f"{json.dumps(last[1], ensure_ascii=False)[:200]}")


def _gql(query: str, variables: dict) -> dict:
    url = os.environ.get("EMELIA_GRAPHQL_URL", DEFAULT_GRAPHQL_URL)
    parsed = _call(url, {"query": query, "variables": variables}, "POST")
    if not isinstance(parsed, dict):
        raise EmeliaError(f"réponse GraphQL illisible: {str(parsed)[:200]}")
    if parsed.get("errors"):
        msgs = "; ".join(str(e.get("message")) for e in parsed["errors"])
        raise EmeliaError(f"GraphQL: {msgs}")
    return parsed.get("data") or {}


def _rest(path: str, payload: dict | None = None, method: str = "GET") -> object:
    base = os.environ.get("EMELIA_API_URL", DEFAULT_REST_URL).rstrip("/")
    return _call(f"{base}{path}", payload, method)


# --------------------------------------------------------------------------
# Database helpers (function mode — the only door, §4)
# --------------------------------------------------------------------------

def _resolve(db: str | None, root: str | None) -> str:
    return dbmod.resolve(db, root or "bricks")


def _check_week(week: str | None) -> str | None:
    if week and not _WEEK_RE.match(week):
        raise EmeliaError("--week doit ressembler à 2026-W28")
    return week


def _rows(path: str, table: str, where: str, cols: str | None = None) -> list[dict]:
    return dbmod.select(path, table, where=where, cols=cols, limit=-1)["rows"]


def _has_col(path: str, table: str, col: str) -> bool:
    """Columns are dynamic (created on first write) — WHEREs must tolerate
    a column that no writer has created yet."""
    return col in dbmod.schema(path, table)["columns"]


def _contacts_by_id(path: str, ids: list) -> dict[str, dict]:
    if not ids:
        return {}
    id_list = ",".join(str(int(str(i).strip())) for i in ids)
    rows = _rows(path, "contacts", f"_id IN ({id_list})")
    return {str(r["_id"]): r for r in rows}


def _companies_by_id(path: str, ids: list) -> dict[str, dict]:
    clean = sorted({int(str(i).strip()) for i in ids if str(i or "").strip()})
    if not clean:
        return {}
    rows = _rows(path, "companies", f"_id IN ({','.join(map(str, clean))})",
                 cols="_id,name,domain")
    return {str(r["_id"]): r for r in rows}


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").split()
    return (parts[0], " ".join(parts[1:])) if parts else ("", "")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Seed guard — the hackathon hard rule lives HERE, not in prose
# --------------------------------------------------------------------------

def _seed_entries() -> list[str]:
    raw = os.environ.get("EMELIA_SEED_INBOXES", "")
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


def _seed_allowed(email: str, entries: list[str]) -> bool:
    email = (email or "").strip().lower()
    return any(email == e or (e.startswith("@") and email.endswith(e))
               for e in entries)


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------

def test_auth(db: str | None = None, root: str | None = None) -> dict:
    """The morning smoke: which transport authenticates, with which prefix."""
    out: dict = {"graphql": {}, "rest": {}}
    try:
        data = _gql("query all_campaigns { all_campaigns { _id name status } }", {})
        out["graphql"] = {"ok": True,
                          "campaigns": len(data.get("all_campaigns") or [])}
    except EmeliaError as exc:
        out["graphql"] = {"ok": False, "error": str(exc)}
    try:
        _rest(_REST_PATHS["campaigns"])
        out["rest"] = {"ok": True}
    except EmeliaError as exc:
        out["rest"] = {"ok": False, "error": str(exc)}
    out["authPrefix"] = repr(_auth_prefix_cache)
    out["seedInboxes"] = _seed_entries() or "ABSENT — push refusera tout"
    return out


def create_campaign(week: str | None = None, name: str | None = None,
                    channel: str = "email", from_id: str | None = None,
                    db: str | None = None, root: str | None = None) -> dict:
    """Create the week's campaign — duplicate the UI template when one exists."""
    _check_week(week)
    name = name or f"Signal Interceptor {week or _now()[:10]}"
    if channel == "advanced":
        parsed = _rest(_REST_PATHS["advanced_create"], {"name": name}, "POST")
        cid = ""
        if isinstance(parsed, dict):
            cid = str(parsed.get("_id") or parsed.get("id")
                      or (parsed.get("campaign") or {}).get("_id", ""))
        return {"campaign_id": cid, "name": name, "channel": "advanced",
                "raw": parsed if not cid else None,
                "next": "pose les étapes dans l'UI (LinkedIn visit J0 + "
                        "invite J+1 SANS note, emails {{email_1..3}}), puis "
                        "`push --campaign " + (cid or "<id>") + " --channel advanced`"}
    from_id = from_id or os.environ.get("EMELIA_TEMPLATE_ID", "").strip()
    if from_id:
        data = _gql(
            "mutation duplicateCampaign($fromId: ID!, $name: String!, "
            "$copySettings: Boolean!, $copyMails: Boolean!, "
            "$copyContacts: Boolean!, $copyProvider: Boolean!) { "
            "duplicateCampaign(fromId: $fromId name: $name "
            "copySettings: $copySettings copyMails: $copyMails "
            "copyContacts: $copyContacts copyProvider: $copyProvider) }",
            {"fromId": from_id, "name": name, "copySettings": True,
             "copyMails": True, "copyContacts": False, "copyProvider": True})
        cid = data.get("duplicateCampaign")
        if not isinstance(cid, str) or not cid:      # some versions return true
            camps = _gql("query all_campaigns { all_campaigns { _id name } }",
                         {}).get("all_campaigns") or []
            cid = next((c["_id"] for c in camps if c.get("name") == name), "")
        if not cid:
            raise EmeliaError("duplication OK mais id introuvable — liste les "
                              "campagnes dans l'UI et passe --campaign à push")
        return {"campaign_id": cid, "name": name, "channel": "email",
                "from_template": from_id,
                "next": f"push --campaign {cid}"}
    data = _gql("mutation createCampaign($name: String!) { "
                "createCampaign(name: $name) { _id name status } }",
                {"name": name})
    created = data.get("createCampaign") or {}
    return {"campaign_id": created.get("_id", ""), "name": name,
            "channel": "email", "from_template": None,
            "next": "campagne VIERGE : pose les 3 étapes {{email_1}}/"
                    "{{email_2}}/{{email_3}} (J0/+3/+7) dans l'UI UNE fois, "
                    "sauve cet id comme EMELIA_TEMPLATE_ID pour les semaines "
                    "suivantes, puis push"}


def _push_one(campaign: str, contact: dict, advanced: bool) -> None:
    if advanced:
        _rest(_REST_PATHS["advanced_add_contact"],
              {"campaignId": campaign, "contact": contact}, "POST")
        return
    _gql("mutation AddContactToCampaignHook($id: ID!, $contact: JSON!) { "
         "addContactToCampaignHook(id: $id, contact: $contact) }",
         {"id": campaign, "contact": contact})


def push(campaign: str, week: str | None = None, channel: str = "email",
         no_seed_guard: bool = False,
         db: str | None = None, root: str | None = None) -> dict:
    """Push the approved outreach rows into the campaign, then stamp them."""
    if not campaign:
        raise EmeliaError("--campaign requis (l'id retourné par create-campaign)")
    _check_week(week)
    path = _resolve(db, root)
    where = "status='approved'"
    if _has_col(path, "outreach", "emelia_campaign_id"):
        where += " AND (emelia_campaign_id IS NULL OR emelia_campaign_id='')"
    if week:
        where += f" AND week='{week}'"
    queue = _rows(path, "outreach", where)
    if not queue:
        return {"pushed": 0, "note": "aucune ligne approved à pousser "
                                     "(déjà poussées, ou approbation manquante)"}
    contacts = _contacts_by_id(path, [r["contact_id"] for r in queue])
    companies = _companies_by_id(
        path, [c.get("company_id") for c in contacts.values()])

    entries = _seed_entries()
    if not entries and not no_seed_guard:
        raise EmeliaError("EMELIA_SEED_INBOXES absent — règle hackathon : "
                          "uniquement les boîtes seed. Ajoute-la dans "
                          "~/.bricks/env (emails ou @domaines, séparés par "
                          "des virgules), ou --no-seed-guard APRÈS l'événement.")

    pushed, updates, blocked, skipped, failures = [], [], [], [], []
    for row in queue:
        contact = contacts.get(str(row["contact_id"]))
        email = (contact or {}).get("email") or ""
        if not contact or not email.strip():
            skipped.append({"outreach_id": row["_id"],
                            "reason": "contact sans email (enrichir d'abord)"})
            continue
        if not no_seed_guard and not _seed_allowed(email, entries):
            blocked.append({"outreach_id": row["_id"], "email": email})
            continue
        first, last = _split_name(contact.get("full_name") or "")
        company = companies.get(str(contact.get("company_id") or ""), {})
        payload = {
            "email": email.strip(),
            "firstName": first, "lastName": last,
            "company": company.get("name") or "",
            "linkedinUrl": contact.get("linkedin_url") or "",
            "phoneNumber": contact.get("phone") or "",
            "custom": {
                "email_1": row.get("email_1") or "",
                "email_2": row.get("email_2") or "",
                "email_3": row.get("email_3") or "",
                "icebreaker_call": row.get("icebreaker_call") or "",
                "why_now": contact.get("why_now") or "",
            },
        }
        try:
            _push_one(campaign, payload, channel == "advanced")
            pushed.append(email)
            updates.append({"_id": row["_id"], "emelia_campaign_id": campaign,
                            "sent_at": _now(), "status": "sent"})
        except EmeliaError as exc:
            failures.append({"outreach_id": row["_id"], "email": email,
                             "error": str(exc)[:200]})
        time.sleep(HOOK_SLEEP)

    if updates:                                   # ONE wave, never per row
        dbmod.modify(path, "outreach", updates=updates)
    return {"campaign_id": campaign, "pushed": len(updates),
            "blockedBySeedGuard": blocked,        # loud and complete, always
            "skippedNoEmail": skipped[:10],
            "failed": failures[:3],
            "samples": pushed[:3],
            "note": "poussés au séquenceur — `start --campaign " + campaign +
                    "` si la campagne n'est pas déjà RUNNING"}


def start(campaign: str, db: str | None = None, root: str | None = None) -> dict:
    if not campaign:
        raise EmeliaError("--campaign requis")
    _gql("mutation startCampaign($id: ID!) { startCampaign(id: $id) }",
         {"id": campaign})
    return {"campaign_id": campaign, "started": True}


def _walk_activities(parsed: object) -> list[dict]:
    """Accept the shapes a REST activities payload plausibly takes."""
    if isinstance(parsed, list):
        return [a for a in parsed if isinstance(a, dict)]
    if isinstance(parsed, dict):
        for key in ("activities", "data", "events", "results"):
            inner = parsed.get(key)
            if isinstance(inner, (list, dict)):
                found = _walk_activities(inner)
                if found:
                    return found
    return []


def _activity_email(act: dict) -> str:
    contact = act.get("contact")
    if isinstance(contact, dict):
        return str(contact.get("email") or contact.get("mail") or "").lower()
    return str(act.get("email") or "").lower()


def stats(campaign: str | None = None, week: str | None = None,
          db: str | None = None, root: str | None = None) -> dict:
    """Poll opens/replies and write them back — re-runnable, idempotent."""
    _check_week(week)
    path = _resolve(db, root)
    if not _has_col(path, "outreach", "emelia_campaign_id"):
        return {"note": "aucune ligne poussée (colonne emelia_campaign_id "
                        "encore absente) — rien à poller"}
    where = "emelia_campaign_id IS NOT NULL AND emelia_campaign_id!=''"
    if campaign:
        where += f" AND emelia_campaign_id='{campaign}'"
    if week:
        where += f" AND week='{week}'"
    rows = _rows(path, "outreach", where)
    if not rows:
        return {"note": "aucune ligne poussée dans ce périmètre — rien à poller"}
    contacts = _contacts_by_id(path, [r["contact_id"] for r in rows])
    campaign_ids = sorted({r["emelia_campaign_id"] for r in rows})

    # Global stats (documented GraphQL) — the receipt's header numbers.
    aggregates = {}
    try:
        camps = _gql("query all_campaigns { all_campaigns { _id name status "
                     "stats { mailsSent opens repliedPercent bouncedPercent "
                     "progressPercent } } }", {}).get("all_campaigns") or []
        aggregates = {c["_id"]: c for c in camps if c.get("_id") in campaign_ids}
    except EmeliaError as exc:
        aggregates = {"error": str(exc)[:200]}

    # Per-contact events (REST) — email lane first, advanced as fallback.
    opened: dict[str, int] = {}
    replied: dict[str, bool] = {}
    activity_errors = []
    for cid in campaign_ids:
        parsed = None
        for path_key in ("activities", "advanced_activities"):
            try:
                parsed = _rest(_REST_PATHS[path_key].format(id=cid))
                break
            except EmeliaError as exc:
                parsed = None
                err = str(exc)
        if parsed is None:
            activity_errors.append({"campaign": cid, "error": err[:200]})
            continue
        for act in _walk_activities(parsed):
            email = _activity_email(act)
            event = str(act.get("event") or act.get("type") or "").upper()
            if not email or not event:
                continue
            if "OPEN" in event:
                opened[email] = opened.get(email, 0) + 1
            if "REPL" in event:
                replied[email] = True

    updates, to_call = [], []
    for row in rows:
        contact = contacts.get(str(row["contact_id"])) or {}
        email = (contact.get("email") or "").lower()
        if not email:
            continue
        n_open, has_reply = opened.get(email, 0), replied.get(email, False)
        update = {"_id": row["_id"], "opened_count": n_open,
                  "replied": "1" if has_reply else "0"}
        if has_reply:
            update["status"] = "replied"
            to_call.append({"contact": contact.get("full_name") or email,
                            "phone": contact.get("phone") or "(pas de tél)",
                            "reason": "a répondu — stop séquence, appel"})
        elif n_open >= 2:
            to_call.append({"contact": contact.get("full_name") or email,
                            "phone": contact.get("phone") or "(pas de tél)",
                            "reason": f"{n_open} ouvertures sans réponse — "
                                      "bascule file call"})
        updates.append(update)
    if updates:
        dbmod.modify(path, "outreach", updates=updates)
    return {"campaigns": campaign_ids, "aggregates": aggregates,
            "rowsUpdated": len(updates),
            "replied": sum(1 for u in updates if u.get("replied") == "1"),
            "aAppeler": to_call,
            "activityErrors": activity_errors or None}


def export_csv(week: str | None = None, out: str | None = None,
               db: str | None = None, root: str | None = None) -> dict:
    """The assumed fallback: a « prêt à importer » CSV, zero API, zero auth."""
    _check_week(week)
    path = _resolve(db, root)
    where = "status='approved'"
    if week:
        where += f" AND week='{week}'"
    queue = _rows(path, "outreach", where)
    if not queue:
        return {"exported": 0, "note": "aucune ligne approved dans ce périmètre"}
    contacts = _contacts_by_id(path, [r["contact_id"] for r in queue])
    companies = _companies_by_id(
        path, [c.get("company_id") for c in contacts.values()])
    out = out or os.path.join(os.path.dirname(path), "staging",
                              f"emelia_import_{week or 'all'}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    entries = _seed_entries()
    non_seed = []
    fields = ["email", "firstName", "lastName", "company", "linkedinUrl",
              "phoneNumber", "email_1", "email_2", "email_3",
              "icebreaker_call", "why_now"]
    written = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in queue:
            contact = contacts.get(str(row["contact_id"])) or {}
            email = (contact.get("email") or "").strip()
            if not email:
                continue
            if entries and not _seed_allowed(email, entries):
                non_seed.append(email)
            first, last = _split_name(contact.get("full_name") or "")
            company = companies.get(str(contact.get("company_id") or ""), {})
            writer.writerow({
                "email": email, "firstName": first, "lastName": last,
                "company": company.get("name") or "",
                "linkedinUrl": contact.get("linkedin_url") or "",
                "phoneNumber": contact.get("phone") or "",
                "email_1": row.get("email_1") or "",
                "email_2": row.get("email_2") or "",
                "email_3": row.get("email_3") or "",
                "icebreaker_call": row.get("icebreaker_call") or "",
                "why_now": contact.get("why_now") or "",
            })
            written += 1
    return {"exported": written, "out": out,
            "nonSeedWarning": non_seed or None,
            "note": "import manuel : Emelia → campagne → Import CSV ; mappe "
                    "les colonnes custom (email_1..3, icebreaker_call)"}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Emelia sequencer provider (P7).")
    dbflags = argparse.ArgumentParser(add_help=False)
    dbflags.add_argument("--db", default=None)
    dbflags.add_argument("--root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("test-auth", parents=[dbflags],
                   help="smoke du matin : quelle surface authentifie")

    p = sub.add_parser("create-campaign", parents=[dbflags],
                       help="crée (ou duplique depuis EMELIA_TEMPLATE_ID) la campagne")
    p.add_argument("--week", default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--channel", choices=["email", "advanced"], default="email")
    p.add_argument("--from", dest="from_id", default=None,
                   help="id du template à dupliquer (défaut: EMELIA_TEMPLATE_ID)")

    p = sub.add_parser("push", parents=[dbflags],
                       help="pousse les outreach approved → custom vars par contact")
    p.add_argument("--campaign", required=True)
    p.add_argument("--week", default=None)
    p.add_argument("--channel", choices=["email", "advanced"], default="email")
    p.add_argument("--no-seed-guard", action="store_true",
                   help="APRÈS l'événement seulement — désactive la règle boîtes seed")

    p = sub.add_parser("start", parents=[dbflags], help="démarre la campagne")
    p.add_argument("--campaign", required=True)

    p = sub.add_parser("stats", parents=[dbflags],
                       help="poll opens/replies → outreach.opened_count/replied")
    p.add_argument("--campaign", default=None)
    p.add_argument("--week", default=None)

    p = sub.add_parser("export-csv", parents=[dbflags],
                       help="fallback : CSV prêt à importer dans staging/")
    p.add_argument("--week", default=None)
    p.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    try:
        if args.command == "test-auth":
            out = test_auth(args.db, args.root)
        elif args.command == "create-campaign":
            out = create_campaign(args.week, args.name, args.channel,
                                  args.from_id, args.db, args.root)
        elif args.command == "push":
            out = push(args.campaign, args.week, args.channel,
                       args.no_seed_guard, args.db, args.root)
        elif args.command == "start":
            out = start(args.campaign, args.db, args.root)
        elif args.command == "stats":
            out = stats(args.campaign, args.week, args.db, args.root)
        else:
            out = export_csv(args.week, args.out, args.db, args.root)
    except (EmeliaError, dbmod.DbError, urllib.error.URLError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
