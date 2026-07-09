#!/usr/bin/env python3
"""BRICKS V3 « DÉPLACEMENT » — exploration massive Fable 5.
Trois corpus structurés :
  A) RED FLAGS (~200 générés → dédup/classés) : signaux détectables sur les CLIENTS
     DES CONCURRENTS qui ouvrent une fenêtre de démarchage MAINTENANT.
  B) DISCOVERY PLAYBOOK : toutes les méthodes pour constituer la base
     « clients des concurrents » (posts LinkedIn, cas clients, logos, avis, jobs…).
  C) FAILLES CONCURRENT : signaux côté concurrent → leviers de persuasion.
Chaque flag est mappé sur les PRIMITIVES SILLAGE RÉELLES (spec gelée 09/07 :
watchlists customer/competitor company+profile, agents keyword_detection/
job_posting_keyword_detection/job_update/customer/champion/competitor,
content-requests account_mapping + top_account_content)."""
import sys, os, json, time
import concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fable_api import call

OUT = os.path.dirname(os.path.abspath(__file__))

def arr_from(txt):
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

SYS = ("Tu conçois BRICKS V3 : un moteur GTM de DÉPLACEMENT CONCURRENTIEL — voler les clients des concurrents "
 "plutôt que prospecter à froid. L'univers surveillé = la liste fermée des CLIENTS des concurrents de l'utilisateur. "
 "Tu es un stratège GTM brutal, terrain, anti-slop, qui chiffre honnêtement.\n\n"
 "PRIMITIVES SILLAGE RÉELLES (spec API gelée, workspace live vérifié) :\n"
 "- watchlists typées {customer, competitor, partner, influencer, champion} × entités {company, profile} (max 100/appel)\n"
 "- agents : keyword_detection (mots-clés dans les posts LinkedIn), job_posting_keyword_detection (mots-clés dans "
 "les offres d'emploi), job_update (changements de poste), customer/champion/competitor/partner/influencer (liés à une watchlist)\n"
 "- content-requests : account_mapping (profils employés d'une entreprise) + top_account_content (les POSTS LinkedIn d'un compte)\n"
 "- signals/query (curseur), signal-runs launch→poll, PAS de webhooks. Identité par domaine/LinkedIn.\n"
 "FULLENRICH : email vérifié=1 crédit, mobile=10, search=0,25/résultat (cartographie de comité quasi gratuite).\n"
 "CLAUDE : extraction, jugement, rédaction. Autres outils de scraping autorisés en complément si besoin (à nommer)."
)

# ─── A) RED FLAGS par catégorie ───
CATS = [
 ("recrutement_interne", "RECRUTEMENT & INTERNALISATION : offres d'emploi du client qui trahissent une insatisfaction du prestataire actuel ou un projet où on peut se substituer (ex: agence de design en place + le client recrute un designer interne ; recrute un profil dont la mission recouvre l'offre du concurrent ; poste 'refonte de X'...)."),
 ("mouvements_personnes", "MOUVEMENTS DE PERSONNES chez le client : départ/arrivée/promotion du sponsor de la relation concurrent, nouveau décideur venu d'une boîte cliente de chez NOUS ou d'un autre univers, départ à la retraite du référent historique, réorganisation du département acheteur."),
 ("posts_communication", "POSTS & COMMUNICATION LinkedIn du client : ce que le client publie qui ouvre une fenêtre (lancement produit, refonte, rebranding, appel à recommandations, plainte voilée, célébration d'un projet SANS mentionner le prestataire habituel, annonce d'un chantier dans notre domaine...)."),
 ("corporate_events", "ÉVÉNEMENTS CORPORATE du client : levée de fonds, M&A/rachat, nouvelle direction, expansion géographique, ouverture de filiale, pivot, changement d'échelle — tout ce qui déclenche une revue des prestataires/outils en place."),
 ("relation_client_concurrent", "SIGNAUX DE RELATION client↔concurrent qui FAIBLIT : le cas client disparaît du site du concurrent, plus de co-marketing depuis N mois, le champion de la relation (côté client OU côté concurrent) change de poste, fin de contrat probable (ancienneté du deal), baisse d'interactions publiques entre les deux."),
 ("evenements_ecosysteme", "ÉVÉNEMENTS & ÉCOSYSTÈME : le client participe à un salon/conférence de notre domaine, prend la parole sur un sujet qu'on adresse, rejoint une association pro, sponsorise un événement, publie un appel d'offres ou un RFP public."),
 ("besoins_manifestes", "BESOINS MANIFESTÉS : demandes publiques de recommandation, sondages posté par le client, questions dans des groupes/communautés, benchmark public d'outils, mention d'un projet à venir dans une interview/podcast/article de presse."),
 ("cycles_budget_contrat", "CYCLES BUDGET & CONTRAT : signaux temporels — clôture d'exercice fiscal, période de renouvellement probable (date de signature du deal concurrent + 10-14 mois), vote de budget annoncé, subventions/appels à projets obtenus qui financent notre domaine."),
]

