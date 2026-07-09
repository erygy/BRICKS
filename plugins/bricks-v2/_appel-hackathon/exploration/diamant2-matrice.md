# DOUBLE MATRICE PROBLÈMES × SOLUTIONS — SYNTHÉTISEUR-STRATÈGE

*Règle appliquée : les fits sont notés sur ce que le concept résout **en standalone** (pas une fois greffé au cœur — sinon tout fusionne et la matrice ne discrimine plus). Anti-biais : la réutilisation de BRICKS ne donne aucun point ; seuls comptent la force du concept, la nécessité du trio, et ce qu'un VP Sales en fait lundi.*

---

## 1. LIGNES — Douleurs prioritaires (Diamant 1, sévérités conservées)

| ID | Douleur | Sévérité |
|---|---|:---:|
| **C3** | Cimetière closed-lost — l'objection datée jamais re-testée *(problème retenu)* | 8 |
| **C4** | Fusion N signaux → 1 décision par compte (déluge, latence, comptes cramés) | 9 |
| **C1** | Le deal vivant qui meurt en silence | 9 |
| **C2** | Le désert post-signature (churn/expansion) | 9 |
| **C5** | Le pari de segment payé plein tarif | 9 |
| **C6** | Crédits brûlés avant toute décision | 7 |
| **C7** | Message signal-aware mais argument-free | 7 |
| **C8** | CRM fiction vs réalité extérieure | 7 |

## 2. COLONNES — 7 concepts dédoublonnés (18 propositions → 7)

