#!/usr/bin/env python3
"""score_v2 — le noyau de scoring signal-natif de Bricks V2.

Déterministe, stdlib uniquement, fichier-entrant → fichier-sortant (jamais la
base directement : lire les lignes et committer les résultats sont des étapes
db.py séparées, comme rank.py/score.py en V1). Même entrée + même arbre →
même sortie, pour toujours.

Modèle (voir ARCHITECTURE.md §3) :
  - signaux LATENTS en 3 couches (P gates doux multiplicatifs · S évidence
    log-vraisemblance plafonnée par cluster · O bonus borné ≤ 5) ;
  - chaque signal porte des PROXIES observables (fidélité, taux de faux
    positifs, couverture, coût) ; croyance mise à jour en odds bayésiens ;
  - non-observé = AUCUNE mise à jour (jamais assimilé à faux) ;
  - trois scores par entreprise : pessimiste ≤ attendu ≤ optimiste — bornes
    obtenues en résolvant, PAR SIGNAL, le proxy inconnu le plus décisif
    (modélise « une vérification de plus », la granularité réelle du VOI) ;
  - bandes : IN (pessimiste ≥ seuil) · OUT (optimiste < seuil) · BAND (le
    budget de vérification ne se dépense QUE là) ;
  - file de repêchage : gate P effondré mais évidence S extraordinaire
    → revue humaine (détecte les thèses trop étroites).

CLI :
  score_v2.py check  --tree tree.json [--universe u.jsonl]
  score_v2.py run    --tree tree.json --universe u.jsonl [--evidence e.jsonl]
                     [--threshold 55] [--out scores.jsonl]
  score_v2.py voi    --tree tree.json --universe u.jsonl [--evidence e.jsonl]
                     [--threshold 55] [--budget 100] [--out plan.json]
  score_v2.py demo   (fixtures MemoVAL : univers réel du field-test 08/07)

Formats d'entrée : JSONL, tableau JSON, ou payload `db.py select` ({"rows":[…]}).
Evidence JSONL : {"company_id":…, "proxy_id":…, "value":true|false,
                  "event_date":"YYYY-MM-DD"?, "evidence_url":…?}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(os.path.dirname(HERE), "fixtures")

LR_CLASSES = {"x1.2": 1.2, "x2": 2.0, "x5": 5.0, "x20": 20.0}
COST_WEIGHT = {0: 0.5, 1: 1.0, 2: 3.0, 3: 10.0}   # unités de budget par vérification
O_BONUS_MAX = 5.0
# Échelle ABSOLUE en nats : 2 nats d'évidence nette (LR cumulé ≈ 7,4) = 50 %.
# Ne dépend PAS de la taille de l'arbre — un arbre de 1000 signaux dont 990
# inconnus ne s'auto-écrase pas (l'inconnu contribue 0 par construction).
SQUASH_K = 1.2          # pente de la logistique (par nat)
SQUASH_THETA = 2.0      # centre de la logistique (nats d'évidence nette)
SALVAGE_GATE = 0.20     # gate P attendu sous ce niveau …
SALVAGE_EVIDENCE = 2.5  # … mais ≥ 2,5 nats d'évidence S → repêchage
# Sémantique de la NÉCESSITÉ : un gate P sature à 1 dès que la croyance atteint
# GATE_TARGET (« suffisamment sûr ») — on ne multiplie PAS des probabilités
# imparfaites entre elles, sinon cinq proxies moyens (b≈0,8 chacun) puniraient
# à 0,33 une entreprise qui remplit très probablement TOUTES les conditions.
GATE_TARGET = 0.70
# Un signal S observé FAUX ne punit pas comme un gate (red-team A1) : la
# nécessité vit dans la couche P. La contribution négative d'un S est amortie —
# on garde l'information d'ordre (faux < inconnu < vrai) sans écraser un
# prospect valide sous des « typiques-mais-pas-nécessaires ».
S_NEG_DAMP = 0.30


# --------------------------------------------------------------------------
# Chargement
# --------------------------------------------------------------------------

def load_rows(path: str) -> list[dict]:
    """JSONL, tableau JSON, ou payload db.py select ({'rows': [...]})."""
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "rows" in obj:
            return obj["rows"]
        if isinstance(obj, list):
            return obj
        return [obj]
    except json.JSONDecodeError:
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows


def load_tree(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        tree = json.load(f)
    errs = validate_tree(tree)
    if errs:
        raise SystemExit(json.dumps({"ok": False, "tree_errors": errs}, ensure_ascii=False))
    return tree


def validate_tree(tree: dict) -> list[str]:
    errs = []
    if not tree.get("thesis_id"):
        errs.append("thesis_id manquant")
    seen = set()
    for s in tree.get("signals", []):
        sid = s.get("id", "?")
        if sid in seen:
            errs.append(f"{sid}: id dupliqué")
        seen.add(sid)
        layer = s.get("layer")
        if layer not in ("P", "S", "O"):
            errs.append(f"{sid}: layer invalide {layer!r}")
        if layer == "P" and s.get("crit") not in (1, 2):
            errs.append(f"{sid}: P sans crit ∈ {{1,2}}")
        if layer in ("S", "O") and s.get("lr_class") not in LR_CLASSES:
            errs.append(f"{sid}: {layer} sans lr_class valide")
        if not s.get("cluster"):
            errs.append(f"{sid}: cluster manquant")
        if not s.get("proxies") and not s.get("unobservable_question"):
            errs.append(f"{sid}: ni proxy ni unobservable_question")
        for p in s.get("proxies", []):
            fid, fpr = p.get("fidelity"), p.get("fpr")
            # fidélité = SENSIBILITÉ P(observé|acheteur) : peut être basse pour un
            # événement rare. L'exigence est l'INFORMATIVITÉ : fidelity > fpr.
            if not (isinstance(fid, (int, float)) and 0.02 <= fid <= 0.99):
                errs.append(f"{sid}/{p.get('id')}: fidelity hors [0.02,0.99]")
            if not (isinstance(fpr, (int, float)) and 0.005 <= fpr <= 0.5):
                errs.append(f"{sid}/{p.get('id')}: fpr hors [0.005,0.5]")
            if isinstance(fid, (int, float)) and isinstance(fpr, (int, float)) and fid <= fpr:
                errs.append(f"{sid}/{p.get('id')}: fidelity ≤ fpr (proxy sans information)")
            if p.get("cost_class") not in (0, 1, 2, 3):
                errs.append(f"{sid}/{p.get('id')}: cost_class hors 0-3")
    return errs


# --------------------------------------------------------------------------
# Évaluation des proxies
# --------------------------------------------------------------------------

def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def eval_registry_proxy(proxy: dict, company: dict):
    """→ True / False / None (inconnu). Les cellules db.py arrivent en str."""
    field = proxy.get("field")
    raw = company.get(field)
    if raw is None or raw == "":
        return None
    op, val = proxy.get("op"), proxy.get("value")
    s = str(raw)
    if op == "gte":
        n = _num(raw); return None if n is None else n >= val
    if op == "lte":
        n = _num(raw); return None if n is None else n <= val
    if op == "between":
        n = _num(raw); return None if n is None else (val[0] <= n <= val[1])
    if op == "eq":
        n, m = _num(raw), _num(val)
        return (n == m) if (n is not None and m is not None) else (s == str(val))
    if op == "neq":
        n, m = _num(raw), _num(val)
        return (n != m) if (n is not None and m is not None) else (s != str(val))
    if op == "in":
        n = _num(raw)
        if n is not None and all(_num(v) is not None for v in val):
            return n in [_num(v) for v in val]
        return s in [str(v) for v in val]
    if op == "not_in":
        r = eval_registry_proxy({**proxy, "op": "in"}, company)
        return None if r is None else not r
    if op == "prefix_in":
        return any(s.startswith(str(v)) for v in val)
    if op == "not_prefix_in":
        return not any(s.startswith(str(v)) for v in val)
    if op == "regex":
        return re.search(val, s, re.I) is not None
    if op == "not_regex":
        return re.search(val, s, re.I) is None
    if op == "exists":
        return True
    return None


def decay_mult(proxy: dict, event_date: str | None, today: dt.date) -> float:
    d = proxy.get("decay")
    if not d or not event_date:
        return 1.0
    try:
        age = max(0, (today - dt.date.fromisoformat(event_date[:10])).days)
    except ValueError:
        return 1.0
    if age <= d.get("fresh_days", 60):
        return 1.0
    if age <= d.get("context_days", 180):
        return float(d.get("context_mult", 0.5))
    return float(d.get("stale_mult", 0.2))


# --------------------------------------------------------------------------
# Croyances par signal
# --------------------------------------------------------------------------

def _odds(p): return p / (1.0 - p)
def _prob(o): return o / (1.0 + o)


def signal_belief(signal: dict, company: dict, evidence: dict, defaults: dict,
                  today: dt.date):
    """Retourne (b_expected, b_pess, b_opt, observed[], unknown_proxies[]).

    Mise à jour bayésienne en odds. Bornes = résolution du proxy INCONNU le
    plus décisif (|log LR| max), à faux (pess) ou à vrai (opt).
    """
    layer = signal["layer"]
    prior = signal.get("prior", defaults.get("prior", {}).get(layer, 0.35))
    o = _odds(prior)
    observed, unknowns = [], []
    for p in signal.get("proxies", []):
        if p.get("status") == "absent":
            continue
        val, ev_date, url = None, None, None
        if p["source"] == "registry":
            val = eval_registry_proxy(p, company)
        key = (str(company.get("_id")), p["id"])
        if key in evidence:                       # l'évidence explicite PRIME
            e = evidence[key]
            ev_val = e.get("value")               # jamais d'accès direct sur
            if ev_val is not None:                # de la donnée externe (B1)
                val, ev_date, url = bool(ev_val), e.get("event_date"), e.get("evidence_url")
        if val is None:
            unknowns.append(p)
            continue
        m = decay_mult(p, ev_date, today)
        lr = (p["fidelity"] / p["fpr"]) if val else ((1 - p["fidelity"]) / (1 - p["fpr"]))
        o *= lr ** m
        observed.append({"proxy_id": p["id"], "value": val, "lr_applied": round(lr ** m, 3),
                         "evidence_url": url})
    b = _prob(o)
    b_pess, b_opt = b, b
    if unknowns:
        # Bornes = « UNE vérification de plus » : le proxy inconnu le plus
        # décisif du signal, résolu à faux (pess) / vrai (opt) — avec son LR
        # PONDÉRÉ PAR LA COUVERTURE (red-team A3 : un jackpot x20 qui n'est
        # mesurable que chez 5 % des candidats ne peut pas promettre 100 à
        # tout le monde ; une boîte vide ne survit plus en BAND par magie).
        # Tie-break déterministe sur l'id (indépendant de l'ordre JSON).
        best = max(unknowns, key=lambda p: (abs(math.log(p["fidelity"] / p["fpr"])), p["id"]))
        cov = max(0.05, min(1.0, best.get("coverage", 1.0)))
        b_pess = _prob(o * ((1 - best["fidelity"]) / (1 - best["fpr"])) ** cov)
        b_opt = _prob(o * (best["fidelity"] / best["fpr"]) ** cov)
    return b, b_pess, b_opt, observed, unknowns


# --------------------------------------------------------------------------
# Score d'une entreprise
# --------------------------------------------------------------------------

def build_clusters(tree: dict):
    caps = {}
    for s in tree["signals"]:
        if s["layer"] != "S" or s.get("status") == "killed":
            continue
        w = math.log(LR_CLASSES[s["lr_class"]])
        cl = s["cluster"]
        caps[cl] = max(caps.get(cl, 0.0), w)
    return {cl: 1.5 * w for cl, w in caps.items()}   # plafond anti-double-comptage


def score_company(company: dict, tree: dict, evidence: dict, threshold: float,
                  today: dt.date):
    defaults = tree.get("defaults", {})
    floor_default = defaults.get("gate_floor", 0.05)
    caps = build_clusters(tree)

    gate = {"e": 1.0, "p": 1.0, "o": 1.0}
    s_ev = {"e": {}, "p": {}, "o": {}}   # par cluster
    o_ev = {"e": 0.0, "p": 0.0, "o": 0.0}
    o_cap = 0.0
    contributors, unknown_checks, questions = [], [], []
    min_gate_expected = 1.0

    for sig in tree["signals"]:
        if sig.get("status") == "killed":
            continue
        if not sig.get("proxies") and sig.get("unobservable_question"):
            questions.append({"signal": sig["id"], "ask": sig["unobservable_question"]})
            continue
        b, bp, bo, obs, unk = signal_belief(sig, company, evidence, defaults, today)
        for p in unk:
            unknown_checks.append({"signal": sig, "proxy": p,
                                   "belief_now": b})
        layer = sig["layer"]
        prior = sig.get("prior", defaults.get("prior", {}).get(layer, 0.35))
        if layer == "P":
            fl, crit = sig.get("gate_floor", floor_default), sig.get("crit", 1)
            def _g(bb):
                return max(fl, min(1.0, (bb / GATE_TARGET) ** crit))
            gate["e"] *= _g(b)
            gate["p"] *= _g(bp)
            gate["o"] *= _g(bo)
            min_gate_expected = min(min_gate_expected, b)
            contributors.append({"signal": sig["id"], "layer": "P", "belief": round(b, 3),
                                 "observed": obs})
        elif layer == "S":
            # Contribution RELATIVE AU PRIOR : un signal non observé (b=prior)
            # contribue exactement 0 — un arbre géant plein d'inconnus reste
            # neutre. Contribution négative AMORTIE (S_NEG_DAMP) : un S faux
            # informe sans jamais punir comme un gate (red-team A1/E2).
            w = math.log(LR_CLASSES[sig["lr_class"]])
            cl = sig["cluster"]
            def _contrib(bb):
                c = w * 2.0 * (bb - prior)
                return c if c >= 0 else c * S_NEG_DAMP
            for k, bb in (("e", b), ("p", bp), ("o", bo)):
                s_ev[k][cl] = s_ev[k].get(cl, 0.0) + _contrib(bb)
            contributors.append({"signal": sig["id"], "layer": "S", "cluster": cl,
                                 "belief": round(b, 3), "w": round(w, 3),
                                 "contribution": round(_contrib(b), 3),
                                 "observed": obs})
        else:  # O
            w = math.log(LR_CLASSES[sig["lr_class"]])
            o_cap += w
            for k, bb in (("e", b), ("p", bp), ("o", bo)):
                o_ev[k] += w * max(0.0, 2.0 * (bb - prior))

    def _final(k):
        # Plafond par cluster (anti-double-comptage), puis échelle ABSOLUE en nats.
        e_s = sum(max(-caps[cl], min(caps[cl], v)) for cl, v in s_ev[k].items())
        core = 100.0 * gate[k] / (1.0 + math.exp(-SQUASH_K * (e_s - SQUASH_THETA)))
        bonus = O_BONUS_MAX * min(1.0, o_ev[k] / o_cap) if o_cap else 0.0
        return max(0.0, min(100.0, core + bonus)), e_s

    exp_score, e_nats = _final("e")
    pess_score, _ = _final("p")
    opt_score, _ = _final("o")
    pess_score, opt_score = min(pess_score, exp_score), max(opt_score, exp_score)

    n_observed = sum(len(c.get("observed", [])) for c in contributors)
    if n_observed == 0:
        band = "OUT"   # aucune donnée observée : pas de pari (boîte vide ≠ BAND)
    elif pess_score >= threshold:
        band = "IN"
    elif opt_score < threshold:
        band = "OUT"
    else:
        band = "BAND"
    salvage = (min_gate_expected < SALVAGE_GATE and e_nats >= SALVAGE_EVIDENCE)

    top = sorted((c for c in contributors if c["layer"] == "S"),
                 key=lambda c: -abs(c.get("contribution", 0)))[:3]
    return {
        "_id": company.get("_id"), "name": company.get("name"),
        "thesis_id": tree["thesis_id"], "tree_version": tree.get("version"),
        "pessimistic": round(pess_score, 1), "expected": round(exp_score, 1),
        "optimistic": round(opt_score, 1), "band": band, "salvage": salvage,
        "gate_P": round(gate["e"], 4), "evidence_S_nats": round(e_nats, 3),
        "top_contributors": top, "qualification_questions": questions,
    }, unknown_checks


# --------------------------------------------------------------------------
# VOI — plan de vérification pour la bande d'incertitude
# --------------------------------------------------------------------------

def voi_plan(universe, tree, evidence, threshold, budget, today):
    """Plan de vérification DÉCISION-FIRST (red-team C2/E3) : un check n'entre
    au plan que s'il peut faire CHANGER DE BANDE (flips ≥ 1) ; priorité =
    flips dominant, départagé par l'ampleur, divisé par le coût. Périmètre =
    bande d'incertitude + file de repêchage (A6/E5 : le salvage est routé,
    pas juste flaggé). Ne mute JAMAIS l'évidence partagée (B2)."""
    plan = []
    for c in universe:
        base, unknowns = score_company(c, tree, evidence, threshold, today)
        if base["band"] != "BAND" and not base["salvage"]:
            continue
        for u in unknowns:
            p = u["proxy"]
            key = (str(c.get("_id")), p["id"])
            if key in evidence:
                continue                      # déjà vérifié : pas un inconnu
            ev2 = dict(evidence)              # copie — jamais de del sur l'original
            ev2[key] = {"value": True}
            s_true, _ = score_company(c, tree, ev2, threshold, today)
            ev2[key] = {"value": False}
            s_false, _ = score_company(c, tree, ev2, threshold, today)
            flips = int(s_true["band"] != base["band"]) + int(s_false["band"] != base["band"])
            spread = abs(s_true["expected"] - s_false["expected"])
            cost = COST_WEIGHT[p["cost_class"]]
            if flips == 0:
                continue                      # pas de décision en jeu → pas un centime
            plan.append({
                "company_id": c.get("_id"), "company": c.get("name"),
                "signal": u["signal"]["id"], "proxy_id": p["id"],
                "source": p["source"], "capability": p.get("capability"),
                "cost": cost, "decision_flips": flips,
                "score_spread": round(spread, 1),
                "salvage_review": base["salvage"],
                "priority": round((flips * 10.0 + spread / 25.0) / cost, 3),
            })
    plan.sort(key=lambda x: (-x["priority"], str(x["proxy_id"])))
    kept, spent = [], 0.0
    for item in plan:
        if spent + item["cost"] > budget:
            continue
        spent += item["cost"]
        kept.append(item)
    return {"budget": budget, "spent": round(spent, 1), "checks": kept,
            "dropped": len(plan) - len(kept)}


