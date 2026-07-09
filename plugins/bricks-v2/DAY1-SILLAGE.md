# DAY-1 — Brancher Sillage & FullEnrich (rituel du 9 juillet, ~45 min tout compris)

> Contexte : hackathon Agentic GTM (Station F, 09/07/2026) — partenaires
> Anthropic + Sillage + FullEnrich. Tout ce qui suit est PRÉ-CONSTRUIT et
> testé en mock ; il ne reste que les accès.
> Docs vérifiées le 08/07 : getsillage.com/docs (+ llms.txt) · docs.fullenrich.com.

## A. FullEnrich (10 min — l'adapter est final à 95 %)

1. Clé : app.fullenrich.com/app/api → `~/.bricks/env` :
   `FULLENRICH_API_KEY=...` (chmod 600).
2. `python3 tools/fullenrich_adapter.py verify` → clé valide + solde de crédits.
3. **Smoke à 0 crédit** : `python3 tools/fullenrich_adapter.py smoke` →
   `poll --id <enrichment_id>` après ≥1 min. Le contact de test (Grégoire
   Démogé) est officiel et gratuit — l'E2E est validé sans dépenser.
4. Noter dans `memory/state.json` : solde, plan, rate limit constaté.
   Rappels durs : 60 appels/min · 100 contacts/bulk · email=1 crédit,
   mobile=10 (jamais par défaut) · re-enrich <3 mois gratuit → TOUJOURS
   re-poll, jamais re-submit.

## B. Sillage (20 min — suivre `skills/sillage-connect`)

1. **MCP (recommandé)** :
   `claude mcp add --transport http sillage https://api.getsillage.com/api/mcp/v2`
   → OAuth navigateur (compte du workspace hackathon). Redémarrer la session.
   (Alternative REST : clé `sk_live_` — Settings → API Keys ; la génération
   peut nécessiter le support → demander aux organisateurs.)
2. **Quotas d'abord** : `sillage_v2_get_rate_limit` + ressource
   `sillage://setup-state`. ⚠️ Trial = **cap à VIE de top accounts** → fixer
   le contingent (proposition : 60 comptes = les 50 meilleurs scores + 10 de
   la file de repêchage) AVANT tout push. Un push trop gros est REJETÉ en
   entier (`top-account-quota-exceeded`).
3. **Découverte** : lister les outils `sillage_v2_*` → sauvegarder en JSON →
   `python3 tools/sillage_adapter.py discover --tools-json tools.json`.
   Télécharger l'OpenAPI : `curl https://api.getsillage.com/api/v1/docs/spec`
   → geler les endpoints `to_confirm` de `schema/sillage.endpoints.json` +
   les payloads `data` réels des 8 types de signaux (seul keywordDetection
   est exemplifié dans la doc).
4. **Re-mapping** : `@v2-broker` avec le catalogue découvert (proxies
   presumed → confirmed/absent).
5. **Golden queries** : pousser 20 comptes du field-test (domaines vérifiés à
   la main), `upsert_persona` (thèse MemoVAL), créer les 3 agents compilés
   (`python3 tools/sillage_adapter.py compile --tree fixtures/memoval-signals.json`),
   lancer UN signal run, poller, `query_signals` → vérifier la jointure par
   domaine. Recouvrement bas = mapping d'identité à corriger, PAS la thèse.
6. Receipt → `memory/state.json` + NOTES.md : quotas réels, latence d'un run,
   types de signaux actifs, contingent consommé.

## C. Le chaînon domaines (15 min, PRÉALABLE au push réel)

Sillage et FullEnrich ignorent le SIREN — il faut `companies.domain`.
Sur les ~60 comptes du contingent : engine V1
(`runner.py --tools web`, prompt « trouve le site officiel de {{name}}
({{ville}}, {{naf}}) — réponds {domain, confidence, evidence_url} »),
preview 10 → GO → masse. Coût ≈ 1 crédit Bright Data/ligne OU worker
abonnement. Écrire domain + domain_confidence ; les low-confidence ne sont
PAS poussés chez Sillage (gaspillage de quota).

## D. Première boucle complète réelle (le soir même)

`campaign-v2` phase 3 sur la thèse MemoVAL : push du contingent → agents →
run → `signals_to_evidence` → `score_v2.py run` (des entreprises doivent
bouger de bande) → `voi` → 10-20 checks VERIFIER → re-score.
Ensuite CONNECTOR sur les IN (vague de 20, work_emails seulement) →
COMPOSER → drafts. **Rien ne part** : la présentation montre la chaîne
complète avec de vraies données, envois désactivés.

## Si l'accès est MCP-SEULEMENT (probable au hackathon)

Les scripts REST lèveront `NotConfigured` — c'est prévu. Le chemin MCP-only :
la SESSION exécute les écritures via les outils `sillage_v2_*`
(add_top_accounts, upsert_persona, create_agent, launch_signal_run,
list_signals), et les scripts ne servent qu'aux deux bouts FICHIERS :
`sillage_adapter.py compile --tree` (arbre → specs d'agents à recopier dans
les appels MCP) et `signals_to_evidence` (export JSON des signaux MCP →
évidence score_v2). La masse des signaux s'exporte en JSON dans `staging/`,
jamais recopiée dans la conversation (data-plane V1 §10).

## ⚖️ Gel légal (avant d'activer quoi que ce soit sur des personnes)

`S-EVT-13` (keyword-tracking des posts d'un dirigeant nommé) et
`P-HOR-02.b` (job_update d'une personne) portent **`legal_hold: true`** :
NE PAS activer ces agents au hackathon sans validation juriste (base légale
intérêt légitime documentée + DPIA légère — donnée publique ≠ traitement
licite ; angle discrimination par l'âge à traiter). Les agents
`job_posting_keyword_detection` (offres d'emploi de l'ENTREPRISE) ne posent
pas ce problème — commencer par eux.

## Pièges connus (à ne pas redécouvrir)

- `sillage.ai` = AUTRE société (conseil alsacien). Le bon domaine : getsillage.com.
- Pagination signals = CURSEUR (pas offset) ; persister le curseur dans state.json.
- `signal_type` en camelCase dans les payloads (keywordDetection) vs snake_case
  dans la doc des agents — `signals_to_evidence` gère la conversion.
- Pas de webhooks Sillage → poller ; FullEnrich : poll ≥5 min ou webhook HMAC-SHA1.
- Erreur 402 = crédits insuffisants ; 429 → respecter Retry-After.
- MCP scoped à UN workspace — vérifier qu'on est sur le bon avant tout write.
