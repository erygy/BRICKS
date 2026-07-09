#!/usr/bin/env python3
"""V3 — consolidation de la taxonomie : dédup sémantique (Fable) → classement
déterministe → compilation en PACKS D'AGENTS SILLAGE prêts à créer.
Un pack = une config d'agent réelle (type + mots-clés FR curés + watchlist à lier)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fable_api import call

S = os.path.dirname(os.path.abspath(__file__))
flags = json.load(open(f"{S}/flags_raw.json"))

def _js(txt, opener="["):
    closer = "]" if opener == "[" else "}"
    s = txt.find(opener)
    if s < 0: return None
    depth=0; instr=False; esc=False
    for i in range(s, len(txt)):
        c=txt[i]
        if esc: esc=False; continue
        if c=="\\": esc=True; continue
        if c=='"': instr=not instr
        elif not instr:
            if c==opener: depth+=1
            elif c==closer:
                depth-=1
                if depth==0:
                    try: return json.loads(txt[s:i+1])
                    except Exception: return None
    return None

def num(x, d=0.0):
    try: return float(x)
    except Exception: return d

# ── 1. dédup sémantique (1 appel, liste compacte) ──
compact = "\n".join(f'{f["fid"]}|{f.get("category","")[:18]}|{str(f.get("name",""))[:52]}|{str(f.get("what",""))[:70]}' for f in flags)
DEDUP_U = ("Voici 257 red flags (fid|catégorie|nom|description). Identifie les GROUPES DE DOUBLONS SÉMANTIQUES "
 "(même événement observable, même s'il est formulé différemment ou rangé dans une autre catégorie). "
 "Ne groupe QUE les vrais doublons — deux flags voisins mais distincts restent séparés.\n\n" + compact +
 "\n\nRéponds UNIQUEMENT en JSON strict : [{\"keep\":\"Fxxx (le mieux formulé)\",\"drop\":[\"Fyyy\",...]}]  "
 "— uniquement les groupes avec au moins 1 doublon.")
print("── dédup sémantique…")
r1 = call(DEDUP_U, system="Tu dédoublonnes une taxonomie GTM. Précis, conservateur, JSON strict uniquement.", max_tokens=9000, label="dedup")
groups = _js(r1["text"], "[") or []
drop = set()
for g in groups:
    for d in g.get("drop", []): drop.add(d.strip())
kept = [f for f in flags if f["fid"] not in drop]
print(f"  {len(flags)} → {len(kept)} flags après dédup ({len(drop)} retirés, stop={r1.get('stop')})")

# ── 2. classement déterministe ──
for f in kept:
    st = num(f.get("strength"), 5); fr = num(f.get("freq_per_1000_month"), 1)
    det = 1.0 if (f.get("sillage") or {}).get("detectable") else 0.55   # détectable Sillage = prime
    # rank = force × log-fréquence × détectabilité (un flag fort mais indétectable vaut moins)
    import math
    f["rank_score"] = round(st * (1 + math.log10(max(fr, 0.1) + 1)) * det, 2)
kept.sort(key=lambda f: f["rank_score"], reverse=True)
json.dump(kept, open(f"{S}/flags_ranked.json", "w"), ensure_ascii=False, indent=0)
tiers = {"A (déclencheur seul)": [f for f in kept if f["rank_score"] >= 12],
         "B (fort en cumul)": [f for f in kept if 7 <= f["rank_score"] < 12],
         "C (contexte/scoring)": [f for f in kept if f["rank_score"] < 7]}
for t, fl in tiers.items(): print(f"  tier {t}: {len(fl)}")

# ── 3. compilation des PACKS D'AGENTS SILLAGE (configs prêtes à créer) ──
top = kept[:150]
flags_txt = "\n".join(
    f'{f["fid"]}|{f.get("category","")[:20]}|{str(f.get("name",""))[:46]}|agent={((f.get("sillage") or {}).get("agent_type") or "-")}|kw={str(((f.get("sillage") or {}).get("keywords") or [])[:4])[:70]}'
    for f in top if (f.get("sillage") or {}).get("detectable"))
PACKS_U = ("Voici les red flags détectables via Sillage (fid|catégorie|nom|type d'agent|mots-clés proposés) :\n\n" + flags_txt +
 "\n\nCompile-les en 8 à 12 PACKS D'AGENTS SILLAGE prêts à créer — regroupe les flags par type d'agent × famille "
 "sémantique pour MINIMISER le nombre d'agents (quota précieux) sans noyer le signal. Pour chaque pack :\n"
 "- des mots-clés FR CURÉS (12-25, spécifiques, faible bruit — évite les mots seuls trop génériques, préfère des "
 "expressions ; pense aussi variantes anglaises si usuelles en France)\n"
 "- la watchlist à lier : customer-companies (clients des concurrents) | customer-profiles (sponsors) | competitor-companies\n"
 "- les fids couverts.\n\nRéponds UNIQUEMENT en JSON strict :\n"
 '[{"pack_id":"slug","name":"nom de l_agent à créer","agent_type":"keyword_detection|job_posting_keyword_detection|job_update|customer|champion|competitor",'
 '"watchlist":"customer-companies|customer-profiles|competitor-companies","keywords":["...",...],"covers":["Fxxx",...],"purpose":"1 phrase"}]')
print("── compilation des packs d'agents…")
r2 = call(PACKS_U, system="Tu configures des agents Sillage réels. Opérationnel, quota-aware, JSON strict.", max_tokens=13000, label="packs")
packs = _js(r2["text"], "[") or []
json.dump(packs, open(f"{S}/agent_packs.json", "w"), ensure_ascii=False, indent=1)
print(f"  {len(packs)} packs (stop={r2.get('stop')})")
for p in packs:
    print(f"  [{p.get('agent_type','?'):30}] {str(p.get('name',''))[:44]:44} kw={len(p.get('keywords',[]))} → {p.get('watchlist','')}")
TIN=r1.get("in",0)+r2.get("in",0); TOUT=r1.get("out",0)+r2.get("out",0)
print(f"\n→ flags_ranked.json ({len(kept)}) + agent_packs.json ({len(packs)}) · ~${TIN/1e6*3+TOUT/1e6*15:.2f}")
