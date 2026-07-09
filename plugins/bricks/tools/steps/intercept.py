#!/usr/bin/env python3
"""Interception step — resolve the external actor of a competitor* signal.

Deterministic runner step (P4, driven by /surveil through the iron gate):

    python3 tools/core/runner.py run --table signals \
      --status-col intercept_status --run-id intercept-<date> \
      --step "tools/steps/intercept.py:step" --preview 10
    # receipts → ONE explicit GO → same command with --commit

Per pending signal row (a `competitor*` detection pulled by sillage.py):

1. READ the evidence — `payload_json` (the raw Sillage detection) plus the
   actor columns already on the row. The resolution is EVIDENCE-ONLY:
   the actor's company must appear in the payload (name + domain, or a
   LinkedIn company URL alongside a domain). Nothing is fabricated, no
   guessed domains, no web calls (v1 — a FullEnrich resolve can be added
   as an explicit args opt-in later).
2. RESOLVED → insert the company through the only door (§4), dedup by
   domain: `source='competitor_interception'`, `qualify_status='pending'`
   armed AT INSERT — the SAME P2 gate as sourced rows. Static firmo
   (headcount / industry / geo) is copied when the payload carries it.
   The step then returns the signal-side fields: `company_id`,
   `type='competitor_engagement'` (the canonical type, posed HERE per
   contract), and a rewritten human summary.
3. UNRESOLVED → returns `{"intercept_status": "not_found"}` — the fields
   dict is merged AFTER the engine's status write, so the row lands
   `not_found` (a RESULT, §4) instead of `done`; the signal keeps no
   company_id and no phantom company row is ever created.

Companies are inserted on preview AND commit (§5: preview rows are
settled, never re-paid — same doctrine as fullenrich.py child rows).

One-off dry CLI (no database writes, resolution only):
    python3 tools/steps/intercept.py --payload '{"…": "…"}'
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

_CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
sys.path.insert(0, os.path.abspath(_CORE))
import db as dbmod  # noqa: E402

_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{2,250}\.[a-z]{2,24}$")

#: payload keys that plausibly carry the ACTOR'S company object/values —
#: Sillage payload shapes vary by agent; we look, we never invent.
_COMPANY_NODES = ("actor_company", "author_company", "company",
                  "organization", "current_company")
_DOMAIN_KEYS = ("domain", "company_domain", "website", "company_website")
_NAME_KEYS = ("company_name", "name")
_LINKEDIN_KEYS = ("company_linkedin_url", "linkedin_url", "linkedinUrl")
_HEADCOUNT_KEYS = ("headcount", "employee_count", "number_of_employees",
                   "numberOfEmployees", "company_size")
_INDUSTRY_KEYS = ("industry", "company_industry")
_GEO_KEYS = ("geo", "country", "location", "company_country")


def _norm_domain(value) -> str:
    d = str(value or "").strip().lower()
    d = re.sub(r"^[a-z]+://", "", d)
    d = d.split("/")[0].split("?")[0]
    d = d[4:] if d.startswith("www.") else d
    return d if _DOMAIN_RE.match(d) else ""


def _norm_linkedin(value) -> str:
    u = str(value or "").strip()
    if not u:
        return ""
    match = re.search(r"linkedin\.com/(in|company)/([^/?#]+)", u, re.I)
    if not match:
        return ""
    return f"https://www.linkedin.com/{match.group(1).lower()}/{match.group(2)}"


def _first(node: dict, keys: tuple) -> str:
    for key in keys:
        for k, v in node.items():
            if k.lower() == key.lower() and v not in (None, "", [], {}):
                return str(v)
    return ""


def _company_candidates(payload: object) -> list[dict]:
    """Every dict in the payload that smells like a company object, plus the
    payload roots themselves (flat shapes)."""
    found, queue = [], [payload]
    while queue:
        item = queue.pop(0)
        if isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, dict) and k.lower() in _COMPANY_NODES:
                    found.append(v)
                queue.append(v) if isinstance(v, (dict, list)) else None
            found.append(item)  # flat payloads carry company_* keys at root
        elif isinstance(item, list):
            queue.extend(item)
    return found


def resolve_actor(row: dict) -> dict | None:
    """Extract {name, domain, linkedin_url, headcount, industry, geo} from
    the signal's payload — or None when the evidence is not there."""
    try:
        payload = json.loads(row.get("payload_json") or "{}")
    except json.JSONDecodeError:
        payload = {}
    for node in _company_candidates(payload):
        domain = _norm_domain(_first(node, _DOMAIN_KEYS))
        if not domain:
            continue
        return {"name": _first(node, _NAME_KEYS) or domain,
                "domain": domain,
                "linkedin_url": _norm_linkedin(_first(node, _LINKEDIN_KEYS)),
                "headcount": _first(node, _HEADCOUNT_KEYS),
                "industry": _first(node, _INDUSTRY_KEYS),
                "geo": _first(node, _GEO_KEYS)}
    return None


def _competitor_name(db_path: str, row: dict) -> str:
    cid = str(row.get("competitor_id") or "").strip()
    if not cid.isdigit():
        return ""
    rows = dbmod.select(db_path, "competitors", where=f"_id={int(cid)}",
                        cols="_id,name")["rows"]
    return rows[0]["name"] if rows else ""


def step(row: dict, ctx: dict, args: dict | None = None) -> dict:
    resolved = resolve_actor(row)
    if resolved is None:
        # a RESULT, not an error: fields merge AFTER the engine's status
        # write, so the row lands not_found and stays company-less (§4).
        return {"intercept_status": "not_found"}

    company_row = {"name": resolved["name"],
                   "domain": resolved["domain"],
                   "linkedin_url": resolved["linkedin_url"],
                   "headcount": resolved["headcount"],
                   "industry": resolved["industry"],
                   "geo": resolved["geo"],
                   "source": "competitor_interception",
                   "qualify_status": "pending",       # SAME P2 gate for all
                   "source_run": ctx.get("run_id") or ""}
    if ctx.get("commit") or ctx.get("preview"):
        dbmod.add(ctx["db"], "companies", [company_row], key="domain")
    matches = dbmod.select(ctx["db"], "companies",
                           where=f"domain='{resolved['domain']}'",
                           cols="_id,name")["rows"]
    if not matches:
        raise RuntimeError(f"company inserted but not found back "
                           f"({resolved['domain']}) — db inconsistency")
    company_id = matches[0]["_id"]

    actor = str(row.get("actor_name") or "").strip() or "Acteur externe"
    headline = str(row.get("actor_headline") or "").strip()
    competitor = _competitor_name(ctx["db"], row)
    summary = (f"Intercepté : {actor}"
               + (f" ({headline})" if headline else "")
               + f" — {resolved['name']}"
               + (f" engage avec {competitor}" if competitor
                  else " engage avec un concurrent surveillé")
               + " ; à qualifier (P2)")

    return {"company_id": str(company_id),
            "type": "competitor_engagement",
            "summary": summary[:300]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run the actor resolution on one payload (no writes).")
    parser.add_argument("--payload", required=True,
                        help="payload_json (or - for stdin)")
    args = parser.parse_args(argv)
    raw = sys.stdin.read() if args.payload == "-" else args.payload
    resolved = resolve_actor({"payload_json": raw})
    print(json.dumps({"ok": True, "resolved": resolved,
                      "verdict": "insertable" if resolved else "not_found"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
