#!/usr/bin/env python3
"""messaging_factory — la fabrique de messages V2 (bout de chaîne). Stdlib only.

Implémente le schéma DONNÉES → AXES → (× FORMAT) → BASE → RESSOURCES →
PROMPT SUR MESURE → LLM « je sais écrire un mail » → MAIL :

  DONNÉES     Le TABLEAU : colonnes sur mesure = les SIGNAUX CLÉS choisis
              judicieusement (fréquence × poids × couche parmi les top
              contributeurs de la population cible). Une colonne par signal
              clé + `signal_cle` (dominant) + `axe` (groupe). Écrites dans
              companies via db.py → visibles/groupables dans l'UI Bricks.
  AXES        Pré-groupement DÉTERMINISTE par signal dominant (ici), puis
              l'agent AXE-MAPPER (Opus 4.8) nomme/fusionne les axes et écrit
              le PROMPT D'AXE (skill prompt-smith-outreach).
  FORMAT      messaging/FORMATS.md — les supports de prospection (email
              premier contact, relance, breakup, DM, invite, mini-audit).
  BASE        AXE × FORMAT : brief réutilisable par segment et par support.
  RESSOURCES  Par entreprise : synthèse des données DISPONIBLES du tableau
              (faits observés + URLs + fraîcheur, inconnues → questions).
  PROMPT      BASE + RESSOURCES + offre/voix → prompt final pour le LLM②
              (skill email-craft). La génération reste au LLM ; TOUT le
              reste est du code rejouable.

CLI :
  messaging_factory.py select-key-signals --scores S --tree T [--max 8]
  messaging_factory.py materialize --scores S --tree T --universe U
                       [--evidence E] [--key-signals K] --out updates.json
  messaging_factory.py axes-prep --materialized M --out groups.json
  messaging_factory.py resources --materialized M --tree T --universe U
                       [--evidence E] [--band IN] --out resources.jsonl
  messaging_factory.py compile-prompt --axes A --formats F --resources R
                       --company-id X --format-id F1 [--offer O] [--voice V]
  messaging_factory.py demo
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(V2ROOT, "fixtures")
MESSAGING = os.path.join(V2ROOT, "messaging")

sys.path.insert(0, HERE)
import score_v2 as sv  # noqa: E402 — réutilise le chargement + croyances


def _rows(path):
    return sv.load_rows(path)


def _sig_index(tree):
    return {s["id"]: s for s in tree["signals"]}


# --------------------------------------------------------------------------
# 1. SIGNAUX CLÉS — le choix judicieux des colonnes du tableau
# --------------------------------------------------------------------------

def select_key_signals(scores: list[dict], tree: dict, max_cols: int = 8) -> dict:
    """Un signal est CLÉ s'il décide réellement dans la population cible :
    score = fréquence d'apparition en top-contributeur (IN + BAND haut)
            × poids de classe × bonus de couche (P=×1,25 : un gate raconte
            le segment ; O=×0,6 : accroche, rarement un axe).
    """
    idx = _sig_index(tree)
    target = [s for s in scores if s["band"] == "IN" or
              (s["band"] == "BAND" and s["expected"] >= 50)]
    freq, contrib = {}, {}
    for s in target:
        for c in s.get("top_contributors", []):
            freq[c["signal"]] = freq.get(c["signal"], 0) + 1
            contrib[c["signal"]] = contrib.get(c["signal"], 0.0) + abs(c.get("contribution", 0))
    ranked = []
    for sid, n in freq.items():
        sig = idx.get(sid)
        if not sig:
            continue
        layer_mult = {"P": 1.25, "S": 1.0, "O": 0.6}[sig["layer"]]
        w = math.log(sv.LR_CLASSES.get(sig.get("lr_class", "x2"), 2.0))
        ranked.append({"signal": sid, "layer": sig["layer"], "claim": sig["claim"],
                       "cluster": sig["cluster"],
                       "key_score": round((n / max(1, len(target))) * w * layer_mult, 3),
                       "seen_in": n})
    ranked.sort(key=lambda x: -x["key_score"])
    return {"population": len(target), "key_signals": ranked[:max_cols],
            "dropped": max(0, len(ranked) - max_cols)}


# --------------------------------------------------------------------------
# 2. MATERIALIZE — les colonnes sur mesure du tableau
# --------------------------------------------------------------------------

def materialize(scores, tree, universe, evidence, key_signals, today):
    """Par entreprise cible : une colonne par signal clé (valeur lisible +
    couche), la colonne `signal_cle` (contributeur dominant) et le squelette
    d'`axe` (groupe déterministe = cluster du signal dominant ; l'AXE-MAPPER
    renommera/fusionnera). Sortie = payload db.py modify --updates -."""
    idx = _sig_index(tree)
    uidx = {c["_id"]: c for c in universe}
    keys = [k["signal"] for k in key_signals["key_signals"]]
    defaults = tree.get("defaults", {})
    updates = []
    for s in scores:
        if s["band"] == "OUT":
            continue
        c = uidx.get(s["_id"])
        if not c:
            continue
        row = {"_id": s["_id"], "band": s["band"], "score_v2": s["expected"]}
        for sid in keys:
            sig = idx[sid]
            b, _, _, obs, unk = sv.signal_belief(sig, c, evidence, defaults, today)
            col = "sig_" + sid.lower().replace("-", "_")
            if obs:
                truthy = [o for o in obs if o["value"]]
                row[col] = (f"[{sig['layer']}] oui ({len(truthy)}/{len(obs)} proxies)"
                            if truthy else f"[{sig['layer']}] non")
            else:
                row[col] = f"[{sig['layer']}] ?"
        top = (s.get("top_contributors") or [{}])
        dom = top[0].get("signal")
        row["signal_cle"] = dom or "aucun"
        row["axe"] = idx[dom]["cluster"] if dom in idx else "sans_signal"
        updates.append(row)
    return updates


# --------------------------------------------------------------------------
# 3. AXES-PREP — le pré-groupement déterministe pour l'AXE-MAPPER
# --------------------------------------------------------------------------

def axes_prep(materialized: list[dict]) -> dict:
    groups = {}
    for r in materialized:
        g = groups.setdefault(r["axe"], {"axe_provisoire": r["axe"], "n": 0,
                                         "bands": {}, "companies": [],
                                         "signaux_cles": {}})
        g["n"] += 1
        g["bands"][r["band"]] = g["bands"].get(r["band"], 0) + 1
        g["signaux_cles"][r["signal_cle"]] = g["signaux_cles"].get(r["signal_cle"], 0) + 1
        g["companies"].append(r["_id"])
    out = sorted(groups.values(), key=lambda g: -g["n"])
    return {"groups": out,
            "consigne_axe_mapper": ("Nommer 3-6 AXES marketing (un axe = une "
                                    "histoire de segment, ex. « délégation en cours », "
                                    "« très forte ancienneté ») ; fusionner les groupes "
                                    "trop proches ; puis écrire le PROMPT D'AXE de chacun "
                                    "avec le skill prompt-smith-outreach.")}


# --------------------------------------------------------------------------
# 4. RESSOURCES — la synthèse par entreprise de ce que le tableau SAIT
# --------------------------------------------------------------------------

def build_resources(scores, tree, universe, evidence, today, band_filter=None):
    idx = _sig_index(tree)
    uidx = {c["_id"]: c for c in universe}
    defaults = tree.get("defaults", {})
    out = []
    for s in scores:
        if band_filter and s["band"] != band_filter:
            continue
        c = uidx.get(s["_id"])
        if not c:
            continue
        facts, questions = [], list(q["ask"] for q in s.get("qualification_questions", []))
        for sig in tree["signals"]:
            if sig.get("status") == "killed" or not sig.get("proxies"):
                continue
            b, _, _, obs, unk = sv.signal_belief(sig, c, evidence, defaults, today)
            for o in obs:
                if not o["value"]:
                    continue
                facts.append({"signal": sig["id"], "claim": sig["claim"],
                              "layer": sig["layer"],
                              "evidence_url": o.get("evidence_url"),
                              "poids": round(abs(math.log(sv.LR_CLASSES.get(
                                  sig.get("lr_class", "x2"), 2.0))), 2)})
        facts.sort(key=lambda f: -f["poids"])
        firmo = {k: c.get(k) for k in ("name", "ville", "dept", "naf", "ca_eur",
                                       "age_societe", "dirigeant", "dirigeant_age",
                                       "effectif_tranche") if c.get(k)}
        out.append({"company_id": s["_id"], "name": c.get("name"),
                    "band": s["band"], "score": s["expected"],
                    "axe": None,  # rempli après l'AXE-MAPPER
                    "firmo": firmo,
                    "faits_sources": facts[:6],
                    "questions_qualification": questions[:2],
                    "regle": "Tout fait absent de cette liste N'EXISTE PAS pour le mail."})
    return out


# --------------------------------------------------------------------------
# 5. COMPILE-PROMPT — BASE (axe × format) + RESSOURCES → prompt sur mesure
# --------------------------------------------------------------------------

PROMPT_TEMPLATE = """# PROMPT DE GÉNÉRATION — {company} · axe « {axe_name} » · format {format_id}

