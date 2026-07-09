#!/usr/bin/env python3
"""APPEL — LE TRIBUNAL DE FALSIFICATION (cœur, preuve).

Chaque raison de perte closed-lost est une HYPOTHÈSE DATÉE sur le monde.
On confronte cette hypothèse à un ÉVÉNEMENT réel (signal Sillage) et on rend un
verdict de POLARITÉ : l'événement FALSIFIE-t-il l'objection, la laisse-t-il
INTACTE (voire la RENFORCE), ou n'a-t-on pas de quoi juger (ABSTENTION) ?

Répartition des rôles (la thèse du hackathon, testée au retrait) :
- Le TYPAGE de l'objection + le ROUTAGE + le GATE VOI (dépenser un crédit ?) sont
  DÉTERMINISTES — 0 token, instantané. (Sans FullEnrich : dossier envoyé à un fantôme.)
- Le JUGEMENT DE POLARITÉ (raison × événement) passe par CLAUDE sous contrainte JSON —
  c'est le seul maillon qu'aucune table de règles ne peut rendre. (Sans Claude : bruit.)
- L'ÉVÉNEMENT vient du monde réel (Sillage). (Sans Sillage : nurture calendaire.)

Ce fichier prouve le moment-wow : MÊME levée de fonds, TROIS verdicts opposés selon
la raison de perte — verdicts issus d'un vrai raisonnement, pas d'un if/else."""
import json, re, sys
from fable_api import call

# ─────────────────────────────────────────────────────────────────────────────
# 1. TYPAGE DÉTERMINISTE de la raison de perte (0 token, 0 hallucination possible)
# ─────────────────────────────────────────────────────────────────────────────
OBJECTION_TYPES = {
    "BUDGET":     ["budget", "trop cher", "prix", "cost", "expensive", "price", "coût", "pas les moyens", "cash"],
    "COMPETITOR": ["concurrent", "competitor", "choisi", "chose", "went with", "préféré", "rival", "competition"],
    "TIMING":     ["timing", "trop tôt", "trop tard", "pas le moment", "plus tard", "next year", "l'an prochain", "reporté", "not now"],
    "AUTHORITY":  ["décideur", "champion parti", "sponsor", "no authority", "pas le bon interlocuteur", "changement de direction"],
    "NEED":       ["pas besoin", "no need", "pas prioritaire", "use case", "cas d'usage", "fonctionnalité manquante", "feature"],
}
DIRTY = {"", "other", "n/a", "na", "-", "no decision", "no reason", "unknown", "closed lost", "lost", "?", "rien"}

def type_objection(raw):
    t = (raw or "").lower().strip()
    if t in DIRTY or len(t) < 4:
        return "DIRTY"          # objection jamais plaidée → candidate à l'abstention structurelle
    for typ, kws in OBJECTION_TYPES.items():
        if any(k in t for k in kws):
            return typ
    return "UNTYPED"            # plaidée mais non catégorisée → Claude juge quand même

# ─────────────────────────────────────────────────────────────────────────────
# 2. LE PROCÈS — Claude juge la POLARITÉ (raison × événement), JSON strict
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM = """Tu es le juge d'APPEL — le tribunal de falsification des deals perdus (closed-lost).

Tu ne juges QU'UNE chose : la relation logique entre la RAISON DE PERTE d'un deal et un ÉVÉNEMENT réel survenu depuis. Tu ne vends rien, tu ne supposes rien, tu n'inventes aucun fait.

TROIS VERDICTS POSSIBLES, et un seul :
- FALSIFIÉE : l'événement rend l'objection logiquement caduque. Exemple canonique : objection « pas de budget » × événement « levée de fonds de 22M€ » → l'hypothèse "ils n'ont pas les moyens" est morte, datée, prouvée.
- INTACTE : l'événement ne change rien à l'objection, ou la RENFORCE. Exemple : objection « ils ont choisi un concurrent » × événement « ils lèvent 22M€ » → plus d'argent = ils investiront PLUS dans le concurrent choisi ; l'objection tient, voire se renforce. Ne PAS rouvrir.
- ABSTENTION : la raison de perte est vide, illisible, générique ("Other", "no decision") ou l'événement ne porte pas sur l'objection. Dans le doute, ABSTENTION. Un tribunal ne juge que ce qui a été plaidé.

RÈGLES DURES :
- Tu cites l'événement comme falsificateur, jamais une supposition ("ils ont sûrement…" est interdit).
- Une levée de fonds ne falsifie PAS une objection « pas besoin » ou « mauvais timing produit » — reste strict sur le lien logique.
- La confiance reflète la FORCE DU LIEN LOGIQUE, pas ton enthousiasme commercial.

Réponds UNIQUEMENT par un objet JSON strict, sans texte autour :
{"verdict":"FALSIFIÉE|INTACTE|ABSTENTION","polarite":"falsifie|renforce|sans_rapport","confiance":0-100,"falsificateur":"la phrase exacte de l'événement qui tue (ou vide)","raisonnement":"1-2 phrases, le lien logique","risque":"le contre-argument honnête qui pourrait invalider ce verdict"}"""

