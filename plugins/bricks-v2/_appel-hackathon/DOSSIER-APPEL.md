# APPEL — Le Tribunal de Falsification
### Dossier de l'idée gagnante · Hackathon IA-GTM (Anthropic × Sillage × FullEnrich)

> **« Chaque raison de perte est une hypothèse datée sur le monde. APPEL surveille le
> monde, et quand le monde tue l'objection, il livre le certificat de décès — preuve
> datée, contact vérifié vivant, brouillon prêt, prix affiché. Quand le monde ne la tue
> pas, il refuse de rouvrir. »**

Produit issu d'une exploration double-diamant menée sur **Fable 5 via l'API** (6 lentilles
problème → synthèse → critique adversariale → 6 architectes solution → double matrice →
jury à 3 têtes). Coût total de l'exploration : **~2,4 $**. Le cœur du produit est **prouvé
empiriquement** (voir §3), pas seulement conçu.

---

## 0. En une page

- **Douleur.** Le cimetière des *closed-lost* est le plus gros actif dormant de tout CRM
  (CAC déjà payé, relation déjà tiède) — et personne ne re-teste jamais l'objection qui a
  tué le deal. Pire : quand un événement la rend caduque (« pas de budget » × une levée de
  22 M€), personne ne le voit.
- **Idée.** APPEL traite chaque raison de perte comme une **hypothèse falsifiable**. Il
  surveille le monde (Sillage), et le jour où un événement **falsifie** l'objection, il
  rend un verdict — **FALSIFIÉE / INTACTE / ABSTENTION** — puis, uniquement si c'est
  falsifié et rentable, dépense un crédit FullEnrich pour livrer un dossier de réouverture
  au **bon contact encore vivant**, avec le brouillon.
- **Pourquoi ces 3 outils et pas d'autres.** Chacun est mortel au retrait (§4). Et Claude y
  est le **héros** : la polarité *raison × événement* (même levée → 3 verdicts opposés) est
  le seul maillon qu'aucune table de règles ne peut rendre — l'argument massue dans un
  hackathon **organisé par Anthropic**.
- **Pourquoi ça gagne.** C'est la seule entrée dont le climax est un **refus** : *195 deals
  laissés dormir avec justification, ~15 crédits loggés*, dans une salle où tous les autres
  systèmes démontreront qu'ils *envoient plus*.
- **Honnêteté (la jurisprudence appliquée à soi-même).** On ne revendique aucun revenu. La
  métrique de démo est : *objections falsifiées + preuve datée + contact vérifié +
  brouillon*. Les raisons de perte réelles sont sales → l'abstention est une **fierté**, pas
  un aveu.

---

## 1. Le problème — sortie du Diamant 1 (espace PROBLÈME)

Six lentilles (dirigeant B2B, ingénieur GTM/RevOps, équipe commerciale, fossé signal→action,
gaspillage, contrarian) ont exploré la douleur GTM. La matrice a dédoublonné 8 clusters. Le
synthétiseur a d'abord couronné **C2 — le radar post-signature (churn)**. Le **critique
adversarial l'a renversé**, et c'est le tournant du projet :

- **C2 = le pitch mot-pour-mot de UserGems / Champify.** « Champion parti = risque churn +
  re-signer le champion ailleurs » est *leur* feature phare. L'unicité prétendue (9/10) est
  indéfendable.
- **La couverture 40-60 % est disqualifiante pour un radar de RISQUE** : un faux négatif
  détruit la confiance (un churn manqué = désinstallation).
