# BRICKS-FINAL — base curée pour la v3 (« Signal Interceptor »)

Sélection minimale extraite de Bricks-v2 : **le moteur qui survit** au passage
sur le stack sponsors (Claude + Sillage + FullEnrich), débarrassé de tout le
scraping maison et du packaging plugin. C'est la fondation de la nouvelle
version du projet — pas une application complète.

> ⚠️ **Ce repo n'est PAS le repo de soumission du hackathon.**
> Règle de l'événement : « Build entirely during the event. No prior commits. »
> Ce dépôt sert de référence/fondation ; le jour J, on repart d'un repo vierge
> (ou on le déclare comme dépendance open-source créditée SI les organisateurs
> valident explicitement).

## Structure

```
tools/core/           le moteur (inchangé, chemins repo-relatifs)
  db.py               la SEULE porte vers SQLite — tables/colonnes dynamiques,
                      claim atomique, import-csv, receipts JSON
  runner.py           LA boucle batch — preview 10 → GO → commit, statuts,
                      claims par tranches, rollback
  agent.py            un prompt → une réponse (transport SDK abonnement)
  agent_api.py        même contrat via l'API Anthropic (BRICKS_AGENT_TRANSPORT=api)
  workspace.py        cycle de vie workspace (bricks/ + config.json + context/)
  envfile.py          chargement ~/.bricks/env
  session_auth.py     détection d'auth (dépendance d'agent.py)
tools/providers/
  fullenrich.py       recherche personnes + cascade d'enrichissement (child rows)
skills/               les playbooks GARDÉS comme matière première (voir bas)
templates/context/    gabarits offer/icp/personas copiés par workspace.py new
CONVENTIONS.md        le contrat runtime (adapté : chemins relatifs, plus de namespace)
```

## Gardé / jeté (depuis Bricks-v2)

**Gardé** : le core complet, `fullenrich.py`, et 9 skills-matière première :
`gtm-onboard`, `context-write`, `enrich`, `rank-accounts`, `plan-outreach`,
`write-outreach`, `playbook-outbound`, `workspace`, `tools-guide`.

**Jeté** : `jobs.py`, `news.py`, `firmo.py` (remplacés par Sillage/FullEnrich),
toute la voie Bright Data, le front table (`front/`), le packaging plugin
(`.claude-plugin`, hooks, session_start), et 16 skills liées au scraping ou
hors scope (find*, enrich-buying-committee, enrich-person-profile,
signal-person, score, transform, interface, scan-mentions, lookalike*,
create-landing-page, brickgent, tools de session).

## À construire (volontairement absent — rien n'est codé ici)

| Brique | Rôle | S'appuie sur |
|---|---|---|
| `tools/providers/sillage.py` | persona, top-accounts, watchlists, agents, pull signaux → table `signals`, `add_signal` (démo) | pattern de `fullenrich.py` |
| `tools/providers/emelia.py` | campagne, push contacts, stats retour | — |
| `tools/core/score.py` | scoring déterministe : poids/type × décote fraîcheur × signaux des collègues | kernel de `skills/rank-accounts/scripts/rank.py` |
| Schéma 5 tables | competitors, companies, contacts, signals, outreach | `db.py` (colonnes dynamiques : zéro migration) |
| 4 skills maigres | onboard / surveil / prioritize / outreach | distillées des 9 gardées |
| Front graphe | tables + écran graphe (Cytoscape) + fiche cold-call | neuf (l'ancien front était table-only) |

## Références périmées connues (assumées, à résoudre dans la v3)

Les skills gardées mentionnent encore des briques jetées — c'est de la
matière première, pas du produit fini : `playbook-outbound` chaîne `/score` et
`/signal-person` (→ futures briques scoring/surveil) ; `enrich`,
`plan-outreach`, `rank-accounts`, `CONVENTIONS.md` citent `/brickgent`,
`/find*` ou `/interface` par endroits ; `agent.py --web` référence Bright Data
(optionnel, non-sponsor — ne pas utiliser au hackathon).

## Démarrage

```bash
# secrets dans ~/.bricks/env (chmod 600) :
#   ANTHROPIC_API_KEY=...            # crédits hackathon
#   BRICKS_AGENT_TRANSPORT=api       # forcer la voie API
#   FULLENRICH_API_KEY=...
python3 tools/core/workspace.py status   # ne crée rien, rapporte l'état
```
