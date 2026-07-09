# BRICKS-FINAL — règles du repo

Base curée de Bricks-v2 (voir README.md pour le pipeline, le périmètre
gardé/jeté et l'état de la v3), distribuée comme **plugin Claude Code** — l'architecture
d'origine est conservée : manifeste `.claude-plugin/plugin.json`, hook
SessionStart (`hooks/hooks.json` → `tools/core/session_start.py`), MCP servers
dans `.mcp.json`, skills namespacées `/bricks:*`, chemins via
`${CLAUDE_PLUGIN_ROOT}`, workspaces `bricks/` par répertoire de travail.

## Les règles qui survivent

1. **La logique vit dans les tools, jamais dans les skills.** Un besoin
   nouveau = un provider ou un skill qui orchestre — jamais du code enfoui
   dans un SKILL.md, jamais de SQL écrit à la main dans la conversation.

2. **`db.py` est la seule porte vers la base.** Tables/colonnes dynamiques,
   `_id` réservé, colonne `X_status` appariée à toute colonne enrichie
   (`pending|running|done|not_found|failed`). Écritures en vagues
   (`modify --updates '[...]'`), jamais un appel par ligne.

3. **La porte de fer : preview → GO → commit.** Tout batch passe par
   `runner.py run … --preview 10`, UN GO explicite, puis `--commit`.
   Les statuts sont le checkpoint ; re-lancer reprend, ne repaie pas.

4. **Un chemin par capacité.** Sourcing = CSV sur disque →
   `db.py import-csv --key`. Enrichissement = pass-through (`import-csv`/
   `modify`) OU pipeline `runner.py` — jamais de boucle par ligne en session.

5. **La conversation décide ; les fichiers portent.** Jamais de masse de
   lignes dans le contexte — receipts, max 3 lignes d'échantillon.

Contrat runtime détaillé : `CONVENTIONS.md`. Référence outil par outil
(deux modes d'appel, CLI et fonctions) : `skills/tools-guide/SKILL.md`.

## Spécifique à cette base

- **Transport IA au hackathon : la voie API** (`BRICKS_AGENT_TRANSPORT=api` +
  `ANTHROPIC_API_KEY` dans `~/.bricks/env`). Ne pas utiliser `agent.py --web`
  (Bright Data, non-sponsor).
- **Données externes : sponsors d'abord.** Découverte et coordonnées =
  FullEnrich ; décideurs et signaux = Sillage (provider à écrire, pattern
  `fullenrich.py` : CLI JSON stdout + fonction `step(row, ctx, args)`).
- Les 4 skills maigres sont écrites : `skills/onboard`, `skills/surveil`,
  `skills/prioritize`, `skills/outreach` — ce sont ELLES qu'on pilote. Les
  9 skills héritées de Bricks-v2 restent en matière première (références
  périmées assumées, ne pas « réparer » au fil de l'eau).

## LE CONTRAT — les 5 tables (GELÉ)

L'interface entre les trois sessions : on ne se parle qu'à travers ces
tables. Besoin d'un champ nouveau → huddle 2 min à trois, **seul Robin
édite ce fichier**. `db.py` crée tables et colonnes à la volée : ce schéma
n'est pas une migration, c'est la LISTE FERMÉE des colonnes autorisées et
de qui les écrit.

Propriété des chemins — Thomas : `front/**` + `tools/steps/intercept.py` ·
Robin : `skills/**` + `tools/core/score.py` + `tools/providers/emelia.py` +
`CLAUDE.md` · Dev 3 : `tools/providers/sillage.py` + `fullenrich.py` +
`seed/`. Besoin d'une fonction chez l'autre → on la demande, on ne
l'écrit pas.

### Conventions transverses

- Tout est TEXT en base (db.py) : booléens `'1'|'0'`, dates `YYYY-MM-DD`,
  horodatages ISO 8601 UTC, colonnes `*_json` = JSON sérialisé. Numériques
  stockés en texte → toujours `CAST(col AS INTEGER)` dans un `--order` ou
  une comparaison.
- `_id` INTEGER auto — jamais fourni. Les FK (`company_id`, `contact_id`,
  `competitor_id`) stockent le `_id` de la ligne visée.
- `domain` normalisé : minuscules, sans protocole ni `www.` ;
  `linkedin_url` normalisée : `https://www.linkedin.com/in/<slug>` (ou
  `/company/<slug>`), sans slash final. La clé d'import est OBLIGATOIRE :
  acteur sans domaine résolu = pas de ligne company (le signal reste sans
  `company_id`, jamais de company fantôme).
- Toute colonne `X_status` = vocabulaire moteur
  `pending|running|done|not_found|failed` (§4 CONVENTIONS.md), jamais un
  autre.
- Le moteur pose seul ses colonnes techniques (`<base>_run`,
  `source_run`) — on ne les crée ni ne les écrit à la main.

### competitors — clé d'import `domain`

| colonne | valeurs / format | écrite par |
|---|---|---|
| name, domain, linkedin_url | identité, résolue via FullEnrich | onboard (P0) |
| why_we_win | 2-3 phrases : notre angle contre CE concurrent | onboard → brain (P0) |
| interest_score | 0-100, priorité de surveillance | onboard (P0) |
| watched | `'1'` = sur la watchlist Sillage (top 5-10) | sillage.py watchlist (P3) |
| sillage_entity_id | id d'entité watchlist Sillage | sillage.py (P3) |

### companies — clé d'import `domain`

| colonne | valeurs / format | écrite par |
|---|---|---|
| name, domain, linkedin_url | identité | l'inserteur : import P1 (Dev 3) ou intercept.py (Thomas) |
| source | `fullenrich_search` \| `competitor_interception` | l'inserteur |
| headcount, industry, geo, firmo_json | firmo STATIQUE seulement — tout le dynamique est à Sillage | l'inserteur (CSV FullEnrich en P1, resolve-actor en P4) |
| qualify_status | moteur ; `'pending'` posé À L'INSERT (= « à qualifier ») | l'inserteur arme ; runner règle |
| icp_verdict | `qualified` \| `rejected` \| NULL (pas encore jugé) | runner `--ai` qualif (P2) |
| icp_reason | 1 phrase | runner `--ai` qualif (P2) |
| fit_score | 0-100, fit ICP statique | runner `--ai` qualif (P2) |
| sillage_company_id | id compte Sillage | sillage.py setup (P3) |
| tracked | `'1'` = occupe un des 20 slots | sillage.py setup (P3) |
| priority_score | 0-100 | score.py (P5) |
| priority_tier | `now` \| `week` \| `nurture` | score.py (P5) |
| why_now | 1 phrase — draft déterministe posé par score.py, poli par la passe `--ai` sur les tiers chauds | score.py puis prioritize → agent_api (P5) |
| why_now_evidence | JSON `[{"_id","type","date","summary"}]` — les 2-3 preuves les plus chaudes | score.py (P5) |
| why_now_status | moteur ; `'pending'` posé par prioritize sur les tiers `now`\|`week` | prioritize arme ; runner `--ai` règle |
| scored_at | date ISO du dernier scoring | score.py (P5) |

Seules les lignes `icp_verdict='qualified'` concourent aux 20 slots et au
scoring. Les rejetées restent en base (audit), jamais supprimées le jour J.

### contacts — clé d'import `linkedin_url`

| colonne | valeurs / format | écrite par |
|---|---|---|
| company_id | FK companies, OBLIGATOIRE | l'inserteur : sillage.py leads (P3) |
| sillage_lead_id | id lead Sillage | sillage.py (P3) |
| full_name, position, seniority, linkedin_url | identité | l'inserteur |
| is_champion | `'1'` = ex-contact closed-lost (watchlist champion) | surveil, import CRM (P3) |
| email, phone | coordonnées vérifiées | fullenrich.py enrich-contact (P6) |
| email_status, phone_status | moteur ; `'pending'` posé par le skill outreach sur les SEULS approuvés (gate budget) | outreach arme ; fullenrich.py règle |
| priority_score, priority_tier, why_now, why_now_evidence, why_now_status, scored_at | mêmes formats et écrivains que companies | score.py / prioritize (P5) |

### signals — clé d'import `sillage_signal_id`

| colonne | valeurs / format | écrite par |
|---|---|---|
| sillage_signal_id | id Sillage, unique — la dédup des pulls | sillage.py pull (P4) |
| company_id | FK ; NULL tant que l'acteur externe n'est pas résolu | sillage.py ; intercept.py pour les externes |
| contact_id | FK ; NULL si l'acteur n'est pas un lead connu | sillage.py |
| competitor_id | FK ; posé sur les signaux de la watchlist concurrent | sillage.py |
| type | CANONIQUE, lu par le scoring : `newJob` \| `recentlyPromoted` \| `jobPosting` \| `keywordDetection` \| `champion_move` \| `competitor_engagement` | sillage.py (mapping au pull) ; intercept.py pose `competitor_engagement` après résolution + qualif |
| sillage_type | type brut Sillage, jamais réécrit | sillage.py |
| signal_date, detected_at | date de l'événement / date du pull | sillage.py |
| actor_name, actor_headline, actor_linkedin | l'acteur du signal | sillage.py |
| actor_side | `lead` \| `watchlist` \| `external` | sillage.py |
| post_text, comment_text, source_url | texte complet (get_contents) + preuve | sillage.py |
| summary | 1 phrase lisible, générée à l'ingestion | sillage.py ; réécrite par intercept.py sur les interceptés |
| payload_json | réponse brute | sillage.py |
| intercept_status | moteur ; `'pending'` posé par le pull sur les SEULS types `competitor*` | sillage.py arme ; runner + intercept.py règle |

### outreach — clé d'import `dedup_key` = `<week>:<contact_id>` (ex. `2026-W28:42`)

| colonne | valeurs / format | écrite par |
|---|---|---|
| dedup_key, contact_id, week | week ISO `2026-Wnn` | skill outreach (P6, création de la file) |
| strategy | `email_only` \| `email_call` \| `call_only` | skill outreach, validée en conversation |
| brief_json | le matériau de rédaction (why_now, faisceau, persona, why_we_win…) — SEULE source autorisée des drafts | skill outreach (P6) |
| draft_status | moteur ; `'pending'` posé à la création de la file | outreach arme ; runner `--ai` rédaction règle |
| email_1, email_2, email_3, icebreaker_call | les drafts, générés depuis `{{brief_json}}` | runner `--ai` rédaction (P6, drive : skill outreach) |
| audit_status | moteur ; `'pending'` posé sur les rows `draft_status='done'` | outreach arme ; runner `--ai` audit règle |
| audit_score, audit_notes | 0-100 ; **< 70 = ne peut pas passer `approved`** | runner `--ai` audit (P6, passe indépendante) |
| status | `draft` → `approved` (HUMAIN : GO conversation ou POST du front) → `sent` → `replied` | création : outreach · approved : humain · sent/replied : emelia.py |
| emelia_campaign_id, sent_at, opened_count, replied | retours de campagne | emelia.py (P7) |

### Qui arme quel pipeline (le résumé anti-collision)

- Inserteur de `companies` (import P1 **et** intercept.py) → pose
  `qualify_status='pending'`. Même porte P2 pour tout le monde.
- `sillage.py pull` → pose `intercept_status='pending'` sur les
  `competitor*` uniquement.
- Skill outreach, APRÈS le GO budget → pose `email_status`/`phone_status`
  `='pending'` sur les seuls contacts approuvés.
- Skill prioritize, APRÈS le commit des scores → pose
  `why_now_status='pending'` sur les tiers `now`|`week` (companies et
  contacts), puis UNE passe `runner --ai` (haiku) polit le `why_now` depuis
  `{{why_now_evidence}}`.
- Skill outreach → pose `draft_status='pending'` à la création de la file,
  puis `audit_status='pending'` sur les rows rédigées — deux passes
  `runner --ai` distinctes (rédaction, puis audit indépendant).
- Curseur de pull Sillage + job ids async FullEnrich → `memory/state.json`
  (§8 CONVENTIONS.md), jamais en table.
- Persona Sillage = PAR WORKSPACE : l'union des titres cibles de
  `context/icp.md`, pas un persona par compte.

### Le graphe = les FK, rien d'autre

`contacts.company_id` → arête « emploie » · `signals.company_id|contact_id`
→ « a émis » · `signals.competitor_id` → « a engagé avec ». Le front lit
tout via db.py (mode fonction), n'écrit QUE `outreach.status`
`draft→approved` (bouton Approve) et déclenche les tools pour
Enrichir / Envoyer.

### Écarts assumés vs la spec d'origine (ne pas « recorriger »)

1. `icp_status (to_qualify|qualified|rejected)` est devenu
   `qualify_status` (vocabulaire moteur, `pending` = à qualifier) +
   `icp_verdict`/`icp_reason`/`fit_score` — le claim de runner.py exige le
   vocabulaire §4.
2. `score`/`tier` sont `priority_score`/`priority_tier` — les noms du
   kernel rank.py que score.py étend ; `tier` seul collisionnait avec le
   tier de fit ICP.
3. Clé outreach mono-colonne `dedup_key` — `add --key` ne fait pas de clé
   composite. Et `--key` DÉDOUBLONNE (skip), il ne met jamais à jour :
   toute update passe par `modify --updates` avec `_id`.
4. `signals.type` canonique séparé de `sillage_type` brut ; ajout de
   `competitor_id` (l'arête « a engagé avec » + le `why_we_win` des
   drafts) et de `intercept_status` (la branche interception tourne dans
   runner.py, pas en boucle de session).
5. Les retours de campagne (`sent_at`, `opened_count`, `replied`,
   `status sent→replied`) vivent sur `outreach` (FK `contact_id`),
   jamais sur `contacts` — la roadmap disait « dans la table contact » :
   même information, une seule écriture, le front joint via `contact_id`.
