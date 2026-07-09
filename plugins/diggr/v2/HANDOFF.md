# HANDOFF — Bricks V2 (moteur signal-natif) + fabrique de messages

> **À lire en premier.** Ce document est le point d'entrée unique du travail
> de Thomas des 8-9 juillet 2026 : un test scientifique de la V1 sur un cas
> réel, puis la conception + le prototype d'une V2 signal-native prête à
> brancher sur Sillage/FullEnrich au hackathon. Tout est ici ou pointé d'ici.
>
> Lecteur cible : Rémi / Robin (ou tout collaborateur reprenant le sujet).
> Auteur : Thomas Jebabli, assisté de Claude (Fable 5). Rien n'est câblé au
> marketplace ni commité sur `main` — c'est une proposition à revoir ensemble.

---

## 1. TL;DR (30 secondes)

- **Vérifie tout en 1 commande** : `cd plugins/bricks-v2 && bash verify.sh`
  → 7/7 PASS, zéro clé, zéro dépendance (stdlib Python 3). Le HANDOFF ne
  demande pas de croire — il demande de lancer.
- **V2 est un cerveau au-dessus de la plomberie V1** : « j'ai un concept →
  qui l'achète, pourquoi, prouve-le, dois-je continuer ? ». Concept → thèse
  falsifiable → arbre de signaux (3 couches P/S/O, latent→proxies) → **score
  par intervalles + budget dépensé seulement là où il décide (VOI)** →
  **fabrique de messages** (signaux clés → axes → formats → mails) →
  **envoi réel gated** → **moteur de verdict OUI/NON**.
- **Testé scientifiquement, deux fois** (mêmes juges adversariaux, même
  univers de 303 PME réelles) : V1 45 %→75 % en 3 corrections manuelles ;
  **V2 90 % du premier coup, 0 correction** ; mails 8,5/10, 0 hallucination,
  0 crédit. Preuves : `_field-test-v1-memoval/` et `_field-test-v2-memoval/`.
