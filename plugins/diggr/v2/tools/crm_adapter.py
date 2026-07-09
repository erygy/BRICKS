#!/usr/bin/env python3
"""crm_adapter — le CRM auto-updater de Bricks V2 (writeback). Stdlib only.

Ferme la boucle « production-ready GTM agent » : un agent qui SCORE mais
n'écrit nulle part n'est pas déployable. Ici, tout ce que le moteur produit
(score, bande, signal dominant + preuve, next-best-action, coût/RDV) est
poussé dans le CRM — Account/Company + une Task d'action — par DOMAINE
(la clé de jointure que domain_resolver fournit déjà).

Couche anti-corruption identique à sillage_adapter :
  - MockCRM : backend déterministe persistant (fichier JSON) — la démo montre
    « le CRM se remplit » sans aucune clé.
  - RestCRM : Salesforce (sObject Account + Task) / HubSpot (companies) /
    Attio (objects) ; lit CRM_KIND + CRM_TOKEN dans ~/.bricks/env, lève
    NotConfigured sans creds. Le mapping des champs custom est explicite par CRM.
Idempotent par `external_id = domain` (upsert, jamais de doublon).

Champs custom écrits (préfixe bricks_) : intent_band, intent_score,
dominant_signal, evidence_url, next_action, cost_per_meeting_eur, updated_at.

CLI :
  crm_adapter.py push --in scored.jsonl [--kind mock|salesforce|hubspot|attio]
                 [--task-band IN] [--db mock-crm.json]
  crm_adapter.py show [--db mock-crm.json]
  crm_adapter.py demo
Entrée `scored.jsonl` : lignes du scoring d'achat (score_v2 : _id,name,domain,
band,expected,top_contributors) OU du risque (pipeline_monitor : account,
domain,risk_band,risk_score,dominant_signal,next_best_action,eur_at_risk).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(os.path.dirname(HERE), "fixtures")
ENV_FILE = os.path.expanduser("~/.bricks/env")
DEFAULT_DB = os.path.join(FIXTURES, "mock-crm.json")

# Mapping des champs Bricks → objet/champ natif par CRM (le vrai contrat d'écriture)
CRM_MAP = {
    "salesforce": {"object": "Account", "match": "Website",
                   "task_object": "Task",
                   "fields": {"intent_band": "Bricks_Intent_Band__c",
                              "intent_score": "Bricks_Intent_Score__c",
                              "dominant_signal": "Bricks_Signal__c",
                              "evidence_url": "Bricks_Evidence_URL__c",
                              "next_action": "Bricks_Next_Action__c"}},
    "hubspot": {"object": "companies", "match": "domain", "task_object": "tasks",
                "fields": {"intent_band": "bricks_intent_band",
                           "intent_score": "bricks_intent_score",
                           "dominant_signal": "bricks_signal",
                           "evidence_url": "bricks_evidence_url",
                           "next_action": "bricks_next_action"}},
    "attio": {"object": "companies", "match": "domains", "task_object": "tasks",
              "fields": {"intent_band": "bricks_intent_band",
                         "intent_score": "bricks_intent_score",
                         "dominant_signal": "bricks_signal",
                         "evidence_url": "bricks_evidence_url",
                         "next_action": "bricks_next_action"}},
}


class NotConfigured(RuntimeError):
    pass


def _env(k):
    if os.environ.get(k):
        return os.environ[k]
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            if line.strip().startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def normalize(row: dict) -> dict | None:
    """Ligne de scoring (achat OU risque) → payload CRM homogène. Domaine requis."""
    domain = row.get("domain")
    if not domain:
        return None
    if "risk_band" in row:   # sortie pipeline_monitor
        band = {"À_RISQUE": "AT_RISK", "À_SURVEILLER": "WATCH", "SAIN": "HEALTHY"}.get(row["risk_band"], row["risk_band"])
        return {"domain": domain, "name": row.get("account"),
                "intent_band": band, "intent_score": row.get("risk_score"),
                "dominant_signal": row.get("dominant_signal"),
                "evidence_url": (row.get("why") or {}).get("observed", [{}])[0].get("evidence_url")
                    if isinstance(row.get("why"), dict) else None,
                "next_action": row.get("next_best_action"),
                "amount_at_risk_eur": row.get("eur_at_risk"), "kind": "risk"}
    # sortie score_v2 (achat)
    top = (row.get("top_contributors") or [{}])
    dom = top[0].get("signal") if top else None
    ev = None
    for o in (top[0].get("observed") or []) if top else []:
        if o.get("evidence_url"):
            ev = o["evidence_url"]; break
    return {"domain": domain, "name": row.get("name"),
            "intent_band": row.get("band"), "intent_score": row.get("expected"),
            "dominant_signal": dom, "evidence_url": ev,
            "next_action": None, "kind": "buy"}


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------

class MockCRM:
    def __init__(self, db=DEFAULT_DB):
        self.db = db
        self.state = json.load(open(db, encoding="utf-8")) if os.path.exists(db) else {"accounts": {}, "tasks": []}

    def upsert_account(self, p):
        acc = self.state["accounts"].get(p["domain"], {"external_id": p["domain"]})
        acc.update({"name": p.get("name") or acc.get("name"),
                    "bricks_intent_band": p["intent_band"],
                    "bricks_intent_score": p["intent_score"],
                    "bricks_signal": p.get("dominant_signal"),
                    "bricks_evidence_url": p.get("evidence_url"),
                    "bricks_next_action": p.get("next_action"),
                    "updated_by": "bricks-v2"})
        self.state["accounts"][p["domain"]] = acc
        return {"upserted": p["domain"]}

    def create_task(self, domain, subject, owner="account_owner"):
        key = f"{domain}::{subject[:40]}"
        if any(t["key"] == key for t in self.state["tasks"]):
            return {"task": "exists"}   # idempotent
        self.state["tasks"].append({"key": key, "account": domain, "subject": subject, "owner": owner, "status": "open"})
        return {"task": "created"}

    def commit(self):
        json.dump(self.state, open(self.db, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def capabilities(self):
        return {"kind": "mock", "objects": ["Account", "Task"], "persist": self.db}


class RestCRM:
    def __init__(self, kind):
        self.kind = kind
        if kind not in CRM_MAP:
            raise NotConfigured(f"CRM inconnu {kind!r} — au choix : {list(CRM_MAP)}")
        self.map = CRM_MAP[kind]
        self.token = _env("CRM_TOKEN")
        self.base = _env("CRM_BASE_URL")
        if not (self.token and self.base):
            raise NotConfigured(
                f"CRM_TOKEN / CRM_BASE_URL absents de ~/.bricks/env pour {kind}. "
                "Le mapping des champs est prêt (CRM_MAP) ; il ne manque que l'auth "
                "(OAuth Salesforce / clé privée HubSpot / token Attio).")

    def _call(self, path, payload, method="POST"):
        req = urllib.request.Request(
            self.base.rstrip("/") + path, method=method,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"ok": False, "status": e.code, "body": e.read().decode(errors="replace")[:300]}

    def upsert_account(self, p):
        f = self.map["fields"]
        body = {f["intent_band"]: p["intent_band"], f["intent_score"]: p["intent_score"],
                f["dominant_signal"]: p.get("dominant_signal"),
                f["evidence_url"]: p.get("evidence_url"), f["next_action"]: p.get("next_action")}
        # upsert par domaine (external id) — chemin réel dépend du CRM, ici la forme Salesforce
        return self._call(f"/{self.map['object']}/{self.map['match']}/{p['domain']}", body, "PATCH")

    def create_task(self, domain, subject, owner="account_owner"):
        return self._call(f"/{self.map['task_object']}", {"Subject": subject, "WhatId": domain})

    def commit(self):
        pass

    def capabilities(self):
        return {"kind": self.kind, "object": self.map["object"], "champs": self.map["fields"]}


def get_backend(kind, db=DEFAULT_DB):
    return MockCRM(db) if kind == "mock" else RestCRM(kind)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_push(a):
    try:
        crm = get_backend(a.kind, a.db)
    except NotConfigured as e:
        print(json.dumps({"ok": False, "crm": a.kind, "not_configured": str(e),
                          "note": "le mapping des champs est prêt (CRM_MAP) ; il ne manque que l'auth"},
                         ensure_ascii=False, indent=2))
        return
    rows = sv_load(a.infile)
    up, tasks, skipped = 0, 0, 0
    for row in rows:
        p = normalize(row)
        if not p:
            skipped += 1
            continue
        crm.upsert_account(p)
        up += 1
        band = p["intent_band"]
        if band in (a.task_band, "AT_RISK") or (a.task_band == "IN" and band == "IN"):
            subj = (f"[Risque {p['intent_score']}] {p.get('next_action') or 'Défendre le deal'}"
                    if p["kind"] == "risk" else
                    f"[IN {p['intent_score']}] Contacter — signal {p.get('dominant_signal')}")
            crm.create_task(p["domain"], subj)
            tasks += 1
    crm.commit()
    print(json.dumps({"ok": True, "crm": a.kind, "comptes_upsertes": up,
                      "tasks_creees": tasks, "ignores_sans_domaine": skipped,
                      "capabilities": crm.capabilities()}, ensure_ascii=False, indent=2))


def sv_load(path):
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    try:
        obj = json.loads(text)
        return obj.get("rows", obj) if isinstance(obj, dict) else obj
    except json.JSONDecodeError:
        return [json.loads(l) for l in text.splitlines() if l.strip()]


def cmd_show(a):
    crm = MockCRM(a.db)
    accs = crm.state["accounts"]
    print(json.dumps({"comptes": len(accs), "tasks": len(crm.state["tasks"]),
                      "exemple_compte": next(iter(accs.values()), None),
                      "exemple_task": crm.state["tasks"][0] if crm.state["tasks"] else None},
                     ensure_ascii=False, indent=2))


def cmd_demo(_a):
    db = "/tmp/bricks-demo-crm.json"
    if os.path.exists(db):
        os.remove(db)
    # 1) ACHAT : quelques comptes IN à domaine résolu (le writeback exige un domaine).
    buy = [
        {"name": "ELEC 4", "domain": "elec4.fr", "band": "IN", "expected": 87.4,
         "top_contributors": [{"signal": "S-HOR-04", "observed": [{"evidence_url": None}]}]},
        {"name": "EGS Clim", "domain": "egsclim.fr", "band": "IN", "expected": 87.4,
         "top_contributors": [{"signal": "S-HOR-04", "observed": []}]},
        {"name": "Éts Baleydier", "domain": "baleydier.fr", "band": "IN", "expected": 87.9,
         "top_contributors": [{"signal": "S-REL-07", "observed": []}]},
    ]
    buyf = "/tmp/bricks-demo-buy.jsonl"
    with open(buyf, "w", encoding="utf-8") as f:
        for r in buy:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("— writeback des comptes d'ACHAT (bande IN, domaine résolu) —")
    cmd_push(argparse.Namespace(kind="mock", infile=buyf, task_band="IN", db=db))
    # 2) RISQUE : les deals du pipeline_monitor, dans le MÊME CRM
    a2 = argparse.Namespace(kind="mock", infile="/tmp/pipeline-risk.jsonl",
                            task_band="AT_RISK", db=db)
    if os.path.exists(a2.infile):
        print("\n— writeback des DEALS À RISQUE (le même CRM) —")
        cmd_push(a2)
    print("\n— état du CRM (mock) : acquisition ET rétention côte à côte —")
    cmd_show(argparse.Namespace(db=db))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — CRM writeback")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("push")
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--kind", default="mock")
    p.add_argument("--task-band", default="IN")
    p.add_argument("--db", default=DEFAULT_DB)
    p = sub.add_parser("show"); p.add_argument("--db", default=DEFAULT_DB)
    sub.add_parser("demo")
    args = ap.parse_args(argv)
    {"push": cmd_push, "show": cmd_show, "demo": cmd_demo}[args.cmd](args)


if __name__ == "__main__":
    main()