FLAG_SCHEMA = ('[{"id":"court-slug","name":"nom du flag","what":"l_événement observable en 1 phrase",'
 '"why_window":"pourquoi ça ouvre une fenêtre de déplacement MAINTENANT",'
 '"strength":1-10 (force du signal de déplacement),'
 '"sillage":{"detectable":true|false,"agent_type":"keyword_detection|job_posting_keyword_detection|job_update|customer|champion|competitor|null",'
 '"watchlist":"customer-companies|customer-profiles|competitor-companies|null","keywords":["mots-clés FR à traquer",...]},'
 '"other_detection":"si Sillage ne suffit pas : quelle source/outil (site web, presse, G2, job boards, registre...)",'
 '"freq_per_1000_month":estimation honnête du nombre d_occurrences par 1000 comptes surveillés par mois,'
 '"window_days":durée de la fenêtre d_action,'
 '"pitch_angle":"l_angle d_ouverture en 1 phrase (jamais dénigrer le concurrent)",'
 '"false_positive":"le risque de faux positif principal + le garde-fou"}]')

def gen_flags(cat_id, brief, n=2):
    def one(k):
        u = (f"CATÉGORIE : {brief}\n\n"
         f"Génère 16 RED FLAGS distincts et SPÉCIFIQUES de cette catégorie (variante {k+1} : "
         + ("les plus fréquents/robustes" if k == 0 else "les plus malins/non-évidents, que personne ne surveille") +
         "). Pense TOUS SECTEURS (agences, SaaS, industrie, services pro, BTP...). Chiffre freq_per_1000_month "
         "honnêtement (la plupart des flags sont RARES : 0.5-20/1000/mois ; les posts génériques plus fréquents).\n\n"
         "Réponds UNIQUEMENT en JSON strict :\n" + FLAG_SCHEMA)
        r = call(u, system=SYS, max_tokens=13000, label=f"{cat_id}-{k}")
        arr = arr_from(r["text"])
        for f in arr: f["category"] = cat_id
        return arr, r
    return [one(k) for k in range(n)]

# ─── B) DISCOVERY PLAYBOOK ───
DISCOVERY_U = ("MISSION : constituer la base « CLIENTS DES CONCURRENTS » la plus riche possible (l'actif central de V3). "
 "Liste 18-24 MÉTHODES distinctes pour identifier les clients d'un concurrent donné, TOUTES sources : site web du "
 "concurrent (logos, cas clients, témoignages, portfolio, blog), posts LinkedIn du concurrent (via Sillage "
 "top_account_content + Claude extraction), posts des CLIENTS qui remercient/mentionnent, avis G2/Capterra/Trustpilot, "
 "offres d'emploi des clients qui mentionnent l'outil du concurrent, pages partenaires, études de cas PDF, webinaires/"
 "événements co-brandés, presse, registres publics (marchés publics BOAMP/appels d'offres attribués), GitHub/intégrations "
 "techniques, DNS/technographie (BuiltWith/Wappalyzer), Featured customers/PeerSpot, LinkedIn 'Pages affiliées/Also viewed'. "
 "Pour CHAQUE méthode, sois opérationnel.\n\nRéponds UNIQUEMENT en JSON strict :\n"
 '[{"id":"slug","method":"nom","how":"le mode opératoire concret en 2-3 phrases","tooling":"Sillage (quelle primitive)|Claude|scraping simple|API tierce (laquelle)",'
 '"yield_estimate":"combien de clients identifiables par concurrent (fourchette honnête)","reliability":1-10,'
 '"cost":"gratuit|crédits Sillage|abonnement tiers ~X€","legal_note":"CGU/RGPD en 1 phrase honnête","sector_fit":"tous|SaaS|agences|industrie|..."}]')