- **L'outcome est indémontrable en 48h** (la règle même qui avait tué la thèse d'origine).
- Pour un hackathon **Anthropic**, C2 est le cluster où **Claude est le plus remplaçable**
  (un tri en 3 buckets = un prompt, pas de l'orchestration).

**Verdict du Diamant 1 → attaquer C3, reformulé en FALSIFICATION D'OBJECTION.** Ses avantages
structurels, invisibles au premier scoring :

| Avantage | Pourquoi c'est décisif |
|---|---|
| **Le signal déclencheur est dans le PASSÉ** | Une levée du mois dernier est un fait daté, interrogeable ce week-end → **zéro risque de fraîcheur en démo**. |
| **Récit inoccupé** | UserGems tracke les *contacts* des closed-lost ; **personne ne raisonne sur la RAISON DE PERTE** × événement. |
| **Claude est le héros** | Le croisement raison × signal est impossible en règles — cœur de valeur, pas garniture. |
| **FullEnrich non-négociable** | 20-30 % des contacts ont bougé à 8-18 mois (estimation dérivée du turnover, pas un fait). |
| **L'échec ne coûte rien** | Rater une réouverture ne coûte rien : le deal était déjà mort. La limite 40-60 % qui *tue* C2 est ici sans conséquence. |
| **Économie imbattable** | Closed-lost = CAC déjà payé, relation tiède, coût marginal ≈ 0. |

*(Trace complète : `exploration/diamant1-synthese.md` et `diamant1-critique.md`.)*

---

## 2. La solution — sortie du Diamant 2 (espace SOLUTION)

Six architectes (compositeur de signaux, moteur du « quand », tueur de gaspillage, radar,
agent autonome, wildcard) ont produit 18 concepts. La **double matrice problèmes × solutions**
les a fusionnés en 7, notés au **produit multiplicatif** (Σ fit×sévérité × unicité × démo48h ×
wow × aiguille). Un seul a émergé nettement :

### 🏆 APPEL — Le Tribunal de Falsification — composite 49,0 (> 2,5× le second)

Le mécanisme, en 6 étapes :

1. **Typage déterministe** de la raison de perte (BUDGET / COMPETITOR / TIMING / AUTHORITY /
   NEED / DIRTY) — 0 token.
2. **Surveillance Sillage** compilée *par objection* sur la liste fermée des domaines
   closed-lost (push une fois, poll pour toujours — usage rêvé de l'asynchrone + du quota).
3. **Le procès** : procureur (le falsificateur) vs défense (les anti-signaux), Claude juge la
   **polarité** raison × événement.
4. **Verdict** : `FALSIFIÉE` / `INTACTE` (voire renforcée) / `ABSTENTION`.
5. **Gate VOI** : ne dépenser un crédit FullEnrich **que** si FALSIFIÉE **et** rentable →
   contact actuel vérifié (successeur si l'ancien est parti).
6. **Dossier de réouverture** : preuve datée + bon contact + brouillon + prix → writeback CRM.

**Les satellites** (le reste des concepts devient des couches, pas des produits concurrents) :
- **Demi-Vie** → couche d'ordonnancement : chaque falsification porte une fenêtre
  [pess, attendu, opt] ; le ticket qui expire est **détruit en live** sur scène.
- **Morgue gérée** → salle des machines invisible : kill-rule + knapsack de crédits rendent
  « zéro crédit gaspillé » *démontrable*, pas déclaré.
- **Revanche** → branche-vedette : lost-to-competitor, **deux domaines surveillés par deal**
  (prospect + concurrent) — usage Sillage qu'aucun autre concept n'a.
- **Comité fantôme** → coda de 30 s : « on ne rouvre pas par la porte qui s'est fermée ».
- **Second Match** (le champion qui rejoue ailleurs) → **éliminé** : feature mot-pour-mot de
  UserGems.

*(Trace complète : `exploration/diamant2-matrice.md` et `diamant2-jury.md`.)*

---

## 3. La preuve empirique — le triptyque, tourné sur Fable 5

Le cœur (`tribunal.py`) n'est pas une maquette : il **tourne**. Même événement (une Série B de
22 M€), trois raisons de perte différentes, **trois verdicts opposés** — chacun raisonné,
chacun portant son propre contre-argument honnête (champ `risque`) :

| Deal | Raison de perte | Événement (identique) | Verdict | Confiance | Décision |
|---|---|---|---|:---:|---|
| **TechFlow** 48 k€ | « pas de budget » | Série B 22 M€ | ⚖️ **FALSIFIÉE** | 92 % | Rouvrir · 1,25 crédit |
| **DataNimbus** 60 k€ | « choisi un concurrent » | Série B 22 M€ | 🛑 **INTACTE / renforce** | 90 % | Laisser dormir · 0 |
| **Postbox** 32 k€ | « Other » | Série B 22 M€ | 🤔 **ABSTENTION** | 95 % | Demander au rep · 0 |

> Compteur de retenue : **3 jugés · 1 rouvert · 2 laissés dormir · 1,25 crédit · 0 token pour
> le tri déterministe** (jugement LLM : 743 tokens out ≈ 0,01 $).

C'est **le moment-wow du pitch, prouvé**. Reproduire : `python3 tribunal.py`. Sortie complète
archivée : `proof-triptyque.txt`.

---

## 4. Le trio, testé au retrait (le critère éliminatoire du brief)

| On retire… | Ce qu'il reste | Verdict |
|---|---|---|
| **Sillage** | Nurture calendaire à l'aveugle (le statu quo qu'on attaque) | **Mort** |
| **Claude** | Des alertes Crunchbase brutes, sans polarité → du bruit dans Slack | **Mort** |
| **FullEnrich** | Un dossier de réouverture parfait… envoyé à un fantôme (contact parti) | **Boiterie grave** |

Aucun concurrent ne couvre la chaîne **détection → verdict → contact → brouillon** : UserGems
détecte mais ne juge pas l'objection ; Clay enrichit mais ne raisonne pas ; Gainsight voit
l'usage, pas le monde.

---

## 5. Le plan de construction 48h (briques BRICKS + le neuf)

**~70 % de la plomberie existe déjà** dans `bricks-v2`. Le chemin critique restant est du
**prompt engineering structuré**, pas de l'infrastructure.

| Composant | Statut | Brique |
|---|---|---|
| Tri déterministe + typage objection | ✅ **fait** (prouvé §3) | `tribunal.py` (neuf, 0 token) |
| Jugement de polarité (le procès) | ✅ **fait** (prouvé §3) | `tribunal.py` + Claude sous JSON |
| Gate VOI (dépenser un crédit ?) | ✅ existe | `score_v2.py` (VOI) + `tribunal.voi_gate` |
| Scoring signal-natif / bandes | ✅ existe | `score_v2.py` |
| Fenêtres [pess, attendu, opt] (Demi-Vie) | ✅ existe (intervalles) | `score_v2.py` |
| Kill-rule / knapsack (Morgue) | ✅ existe | `verdict.py` |
| Surveillance par objection | ⚙️ à câbler | `sillage_adapter.py` (mock prouvé, REST prêt) |
| Enrichissement conditionnel | ⚙️ à câbler | `fullenrich_adapter.py` |
| Contact → domaine | ✅ existe | `domain_resolver.py` |
| Dossier de réouverture (brouillon) | ✅ existe | `messaging_factory.py` (ressources fermées, 0 hallucination) |
| Writeback CRM | ✅ existe | `crm_adapter.py` (par domaine, idempotent) |

**Séquence 48h :**
1. **H+0** — pousser **10-15 comptes réels** dans Sillage (le poll a 48h pour ramener ≥ 1
   signal live — condition jury n°1). Peupler 185 comptes en **mock horodaté** via
   `sillage_adapter`, **affiché comme mock à l'écran**.
2. **J1 matin** — brancher `tribunal.py` sur les fixtures closed-lost (raisons **sales** et
   représentatives — condition jury n°2). Pré-calculer et **cacher** les verdicts des 3 deals
   du script (condition jury n°3).
3. **J1 après-midi** — câbler le gate VOI → `fullenrich_adapter` (pré-chauffé la veille via la
   dédup 3 mois pour éviter 90 s de silence en live) → `messaging_factory` (brouillon) →
   `crm_adapter` (writeback).
4. **J2 matin** — la couche Demi-Vie (tickets à péremption) + la branche Revanche (2 domaines
   sur 3-5 deals seulement — le quota Sillage est la ressource rare).
5. **J2 après-midi** — répétition de la démo + le **4ᵉ deal jugé à froid** en live.

---

## 6. La démo 3 minutes (script)

1. **0:00 — Le cadre.** « Voici 200 deals que vous avez perdus. Vous n'y toucherez plus
   jamais. Regardez. » (Compteur : 200 surveillés.)
2. **0:20 — Le triptyque (le wow).** Même levée de 22 M€, trois deals :
   - Deal A « pas de budget » → **FALSIFIÉE** → dossier + successeur trouvé (1,25 crédit).
   - Deal B « choisi un concurrent » → **INTACTE** → *on ne rouvre pas*.
   - Deal C « Other » → **ABSTENTION** → *question au rep*.
   « Même événement du monde. Trois verdicts. Aucune table de règles ne fait ça. »
3. **1:30 — La destruction.** Un ticket dont la fenêtre a expiré est **supprimé en direct** :
   « la retenue est une feature, pas un bug. »
4. **2:00 — Le 4ᵉ deal, à froid.** On demande à un juré une raison de perte + un événement.
   Verdict rendu en live. (Preuve que ce n'est pas du théâtre.)
5. **2:30 — Le compteur de retenue.** *200 surveillés · 5 rouverts · 195 laissés dormir ·
   ~15 crédits · 0 token pour le tri.* « Le seul système de la salle qui sait ne PAS envoyer. »

---

## 7. Le pitch

- **Thèse (1 phrase).** *« Chaque raison de perte est une hypothèse datée sur le monde ; APPEL
  la re-teste contre le monde réel, et ne rouvre que lorsqu'un événement l'a prouvée morte. »*
- **One-liner.** *La cour d'appel du closed-lost — le seul « appel » qu'un rep ait envie de
  passer.*
- **Réponses préemptives (dire avant qu'on demande) :**
  - *« C'est UserGems ? »* → Non. Eux trackent les **contacts** des closed-lost ; nous
    raisonnons sur **l'objection**. Le contact est notre étape 5, pas notre produit.
  - *« Et si les raisons de perte sont sales ? »* → 40-60 % le sont. C'est pour ça que
    l'**abstention** existe — et son taux est une métrique de **fierté** (on ne juge que ce
    qui a été plaidé). Si l'abstention explose, on est aussi un **audit d'hygiène CRM**.
  - *« Sillage sert vraiment ? »* → Retirez-le : il reste du nurture calendaire. Au moins un
    signal est poussé **live** pendant le hackathon.
  - *« Vous revendiquez du revenu ? »* → Non. On livre *objection falsifiée + preuve + contact
    + brouillon*. Une réouverture n'est pas un deal gagné.

---

## 8. Scorecard

| Critère (brief) | APPEL | Note |
|---|---|:---:|
| Exploite le trio, chacun **indispensable** | Testé au retrait, chacun mortel/estropiant | **9/10** |
| **Claude** met en valeur (hackathon Anthropic) | Polarité raison × événement, impossible en règles | **9/10** |
| **Démontrable** en 48h (live + mock avoué) | 70 % des briques existent ; cœur prouvé §3 | **8,5/10** |
| **Fait bouger l'aiguille** (équipes de vente) | Rouvre l'actif dormant n°1 du CRM, sans cramer | **8/10** |
| **Effet-WOW** jury | Triptyque + destruction live + compteur de retenue | **9/10** |
| **Unicité** (récit inoccupé) | Personne ne raisonne sur la raison de perte × événement | **9/10** |
| **Honnêteté / anti-slop** | Métrique bornée, abstention en fierté, limites assumées | **9/10** |

---

## 9. Les 3 conditions non-négociables du jury (à respecter sous peine de perdre)

1. **Au moins un signal Sillage réellement live** (comptes réels poussés à H+0) — sinon le
   Juge A requalifie le trio en « duo + mock ».
2. **Le triptyque sur des raisons de perte SALES** (pas 3 cas triés), taux d'abstention
   **affiché comme métrique de fierté** — sinon le Juge B plaide *garbage in, verdict out* et
   gagne.
3. **Verdicts du script pré-cachés + un 4ᵉ deal jugé à froid** — sinon le Juge C regarde
   Claude improviser sur le moment le plus cher de la démo.

---

## 10. Les limites assumées (la jurisprudence appliquée à soi-même)

- **Garbage in.** On ne juge que ce qui a été plaidé. Raisons vides → abstention. Assumé, et
  transformé en feature.
- **Couverture partielle.** On ne rouvre qu'une fraction du cimetière — mais rater n'a **aucun
  coût** (le deal était déjà mort). C'est ce qui rend ce terrain supérieur au radar de churn.
- **« 20-30 % de contacts partis »** = estimation dérivée du turnover, **jamais** présentée
  comme un fait.
- **Une réouverture n'est pas un deal gagné.** La métrique s'arrête au dossier livré.
- **Le mock est avoué à l'écran.** Le mock découvert tue ; le mock assumé survit aux questions.

---

## 11. Annexe — traçabilité de l'exploration

- **Méthode.** Double-diamant type EuroGuide, exécuté par des sous-agents **Fable 5 réels via
  l'API** : Diamant 1 = 6 explorateurs → synthèse → critique adversariale ; Diamant 2 = 6
  architectes → double matrice → jury à 3 têtes. Convergence par élimination brutale, anti-biais
  explicite (la thèse BRICKS d'origine a été rétrogradée puis le « gagnant confortable » C2 a
  été renversé par la critique).
- **Coût réel.** Diamant 1 ≈ 1,06 $ · Diamant 2 ≈ 1,36 $ · preuve triptyque ≈ 0,01 $ →
  **~2,43 $** sur les 100 $ de crédits.
- **Robustesse technique.** Le mur de connexion Mac→Anthropic (« Remote end closed ») a été
  contourné par **streaming curl** (`fable_api.py`) — les tokens circulent en continu, la
  connexion ne se coupe plus.
- **Fichiers.** `tribunal.py` (cœur + démo) · `fable_api.py` (appel robuste) ·
  `proof-triptyque.txt` (preuve) · `exploration/` (les 4 sorties brutes des diamants).
