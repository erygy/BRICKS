#!/usr/bin/env python3
"""verdict — le moteur de verdict GTM de Bricks V2. Stdlib only, zéro LLM.

LA promesse : après une campagne, savoir si OUI ou NON la thèse est viable —
ou combien de contacts il manque pour trancher. Pas un dashboard : une
DÉCISION, avec son incertitude, calculée honnêtement.

Méthode (décision séquentielle bayésienne, codée, reproductible) :
  - chaque taux (réponse positive, RDV) est modélisé par un posterior
    Beta(a0+k, b0+n−k) ; prior faible Beta(1,19) ≈ « 5 % attendu, peu sûr » ;
  - VIABLE   si P(taux ≥ seuil_viable) ≥ conf_viable        (défaut 0,70)
  - NON_VIABLE si P(taux ≥ seuil_plancher) ≤ conf_kill ET n ≥ n_min
  - CONTINUE sinon — avec l'ESTIMATION DU N MANQUANT pour trancher
    (simulation : à taux courant constant, combien d'envois de plus ?).
  - Doctrine d'abstention : AUCUN pourcentage affiché sous n_abstention (25)
    — en dessous, on raisonne en événements bruts et en probabilités de
    seuil, jamais en « taux ».
  - Validation du SCORING lui-même : la bande IN doit battre le témoin BAND ;
    le verdict le teste (P(taux_IN > taux_témoin)) et le dit.

Le LEDGER : coûts réels saisis par étape → coût par contact joignable,
par réponse positive, par RDV — réels et projetés. C'est le chiffre que
personne d'autre n'a en live.

CLI :
  verdict.py assess --campaign campaign.json [--config verdict-config.json]
  verdict.py ledger --campaign campaign.json
  verdict.py demo
campaign.json : {"sent":N,"delivered":N,"replies":N,"replies_positive":N,
  "meetings":N,"clients":N, "control":{...mêmes champs, optionnel},
  "costs":{"fullenrich_credits":N,"api_eur":X,"human_hours":X, ...}}
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2ROOT = os.path.dirname(HERE)
DEFAULT_CONFIG = os.path.join(V2ROOT, "messaging", "verdict-config.json")

GRID = 2000  # intégration numérique du posterior Beta


# --------------------------------------------------------------------------
# Posterior Beta sans scipy : densité sur grille, normalisée
# --------------------------------------------------------------------------

def _beta_posterior(k: int, n: int, a0: float, b0: float):
    a, b = a0 + k, b0 + (n - k)
    xs = [(i + 0.5) / GRID for i in range(GRID)]
    logpdf = [(a - 1) * math.log(x) + (b - 1) * math.log(1 - x) for x in xs]
    m = max(logpdf)
    pdf = [math.exp(v - m) for v in logpdf]
    s = sum(pdf)
    return xs, [p / s for p in pdf]


def prob_rate_geq(k: int, n: int, threshold: float, a0=1.0, b0=19.0) -> float:
    xs, pdf = _beta_posterior(k, n, a0, b0)
    return sum(p for x, p in zip(xs, pdf) if x >= threshold)


def posterior_mean(k: int, n: int, a0=1.0, b0=19.0) -> float:
    return (a0 + k) / (a0 + b0 + n)


def prob_a_beats_b(ka, na, kb, nb, a0=1.0, b0=19.0, samples_grid=400) -> float:
    """P(taux_A > taux_B) par convolution de grilles (déterministe)."""
    xa, pa = _beta_posterior(ka, na, a0, b0)
    xb, pb = _beta_posterior(kb, nb, a0, b0)
    step = GRID // samples_grid
    xa, pa = xa[::step], pa[::step]
    xb, pb = xb[::step], pb[::step]
    sa, sb = sum(pa), sum(pb)
    pa = [p / sa for p in pa]
    pb = [p / sb for p in pb]
    cum_b, acc = [], 0.0
    for p in pb:
        acc += p
        cum_b.append(acc)
    return sum(pa[i] * cum_b[i] for i in range(len(pa)))


# --------------------------------------------------------------------------
# Le verdict
# --------------------------------------------------------------------------

def load_config(path: str | None) -> dict:
    p = path or DEFAULT_CONFIG
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    # défauts prudents (écrasés par verdict-config.json calibré par BUSINESS/GROWTH)
    return {
        "n_abstention": 25,
        "n_min_kill": 40,
        "positive_reply": {"viable": 0.05, "floor": 0.02},
        "meeting": {"viable": 0.03, "floor": 0.01},
        "conf_viable": 0.70, "conf_kill": 0.15,
        "prior": {"a0": 1.0, "b0": 19.0},
        "close_rate_assumed": 0.25,
        "note": "défauts internes — remplacés par les seuils BUSINESS/GROWTH",
    }


def _n_to_decide(k: int, n: int, threshold: float, conf: float, a0, b0,
                 max_extra: int = 400) -> int | None:
    """À taux courant constant, combien d'envois de plus pour VIABLE ?"""
    rate = max(posterior_mean(k, n, a0, b0), 1e-4)
    for extra in range(10, max_extra + 1, 10):
        k2 = k + rate * extra
        if prob_rate_geq(round(k2), n + extra, threshold, a0, b0) >= conf:
            return extra
    return None