# ─── C) FAILLES CONCURRENT ───
FAILLES_U = ("MISSION : la couche FAILLES — surveiller le CONCURRENT lui-même pour trouver les LEVIERS de persuasion "
 "au moment du démarchage de son client. Liste 20-26 signaux de faille côté concurrent, avec pour chacun le levier "
 "commercial qu'il arme (sans jamais dénigrer frontalement). Exemples de familles : hémorragie de talents (départs "
 "clés, vague de départs support/CSM), dégradation produit/service (avis récents négatifs, incidents publics, hausse "
 "de prix annoncée, sunset de fonctionnalité), distraction stratégique (levée qui déplace le focus upmarket, rachat, "
 "pivot, nouvelle cible), fragilité économique (licenciements, gel d'embauches, fermeture de bureau), sur-croissance "
 "(afflux de clients → qualité de service qui chute), dépendance (le concurrent perd son propre partenaire clé).\n\n"
 "Réponds UNIQUEMENT en JSON strict :\n"
 '[{"id":"slug","name":"nom de la faille","what":"le signal observable","sillage":{"detectable":true|false,"agent_type":"...","keywords":[...]},'
 '"other_detection":"autre source si besoin","levier":"comment l_utiliser dans le discours SANS dénigrer (posture aspirine)",'
 '"strength":1-10,"freq_per_competitor_year":estimation honnête,"guard":"le garde-fou éthique/factuel"}]')

if __name__ == "__main__":
    t0=time.time(); TIN=TOUT=0
    print("═══ V3 · EXPLORATION MASSIVE — flags + discovery + failles (Fable 5) ═══")
    tasks = []
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {}
        for cid, brief in CATS:
            for k in range(2):
                def mk(cid=cid, brief=brief, k=k):
                    u = (f"CATÉGORIE : {brief}\n\n"
                     f"Génère 16 RED FLAGS distincts et SPÉCIFIQUES de cette catégorie (variante {k+1} : "
                     + ("les plus fréquents/robustes" if k==0 else "les plus malins/non-évidents, que personne ne surveille") +
                     "). Pense TOUS SECTEURS (agences, SaaS, industrie, services pro, BTP...). Chiffre freq_per_1000_month "
                     "honnêtement (la plupart des flags sont RARES : 0.5-20/1000/mois ; les posts génériques plus fréquents).\n\n"
                     "Réponds UNIQUEMENT en JSON strict :\n" + FLAG_SCHEMA)
                    r = call(u, system=SYS, max_tokens=13000, label=f"{cid}-{k}")
                    arr = arr_from(r["text"])
                    for f in arr: f["category"] = cid
                    return ("flag", arr, r)
                futs[ex.submit(mk)] = f"{cid}-{k}"
        futs[ex.submit(lambda: ("discovery", arr_from(call(DISCOVERY_U, system=SYS, max_tokens=14000, label="discovery")["text"]), None))] = "discovery"
        # NB: discovery/failles refaits proprement ci-dessous pour capturer l'usage
        flags=[]; disc=[]; failles=[]
        for f in cf.as_completed(futs):
            kind, arr, r = f.result()
            if r: TIN+=r.get("in",0); TOUT+=r.get("out",0)
            if kind=="flag": flags+=arr
            elif kind=="discovery": disc=arr
            print(f"  ✓ {futs[f]:28} {len(arr):>3} items")
    # discovery (si vide) + failles en direct
    if not disc:
        r = call(DISCOVERY_U, system=SYS, max_tokens=14000, label="discovery")
        disc = arr_from(r["text"]); TIN+=r.get("in",0); TOUT+=r.get("out",0)
        print(f"  ✓ discovery(retry) {len(disc)} items")
    r = call(FAILLES_U, system=SYS, max_tokens=14000, label="failles")
    failles = arr_from(r["text"]); TIN+=r.get("in",0); TOUT+=r.get("out",0)
    print(f"  ✓ failles {len(failles)} items")

    for i,f in enumerate(flags): f["fid"]=f"F{i:03d}"
    json.dump(flags, open(f"{OUT}/flags_raw.json","w"), ensure_ascii=False, indent=0)
    json.dump(disc, open(f"{OUT}/discovery.json","w"), ensure_ascii=False, indent=1)
    json.dump(failles, open(f"{OUT}/failles.json","w"), ensure_ascii=False, indent=1)
    cost=TIN/1e6*3+TOUT/1e6*15
    print(f"\n→ {len(flags)} flags bruts · {len(disc)} méthodes discovery · {len(failles)} failles")
    print(f"→ {time.time()-t0:.0f}s · ~${cost:.2f} · v3/flags_raw.json + discovery.json + failles.json")
