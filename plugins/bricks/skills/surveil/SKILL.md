---
name: surveil
description: P3/P4 — put the qualified world under surveillance and pull the signals. Drives tools/providers/sillage.py (setup slots/watchlists/agents, run, pull with cursor, leads), then the interception pipeline (intercept.py) and the ICP qualification gate (runner --ai) on whatever new companies arrived. Use when the user says "mets sous surveillance", "lance sillage", "pull les signaux", "quoi de neuf", "check les signaux", "setup la watchlist".
---

# Surveil (P3/P4)

**Before anything, read `CONVENTIONS.md`**, then the CONTRAT in
`CLAUDE.md` (tables `companies`, `contacts`, `signals` — who writes
what). This skill DRIVES two bricks it does not own: `sillage.py` (Rémi)
and `tools/steps/intercept.py` (Thomas). A subcommand missing or absent
file → STOP and name the brick and its owner; never reimplement it
in-session, never write SQL around it.

Gates: workspace resolved (§2); `context/icp.md` filled and `competitors`
table present (else → `/onboard`); `companies` carries qualified rows
(else → sourcing P1 + qualification below, nothing to watch yet).

## The sillage.py surface this skill consumes (CLI JSON stdout, §4)

| subcommand | effect on the contract tables |
|---|---|
| `setup` | persona (UNION of icp.md buying-role titles, per workspace) + push top-20 accounts → `companies.sillage_company_id`, `tracked='1'` |
| `watchlist --type competitor\|champion` | create + add entities → `competitors.watched/sillage_entity_id` (companies) or champion profile URLs |
| `agents` | create the 4 agents: `job_update`, `job_posting_keyword`, `keyword_detection` (pain keywords from offer/icp), `competitor` |
| `run [--lookback 90]` | launch signal run + poll until done |
| `pull` | signals since cursor → dedup `sillage_signal_id` → `get_contents` for text → summary → INSERT `signals` ; arms `intercept_status='pending'` on `competitor*` rows ; cursor in `memory/state.json` |
| `leads` | persona mapping → INSERT `contacts` (dedup linkedin_url, company_id set) |
| `add-signal --json '{…}'` | THE demo injection (official) — a signal row as if pulled |

## Setup (once — idempotent, re-run safe)

The 20 slots are the scarce resource; `fit_score` decides who deserves
them. Announce the allocation before pushing:

```bash
python3 "tools/core/db.py" select companies --where "icp_verdict='qualified'" \
  --cols _id,name,domain,fit_score \
  --order "CAST(fit_score AS INTEGER) DESC" --limit 20
python3 "tools/providers/sillage.py" setup            # persona + top-20
python3 "tools/providers/sillage.py" watchlist --type competitor   # top interest_score, sets watched='1'
python3 "tools/providers/sillage.py" watchlist --type champion     # closed-lost profile URLs (CRM export) — none provided → skip and say so
python3 "tools/providers/sillage.py" agents
python3 "tools/providers/sillage.py" run --lookback 90             # first backfill
```

Watchlists live OUTSIDE the 20-slot quota. Everything is async upstream —
run setup as early as possible in the day; every waiting minute is signal
lost.

## Pull (the re-runnable heartbeat)

```bash
python3 "tools/providers/sillage.py" run
python3 "tools/providers/sillage.py" pull
python3 "tools/providers/sillage.py" leads
```

Re-running resumes from the cursor and re-pays nothing (dedup by
`sillage_signal_id`). Receipt: new signals by `type`, new contacts, how
many `competitor*` rows await interception. Max 3 sample summaries (§1).

## Interception (Thomas's step, driven here — the iron gate applies)

Pending `competitor*` rows → the runner claims and processes them:

```bash
python3 "tools/core/runner.py" run --table signals \
  --status-col intercept_status --run-id intercept-<date> \
  --step "tools/steps/intercept.py:step" --preview 10
# check the receipts → ONE explicit GO → same command with --commit
```

Effect (per contract): external actor resolved → new `companies` row
(source=`competitor_interception`, `qualify_status='pending'` — SAME
door as sourced rows), signal row completed (`company_id`,
`type='competitor_engagement'`, readable summary). Unresolvable actor →
signal stays without company_id, never a phantom row.

## Qualification (P2 — the one gate for sourced AND intercepted)

Whenever `qualify_status='pending'` rows exist (first sourcing or fresh
interceptions). STATIC criteria only — headcount, industry, geo,
business model, from `context/icp.md` (kill rules included).

**Liste d'exclusion Sillage** — le dynamique est le travail de Sillage
(getsillage.com/docs/playbooks/signal-reference) : on ne l'enrichit NI
ne le juge à P2, il arrive en lignes `signals` au pull (P4) et est
scoré à P5. Couvert par ses agents :

- `job_update` — prises de poste, promotions (→ `newJob`, `recentlyPromoted`)
- `job_posting_keyword_detection` — offres d'emploi (→ `jobPosting`)
- `keyword_detection` — mots-clés posts & actu (→ `keywordDetection`)
- `competitor` — engagement avec un concurrent surveillé (→ `competitor_engagement`)
- `champion` — mouvements de champion (→ `champion_move`)
- `partner` / `customer` / `influencer` — agents Sillage non souscrits ;
  dynamiques quand même, pas plus l'affaire de P2.

Un verdict P2 qui cite un recrutement, un changement de poste ou un
post est un MAUVAIS verdict — resserre le prompt et re-lance la ligne.
`--ai` writes exactly `icp_verdict`, `icp_reason`, `fit_score`:

```bash
python3 "tools/core/runner.py" run --table companies \
  --status-col qualify_status --run-id qualify-<date> \
  --ai '{"prompt":"ICP: <criteria + kill rules from icp.md>. Entreprise: {{name}} ({{domain}}) — {{headcount}} / {{industry}} / {{geo}}. Juge le fit STATIQUE uniquement : taille, secteur, géo, business model. IGNORE tout signal dynamique — recrutements, prises de poste, promotions, posts, actu, engagement concurrent, mouvement champion : couvert par Sillage, jugé au scoring, pas ici. Tranche: qualified|rejected + raison (1 phrase, critères statiques seulement) + fit_score 0-100.","schema":{"type":"object","properties":{"icp_verdict":{"type":"string","enum":["qualified","rejected"]},"icp_reason":{"type":"string"},"fit_score":{"type":"integer"}}},"model":"haiku"}' \
  --preview 10
# preview receipts → ONE GO → --commit
```

Newly qualified intercepted companies with hot signals may DESERVE a
slot: say it in the receipt (« X qualifiée par interception, fit 85 —
candidate aux 20 slots au prochain setup »), the user arbitrates.

## The demo button (rehearse it)

`add-signal` (a fresh `champion_move` on a tracked account) →
`/prioritize` re-run → the contact climbs to `now` in front of the jury.
Wifi-independent. Rehearse once before 16h.

## Close the run

`memory/state.json` (cursor is written by sillage.py; add run counts) +
one `NOTES.md` line (§8). Receipt ends with a statement: « Next :
`/prioritize` fusionne fit + signaux et sort la file. »