- **La boucle est fermée jusqu'aux premiers clients** : `verdict.py`
  (viabilité bayésienne), `domain_resolver.py` (jointure zéro-clé, testé réel),
  `outreach_send.py` (envoi triple-clé + détection de réponses), et un plan de
  test exécutable **GTM-TEST-MEMOVAL.md** (~100 €, verdict codé d'avance).
- **Il reste : la revue avec vous + le branchement réel** (DAY1-SILLAGE.md) —
  rien n'est câblé au marketplace ni commité.

---

## 2. D'où ça vient — le field-test qui a motivé la V2

Dossier : **`_field-test-v1-memoval/`** (rapatrié du scratchpad éphémère —
sinon perdu).

- Protocole **pré-enregistré** (hypothèses + seuils fixés AVANT le run) :
  `PROTOCOL.md`.
- Résultat clé : `H2-precision-45-65-75.json` — précision ICP jugée par un
  agent adversarial, n=20, sur 3 cycles de correction :
  - **45 %** (le panier NAF aspirait l'ingénierie 71.12B = l'anti-ICP)
  - → **65 %** (blacklist secteurs)
  - → **75 %** (filtre filiales + plancher d'ancienneté).
- Ce que ça a appris, et qui fonde la V2 : **la pertinence n'est pas magique,
  elle se calibre** ; et **pour MemoVAL le signal d'achat est un ÉTAT
  firmographique** (dirigeant 58-68 + société mûre indépendante), pas un
  événement presse — d'où un moteur qui raisonne en *signaux nécessaires*,
  pas en mots-clés.
- `scorecard.html` = la présentation visuelle du test (double-cliquer).
  `memoval-offer.md` / `memoval-icp.md` = le contexte produit (kill-rules
  patchées incluses). `drafts-5-comptes.json` = les 5 mails CPPC produits
  (8,4/10, 100 % sans hallucination).
- **Non-testé (pas de clés) :** FullEnrich (emails) et Bright Data (scraping).
  À garder honnête en présentation.

---

## 3. Ce qui a été construit (la V2)

La conception complète est dans **`ARCHITECTURE.md`** (à lire en 2ᵉ). Résumé
de la chaîne A→Z :

```
« j'ai une idée » → THÈSES falsifiables → arbre de SIGNAUX (P/S/O, latent→proxy)
   → CRITIC tue les fausses nécessités → BROKER matche signaux↔capacités sources
   → PROSPECTOR (univers registre gratuit + push Sillage) → SCORE par intervalles
   → VOI (budget only sur la bande d'incertitude) → CONNECTOR (FullEnrich sur IN)
   → FABRIQUE DE MESSAGES → SEND-GUARD (envoi gated) → VERDICT DE THÈSE chiffré
```

### Les 3 idées qui font le moat (« la subtilité »)
1. **Latent vs proxy** : ~50-150 signaux latents/thèse × 5-30 proxies chacun
   = milliers de sous-signaux, sans soupe (poids ordinaux au niveau latent,
   fidélité/couverture/coût au niveau proxy, clusters plafonnés anti-double-comptage).
2. **Score = intervalle** [pessimiste, attendu, optimiste] → bandes
   **IN / BAND / OUT** ; le budget de vérification ne se dépense QUE sur la
   BAND, check le plus décisif d'abord (VOI décision-first : `flips ≥ 1`).
3. **La fabrique de messages** (schéma manuscrit de Thomas) : le TABLEAU gagne
   des colonnes = **signaux clés** → un agent Opus 4.8 en tire des **AXES**
   (segments-histoires) → croisés avec des **FORMATS** (email parfait, relance…)
   → **RESSOURCES** (les faits dispo par entreprise) → **prompt sur mesure** →
   LLM « je sais écrire un mail ». Chaque mail porte `axe` + `format` → on
   mesure quel axe et quel format marchent (n≥25 sinon abstention).

### Inventaire
- **9 agents** (`agents/`) : strategist, signal-architect, critic, broker,
  prospector, verifier, connector, **axe-mapper (Opus 4.8)**, composer.
- **6 skills** (`skills/`) : campaign-v2 (l'orchestrateur A→Z),
  concept-to-signals, sillage-connect, score-v2, **prompt-smith-outreach**
  (« je sais créer des prompts pour écrire des mails »), **email-craft**
  (« je sais écrire un mail »).
- **5 outils** (`tools/`) : `score_v2.py` (noyau déterministe + 22 tests),
  `messaging_factory.py` (la fabrique), `sillage_adapter.py`,
  `fullenrich_adapter.py`, `test_score_v2.py`.
- **messaging/** : `FORMATS.md` + `formats.json` (les supports de prospection).
- **schema/** : thèse / signal / capacités + manifest endpoints Sillage.
- **fixtures/** : thèse & arbre MemoVAL, univers réel 303, catalogue Sillage,
  et les sorties de démo (`demo-axes`, `demo-resources`, `demo-mails.md`).

---

## 4. État prouvé (post red-team, en mock)

| Preuve | Commande | Résultat |
|---|---|---|
| Noyau de scoring | `python3 tools/test_score_v2.py` | **22 assertions vertes** |
| Scoring + VOI sur 303 | `python3 tools/score_v2.py demo` | **26 IN**, top-50 = 98 % ICP-fit V1, séparation 10×, VOI 100 % décisif |
| Chaîne Sillage complète | `python3 tools/sillage_adapter.py mock-demo` | résolution domaines → push → 3 agents compilés → signaux → évidence |
| Fabrique de messages | `python3 tools/messaging_factory.py demo` | 5 signaux clés → tableau (203×9) → 2 axes → 26 ressources → prompts compilés |
| Mails générés | `fixtures/demo-mails.md` | 3 mails, même axe = mails distincts, 88/93/58 mots, 0 invention |

**Red-team** (rapport adversarial ingénieur) : 2 bloquants trouvés et corrigés
le soir même (un signal secondaire faux écrasait les bons prospects ; la bande
IN était inatteignable), + 6 sérieux (I/O externes blindées 402/429, mutation
d'évidence supprimée, collisions de domaines, VOI décision-first). Le
**risque n°1 non-technique** identifié : le RGPD du tracking de dirigeants
nommés → signaux personne-physique **gelés (`legal_hold`)** jusqu'à validation
juriste.

---

## 5. Comment lancer (2 minutes, zéro clé)

```bash
cd plugins/bricks-v2
python3 tools/test_score_v2.py        # les tests
python3 tools/score_v2.py demo        # scoring + VOI sur l'univers réel
python3 tools/sillage_adapter.py mock-demo   # la chaîne Sillage en mock
python3 tools/messaging_factory.py demo      # la fabrique de messages
```

Python 3 (stdlib uniquement, aucune dépendance). Le seul mock est la donnée
externe (Sillage/FullEnrich absents) ; toute la logique est réelle et
déterministe.

---

## 6. Demain — brancher pour de vrai

Tout est dans **`DAY1-SILLAGE.md`** (rituel ~45 min). Points durs :
- **Sillage** = `getsillage.com` (⚠️ pas `sillage.ai`, homonyme). MCP OAuth
  (`/api/mcp/v2`) ou REST (`api.getsillage.com/api/v2`, clé `sk_live_`).
  **Identité par domaine/LinkedIn, PAS de SIREN** → une étape de résolution
  de domaine est obligatoire (prévue via l'engine V1 web). **Quota trial =
  cap à VIE** → pousser un contingent, pas l'univers. Pas de webhooks → poller.
- **FullEnrich** = OpenAPI complète, **contact de test à 0 crédit** pour
  valider l'adapter avant de dépenser (email=1 crédit, mobile=10).
- **Gel légal** : ne PAS activer les agents de keyword-tracking sur des
  personnes nommées sans feu vert juridique ; commencer par les offres
  d'emploi de l'ENTREPRISE (sans problème RGPD).

---

## 7. Ce qui a besoin de VOTRE décision (Rémi / Robin)

1. **Câblage** : bricks-v2 est un plugin séparé, non ajouté au marketplace.
   Le fusionner dans `bricks` ou le garder distinct le temps de la V2 ?
2. **Réutilisation V1** : la V2 réutilise db.py, l'engine (runner/researcher),
   les gates §8, les statuts — sans les modifier. À valider que rien ne casse
   le contrat CONVENTIONS partagé (votre surface, PR à deux approbations).
3. **Transport Sillage** : MCP-only probable au hackathon → il reste un
   pont MCP→scripts à écrire (les adapters REST lèvent `NotConfigured` sur les
   endpoints non confirmés). Décider ce soir.
4. **Périmètre démo** : quelle thèse, quel contingent de comptes (quota à vie),
   quels agents (les non-`legal_hold`).

---

## 8. Carte de lecture

1. **HANDOFF.md** (ce fichier) — l'entrée.
2. **ARCHITECTURE.md** — la conception complète (chaîne, scoring, VOI, fabrique, risques).
3. **GTM-TEST-MEMOVAL.md** — LE test de viabilité 14 jours exécutable (seuils codés, ~100 €).
4. **PITCH.md** — le pitch 3 min + démo live minute par minute + objections.
5. **DAY1-SILLAGE.md** — le branchement pas-à-pas.
6. **README.md** — la carte du dossier + démarrage.
7. `_field-test-v1-memoval/` et `_field-test-v2-memoval/` — les deux tests
   scientifiques (protocoles, résultats 45→75 % et 90 %, conseil
   BUSINESS+GROWTH, scorecards).
8. `agents/`, `skills/`, `messaging/` — les définitions (lisibles seules).

## 8bis. La couche « machine à décision » (ajoutée le 08/07 au soir)

Quatre outils ferment la boucle jusqu'aux premiers clients :
- **`tools/verdict.py`** — le moteur de verdict GTM : décision séquentielle
  bayésienne (VIABLE / NON_VIABLE / CONTINUE + n manquant), abstention
  sous n=25, validation IN-vs-témoin, ledger coût/RDV. Seuils calibrés par
  l'agent BUSINESS dans `messaging/verdict-config.json`.
- **`tools/domain_resolver.py`** — résolution nom→domaine ZÉRO CLÉ
  (DuckDuckGo lite + heuristiques slug + vérification de contenu),
  testée en réel : 4/8 résolus dont elec4.fr trouvé, faux positifs éliminés
  par durcissement. Qualité avant rappel (quota Sillage à vie).
- **`tools/outreach_send.py`** — l'envoi RÉEL sous triple clé (dry-run par
  défaut, GO campagne obligatoire, caps/fenêtres codés), détection de
  réponses IMAP → gel de séquence, export → verdict.
- **`messaging/verdict-config.json`** — benchmarks et seuils BUSINESS/GROWTH
  (réponse 4-9 %, RDV 1,5-4 %, close 10-18 % ; OUI ≥4 positives ou ≥3 RDV
  sur 60 ; NON à 120 si 0 RDV et ≤1 positive).

---

## 9. Ce qui est éphémère (à savoir)

- Le workspace de test `memoval-outbound` vivait dans le scratchpad
  `/private/tmp` — **il n'existe plus après la session**. Ses résultats
  durables sont dans `_field-test-v1-memoval/` (rapatriés) et reproductibles
  depuis `fixtures/mock-universe.jsonl` (les 303 entreprises).
- La scorecard est aussi publiée en ligne (artifact claude.ai) — mais la copie
  `_field-test-v1-memoval/scorecard.html` est autonome, ouvrable hors ligne.
