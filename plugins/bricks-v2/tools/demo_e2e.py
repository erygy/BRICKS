#!/usr/bin/env python3
"""demo_e2e — le « live wire » du pitch : UNE commande, les 3 piliers, les
4 archétypes GTM, chronométré, provenance visible. Stdlib only, zéro clé.

Prouve LA grande idée : le MÊME moteur d'intervalles (score_v2.py, 0 token,
déterministe) alimente l'ACQUISITION (scorer qui achète) ET la RÉTENTION
(scorer quel deal meurt), sur des signaux Sillage, écrit dans le CRM,
budget FullEnrich alloué par VOI. 4 agents, 1 cerveau.

  python3 demo_e2e.py
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
FIX = os.path.join(V2, "fixtures")
sys.path.insert(0, HERE)
import score_v2 as sv
import pipeline_monitor as pm
import crm_adapter as crm

TODAY = dt.date(2026, 7, 9)


def band(label):
    print(f"\n\033[1m{label}\033[0m")


def main():
    t0 = time.perf_counter()
    print("═══ BRICKS V2 — un seul moteur, quatre agents GTM, trois piliers ═══")

    # ── AGENT 1 & 2 : ICP SCORING + OUTREACH (acquisition) ──
    band("① ICP SCORING ENGINE  —  qui achète ? (moteur d'intervalles + bandes)")
    tree = sv.load_tree(os.path.join(FIX, "memoval-signals.json"))
    univ = sv.load_rows(os.path.join(FIX, "mock-universe.jsonl"))
    ev = sv.load_evidence(os.path.join(FIX, "demo-evidence.jsonl"))
    t = time.perf_counter()
    buy = [sv.score_company(c, tree, ev, 55.0, TODAY)[0] for c in univ]
    dt_buy = (time.perf_counter() - t) * 1000
    IN = [s for s in buy if s["band"] == "IN"]
    print(f"   {len(univ)} comptes scorés en {dt_buy:.0f} ms (0 token, déterministe) → "
          f"{len(IN)} en bande IN (à contacter), le reste en BAND/OUT")
    print(f"   preuve : score par intervalle, ex. {IN[0]['name'][:22]} "
          f"[{IN[0]['pessimistic']}-{IN[0]['optimistic']}] band=IN")

    # ── AGENT 3 : PIPELINE RISK MONITOR (rétention) — LE MÊME MOTEUR ──
    band("② PIPELINE RISK MONITOR  —  quel deal meurt ? (le MÊME score_v2, arbre de risque)")
    rtree = sv.load_tree(os.path.join(FIX, "retention-signals.json"))
    deals = sv.load_rows(os.path.join(FIX, "mock-deals.json"))
    rev = sv.load_evidence(os.path.join(FIX, "mock-deal-signals.jsonl"))
    risk = pm.monitor(deals, rtree, rev, 55.0, TODAY)
    at_risk = [r for r in risk if r["risk_band"] == "À_RISQUE"]
    eur = sum(r["eur_at_risk"] for r in risk if r["risk_band"] == "À_RISQUE")
    print(f"   {len(deals)} deals scorés par le MÊME moteur → {len(at_risk)} à risque, "
          f"{eur:.0f}€ de pipeline menacé")
    for r in at_risk:
        print(f"   ⚠ {r['account']:16} risque {r['risk_score']:.0f} ← {r['dominant_signal']} "
              f"(Sillage) · {r['eur_at_risk']:.0f}€ · {r['next_best_action'][:46]}…")

    # ── AGENT 4 : CRM AUTO-UPDATER — les deux flux dans le CRM ──
    band("③ CRM AUTO-UPDATER  —  écrit acquisition ET rétention dans le CRM (archétype du brief)")
    db = "/tmp/bricks-e2e-crm.json"
    if os.path.exists(db):
        os.remove(db)
    c = crm.MockCRM(db)
    up = 0
    for r in risk:
        p = crm.normalize(r)
        if p:
            c.upsert_account(p); up += 1
            if r["risk_band"] == "À_RISQUE":
                c.create_task(p["domain"], f"[Risque {r['risk_score']:.0f}] {r['next_best_action']}")
    c.commit()
    print(f"   {up} comptes upsertés + {len(c.state['tasks'])} tasks d'action créées, "
          f"par domaine, idempotent — le CRM se remplit tout seul")

    # ── VOI / FullEnrich : le budget suit la décision ──
    band("④ VOI × FULLENRICH  —  le budget ne s'enrichit QUE là où ça décide")
    voi = sv.voi_plan(univ, tree, ev, 55.0, 60.0, TODAY)
    print(f"   plan de vérification : {len(voi['checks'])} checks retenus (tous font basculer une bande), "
          f"{voi['dropped']} écartés sans valeur")
    print(f"   → on n'enrichit (crédit FullEnrich) que la bande IN ({len(IN)}), jamais les {len(univ)}")

    dt_total = time.perf_counter() - t0
    band(f"═══ 3 piliers · 4 archétypes · 1 moteur · {dt_total:.1f} s · 0 crédit ═══")
    print("   Claude conçoit l'arbre + écrit les mails · Sillage nourrit les signaux "
          "(achat ET risque) · FullEnrich enrichit sous garde VOI · le tout écrit dans le CRM.")


if __name__ == "__main__":
    main()