Tu écris UN {format_name} en suivant STRICTEMENT le skill email-craft
(« je sais écrire un mail »). Ce prompt a été compilé par la fabrique —
tu n'as AUCUNE liberté sur les faits, seulement sur la langue.

## L'AXE (le segment et son histoire)
{axe_prompt}

## LE FORMAT (le contrat de support)
{format_contract}

## L'OFFRE (résumé — la vérité, pas un argumentaire)
{offer_digest}

## LA VOIX
{voice_digest}

## RESSOURCES — les SEULS faits utilisables (tout le reste n'existe pas)
{resources_block}

## Auto-contrôle avant de rendre (échec à UN critère = réécris)
1. Le test du pair : un dirigeant enverrait-il ce message à un autre dirigeant ?
2. Chaque phrase gagne sa place (curiosité, pertinence, crédibilité ou ask).
3. L'ouverture = un FAIT des ressources, relié au problème (jamais décoratif).
4. ≤ 100 mots, UNE question finale, sujet plat sans slogan.
5. Zéro promesse de résultat (anti-L121), zéro fait hors ressources,
   zéro placeholder, signature = champ fourni sinon [Prénom NOM].
"""


def compile_prompt(axes, formats_doc, resources, company_id, format_id,
                   offer_path=None, voice_path=None):
    res = next((r for r in resources if str(r["company_id"]) == str(company_id)), None)
    if not res:
        raise SystemExit(json.dumps({"ok": False, "error": f"company {company_id} sans ressources"}))
    axe = next((a for a in axes["axes"] if a["axe_id"] == res.get("axe")), None)
    if axe is None:  # fallback : axe par signal_cle non encore mappé
        axe = axes["axes"][0]
    fmt = next((f for f in formats_doc["formats"] if f["id"] == format_id), None)
    if not fmt:
        raise SystemExit(json.dumps({"ok": False, "error": f"format {format_id} inconnu"}))
    offer = open(offer_path, encoding="utf-8").read()[:900] if offer_path and os.path.exists(offer_path) else "(offer.md absent — STOP, gate V1 §3)"
    voice = open(voice_path, encoding="utf-8").read()[:400] if voice_path and os.path.exists(voice_path) else "Vouvoiement, sobre, dirigeant-à-dirigeant, français. Signature non fournie → [Prénom NOM]."
    rblock = json.dumps({k: res[k] for k in ("firmo", "faits_sources",
                                             "questions_qualification")},
                        ensure_ascii=False, indent=2)
    return PROMPT_TEMPLATE.format(
        company=res["name"], axe_name=axe["name"], format_id=fmt["id"],
        format_name=fmt["name"], axe_prompt=axe["axe_prompt"].strip(),
        format_contract=fmt["contract"].strip(), offer_digest=offer.strip(),
        voice_digest=voice.strip(), resources_block=rblock)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_demo(_a):
    today = dt.date(2026, 7, 8)
    tree = json.load(open(os.path.join(FIXTURES, "memoval-signals.json"), encoding="utf-8"))
    universe = _rows(os.path.join(FIXTURES, "mock-universe.jsonl"))
    scores = _rows("/tmp/bricks-v2-demo-scores.jsonl")
    ev = sv.load_evidence(os.path.join(FIXTURES, "demo-evidence.jsonl"))
    ks = select_key_signals(scores, tree)
    print(json.dumps({"1_signaux_cles": [(k['signal'], k['key_score']) for k in ks['key_signals']],
                      "population": ks["population"]}, ensure_ascii=False))
    mat = materialize(scores, tree, universe, ev, ks, today)
    out_m = os.path.join(FIXTURES, "demo-tableau-updates.json")
    json.dump(mat, open(out_m, "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps({"2_tableau": {"lignes": len(mat), "colonnes_ajoutees":
                     [k for k in mat[0] if k != '_id'], "out": out_m}}, ensure_ascii=False))
    groups = axes_prep(mat)
    print(json.dumps({"3_groupes_pour_axe_mapper":
                     [(g['axe_provisoire'], g['n'], g['bands']) for g in groups['groups']]},
                     ensure_ascii=False))
    res = build_resources(scores, tree, universe, ev, today, band_filter="IN")
    out_r = os.path.join(FIXTURES, "demo-resources.jsonl")
    with open(out_r, "w", encoding="utf-8") as f:
        for r in res:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"4_ressources": {"entreprises_IN": len(res), "out": out_r,
                      "exemple_faits": res[0]["faits_sources"][:2] if res else None}},
                     ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — fabrique de messages")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    p = sub.add_parser("select-key-signals")
    p.add_argument("--scores", required=True); p.add_argument("--tree", required=True)
    p.add_argument("--max", type=int, default=8)
    p = sub.add_parser("materialize")
    for a in ("--scores", "--tree", "--universe"):
        p.add_argument(a, required=True)
    p.add_argument("--evidence"); p.add_argument("--key-signals")
    p.add_argument("--out", required=True); p.add_argument("--today")
    p = sub.add_parser("axes-prep")
    p.add_argument("--materialized", required=True); p.add_argument("--out")
    p = sub.add_parser("resources")
    for a in ("--scores", "--tree", "--universe"):
        p.add_argument(a, required=True)
    p.add_argument("--evidence"); p.add_argument("--band")
    p.add_argument("--out", required=True); p.add_argument("--today")
    p = sub.add_parser("compile-prompt")
    for a in ("--axes", "--formats", "--resources", "--company-id", "--format-id"):
        p.add_argument(a, required=True)
    p.add_argument("--offer"); p.add_argument("--voice"); p.add_argument("--out")
    args = ap.parse_args(argv)

    if args.cmd == "demo":
        return cmd_demo(args)
    if args.cmd == "select-key-signals":
        tree = json.load(open(args.tree, encoding="utf-8"))
        print(json.dumps(select_key_signals(_rows(args.scores), tree, args.max),
                         ensure_ascii=False, indent=2))
        return
    today = dt.date.fromisoformat(args.today) if getattr(args, "today", None) else dt.date.today()
    if args.cmd == "materialize":
        tree = json.load(open(args.tree, encoding="utf-8"))
        scores = _rows(args.scores)
        ks = (json.load(open(args.key_signals, encoding="utf-8"))
              if args.key_signals else select_key_signals(scores, tree))
        ev = sv.load_evidence(args.evidence)
        mat = materialize(scores, tree, _rows(args.universe), ev, ks, today)
        json.dump(mat, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
        print(json.dumps({"ok": True, "rows": len(mat), "out": args.out,
                          "next": "db.py modify companies --updates - < " + args.out}))
    elif args.cmd == "axes-prep":
        g = axes_prep(_rows(args.materialized))
        if args.out:
            json.dump(g, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(json.dumps({"ok": True, "groups": len(g["groups"]), "out": args.out},
                         ensure_ascii=False))
    elif args.cmd == "resources":
        tree = json.load(open(args.tree, encoding="utf-8"))
        ev = sv.load_evidence(args.evidence)
        res = build_resources(_rows(args.scores), tree, _rows(args.universe), ev,
                              today, band_filter=args.band)
        with open(args.out, "w", encoding="utf-8") as f:
            for r in res:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(json.dumps({"ok": True, "companies": len(res), "out": args.out}))
    elif args.cmd == "compile-prompt":
        axes = json.load(open(args.axes, encoding="utf-8"))
        formats_doc = json.load(open(args.formats, encoding="utf-8"))
        prompt = compile_prompt(axes, formats_doc, _rows(args.resources),
                                args.company_id, args.format_id, args.offer, args.voice)
        if args.out:
            open(args.out, "w", encoding="utf-8").write(prompt)
            print(json.dumps({"ok": True, "out": args.out, "chars": len(prompt)}))
        else:
            print(prompt)


if __name__ == "__main__":
    main()
