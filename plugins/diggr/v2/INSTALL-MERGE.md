# INSTALL & MERGE — Bricks V2 → dans le produit, sans régression

> Pour le collaborateur qui reçoit ce zip (Robin / Rémi). Objectif clair :
> **reprendre ce qu'il y a de bon à prendre dans V2, de façon additive, sans
> introduire la moindre régression sur V1.** Ce document dit quoi installer,
> comment le prouver en 1 commande, et — le cœur — comment merger
> intelligemment : ce qui se greffe tel quel, ce qui se coordonne avec vos
> plans, ce qu'on ne touche pas.

## 0. Ce qu'il y a dans le zip

Le dossier `bricks-v2/` — un plugin Claude Code **autonome**, séparé du plugin
`bricks` (V1). **77 fichiers, Python 3 stdlib uniquement, zéro dépendance,
zéro clé** pour tout vérifier. Point d'entrée de lecture : `HANDOFF.md`.

C'est un **cerveau signal-natif** qui couvre les **4 archétypes GTM** du brief
du hackathon (Anthropic + Sillage + FullEnrich), avec une idée-force :
*un seul moteur de décision, pointé dans les deux sens du cycle de vie.*

| Archétype (brief) | Brique V2 |
|---|---|
| ICP scoring engine | `score_v2.py` (intervalles + bandes IN/BAND/OUT + VOI) |
| Outreach sequencer | `messaging_factory.py` + `outreach_send.py` |
| CRM auto-updater | `crm_adapter.py` (writeback Salesforce/HubSpot/Attio, par domaine) |
| Pipeline risk monitor | `pipeline_monitor.py` (le MÊME `score_v2`, arbre de risque) |

## 1. Installer & vérifier (2 minutes, zéro clé)

```bash
unzip bricks-v2-deploy.zip
cd bricks-v2
bash verify.sh          # 10/10 PASS attendu — toute la chaîne, zéro clé
```

`verify.sh` prouve, sur ta machine, chaque affirmation du HANDOFF : noyau de
scoring (22 tests) · scoring+VOI sur 303 PME réelles · chaîne Sillage (mock
E2E) · fabrique de messages · moteur de verdict · résolution de domaine ·
arbre de risque · pipeline monitor · CRM writeback · démo E2E 4-archétypes.
**Si 10/10, tu peux faire confiance au reste.** Puis : `HANDOFF.md` →
`ARCHITECTURE.md`. La démo qui résume tout : `python3 tools/demo_e2e.py`
(les 4 archétypes, 1 moteur, 3 piliers, en ~0,4 s).

## 2. Le contrat de non-régression (à lire avant de merger)

**V2 ne modifie AUCUN fichier du plugin `bricks` (V1).** Il vit à côté et
**réutilise** V1 au runtime, via les mêmes contrats, sans jamais les éditer :

- `db.py` reste la porte unique de la base — V2 l'appelle, ne le remplace pas.
- l'engine (`runner.py`/`researcher.py`) est réutilisé comme flotte de
  vérification — inchangé.