def assess(campaign: dict, cfg: dict) -> dict:
    a0, b0 = cfg["prior"]["a0"], cfg["prior"]["b0"]
    n = campaign.get("delivered") or campaign.get("sent", 0)
    kp = campaign.get("replies_positive", 0)
    km = campaign.get("meetings", 0)
    out = {"n_contacts": n, "events": {"replies_positive": kp, "meetings": km,
                                       "clients": campaign.get("clients", 0)}}

    if n == 0:
        return {**out, "verdict": "PAS_DE_DONNEES",
                "explication": "aucun envoi délivré — rien à évaluer"}

    # métrique primaire = RDV ; secondaire = réponses positives
    metrics = {}
    for key, k in (("meeting", km), ("positive_reply", kp)):
        th = cfg[key]
        p_viable = prob_rate_geq(k, n, th["viable"], a0, b0)
        p_floor = prob_rate_geq(k, n, th["floor"], a0, b0)
        m = {"events": k,
             "P_taux_atteint_seuil_viable": round(p_viable, 3),
             "P_taux_au_dessus_du_plancher": round(p_floor, 3)}
        if n >= cfg["n_abstention"]:
            m["taux_posterior_moyen_pct"] = round(100 * posterior_mean(k, n, a0, b0), 1)
        else:
            m["taux"] = f"ABSTENTION (n={n} < {cfg['n_abstention']})"
        metrics[key] = m

    pv, pf = (metrics["meeting"]["P_taux_atteint_seuil_viable"],
              metrics["meeting"]["P_taux_au_dessus_du_plancher"])
    pv2 = metrics["positive_reply"]["P_taux_atteint_seuil_viable"]

    # règle événementielle BUSINESS (complément du bayésien, codée telle quelle) :
    # N cumulé ≥ n_min_kill avec 0 RDV et ≤1 réponse positive = falsification.
    kill_event_rule = (n >= cfg["n_min_kill"] and km == 0 and kp <= 1)

    if pv >= cfg["conf_viable"] or (km >= 3 and pv2 >= cfg["conf_viable"]):
        verdict, expl = "SIGNAL_VIABLE", (
            "le taux de RDV a une probabilité suffisante d'atteindre le seuil de "
            "viabilité — la thèse tient, passer à l'échelle de la vague suivante")
    elif kill_event_rule or (pf <= cfg["conf_kill"] and pv2 <= cfg["conf_kill"]
                             and n >= cfg["n_min_kill"]):
        verdict, expl = "NON_VIABLE", (
            "falsification honnête : quasi-absence de signal après un échantillon "
            "suffisant (règle : ≥{} contacts, 0 RDV, ≤1 réponse positive). NON ne "
            "tue pas le produit — il tue CE motion (canal/message/cible) : pivot "
            "de canal (prescripteur), d'axe ou de persona".format(cfg["n_min_kill"]))
    else:
        extra = _n_to_decide(km, n, cfg["meeting"]["viable"], cfg["conf_viable"], a0, b0)
        verdict = "CONTINUE"
        expl = ("pas encore tranchable — au rythme courant, il faudrait environ "
                f"{extra if extra else '>400'} contacts de plus pour un verdict VIABLE ; "
                "chaque réponse recale le calcul")
        out["n_supplementaires_estimes"] = extra

    out.update({"verdict": verdict, "explication": expl, "metrics": metrics})

    # validation du scoring : IN doit battre le témoin
    ctl = campaign.get("control")
    if ctl and (ctl.get("delivered") or ctl.get("sent")):
        nc = ctl.get("delivered") or ctl.get("sent")
        p_beat = prob_a_beats_b(kp, n, ctl.get("replies_positive", 0), nc, a0, b0)
        out["validation_scoring"] = {
            "P_bande_IN_bat_temoin": round(p_beat, 3),
            "lecture": ("le scoring cible juste" if p_beat >= 0.8 else
                        "pas encore discriminant — plus de données ou poids à recaler"
                        if p_beat >= 0.5 else
                        "ALERTE : le témoin fait mieux que la bande IN — les poids mentent")}

    # projection économique
    if km > 0 and n >= cfg["n_abstention"]:
        close = cfg.get("close_rate_assumed", 0.25)
        out["projection"] = {
            "hypothese_close_rate": close,
            "clients_projetes_pour_100_contacts":
                round(100 * posterior_mean(km, n, a0, b0) * close, 2),
            "note": "projection = posterior RDV × close supposé — à remplacer par le réel dès le premier cycle de vente",
        }
    return out


