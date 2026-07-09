#!/usr/bin/env python3
"""P1 sourcing import — FullEnrich companies CSV → table `companies`.

The ONE sourcing path (§6): a CSV lands on disk (FullEnrich MCP
`export_companies`, or any companies CSV), this script normalizes it into
the contract columns, stages the cleaned file in the workspace `staging/`,
then feeds it through the only door (`db.import_csv`, dedup `--key domain`).

Contract writes (CLAUDE.md, table companies — l'inserteur, c'est ici) :
    name, domain, linkedin_url        identity (domain normalized, REQUIRED —
                                      no resolved domain, no row, ever)
    headcount, industry, geo          static firmo only (dynamic = Sillage)
    source                            'fullenrich_search' (--source overrides)
    qualify_status                    'pending' armed AT INSERT (same P2 gate
                                      for every inserter)

Usage:
    python3 seed/import_p1.py --csv staging/fullenrich_export.csv
    python3 seed/import_p1.py --csv export.csv \
        --map "domain=Website,name=Company Name,headcount=Employees"

Header auto-detection covers the usual FullEnrich/Clay/CRM spellings;
--map target=Header wins over detection. Unmapped CSV columns are IGNORED
(listed in the receipt) — the contract is a closed column list.

CLI JSON receipt on stdout; errors JSON on stderr + exit 1.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys

_CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "tools", "core")
sys.path.insert(0, os.path.abspath(_CORE))
import db as dbmod  # noqa: E402

#: normalized header spellings → contract column
CANDIDATES = {
    "name": ["name", "company_name", "company", "organization", "org_name"],
    "domain": ["domain", "website", "company_domain", "primary_domain",
               "website_url", "site", "web_site"],
    "linkedin_url": ["linkedin_url", "linkedin", "company_linkedin_url",
                     "linkedin_company_url", "company_linkedin"],
    "headcount": ["headcount", "employees", "employee_count",
                  "number_of_employees", "company_size", "size",
                  "headcount_range", "staff_count"],
    "industry": ["industry", "industries", "sector", "vertical"],
    "geo": ["geo", "country", "location", "city", "region", "hq_country",
            "headquarters", "hq_location", "company_country"],
}

FIELDS = ["name", "domain", "linkedin_url", "headcount", "industry", "geo",
          "source", "qualify_status"]


def _norm_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (header or "").strip().lower()).strip("_")


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


def _build_mapping(headers: list[str], overrides: dict) -> tuple[dict, list]:
    """contract column → actual CSV header (overrides win), + ignored headers."""
    normalized = {_norm_header(h): h for h in headers}
    mapping: dict[str, str] = {}
    for target, spellings in CANDIDATES.items():
        if target in overrides:
            if overrides[target] not in headers:
                raise dbmod.DbError(
                    f"--map {target}={overrides[target]!r} : colonne absente "
                    f"du CSV (en-têtes : {', '.join(headers[:12])})")
            mapping[target] = overrides[target]
            continue
        for spelling in spellings:
            if spelling in normalized:
                mapping[target] = normalized[spelling]
                break
    used = set(mapping.values())
    return mapping, [h for h in headers if h not in used]


def import_p1(csv_path: str, mapping_arg: str | None = None,
              source: str = "fullenrich_search", out: str | None = None,
              db: str | None = None, root: str | None = None) -> dict:
    path = dbmod.resolve(db, root or "bricks")
    overrides = {}
    for pair in (mapping_arg or "").split(","):
        if pair.strip():
            target, _, header = pair.partition("=")
            if target.strip() not in CANDIDATES:
                raise dbmod.DbError(f"--map : cible inconnue {target.strip()!r} "
                                    f"(attendu : {', '.join(CANDIDATES)})")
            overrides[target.strip()] = header.strip()

    if not os.path.isfile(csv_path):
        raise dbmod.DbError(f"CSV introuvable : {csv_path}")
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if not headers:
            raise dbmod.DbError(f"CSV sans ligne d'en-tête : {csv_path}")
        mapping, ignored = _build_mapping(headers, overrides)
        if "domain" not in mapping:
            raise dbmod.DbError(
                "aucune colonne domaine détectée — passe "
                f"--map \"domain=<en-tête>\" (en-têtes : {', '.join(headers[:12])})")
        staged_rows, skipped_no_domain, samples = [], 0, []
        for raw in reader:
            domain = _norm_domain(raw.get(mapping["domain"]))
            if not domain:
                skipped_no_domain += 1      # pas de domaine = pas de ligne
                continue
            row = {"name": (raw.get(mapping.get("name", ""), "") or "").strip(),
                   "domain": domain,
                   "linkedin_url": _norm_linkedin(
                       raw.get(mapping.get("linkedin_url", ""), "")),
                   "headcount": (raw.get(mapping.get("headcount", ""), "")
                                 or "").strip(),
                   "industry": (raw.get(mapping.get("industry", ""), "")
                                or "").strip(),
                   "geo": (raw.get(mapping.get("geo", ""), "") or "").strip(),
                   "source": source,
                   "qualify_status": "pending"}
            staged_rows.append(row)
            if len(samples) < 3:
                samples.append(f"{row['name'] or '?'} — {domain}")
    if not staged_rows:
        raise dbmod.DbError("0 ligne avec domaine résolu — rien à importer")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    staged = out or os.path.join(os.path.dirname(path), "staging",
                                 f"p1_import_{stamp}.csv")
    os.makedirs(os.path.dirname(staged), exist_ok=True)
    with open(staged, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(staged_rows)

    result = dbmod.import_csv(path, "companies", staged, key="domain")
    return {"ok": True, "read": len(staged_rows) + skipped_no_domain,
            "skippedNoDomain": skipped_no_domain,
            "staged": staged,
            "added": result.get("added", 0),
            "skippedDuplicates": result.get("skippedDuplicates", 0),
            "tableRows": result.get("rows"),
            "ignoredColumns": ignored or None,
            "samples": samples,
            "next": "porte P2 : qualification runner --ai (voir /surveil)"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Import P1 : CSV companies (FullEnrich) → table companies.")
    parser.add_argument("--csv", required=True, help="CSV source sur disque")
    parser.add_argument("--map", default=None, dest="mapping",
                        help='surcharges "cible=En-tête,…" '
                             "(cibles : name,domain,linkedin_url,headcount,"
                             "industry,geo)")
    parser.add_argument("--source", default="fullenrich_search")
    parser.add_argument("--out", default=None,
                        help="chemin du CSV stagé (défaut : staging/ du workspace)")
    parser.add_argument("--db", default=None)
    parser.add_argument("--root", default=None)
    args = parser.parse_args(argv)
    try:
        out = import_p1(args.csv, args.mapping, args.source, args.out,
                        args.db, args.root)
    except dbmod.DbError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
