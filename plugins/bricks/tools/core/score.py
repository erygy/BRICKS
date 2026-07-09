#!/usr/bin/env python3
"""Signal-fusion scoring kernel — the deterministic half of /prioritize (P5).

File in → file out. Zero LLM, zero network, zero database: like rank.py (the
kernel this one extends), this script never touches bricks.db — reading the
rows and committing the results are separate db.py steps, done by the skill.
Given the same inputs and the same spec it produces the same output, forever:
a priority ranking must be reproducible and explainable to a jury, never
re-invented by a model each run.

What it does, in one deterministic pass over the CONTRACT tables (CLAUDE.md):
  1. fold the `signals` table into per-company and per-contact HEAT:
         heat = min(cap, Σ points(type) × e^(−age_days/21))
     where a contact's own signals count ×1.0 and the colleagues'/company
     signals count ×0.5 (the "faisceau" — convergence beats any single hit);
  2. fuse into scores /100:
         contact = 0.35×fit + 0.45×heat + 0.20×persona
         company = 0.45×fit + 0.55×heat
     fit = companies.fit_score (P2 verdict), persona = seniority/role match,
     is_champion contacts pin persona to 100;
  3. tier now|week|nurture, pick the top 2-3 FRESH signals as
     `why_now_evidence` (JSON [{_id,type,date,summary}] — the proof ids the
     UI and the drafts cite), assemble a deterministic `why_now` draft from
     the strongest one (template, no model — never an overstatement);
  4. optionally emit the WEEK QUEUE: the top-N contacts as outreach rows
     ready for `db.py add outreach --rows - --key dedup_key`.

Only companies with icp_verdict='qualified' (and their contacts) are scored —
same gate for sourced and intercepted rows. Signals without a resolved
company_id are counted `unresolved`, never guessed.

The polished one-sentence why_now is NOT this script's job: the /prioritize
skill arms `why_now_status='pending'` on the now|week rows it just committed
and runs ONE runner.py `--ai` pass (agent_api under BRICKS_AGENT_TRANSPORT=api)
whose prompt cites {{why_now_evidence}} — model output replaces the draft,
evidence ids stay. Example pass (haiku, schema-forced):

    python3 tools/core/db.py modify contacts --set why_now_status=pending \
        --where "priority_tier IN ('now','week')"
    python3 tools/core/runner.py run --table contacts \
        --status-col why_now_status --run-id whynow-contacts-2026-07-09 \
        --ai '{"prompt":"Faisceau de signaux du prospect {{full_name}} :\n{{why_now_evidence}}\nÉcris LE why-now : UNE phrase française, factuelle et datée, qui donne la raison d'appeler CETTE semaine. Chaque fait vient du faisceau, zéro superlatif.","schema":{"type":"object","properties":{"why_now":{"type":"string"}}},"model":"haiku"}' \
        --preview 10        # check, ONE GO, then --commit

The full P5 loop (db.py select default limit is 50 — always pass --limit):

    python3 tools/core/db.py select companies --limit 100000 > staging/companies.json
    python3 tools/core/db.py select contacts  --limit 100000 > staging/contacts.json
    python3 tools/core/db.py select signals   --limit 100000 > staging/signals.json
    python3 tools/core/score.py run \
        --companies staging/companies.json --contacts staging/contacts.json \
        --signals staging/signals.json \
        --out-companies staging/score_companies.json \
        --out-contacts staging/score_contacts.json \
        --queue 10 --out-queue staging/score_queue.json
    python3 tools/core/db.py modify companies --updates - < staging/score_companies.json
    python3 tools/core/db.py modify contacts  --updates - < staging/score_contacts.json
    # the queue file is a PROPOSAL — /outreach reviews it, then:
    #   python3 tools/core/db.py add outreach --rows - --key dedup_key < staging/score_queue.json

CLI (JSON receipt on stdout; on error JSON on stderr + exit 1):
    python3 score.py run --companies F --contacts F --signals F [--spec F]
        [--out-companies F] [--out-contacts F] [--today YYYY-MM-DD]
        [--queue N] [--week 2026-Wnn] [--out-queue F]

Inputs are whatever `db.py select` prints (a dict with a "rows" list), a
plain JSON array, or JSONL. Column NAMES are fixed by the frozen contract
(CLAUDE.md) and are code constants here; every WEIGHT and THRESHOLD is a
spec-JSON hole with a default baked in, so an empty `{}` still runs:

    {
      "type_points": {"champion_move": 30, "competitor_engagement": 25,
                      "newJob": 25, "recentlyPromoted": 20,
                      "jobPosting": 15, "keywordDetection": 10},
      "default_type_points": 0,          # unknown type = loud in the receipt, worth 0
      "tau_days": 21,                    # e^(−age/21): ~½ at 15d, ~⅓ at 21d
      "default_age_days": 45,            # signal with no parseable date
      "colleague_factor": 0.5,
      "heat_cap": 100,
      "contact_weights": {"fit": 0.35, "heat": 0.45, "persona": 0.20},
      "company_weights": {"fit": 0.45, "heat": 0.55},
      "default_fit": 40,                 # fit_score missing/unparseable
      "persona_patterns": [["founder",100], ["chief",100], ["ceo",100], ...],
      "default_persona_points": 30,
      "champion_persona_points": 100,    # is_champion='1' pins persona
      "tiers": {"now": 60, "week": 40},
      "evidence_top": 3,
      "evidence_min_decay": 0.05,        # older than ~63d = context, not proof
      "queue_tiers": ["now", "week"],
      "type_labels": {"champion_move": "Champion en mouvement", ...}
    }
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import time

DEFAULT_SPEC = {
    "type_points": {"champion_move": 30, "competitor_engagement": 25,
                    "newJob": 25, "recentlyPromoted": 20,
                    "jobPosting": 15, "keywordDetection": 10},
    "default_type_points": 0,
    "tau_days": 21,
    "default_age_days": 45,
    "colleague_factor": 0.5,
    "heat_cap": 100,
    "contact_weights": {"fit": 0.35, "heat": 0.45, "persona": 0.20},
    "company_weights": {"fit": 0.45, "heat": 0.55},
    "default_fit": 40,
    "persona_patterns": [
        ["founder", 100], ["co-founder", 100], ["fondateur", 100],
        ["chief", 100], ["ceo", 100], ["cto", 100], ["coo", 100],
        ["cro", 100], ["cmo", 100], ["cfo", 100], ["c-level", 100],
        ["c_suite", 100], ["owner", 95], ["président", 95], ["president", 95],
        ["partner", 90], ["evp", 90], ["svp", 90], ["vp", 85],
        ["vice president", 85], ["head", 85], ["director", 70],
        ["directeur", 70], ["directrice", 70], ["manager", 55],
        ["responsable", 55], ["lead", 45], ["senior", 35], ["entry", 20],
    ],
    "default_persona_points": 30,
    "champion_persona_points": 100,
    "tiers": {"now": 60, "week": 40},
    "evidence_top": 3,
    "evidence_min_decay": 0.05,
    "queue_tiers": ["now", "week"],
    "type_labels": {"champion_move": "Champion en mouvement",
                    "competitor_engagement": "Engagé chez le concurrent",
                    "newJob": "Prise de poste",
                    "recentlyPromoted": "Promotion récente",
                    "jobPosting": "Recrute",
                    "keywordDetection": "Douleur exprimée"},
}

QUALIFIED = "qualified"                  # companies.icp_verdict gate (contract)
TRUTHY = ("1", "true", "yes")


class ScoreError(ValueError):
    """Raised on any invalid input; nothing is written."""


# --------------------------------------------------------------------------
# Loading (same tolerance as rank.py: db.py payload / JSON array / JSONL)
# --------------------------------------------------------------------------

def _load_rows(path: str, what: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
    except OSError as exc:
        raise ScoreError(f"cannot read {what} file {path!r}: {exc}") from None
    if not text:
        return []
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for i, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ScoreError(f"{what}: line {i} is not valid JSON ({exc})") from None
        return rows
    if isinstance(obj, dict) and isinstance(obj.get("rows"), list):
        return obj["rows"]
    if isinstance(obj, list):
        return obj
    raise ScoreError(f"{what}: expected a db.py select payload, a JSON array, or JSONL")


def _merge_spec(user: dict) -> dict:
    spec = json.loads(json.dumps(DEFAULT_SPEC))  # deep copy
    for key, value in (user or {}).items():
        if isinstance(value, dict) and isinstance(spec.get(key), dict):
            spec[key].update(value)
        else:
            spec[key] = value
    return spec


# --------------------------------------------------------------------------
# Deterministic helpers
# --------------------------------------------------------------------------

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")


def _parse_date(value) -> dt.date | None:
    if not isinstance(value, str):
        return None
    m = _DATE_RE.search(value)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _num(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sid(value) -> str:
    """FK/id as a string key — every db.py column is TEXT, `_id` is INTEGER."""
    return "" if value is None else str(value).strip()


def _signal_features(sig: dict, spec: dict, today: dt.date) -> dict:
    """One signal → its scoring features (unknown types weigh default_type_points)."""
    kind = str(sig.get("type") or "").strip()
    points = spec["type_points"].get(kind)
    if points is None:
        points = spec["default_type_points"]
        known = False
    else:
        known = True
    date = _parse_date(sig.get("signal_date")) or _parse_date(sig.get("detected_at"))
    age = max(0, (today - date).days) if date else spec["default_age_days"]
    decay = math.exp(-age / float(spec["tau_days"]))
    return {
        "id": sig.get("_id"),
        "type": kind,
        "known": known,
        "date": date.isoformat() if date else "",
        "summary": str(sig.get("summary") or "").strip(),
        "contact_id": _sid(sig.get("contact_id")),
        "contribution": points * decay,
        "decay": decay,
    }


def _persona_points(contact: dict, spec: dict) -> int:
    if str(contact.get("is_champion") or "").strip().lower() in TRUTHY:
        return int(spec["champion_persona_points"])
    haystack = " ".join(str(contact.get(col) or "") for col in ("seniority", "position")).lower()
    for pattern, points in spec["persona_patterns"]:
        pat = str(pattern).lower()
        if len(pat) <= 3:                          # short tokens: word-bounded
            if re.search(rf"\b{re.escape(pat)}\b", haystack):
                return int(points)
        elif pat in haystack:
            return int(points)
    return int(spec["default_persona_points"])


def _fold_heat(feats: list[tuple[dict, float]], spec: dict) -> float:
    """Σ contribution×factor, capped — the faisceau in one number."""
    raw = sum(f["contribution"] * factor for f, factor in feats)
    return min(float(spec["heat_cap"]), raw)


def _evidence(feats: list[tuple[dict, float]], spec: dict) -> list[dict]:
    """Top fresh signals by weighted contribution → the proof the UI shows."""
    fresh = [(f, factor) for f, factor in feats
             if f["decay"] >= spec["evidence_min_decay"] and f["contribution"] * factor > 0]
    fresh.sort(key=lambda pair: pair[0]["contribution"] * pair[1], reverse=True)
    return [{"_id": f["id"], "type": f["type"], "date": f["date"],
             "summary": f["summary"]} for f, _ in fresh[:int(spec["evidence_top"])]]


def _why_now_draft(evidence: list[dict], spec: dict) -> str:
    """Deterministic fallback sentence — the --ai pass may overwrite it."""
    if not evidence:
        return ""
    top = evidence[0]
    label = spec["type_labels"].get(top["type"], top["type"])
    head = f"{label} : {top['summary']}" if top["summary"] else label
    if top["date"]:
        head += f" ({top['date']})"
    if len(evidence) > 1:
        head += f" — faisceau de {len(evidence)} signaux"
    return head


def _tier(score: int, spec: dict) -> str:
    tiers = spec["tiers"]
    if score >= tiers["now"]:
        return "now"
    if score >= tiers["week"]:
        return "week"
    return "nurture"


def _clamp100(value: float) -> int:
    return int(round(min(100.0, max(0.0, value))))


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def run(companies_path: str, contacts_path: str, signals_path: str,
        spec_path: str | None = None,
        out_companies: str = "score_companies.updates.json",
        out_contacts: str = "score_contacts.updates.json",
        queue: int = 0, week: str | None = None,
        out_queue: str = "score_queue.json",
        today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    user_spec = {}
    if spec_path:
        try:
            with open(spec_path, encoding="utf-8") as f:
                user_spec = json.load(f)
        except OSError as exc:
            raise ScoreError(f"cannot read spec {spec_path!r}: {exc}") from None
        except json.JSONDecodeError as exc:
            raise ScoreError(f"spec {spec_path!r} is not valid JSON ({exc})") from None
    spec = _merge_spec(user_spec)
    if week and not _WEEK_RE.match(week):
        raise ScoreError("--week must look like 2026-W28")
    if queue and not week:
        iso = today.isocalendar()
        week = f"{iso[0]}-W{iso[1]:02d}"

    companies = _load_rows(companies_path, "companies")
    contacts = _load_rows(contacts_path, "contacts")
    signals = _load_rows(signals_path, "signals")

    # --- the qualified gate: same door for sourced and intercepted rows
    scored_companies = {_sid(c.get("_id")): c for c in companies
                        if _sid(c.get("_id"))
                        and str(c.get("icp_verdict") or "").strip().lower() == QUALIFIED}

    # --- fold signals by company, count the rest loudly
    by_company: dict[str, list[dict]] = {}
    unresolved = out_of_scope = 0
    unknown_types: dict[str, int] = {}
    for sig in signals:
        feat = _signal_features(sig, spec, today)
        if not feat["known"] and feat["type"]:
            unknown_types[feat["type"]] = unknown_types.get(feat["type"], 0) + 1
        cid = _sid(sig.get("company_id"))
        if not cid:
            unresolved += 1            # interception not resolved yet — expected
            continue
        if cid not in scored_companies:
            out_of_scope += 1          # rejected / unknown company
            continue
        by_company.setdefault(cid, []).append(feat)

    # --- companies
    c_weights = spec["company_weights"]
    company_updates, company_tiers = [], {"now": 0, "week": 0, "nurture": 0}
    for cid, company in scored_companies.items():
        feats = [(f, 1.0) for f in by_company.get(cid, [])]
        fit = _num(company.get("fit_score"), spec["default_fit"])
        heat = _fold_heat(feats, spec)
        score = _clamp100(c_weights["fit"] * fit + c_weights["heat"] * heat)
        band = _tier(score, spec)
        evidence = _evidence(feats, spec)
        company_updates.append({
            "_id": company.get("_id"),
            "priority_score": score,
            "priority_tier": band,
            "why_now": _why_now_draft(evidence, spec),
            "why_now_evidence": json.dumps(evidence, ensure_ascii=False),
            "scored_at": today.isoformat(),
        })
        company_tiers[band] += 1
    company_updates.sort(key=lambda u: u["priority_score"], reverse=True)

    # --- contacts (own ×1.0, colleagues/company ×0.5)
    k_weights = spec["contact_weights"]
    colleague = float(spec["colleague_factor"])
    contact_updates, contact_tiers, skipped_contacts = [], {"now": 0, "week": 0, "nurture": 0}, 0
    queue_pool = []
    for contact in contacts:
        kid = _sid(contact.get("_id"))
        cid = _sid(contact.get("company_id"))
        if not kid or cid not in scored_companies:
            skipped_contacts += 1
            continue
        feats = [(f, 1.0 if f["contact_id"] == kid else colleague)
                 for f in by_company.get(cid, [])]
        fit = _num(scored_companies[cid].get("fit_score"), spec["default_fit"])
        heat = _fold_heat(feats, spec)
        persona = _persona_points(contact, spec)
        score = _clamp100(k_weights["fit"] * fit + k_weights["heat"] * heat
                          + k_weights["persona"] * persona)
        band = _tier(score, spec)
        evidence = _evidence(feats, spec)
        why_now = _why_now_draft(evidence, spec)
        contact_updates.append({
            "_id": contact.get("_id"),
            "priority_score": score,
            "priority_tier": band,
            "why_now": why_now,
            "why_now_evidence": json.dumps(evidence, ensure_ascii=False),
            "scored_at": today.isoformat(),
        })
        contact_tiers[band] += 1
        queue_pool.append({
            "contact_id": contact.get("_id"), "score": score, "tier": band,
            "name": str(contact.get("full_name") or "").strip(),
            "company": str(scored_companies[cid].get("name") or "").strip(),
            "why_now": why_now,
        })
    contact_updates.sort(key=lambda u: u["priority_score"], reverse=True)

    with open(out_companies, "w", encoding="utf-8") as f:
        json.dump(company_updates, f, ensure_ascii=False)
    with open(out_contacts, "w", encoding="utf-8") as f:
        json.dump(contact_updates, f, ensure_ascii=False)

    # --- the week queue: top-N contacts, hot tiers only, ready for db.py add
    queue_rows, queue_sample = [], []
    if queue:
        tier_order = {t: i for i, t in enumerate(spec["queue_tiers"])}
        pool = [q for q in queue_pool if q["tier"] in tier_order]
        pool.sort(key=lambda q: (tier_order[q["tier"]], -q["score"]))
        for q in pool[:queue]:
            queue_rows.append({"dedup_key": f"{week}:{q['contact_id']}",
                               "contact_id": q["contact_id"], "week": week,
                               "status": "draft"})
            queue_sample.append({"contact": q["name"], "company": q["company"],
                                 "score": q["score"], "tier": q["tier"]})
        with open(out_queue, "w", encoding="utf-8") as f:
            json.dump(queue_rows, f, ensure_ascii=False)

    receipt = {
        "ok": True,
        "today": today.isoformat(),
        "companies": {"scored": len(company_updates),
                      "notQualified": len(companies) - len(company_updates),
                      "tiers": company_tiers, "out": out_companies},
        "contacts": {"scored": len(contact_updates), "skipped": skipped_contacts,
                     "tiers": contact_tiers, "out": out_contacts},
        "signals": {"seen": len(signals), "unresolved": unresolved,
                    "outOfScope": out_of_scope},
        "samples": {"companies": [{k: u[k] for k in ("_id", "priority_score", "priority_tier", "why_now")}
                                  for u in company_updates[:3]],
                    "contacts": [{k: u[k] for k in ("_id", "priority_score", "priority_tier", "why_now")}
                                 for u in contact_updates[:3]]},
    }
    if unknown_types:
        receipt["signals"]["unknownTypes"] = unknown_types   # a writer bug — surface it
    if queue:
        receipt["queue"] = {"size": len(queue_rows), "week": week,
                            "out": out_queue, "samples": queue_sample[:3]}
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic signal-fusion scoring kernel (P5).")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run", help="score companies + contacts from the signals table")
    p.add_argument("--companies", required=True, help="db.py select payload / JSON array / JSONL")
    p.add_argument("--contacts", required=True, help="db.py select payload / JSON array / JSONL")
    p.add_argument("--signals", required=True, help="db.py select payload / JSON array / JSONL")
    p.add_argument("--spec", default=None, help="spec JSON (weights/thresholds); defaults baked in")
    p.add_argument("--out-companies", default="score_companies.updates.json",
                   help="JSON array for db.py modify companies --updates -")
    p.add_argument("--out-contacts", default="score_contacts.updates.json",
                   help="JSON array for db.py modify contacts --updates -")
    p.add_argument("--queue", type=int, default=0,
                   help="also emit the top-N contacts as outreach rows")
    p.add_argument("--week", default=None, help="ISO week for the queue (default: from --today)")
    p.add_argument("--out-queue", default="score_queue.json",
                   help="JSON array for db.py add outreach --rows - --key dedup_key")
    p.add_argument("--today", default=None, help="YYYY-MM-DD, for reproducible decay (default: today)")

    args = parser.parse_args(argv)
    t0 = time.perf_counter()
    try:
        if args.today:
            m = _DATE_RE.fullmatch(args.today.strip())
            if not m:
                raise ScoreError("--today must be YYYY-MM-DD")
            today = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        else:
            today = dt.date.today()
        result = run(args.companies, args.contacts, args.signals, args.spec,
                     args.out_companies, args.out_contacts,
                     args.queue, args.week, args.out_queue, today)
    except ScoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    result["elapsed_s"] = round(time.perf_counter() - t0, 3)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