# --------------------------------------------------------------------------
# Le ledger
# --------------------------------------------------------------------------

def ledger(campaign: dict, cfg: dict) -> dict:
    c = campaign.get("costs", {})
    fe_eur = c.get("fullenrich_credits", 0) * c.get("eur_per_credit", 0.20)
    api_eur = c.get("api_eur", 0.0)
    human_eur = c.get("human_hours", 0.0) * c.get("eur_per_hour", 50.0)
    total = round(fe_eur + api_eur + human_eur, 2)
    out = {"couts": {"fullenrich_eur": round(fe_eur, 2), "api_eur": api_eur,
                     "humain_eur": round(human_eur, 2), "total_eur": total}}
    n = campaign.get("delivered") or campaign.get("sent", 0)
    kp, km = campaign.get("replies_positive", 0), campaign.get("meetings", 0)
    if n:
        out["cout_par_contact_delivre"] = round(total / n, 2)
    if kp:
        out["cout_par_reponse_positive"] = round(total / kp, 2)
    if km:
        out["cout_par_rdv"] = round(total / km, 2)
        close = cfg.get("close_rate_assumed", 0.25)
        out["cout_par_client_projete"] = round(total / (km * close), 2)
    out["comparaison"] = cfg.get("cost_baselines", {
        "clay_seat_mois_eur": "~800 (149-800$/mois + crédits)",
        "agence_prospection_rdv_eur": "150-400 / RDV",
        "sdr_temps_plein_mois_eur": "4500-6000 chargé",
    })
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_demo(_a):
    cfg = load_config(None)
    print("— Scénario 1 : vague 1 prometteuse (60 envoyés, 5 rép. positives, 3 RDV, témoin 20/0)")
    camp = {"sent": 60, "delivered": 57, "replies_positive": 5, "meetings": 3,
            "control": {"sent": 20, "delivered": 19, "replies_positive": 0},
            "costs": {"fullenrich_credits": 70, "eur_per_credit": 0.20,
                      "api_eur": 4.0, "human_hours": 3, "eur_per_hour": 50}}
    print(json.dumps(assess(camp, cfg), ensure_ascii=False, indent=2))
    print(json.dumps(ledger(camp, cfg), ensure_ascii=False, indent=2))
    print("\n— Scénario 2 : silence radio (60 envoyés, 0 réponse)")
    print(json.dumps(assess({"sent": 60, "delivered": 55, "replies_positive": 0,
                             "meetings": 0}, cfg), ensure_ascii=False, indent=2))
    print("\n— Scénario 3 : trop tôt (15 envoyés, 1 réponse positive)")
    print(json.dumps(assess({"sent": 15, "delivered": 15, "replies_positive": 1,
                             "meetings": 0}, cfg), ensure_ascii=False, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — moteur de verdict GTM")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("assess", "ledger"):
        p = sub.add_parser(name)
        p.add_argument("--campaign", required=True)
        p.add_argument("--config")
    sub.add_parser("demo")
    args = ap.parse_args(argv)
    if args.cmd == "demo":
        return cmd_demo(args)
    cfg = load_config(args.config)
    camp = json.load(open(args.campaign, encoding="utf-8"))
    fn = assess if args.cmd == "assess" else ledger
    print(json.dumps(fn(camp, cfg), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
