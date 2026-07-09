#!/usr/bin/env python3
"""BRICKS V4 — constructeur du jeu de données de démonstration (RÉEL, pas lorem).
Assemble seed.json depuis : les clients minés live (mined_clients.json), la
taxonomie de flags classée (flags_ranked.json), les failles (failles.json), les
comptes Sillage réels (live-accounts.json). Le BRIEF d'un compte est généré par
Fable 5 (contenu réel, sous contrainte JSON), le reste est déterministe.

Rôles des 3 arbres rendus visibles : FIT (qualité, IN/BAND/OUT → tier A/B/C),
FENÊTRE (timing, OPEN/WARM/CLOSED depuis les flags), LEVIER (faille du rival)."""
import json, os, sys, hashlib, math

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "_data")
PROOFS = os.path.join(os.path.dirname(HERE), "_proofs")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/plugins/bricks-v2")
# fable_api vit dans _appel-hackathon / _secondavis ; on le copie à côté pour l'import
sys.path.insert(0, HERE)
try:
    from fable_api import call
    HAVE_FABLE = True
except Exception:
    HAVE_FABLE = False

def load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default

mined = load(os.path.join(DATA, "mined_clients.json"), {})
flags = load(os.path.join(DATA, "flags_ranked.json"), [])
failles = load(os.path.join(DATA, "failles.json"), [])
live_accounts = load(os.path.join(PROOFS, "live-accounts.json"), {"data": []})

def slug(s):
    return hashlib.md5(s.encode()).hexdigest()[:8]

