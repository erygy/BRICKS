# DÉCISION FINALE — STRATÈGE

---

## 1) L'IDÉE GAGNANTE : **GhostAccount Detector** (version durcie)

### Phrase-thèse
> **« Vu de l'intérieur, tous les silences clients se ressemblent. Vu de l'extérieur, ils divergent — et c'est la seule donnée que votre CSM n'a pas. »**

### Douleur ciblée
Le **dirigeant B2B SaaS** vit sous la dictature du NRR : c'est la métrique de board, de valorisation, de survie. Et le churn se manifeste toujours pareil — **un compte qui devient silencieux** — sans que personne ne sache si ce silence est de l'occupation ou de la défection. Résultat : le « just checking in » aveugle, envoyé trop tard, au mauvais contact. À tout instant, 20-40 % d'un book of business est silencieux. C'est une douleur **permanente**, pas événementielle.

### Mécanisme en 5 temps (durci vs version originale)
1. **Ingestion du silence interne** : export usage/tickets/meetings → score de silence par compte (format Gainsight/Amplitude standard).
2. **Sillage poll par compte silencieux** : constitution d'un **dossier de faits externes datés** — vagues d'embauche, départ du champion, M&A, levée, mouvement de filiale, engagement concurrent.
3. **Diagnostic différentiel par Claude** — *pas une table d'heuristiques* : Claude confronte 4 hypothèses (occupé / distrait / en partance / **indéterminé**) aux faits du dossier. Chaque verdict **cite ses preuves datées** et énonce **ce qui le falsifierait** (« ce verdict tombe si le champion apparaît chez un concurrent »).
4. **Silence toxique** → FullEnrich enrichit **2 contacts alternatifs** (le champion EST souvent le point de silence) + message de rupture de pattern qui référence le fait externe, jamais le silence.
5. **Bénin / indéterminé** → mise en hold avec **date de re-poll et signal à surveiller explicite** — le bouton re-poll est montré en démo (pas de promesse J+14 invérifiable).

### Test de retrait
| Outil | Sans lui |
|---|---|
| **Sillage** | Tous les silences redeviennent identiques → retour au « just checking in » aveugle, le problème de départ. **Irremplaçable.** |
| **Claude** | Deux flux de données juxtaposés ; le CSM refait la synthèse à la main sur 80 comptes. Le diagnostic différentiel *est* le produit. |
| **FullEnrich** | Verdict toxique + champion silencieux = impasse opérationnelle. FullEnrich est le seul chemin vers l'action. Non décoratif (contrairement à Seat Debt). |

### Pourquoi Claude est le héros
C'est le seul concept survivant où Claude fait de la **composition de deux flux hétérogènes en un jugement falsifiable** — pas du parsing (Post-Mortem), pas du lookup déguisé (Second Domino), pas de l'auto-notation (Treasurer). Le raisonnement différentiel avec preuves citées et conditions de falsification est un usage LLM authentique et démontrable en live.

