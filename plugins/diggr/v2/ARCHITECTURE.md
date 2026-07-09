# BRICKS V2 — Le moteur signal-natif

> **Thèse produit.** V1 répond à « trouve-moi des entreprises qui ressemblent à X ».
> V2 répond à « **j'ai un concept — dis-moi qui l'achèterait, pourquoi, et prouve-le** ».
> Le moat n'est ni la donnée (Sillage l'a) ni l'envoi (tout le monde envoie) : c'est la
> **subtilité** — la finesse avec laquelle un concept est décomposé en signaux nécessaires,
> et la rigueur avec laquelle ces signaux sont confrontés à ce que les sources savent
> réellement observer. Des milliers de sous-signaux, un score explicable, un budget dépensé
> là où il change la décision.

---

## 0. La chaîne A→Z

```
 « J'ai une idée / un produit / un service »
        │
        ▼
 ① STRATEGIST ──────────── concept → 1-3 THÈSES D'ACHAT falsifiables
        │                          (qui achète, pourquoi, pourquoi maintenant)
        ▼
 ② SIGNAL-ARCHITECTS ×N ── chaque thèse → ONTOLOGIE DE SIGNAUX (3 couches P/S/O,
        │                   signaux latents → proxies observables ; milliers de sous-signaux)
        ▼
 ③ CRITIC ──────────────── red-team : tue les faux « nécessaires », les doublons,
        │                   les signaux non-mesurables, les signaux illégaux
        ▼
 ④ BROKER ──────────────── matching signaux NÉCESSAIRES ↔ signaux DISPONIBLES
        │                   (catalogue de capacités Sillage/FullEnrich/registres/web)
        ▼
 ⑤ PROSPECTOR ──────────── gates P compilés en requêtes Sillage → UNIVERS CANDIDAT
        │                   (SIREN-dédupliqué, ingéré en base, statuts V1)
        ▼
 ⑥ SCORER (code pur) ───── score de pertinence par intervalle [pessimiste, optimiste]
        │                   → bandes IN / BAND / OUT
        ▼
 ⑦ VOI ALLOCATOR ───────── le budget de vérification va UNIQUEMENT sur la bande
        │                   d'incertitude, proxy le plus décisif d'abord
        ▼                   (VERIFIER fleet = engine V1 réutilisé pour les checks LLM)
 ⑧ CONNECTOR ───────────── FullEnrich : contacts du persona de la thèse,
        │                   uniquement au-dessus de la coupe, gate de dépense V1 §8
        ▼
 ⑨ COMPOSER + SEND-GUARD ─ séquences dont CHAQUE message cite les signaux qui ont
        │                   fait entrer l'entreprise ; GO campagne humain → envoi
        ▼                   automatisé sous caps ; réponses = events
 ⑩ VALIDATION LOOP ─────── taux de réponse par tier → si tier A ne bat pas tier C,
                            la thèse ou les poids sont FAUX → recalibrage.
                            V2 n'est pas un outil de lead-gen : c'est un
                            INSTRUMENT DE VALIDATION DE MARCHÉ.
```

---

## 1. Les concepts fondamentaux

### 1.1 La thèse d'achat (buying thesis)

Un concept ne cible presque jamais UN acheteur. Le STRATEGIST produit 1 à 3 **thèses**
distinctes, chacune falsifiable :

