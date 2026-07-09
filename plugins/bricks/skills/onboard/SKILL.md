---
name: onboard
description: P0 — the front door. Interview offre + ICP falsifiable + personas + CONCURRENTS directs (résolus FullEnrich, why_we_win généré), persisted to context/ and the competitors table. Use at the first GTM interaction — "on lance le projet", "définis mon ICP", "je vends X à Y", "onboarde-moi", or a vague opening. Trigger broadly: better to over-trigger onboarding than to miss it.
---

# Onboard (P0)

**Before anything, read `CONVENTIONS.md` in full**, then the CONTRAT
section of `CLAUDE.md` — the 5 frozen tables this skill feeds. Distilled
from `/gtm-onboard` + `/context-write`: one skill, four phases, and it
now interviews the COMPETITORS too (they are the interception fuel).

Run `python3 "tools/core/workspace.py" status` (§2). No workspace → create
one named after the project. Context already filled → this run UPDATES
(never wipes); a manifestly different project → propose a new workspace,
never decide alone.

## Phase 1 — Discovery (offre + ICP)

**Infer first, question second. One question per turn, maximum.** Present
every inference as *« je suppose X — confirme ou corrige »*, never
*« quel est X ? »*. Never ask what the input or context already answers.

Fill, in this order:

1. **Offre** — what we sell (one sentence), problems solved, proof
   points, tone. Schema: `templates/context/offer.md`.
2. **ICP** — industry/vertical, size, geography, other fit signals,
   KILL RULES (hard disqualifiers, one testable condition per bullet),
   buying roles (decision maker + champion, title patterns
   `|`-separated). Schema: `templates/context/icp.md`.

Stop when every field is filled or explicitly TODO — never invent a
size, a country or a role that was not stated.

## Phase 2 — Challenge falsifiable

Three passes; a vague answer sends you BACK to Phase 1 on that field:

- **Entreprise** — propose 2-3 candidate profiles, push for ONE
  observable signal separating in-target from out (it becomes P2's
  qualification criterion — STATIC only: headcount, industry, geo,
  business model; everything dynamic belongs to Sillage).
- **Persona** — « qui signe vs qui utilise vs qui prescrit ? ». The
  title patterns collected here are also **the Sillage persona**: ONE
  persona per workspace, so write the UNION of every target title —
  `/surveil` pushes it verbatim.
- **Localisation** — « France entière » is almost always too broad;
  push toward a testable segment.

## Phase 3 — Concurrents (the interception fuel)

Ask ONCE: *« tes 3-7 concurrents directs — ceux que tes prospects
comparent vraiment ? »* Then per competitor:

1. **Resolve** via the FullEnrich MCP `search_companies` (name → domain,
   linkedin_url). MCP tools absent → the user is not signed in: STOP,
   tell them to run `/mcp` → `fullenrich` → sign in, then resume. Never
   fabricate a domain. Unresolvable → keep the name, leave domain TODO
   and say so (it cannot be watched without a resolution).
2. **why_we_win** — draft 2-3 sentences from the offer's proof points vs
   what is known of that competitor: *our angle when a prospect engages
   with THEM*. Present all drafts as hypotheses in ONE block; the user
   corrects.
3. **interest_score** 0-100 (surveillance priority — who deserves the
   watchlist). Propose, let the user reorder.

Confirmed → ONE write through the only door (§4), dedup by domain:

```bash
python3 "tools/core/db.py" add competitors --rows '[{"name":"…",
  "domain":"…","linkedin_url":"…","why_we_win":"…","interest_score":"80"}]' \
  --key domain
```

`watched` stays empty here — `/surveil` sets it when the watchlist is
actually pushed. 3-7 rows dictated in-session is the §6 exception, not a
loop.

## Phase 4 — Persist the context

Write (update-not-wipe: read each file first, preserve filled fields,
replace only TODOs the interview answered — schema headings verbatim):

- `context/offer.md`
- `context/icp.md` — kill rules become P2 prompt material; buying roles
  = the persona union `/surveil` reads.
- `context/personas/<slug>.md` per buying role surfaced (headings from
  `templates/context/personas/decision-maker.md`). A committee surfaced
  in conversation must not evaporate into one file.

## Receipt

3-5 lines: ICP fields filled vs TODO, kill rules count, personas
persisted, competitors written (n, top interest first — max 3 samples,
§1). State plainly this is a **v1 falsifiable ICP** — sourcing and
replies are what validate it. End with a statement, never a question:
« Next : Rémi lance le sourcing P1 (fullenrich companies-export), puis
`/surveil` met le monde sous surveillance. »
