#!/usr/bin/env python3
"""pipeline_monitor — le 4e archétype GTM : moniteur de risque de pipeline.
LA PREUVE de « un seul moteur, l'autre sens du cycle de vie » : ce fichier
n'a PAS de moteur à lui — il RÉUTILISE score_v2.score_company (le même code
déterministe, testé, 0 token) pointé sur l'arbre de RISQUE (retention-signals)
au lieu de l'arbre d'achat. IN/BAND/OUT devient à-risque / à-surveiller / sain.

Nourri des signaux Sillage que l'arbre d'acquisition n'utilisait pas :
champion (job change), competitor (engagement), job_update, customer, +
leadership/M&A (web). Le VOI répond à « quel deal vérifier en priorité ».

Sortie par deal : risk band, € À RISQUE (montant × risque), le signal
dominant sourcé (avec date/URL), et la NEXT BEST ACTION. Prêt pour le
CRM writeback (crm_adapter) et pour un routing d'alerte.

CLI :
  pipeline_monitor.py run --deals deals.json --tree retention-signals.json
                      [--evidence signals.jsonl] [--threshold 55] [--out risk.jsonl]
  pipeline_monitor.py voi --deals … --tree … [--budget 40]
  pipeline_monitor.py demo
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(os.path.dirname(HERE), "fixtures")
sys.path.insert(0, HERE)
import score_v2 as sv  # LE MÊME MOTEUR — réutilisé, pas réécrit

# Bande de score → sémantique de risque + action, par signal dominant
BAND_TO_RISK = {"IN": "À_RISQUE", "BAND": "À_SURVEILLER", "OUT": "SAIN"}
NEXT_ACTION = {
    "S-CHAMP-01": "Sponsor perdu — identifier et enrôler un nouveau champion cette semaine (multi-thread).",
    "S-COMP-01": "Engagement concurrent — déclencher un call de défense + partager le comparatif différenciant.",
    "S-INACT-01": "Deal muet — relance de ré-engagement avec un angle neuf (valeur, pas 'on relance').",
    "S-LEAD-01": "Nouveau décideur — obtenir une intro, re-vendre la valeur au nouvel arrivant.",
    "S-MA-01": "M&A en cours — geler la prévision, cartographier le nouveau décideur post-deal.",
    "S-SILENT-01": "Silence produit — alerter le CS : QBR + plan d'adoption avant le renouvellement.",
}


def _load(path):
    return sv.load_rows(path) if path else []


def monitor(deals, tree, evidence, threshold, today):
    out = []
    for d in deals:
        # score_v2 attend une "company" ; un deal EST une company enrichie de contexte deal.
        s, unknowns = sv.score_company(d, tree, evidence, threshold, today)
        risk = BAND_TO_RISK[s["band"]]
        amount = 0.0
        try:
            amount = float(d.get("amount_eur") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        # € à risque = montant × probabilité de slip (score attendu /100)
        eur_at_risk = round(amount * s["expected"] / 100.0, 0)
        top = s.get("top_contributors") or []
        dom = top[0]["signal"] if top else None
        out.append({
            "deal_id": d.get("_id"), "account": d.get("name"),
            "domain": d.get("domain"), "stage": d.get("stage"),
            "amount_eur": amount, "risk_band": risk,
            "risk_score": s["expected"], "risk_interval": [s["pessimistic"], s["optimistic"]],
            "eur_at_risk": eur_at_risk,
            "dominant_signal": dom,
            "why": (top[0] if top else {}),
            "next_best_action": NEXT_ACTION.get(dom, "Surveiller — pas de signal de risque net.")
                if risk != "SAIN" else "RAS — compte sain, maintenir le rythme.",
            "unknowns": len(unknowns),
        })
    # tri : à-risque d'abord, puis par € à risque décroissant
    order = {"À_RISQUE": 0, "À_SURVEILLER": 1, "SAIN": 2}
    out.sort(key=lambda x: (order[x["risk_band"]], -x["eur_at_risk"]))
    return out


def summary(rows):
    from collections import Counter
    bands = Counter(r["risk_band"] for r in rows)
    at_risk_eur = sum(r["eur_at_risk"] for r in rows if r["risk_band"] == "À_RISQUE")
    return {"deals": len(rows), "bandes": dict(bands),
            "eur_total_a_risque": round(at_risk_eur, 0)}


def cmd_run(a):
    tree = sv.load_tree(a.tree)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    ev = sv.load_evidence(a.evidence)
    rows = monitor(_load(a.deals), tree, ev, a.threshold, today)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": True, "action": "run", **summary(rows), "out": a.out},
                     ensure_ascii=False, indent=2))
    return rows


def cmd_voi(a):
    tree = sv.load_tree(a.tree)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    ev = sv.load_evidence(a.evidence)
    plan = sv.voi_plan(_load(a.deals), tree, ev, a.threshold, a.budget, today)
    print(json.dumps({"ok": True, "action": "voi", "spent": plan["spent"],
                      "checks": [{"deal": c["company"], "signal": c["signal"],
                                  "source": c["source"], "flips": c["decision_flips"]}
                                 for c in plan["checks"][:10]],
                      "dropped": plan["dropped"]}, ensure_ascii=False, indent=2))


def cmd_demo(_a):
    a = argparse.Namespace(
        deals=os.path.join(FIXTURES, "mock-deals.json"),
        tree=os.path.join(FIXTURES, "retention-signals.json"),
        evidence=os.path.join(FIXTURES, "mock-deal-signals.jsonl"),
        threshold=55.0, today="2026-07-09", out="/tmp/pipeline-risk.jsonl")
    rows = cmd_run(a)
    print("\n=== deals par risque (le même moteur que le scoring d'achat) ===")
    for r in rows:
        print(f"  {r['risk_band']:14} {r['account'][:26]:26} {r['risk_score']:5.1f}  "
              f"{r['eur_at_risk']:>8.0f}€ à risque  ← {r['dominant_signal'] or '—'}")
        if r["risk_band"] != "SAIN":
            print(f"       action: {r['next_best_action']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — moniteur de risque de pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "voi"):
        p = sub.add_parser(name)
        p.add_argument("--deals", required=True)
        p.add_argument("--tree", required=True)
        p.add_argument("--evidence")
        p.add_argument("--threshold", type=float, default=55.0)
        p.add_argument("--today")
        if name == "run":
            p.add_argument("--out")
        else:
            p.add_argument("--budget", type=float, default=40.0)
    sub.add_parser("demo")
    args = ap.parse_args(argv)
    {"run": cmd_run, "voi": cmd_voi, "demo": cmd_demo}[args.cmd](args)


if __name__ == "__main__":
    main()
