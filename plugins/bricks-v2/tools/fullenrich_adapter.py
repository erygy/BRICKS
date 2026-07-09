#!/usr/bin/env python3
"""fullenrich_adapter — enrichissement de contacts pour Bricks V2. Stdlib only.

Doc officielle (docs.fullenrich.com, OpenAPI complète, vérifiée 08/07/2026) :
  base   https://app.fullenrich.com/api/v2
  auth   Authorization: Bearer <clé>            (app.fullenrich.com/app/api)
  bulk   POST /contact/enrich/bulk              (max 100 contacts, ASYNC 30-90 s/contact)
  poll   GET  /contact/enrich/bulk/{id}         (déconseillé <5 min ; préférer webhook)
  hook   HMAC-SHA1 du body brut, secret = clé API, header X-Signature-SHA1,
         retries 1/min ×5 ; webhook_events.contact_finished = temps réel par contact
  crédits (débités SUR HIT uniquement) : email pro=1 · mobile=10 · email perso=3 ·
         search=0,25/résultat ; re-enrich <3 mois même inputs = gratuit
  limites 60 appels/min · 100 bulks concurrents/workspace
  solde  GET /account/credits · clé : GET /account/keys/verify

Doctrine V2 : n'enrichir QUE la bande IN (jamais BAND/OUT), persona de la thèse,
job ids persistés dans memory/state.json (jamais payer deux fois — règle V1 §8).

CLI :
  fullenrich_adapter.py verify                 # clé + solde
  fullenrich_adapter.py smoke                  # contact de test OFFICIEL = 0 crédit
  fullenrich_adapter.py enrich --in contacts.json [--fields work_emails]
  fullenrich_adapter.py poll --id <enrichment_id>
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.request

BASE = "https://app.fullenrich.com/api/v2"
ENV_FILE = os.path.expanduser("~/.bricks/env")

# Contact de test officiel, codé en dur côté FullEnrich : 0 crédit, parfait
# pour valider l'adapter de bout en bout AVANT de dépenser (Day-1, étape 1).
FREE_TEST_CONTACT = {"first_name": "Grégoire", "last_name": "Démogé",
                     "domain": "fullenrich.com", "company_name": "FullEnrich",
                     "linkedin_url": "https://www.linkedin.com/in/demoge/"}

FIELDS = {"work_emails": "contact.work_emails", "phones": "contact.phones",
          "personal_emails": "contact.personal_emails"}


def _key() -> str:
    k = os.environ.get("FULLENRICH_API_KEY")
    if not k and os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            if line.strip().startswith("FULLENRICH_API_KEY="):
                k = line.strip().split("=", 1)[1]
    if not k:
        raise SystemExit(json.dumps({"ok": False, "error":
            "FULLENRICH_API_KEY absent de ~/.bricks/env — Day-1 : app.fullenrich.com/app/api"}))
    return k


def _call(path: str, payload=None, method: str | None = None):
    method = method or ("POST" if payload is not None else "GET")
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # 402 (crédits) et 429 (rate limit, 60/min) sont GARANTIS d'arriver :
        # jamais un crash de batch — remonter structuré + Retry-After.
        body = e.read().decode(errors="replace")
        try:
            problem = json.loads(body)
        except json.JSONDecodeError:
            problem = {"raw": body[:400]}
        return {"ok": False, "status": e.code, "problem": problem,
                "retry_after": e.headers.get("Retry-After")}


def verify_webhook_signature(raw_body: bytes, header_sig: str) -> bool:
    """X-Signature-SHA1 = HMAC-SHA1(body brut, secret = clé API)."""
    expected = hmac.new(_key().encode(), raw_body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected, header_sig or "")


def enrich_bulk(contacts: list[dict], name: str, fields=("work_emails",),
                webhook_url: str | None = None) -> dict:
    if len(contacts) > 100:
        raise SystemExit(json.dumps({"ok": False, "error": "max 100 contacts/bulk — découper en vagues"}))
    data = []
    for c in contacts:
        row = {k: c[k] for k in ("first_name", "last_name", "domain", "company_name",
                                 "linkedin_url") if c.get(k)}
        row["enrich_fields"] = [FIELDS[f] for f in fields]
        if c.get("custom"):
            row["custom"] = c["custom"]   # ex. {"company_id": "...", "thesis": "..."} → revient dans le résultat
        data.append(row)
    payload = {"name": name, "data": data}
    if webhook_url:
        payload["webhook_url"] = webhook_url
        payload["webhook_events"] = {"contact_finished": True}
    return _call("/contact/enrich/bulk", payload)


def cmd_verify(_a):
    print(json.dumps({"key": _call("/account/keys/verify"),
                      "credits": _call("/account/credits")}, ensure_ascii=False, indent=2))


def cmd_smoke(_a):
    r = enrich_bulk([dict(FREE_TEST_CONTACT, custom={"purpose": "bricks-v2-smoke"})],
                    name="bricks-v2-smoke-test")
    print(json.dumps({"ok": True, "enrichment_id": r.get("enrichment_id"),
                      "next": "poll --id <enrichment_id> (attendre ≥1 min)",
                      "cout": "0 crédit (contact de test officiel)"}, ensure_ascii=False, indent=2))


def cmd_enrich(a):
    contacts = json.load(open(a.infile, encoding="utf-8"))
    r = enrich_bulk(contacts, name=a.name, fields=tuple(a.fields.split(",")),
                    webhook_url=a.webhook)
    print(json.dumps({"ok": True, "submitted": len(contacts),
                      "enrichment_id": r.get("enrichment_id"),
                      "rappel": "persister l'id dans memory/state.json (jamais payer deux fois)"},
                     ensure_ascii=False, indent=2))


def cmd_poll(a):
    print(json.dumps(_call(f"/contact/enrich/bulk/{a.id}"), ensure_ascii=False, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — adapter FullEnrich")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    sub.add_parser("smoke")
    p = sub.add_parser("enrich")
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--name", default="bricks-v2")
    p.add_argument("--fields", default="work_emails")
    p.add_argument("--webhook")
    p = sub.add_parser("poll"); p.add_argument("--id", required=True)
    a = ap.parse_args(argv)
    {"verify": cmd_verify, "smoke": cmd_smoke, "enrich": cmd_enrich, "poll": cmd_poll}[a.cmd](a)


if __name__ == "__main__":
    main()
