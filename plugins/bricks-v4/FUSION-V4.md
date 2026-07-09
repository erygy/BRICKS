# BRICKS V4 — LA FUSION
### Un seul moteur, trois questions : QUI (fit) × QUAND (fenêtre) × COMMENT (levier)

> Fusion **V2 (moteur signal-natif)** × **V3 (déplacement concurrentiel)** — sans régression,
> sans perte, sans doublon. Principe directeur : **V2 et V3 ne répondent pas à la même
> question sur un compte.** Les fusionner n'est donc pas les mélanger — c'est les empiler.
> ⚠️ La page Notion « contexte roadmap » est privée (mur de login) — ce plan s'appuie sur la
> source de vérité locale (repo + field-tests V2 + preuves live V3). À réconcilier avec la
> roadmap Notion dès qu'elle est accessible (publier la page ou coller le contenu).

---

## 0. Le théorème de fusion

| Question | Qui y répond | Actif |
|---|---|---|
| **QUI** — ce compte nous correspond-il ? | **V2** | `score_v2.py` + arbre ICP (P/S/O, intervalles, bandes) |
| **QUAND** — est-ce le moment de le démarcher ? | **V3** | taxonomie de red flags → agents Sillage → fenêtre |
| **COMMENT** — avec quel angle le convaincre ? | **V3+V2** | failles concurrent (levier) + fabrique de messages |
| **COMBIEN** — le motion est-il viable, où dépenser ? | **V2** | `verdict.py` (bayésien) + VOI (chaque crédit sur un flip) |

**L'erreur de mix à ne PAS commettre** (le « mix maladroit » redouté) : fourrer les red flags
dans l'arbre ICP. Un flag n'est pas un signal de fit — c'est un signal de **timing**. Un compte
peut être parfaitement ICP et hors-fenêtre (on ne le démarche pas), ou en fenêtre béante et
hors-ICP (on ne le démarche pas non plus). **Deux arbres, deux scores, croisés au niveau du
dossier** — jamais fusionnés en un score unique illisible.

**L'élégance structurelle** : `score_v2.py` sait déjà faire tourner **plusieurs arbres** (il fait
acquisition + risque-de-churn en V2). V4 lui ajoute un **troisième arbre : la fenêtre de
déplacement** (les flags avec leurs forces, fréquences, anti-double-comptage par cluster).
Un seul moteur déterministe — trois questions. Zéro nouveau moteur à écrire.

---

## 1. L'architecture V4 (les 6 couches)

```
┌──────────── COUCHE 0 · INTAKES (constituer l'univers) ─────────────┐
│  A. MINAGE DÉPLACEMENT (V3, prouvé live)   B. SOURCING FROID (V1/V2)│
│  concurrents → posts/site/avis/jobs        API gouv, firmo, listes  │
│  → clients avec evidence+certainty         → comptes froids         │
│        provenance = "stolen"                  provenance = "cold"   │
└──────────────────────────┬──────────────────────────────────────────┘
┌──────────── COUCHE 1 · FIT (V2 tel quel) ──────────────────────────┐
│  score_v2 × arbre ICP → IN / BAND / OUT (par compte, 0 token)      │
└──────────────────────────┬──────────────────────────────────────────┘
┌──────────── COUCHE 2 · FENÊTRE (V3) ───────────────────────────────┐
│  watchlists Sillage (customer-companies + profils sponsors)         │
│  packs d'agents (8-12, quota-aware) → poll quotidien signals/query  │
│  → score_v2 × arbre FLAGS → fenêtre OUVERTE / TIÈDE / FERMÉE       │
└──────────────────────────┬──────────────────────────────────────────┘
┌──────────── COUCHE 3 · LEVIER (V3, LLM) ───────────────────────────┐
│  fit=IN × fenêtre=OUVERTE → analyse du concurrent en place          │
│  (posts récents, avis, mouvements) → taxonomie failles → LEVIER    │
│  contrainte codée : posture aspirine, zéro dénigrement              │
└──────────────────────────┬──────────────────────────────────────────┘
┌──────────── COUCHE 4 · ACTION (V2 tel quel) ───────────────────────┐
│  VOI gate → FullEnrich (search 0,25 comité → email 1 au dossier)    │
│  messaging_factory (ressources fermées : evidence + flag + levier)  │
│  outreach_send (dry-run défaut, triple clé) → crm_adapter           │
└──────────────────────────┬──────────────────────────────────────────┘
┌──────────── COUCHE 5 · DÉCISION (V2 étendu) ───────────────────────┐
│  verdict.py PAR PROVENANCE (stolen ≠ cold : seuils distincts)       │
│  + PAR CONCURRENT (quel rival est le meilleur gisement ?)           │
└──────────────────────────────────────────────────────────────────────┘
```

## 2. La matrice anti-doublon (chaque capacité n'existe qu'à UN endroit)

