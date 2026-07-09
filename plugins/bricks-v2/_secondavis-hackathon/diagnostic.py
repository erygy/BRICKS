#!/usr/bin/env python3
"""SECOND AVIS — LE DIAGNOSTIC DIFFÉRENTIEL DU SILENCE (cœur, preuve).

Vu de l'intérieur, tous les silences clients se ressemblent. Vu de l'extérieur,
ils divergent. Ce fichier le PROUVE : cinq comptes au silence interne STRICTEMENT
IDENTIQUE (même chute d'usage, même absence de réponse — figé en dur, 0 token),
chacun avec un dossier de faits externes (signaux Sillage) différent. Claude rend
un diagnostic différentiel — BÉNIN / TOXIQUE / INDÉTERMINÉ — qui CITE ses preuves
datées et énonce ce qui le falsifierait. Aucun score de confiance numérique
(objection du réfuteur corrigée) ; l'indéterminé est assumé comme une fierté.

Sans Sillage : les 5 silences restent identiques → 'just checking in' aveugle.
Sans Claude : deux flux juxtaposés, la synthèse reste à faire à la main.
Sans FullEnrich : verdict toxique + champion muet = impasse (étape 5)."""
import json, re, sys
from fable_api import call

# ── Le silence INTERNE, identique pour les 5 (déterministe, 0 token) ──
SILENCE_INTERNE = {
    "usage_30j": "-63 %", "derniere_reponse": "il y a 24 jours",
    "meetings": "2 QBR annulés d'affilée", "tickets_support": "0 depuis 5 semaines",
    "resume": "chute d'usage franche, plus aucune réponse, comité de pilotage annulé",
}

# ── Les faits EXTERNES divergent (signaux Sillage, déjà survenus) ──
COMPTES = [
    {"nom": "Northwind", "domaine": "northwind.io", "arr": 90000,
     "sillage": "Vague d'embauche : 34 postes ouverts (dont 12 en engineering), 2 bureaux annoncés. Aucun signal négatif."},
    {"nom": "Halcyon", "domaine": "halcyon.co", "arr": 120000,
     "sillage": "Rachat annoncé il y a 3 semaines par un groupe US ; intégration en cours ; nouveau CFO nommé."},
    {"nom": "Vantle", "domaine": "vantle.com", "arr": 75000,
     "sillage": "Le champion (VP Ops, sponsor du deal) a quitté l'entreprise il y a 12 jours ; son successeur vient de chez un concurrent direct."},
    {"nom": "Orbix", "domaine": "orbix.ai", "arr": 60000,
     "sillage": "L'entreprise a publié 3 posts d'étude de cas avec un concurrent direct, et recruté 2 personnes venant de ce concurrent."},
    {"nom": "Calder", "domaine": "calderhq.com", "arr": 45000,
     "sillage": "Aucun signal externe détecté sur les 90 derniers jours."},
]

SYS = ("Tu es le juge de SECOND AVIS — le diagnostic différentiel du silence client. Un compte est devenu "
 "silencieux (chute d'usage, plus de réponse). Tu ne juges QU'UNE chose : à la lumière des FAITS EXTERNES "
 "datés (signaux Sillage), ce silence est-il BÉNIN (le client est occupé/distrait mais reste engagé), "
 "TOXIQUE (le client est en train de partir), ou INDÉTERMINÉ (les faits ne permettent pas de trancher) ?\n\n"
 "RÈGLES DURES :\n"
 "- Le silence interne est IDENTIQUE pour tous les comptes : il ne discrimine rien. Seuls les faits externes "
 "peuvent faire diverger ton verdict.\n"
 "- Tu CITES le fait externe qui fonde ton verdict, et tu énonces CE QUI LE FALSIFIERAIT.\n"
 "- Absence de signal externe n'est PAS une preuve de silence bénin → INDÉTERMINÉ, et tu dis quel signal "
 "surveiller. L'indétermination est un verdict honnête, pas un échec.\n"
 "- Une vague d'embauche = occupé (bénin) ; un départ de champion vers un concurrent, ou un engagement "
 "concurrent = danger (toxique) ; un M&A = distraction à risque (souvent toxique à terme, mais dis pourquoi).\n"
 "- PAS de score de confiance numérique. Tu raisonnes sur les faits.\n\n"
 "Réponds UNIQUEMENT en JSON strict :\n"
 '{"verdict":"BÉNIN|TOXIQUE|INDÉTERMINÉ","hypothese":"la cause probable du silence en 1 phrase",'
 '"preuve":"le fait externe daté qui fonde le verdict (ou vide)","falsifie_si":"ce qui renverserait ce verdict",'
 '"action":"l_action recommandée","contact_alternatif":true|false}')

