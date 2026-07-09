---
name: prioritize
description: P5 — fuse ICP fit + the signal faisceau into priority_score/tier + why_now, per company AND per contact. Drives tools/core/score.py (deterministic, free), then ONE runner --ai pass to polish the why_now sentences. Use when the user says "priorise", "qui appeler en premier", "classe mes comptes", "les faisceaux", "score les contacts", "re-score", "why now".
---

# Prioritize (P5)

**Before anything, read `CONVENTIONS.md`**, then the CONTRAT in
`CLAUDE.md`. Successor of `/rank-accounts`, generalized to contacts: the
maths live in `tools/core/score.py` (read its docstring — formula,
weights, spec holes), one deterministic pass, zero model, zero credit,
auditable by a jury. The model writes NO scoring code; at most it edits
one weight in a spec JSON (« mets champion à 40 », « seuil now à 70 » →
write the override file, pass `--spec`).

Gates: workspace (§2); qualified companies exist (else → `/surveil`
qualification). Zero `signals` rows → fit-only scores, empty why_now —
the honest no-signal result, SAY SO, not an error.

## Run (deterministic + free → announce in one line and run, §5 N/A)

```bash
RUN="bricks/tmp/score-<date>"; mkdir -p "$RUN"
python3 "tools/core/db.py" select companies --limit 100000 > "$RUN/companies.json"
python3 "tools/core/db.py" select contacts  --limit 100000 > "$RUN/contacts.json"
python3 "tools/core/db.py" select signals   --limit 100000 > "$RUN/signals.json"
python3 "tools/core/score.py" run \
  --companies "$RUN/companies.json" --contacts "$RUN/contacts.json" \
  --signals "$RUN/signals.json" \
  --out-companies "$RUN/up_companies.json" \
  --out-contacts "$RUN/up_contacts.json" \
  --queue 10 --out-queue "$RUN/queue.json"
python3 "tools/core/db.py" modify companies --updates - < "$RUN/up_companies.json"
python3 "tools/core/db.py" modify contacts  --updates - < "$RUN/up_contacts.json"
```

The queue file is a PROPOSAL for `/outreach` — do not add it to
`outreach` here. Relay the receipt's warnings LOUDLY: `unknownTypes` = a
writer bug or interceptions still pending (name the upstream fix);
`unresolved` = external actors awaiting `/surveil` interception.

## Polish the why_now (the only paid step — iron gate applies)

score.py wrote a deterministic DRAFT why_now. Polish the hot tiers with
ONE `--ai` pass per table (haiku, ~cents; skipping it is fine, the draft
stands — say which one the user gets):

```bash
python3 "tools/core/db.py" modify contacts --set why_now_status=pending \
  --where "priority_tier IN ('now','week')"
python3 "tools/core/runner.py" run --table contacts \
  --status-col why_now_status --run-id whynow-contacts-<date> \
  --ai '{"prompt":"Faisceau de signaux du prospect {{full_name}} :\n{{why_now_evidence}}\nÉcris LE why-now : UNE phrase française, factuelle et datée, la raison d'appeler CETTE semaine. Chaque fait vient du faisceau, zéro superlatif.","schema":{"type":"object","properties":{"why_now":{"type":"string"}}},"model":"haiku"}' \
  --preview 10
# preview → ONE GO → --commit ; same pass on companies (why_now_status, {{name}})
```

## Present the faisceaux (the product moment)

From the receipt + a `select` of the top rows (never a dump, §1) — for
the top 3 contacts, one block each:

```
Marie Kowalski (TargetCo) — 64/now
  why_now : Champion en mouvement : … (2026-07-02)
  faisceau : champion_move 02/07 (_id 12) · competitor_engagement 05/07 (_id 15) · newJob 09/06 (_id 3)
```

The convergence IS the pitch — several weak signals beat one strong. The
full list lives in the UI (`front/`, reads the same columns); point the
user there. Tie each claim to its `_id` — the proof survives into the
drafts.

## Re-runnable by design

Priority is a SNAPSHOT: decay moves daily, so re-run after every
`/surveil` pull and after every `add-signal` (THE live demo: inject →
re-run → the contact climbs under the jury's eyes — wall time is
seconds, announce it). Full recompute, no per-row statuses except the
why_now pass (which claims only re-armed rows).

## Close the run

`memory/state.json` (tier counts, scored_at) + one `NOTES.md` line (§8).
Receipt: tier distribution companies/contacts, queue proposal size,
elapsed_s, top 3 blocks. End with a statement: « Next : `/outreach`
prend la file de la semaine (budget crédits à valider). »