- statuts, gate de dépense §8, doctrine « drafts only / rien ne part sans
  humain » : respectés tels quels (l'envoi V2 est gated en triple clé).

**Conséquence : installer `bricks-v2/` tel quel ne peut PAS régresser V1** —
c'est purement additif, aucun fichier partagé touché. Le « merge intelligent »
consiste donc à décider, brique par brique, ce qui *graduate* de `bricks-v2`
vers le plugin `bricks` livré — chaque graduation restant additive.

## 3. Ce qu'il y a de bon à prendre — matrice de décision

**✅ ADOPTER** (greffe additive, aucun conflit V1, valeur nette immédiate) :

| Brique | Ce que ça apporte | Comment merger |
|---|---|---|
| `score_v2.py` + `schema/signal.schema.json` | Le joyau : scoring par **intervalles + bandes + VOI** (90 % vs 75 % mesuré, 22 tests) | nouveau skill `score-v2` à côté de `score` |
| `messaging_factory.py` + `messaging/` + skills `email-craft`, `prompt-smith-outreach` | **fabrique de messages** par axe × format, ressources fermées (0 hallucination) | à côté de `write-outreach` |
| `verdict.py` + `messaging/verdict-config.json` | **verdict OUI/NON** bayésien + ledger coût/RDV — capacité neuve | pur ajout |
| `pipeline_monitor.py` + `fixtures/retention-signals.json` | **4ᵉ archétype** : risque de churn via le MÊME moteur, signaux Sillage (champion/competitor/M&A) | nouveau skill `pipeline-monitor` |
| `domain_resolver.py` | jointure nom→domaine **zéro-clé** (indispensable à Sillage), testée réel | plomberie `tools/` |
| `sillage_adapter.py` + `schema/sillage.*` + `fixtures/sillage.capabilities.json` | anti-corruption layer Sillage (mock+REST+MCP-discovery), 8 types ontologisés | **c'est la brique `signal-sillage`** attendue |
| 9 `agents/`, skills `campaign-v2`/`concept-to-signals`/`sillage-connect`, `demo_e2e.py` | l'orchestration signal-native + la démo | avec le reste |

**⚠️ COORDONNER** (bon code, mais recouvre un plan existant — aligner avant de livrer, ne PAS double-livrer) :

| Brique | Pourquoi coordonner |
|---|---|
| `outreach_send.py` | recouvre la lane `outreach-send` prévue par Rémi — comparer les deux designs, en garder UN |
| `fullenrich_adapter.py` | FullEnrich existe déjà en **MCP** côté V1 ; ici c'est le **REST**. Choisir le transport, pas empiler |
| `crm_adapter.py` | CRM writeback — vérifier qu'il n'entre pas en collision avec `crm-import`/`crm-push` (Rémi, data-out) ; le mapping des champs est agnostique (Salesforce/HubSpot/Attio) |

**Règle d'or** : chaque brique adoptée = **un nouveau skill/outil**, jamais une
réécriture d'un existant. On enrichit le catalogue, on ne remplace rien.

## 4. La checklist de merge sans régression (par brique graduée)

1. **Additif** : nouveau `skills/<nom>/` ou `tools/<nom>.py` — ne touche aucun
   fichier existant. Si une brique exigeait de modifier `db.py` ou
   `CONVENTIONS.md` (surface partagée) → **STOP**, PR à double approbation
   (votre règle). Aucune brique V2 n'en a besoin telle quelle.
2. **Bump de version** (votre Rule 3) : `plugins/bricks/.claude-plugin/plugin.json`
   ET `.claude-plugin/marketplace.json` — sinon le cache sert la version stale.
3. **Gate de régression** : après merge, `bash bricks-v2/verify.sh` (10/10)
   **et** vos field-tests V1 restent verts.
4. `claude plugin update bricks@bricks` + redémarrage de session.

## 5. Ce qu'on ne touche pas (garde-fous)

- Ne pas modifier `db.py`, l'engine, `CONVENTIONS.md` sans double approbation.
- Ne pas câbler `bricks-v2` au marketplace tant que la revue n'est pas faite
  (il n'y est pas — volontairement).
- Ne pas activer les signaux `legal_hold` (tracking de personnes nommées :
  `S-EVT-13`, `P-HOR-02.b`) sans validation juriste — cf. `ARCHITECTURE.md §9`.
- Ne pas envoyer d'emails sans le GO campagne explicite d'`outreach_send.py`
  (dry-run par défaut, c'est voulu).

## 6. Chemin recommandé (le plus sûr)

1. **Jour 1** : installer `bricks-v2/` tel quel (plugin séparé, risque nul),
   le faire tourner en mock (`bash verify.sh`, `demo_e2e.py`), brancher
   Sillage/FullEnrich réels (`DAY1-SILLAGE.md`, rituel ~45 min).
2. **Après validation terrain** : graduer une par une les briques **✅ ADOPTER**
   du §3 dans le plugin `bricks`, chacune additive + bump + gate §4.
3. **Coordonner** les 3 briques **⚠️** avec vos lanes existantes avant livraison.

Le meilleur de V2 — scoring signal-natif, fabrique de messages, moteur de
verdict, moniteur de risque, CRM writeback — entre ainsi dans le produit
**sans qu'aucune ligne de V1 ne bouge**.

---

*Contexte honnête : Sillage réel n'est pas encore branché (adapter + rituel
prêts, mock prouvé E2E) ; `outreach_send` et l'enrichissement payant restent à
éprouver en conditions réelles. Le brief officiel ne mentionne aucun jury —
tout est argumenté sur les 4 archétypes et les 3 personas du brief.*