def _json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m: return {"verdict": "INDÉTERMINÉ", "hypothese": "parse", "preuve": "", "falsifie_si": "", "action": "", "contact_alternatif": False}
    try: return json.loads(m.group(0))
    except Exception: return {"verdict": "INDÉTERMINÉ", "hypothese": "json invalide", "preuve": "", "falsifie_si": "", "action": "", "contact_alternatif": False}

def diagnose(compte):
    u = (f"COMPTE SILENCIEUX : {compte['nom']} ({compte['domaine']}) — {compte['arr']}€ ARR\n\n"
     f"SILENCE INTERNE (identique pour tous les comptes) :\n- {SILENCE_INTERNE['resume']}\n"
     f"  (usage {SILENCE_INTERNE['usage_30j']}, {SILENCE_INTERNE['derniere_reponse']}, {SILENCE_INTERNE['meetings']})\n\n"
     f"FAITS EXTERNES (Sillage, déjà survenus) :\n- {compte['sillage']}\n\n"
     "Rends ton diagnostic différentiel. JSON strict uniquement.")
    r = call(u, system=SYS, max_tokens=3500, label=compte["nom"])
    return _json(r["text"]), r

MSG_SYS = ("Tu écris un email de reprise de contact court (5-7 lignes), humain, sans corporate-speak. Tu ne mentionnes "
 "JAMAIS le silence ni la baisse d'usage (ce serait accusateur). Tu accroches sur le FAIT EXTERNE pertinent. "
 "Pour un silence bénin : ton léger, utile, tu facilites la vie d'une équipe débordée. Pour un silence toxique : "
 "tu t'adresses à un contact alternatif, tu rouvres la valeur sans mendier. Signé 'Thomas'.")

def message(compte, diag):
    u = (f"Compte : {compte['nom']}. Verdict : {diag['verdict']}. Hypothèse : {diag['hypothese']}. "
     f"Fait externe : {compte['sillage']}. Écris l'email de reprise adapté à ce type de silence.")
    r = call(u, system=MSG_SYS, max_tokens=1500, label=f"msg-{compte['nom']}")
    return r["text"].strip(), r

SYMB = {"BÉNIN": "🟢 BÉNIN — nourrir", "TOXIQUE": "🔴 TOXIQUE — intervenir", "INDÉTERMINÉ": "🟡 INDÉTERMINÉ — surveiller"}

if __name__ == "__main__":
    print("═" * 78)
    print("  SECOND AVIS · DIAGNOSTIC DIFFÉRENTIEL DU SILENCE (Fable 5, verdicts réels)")
    print(f"  Silence INTERNE identique pour les 5 : {SILENCE_INTERNE['resume']}")
    print("═" * 78)
    diags = []; tin = tout = 0
    for c in COMPTES:
        d, r = diagnose(c); diags.append((c, d)); tin += r.get("in", 0); tout += r.get("out", 0)
        print(f"\n▶ {c['nom']} ({c['arr']}€) — dehors : {c['sillage'][:66]}…")
        print(f"   {SYMB.get(d.get('verdict'), d.get('verdict'))}")
        print(f"   hypothèse : {d.get('hypothese')}")
        if d.get("preuve"): print(f"   preuve    : {d.get('preuve')}")
        print(f"   falsifié si : {d.get('falsifie_si')}")
        print(f"   action    : {d.get('action')}  {'[+ contact alternatif FullEnrich]' if d.get('contact_alternatif') else ''}")
    # compteur
    from collections import Counter
    cnt = Counter(d.get("verdict") for _, d in diags)
    print("\n" + "═" * 78)
    print(f"  MÊME silence interne → {cnt.get('BÉNIN',0)} bénin · {cnt.get('TOXIQUE',0)} toxique · {cnt.get('INDÉTERMINÉ',0)} indéterminé")
    print(f"  Silence EXPLIQUÉ : {sum(1 for _,d in diags if d.get('verdict')!='INDÉTERMINÉ')}/5 comptes → action ciblée au lieu du 'just checking in' aveugle")
    print("═" * 78)
    # deux messages opposés depuis le MÊME silence interne
    benin = next((x for x in diags if x[1].get("verdict") == "BÉNIN"), None)
    toxique = next((x for x in diags if x[1].get("verdict") == "TOXIQUE"), None)
    print("\n── DEUX EMAILS OPPOSÉS, générés depuis un silence interne IDENTIQUE ──")
    for label, pair in [("SILENCE BÉNIN", benin), ("SILENCE TOXIQUE", toxique)]:
        if not pair: continue
        c, d = pair; m, r = message(c, d); tin += r.get("in", 0); tout += r.get("out", 0)
        print(f"\n▷ {label} — {c['nom']}\n{m}")
    print(f"\n(jugement + rédaction : {tin} tokens in / {tout} out)")
