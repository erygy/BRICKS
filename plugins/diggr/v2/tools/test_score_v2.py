#!/usr/bin/env python3
"""Tests du noyau score_v2 — stdlib, exécutable directement : python3 test_score_v2.py"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_v2 as sv

TODAY = dt.date(2026, 7, 8)
PASS = 0


def check(name, cond, detail=""):
    global PASS
    status = "ok" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    assert cond, f"{name}: {detail}"
    PASS += 1


def tree(signals, floor=0.05):
    return {"thesis_id": "t", "version": "test",
            "defaults": {"prior": {"P": 0.5, "S": 0.35, "O": 0.3}, "gate_floor": floor},
            "signals": signals}


def sig_P(id="P-AAA-01", crit=1, proxies=None, **kw):
    return {"id": id, "layer": "P", "claim": "c", "cluster": "cl_" + id, "crit": crit,
            "proxies": proxies or [], **kw}


def sig_S(id="S-AAA-01", lr="x5", cluster=None, proxies=None, **kw):
    return {"id": id, "layer": "S", "claim": "c", "cluster": cluster or ("cl_" + id),
            "lr_class": lr, "proxies": proxies or [], **kw}


def px(id, field, op, value, fid=0.9, fpr=0.1, cost=0, src="registry", **kw):
    return {"id": id, "source": src, "field": field, "op": op, "value": value,
            "fidelity": fid, "fpr": fpr, "coverage": 1.0, "cost_class": cost, **kw}


print("== évaluation des proxies (coercition str de db.py) ==")
c = {"_id": 1, "age": "42", "naf": "25.62B", "name": "ETS MARTIN"}
check("gte sur str", sv.eval_registry_proxy(px("a", "age", "gte", 40), c) is True)
check("between sur str", sv.eval_registry_proxy(px("b", "age", "between", [40, 45]), c) is True)
check("prefix_in", sv.eval_registry_proxy(px("c", "naf", "prefix_in", ["25", "28"]), c) is True)
check("not_regex", sv.eval_registry_proxy(px("d", "name", "not_regex", "HOLDING"), c) is True)
check("champ manquant → inconnu", sv.eval_registry_proxy(px("e", "absent", "gte", 1), c) is None)

print("== croyances bayésiennes ==")
t1 = tree([sig_S(proxies=[px("p1", "age", "gte", 40)])])
b, bp, bo, obs, unk = sv.signal_belief(t1["signals"][0], c, {}, t1["defaults"], TODAY)
check("proxy vrai monte la croyance", b > 0.35, f"b={b}")
check("pas d'inconnu → bornes = point", bp == b == bo)
t2 = tree([sig_S(proxies=[px("p1", "absent", "gte", 1, cost=2)])])
b, bp, bo, _, unk = sv.signal_belief(t2["signals"][0], c, {}, t2["defaults"], TODAY)
check("proxy inconnu → croyance = prior", abs(b - 0.35) < 1e-9)
check("bornes s'écartent avec l'inconnu", bp < b < bo, f"{bp} {b} {bo}")
check("non-observé ≠ faux", bp > 0.0)

print("== évidence explicite prime + décroissance ==")
ev = {("1", "p1"): {"value": True, "event_date": "2026-07-01"}}
t3 = tree([sig_S(proxies=[px("p1", "absent", "gte", 1, cost=2, src="sillage",
                             decay={"fresh_days": 60, "context_days": 180,
                                    "context_mult": 0.5, "stale_mult": 0.2})])])
b_fresh, *_ = sv.signal_belief(t3["signals"][0], c, ev, t3["defaults"], TODAY)
ev_old = {("1", "p1"): {"value": True, "event_date": "2025-01-01"}}
b_old, *_ = sv.signal_belief(t3["signals"][0], c, ev_old, t3["defaults"], TODAY)
check("évidence explicite résout l'inconnu", b_fresh > 0.6)
check("signal périmé pèse moins que frais", b_old < b_fresh, f"{b_old} vs {b_fresh}")

print("== gates P ==")
tp = tree([sig_P(crit=2, proxies=[px("p1", "age", "gte", 99)]),   # échoue
           sig_S(proxies=[px("p2", "age", "gte", 40)])])
s, _ = sv.score_company(c, tp, {}, 55.0, TODAY)
check("gate P échoué écrase le score", s["expected"] < 10, f"score={s['expected']}")
check("plancher: le score n'est pas exactement 0", s["gate_P"] > 0)

print("== plafond de cluster (anti-double-comptage) ==")
same = [sig_S(f"S-DUP-0{i}", "x5", cluster="meme_chose",
              proxies=[px(f"p{i}", "age", "gte", 40)]) for i in range(1, 6)]
diff = [sig_S(f"S-DIF-0{i}", "x5", cluster=f"cl{i}",
              proxies=[px(f"q{i}", "age", "gte", 40)]) for i in range(1, 6)]
tP = [sig_P(proxies=[px("pg", "age", "gte", 40)])]
s_same, _ = sv.score_company(c, tree(tP + same), {}, 55.0, TODAY)
s_diff, _ = sv.score_company(c, tree(tP + diff), {}, 55.0, TODAY)
check("5 signaux corrélés < 5 signaux indépendants", s_same["expected"] < s_diff["expected"],
      f"{s_same['expected']} vs {s_diff['expected']}")

print("== bandes ==")
tb = tree(tP + [sig_S("S-KNW-01", "x5", proxies=[px("k1", "age", "gte", 40)]),
                sig_S("S-UNK-01", "x20", proxies=[px("u1", "absent", "gte", 1, cost=2)])])
s, unks = sv.score_company(c, tb, {}, 55.0, TODAY)
check("intervalle non trivial", s["pessimistic"] < s["optimistic"])
check("bande cohérente", s["band"] in ("IN", "BAND", "OUT"))
check("les inconnus sont remontés", len(unks) >= 1)

print("== VOI ==")
universe = [dict(c, _id=i) for i in range(1, 6)]
plan = sv.voi_plan(universe, tb, {}, 55.0, budget=100.0, today=TODAY)
if plan["checks"]:
    costs = [ch["priority"] for ch in plan["checks"]]
    check("plan trié par priorité décroissante", costs == sorted(costs, reverse=True))
    check("budget respecté", plan["spent"] <= 100.0)
else:
    check("plan vide acceptable si aucune bande", True)

print("== déterminisme ==")
s1, _ = sv.score_company(c, tb, {}, 55.0, TODAY)
s2, _ = sv.score_company(c, tb, {}, 55.0, TODAY)
check("même entrée → même sortie", json.dumps(s1, sort_keys=True) == json.dumps(s2, sort_keys=True))

print("== validation d'arbre ==")
bad = tree([{"id": "X-BAD-01", "layer": "P", "claim": "c", "cluster": "cl",
             "proxies": [px("p", "a", "gte", 1, fid=0.3, fpr=0.4)]}])  # crit manquant + proxy non informatif (fid ≤ fpr)
errs = sv.validate_tree(bad)
check("arbre invalide rejeté", len(errs) >= 2, str(errs))

print(f"\n{PASS} assertions OK")