def det(seed, lo, hi):
    """pseudo-aléa déterministe [lo,hi] à partir d'une graine texte."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return lo + (h % 1000) / 1000 * (hi - lo)

# ── L'ENTREPRISE UTILISATRICE (démo) ──
COMPANY = {
    "name": "Lumen Search",
    "sector": "SaaS B2B — recherche & découverte produit (AI commerce)",
    "services": ["Search-as-a-service", "Reco produit IA", "Merchandising", "Agentic search"],
    "market": "France + Europe",
    "positioning": "L'alternative européenne, souveraine et frugale aux moteurs de recherche e-commerce US — installée en 2 semaines, pas 6 mois.",
    "tone": "Direct, technique, sans esbroufe",
    "icp": "Retailers & marketplaces 20-500M€ GMV, équipe produit/tech en place, insatisfaits d'un moteur US coûteux et rigide.",
    "description": "Lumen Search fournit un moteur de recherche et de recommandation e-commerce piloté par IA, hébergé en Europe. On remplace les moteurs US (lents à intégrer, chers à l'échelle) par une brique frugale et souveraine, installée en 2 semaines.",
}

# ── LES CONCURRENTS (rivals) — dont les vrais comptes minés live ──
RIVAL_META = {
    "Algolia":  {"domain": "algolia.com",  "linkedin": "algolia",  "note": "le leader US, cher à l'échelle"},
    "Devoteam": {"domain": "devoteam.com", "linkedin": "devoteam", "note": "ESN cloud/data, gros comptes"},
    "Coveo":    {"domain": "coveo.com",    "linkedin": "coveo",    "note": "search enterprise US/CA"},
    "Lucidworks":{"domain": "lucidworks.com","linkedin": "lucidworks","note": "Fusion/Solr, lourd"},
    "Constructor":{"domain": "constructor.io","linkedin": "constructor-io","note": "reco e-commerce US"},
}

# failles → rattachées aux rivals (rotation déterministe)
strong_failles = sorted(failles, key=lambda f: f.get("strength", 0), reverse=True)

rivals = []
for i, (name, meta) in enumerate(RIVAL_META.items()):
    clients = mined.get(name, [])
    fa = strong_failles[i % len(strong_failles)] if strong_failles else {}
    rivals.append({
        "id": "R" + slug(name),
        "name": name, "domain": meta["domain"], "linkedin": meta["linkedin"], "note": meta["note"],
        "client_count": len(clients),
        "faille": {"name": fa.get("name", ""), "levier": fa.get("levier", ""),
                   "strength": fa.get("strength", 0), "guard": fa.get("guard", ""),
                   "what": fa.get("what", "")},
    })

# ── LES COMPTES (accounts) = clients minés (stolen) + quelques froids ──
strong_flags = [f for f in flags if (f.get("sillage") or {}).get("detectable")]
strong_flags = sorted(strong_flags, key=lambda f: f.get("rank_score", 0), reverse=True)

def firmo_for(name, dom):
    ca = int(det(name + "ca", 8, 320))  # M€
    eff = int(det(name + "eff", 40, 4000))
    age = int(det(name + "age", 6, 40))
    return {"ca_eur": f"{ca}M€", "effectif": eff, "age_societe": age,
            "pays": ["France", "UK", "Allemagne", "Espagne", "US", "Suède"][int(det(name, 0, 5.99))],
            "domain": dom}

FAMILY_ICON = {"recrutement_interne": "hire", "mouvements_personnes": "move", "posts_communication": "post",
               "corporate_events": "corp", "relation_client_concurrent": "link", "evenements_ecosysteme": "event",
               "besoins_manifestes": "need", "cycles_budget_contrat": "budget"}

accounts = []
signals_feed = []
aidx = 0
for rival in rivals:
    clients = mined.get(rival["name"], [])
    for c in clients:
        aidx += 1
        cname = c.get("client", "?")
        dom = (cname.lower().replace(" ", "").replace("'", "") + ".com")
        aid = "A" + slug(rival["name"] + cname)
        # FIT déterministe (qualité) — les 'haute' certitude scorent mieux
        cert = c.get("certainty", "moyenne")
        base = {"haute": 72, "moyenne": 58, "basse": 44}.get(cert, 50)
        expected = round(base + det(aid + "fit", -8, 14), 1)
        pess = round(max(0, expected - det(aid + "p", 8, 22)), 1)
        opt = round(min(100, expected + det(aid + "o", 6, 18)), 1)
        band = "IN" if expected >= 62 else ("BAND" if expected >= 50 else "OUT")
        tier = {"IN": "A", "BAND": "B", "OUT": "C"}[band]
        # FENÊTRE (timing) — on attache 0-3 flags datés
        nflags = int(det(aid + "nf", 0, 3.6))
        acc_flags = []
        for k in range(nflags):
            f = strong_flags[(aidx * 3 + k) % len(strong_flags)]
            days = int(det(aid + str(k), 1, 40))
            sg = f.get("sillage") or {}
            fl = {"id": "S" + slug(aid + str(k)), "name": f.get("name", ""),
                  "family": f.get("category", ""), "icon": FAMILY_ICON.get(f.get("category"), "post"),
                  "strength": f.get("strength", 5), "days_ago": days,
                  "agent_type": sg.get("agent_type", ""), "pitch_angle": f.get("pitch_angle", ""),
                  "evidence": f.get("what", ""), "window_days": f.get("window_days", 30)}
            acc_flags.append(fl)
            signals_feed.append({**fl, "account": cname, "account_id": aid, "rival": rival["name"]})
        strongest = max([f["strength"] for f in acc_flags], default=0)
        wstate = "OPEN" if strongest >= 7 else ("WARM" if acc_flags else "CLOSED")
        accounts.append({
            "id": aid, "name": cname, "domain": dom, "provenance": "stolen",
            "axis": "client",   # CAPTATION : déjà client du concurrent → on le déplace
            "rival": rival["name"],
            "evidence": c.get("evidence", ""), "certainty": cert, "relation": c.get("relation", ""),
            "fit": {"band": band, "expected": expected, "pessimistic": pess, "optimistic": opt, "tier": tier},
            "window": {"state": wstate, "flags": acc_flags, "strongest": strongest},
            "firmo": firmo_for(cname, dom),
            "faille_rival": rival["faille"],
        })

# ── AXE 2 : INTERCEPTION DE PROSPECTS ── comptes en train d'ÉVALUER le concurrent
# (pas encore clients) → intercepter AVANT la signature. Détectés par signaux d'INTENT.
INTENT_TEMPLATES = [
    ("engagement_contenu", "engage publiquement avec le contenu de {rival} (commentaires, réactions sur ses posts de lancement)", "moyenne", "relation_client_concurrent"),
    ("offre_emploi_outil", "publie une offre d'emploi exigeant « expérience {rival} appréciée » — évaluation ou adoption en cours", "haute", "besoins_manifestes"),
    ("rfp_ouvert", "a ouvert une consultation / RFP où {rival} est pressenti — décision d'achat imminente", "haute", "evenements_ecosysteme"),
    ("demande_reco", "demande publiquement une recommandation d'outil sur notre catégorie, {rival} cité dans les réponses", "moyenne", "besoins_manifestes"),
]
PROSPECT_NAMES = ["Vestio", "Maréa Retail", "Brakonn", "Cielto", "Palmier & Co", "Onhava Group",
                  "Ravel Commerce", "Studio Nord", "Kessler Retail", "Vireo"]
pi = 0
for rival in rivals:
    for k in range(2):  # 2 prospects interceptables par concurrent
        pi += 1
        cn = PROSPECT_NAMES[(pi - 1) % len(PROSPECT_NAMES)]
        tmpl = INTENT_TEMPLATES[(pi - 1) % len(INTENT_TEMPLATES)]
        aid = "P" + slug(rival["name"] + cn + str(k))
        dom = cn.lower().replace(" & ", "").replace(" ", "") + ".com"
        intent_ev = tmpl[1].format(rival=rival["name"])
        cert = tmpl[2]
        base = {"haute": 68, "moyenne": 56}.get(cert, 52)
        expected = round(base + det(aid + "fit", -6, 12), 1)
        band = "IN" if expected >= 62 else ("BAND" if expected >= 50 else "OUT")
        tier = {"IN": "A", "BAND": "B", "OUT": "C"}[band]
        # signal d'intent daté = fenêtre (l'interception est TRÈS sensible au timing)
        days = int(det(aid + "d", 1, 18))
        strg = {"haute": 9, "moyenne": 7}.get(cert, 6)
        fl = {"id": "S" + slug(aid), "name": {"engagement_contenu": "Engagement avec le contenu du concurrent",
              "offre_emploi_outil": "Offre d'emploi mentionnant l'outil concurrent",
              "rfp_ouvert": "Consultation/RFP ouverte, concurrent pressenti",
              "demande_reco": "Demande publique de recommandation d'outil"}[tmpl[0]],
              "family": tmpl[3], "icon": FAMILY_ICON.get(tmpl[3], "need"), "strength": strg, "days_ago": days,
              "agent_type": "competitor" if tmpl[0] == "engagement_contenu" else ("job_posting_keyword_detection" if tmpl[0] == "offre_emploi_outil" else "keyword_detection"),
              "pitch_angle": "Avant de trancher, comparez : installation 2 semaines, prix gelé 24 mois, hébergement européen.",
              "evidence": intent_ev, "window_days": 14}
        signals_feed.append({**fl, "account": cn, "account_id": aid, "rival": rival["name"]})
        accounts.append({
            "id": aid, "name": cn, "domain": dom, "provenance": "stolen",
            "axis": "prospect",   # INTERCEPTION : évalue le concurrent → on intercepte avant la signature
            "rival": rival["name"],
            "evidence": intent_ev, "certainty": cert, "relation": "intent",
            "fit": {"band": band, "expected": expected, "pessimistic": round(max(0, expected-14),1),
                    "optimistic": round(min(100, expected+10),1), "tier": tier},
            "window": {"state": "OPEN" if strg >= 7 else "WARM", "flags": [fl], "strongest": strg},
            "firmo": firmo_for(cn, dom), "faille_rival": rival["faille"],
        })

# quelques prospects FROIDS (cold) — ni client ni prospect d'un concurrent
COLD = [("Maison Ferrand", "retail"), ("Groupe Alteor", "marketplace"), ("Novarue", "e-commerce")]
for cn, kind in COLD:
    aidx += 1
    aid = "A" + slug("cold" + cn)
    expected = round(det(aid, 46, 66), 1)
    band = "IN" if expected >= 62 else ("BAND" if expected >= 50 else "OUT")
    accounts.append({
        "id": aid, "name": cn, "domain": cn.lower().replace(" ", "") + ".fr", "provenance": "cold",
        "axis": "cold", "rival": None,
        "evidence": "", "certainty": None, "relation": None,
        "fit": {"band": band, "expected": expected, "pessimistic": round(expected-12,1), "optimistic": round(expected+9,1),
                "tier": {"IN": "A", "BAND": "B", "OUT": "C"}[band]},
        "window": {"state": "CLOSED", "flags": [], "strongest": 0},
        "firmo": firmo_for(cn, cn.lower().replace(" ", "") + ".fr"), "faille_rival": None,
    })

signals_feed.sort(key=lambda s: (s["days_ago"], -s["strength"]))

# ── LE BRIEF — généré par Fable 5, CONSCIENT DE L'AXE (captation vs interception) ──
# On pré-génère le dossier de TOUS les comptes (démo live 100% robuste, zéro bouton "générer")
brief_targets = list(accounts)

BRIEF_SYS = (
 "Tu es l'analyste de démarchage de Lumen Search (moteur de recherche e-commerce IA, souverain européen, "
 "installé en 2 semaines, alternative frugale aux moteurs US). Tu es factuel, sans slop, tu n'inventes pas de "
 "chiffres précis (ordres de grandeur, tu marques les inconnues). Sortie JSON STRICTE uniquement.")

def gen_brief(a):
    ev = a.get("evidence", ""); rival = a.get("rival", ""); fa = a.get("faille_rival") or {}
    flags_txt = "; ".join(f"{f['name']} (force {f['strength']}, il y a {f['days_ago']}j)" for f in a["window"]["flags"]) or "aucun flag daté"
    if a.get("axis") == "cold":
        situ = (f"COMPTE CIBLE : {a['name']} ({a['domain']}) — PROSPECT FROID (ni client ni évaluateur d'un concurrent identifié).\n"
                f"AXE = prospection classique : ouvrir sur la valeur, sans signal de déplacement.\n")
        msg_hint = "un email de prospection sobre de 5-7 lignes, orienté valeur (installation 2 semaines, souveraineté, frugalité), signé Thomas"
    elif a.get("axis") == "prospect":
        situ = (f"COMPTE CIBLE : {a['name']} ({a['domain']}) — PROSPECT en train d'ÉVALUER {rival} (PAS encore client).\n"
                f"AXE = INTERCEPTION : arriver AVANT la signature, se placer dans l'évaluation, sans dénigrer {rival}.\n"
                f"Signal d'intent : « {ev} »\n")
        msg_hint = "un email d'INTERCEPTION de 6-8 lignes : se placer dans leur évaluation en cours, proposer une comparaison factuelle, jamais dénigrer le concurrent, signé Thomas"
    else:
        situ = (f"COMPTE CIBLE : {a['name']} ({a['domain']}) — actuellement CLIENT de {rival}.\n"
                f"AXE = CAPTATION : le déplacer vers nous en s'appuyant sur un signal de fenêtre + la faille du concurrent.\n"
                f"Preuve du minage : « {ev} »\n")
        msg_hint = "un email de CAPTATION de 6-8 lignes qui accroche sur le signal réel et le levier, jamais dénigrant, signé Thomas — SANS mentionner qu'on les surveille"
    u = (situ +
     f"Firmo (ordres de grandeur) : CA {a['firmo']['ca_eur']}, {a['firmo']['effectif']} employés, {a['firmo']['pays']}.\n"
     f"Signaux de fenêtre : {flags_txt}\n"
     f"Faille du concurrent {rival} : {fa.get('name','')} — {fa.get('what','')} (levier : {fa.get('levier','')}).\n\n"
     "Produis le dossier. JSON STRICT :\n"
     '{"headline":"une phrase : pourquoi ce compte MAINTENANT, selon l_axe",'
     '"key_signals":[{"label":"signal clé","reading":"ce que ça dit sur leur besoin"}],'
     '"strategic_axes":[{"axis":"axe d_approche","why":"pourquoi cet angle pour EUX"}],'
     '"key_members":[{"role":"le RÔLE à contacter (pas un nom inventé)","why":"pourquoi ce point d_entrée","enrich":"ce que FullEnrich doit trouver"}],'
     '"key_figures":[{"figure":"un chiffre/fait d_ordre de grandeur","note":"source/limite"}],'
     f'"pre_written_message":"{msg_hint}",'
     '"levers":[{"lever":"levier de persuasion","proof":"sur quoi il s_appuie"}]}')
    r = call(u, system=BRIEF_SYS, max_tokens=4500, label=a["name"])
    import re
    m = re.search(r"\{.*\}", r["text"], re.S)
    if not m: return None
    try:
        d = json.loads(m.group(0)); d["axis"] = a.get("axis"); return d
    except Exception: return None

briefs = {}
if HAVE_FABLE:
    import concurrent.futures as _cf
    def _one(a):
        b = gen_brief(a)
        if b: b["account_id"] = a["id"]
        return a, b
    print(f"  génération de {len(brief_targets)} dossiers en parallèle (Fable)…")
    with _cf.ThreadPoolExecutor(max_workers=4) as _ex:
        for a, b in _ex.map(_one, brief_targets):
            if b:
                briefs[a["id"]] = b
                print(f"  ✓ {a.get('axis'):8} {a['name']} (volé à {a['rival']})")
            else:
                print(f"  ✗ {a['name']} — échec (sera généré à la demande)")
else:
    print("  (fable_api absent — briefs vides, l'API sera appelée à la volée par le serveur)")

# ── VIABILITÉ (reprise du calcul réel) ──
viability = {"universe": 800, "flags_day": 28, "strong_day": 16, "qualified_week": 76,
             "detectable": 231, "total_flags": len(flags)}

seed = {
    "company": COMPANY,
    "rivals": rivals,
    "accounts": accounts,
    "signals_feed": signals_feed[:60],
    "briefs": briefs,
    "brief_targets": [a["id"] for a in brief_targets],
    "viability": viability,
    "agent_packs_count": 12,
    "stats": {
        "accounts": len(accounts),
        "clients": sum(1 for a in accounts if a.get("axis") == "client"),      # captation
        "prospects": sum(1 for a in accounts if a.get("axis") == "prospect"),  # interception
        "cold": sum(1 for a in accounts if a.get("axis") == "cold"),
        "rivals": len(rivals),
        "signals": len(signals_feed),
        "open_windows": sum(1 for a in accounts if a["window"]["state"] == "OPEN"),
        "tier_a": sum(1 for a in accounts if a["fit"]["tier"] == "A"),
    },
}
json.dump(seed, open(os.path.join(HERE, "seed.json"), "w"), ensure_ascii=False, indent=1)
print(f"\n→ seed.json : {len(accounts)} comptes ({seed['stats']['clients']} captation / "
      f"{seed['stats']['prospects']} interception / {seed['stats']['cold']} froids), "
      f"{len(rivals)} concurrents, {len(signals_feed)} signaux, {len(briefs)} briefs, {seed['stats']['open_windows']} fenêtres ouvertes")
