# Bricks V2 — le moteur signal-natif (pré-construit, prêt pour le Day-1)

**Statut : prototype fonctionnel** (08/07/2026) — conçu et construit en amont de
l'accès Sillage/FullEnrich (hackathon Station F 09/07). Toute la chaîne tourne
dès aujourd'hui en mock sur les **303 entreprises réelles** du field-test V1.

## L'idée en trois phrases

V1 répond à « trouve-moi des entreprises qui ressemblent à X ». V2 répond à
« **j'ai un concept — dis-moi qui l'achèterait, pourquoi, et prouve-le** » :
une équipe d'agents décompose le concept en **milliers de signaux nécessaires**
(3 couches principal/secondaire/optionnel, signaux latents → proxies
observables), les confronte à ce que les sources savent réellement voir
(Sillage, FullEnrich, registres gratuits), et produit un **score de pertinence
par intervalle** dont chaque point est expliqué et sourcé. Le budget de
vérification ne se dépense que là où il change une décision (VOI), et la
campagne rend un **verdict de thèse chiffré** — c'est un instrument de
validation de marché, pas un simple générateur de listes.

## Ce qui est prouvé (aujourd'hui, en mock — post red-team)

- `score_v2.py` : 22 assertions de tests vertes ; identifiabilité « ok » sur
  l'univers réel des 303 ; **26 comptes IN** (pessimiste ≥ 64, enrichissables),
  **top-50 = 98 % de vrais ICP** (vs juge adversarial V1, IN = 96 %) ;
  séparation 10× entre ICP-fit (53,0) et disqualifiés (5,3) ; le repêchage a
  détecté Ponant Technologies (vrai signal de cession écrasé par un kill trop
  large).
- Plan VOI **100 % décisif** : chaque check retenu peut faire changer de bande
  (`flips ≥ 1`) — zéro budget sur des vérifications qui ne décident rien.
- `sillage_adapter.py mock-demo` : chaîne 1→6 complète (résolution domaines →
  push des comptes → persona → 3 agents compilés depuis l'arbre → run →
  signaux → évidence) ; le re-scoring déplace les entreprises signalées de
  +40 pts en moyenne.
- `fullenrich_adapter.py` : final à ~95 % (OpenAPI publique complète), smoke
  test officiel à 0 crédit prêt, erreurs 402/429 gérées.
- **Red-team adversarial passé** (rapport exécutable) : 2 bloquants + 6 sérieux
  corrigés le soir même — contribution S amortie (un « typique » faux ne tue
  plus un prospect), bornes pondérées par la couverture (IN atteignable, OUT
  protecteur), VOI décision-first, I/O externes blindées, mutation d'évidence
  supprimée, gel légal (`legal_hold`) des signaux personne-physique en
  attente de validation juriste.
- **La fabrique de messages tourne** (`messaging_factory.py demo`) : 5 signaux
  clés sélectionnés → tableau matérialisé (203 lignes, 9 colonnes, groupable
  par signal clé dans l'UI) → 4 groupes pour l'AXE-MAPPER → 2 axes nommés avec
  prompts d'axe → 26 ressources IN → prompts compilés (5,8k car., ressources
  fermées) → 3 mails de démonstration sous email-craft (88/93/58 mots, même
  axe = mails visiblement différents) : `fixtures/demo-mails.md`.

## Démarrage

```bash
bash verify.sh                            # TOUT vérifier en 1 commande (7/7, zéro clé)
# ou étape par étape :
python3 tools/test_score_v2.py            # les tests
python3 tools/score_v2.py demo            # scoring + VOI sur l'univers réel
python3 tools/messaging_factory.py demo   # la fabrique de messages
python3 tools/verdict.py demo             # le moteur de verdict OUI/NON
python3 tools/sillage_adapter.py mock-demo # la chaîne Sillage en mock
```

Accès reçus → suivre **DAY1-SILLAGE.md** (45 min).

## Carte du dossier

| Chemin | Rôle |
|---|---|
| `ARCHITECTURE.md` | La conception complète (chaîne A→Z, scoring, VOI, équipe, risques) |
| `DAY1-SILLAGE.md` | Le rituel de branchement du jour J |
| `agents/` | 9 agents : strategist, signal-architect, critic, broker, prospector, verifier, connector, **axe-mapper (Opus 4.8)**, composer |
| `skills/` | campaign-v2 (A→Z), concept-to-signals, sillage-connect, score-v2, **prompt-smith-outreach** (« je sais créer des prompts pour écrire des mails »), **email-craft** (« je sais écrire un mail ») |
| `messaging/` | **FORMATS.md + formats.json** — les supports de prospection (email parfait, relance, breakup, DM, invite, mini-audit) |
| `tools/score_v2.py` | Le noyau de scoring (déterministe, stdlib, testé) |
| `tools/messaging_factory.py` | **La fabrique de messages** : tableau des signaux clés → axes → base (axe×format) → ressources → prompts compilés |
| `tools/verdict.py` | **Le moteur de verdict GTM** : VIABLE/NON_VIABLE/CONTINUE (bayésien séquentiel, seuils BUSINESS codés) + ledger coût/RDV |
| `tools/domain_resolver.py` | **Résolution nom→domaine zéro-clé** (testée réel) — la jointure vers Sillage/FullEnrich |
| `tools/outreach_send.py` | **L'envoi réel sous triple clé** (dry-run défaut, GO campagne, caps) + détection de réponses IMAP |
| `tools/pipeline_monitor.py` | **Moniteur de risque de pipeline** (4ᵉ archétype) — le MÊME score_v2 pointé sur un arbre de RISQUE, nourri des signaux Sillage champion/competitor/M&A |
| `tools/crm_adapter.py` | **CRM auto-updater** (writeback) — upsert Account + Task par domaine (Salesforce/HubSpot/Attio), mock + stub REST |
| `tools/demo_e2e.py` | **La démo « live wire »** : 4 archétypes, 1 moteur, 3 piliers, en 0,4 s |
| `tools/sillage_adapter.py` | Anti-corruption layer Sillage (mock + REST + découverte MCP) |
| `tools/fullenrich_adapter.py` | FullEnrich (bulk, webhook HMAC, smoke 0 crédit) |
| `GTM-TEST-MEMOVAL.md` | **Le test de viabilité 14 jours** (~100 €, verdict codé d'avance) |
| `PITCH.md` | Le pitch hackathon + démo live minute par minute |
| `schema/` | Schémas thèse/signal/capacités + manifest endpoints Sillage |
| `fixtures/` | Thèse & arbre MemoVAL, univers réel 303, catalogue Sillage, **demo-axes / demo-resources / demo-mails** |

## Rapport à V1

V2 ne remplace rien : c'est un **cerveau au-dessus de la plomberie V1**
(db.py porte unique, statuts, engine runner/researcher réutilisé comme fleet
de vérification, gates de dépense §8, data-plane §10). Les briques V1
restent invocables — V2 leur fournit de meilleures listes et de meilleures
accroches. Dossier volontairement séparé (`plugins/bricks-v2/`), non câblé
au marketplace : à brancher après revue Rémi/Robin.