def _parse(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return {"verdict": "ABSTENTION", "polarite": "sans_rapport", "confiance": 0,
                "falsificateur": "", "raisonnement": "réponse non parsable", "risque": "parse"}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"verdict": "ABSTENTION", "polarite": "sans_rapport", "confiance": 0,
                "falsificateur": "", "raisonnement": "JSON invalide", "risque": "parse"}

def judge(deal, event):
    objtype = type_objection(deal["loss_reason"])
    user = (
        "DEAL PERDU\n"
        f"- Compte : {deal['name']} ({deal['domain']}) — {deal['amount']}€ ARR\n"
        f"- Raison de perte (brute, telle que dans le CRM) : \"{deal['loss_reason']}\"  [type détecté par le code : {objtype}]\n"
        f"- Perdu le : {deal['loss_date']}\n\n"
        "ÉVÉNEMENT DU MONDE (signal Sillage, déjà survenu)\n"
        f"- Type : {event['type']}\n"
        f"- Détail : {event['detail']}\n"
        f"- Daté : {event['date']}\n\n"
        "Rends ton verdict. JSON strict uniquement."
    )
    r = call(user, system=SYSTEM, max_tokens=4000, label=deal["name"])
    return objtype, _parse(r["text"]), r

# ─────────────────────────────────────────────────────────────────────────────
# 3. GATE VOI — ne dépenser un crédit contact QUE si ça change la décision (0 token)
# ─────────────────────────────────────────────────────────────────────────────
def voi_gate(deal, verdict):
    v = verdict.get("verdict")
    if v != "FALSIFIÉE":
        return {"spend": False, "credits": 0.0,
                "reason": "objection non falsifiée → aucun crédit, on laisse dormir"}
    if deal["amount"] < 5000:
        return {"spend": False, "credits": 0.0,
                "reason": "deal sous le seuil VOI → réouverture non rentable"}
    # falsifiée + deal significatif : on vérifie le contact (successeur si l'ancien est parti)
    return {"spend": True, "credits": 1.25,
            "action": "FullEnrich : search 0,25 (comité actuel) + email 1 (bon vivant) → dossier de réouverture"}

# ─────────────────────────────────────────────────────────────────────────────
# 4. DÉMO — le triptyque : MÊME levée, TROIS verdicts (+ compteur de retenue)
# ─────────────────────────────────────────────────────────────────────────────
RAISE = {"type": "funding_round",
         "detail": "Série B de 22M€ menée par Accel, annoncée publiquement",
         "date": "2026-07-02"}

TRIPTYQUE = [
    {"name": "TechFlow",   "domain": "techflow.io",   "amount": 48000,
     "loss_reason": "Trop cher, pas de budget alloué cette année", "loss_date": "2025-11-14", "event": RAISE},
    {"name": "DataNimbus", "domain": "datanimbus.co",  "amount": 60000,
     "loss_reason": "Ont choisi un concurrent (Rival Corp)",        "loss_date": "2025-09-30", "event": RAISE},
    {"name": "Postbox",    "domain": "getpostbox.com", "amount": 32000,
     "loss_reason": "Other",                                        "loss_date": "2025-12-02", "event": RAISE},
]

SYMB = {"FALSIFIÉE": "⚖️ FALSIFIÉE → ROUVRIR", "INTACTE": "🛑 INTACTE → LAISSER DORMIR",
        "ABSTENTION": "🤔 ABSTENTION → DEMANDER AU REP"}

def run_demo(deals):
    print("═" * 74)
    print("  APPEL · LE TRIBUNAL DE FALSIFICATION — triptyque (Fable 5, verdicts réels)")
    print("  Événement identique pour les 3 : «", RAISE["detail"], "»")
    print("═" * 74)
    reopened = credits = 0.0
    tin = tout = 0
    for d in deals:
        objtype, v, r = judge(d, d["event"])
        gate = voi_gate(d, v)
        tin += r.get("in", 0); tout += r.get("out", 0)
        print(f"\n▶ {d['name']} ({d['amount']}€) — perdu : « {d['loss_reason']} »  [type: {objtype}]")
        print(f"   {SYMB.get(v.get('verdict'), v.get('verdict'))}   (confiance {v.get('confiance')}%)")
        print(f"   polarité   : {v.get('polarite')}")
        if v.get("falsificateur"):
            print(f"   falsificateur : « {v.get('falsificateur')} »")
        print(f"   raisonnement : {v.get('raisonnement')}")
        print(f"   risque       : {v.get('risque')}")
        print(f"   VOI          : {gate['reason'] if not gate['spend'] else gate['action']}  (+{gate['credits']} crédit)")
        if gate["spend"]:
            reopened += 1; credits += gate["credits"]
    print("\n" + "═" * 74)
    print(f"  COMPTEUR DE RETENUE : {len(deals)} jugés · {int(reopened)} rouverts · "
          f"{len(deals)-int(reopened)} laissés dormir · {credits:.2f} crédits · 0 token pour le tri déterministe")
    print(f"  (jugement LLM : {tin} tokens in / {tout} out)")
    print("═" * 74)

if __name__ == "__main__":
    run_demo(TRIPTYQUE)
