# BRICKS — « Signal Interceptor », le moteur GTM agentique

Un agent commercial qui **surveille** tes comptes cibles et tes concurrents
(Sillage), **intercepte** les prospects qui discutent avec un concurrent,
**qualifie** tout le monde à la même porte ICP, **score** le « qui appeler
maintenant et pourquoi » (le WHY NOW, preuves à l'appui), **prépare la file
de la semaine**, rédige et audite les messages, puis **envoie** (Emelia) et
rapatrie les retours. Le tout piloté en conversation Claude Code, données
dans SQLite, interface web locale avec fiche cold-call et graphe.

> ⚠️ **Ce repo n'est PAS le repo de soumission du hackathon.**
> Règle de l'événement : « Build entirely during the event. No prior commits. »
> Ce dépôt sert de référence/fondation ; le jour J, on repart d'un repo vierge
> (ou on le déclare comme dépendance open-source créditée SI les organisateurs
> valident explicitement).

## Le pipeline (P0 → P7)

```
P0 onboard      interview : offre + ICP falsifiable + personas + CONCURRENTS
                → context/*.md + table competitors (why_we_win, interest_score)
P1 sourcing     FullEnrich export → CSV → seed/import_p1.py
                → companies (source, qualify_status='pending' armé à l'insert)
P2 qualif       runner --ai (critères STATIQUES d'icp.md ; le dynamique est
                exclu, c'est le travail de Sillage) → icp_verdict + fit_score
P3 surveillance sillage.py setup + watchlist + agents + run
                → tracked (20 slots), watched, agents Bricks
P4 signaux      sillage.py pull (curseur, dédup) + leads → tables signals,
                contacts ; branche competitor* → runner + intercept.py
                → company interceptée (MÊME porte P2) + competitor_engagement
P5 scoring      score.py (déterministe : fit + faisceau ×0.5 collègues +
                décote fraîcheur) → priority_score/tier + why_now(_evidence),
                puis une passe --ai (haiku) polit les why_now des tiers chauds
P6 outreach     file de la semaine (outreach), stratégie par contact, GATE
                BUDGET avant d'enrichir email/tél (fullenrich), drafts
                (emails 1/2/3 + icebreaker), AUDIT bloquant (<70 = jamais
                approved), approbation HUMAINE (conversation ou bouton front)
P7 envoi        emelia.py create-campaign + push (seed guard) + start + stats
                → status sent→replied, opened_count, liste « à appeler »
```

Chaque batch passe par **la porte de fer** : `preview 10 → UN GO explicite
→ commit`. Les statuts (`pending|running|done|not_found|failed`) sont le
checkpoint : re-lancer reprend, ne repaie pas.

## Structure

```
.claude-plugin/plugin.json  manifeste du plugin (nom, version, MCP)
.mcp.json                   serveurs MCP embarqués (fullenrich)
hooks/hooks.json            hook SessionStart → session_start.py
../../CLAUDE.md             LE CONTRAT (racine du repo) : 5 tables, qui écrit quoi
CONVENTIONS.md              le contrat runtime des skills (§1–§8)
DEMO.md                     le script de test complet P0→P7 (prompts à coller)
tools/core/
  db.py                     la SEULE porte vers SQLite — tables/colonnes
                            dynamiques, claim atomique, import-csv, receipts
  runner.py                 LA boucle batch — preview → GO → commit, statuts,
                            rollback --manifest
  score.py                  scoring P5 déterministe (fit+heat+persona,
                            faisceau collègues, why_now_evidence, file week)
  agent.py / agent_api.py   un prompt → une réponse (SDK abonnement, ou API
                            Anthropic via BRICKS_AGENT_TRANSPORT=api)
  workspace.py              cycle de vie workspace (bricks/ + context/)
  envfile.py                clés ~/.bricks/env + registre du panneau ⚙
  session_start.py          contexte de session (workspace courant, banner)
tools/providers/
  fullenrich.py             recherche personnes (cascade de vagues, child rows)
  sillage.py                surveillance P3/P4 : setup, watchlists, agents,
                            run (reprise), pull (curseur), leads, add-signal
  emelia.py                 envoi P7 : campagne, push (seed guard), start,
                            stats (retours → outreach), export-csv fallback
tools/steps/
  intercept.py              interception P4 : acteur competitor* → company
                            interceptée + competitor_engagement (runner step)
seed/
  import_p1.py + README     sourcing P1 : CSV FullEnrich → companies
front/
  server.py + index.html    UI locale : tables, file de la semaine, la FICHE
                            (WHY NOW + graphe FK + Approve) — voir front/README
skills/
  onboard / surveil / prioritize / outreach    les 4 skills maigres PILOTÉES
  tools-guide                référence outil par outil (CLI + fonctions)
  interface / workspace / gtm-onboard / …      héritage v2 (matière première)
templates/context/          gabarits offer/icp/personas copiés à la création
```

## Les 5 tables (le contrat gelé)

`competitors` · `companies` · `contacts` · `signals` · `outreach` — la
« To contact this week » du produit, C'EST `outreach` (`dedup_key =
<semaine>:<contact_id>`, `email_1/2/3`, `icebreaker_call`, `status
draft→approved→sent→replied`). Colonnes autorisées, formats et **qui écrit
quoi** : voir le CONTRAT dans [CLAUDE.md](../../CLAUDE.md) — liste fermée,
seul Robin l'édite. Le graphe du front = les FK (`contacts.company_id`,
`signals.company_id|contact_id|competitor_id`), rien d'autre.

## Les règles qui ne se négocient pas

1. La logique vit dans les **tools**, jamais dans les skills.
2. **db.py est la seule porte** vers la base (écritures en vagues).
3. **Preview → GO → commit** sur tout batch ; statuts = checkpoint.
4. **Un chemin par capacité** (sourcing = CSV → import-csv ; enrichissement
   = pass-through OU runner ; jamais de boucle par ligne en session).
5. **Receipts, jamais de dump** — max 3 lignes d'échantillon en chat.

Détail : [CONVENTIONS.md](CONVENTIONS.md).

## Les clés (`~/.bricks/env`, chmod 600 — ou le panneau ⚙ de l'interface)

| Clé | Sert à | Où l'obtenir |
|---|---|---|
| `ANTHROPIC_API_KEY` | les passes `--ai` du runner (workers haiku) | console.anthropic.com |
| `BRICKS_AGENT_TRANSPORT=api` | forcer la voie API (règle hackathon) | — |
| `FULLENRICH_API_KEY` | recherche/enrichissement contacts | app.fullenrich.com → Settings → API |
| `SILLAGE_API_KEY` | surveillance & signaux (`sk_live_…`) | équipe Sillage (sponsor) |
| `EMELIA_API_KEY` | envoi des séquences | app.emelia.io → Settings → API |
| `EMELIA_SEED_INBOXES` | **garde-fou** : seules boîtes autorisées à recevoir pendant l'événement (emails ou `@domaine`, virgules) | toi |
| `EMELIA_TEMPLATE_ID` | (optionnel) campagne modèle à dupliquer | UI Emelia |

## Démarrage rapide

```bash
python3 tools/core/workspace.py status        # état (ne crée rien)
python3 tools/core/workspace.py new <projet>  # workspace + context/
python3 front/server.py --port 4321           # l'UI → http://127.0.0.1:4321
python3 tools/providers/sillage.py test-auth  # smoke Sillage
python3 tools/providers/emelia.py  test-auth  # smoke Emelia
```

Puis déroule **[DEMO.md](DEMO.md)** : le fil de test complet P0→P7 avec un
prompt à coller par phase (exemple : agence de référencement IA), les
receipts attendus, les GO, et la séquence jury de 90 secondes
(`add-signal` → re-score → fiche → Approve → push seed).

## L'interface

Tables triables/filtrables, onglet **📞 To contact this week** (jointure
outreach⋈contacts⋈companies), et **la fiche** — le même écran à deux
entrées (clic company ou contact) : bandeau WHY NOW + faisceau de preuves
daté, graphe SVG des FK (concurrents en pointillés, signaux frais en
orange), signaux, décideurs/collègues, coordonnées, drafts dépliables et
bouton **Approve** (seule écriture du front ; refuse si `audit_score < 70`).
Endpoints et détails : [front/README.md](front/README.md).

## Équipe & propriété des chemins

Thomas : `front/**` + `tools/steps/intercept.py` · Robin : `skills/**` +
`tools/core/score.py` + `tools/providers/emelia.py` + `CLAUDE.md` · Rémi :
`tools/providers/sillage.py` + `fullenrich.py` + `seed/`. Besoin d'une
fonction chez l'autre → on la demande, on ne l'écrit pas.

## Héritage Bricks-v2 (le périmètre gardé / jeté)

**Gardé** : le core complet (`db.py`, `runner.py`, `agent*.py`,
`workspace.py`, `envfile.py`), `fullenrich.py`, le packaging plugin, le
front table, et 9 skills-matière première (`gtm-onboard`, `context-write`,
`enrich`, `rank-accounts`, `plan-outreach`, `write-outreach`,
`playbook-outbound`, `workspace`, `tools-guide`) — leurs références
périmées sont assumées, on ne les « répare » pas au fil de l'eau.

**Jeté** : `jobs.py`, `news.py`, `firmo.py` (remplacés par
Sillage/FullEnrich), toute la voie Bright Data (non-sponsor — ne pas
utiliser `agent.py --web` au hackathon), et 15 skills scraping/hors scope.

**Construit depuis (la v3, livrée)** : le contrat 5 tables, `sillage.py`,
`emelia.py`, `score.py`, `intercept.py`, `seed/`, les 4 skills maigres
(`onboard`, `surveil`, `prioritize`, `outreach`), la liste d'exclusion
Sillage à la qualif, le panneau ⚙ complet, l'onglet semaine et la fiche
graphe du front. Reste ouvert : boutons « Enrichir / Envoyer » dans l'UI
(déclencher les tools depuis le serveur — décision d'équipe).