# --------------------------------------------------------------------------
# Identifiabilité
# --------------------------------------------------------------------------

def identifiability(scores: list[dict]) -> dict:
    n = len(scores) or 1
    hi = sum(1 for s in scores if s["expected"] > 80)
    lo = sum(1 for s in scores if s["expected"] < 20)
    bands = {}
    for s in scores:
        bands[s["band"]] = bands.get(s["band"], 0) + 1
    verdict = "ok"
    if hi / n > 0.30:
        verdict = "TROP LÂCHE — >30% des candidats scorent >80 : resserrer les poids ou le seuil"
    elif (hi + bands.get("IN", 0)) == 0:
        verdict = "TROP STRICT — personne ne passe : la thèse est-elle testable sur cet univers ?"
    elif bands.get("IN", 0) == 0:
        verdict = "ATTENTION — 0 IN : les bornes pessimistes ne se ferment pas ; vérifier les proxies P inconnus avant de dépenser"
    return {"n": n, "share_gt80": round(hi / n, 3), "share_lt20": round(lo / n, 3),
            "bands": bands, "verdict": verdict}


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------

def load_evidence(path: str | None) -> dict:
    """Robuste aux payloads externes sales : une ligne sans company_id/proxy_id/
    value est SAUTÉE (comptée), jamais un crash de batch (red-team B1)."""
    ev, skipped = {}, 0
    if not path:
        return ev
    for row in load_rows(path):
        cid, pid, val = row.get("company_id"), row.get("proxy_id"), row.get("value")
        if cid is None or pid is None or val is None:
            skipped += 1
            continue
        ev[(str(cid), pid)] = {"value": bool(val),
                               "event_date": row.get("event_date"),
                               "evidence_url": row.get("evidence_url")}
    if skipped:
        print(json.dumps({"warning": f"{skipped} lignes d'évidence invalides ignorées"}),
              file=sys.stderr)
    return ev


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_run(args):
    tree = load_tree(args.tree)
    universe = load_rows(args.universe)
    evidence = load_evidence(args.evidence)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    scores = []
    for c in universe:
        s, _ = score_company(c, tree, evidence, args.threshold, today)
        scores.append(s)
    scores.sort(key=lambda s: -s["expected"])
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for s in scores:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
    ident = identifiability(scores)
    receipt = {"ok": True, "action": "run", "thesis": tree["thesis_id"],
               "scored": len(scores), "threshold": args.threshold,
               "identifiability": ident,
               "out": args.out}
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return scores