| Capacité | Source unique en V4 | Ce qu'on NE refait pas |
|---|---|---|
| Scoring déterministe (3 arbres) | `bricks-v2/tools/score_v2.py` **importé** | ré-écrire un scorer V3 ✗ |
| Résolution nom→domaine | `bricks-v2/tools/domain_resolver.py` | scraper DDG à nouveau ✗ |
| Fabrique de messages | `bricks-v2/tools/messaging_factory.py` (ressources = evidence/flag/levier) | prompt ad-hoc V3 ✗ |
| Verdict de viabilité | `bricks-v2/tools/verdict.py` + config **par provenance** | métriques bricolées ✗ |
| Envoi gated / CRM | `outreach_send.py` / `crm_adapter.py` | ✗ |
| Adapter Sillage | `bricks-v2/tools/sillage_adapter.py` **mis à jour** (spec réelle gelée : chemins confirmés, watchlists, contents) | un 2ᵉ client HTTP V3 ✗ |
| Adapter FullEnrich | `bricks-v2/tools/fullenrich_adapter.py` (REST) + MCP enregistré | ✗ |
| **NOUVEAU** Minage clients | `bricks-v4/client_miner.py` (prototype prouvé : `_proofs/mine_clients.py`) | — |
| **NOUVEAU** Taxonomies | `bricks-v4/flags/` (flags classés, packs d'agents, failles) | — |
| **NOUVEAU** Daemon de veille | `bricks-v4/displacement_daemon.py` (poll → arbre fenêtre → file de dossiers) | — |
| **NOUVEAU** Rival Board | vue par concurrent (JSON d'abord ; UI = lane front de Rémi, pas un 2ᵉ front) | ✗ |

**Mécanique d'import sans fork** : `bricks-v4` n'embarque AUCUNE copie de code V2 — il importe
par chemin relatif (`../bricks-v2/tools`). Un fix dans V2 profite à V4 instantanément ; aucun
drift possible. Les deux plugins restent installables indépendamment (V4 déclare sa dépendance).

## 3. Ce que V4 corrige à CHAQUE monde (le « meilleur des deux »)

**Ce que V3 apporte à V2** :
1. Un **univers chaud** : les comptes minés ont un besoin prouvé et un budget existant — le
   sourcing froid (API gouv) devient le complément, plus le cœur.
2. Le **timing** : V2 savait dire « ce compte est ICP », jamais « c'est maintenant ». L'arbre
   fenêtre le dit, avec des événements datés.
3. Le **levier** : l'angle du message n'est plus générique — c'est la faille du concurrent au
   moment T.
4. **Sillage réel** : la spec gelée + les tests live remplacent le mock partout.

**Ce que V2 apporte à V3** :
1. La **discipline du scoring** : sans l'arbre de fenêtre (anti-double-comptage, bandes), les
   257 flags seraient un déluge d'alertes — exactement la douleur n°3 de l'exploration de masse.
2. La **discipline du crédit** (VOI) : V3 seul enrichirait toute la base (ruineux) ; V4 ne paie
   FullEnrich que sur flip de décision.
3. La **falsifiabilité** (verdict.py) : « voler des clients » devient un motion mesuré
   par concurrent — on sait au bout de N dossiers si un rival est un bon gisement.
4. Les **garde-fous d'envoi** (drafts only, dry-run, caps) et le writeback CRM.

## 4. Les pièges de fusion identifiés (et leur parade)

| Piège | Parade codée |
|---|---|
| Mélanger fit et fenêtre en un score unique | 2 arbres, 2 scores ; croisement uniquement au dossier |
| Seuils de verdict communs cold/stolen | `verdict-config` **par provenance** (les taux de réponse n'ont rien à voir) |
| Ré-implémenter un scorer/messenger côté V3 | import direct des tools V2 (§2) — zéro copie |
| Déluge de flags = alerte-fatigue | tiers A/B/C ; seul le tier A déclenche seul ; B exige un cumul ; C ne fait que scorer |
| Exploser le quota Sillage | packs consolidés (8-12 agents, pas 150) ; watchlists par vagues ; comptes `certainty=haute` d'abord |
| Dénigrement du concurrent (déloyal) | posture aspirine dans le prompt de fabrique + lint anti-dénigrement sur chaque draft |
| Écraser le travail de l'équipe (workspace live partagé) | préfixe `v4-` sur agents/watchlists créés ; jamais de delete ; doc de cohabitation |
| Deux fronts concurrents | Rival Board = JSON/CLI ; l'UI passe par la lane front existante |

## 5. Séquence de construction (ordre de moindre regret)

1. **Geler l'adapter** : mettre à jour `sillage_adapter.py` sur la spec réelle (chemins
   confirmés → statuts `documented`) — bump version, coordination équipe (surface partagée V2).
2. **`client_miner.py`** : industrialiser le prototype prouvé (posts → clients) + site web
   (logos/cas clients) + avis. Sortie : `stolen_targets` avec evidence/certainty/provenance.
3. **Arbre fenêtre** : compiler `flags_ranked.json` au format arbre score_v2 (les tiers A/B/C
   deviennent P/S/O) + créer les packs d'agents (préfixe `v4-`).
4. **Daemon** : poll quotidien → scoring fenêtre → file de dossiers (fit×fenêtre×levier).
5. **Fabrique réarmée** : ressources = evidence minage + flag daté + levier faille.
6. **Verdict par provenance/concurrent** + Rival Board JSON.
7. **Field-test réel** (méthode BRICKS) : 1 entreprise réelle (Eurobrand ? un client design de
   Thomas ?), 5-8 concurrents, base minée, 2 semaines de veille, premiers dossiers.

## 6. Non-régression (le contrat)

- `plugins/bricks` (V1) et `plugins/bricks-v2` : **aucun fichier modifié** sauf la mise à jour
  volontaire et coordonnée de `sillage_adapter.py`/`sillage.endpoints.json` (amélioration pure :
  des chemins `to_confirm` deviennent `documented` — le mock reste intact, les tests V2 restent verts).
- `verify.sh` V2 (10/10) doit rester vert après toute graduation V4.
- Les field-tests V1/V2 archivés restent la référence de comparaison.
- APPEL et SECOND AVIS (dossiers hackathon) restent archivés tels quels.
