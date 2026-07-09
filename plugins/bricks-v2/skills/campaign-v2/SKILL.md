---
name: campaign-v2
description: La chaîne V2 de A à Z — « j'ai une idée de business » → thèses → signaux → univers → scoring → vérification VOI → contacts → séquences. Orchestre les agents V2 par dispatch explicite. À utiliser pour lancer une campagne complète sur un concept.
---

# campaign-v2 — le pipeline complet

Dispatch EXPLICITE (jamais de re-décision par phrase) ; la base est le bus ;
chaque phase émet un receipt et s'arrête aux gates prévus. Deux fan-outs
seulement : les architectes (design) et l'engine (vérifications).

## Phase 0 — Cadrage (gratuit)
1. Workspace V1 (`workspace.py status` / `new`). Gate contexte V1 §3.
2. `@v2-strategist` : concept → `staging/theses.json` (1-3 thèses).
   **GO utilisateur sur les thèses** — c'est le seul moment où l'humain
   choisit QUOI tester. Une thèse = une campagne.

## Phase 1 — L'arbre de signaux (gratuit, fan-out unique)
3. Vague `@v2-signal-architect` ×6-8 (une dimension chacun, en parallèle,
   aveugles entre eux) → fragments `staging/signals-*.json`.
4. Fusion mécanique des fragments (script, pas d'agent) puis `@v2-critic` :
   verdicts kill/demote/merge + levée des legal_flags.
5. `@v2-broker` : mapping proxies ↔ catalogues de capacités, inobservables →
   questions, sondes Day-1. Arbre final versionné : `staging/tree-v<N>.json`.
6. `score_v2.py check` — zéro warning toléré sur la sensibilité.

## Phase 2 — Univers & premier scoring (gratuit)
7. `@v2-prospector` étapes 1-3 : registre → kill rules → résolution de domaines.
8. `score_v2.py run` : contrôle d'IDENTIFIABILITÉ (si « trop lâche/strict » →
   retour CRITIC, on ne dépense RIEN sur un score mort) ; bandes IN/BAND/OUT.

## Phase 3 — Signaux & vérification (payant, gate §8)
9. `@v2-prospector` étapes 4-6 : push Sillage (les mieux scorés d'abord,
   quota !), agents détecteurs, première récolte → `evidence`.
10. `score_v2.py voi --budget <B>` → plan ; **UN GO groupé** (montant + nombre
    de checks) ; `@v2-verifier` exécute par vagues, re-score entre chaque.
    Arrêt : bande vide ou budget épuisé.

## Phase 4 — Contacts & fabrique de messages (payant, gate §8)
11. `@v2-connector` : FullEnrich sur IN uniquement (smoke 0 crédit d'abord).
12. **La fabrique** (`messaging_factory.py`, cf. ARCHITECTURE §6) :
    a. `select-key-signals` + `materialize` → le TABLEAU gagne ses colonnes
       signaux clés (`sig_*`, `signal_cle`, `axe`) — groupable dans l'UI ;
    b. `@v2-axe-mapper` (Opus 4.8) : nomme les AXES, groupe les entreprises,
       écrit les PROMPTS D'AXE (skill prompt-smith-outreach) ;
    c. `resources --band IN` → les RESSOURCES par entreprise ;
    d. `compile-prompt` (BASE = AXE × FORMAT + RESSOURCES) puis
       `@v2-composer` génère sous email-craft → drafts, msg_key, axe+format
       en colonnes.

## Phase 5 — Envoi & verdict de thèse
13. SEND-GUARD : GO campagne (template + 10 exemples réels + volumes) →
    envoi automatisé sous caps, stop-on-reply, opt-out=kill.
14. À J+7/J+14 : taux de réponse PAR BANDE → verdict de thèse
    (success_metric / kill_metric). Tier IN ≤ témoin ⇒ la thèse ou les poids
    mentent : retour CRITIC avec les surprises de calibration. C'est le test
    de marché, chiffré.

## Règles d'airain héritées V1
db.py porte unique · statuts partout · receipts « statements never
questions » · jamais un crédit sur disqualified/OUT · big-spend gate ·
la masse ne monte jamais dans le contexte · drafts par défaut.