### Démo 3 minutes
1. **0:00-0:30** — 5 comptes, dashboards internes identiques : même courbe d'usage en chute. « Lequel part ? Votre CSM ne peut pas le savoir. »
2. **0:30-1:30** — Poll Sillage **en live** sur les 5 domaines réels : les dossiers externes divergent sous les yeux du jury.
3. **1:30-2:30** — 5 verdicts différenciés dont **1 indéterminé assumé** (l'honnêteté comme feature). Côte à côte : le message « bénin » vs le message « toxique » — **deux emails opposés générés depuis le même silence interne**.
4. **2:30-3:00** — Contact alternatif enrichi FullEnrich en live sur le compte toxique. Punchline : « Le health score interne, tout le monde l'a. La moitié externe, personne. »

### Unité de valeur
**Un diagnostic différentiel par compte silencieux** : hypothèse dominante, preuves externes datées et cliquables, condition de falsification, action, contact.

### Métrique honnête
**Taux de silence expliqué** : % de comptes silencieux où au moins un fait externe daté et sourcé **change l'action recommandée** vs la baseline (100 % de « just checking in » identiques). On ne prétend PAS prédire le churn — on prétend éliminer l'action aveugle. Métrique mesurable en démo, non fictive (contrairement au ROI du Treasurer).

### Pourquoi elle bat les autres survivants
- **Score révisé le plus élevé (66)** — et surtout : son point faible (taxonomie causale figée, confiance non calibrée) est le **seul défaut réparable par design** — on l'a réparé ci-dessus (raisonnement sur preuves + falsifiabilité + verdict indéterminé, suppression du score de confiance numérique).
- Les autres ont des défauts **structurels** : entonnoir qui s'effondre (Verbatim : 1-2 triggers/trimestre), dépendance à un CRM sale qui n'existe pas (Lazare, Post-Mortem), cœur invérifiable par construction (Subsidiary), survivorship bias (Window ICP), boucle qui note ses propres devoirs (Treasurer), UserGems reskinné (Verdict), Claude irremplaçable là où il hallucine (Second Domino), FullEnrich décoratif (Seat Debt).
- C'est le **seul** où les 3 outils passent le test de retrait ET où la démo montre la valeur en live sans dépendre d'un événement rare.

---

## 2) Pourquoi elle bat l'idée précédente (réactivation deals perdus / falsification d'objection)

| Axe | Réactivation deals perdus | GhostAccount |
|---|---|---|
| **Douleur dirigeant** | Upside opportuniste sur pipe mort — problème d'AE, pas de board. | Le churn frappe le **NRR**, métrique de valorisation. Perdre un client coûte 5× en acquérir un. C'est le CEO qui saigne, pas l'AE. |
| **Fréquence vécue** | Conditionnée à un triple filtre improbable : objection loggée × compte coté × contradiction frappante ≈ **1-2 triggers/trimestre**. | 20-40 % du book silencieux **en permanence**. Douleur hebdomadaire, universelle, sans prérequis CRM propre. |
| **Effet-WOW** | Un email avec citation — joli, mais conditionnel à un match rare qui peut ne pas arriver en live. | **Deux emails opposés générés depuis des données internes identiques**, divergence visible en 30 secondes, poll Sillage réel sous les yeux du jury. |
| **Dépendance fatale** | Le champ « motif de perte » du CRM — notoirement rempli au hasard. Toute la chaîne causale repose sur des données pourries. | Inputs = métriques d'usage (exportables, simulables crédiblement) + Sillage réel. Zéro dépendance au texte libre CRM. |

---

## 3) Portefeuille de secours

- **Second Domino** — Le meilleur WOW de repli : attaquer les concurrents du compte qui lève pendant que tous les SDR spamment le lauréat. Parade obligatoire : démo sur un marché connu (fintech, dev tools) pour neutraliser le risque d'hallucination sur niche.
- **Seat Debt Collector** — Le business case le plus lisible pour un jury (écart licences/effectif chiffré en euros d'upsell). Reframe nécessaire : FullEnrich sert au multithreading (nouveau VP du département en croissance), pas au cold email.

---

## 4) Les 3 plus gros risques et leurs parades

**R1 — Sillage rend des dossiers vides en live** → 5 verdicts « indéterminé », démo plate.
*Parade* : pré-scouter 15-20 entreprises réelles à signaux récents riches, en retenir 5 ; le poll reste live mais sur domaines vérifiés. Garder **volontairement** 1 indéterminé sur 5 : il devient la preuve d'honnêteté, pas un échec.

**R2 — Le jury attaque le point faible connu** (« diagnostic = heuristiques habillées, confiance non calibrée »).
*Parade* : supprimer tout score numérique de confiance ; chaque verdict cite ses preuves datées + sa condition de falsification ; positionner comme **aide au diagnostic, pas oracle** ; la métrique honnête (« silence expliqué », pas « churn prédit ») en slide 1, avant qu'on nous la demande.

**R3 — Les données internes sont simulées** → critique « garbage in » et comparaison Gainsight/Vitally.
*Parade* : schéma d'export réaliste (format Amplitude/Gainsight), annoncé frontalement : « en prod, c'est VOTRE donnée d'usage ». La partie live de la démo est la **moitié externe** — précisément ce que Gainsight n'a pas. Positionnement en une ligne : *« Gainsight score l'intérieur. Nous sommes la moitié externe du health score. »*

---

**Verdict final : GhostAccount Detector, version durcie. Douleur de dirigeant, fréquence permanente, trois outils irremplaçables, démo live à divergence visible, et une métrique qui ne ment pas.**