def cmd_voi(args):
    tree = load_tree(args.tree)
    universe = load_rows(args.universe)
    evidence = load_evidence(args.evidence)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    plan = voi_plan(universe, tree, evidence, args.threshold, args.budget, today)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, "action": "voi", "budget": plan["budget"],
                      "spent": plan["spent"], "planned_checks": len(plan["checks"]),
                      "dropped_low_value": plan["dropped"], "out": args.out},
                     ensure_ascii=False, indent=2))


def cmd_check(args):
    tree = load_tree(args.tree)   # valide déjà
    n_sig = len(tree["signals"])
    layers = {}
    legal = [s["id"] for s in tree["signals"] if s.get("legal_flag")]
    unobs = [s["id"] for s in tree["signals"] if not s.get("proxies")]
    n_proxies = sum(len(s.get("proxies", [])) for s in tree["signals"])
    warnings = []
    for s in tree["signals"]:
        layers[s["layer"]] = layers.get(s["layer"], 0) + 1
        for p in s.get("proxies", []):
            # fidélité = SENSIBILITÉ P(observé|acheteur), pas la précision.
            # Un proxy rare (couverture faible) ne peut pas être vu chez 90 %
            # des acheteurs — sinon son absence écrase injustement le score.
            if p.get("fidelity", 0) > p.get("coverage", 1) + 0.05:
                warnings.append(f"{s['id']}/{p['id']}: fidelity {p['fidelity']} > coverage "
                                f"{p['coverage']} — confusion précision/sensibilité probable")
    out = {"ok": True, "action": "check", "thesis": tree["thesis_id"],
           "signals": n_sig, "proxies": n_proxies, "layers": layers,
           "clusters": len({s['cluster'] for s in tree['signals']}),
           "legal_flags_a_lever_par_CRITIC": legal,
           "inobservables_devenus_questions": unobs,
           "warnings": warnings}
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_demo(args):
    args.tree = os.path.join(FIXTURES, "memoval-signals.json")
    args.universe = os.path.join(FIXTURES, "mock-universe.jsonl")
    ev_path = os.path.join(FIXTURES, "demo-evidence.jsonl")
    args.evidence = ev_path if os.path.exists(ev_path) else None
    args.threshold, args.out, args.today = 55.0, "/tmp/bricks-v2-demo-scores.jsonl", None
    scores = cmd_run(args)
    print("\n=== TOP 12 (attendu [pessimiste-optimiste] · bande) ===")
    for s in scores[:12]:
        print(f"  {s['expected']:5.1f}  [{s['pessimistic']:5.1f}-{s['optimistic']:5.1f}]"
              f"  {s['band']:4}  {s['name'][:44]}")
    diso = [s for s in scores if s["salvage"]]
    print(f"\nrepêchage (gate mort mais évidence forte): {len(diso)}")
    args.budget = 60.0
    args.out = "/tmp/bricks-v2-demo-voi.json"
    cmd_voi(args)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — scoring signal-natif")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "voi", "check", "demo"):
        p = sub.add_parser(name)
        if name != "demo":
            p.add_argument("--tree", required=True)
        if name in ("run", "voi"):
            p.add_argument("--universe", required=True)
            p.add_argument("--evidence")
            p.add_argument("--threshold", type=float, default=55.0)
            p.add_argument("--today")
            p.add_argument("--out")
        if name == "voi":
            p.add_argument("--budget", type=float, default=100.0)
    args = ap.parse_args(argv)
    {"run": cmd_run, "voi": cmd_voi, "check": cmd_check, "demo": cmd_demo}[args.cmd](args)


if __name__ == "__main__":
    main()