> *Thèse = « [type d'organisation] dans [état] achètera [concept] parce que [douleur]
> devient intenable quand [déclencheur], à condition que [prérequis]. »*

Exemple MemoVAL, thèse n°1 (cédant) : « une PME indépendante de 1,5-10 M€ dont le
dirigeant de 58-68 ans EST la mémoire opérationnelle achètera la capture de mémoire
parce que la décote de cession devient tangible quand la transmission entre dans
son horizon de 1-3 ans, à condition que l'entreprise soit assez mûre pour avoir une
mémoire à capturer. »

Chaque thèse a **son** arbre de signaux, **sa** campagne, **ses** métriques de
validation. On ne mélange jamais les scores de deux thèses.

### 1.2 Signal latent vs proxy observable — la séparation qui rend « des milliers » tractable

L'erreur classique des scorings : confondre ce qu'on veut savoir avec ce qu'on peut voir.

- Un **signal latent** est un trait de l'entreprise qu'on ne voit jamais directement :
  *« le dirigeant prépare sa sortie »*, *« le savoir est concentré dans une tête »*.
- Un **proxy observable** est une mesure imparfaite de ce trait : âge du dirigeant au
  registre (fidélité moyenne), annonce BODACC de modification de gouvernance (fidélité
  haute, couverture faible), embauche récente d'un directeur général (fidélité moyenne),
  mention presse « cède » (fidélité haute, couverture quasi nulle)…

**Structure : ~50-150 signaux latents par thèse × 5-30 proxies chacun = des milliers de
sous-signaux**, sans que les poids deviennent de la soupe : les poids vivent au niveau
latent (interprétable), les proxies portent seulement `fidélité` (P(observé|trait vrai)
vs P(observé|trait faux)), `couverture` (chez combien de candidats c'est mesurable) et
`coût` (crédits/temps pour le vérifier).

### 1.3 Les trois couches — et la vraie sémantique de « nécessaire »

| Couche | Sémantique | Traitement dans le score |
|---|---|---|
| **P — Principaux (nécessaires)** | Sans ce trait, l'entreprise **ne peut pas** être acheteuse. | **Gates multiplicatifs** : un P à zéro écrase le score. |
| **S — Secondaires (prédictifs)** | Chaque trait **augmente la probabilité** d'achat ; son absence informe sans condamner. | **Évidence additive en log-vraisemblance**, plafonnée par cluster ; contribution négative **amortie ×0,3** (un S faux ne punit jamais comme un gate — la nécessité vit en P). |
| **O — Optionnels (contextuels)** | N'augmentent guère la probabilité mais **améliorent l'approche** (accroche, timing, canal). | Bonus borné (≤5 pts) + **carburant de personnalisation** du COMPOSER. |

Deux subtilités non négociables :

1. **La fausse nécessité est le poison n°1.** Le CRITIC a mandat explicite de dégrader
   P→S tout signal qui est *typique* sans être *nécessaire* (le piège « doit utiliser
   Shopify » qui tue les prospects en pleine migration). Notre field-test du 08/07 l'a
   prouvé en sens inverse : un secteur qu'on croyait bon (ingénierie) était en réalité
   un **anti-signal** — précision passée de 45 % à 75 % en le déplaçant en kill rule.
2. **Les gates P sont doux, pas binaires.** Un P vaut `max(plancher, croyance)` avec
   plancher ~0,05 : une entreprise qui échoue un gate mais accumule une évidence S
   extraordinaire n'est pas jetée — elle tombe dans une **file de repêchage** revue par
   l'humain. C'est là qu'on découvre que la thèse était trop étroite.

### 1.4 L'inobservable ne disparaît pas — il change de canal

Le BROKER classe chaque signal : `observable` (≥1 proxy disponible), `coûteux`
(proxy existant mais cher), `inobservable` (aucune source). Les inobservables ne sont
PAS supprimés : ils deviennent **les questions de qualification du premier échange**
(script d'appel / première réponse email). Le système sait ce qu'il ne sait pas, et
transforme ce manque en plan de conversation. C'est une partie du moat : la liste des
questions vaut autant que la liste des entreprises.

---

## 2. L'équipe d'agents

Principe anti-spam : **le fan-out n'existe qu'à deux endroits** (architectes au design,
vérificateurs au runtime — et ces derniers sont l'engine V1 existant). Tout le reste est
séquentiel. L'état vit dans la base (`db.py` porte unique, statuts V1) — jamais dans la
conversation.

| # | Agent | Quand | Entrée → Sortie | Modèle |
|---|---|---|---|---|
| 1 | **CHEF** (session principale) | permanent | orchestre, écrit en base, tient les gates §8 | session |
| 2 | **STRATEGIST** | 1×/concept | interview + concept → `theses.json` (1-3 thèses) | fort |
| 3 | **SIGNAL-ARCHITECT** ×6-8 | 1 vague/thèse | thèse + dimension → 100-300 signaux (schéma strict) | fort |
| 4 | **CRITIC** | après ② et après calibrage | arbre complet → verdicts kill/demote/merge par signal | fort |
| 5 | **BROKER** | après ③ + à chaque connexion de source | signaux × catalogue capacités → mapping proxies, inobservables | moyen |
| 6 | **PROSPECTOR** | 1×/campagne + syncs | gates P → requêtes Sillage → ingestion univers | moyen |
| 7 | **VERIFIER** (fleet) | boucle VOI | 1 check LLM = 1 agent jetable (runner.py/researcher.py V1) | faible |
| 8 | **CONNECTOR** | au-dessus de la coupe | comptes IN → contacts FullEnrich (persona de la thèse) | moyen |
| 9 | **COMPOSER** | après ⑧ | évidence du score → séquences citant les signaux | fort |
| 10 | **SEND-GUARD** | permanent | approbation campagne, caps, suppression, stop-on-reply | code |

Les **dimensions** des architectes (une vague = 6-8 agents en parallèle, une fois) :
firmographique · organisationnelle/gouvernance · événementielle/déclencheurs ·
technographique/empreinte-web · financière · réglementaire/juridique · culturelle/surface
marketing · temporelle/saisonnalité. Chacun est aveugle aux autres → diversité maximale ;
le CRITIC déduplique ensuite (c'est voulu : mieux vaut fusionner des doublons que rater
un angle).

---

## 3. Le moteur de scoring (la partie « brillante »)

### 3.1 Vue d'ensemble

Trois nombres par entreprise, pas un :

```
score_pessimiste ≤ score_attendu ≤ score_optimiste
```

- **attendu** : les proxies non vérifiés valent leur prior.
- **pessimiste / optimiste** : « UNE vérification de plus » — par signal, le
  proxy inconnu le plus décisif résolu contre/pour l'entreprise, avec son LR
  **pondéré par la couverture** (un jackpot x20 mesurable chez 5 % des
  candidats ne promet pas 100 à tout le monde ; une entreprise sans données
  ne survit pas en BAND — elle est OUT tant que rien n'est observé).

D'où trois **bandes de décision** :

- **IN** : `pessimiste ≥ seuil` — plus rien à vérifier, on enrichit (FullEnrich).
- **OUT** : `optimiste < seuil` — plus un crédit dépensé (statut `disqualified`, règle V1).
- **BAND** : l'intervalle chevauche le seuil — **c'est LE périmètre du budget de
  vérification**. Personne d'autre ne consomme un centime.

### 3.2 Formule

Pour une entreprise c et une thèse t :

```
score(c,t) = 100 · GateP(c) · σ( k · (E_S(c) − θ) ) + bonus_O(c)      [borné 0-100]

GateP(c)  = ∏ᵢ max(εᵢ, bᵢ)^{critᵢ}          gates P doux, criticité ∈ {1,2}
E_S(c)    = Σ_clusters min( cap_cl , Σ_{i∈cl} wᵢ·(2bᵢ−1) )   évidence secondaire
wᵢ        = ln(LRᵢ)                            LR ∈ {1.2, 2, 5, 20} (classes ancrées)
bᵢ        = croyance dans le signal latent i, mise à jour bayésienne par proxies
bonus_O   ≤ 5 pts
```

où pour chaque proxy observé sur le signal i :
`odds(bᵢ) ← odds(bᵢ) · [fidélité / taux_faux_positif]` si observé-vrai (et l'inverse
si observé-faux) ; **non-observé = pas de mise à jour** (jamais assimilé à faux — la
leçon des signaux presse du 08/07 : l'absence d'article ne dit rien).

### 3.3 Les cinq garde-fous qui séparent ce score d'un score naïf

1. **Anti-double-comptage par clusters.** « SARL familiale », « nom patronymique »,
   « fondateur = dirigeant » disent la même chose. Les architectes taguent les clusters
   de corrélation ; la contribution d'un cluster est **plafonnée** (`cap_cl` = poids du
   plus fort membre × 1,5). Sans ça, mille sous-signaux = mille occasions de compter
   trois fois la même vérité, et le score explose vers le haut pour les entreprises
   « typiques » plutôt que « pertinentes ».
2. **Poids en classes ordinales, jamais en nombres libres.** Un LLM est bon pour dire
   « ce signal est un indice faible / notable / fort / quasi-décisif » (LR 1,2 / 2 / 5 /
   20) et mauvais pour inventer « 0,73 ». On ne lui demande QUE la classe + une phrase
   de justification P(signal|acheteur) vs P(signal|non-acheteur). Le nombre est dérivé.
3. **Vérification d'identifiabilité avant tout run.** Le scorer simule la distribution
   des scores sur l'univers : si >30 % des candidats scorent >80, les poids sont trop
   lâches → recalibrage automatique (température) + alerte. Un score qui dit oui à tout
   le monde est un score mort ; on le détecte AVANT de dépenser.
4. **Décomposition exigée.** Chaque score sort avec ses contributions par signal +
   l'URL d'évidence de chaque proxy observé. C'est à la fois l'auditabilité (client,
   client), le carburant du COMPOSER (le mail cite les 3 signaux dominants), et le
   debug du calibrage (quel signal a menti ?).
5. **Le score est du code pur** (mode A V1) : le LLM travaille au *design-time*
   (arbres, classes de poids) et au *verify-time* (checks flous par l'engine) — jamais
   au *score-time*. Même entrée → même score, pour toujours. 10 000 entreprises se
   scorent en secondes, gratuitement, et le calibrage est reproductible.

### 3.4 L'allocateur de budget (Value of Information)

Le budget (crédits Sillage, crédits FullEnrich, scrapes, appels engine) est dépensé par
**valeur d'information décroissante** :

```
priorité(check) = P(le résultat fait changer la bande) × |enjeu| / coût(check)
```

**Décision-first** : un check n'entre au plan que s'il peut faire CHANGER DE
BANDE (`flips ≥ 1`) — jamais un centime sur une vérification qui ne déciderait
rien, même gratuite. En pratique, greedy par étages :

| Étage | Source | Coût | Qui |
|---|---|---|---|
| 0 | Registres/API gouv (déjà en base) | 0 | tous les candidats |
| 1 | Requêtes Sillage segmentaires (le retrieval EST une vérification des P) | faible/1000 | univers |
| 2 | Lookups par entreprise : événements Sillage, site web, presse | moyen | **BAND uniquement** |
| 3 | Checks LLM (engine V1), FullEnrich | cher | BAND proche du seuil, puis IN |

Règles héritées V1, non négociables : jamais un crédit sur `disqualified` ; jamais payer
deux fois (job ids en `state.json`) ; big-spend gate §8 (silencieux sous seuil, UN GO
groupé au-dessus) ; receipts avec coût réel et wall-time.

### 3.5 Le calibrage — trois horloges

1. **Avant campagne** (gratuit) : identifiabilité (3.3.3) + juge adversarial sur
   échantillon n=20, protocole du 08/07 (45→65→75 % : la méthode est éprouvée).
2. **Pendant** : chaque vérification VOI qui contredit son prior est loggée ; si un
   signal accumule les surprises, son LR est suspect → file du CRITIC.
3. **Après** (la seule vérité) : taux de réponse/RDV **par bande et par tier**. Si
   tier A ne bat pas tier C, la thèse est fausse ou les poids mentent — le système
   le DIT, chiffres à l'appui, au lieu de laisser croire que « la prospection, c'est
   dur ». C'est ça, valider un marché. **Honnêteté statistique codée** : sous
   n=25 contacts par cellule, le système S'ABSTIENT de tout verdict de taux
   (il dit « échantillon insuffisant », jamais un pourcentage sur n=6) ; les
   verdicts affichent leur intervalle d'incertitude.

---

## 4. Intégration Sillage (accès demain — système prêt aujourd'hui)

### 4.1 Posture : anti-corruption layer + découverte de capacités

On ne connaît pas encore la surface exacte de l'API/MCP. Le système est donc construit
autour d'un **adapter** (`tools/sillage_adapter.py`) avec :

- une **interface abstraite** stable (le reste de V2 ne voit qu'elle) :
  `capabilities()`, `search_companies(filters) → itérateur`, `get_company(siren)`,
  `list_signals(siren|segment, kinds, since)`, `subscribe(kinds)` *(optionnel)* ;
- un **backend mock** complet (l'univers réel du test du 08/07 + événements
  synthétiques) — toute la chaîne tourne AUJOURD'HUI dessus ;
- un **backend REST/MCP** dont seuls les endpoints/schémas restent à remplir
  (`schema/sillage.endpoints.json`, généré par la découverte).

### 4.2 Le rituel de connexion (15 min, jour J) — skill `sillage-connect`

1. **Connexion** MCP (`/mcp`) ou clé API dans `~/.bricks/env` (`SILLAGE_API_KEY`).
2. **Découverte** : énumérer les outils MCP + parser leurs schémas JSON (ou fetch de
   l'OpenAPI si REST) → générer `staging/sillage.capabilities.json` : pour chaque
   capacité, champs filtrables, types de signaux, clés d'identité (SIREN ?), pagination,
   coûts. Trois requêtes-sondes bénignes confirment le format réel des réponses.
3. **Re-mapping automatique du BROKER** : le catalogue de capacités fraîchement
   découvert est confronté à l'ontologie → chaque proxy `sillage:*` passe de
   `présumé` à `confirmé | absent | différent(champ réel)`.
4. **Validation par requêtes-étalons** : 3 golden queries dont on connaît la réponse
   (dont : « PME 1,5-10 M€, dirigeant né ≤1966, région lyonnaise » → recouvrement
   attendu ≥60 % avec nos **194 ICP-fit validés du 08/07**). Si le recouvrement est
   faible, c'est la carte des champs qui est fausse — pas la thèse ; on corrige le
   mapping avant toute campagne.
5. **Campagne fumée** : thèse MemoVAL, gates P seuls, 50 entreprises, zéro envoi.

### 4.3 Le compilateur de requêtes

`thesis → [SillageQuery]` : les gates P s'expriment en filtres natifs quand la capacité
existe (âge dirigeant, CA, NAF, géo…) ; sinon décomposition (pas de OR natif → N
requêtes unionnées, dédup SIREN) ; les signaux S événementiels deviennent des
`list_signals(kinds=[...], since=...)`. Deux disciplines V1 conservées : la **masse ne
transite jamais par le contexte** (export → `staging/` → `import-csv`) et chaque page
brute est cachée dans `staging/` (rejouable, auditable).

### 4.4 Ce que Sillage change au scoring

Les signaux Sillage sont datés → chaque proxy événementiel porte une **décroissance**
(`fresh ≤60j : ×1,0 ; context ≤180j : ×0,5 ; ancien : ×0,2` — courbe par kind,
recalibrable). Le flux temps réel (si disponible) alimente une file « why_now chaud » :
une entreprise IN qui émet un signal frais remonte en tête de la file d'envoi du jour.

---

## 5. Intégration FullEnrich

Déjà branché en V1 (MCP `mcp.fullenrich.com`). Rôle V2, strictement en aval de la coupe :

- **Qui enrichir** : le(s) persona(s) de la THÈSE (pas « un dirigeant » générique —
  la thèse cédant vise le dirigeant-actionnaire ; une thèse DAF viserait le DAF).
- **Waterfall** email+téléphone, bulk asynchrone (job ids persistés dans `state.json`,
  relance = fetch, jamais re-soumission = jamais payer deux fois).
- **Bonus broker** : les recherches FullEnrich (souvent gratuites en preview) servent
  aussi de proxies aux signaux organisationnels (taille d'équipe visible, présence d'un
  rôle donné) — le BROKER les inscrit au catalogue comme n'importe quelle source.
- Gate §8 : l'enrichissement est LE poste cher ; il n'est déclenché que sur IN, par
  vagues, avec UN GO groupé au-dessus du seuil.

---

## 6. La fabrique de messages (bout de chaîne — schéma Thomas 08/07)

```
 DONNÉES (le tableau)          FORMAT (FORMATS.md)      skill « je sais
   colonnes = SIGNAUX CLÉS        le support :           écrire un mail »
   + signal_cle + axe             email parfait,              │
        │                         relance, breakup…           ▼
        ▼                              │              ┌──────────────┐
   AXES (Agent 1 = AXE-MAPPER,         ▼              │    LLM ②     │──→ ✉ MAIL
   Opus 4.8 + skill « je sais    BASE = AXE × FORMAT ─→   génération  │   (draft)
   écrire un prompt »)                 ▲              └──────▲───────┘
        │                              │                     │
        └── prompt d'axe ──────────────┘              RESSOURCES (par
                                                      entreprise : les faits
                                                      DISPONIBLES du tableau)
```

1. **Le TABLEAU** (`messaging_factory.py select-key-signals` + `materialize`) :
   les SIGNAUX CLÉS sont choisis judicieusement (fréquence en top-contributeur
   × poids × couche, dans la population IN/BAND-haut) et deviennent des
   **colonnes sur mesure** (`sig_*` taguées [P]/[S]/[O]) + `signal_cle`
   (dominant) + `axe` — le tableau de l'UI se groupe par signal clé.
2. **Les AXES** (Agent 1 = AXE-MAPPER, **Opus 4.8**, skill
   `prompt-smith-outreach`) : pré-groupement déterministe par signal
   dominant, puis l'agent nomme 3-6 axes-histoires (« l'heure tourne »,
   « le fonds invisible »), fusionne les groupes interchangeables, et écrit
   le **PROMPT D'AXE** de chacun.
3. **Le FORMAT** (`messaging/FORMATS.md` + `formats.json`) : les supports de
   prospection — F1 email parfait (OPPA×CPPC), F2 relance angle neuf,
   F3 breakup, F4 DM, F5 invite sans note, F6 mini-audit — croisement de la
   doctrine V1 et des frameworks growth du corpus.
4. **BASE = AXE × FORMAT**, puis la couche déterministe synthétise les
   **RESSOURCES** de chaque entreprise (les faits observés du tableau, avec
   URLs et poids ; les inconnues deviennent les questions de qualification) —
   et compile le **PROMPT SUR MESURE** (`compile-prompt` : axe → format →
   offre → voix → ressources fermées → auto-contrôle).
5. **LLM ② + skill `email-craft`** (« je sais écrire un mail ») : la
   génération — les 5 lois (test du pair, chaque phrase gagne sa place,
   personnalisation reliée au problème, leur monde d'abord, la vérité
   seulement). Chaque draft porte `axe` et `format_id` : la boucle de
   validation mesure les réponses **par axe × format** (n ≥ 25 sinon
   abstention).

L'envoi reste sous double clé (inchangé) :

1. **GO campagne** (humain, une fois) : le SEND-GUARD présente les prompts
   d'axe + 10 drafts réels + volumes + calendrier.
2. **Envoi automatique** ensuite, sous contraintes codées : caps/jour,
   fenêtres horaires, warm-up, suppression list, **stop-séquence sur
   réponse**, bounce → `invalid`, désinscription → kill ; LinkedIn jamais
   automatisé (file manuelle).
3. Tout envoi/réponse est un **event en base** → boucle de validation §3.5.

Statuts messages V1 conservés : `draft → approved → sent` (+ `replied`,
`bounced`). Rien ne part sans GO campagne ; rien ne repart quand quelqu'un
répond.

---

## 7. Données (nouvelles tables, mêmes règles)

```
theses      _id, concept, statement, persona, status, created_at
signals     _id, thesis_id, layer(P|S|O), claim, cluster, lr_class, crit, floor,
            legal_flag, status(proposed|kept|demoted|killed), source_agent
proxies     _id, signal_id, source(sillage|fullenrich|registry|web|news|llm_check),
            capability, op, value, fidelity, coverage, cost_class, status(presumed|confirmed|absent)
evidence    _id, company_id, proxy_id, value(true|false|unknown), evidence_url,
            source_payload_ref, cost_spent, checked_at
scores      _id, company_id, thesis_id, pessimistic, expected, optimistic, band,
            top_contributors(json), computed_at, tree_version
```

`evidence` est **append-only** : les scores sont recomputables à toute date (audit,
debug de calibrage, « pourquoi cette boîte était IN le 12 et OUT le 19 ? »).
Tout passe par `db.py` (porte unique V1). Les payloads bruts restent dans `staging/`.

## 8. Continuité V1 — ce qu'on ne touche pas

La base-comme-bus, les statuts, `db.py`, l'engine (runner/researcher) réutilisé tel quel
comme fleet de vérification, le big-spend gate §8, les vagues §9, le data-plane §10,
les receipts « statements never questions », drafts-par-défaut. **V2 = un cerveau
au-dessus de la plomberie V1, pas une réécriture.** Les briques V1 (find, enrich,
write-outreach…) restent invocables ; V2 les nourrit avec de meilleures listes et de
meilleures accroches.

## 9. Risques nommés (à traiter, pas à cacher)

1. **RGPD/éthique des signaux personnels — LE risque non-technique n°1** :
   l'âge d'un dirigeant est une donnée publique du registre, mais le
   **keyword-tracking des posts LinkedIn d'une personne nommée** pour inférer
   son intention de céder est un traitement à finalité commerciale dont la
   base légale (intérêt légitime : attente raisonnable + test de balance)
   doit être DOCUMENTÉE, et l'inférence « prépare sa sortie » frôle le
   profilage ; le ciblage sur critère d'âge expose aussi à l'angle
   discrimination. Le `legal_flag` n'est PAS une analyse : les signaux
   personne-physique (S-EVT-13, P-HOR-02.b) sont **gelés
   (`legal_hold`) jusqu'à validation juriste + DPIA légère**. Donnée
   publique ≠ traitement licite. L'outreach reste B2B, opt-out immédiat.
2. **Biais des poids LLM** : contenu par les classes ordinales + l'identifiabilité +
   le juge n=20 + la boucle réponses. Le poids n'est jamais un chiffre sorti du chapeau
   qui survit sans confrontation.
3. **Sillage inconnu** : contenu par l'adapter + la découverte + les golden queries.
   Si une capacité présumée manque, le BROKER dégrade proprement (proxy `absent` →
   le signal redevient inobservable → question de qualification), le système reste
   entier.
4. **Sur-automatisation de l'envoi** : contenu par le GO campagne, les caps codés et
   le stop-on-reply. La réputation d'envoi est un actif qui se détruit en une semaine.

## 10. Ce qui existe déjà dans ce dossier (prêt à l'emploi)

- `tools/score_v2.py` — le moteur (gates, clusters, intervalles, bandes, VOI,
  identifiabilité) + tests. **Tourne aujourd'hui.**
- `tools/sillage_adapter.py` — interface + mock (303 PME réelles) + stub REST/MCP +
  parser de découverte. **Tourne aujourd'hui en mock.**
- `schema/*.json` — schémas thèse / signal / capacités.
- `fixtures/` — thèse MemoVAL + arbre de signaux de démonstration + univers réel.
- `agents/*.md`, `skills/*` — l'équipe et les protocoles d'orchestration.
- `DAY1-SILLAGE.md` — le rituel du jour J, pas à pas.
- Démo E2E : `python3 tools/score_v2.py demo` (voir README).