| ID | Concept fusionné | Sources fusionnées |
|---|---|---|
| **S1** | **LE TRIBUNAL DE FALSIFICATION** — raison sale → hypothèse typée → surveillance Sillage compilée par objection → verdict FALSIFIÉE / INTACTE / ABSTENTION (procureur+défense, anti-signaux) → VOI contact → dossier de réouverture → writeback. Démo-triptyque : *même levée, deux verdicts opposés, plus une abstention.* | LAZARUS (A1, A5), REVENANT (A2), LAZARE (A3, A4), SECONDE INSTANCE (A6) |
| **S2** | **DEMI-VIE / TICKET À PÉREMPTION** — chaque falsification porte une fenêtre [pess, attendu, opt] ; max 3 tickets triés par temps restant ; ticket expiré détruit en live. | DEMI-VIE (A2), DEMI-VIE actuaire (A6) |
| **S3** | **LA MORGUE GÉRÉE** — le cimetière comme portefeuille : verdict de viabilité par cohorte AVANT dépense (verdict.py, kill-rule), knapsack de crédits, file hebdo RESSUSCITER/ATTENDRE/ENTERRER. | MORGUE VIVANTE (A1), MORGUE A UN PRIX (A3), COLD CASE (A5) |
| **S4** | **COMITÉ FANTÔME / LA BONNE PORTE** — à la réouverture, search 0,25 cartographie le comité actuel, Claude choisit la porte d'entrée. | COMITÉ FANTÔME (A2), LA RELÈVE (A3), SECONDE MORT (A4) |
| **S5** | **OVERRULED** — tracker le BLOQUEUR (l'inverse de UserGems) : le véto orphelin (il part) ou cassé (son chef change). | OVERRULED (A6) |
| **S6** | **REVANCHE** — lost-to-competitor : fenêtre de renouvellement adverse (perte + 10-14 mois) × détresse croisée sur DEUX domaines (prospect + concurrent). | REVANCHE (A4) |
| **S7** | **SECOND MATCH** — le champion perdant qui rejoue dans sa nouvelle boîte. | SECOND MATCH (A5) |

## 3. LA MATRICE (fit 0-3)

| Douleur (sév) | S1 Tribunal | S2 Demi-Vie | S3 Morgue | S4 Comité | S5 Overruled | S6 Revanche | S7 2ⁿᵈ Match |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **C3** Cimetière (8) | **3** | 2 | 2 | 1 | 2 | 2 | 1 |
| **C4** Fusion→décision (9) | 2 | 2 | **3** | 0 | 1 | 1 | 0 |
| **C1** Deal silencieux (9) | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| **C2** Post-signature (9) | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| **C5** Pari de segment (9) | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| **C6** Crédits brûlés (7) | 2 | 2 | **3** | 2 | 2 | 1 | 1 |
| **C7** Argument-free (7) | 2 | 1 | 0 | 1 | 1 | 2 | 1 |
| **C8** CRM fiction (7) | 2 | 1 | 2 | 2 | 1 | 1 | 0 |
| **Σ fit×sévérité** | **84** | 62 | 96 | 52 | 53 | 53 | 31 |

## 4. SCORES COMPOSITES

`Composite = Σ(fit×sév) × unicité/10 × démo48h/10 × wow/10 × aiguille/10`

| Concept | Σ pondéré | Unicité trio | Démo 48h | Wow | Aiguille | **COMPOSITE** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **S1 Tribunal** | 84 | 9 | 9 | 9 | 8 | **49,0** |
| **S2 Demi-Vie** | 62 | 7 | 8 | 8 | 7 | **19,4** |
| **S6 Revanche** | 53 | 8 | 8 | 8 | 7 | **19,0** |
| S5 Overruled | 53 | 8 | 7 | 8 | 6 | 14,3 |
| S3 Morgue gérée | 96 | 7 | 7 | 5 | 6 | 14,1 |
| S4 Comité fantôme | 52 | 4 | 9 | 7 | 7 | 9,2 |
| S7 Second Match | 31 | 3 | 8 | 5 | 6 | 2,2 |

**Justifications des notes non évidentes :**
- **S1 Unicité 9, pas 10** : la détection brute « levée sur closed-lost » existe dans Clay ; c'est le *raisonnement raison × événement × polarité* qui est inoccupé. On garde un point d'humilité.
- **S3 : Σ pondéré le plus haut (96) mais Wow 5 et Démo 7** — c'est le paradoxe instructif de la matrice : il couvre le plus de douleurs (y compris C5 !) mais « un verdict sans dossier derrière est un tableau, pas une démo » (A3 lui-même), et mesurer la densité de falsificateurs par cohorte consomme le quota Sillage — **exactement le péché qui a tué C5 au Diamant 1**. La grille multiplicative punit ça, à raison : un hackathon se gagne sur le produit du minimum, pas sur la somme.
- **S4 Unicité 4** : retirer Sillage ne le casse pas → **violation du critère éliminatoire du brief**. Territoire Clay.
- **S7 Unicité 3** : collision frontale avec la feature phare de UserGems — la leçon même du Critique sur C2.

---

## 5. TOP 3 ET VERDICT D'ASSEMBLAGE

### 🥇 S1 — LE TRIBUNAL DE FALSIFICATION (49,0 — plus de 2,5× le second)

Il gagne parce qu'il est le **seul concept complet** : les six architectes, partis d'angles opposés (composition, timing, gaspillage, radar, agent, contrarian), ont convergé sur la même colonne vertébrale à 6 étapes — et cette fois la convergence est réelle (mêmes étapes, mêmes rôles d'outils, mêmes limites assumées), pas une pseudo-triangulation. Ses quatre forces décisives :
1. **Claude est irremplaçable et le prouve en 20 secondes** : *même levée → « pas de budget » = FALSIFIÉE / « choisi le concurrent » = RENFORCÉE / note illisible = ABSTENTION*. Aucune table de règles ne survit à cette polarité contextuelle. Argument massue dans un hackathon Anthropic.
2. **Zéro pari de fraîcheur** : les falsificateurs sont des événements déjà survenus — la démo ne peut pas être trahie par un week-end calme.
3. **Le trio testé au retrait** : sans Sillage = nurture calendaire (le statu quo attaqué) ; sans Claude = alertes Crunchbase ; sans FullEnrich = un dossier parfait envoyé à un fantôme (20-30% de contacts partis à 8-18 mois — *à présenter comme estimation dérivée du turnover, pas comme fait*).
4. **Le refus est démontrable** : 195 deals laissés dormir avec justification, ~15 crédits dépensés et loggés. Dans une salle de systèmes qui envoient plus, le seul qui sait *ne pas envoyer*.

### 🥈 S2 — DEMI-VIE (19,4) → **absorbé comme couche d'ordonnancement de S1**

Il bat les recalés parce qu'il transforme le tribunal en produit vivant : une falsification sans fenêtre est une alerte de plus (la douleur C4 recréée). Le ticket qui expire — détruit en live sur scène — est le deuxième moment de retenue démontrable. Mais en standalone, il présuppose la falsification déjà faite : incomplet, donc couche, pas produit. Ses priors de fenêtre restent des heuristiques affichées en intervalles.

### 🥉 S6 — REVANCHE (19,0) → **absorbé comme branche premium de l'arbre d'objections**

Il bat S5 et S3 sur la démontrabilité (la fenêtre de renouvellement est de l'arithmétique sur données historiques = 100% sûre en démo) et sur un usage Sillage qu'aucun autre concept n'a : **deux domaines surveillés par deal** (prospect + concurrent). Mais il ne couvre que ~20-30% des pertes : le construire seul, c'est jeter le reste du cimetière. C'est la branche la plus spectaculaire du tribunal, pas un tribunal.

### Pourquoi les recalés perdent

| Concept | Sentence |
|---|---|
| **S5 Overruled** | Insight brillant (personne ne tracke les bloqueurs), mais couverture 30-40%, attribution probabiliste (risque de « diffamer un CTO innocent » sans abstention), et 80% de plomberie commune avec S1. → **Classe de signal-assassin du tribunal**, montrée si le temps le permet. |
| **S3 Morgue gérée** | Le meilleur Σ douleurs de la matrice — et la pire démo. Un dashboard d'allocation gagne un débat RevOps, pas un hackathon ; et sa mesure de densité par cohorte reproduit le péché de quota de C5. → **Étage 0 silencieux** : la kill-rule et le knapsack tournent en coulisse et rendent « zéro crédit gaspillé » *démontrable* au lieu de déclaré. |
| **S4 Comité fantôme** | Viole le critère éliminatoire (Sillage optionnel), récit occupé par Clay. → **Coda de 30 secondes** sur UN deal : « on ne rouvre pas par la porte qui s'est fermée » (~2,5 crédits), réponse préemptive à la question jury « pourquoi ça marcherait cette fois ? ». |
| **S7 Second Match** | La feature phare de UserGems, mot pour mot. Le construire, c'est offrir au jury la réplique qui a tué C2. → **Éliminé.** Une phrase de vision, zéro ligne de code. |

---

## 6. L'ENTRÉE GAGNANTE (assemblage final)

> **LE TRIBUNAL DE FALSIFICATION** — cœur S1, avec S2 (fenêtres qui expirent) en couche d'ordonnancement, S3 (kill-rule/knapsack) en salle des machines invisible, S6 (revanche concurrent) en branche-vedette de l'arbre, S4 en coda d'un seul deal. **Un seul pitch** : *« Chaque raison de perte est une hypothèse datée sur le monde. Nous surveillons le monde ; quand il tue l'objection, nous livrons le certificat de décès — preuve datée, bon vivant vérifié, brouillon, prix affiché — et quand il ne la tue pas, nous refusons de rouvrir. »*

**Démo 3 min (triptyque + destruction)** : Deal A rejugé (levée × « pas de budget », successeur trouvé pour 1,25 crédit) → Deal B appel rejeté (même levée, objection « concurrent » renforcée) → Deal C abstention (note illisible → question au rep) → un ticket expiré détruit en live → compteur final : *200 surveillés, 5 rouverts, 195 laissés dormir, ~15 crédits, 0 token pour le tri.*

**Métrique honnête, à dire avant qu'on la demande** : objections falsifiées + preuve datée + contact vérifié + brouillon — **pas** de revenu revendiqué. Raisons de perte réelles sales (mock assumé). Différence vs UserGems en une phrase : *eux trackent les contacts des closed-lost ; nous raisonnons sur l'objection.*