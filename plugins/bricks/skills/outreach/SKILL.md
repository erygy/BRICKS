---
name: outreach
description: P6/P7 — the week's queue to the send. Strategy per contact, the CREDIT BUDGET gate before enriching coordinates (fullenrich enrich-contact), drafting emails 1/2/3 + icebreaker call (runner --ai on brief_json), the BLOCKING audit (real personalization, sourced claims, one CTA), human approval, send via emelia.py, reply loop. Use when the user says "la file de la semaine", "prépare l'outreach", "rédige les séquences", "enrichis les coordonnées", "envoie", "les retours campagne".
---

# Outreach (P6/P7)

**Before anything, read `CONVENTIONS.md`**, then the CONTRAT in
`CLAUDE.md` (table `outreach` — who writes what). Fusion of
`/plan-outreach` + `/write-outreach`, plus the money gate, the audit and
the send. Drafts never leave the machine without a human GO; approval is
a human act, this skill NEVER sets `approved` itself.

Gates: `/prioritize` ran (priority columns present — else run it first);
`context/offer.md` filled (TODO → `/onboard`, refuse to write generic
spam); **sender voice**: tu/vous, tone, forbidden words, SIGNATURE — the
signature is never inferred; missing → fold 3 sane defaults + the name
question into the first GO, persist `context/voice.md`, and if the
answer skips the name, re-ask THAT field alone.

## 1 — The week's queue

Take `/prioritize`'s queue proposal (or rebuild: `select contacts` tier
`now|week`, `--order "CAST(priority_score AS INTEGER) DESC"`). Present
≤ 12 lines: name, company, score/tier, why_now, phone/email known. The
user trims → ONE idempotent write:

```bash
python3 "tools/core/db.py" add outreach --rows - --key dedup_key < queue.json
```

Then build each row's **brief_json** (the drafting material — nothing
outside it may appear in a draft): why_now + faisceau (from
`why_now_evidence`), persona angle (`context/personas/`), company
name/pitch, contact name/position, and for intercepted accounts the
`competitors.why_we_win` (join via the faisceau's
`competitor_engagement` signal → `competitor_id`). Plus **strategy**:
`email_call` when the faisceau holds a fresh `champion_move` or
`competitor_engagement` AND a phone is realistic, `call_only` for
burning Tier-now with phone, else `email_only` (provisional before
enrichment — upgraded after, same writer). Week-scale only (10-20
rows): assembled from selects, written in ONE `modify --updates` wave
(§4).

## 2 — The credit budget gate (THE money moment, §7)

Count queued contacts with no verified email/phone; check the balance
(`get_credits`). Announce BEFORE anything: « N contacts sans
coordonnées × ~2 crédits = ~X sur solde Y — j'enrichis lesquels ? »
**ONE answer decides.** Then arm ONLY the approved (per contract):

```bash
python3 "tools/core/db.py" modify contacts --set email_status=pending \
  --where "_id IN (<approved ids>)"        # same for phone_status
python3 "tools/providers/fullenrich.py" enrich-contact   # async: job id → memory/state.json, results per wave via modify
```

`not_found` is a result (write the status, leave the value empty);
NEVER fabricate a coordinate. Brick absent → STOP: « enrich-contact
(D2, Rémi) pas livré ». Re-check strategy after: phone arrived on a hot
row → upgrade to `email_call`, say it.

## 3 — Drafting (engine, volume — iron gate)

One runner pass writes the 4 drafts per row from `{{brief_json}}`:

```bash
python3 "tools/core/runner.py" run --table outreach \
  --status-col draft_status --run-id draft-<week> \
  --ai '{"prompt":"<CPPC doctrine + voice.md summary>. Matériau (SEULE source autorisée): {{brief_json}}. Écris email_1, email_2 (relance J+3, angle différent), email_3 (breakup J+7), icebreaker_call (2 phrases d ouverture d appel).","schema":{"type":"object","properties":{"email_1":{"type":"string"},"email_2":{"type":"string"},"email_3":{"type":"string"},"icebreaker_call":{"type":"string"}},"required":["email_1","email_2","email_3","icebreaker_call"]},"model":"haiku"}' \
  --preview 10
# stream the previews, ONE GO → --commit
```

The copy doctrine (in the prompt, enforced by the audit): **CPPC** —
Contexte (the why_now, one line) → Problème (posed as the segment's
topic, never asserted) → Proposition (ONE outcome from the offer) →
Call-to-conversation (ONE question). **< 100 mots**, subjects plain
(« prise de contact », never slogans), personalization = ONE real
signal from the faisceau connected to the problem — never decorative
trivia. Intercepted contacts: lean on `why_we_win` as OUR angle, never
name or trash the competitor. Forbidden: talking about ourselves,
stacked CTAs, placeholders, any fact outside brief_json/offer.

## 4 — The blocking audit (independent pass, never self-graded)

Arm `audit_status='pending'` on `draft_status='done'` rows → second
runner `--ai` pass (haiku; « audit en sonnet » if the user says so):
judge the 4 drafts against `{{brief_json}}` on: personnalisation RÉELLE
(cites a faisceau fact, with its date), claims SOURCÉS (offer or brief,
nothing else), UN seul CTA per message, longueur. Schema:
`{"audit_score":integer 0-100, "audit_notes":string}`.

**`audit_score < 70` = the row can NEVER pass `approved`.** Failed rows:
tighten the brief or the prompt, re-arm `draft_status='pending'` on
those `_id`s, ONE re-pass; still failing → hand to human edit, say so.
Receipt: score distribution + the worst 3 notes.

## 5 — Approval, then the send (P7)

Approval: the human, via conversation GO (list the rows) or the front's
Approve button — both set `status='approved'`, nothing else does.

**Hackathon hard rule: recipients are OUR seeded inboxes only — never a
real prospect during the event.** `emelia.py push` ENFORCES it
(EMELIA_SEED_INBOXES allowlist, default-deny; blocked recipients listed
in the receipt). State it in the send GO anyway. Then:

```bash
python3 "tools/providers/emelia.py" test-auth               # morning smoke
python3 "tools/providers/emelia.py" create-campaign --week <week>
#   duplicates EMELIA_TEMPLATE_ID (the UI-built template whose steps are
#   {{email_1}}/{{email_2}}/{{email_3}} — built ONCE, day-J morning)
python3 "tools/providers/emelia.py" push  --campaign <id> --week <week>
python3 "tools/providers/emelia.py" start --campaign <id>
```

ONE explicit send GO (campaign name + recipient count). Auth friction or
any API surprise (assumed risk): `emelia.py export-csv --week <week>` —
the « prêt à importer » CSV in `staging/`, shown on screen; the demo
still closes.

## 6 — The reply loop (what makes it production-ready)

`python3 "tools/providers/emelia.py" stats --week <week>` (poll;
re-runnable, idempotent) → `opened_count`, `replied`,
`status='replied'` via ONE modify wave, plus the ready-made `aAppeler`
list in its receipt: **replied → stop the sequence, Tier-A call** ;
**2 opens, no reply → switch to the call file** (the icebreaker_call is
ready). Relay that list verbatim, then re-run `/prioritize` — the loop
is closed.

## Close the run

`memory/state.json` (campaign id, week, budget spent vs GO) + one
`NOTES.md` line (§8). Receipt: queue → enriched → drafted → audited
(pass/fail) → approved → sent, credits spent vs announced. Statements,
never questions.
