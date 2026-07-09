#!/usr/bin/env python3
"""V3 — PREUVE DU MINAGE : extraire les CLIENTS d'un « concurrent » depuis ses
propres posts LinkedIn (récupérés LIVE via Sillage contents/query).
Claude extrait chaque relation client avec la CITATION exacte qui la prouve +
un niveau de certitude. C'est le maillon 2 du pipeline V3 (concurrent → posts →
noms de clients), démontré sur données réelles."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fable_api import call

S = os.path.dirname(os.path.abspath(__file__))
posts = json.load(open(f"{S}/live-posts.json"))["data"]
accs = {a["company_id"]: a["company"]["name"] for a in json.load(open(f"{S}/live-accounts.json"))["data"] if a.get("company")}

SYS = ("Tu es l'extracteur de relations clients de BRICKS V3. On te donne les posts LinkedIn publics d'une "
 "entreprise (un « concurrent »). Tu identifies les ENTREPRISES CLIENTES que ces posts trahissent : cas client "
 "cité, projet livré, témoignage, co-marketing, événement co-brandé, remerciement, logo. RÈGLES DURES : "
 "(1) uniquement des CLIENTS (pas les partenaires technos, pas les écoles, pas les média, pas ses propres produits) ; "
 "(2) chaque relation DOIT être appuyée par une citation exacte du post ; (3) certitude : haute (cas client explicite), "
 "moyenne (co-marketing/événement), basse (mention ambiguë) ; (4) si un post ne trahit aucun client, ne force rien. "
 "Réponds UNIQUEMENT en JSON strict :\n"
 '[{"client":"nom de l_entreprise cliente","evidence":"citation exacte (~15 mots)","relation":"cas_client|projet|temoignage|co_marketing|evenement|mention","certainty":"haute|moyenne|basse"}]')

def _arr(txt):
    s = txt.find("[")
    if s < 0: return []
    depth=0; instr=False; esc=False
    for i in range(s, len(txt)):
        c=txt[i]
        if esc: esc=False; continue
        if c=="\\": esc=True; continue
        if c=='"': instr=not instr
        elif not instr:
            if c=="[": depth+=1
            elif c=="]":
                depth-=1
                if depth==0:
                    try: return json.loads(txt[s:i+1])
                    except Exception: return []
    return []

if __name__ == "__main__":
    by = {}
    for c in posts:
        nm = accs.get(c.get("company_id"))
        if not nm: continue
        txt = (c.get("data") or {}).get("text") or (c.get("data") or {}).get("commentary") or ""
        if len(txt) > 40: by.setdefault(nm, []).append(txt)
    print("═" * 74)
    print("  V3 · MINAGE DES CLIENTS — posts LinkedIn réels (Sillage live) → Claude")
    print("═" * 74)
    total = 0; tin = tout = 0
    out = {}
    for nm, txts in by.items():
        corpus = "\n\n---POST---\n".join(t[:1200] for t in txts[:25])
        u = f"CONCURRENT : {nm}\n\nSES POSTS LINKEDIN ({len(txts)}) :\n\n---POST---\n{corpus}\n\nExtrais les relations clients. JSON strict."
        r = call(u, system=SYS, max_tokens=8000, label=nm)
        tin += r.get("in", 0); tout += r.get("out", 0)
        rels = _arr(r["text"]); out[nm] = rels; total += len(rels)
        print(f"\n▶ {nm} — {len(txts)} posts analysés → {len(rels)} relations clients détectées")
        for rel in rels[:10]:
            print(f"   [{rel.get('certainty','?'):7}] {rel.get('client','?'):28} ({rel.get('relation','?')}) « {str(rel.get('evidence',''))[:70]} »")
        if len(rels) > 10: print(f"   … +{len(rels)-10} autres")
    json.dump(out, open(f"{S}/mined_clients.json", "w"), ensure_ascii=False, indent=1)
    print("\n" + "═" * 74)
    print(f"  TOTAL : {total} relations clients extraites de {sum(len(v) for v in by.values())} posts réels · {tout} tok out")
    print("═" * 74)
