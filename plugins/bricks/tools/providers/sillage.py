#!/usr/bin/env python3
"""Sillage provider — surveillance, watchlists, signals, leads (P3/P4).

Pure HTTP against the Sillage public API (OpenAPI: /api/v1/docs/spec, base
https://api.getsillage.com/api, `Authorization: Bearer sk_live_…`). The
INTELLIGENCE lives upstream in /surveil; this tool executes mechanically and
writes ONLY the contract columns (CLAUDE.md, tables gelées) through db.py.

The P3/P4 loop (driven by /surveil):
    python3 tools/providers/sillage.py test-auth            # setup-state compact
    python3 tools/providers/sillage.py setup [--top 20]     # persona + top accounts
    python3 tools/providers/sillage.py watchlist --type competitor [--top 5]
    python3 tools/providers/sillage.py watchlist --type champion [--urls a,b]
    python3 tools/providers/sillage.py agents [--keywords "a,b,c"]
    python3 tools/providers/sillage.py run [--lookback 90] [--no-wait|--force]
    python3 tools/providers/sillage.py pull [--limit 100]   # cursor → state.json
    python3 tools/providers/sillage.py leads
    python3 tools/providers/sillage.py add-signal --json '{…}'   # demo injection

Contract writes (and nothing else):
    companies:   sillage_company_id, tracked='1'           (setup)
    competitors: watched='1', sillage_entity_id            (watchlist competitor)
    contacts:    sillage_lead_id, full_name, position, linkedin_url,
                 company_id (REQUIRED — no match, no row)  (leads)
    signals:     the full contract row; canonical `type` mapped at pull;
                 competitor* raw types arm intercept_status='pending' and
                 leave `type` empty — intercept.py poses competitor_engagement
                 after resolution + qualification.

NOTE leads: Sillage returns email/phoneNumber on leads. The frozen contract
says contacts.email/phone are written by fullenrich.py (P6, budget gate) —
so this tool does NOT write them; receipts count how many were available
(huddle material, Robin arbitrates).

Cross-run state (§8): memory/state.json in the workspace — pull cursor,
signal-run ids, watchlist ids. Never in a table.

Env (~/.bricks/env, loaded via envfile): SILLAGE_API_KEY (sk_live_…);
SILLAGE_API_URL overrides the endpoint (tests use a local stub).

Callable both ways (like every Bricks tool): CLI (JSON receipt on stdout,
errors JSON on stderr + exit 1) or `import sillage; sillage.pull(...)`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

_CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
sys.path.insert(0, os.path.abspath(_CORE))
import envfile  # noqa: E402

envfile.load()  # ~/.bricks/env → SILLAGE_API_KEY without shell exports

import db as dbmod  # noqa: E402

DEFAULT_API_URL = "https://api.getsillage.com/api"
TIMEOUT = 45
RATE_SLEEP = 0.3          # polite spacing between calls (contents fetches…)
RETRY_429_SLEEP = 20      # one polite retry per call, then fail cleanly
RUN_POLL_SLEEP = 6        # signal-run polling
RUN_POLL_MAX = 100        # ≈10 min ceiling before returning "still running"

#: Raw Sillage detection types → canonical contract vocabulary.
#: competitor* is INTENTIONALLY absent: the pull arms intercept_status and
#: intercept.py poses `competitor_engagement` after resolution + qualif.
TYPE_MAP = {
    "newJob": "newJob",
    "recentlyPromoted": "recentlyPromoted",
    "jobPostingKeywordDetection": "jobPosting",
    "keywordDetection": "keywordDetection",
    "championInboundComment": "champion_move",
    "championOutboundComment": "champion_move",
}

_RUN_STAGES_FINAL = {"completed", "completed_partial", "failed"}


class SillageError(RuntimeError):
    """Raised on any invalid operation or provider refusal."""


# --------------------------------------------------------------------------
# HTTP plumbing
# --------------------------------------------------------------------------

def _key() -> str:
    key = os.environ.get("SILLAGE_API_KEY", "").strip()
    if not key:
        raise SillageError("SILLAGE_API_KEY absent de l'environnement — "
                           "ajoute-la dans ~/.bricks/env (clé workspace "
                           "sk_live_… fournie par Sillage)")
    return key


def _call(path: str, payload: dict | None = None, method: str = "GET",
          params: dict | None = None) -> object:
    base = os.environ.get("SILLAGE_API_URL", DEFAULT_API_URL).rstrip("/")
    url = f"{base}{path}"
    if params:
        clean = {k: v for k, v in params.items() if v not in (None, "", [])}
        if clean:
            url += "?" + urllib.parse.urlencode(clean, doseq=True)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {_key()}",
                 "Content-Type": "application/json",
                 "User-Agent": "bricks-sillage"})
    for attempt in (1, 2):
        time.sleep(RATE_SLEEP)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = response.read().decode("utf-8", "replace")
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt == 1:
                time.sleep(RETRY_429_SLEEP)
                continue
            detail = ""
            try:  # RFC 9457 problem document
                problem = json.loads(exc.read().decode("utf-8", "replace"))
                detail = (problem.get("detail") or problem.get("message")
                          or (problem.get("error") or {}).get("message") or "")
            except Exception:
                pass
            raise SillageError(
                f"HTTP {exc.code} sur {method} {path}"
                + (f" — {str(detail)[:200]}" if detail else "")) from None
        except urllib.error.URLError as exc:
            raise SillageError(f"réseau injoignable sur {method} {path} — "
                               f"{exc.reason}") from None


# --------------------------------------------------------------------------
# Database & workspace helpers (function mode — the only door, §4)
# --------------------------------------------------------------------------

def _resolve(db: str | None, root: str | None) -> str:
    return dbmod.resolve(db, root or "bricks")


def _rows(path: str, table: str, where: str | None = None,
          cols: str | None = None, order: str | None = None) -> list[dict]:
    try:
        return dbmod.select(path, table, where=where, cols=cols,
                            order=order, limit=-1)["rows"]
    except dbmod.DbError:
        return []          # table not born yet — columns are dynamic


def _has_col(path: str, table: str, col: str) -> bool:
    try:
        return col in dbmod.schema(path, table)["columns"]
    except dbmod.DbError:
        return False


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _norm_domain(value: str | None) -> str:
    d = (value or "").strip().lower()
    d = re.sub(r"^[a-z]+://", "", d)
    d = d.split("/")[0].split("?")[0]
    return d[4:] if d.startswith("www.") else d


def _norm_linkedin(value: str | None) -> str:
    u = (value or "").strip()
    if not u:
        return ""
    match = re.search(r"linkedin\.com/(in|company)/([^/?#]+)", u, re.I)
    if not match:
        return u.rstrip("/")
    return f"https://www.linkedin.com/{match.group(1).lower()}/{match.group(2)}"


def _state_path(db_path: str) -> str:
    return os.path.join(os.path.dirname(db_path), "memory", "state.json")


def _state_read(db_path: str) -> dict:
    try:
        with open(_state_path(db_path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _state_write(db_path: str, sillage_patch: dict) -> dict:
    state = _state_read(db_path)
    state.setdefault("sillage", {}).update(sillage_patch)
    path = _state_path(db_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    return state["sillage"]


def _context_file(db_path: str, name: str) -> str:
    path = os.path.join(os.path.dirname(db_path), "context", name)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _dig(node: object, *names: str) -> object:
    """Best-effort key lookup anywhere in a nested payload (first hit wins)."""
    wanted = {n.lower() for n in names}
    queue = [node]
    while queue:
        item = queue.pop(0)
        if isinstance(item, dict):
            for k, v in item.items():
                if k.lower() in wanted and v not in (None, "", [], {}):
                    return v
            queue.extend(item.values())
        elif isinstance(item, list):
            queue.extend(item)
    return None


# --------------------------------------------------------------------------
# Persona & keywords from the workspace context
# --------------------------------------------------------------------------

def _icp_buying_titles(db_path: str) -> list[str]:
    """UNION of every title pattern under '## Buying roles' in icp.md —
    ONE persona per workspace (contract), pushed verbatim."""
    text = _context_file(db_path, "icp.md")
    in_section, titles = False, []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.lower().startswith("## buying roles")
            continue
        if not in_section or not stripped.startswith("-"):
            continue
        _, _, value = stripped.lstrip("- ").partition(":")
        value = re.sub(r"\((?:title patterns?|patterns?)\)", "", value, flags=re.I)
        for part in value.split("|"):
            part = part.strip(" .;")
            if part and "TODO" not in part.upper():
                titles.append(part)
    seen, union = set(), []
    for t in titles:
        if t.lower() not in seen:
            seen.add(t.lower())
            union.append(t)
    return union


def _icp_geography(db_path: str) -> list[str]:
    text = _context_file(db_path, "icp.md")
    for line in text.splitlines():
        match = re.match(r"-\s*Geograph\w*\s*:\s*(.+)", line.strip(), re.I)
        if match and "TODO" not in match.group(1).upper():
            return [g.strip() for g in re.split(r"[|,]", match.group(1))
                    if g.strip()]
    return []


def _pain_keywords(db_path: str) -> list[str]:
    """Bullets of '## Problems it solves' in offer.md — the pain vocabulary."""
    text = _context_file(db_path, "offer.md")
    in_section, keywords = False, []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.lower().startswith("## problems")
            continue
        if in_section and stripped.startswith("-"):
            value = stripped.lstrip("- ").strip()
            if value and "TODO" not in value.upper():
                keywords.append(value)
    return keywords


# --------------------------------------------------------------------------
# test-auth
# --------------------------------------------------------------------------

def test_auth(db: str | None = None, root: str | None = None) -> dict:
    state = _call("/v2/setup-state")
    checklist = state.get("checklist") or {}
    return {"ok": True,
            "persona_set": state.get("persona_set"),
            "list_uploaded": state.get("list_uploaded"),
            "ingestion_complete": state.get("ingestion_complete"),
            "has_contents": state.get("has_contents"),
            "accounts": (checklist.get("accounts") or {}).get("count"),
            "agents": (checklist.get("agents") or {}).get("count"),
            "missing_agent_types":
                (checklist.get("agents") or {}).get("missing_priority_types")}


# --------------------------------------------------------------------------
# setup — persona + top accounts (the 20 scarce slots)
# --------------------------------------------------------------------------

def setup(top: int = 20, db: str | None = None,
          root: str | None = None) -> dict:
    path = _resolve(db, root)

    titles = _icp_buying_titles(path)
    if not titles:
        raise SillageError("aucun title pattern dans context/icp.md "
                           "(## Buying roles) — lance /onboard d'abord")
    persona_body: dict = {"job_title": titles}
    geography = _icp_geography(path)
    if geography:
        persona_body["location"] = geography
    persona = _call("/v2/persona", persona_body, "PUT")

    candidates = _rows(
        path, "companies",
        "icp_verdict='qualified' AND domain IS NOT NULL AND domain!=''",
        cols="_id,name,domain,fit_score",
        order="CAST(fit_score AS INTEGER) DESC")[: max(1, int(top))]
    if not candidates:
        raise SillageError("aucune company qualified à pousser — la porte P2 "
                           "d'abord (qualification), puis re-lance setup")

    known = {}
    page = 1
    while True:
        listing = _call("/v2/top-account-list/accounts",
                        params={"page": page, "page_size": 100})
        for entry in listing.get("data") or []:
            company = entry.get("company") or {}
            dom = _norm_domain(company.get("domain"))
            if dom:
                known[dom] = entry.get("company_id") or entry.get("id")
        pagination = (listing.get("meta") or {}).get("pagination") or {}
        if page >= int(pagination.get("page_count") or 1):
            break
        page += 1

    to_push = [{"domain": _norm_domain(c["domain"])} for c in candidates
               if _norm_domain(c["domain"]) not in known]
    if to_push:
        _call("/v2/top-account-list/accounts", {"accounts": to_push}, "POST")

    status = _call("/v2/top-account-list/status")
    ingestion = (status.get("ingestion_state") or status.get("state")
                 or _dig(status, "ingestion_state") or "unknown")

    # Re-read after push: resolved accounts carry the Sillage company id —
    # the SAME id space signals.company_id speaks at pull.
    known = {}
    page = 1
    while True:
        listing = _call("/v2/top-account-list/accounts",
                        params={"page": page, "page_size": 100})
        for entry in listing.get("data") or []:
            company = entry.get("company") or {}
            dom = _norm_domain(company.get("domain"))
            if dom:
                known[dom] = entry.get("company_id") or entry.get("id")
        pagination = (listing.get("meta") or {}).get("pagination") or {}
        if page >= int(pagination.get("page_count") or 1):
            break
        page += 1

    updates = []
    for c in candidates:
        sid = known.get(_norm_domain(c["domain"]))
        if sid:
            updates.append({"_id": c["_id"], "sillage_company_id": str(sid),
                            "tracked": "1"})
    if updates:                                   # ONE wave, never per row
        dbmod.modify(path, "companies", updates=updates)

    unresolved = [c["domain"] for c in candidates
                  if _norm_domain(c["domain"]) not in known]
    return {"ok": True, "persona_titles": len(titles),
            "persona_id": (persona.get("data") or {}).get("id"),
            "persona_warnings": persona.get("warnings") or None,
            "pushed": len(to_push), "tracked": len(updates),
            "ingestion_state": ingestion,
            "unresolvedDomains": unresolved[:10] or None,
            "note": ("ingestion en cours — re-lance `setup` dans ~1 min pour "
                     "récupérer les ids manquants" if unresolved else
                     "tous les comptes poussés sont résolus et trackés")}


# --------------------------------------------------------------------------
# watchlist — competitor (companies) | champion (profiles)
# --------------------------------------------------------------------------

def _ensure_watchlist(db_path: str, wtype: str) -> tuple[int, str]:
    """Find-or-create the workspace watchlist of this type; id+kind cached
    in memory/state.json (§8)."""
    state = _state_read(db_path).get("sillage", {})
    cached = (state.get("watchlists") or {}).get(wtype)
    if cached and cached.get("id"):
        return int(cached["id"]), cached.get("kind") or "company"
    for wl in (_call("/v2/watchlists").get("data") or []):
        if wl.get("type") == wtype:
            found = {"id": wl["id"], "kind": wl.get("kind") or "company"}
            wls = state.get("watchlists") or {}
            wls[wtype] = found
            _state_write(db_path, {"watchlists": wls})
            return int(found["id"]), found["kind"]
    created = _call("/v2/watchlists",
                    {"type": wtype, "title": f"Bricks — {wtype}"},
                    "POST").get("data") or {}
    if not created.get("id"):
        raise SillageError(f"création watchlist {wtype} : réponse sans id")
    found = {"id": created["id"], "kind": created.get("kind") or "company"}
    wls = state.get("watchlists") or {}
    wls[wtype] = found
    _state_write(db_path, {"watchlists": wls})
    return int(found["id"]), found["kind"]


def watchlist(wtype: str, top: int = 5, urls: str | None = None,
              db: str | None = None, root: str | None = None) -> dict:
    if wtype not in ("competitor", "champion"):
        raise SillageError("--type doit être competitor ou champion")
    path = _resolve(db, root)
    wl_id, kind = _ensure_watchlist(path, wtype)

    if wtype == "competitor":
        rows = _rows(path, "competitors",
                     "domain IS NOT NULL AND domain!=''",
                     cols="_id,name,domain,interest_score,watched,sillage_entity_id",
                     order="CAST(interest_score AS INTEGER) DESC")
        if not rows:
            raise SillageError("aucun concurrent avec domaine résolu — "
                               "/onboard Phase 3 d'abord")
        targets = [r for r in rows if str(r.get("watched") or "") != "1"]
        targets = targets[: max(1, int(top))]
        updates, errors = [], []
        for r in targets:
            # one entity per call: the response carries no domain echo, a
            # single-entity call keeps the id ↔ competitor mapping unambiguous
            resp = _call(f"/v2/watchlists/{kind}/{wl_id}/entities",
                         {"entities": [{"domain": _norm_domain(r["domain"])}]},
                         "POST")
            entity = next(iter(resp.get("data") or []), None)
            if entity and entity.get("id"):
                updates.append({"_id": r["_id"], "watched": "1",
                                "sillage_entity_id": str(entity["id"])})
            else:
                err = next(iter(resp.get("errors") or []), {})
                errors.append({"domain": r["domain"],
                               "code": err.get("code") or "no_entity",
                               "message": (err.get("message") or "")[:120]})
        if updates:                               # ONE wave, never per row
            dbmod.modify(path, "competitors", updates=updates)
        already = sum(1 for r in rows if str(r.get("watched") or "") == "1")
        return {"ok": True, "watchlist_id": wl_id, "type": wtype,
                "added": len(updates), "alreadyWatched": already,
                "errors": errors or None}

    # champion — profile URLs: --urls wins, else is_champion contacts
    profile_urls = [u.strip() for u in (urls or "").split(",") if u.strip()]
    if not profile_urls:
        champs = _rows(path, "contacts",
                       "is_champion='1' AND linkedin_url IS NOT NULL "
                       "AND linkedin_url!=''", cols="_id,full_name,linkedin_url")
        profile_urls = [c["linkedin_url"] for c in champs]
    if not profile_urls:
        return {"ok": True, "watchlist_id": wl_id, "type": wtype, "added": 0,
                "note": "aucun champion fourni (--urls) ni contact "
                        "is_champion='1' — étape sautée, dit tel quel"}
    added, errors = [], []
    for u in profile_urls:
        resp = _call(f"/v2/watchlists/{kind}/{wl_id}/entities",
                     {"entities": [{"linkedin_url": _norm_linkedin(u)}]},
                     "POST")
        entity = next(iter(resp.get("data") or []), None)
        if entity and entity.get("id"):
            added.append(entity["id"])
        else:
            err = next(iter(resp.get("errors") or []), {})
            errors.append({"linkedin_url": u,
                           "code": err.get("code") or "no_entity",
                           "message": (err.get("message") or "")[:120]})
    state = _state_read(path).get("sillage", {})
    wls = state.get("watchlists") or {}
    wls["champion"] = {**(wls.get("champion") or {"id": wl_id, "kind": kind}),
                       "entity_ids": added}
    _state_write(path, {"watchlists": wls})
    return {"ok": True, "watchlist_id": wl_id, "type": wtype,
            "added": len(added), "errors": errors or None}


# --------------------------------------------------------------------------
# agents — the 4 agents (+champion when its watchlist exists)
# --------------------------------------------------------------------------

def agents(keywords: str | None = None, db: str | None = None,
           root: str | None = None) -> dict:
    path = _resolve(db, root)
    existing = {a.get("type"): a for a in (_call("/v2/agents").get("data") or [])}

    kw = [k.strip() for k in (keywords or "").split(",") if k.strip()]
    if not kw:
        kw = _pain_keywords(path)

    state_wl = _state_read(path).get("sillage", {}).get("watchlists") or {}
    created, skipped = [], []

    def _ensure(agent_type: str, name: str, parameters: dict | None = None,
                watchlist_id: int | None = None) -> None:
        if agent_type in existing:
            skipped.append(agent_type)
            return
        body: dict = {"name": name, "type": agent_type}
        if parameters:
            body["parameters"] = parameters
        if watchlist_id:
            body["watchlist_id"] = int(watchlist_id)
        _call("/v2/agents", body, "POST")
        created.append(agent_type)

    _ensure("job_update", "Bricks — prises de poste")
    if kw:
        _ensure("keyword_detection", "Bricks — mots-clés pain",
                {"tracking_keywords": kw})
        _ensure("job_posting_keyword_detection", "Bricks — offres d'emploi",
                {"tracking_keywords": kw})
    else:
        skipped.append("keyword agents (aucun keyword — passe --keywords "
                       "ou remplis offer.md ## Problems it solves)")

    competitor_wl = (state_wl.get("competitor") or {}).get("id")
    if not competitor_wl:
        for wl in (_call("/v2/watchlists").get("data") or []):
            if wl.get("type") == "competitor":
                competitor_wl = wl["id"]
                break
    if competitor_wl:
        _ensure("competitor", "Bricks — radar concurrents",
                watchlist_id=competitor_wl)
    else:
        skipped.append("competitor (watchlist absente — lance "
                       "`watchlist --type competitor` d'abord)")

    champion_wl = (state_wl.get("champion") or {}).get("id")
    if champion_wl:
        _ensure("champion", "Bricks — champions", watchlist_id=champion_wl)

    return {"ok": True, "created": created, "existing": skipped,
            "keywords_used": kw or None}


# --------------------------------------------------------------------------
# run — launch signal runs (one per agent) and poll until done
# --------------------------------------------------------------------------

def run(lookback: int = 90, no_wait: bool = False, force: bool = False,
        all_agents: bool = False, db: str | None = None,
        root: str | None = None) -> dict:
    path = _resolve(db, root)
    state = _state_read(path).get("sillage", {})
    pending: dict = dict(state.get("runs_pending") or {})

    if pending and not force:
        note = ("runs en cours repris depuis state.json (§8 : on ne repaie "
                "pas) — `--force` pour relancer un cycle complet")
    else:
        pending = {}
        # A shared/sponsor workspace can carry dozens of foreign agents —
        # by default only OUR agents run (the `agents` subcommand prefixes
        # every name with "Bricks"); --all-agents opts out, on purpose.
        skipped_foreign = 0
        for agent in (_call("/v2/agents").get("data") or []):
            if agent.get("enabled") is False:
                continue
            if not all_agents and not str(agent.get("name") or "")\
                    .startswith("Bricks"):
                skipped_foreign += 1
                continue
            resp = _call("/v2/workspace/signal-runs",
                         {"agent_id": int(agent["id"]),
                          "parameters": {"lookback_days": int(lookback)}},
                         "POST")
            run_id = _dig(resp, "signal_request_id", "request_id", "id")
            if run_id:
                pending[str(agent["id"])] = {"run_id": int(run_id),
                                             "type": agent.get("type")}
        if not pending:
            raise SillageError(
                "aucun agent « Bricks » actif — lance `agents` d'abord"
                + (f" ({skipped_foreign} agents étrangers au projet ignorés ; "
                   "--all-agents pour les inclure)" if skipped_foreign else ""))
        _state_write(path, {"runs_pending": pending})
        note = f"{len(pending)} runs lancés (lookback {lookback}j)"

    if no_wait:
        return {"ok": True, "runs": pending, "note": note + " — pas d'attente "
                "(--no-wait) ; re-lance `run` pour poller"}

    stages: dict = {}
    for _ in range(RUN_POLL_MAX):
        stages = {}
        for agent_id, info in pending.items():
            poll = _call(f"/v2/workspace/signal-runs/{info['run_id']}")
            stages[agent_id] = {"type": info.get("type"),
                                "stage": poll.get("stage"),
                                "dropped": ((poll.get("metadata") or {})
                                            .get("failed") or {})
                                .get("dropped_account_ids") or None}
        if all(s["stage"] in _RUN_STAGES_FINAL for s in stages.values()):
            break
        time.sleep(RUN_POLL_SLEEP)

    done = all(s["stage"] in _RUN_STAGES_FINAL for s in stages.values())
    _state_write(path, {"runs_pending": {} if done else pending})
    return {"ok": True, "note": note, "completed": done, "stages": stages,
            "next": "pull" if done else
            "re-lance `run` (reprend le polling, ne relance rien)"}


# --------------------------------------------------------------------------
# pull — detections since cursor → contract signal rows
# --------------------------------------------------------------------------

_SUMMARY_FR = {
    "newJob": "Prise de poste : {actor}{at_company}",
    "recentlyPromoted": "Promotion : {actor}{at_company}",
    "jobPosting": "Offre d'emploi détectée{at_company} : {extra}",
    "keywordDetection": "Mot-clé détecté{at_company} : {extra}",
    "champion_move": "Mouvement du champion {actor}{at_company}",
}


def _summary(canonical: str, raw: str, actor: str, company: str,
             extra: str) -> str:
    at_company = f" chez {company}" if company else ""
    template = _SUMMARY_FR.get(canonical)
    if template:
        text = template.format(actor=actor or "un contact",
                               at_company=at_company,
                               extra=(extra or "voir contenu").strip())
    else:  # competitor* & co — provisional, rewritten by intercept.py
        text = (f"Engagement autour d'un concurrent : "
                f"{actor or 'acteur externe'} — à intercepter")
    return text[:300]


def _content_text(content_id) -> dict:
    try:
        data = (_call(f"/v2/contents/{int(content_id)}",
                      params={"response_format": "normalized"})
                .get("data") or {})
    except (SillageError, ValueError, TypeError):
        return {}
    inner = data.get("data") or {}
    return {"text": inner.get("text") or inner.get("description") or "",
            "title": inner.get("title") or "",
            "url": inner.get("link") or inner.get("linkedin_url") or ""}


def pull(limit: int = 100, since: str | None = None, max_new: int = 500,
         db: str | None = None, root: str | None = None) -> dict:
    path = _resolve(db, root)
    state = _state_read(path).get("sillage", {})
    cursor = state.get("cursor") or None
    if since and not re.match(r"^\d{4}-\d{2}-\d{2}$", since):
        raise SillageError("--since doit être une date YYYY-MM-DD")

    existing = {str(r.get("sillage_signal_id"))
                for r in _rows(path, "signals", cols="sillage_signal_id")}
    by_sillage_company = {
        str(r["sillage_company_id"]): r
        for r in (_rows(path, "companies",
                        "sillage_company_id IS NOT NULL AND sillage_company_id!=''",
                        cols="_id,name,sillage_company_id")
                  if _has_col(path, "companies", "sillage_company_id") else [])}
    by_sillage_lead = {
        str(r["sillage_lead_id"]): r
        for r in (_rows(path, "contacts",
                        "sillage_lead_id IS NOT NULL AND sillage_lead_id!=''",
                        cols="_id,company_id,full_name,sillage_lead_id")
                  if _has_col(path, "contacts", "sillage_lead_id") else [])}
    competitors_rows = _rows(path, "competitors",
                             cols="_id,name,domain,linkedin_url,sillage_entity_id")
    by_entity = {str(r.get("sillage_entity_id")): r for r in competitors_rows
                 if str(r.get("sillage_entity_id") or "")}

    rows, counts, samples = [], {}, []
    pulled = new = 0
    run_tag = f"pull-{_today()}"
    capped = False
    while True:
        body: dict = {"limit": max(1, min(int(limit), 200))}
        if cursor:
            body["cursor"] = cursor
        if since:
            body["signal_start_date"] = since
        page = _call("/v2/workspace/signals/query", body, "POST")
        detections = page.get("data") or []
        meta = page.get("meta") or {}
        pulled += len(detections)
        for det in detections:
            sid = str(det.get("id"))
            if not sid or sid in existing:
                continue
            existing.add(sid)
            raw = str(det.get("signal_type") or "")
            canonical = TYPE_MAP.get(raw, "")
            is_competitor = raw.startswith("competitor")
            data = det.get("data") or {}

            actor_name = str(_dig(data, "actor_name", "full_name", "name",
                                  "author_name") or "").strip()
            if not actor_name:
                first = str(_dig(data, "first_name", "firstName") or "").strip()
                last = str(_dig(data, "last_name", "lastName") or "").strip()
                actor_name = f"{first} {last}".strip()
            actor_headline = str(_dig(data, "headline", "actor_headline",
                                      "position", "title") or "").strip()
            actor_linkedin = _norm_linkedin(
                str(_dig(data, "actor_linkedin", "linkedin_url",
                         "linkedinUrl", "profile_url") or ""))

            company_row = by_sillage_company.get(str(det.get("company_id")))
            contact_row = by_sillage_lead.get(str(det.get("lead_id")))
            company_id = (company_row or {}).get("_id") or \
                         (contact_row or {}).get("company_id") or ""
            company_name = (company_row or {}).get("name") or ""

            competitor_id = ""
            if is_competitor or raw.startswith(("partner", "customer",
                                                "influencer", "champion")):
                entity_ref = _dig(data, "entity_id", "watchlist_entity_id")
                comp = by_entity.get(str(entity_ref)) if entity_ref else None
                if comp is None and is_competitor:
                    dom = _norm_domain(str(_dig(data, "company_domain",
                                                "domain") or ""))
                    comp = next((c for c in competitors_rows
                                 if _norm_domain(c.get("domain")) == dom
                                 and dom), None)
                if comp and is_competitor:
                    competitor_id = comp["_id"]

            content_ref = _dig(data, "content_id", "post_content_id",
                               "contentId")
            content = _content_text(content_ref) if content_ref else {}
            text = content.get("text") or str(_dig(data, "text", "comment",
                                                   "description") or "")
            is_comment = raw.endswith("Comment")
            source_url = (content.get("url")
                          or str(_dig(data, "link", "url", "source_url") or ""))

            if contact_row:
                actor_side = "lead"
            elif is_competitor:
                actor_side = "external"      # the prospect engaging with THEM
            elif raw.startswith(("champion", "partner", "customer",
                                 "influencer")):
                actor_side = "watchlist"
            else:
                actor_side = "lead" if det.get("lead_id") else "watchlist"

            summary = _summary(canonical, raw, actor_name, company_name,
                               content.get("title") or text[:80])
            row = {"sillage_signal_id": sid,
                   "company_id": str(company_id or ""),
                   "contact_id": str((contact_row or {}).get("_id") or ""),
                   "competitor_id": str(competitor_id or ""),
                   "type": canonical,
                   "sillage_type": raw,
                   "signal_date": (det.get("signal_date") or "")[:10],
                   "detected_at": det.get("detected_at") or _now(),
                   "actor_name": actor_name,
                   "actor_headline": actor_headline,
                   "actor_linkedin": actor_linkedin,
                   "actor_side": actor_side,
                   "post_text": "" if is_comment else text,
                   "comment_text": text if is_comment else "",
                   "source_url": source_url,
                   "summary": summary,
                   "payload_json": json.dumps(det, ensure_ascii=False),
                   "source_run": run_tag}
            if is_competitor:
                row["intercept_status"] = "pending"
            rows.append(row)
            new += 1
            counts[canonical or raw or "?"] = \
                counts.get(canonical or raw or "?", 0) + 1
            if len(samples) < 3:
                samples.append(summary)
        cursor = meta.get("next_cursor") or cursor
        if not meta.get("has_more"):
            break
        if max_new and new >= int(max_new):
            capped = True     # cursor already points past this page: resume
            break

    if rows:
        dbmod.add(path, "signals", rows, key="sillage_signal_id")
    if cursor:
        _state_write(path, {"cursor": cursor})
    return {"ok": True, "pulled": pulled, "new": new, "byType": counts,
            "pendingIntercepts": sum(1 for r in rows
                                     if r.get("intercept_status") == "pending"),
            "cursor": cursor, "capped": capped or None, "samples": samples,
            "next": ("plafond --max atteint — re-lance `pull`, le curseur "
                     "reprend" if capped else
                     "leads puis /prioritize" if new else "rien de neuf")}


# --------------------------------------------------------------------------
# leads — persona mapping → contacts (company_id REQUIRED)
# --------------------------------------------------------------------------

def leads(db: str | None = None, root: str | None = None) -> dict:
    path = _resolve(db, root)
    by_domain = {_norm_domain(r["domain"]): r["_id"]
                 for r in _rows(path, "companies",
                                "domain IS NOT NULL AND domain!=''",
                                cols="_id,domain")}
    rows, skipped_company, skipped_linkedin = [], 0, 0
    coords_available = 0
    page = 1
    while True:
        listing = _call("/v1/workspace/leads",
                        params={"page": page, "pageSize": 100, "status": "all"})
        for lead in listing.get("data") or []:
            linkedin = _norm_linkedin(lead.get("linkedinUrl"))
            if not linkedin:
                skipped_linkedin += 1        # no import key, no row
                continue
            company_id = by_domain.get(
                _norm_domain((lead.get("company") or {}).get("domain")))
            if not company_id:
                skipped_company += 1         # company_id OBLIGATOIRE (contrat)
                continue
            if lead.get("email") or lead.get("phoneNumber"):
                coords_available += 1        # NOT written — P6 owns coords
            full_name = " ".join(p for p in [lead.get("firstName"),
                                             lead.get("lastName")] if p).strip()
            rows.append({"company_id": str(company_id),
                         "sillage_lead_id": str(lead.get("id") or ""),
                         "full_name": full_name,
                         "position": lead.get("position") or "",
                         "linkedin_url": linkedin})
        pagination = (listing.get("meta") or {}).get("pagination") or {}
        if page >= int(pagination.get("pageCount") or 1):
            break
        page += 1

    result = dbmod.add(path, "contacts", rows, key="linkedin_url") if rows \
        else {"added": 0, "skippedDuplicates": 0}
    return {"ok": True, "fetched": len(rows) + skipped_company + skipped_linkedin,
            "inserted": result.get("added", 0),
            "dedupSkipped": result.get("skippedDuplicates", 0),
            "skippedNoCompanyMatch": skipped_company,
            "skippedNoLinkedin": skipped_linkedin,
            "coordsAvailableNotWritten": coords_available,
            "note": ("Sillage renvoie email/tél sur certains leads ; le "
                     "contrat réserve ces colonnes à fullenrich (P6, gate "
                     "budget) — non écrits, à arbitrer en huddle"
                     if coords_available else None)}


# --------------------------------------------------------------------------
# add-signal — THE demo injection (official), a row as if pulled
# --------------------------------------------------------------------------

def add_signal(json_payload: str, db: str | None = None,
               root: str | None = None) -> dict:
    if json_payload == "-":
        json_payload = sys.stdin.read()
    try:
        given = json.loads(json_payload or "{}")
    except json.JSONDecodeError as exc:
        raise SillageError(f"--json invalide : {exc}") from None
    if not isinstance(given, dict):
        raise SillageError("--json doit être un objet {…}")
    path = _resolve(db, root)

    raw = str(given.pop("sillage_type", "") or given.get("type") or "")
    canonical = given.pop("type", "") or TYPE_MAP.get(raw, "")
    if raw in TYPE_MAP and canonical not in TYPE_MAP.values():
        canonical = TYPE_MAP[raw]
    is_competitor = (raw.startswith("competitor")
                     or canonical == "competitor_engagement")

    company_id = str(given.pop("company_id", "") or "")
    dom = _norm_domain(given.pop("company_domain", ""))
    company_name = ""
    if dom and not company_id:
        match = next((r for r in _rows(path, "companies",
                                       cols="_id,name,domain")
                      if _norm_domain(r.get("domain")) == dom), None)
        if match:
            company_id, company_name = str(match["_id"]), match.get("name", "")
    contact_id = str(given.pop("contact_id", "") or "")
    contact_linkedin = _norm_linkedin(given.pop("contact_linkedin", ""))
    if contact_linkedin and not contact_id:
        match = next((r for r in _rows(path, "contacts",
                                       cols="_id,linkedin_url")
                      if _norm_linkedin(r.get("linkedin_url"))
                      == contact_linkedin), None)
        if match:
            contact_id = str(match["_id"])
    competitor_id = str(given.pop("competitor_id", "") or "")
    comp_dom = _norm_domain(given.pop("competitor_domain", ""))
    if comp_dom and not competitor_id:
        match = next((r for r in _rows(path, "competitors",
                                       cols="_id,domain")
                      if _norm_domain(r.get("domain")) == comp_dom), None)
        if match:
            competitor_id = str(match["_id"])

    actor_name = str(given.pop("actor_name", "") or "")
    row = {"sillage_signal_id":
               str(given.pop("sillage_signal_id", "")
                   or f"demo-{uuid.uuid4().hex[:8]}"),
           "company_id": company_id, "contact_id": contact_id,
           "competitor_id": competitor_id,
           "type": "" if is_competitor and not given.get("resolved")
                   else canonical,
           "sillage_type": raw or canonical,
           "signal_date": str(given.pop("signal_date", "") or _today()),
           "detected_at": str(given.pop("detected_at", "") or _now()),
           "actor_name": actor_name,
           "actor_headline": str(given.pop("actor_headline", "") or ""),
           "actor_linkedin": _norm_linkedin(given.pop("actor_linkedin", "")),
           "actor_side": str(given.pop("actor_side", "") or
                             ("lead" if contact_id else
                              "external" if is_competitor else "watchlist")),
           "post_text": str(given.pop("post_text", "") or ""),
           "comment_text": str(given.pop("comment_text", "") or ""),
           "source_url": str(given.pop("source_url", "") or ""),
           "summary": str(given.pop("summary", "") or
                          _summary(canonical, raw, actor_name, company_name,
                                   "")),
           "payload_json": json.dumps({"demo": True, **given},
                                      ensure_ascii=False),
           "source_run": f"demo-{_today()}"}
    if is_competitor:
        row["intercept_status"] = "pending"
    result = dbmod.add(path, "signals", [row], key="sillage_signal_id")
    return {"ok": True, "inserted": result.get("added", 0),
            "sillage_signal_id": row["sillage_signal_id"],
            "type": row["type"] or None,
            "sillage_type": row["sillage_type"],
            "intercept_status": row.get("intercept_status"),
            "summary": row["summary"],
            "next": "runner intercept si competitor*, sinon /prioritize"}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Sillage surveillance provider (P3/P4).")
    dbflags = argparse.ArgumentParser(add_help=False)
    dbflags.add_argument("--db", default=None)
    dbflags.add_argument("--root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("test-auth", parents=[dbflags],
                   help="setup-state compact : persona, comptes, agents")

    p = sub.add_parser("setup", parents=[dbflags],
                       help="persona (union icp.md) + top comptes qualified")
    p.add_argument("--top", type=int, default=20)

    p = sub.add_parser("watchlist", parents=[dbflags],
                       help="crée/complète la watchlist competitor|champion")
    p.add_argument("--type", required=True, dest="wtype",
                   choices=["competitor", "champion"])
    p.add_argument("--top", type=int, default=5,
                   help="concurrents à pousser (top interest_score)")
    p.add_argument("--urls", default=None,
                   help="champion : URLs LinkedIn séparées par des virgules")

    p = sub.add_parser("agents", parents=[dbflags],
                       help="crée les agents (job_update, keywords, competitor…)")
    p.add_argument("--keywords", default=None,
                   help="mots-clés pain séparés par des virgules "
                        "(défaut : offer.md ## Problems it solves)")

    p = sub.add_parser("run", parents=[dbflags],
                       help="lance un signal run par agent et polle")
    p.add_argument("--lookback", type=int, default=90)
    p.add_argument("--no-wait", action="store_true")
    p.add_argument("--force", action="store_true",
                   help="relance même si des runs sont en cours dans state.json")
    p.add_argument("--all-agents", action="store_true",
                   help="inclut aussi les agents non « Bricks » du workspace")

    p = sub.add_parser("pull", parents=[dbflags],
                       help="détections depuis le curseur → table signals")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--since", default=None,
                   help="date plancher YYYY-MM-DD (signal_start_date)")
    p.add_argument("--max", type=int, default=500, dest="max_new",
                   help="plafond de nouvelles lignes par pull (0 = illimité)")

    sub.add_parser("leads", parents=[dbflags],
                   help="leads persona → contacts (company_id obligatoire)")

    p = sub.add_parser("add-signal", parents=[dbflags],
                       help="injection démo : une ligne signal comme pullée")
    p.add_argument("--json", required=True, dest="json_payload",
                   help="objet JSON (ou - pour stdin)")

    args = parser.parse_args(argv)
    try:
        if args.command == "test-auth":
            out = test_auth(args.db, args.root)
        elif args.command == "setup":
            out = setup(args.top, args.db, args.root)
        elif args.command == "watchlist":
            out = watchlist(args.wtype, args.top, args.urls,
                            args.db, args.root)
        elif args.command == "agents":
            out = agents(args.keywords, args.db, args.root)
        elif args.command == "run":
            out = run(args.lookback, args.no_wait, args.force,
                      args.all_agents, args.db, args.root)
        elif args.command == "pull":
            out = pull(args.limit, args.since, args.max_new,
                       args.db, args.root)
        elif args.command == "leads":
            out = leads(args.db, args.root)
        else:
            out = add_signal(args.json_payload, args.db, args.root)
    except (SillageError, dbmod.DbError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
