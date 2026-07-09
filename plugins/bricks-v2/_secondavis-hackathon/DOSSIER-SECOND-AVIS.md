# SECOND AVIS — Le diagnostic différentiel du silence client
### Dossier de l'idée gagnante · Hackathon IA-GTM (Anthropic × Sillage × FullEnrich)
*(nom de travail : « GhostAccount Detector » — nom à arbitrer, alternatives en §12)*

> **« Vu de l'intérieur, tous les silences clients se ressemblent. Vu de l'extérieur, ils
> divergent — et c'est la seule donnée que votre CSM n'a pas. »**

Idée issue d'une **exploration de masse** sur Fable 5 via l'API : 941 douleurs générées → 52
clusters → **308 concepts** → scoring de masse → 22 finalistes réfutés un à un → 14
survivants → verdict du stratège. Coût total ~13,5 $ sur 100. **Le cœur est prouvé
empiriquement** (§3), pas seulement conçu.

---

## 0. En une page

- **Douleur (de DIRIGEANT, pas d'AE).** À tout instant, **20-40 % d'un portefeuille client est
  silencieux** — usage en chute, plus de réponse. Vu de l'intérieur, impossible de distinguer
  le client *occupé* du client *qui part*. Résultat : le « just checking in » aveugle, envoyé
  trop tard, au mauvais contact. Le churn frappe le **NRR** — la métrique de board et de
  valorisation. C'est une douleur **permanente**, pas un événement rare.
- **Idée.** SECOND AVIS lit le silence *interne* (chute d'usage) et va chercher, pour chaque
  compte silencieux, un **dossier de faits externes datés** (Sillage). Claude rend un
  **diagnostic différentiel** — silence **BÉNIN / TOXIQUE / INDÉTERMINÉ** — qui **cite ses
  preuves datées** et énonce **ce qui le falsifierait**. Puis, seulement pour le silence
  toxique, FullEnrich sort un **contact alternatif** et Claude écrit le message de reprise.
- **Chaque outil est mortel au retrait.** Sans Sillage : tous les silences redeviennent
  identiques → « just checking in » aveugle. Sans Claude : deux flux juxtaposés, la synthèse
  reste à faire à la main sur 80 comptes. Sans FullEnrich : diagnostic juste, mais impasse
  quand le champion muet est justement le point de silence.
- **Pourquoi ça gagne.** Le seul concept survivant où Claude fait de la **composition de deux
  flux hétérogènes en un jugement falsifiable** (pas du parsing, pas du lookup déguisé), avec
  une **démo à divergence visible** qui ne dépend d'aucun événement rare.
- **Honnêteté (dès la slide 1).** On ne prétend **pas prédire le churn** (qui exigerait une
  couverture parfaite). On prétend **expliquer le silence** : *« % de comptes silencieux où un
  fait externe daté change l'action recommandée »*. Positionnement : **« Gainsight lit
  l'intérieur ; SECOND AVIS est la moitié externe du health score. »**

---

## 1. Le problème — d'où il sort (exploration de masse)

L'exploration n'a pas cherché à flatter une idée : elle a généré **941 douleurs GTM** depuis
42 points de vue (14 rôles × situations), **sans jamais mentionner les 3 outils** (anti-biais
de circularité). Le regroupement en 52 clusters, classés par **magnitude de douleur brute
puis par exploitabilité**, fait remonter en tête, chez les dirigeants B2B et les commerciaux :

| Cluster (top exploitable) | Douleur | Fit-outils |
|---|---|---|
| Personnalisation impossible à l'échelle | 72,9 | 9 |
| Effondrement des canaux outbound | 72,9 | 8 |
| Signaux d'achat perdus / périmés / traités trop tard | 64,8 | 9 |
| Single-threading & perte du champion | 64,8 | 8 |
| **Churn & renewals découverts trop tard** | 64,8 | 5→ (durci) |

Preuve que l'exploration ne se ment pas : *« Vente fondateur non délégable »* est la douleur
n°1 en **magnitude** (81) — mais son fit-outils est 4, donc **rétrogradée** (les 3 outils ne
rendent pas un fondateur délégable). Sur les 308 concepts générés puis réfutés, le survivant
au score révisé le plus haut (**66/100**) attaque le silence client — reformulé pour éviter
le piège du « radar de churn » (voir §2).

*(Trace : `exploration/clusters-52.json`, `concepts-scored-308.json`,
`finalists-refuted-22.json`, `00-VERDICT-STRATEGE.md`.)*

---

## 2. La solution — SECOND AVIS (version durcie)

Le mécanisme, en 5 temps :

1. **Ingestion du silence interne** — export usage / tickets / meetings → score de silence par
   compte (format Gainsight / Amplitude standard). *Déterministe.*
2. **Sillage poll par compte silencieux** — dossier de faits externes datés : vague
   d'embauche, départ du champion, M&A, levée, mouvement de filiale, engagement concurrent.
3. **Diagnostic différentiel par Claude** — *pas une table d'heuristiques* : Claude confronte
   4 hypothèses (occupé / distrait / en partance / **indéterminé**) aux faits. Chaque verdict
   **cite ses preuves datées** et énonce **ce qui le falsifierait**. **Aucun score de confiance
   numérique** (objection du réfuteur corrigée).
4. **Silence toxique** → FullEnrich enrichit **2 contacts alternatifs** (le champion EST
   souvent le point de silence) + message de rupture de pattern qui référence le **fait
   externe**, jamais le silence.
5. **Bénin / indéterminé** → mise en veille avec **date de re-poll et signal à surveiller
   explicites** (montré en démo — pas de promesse J+14 invérifiable).

**Ce qui rend la version « durcie » solide** (le réfuteur avait visé la taxonomie causale
figée + le score de confiance non calibré) : le diagnostic raisonne **sur des preuves citées**,
chaque verdict porte sa **condition de falsification**, l'**indéterminé** est un verdict à part
entière, et il n'y a **aucun score numérique** à défendre.

---

## 3. La preuve empirique — la divergence, tournée sur Fable 5

Le cœur (`diagnostic.py`) **tourne**. Cinq comptes au silence interne **strictement identique**
(même chute d'usage, mêmes QBR annulés — figés en dur, 0 token), cinq dossiers externes
différents → **cinq verdicts divergents**, chacun citant sa preuve datée et sa condition de
falsification :

| Compte | Fait externe (Sillage) | Verdict | Action |
|---|---|---|---|
| **Northwind** 90 k€ | vague d'embauche (34 postes) | 🟢 **BÉNIN** | nourrir (valeur asynchrone) |
| **Halcyon** 120 k€ | rachat + nouveau CFO | 🔴 **TOXIQUE** | dossier ROI au nouveau décideur · contact alt. |
| **Vantle** 75 k€ | champion parti chez un concurrent | 🔴 **TOXIQUE** | re-vente, second sponsor · contact alt. |
| **Orbix** 60 k€ | engagement public avec un concurrent | 🔴 **TOXIQUE** | escalade exécutive · contact alt. |
| **Calder** 45 k€ | aucun signal externe | 🟡 **INDÉTERMINÉ** | surveiller (signaux nommés) — *« l'absence de signal n'est pas rassurante »* |

> **MÊME silence interne → 1 bénin · 3 toxiques · 1 indéterminé. Silence expliqué : 4/5.**
> (jugement + rédaction : ~2 950 tokens out ≈ 0,05 $.)

Et **deux emails opposés générés depuis le même silence interne** (extraits réels) :
- *Bénin — Northwind* : « **34 postes ouverts — bravo (et une idée)** » → propose des templates
  d'onboarding pour les nouveaux arrivants. Ton léger, utile. Ne mentionne jamais le silence.
- *Toxique — Halcyon* : « **Intégration Halcyon — un chiffre qui peut vous servir** » → propose
  un bilan de valeur chiffré, prêt pour la table du nouveau CFO. Adresse le risque de
  rationalisation fournisseurs.

Reproduire : `python3 diagnostic.py`. Sortie complète : `proof-diagnostic.txt`.

---

## 4. Le trio, testé au retrait

| On retire… | Ce qu'il reste | Verdict |
|---|---|---|
| **Sillage** | Tous les silences redeviennent identiques → « just checking in » aveugle (le problème de départ) | **Mort** |
| **Claude** | Deux flux (interne + externe) juxtaposés ; le CSM refait la synthèse à la main sur 80 comptes | **Mort** |
| **FullEnrich** | Verdict toxique juste, mais le champion muet ne répond pas → impasse opérationnelle | **Mort** (non décoratif) |

Personne ne couvre la **jonction** : UserGems détecte le départ d'un champion, Gainsight /
ChurnZero lisent le silence interne — **aucun ne compose les deux en un diagnostic
différentiel falsifiable**.

---

## 5. Le plan de construction 48h (briques BRICKS + le neuf)

| Composant | Statut | Brique |
|---|---|---|
| Diagnostic différentiel (le procès) | ✅ **fait & prouvé** (§3) | `diagnostic.py` (neuf) |
| Deux messages opposés depuis le même silence | ✅ **fait & prouvé** (§3) | `diagnostic.py` + Claude |
| Score de silence interne (ingestion usage) | ⚙️ à câbler | format Gainsight/Amplitude → `score_v2` |
| Surveillance externe par compte | ⚙️ à câbler | `sillage_adapter.py` (mock prouvé, REST prêt) |
| Contact alternatif conditionnel | ⚙️ à câbler | `fullenrich_adapter.py` + `domain_resolver.py` |
| Message de reprise (ressources fermées) | ✅ existe | `messaging_factory.py` (0 hallucination) |
| Mise en veille + re-poll daté | ⚙️ léger | planificateur simple |
| Écriture CRM du diagnostic | ✅ existe | `crm_adapter.py` (par domaine) |

**Séquence 48h :** H+0 pousser **10-15 comptes réels** dans Sillage (≥ 1 signal live —
condition jury n°1) + peupler le reste en mock horodaté, **affiché comme mock**. J1 : brancher
`diagnostic.py` sur des métriques d'usage au **format réaliste** (annoncé : « en prod, c'est
VOTRE donnée »). Pré-cacher les verdicts des 5 comptes du script + garder **1 indéterminé**
(condition jury n°2). J2 : la boucle FullEnrich (pré-chauffée la veille) + writeback +
répétition avec un **6ᵉ compte jugé à froid** en live (condition jury n°3).

---

## 6. La démo 3 minutes

1. **0:00-0:30** — 5 comptes, dashboards internes **identiques** (même courbe d'usage en
   chute). « Lequel part ? Votre CSM ne peut pas le savoir. »
2. **0:30-1:30** — Poll Sillage **en live** sur les 5 domaines réels : les dossiers externes
   **divergent** sous les yeux du jury.
3. **1:30-2:30** — 5 verdicts différenciés dont **1 indéterminé assumé** (l'honnêteté comme
   feature). Côte à côte : le message « bénin » vs le message « toxique » — **deux emails
   opposés depuis le même silence interne**.
4. **2:30-3:00** — Contact alternatif enrichi (FullEnrich) en live sur un compte toxique.
   Punchline : **« Le health score interne, tout le monde l'a. La moitié externe, personne. »**

---

## 7. Le pitch

- **Thèse.** *« Vu de l'intérieur, tous les silences clients se ressemblent. Vu de l'extérieur,
  ils divergent — SECOND AVIS lit cette moitié externe et vous dit pourquoi un compte s'est
  tu, avec la preuve datée et le bon contact. »*
- **One-liner.** *Le second avis externe sur un compte devenu silencieux.*
- **Positionnement.** *« Gainsight score l'intérieur. Nous sommes la moitié externe du health
  score. »*
- **Réponses préemptives :**
  - *« C'est un radar de churn ? Et sa couverture ? »* → Non. On ne **prédit** pas le churn
    (ça exigerait de tout capter). On **explique** le silence qu'on regarde. Rater un compte ne
    casse rien ; on améliore l'action sur ceux qu'on traite.
  - *« C'est UserGems / Gainsight ? »* → Eux font une moitié chacun. **La jonction — diagnostic
    différentiel du silence — n'existe nulle part.**
  - *« Le diagnostic, ce sont des heuristiques déguisées ? »* → Non : chaque verdict **cite ses
    preuves datées** et sa **condition de falsification**. Pas de score magique. Aide au
    diagnostic, pas oracle.
  - *« Vos données internes sont simulées ? »* → Le schéma d'export est réaliste (Amplitude /
    Gainsight) ; **la partie live de la démo est la moitié externe** — précisément ce que
    Gainsight n'a pas.

---

## 8. Scorecard

| Critère (brief) | SECOND AVIS | Note |
|---|---|:---:|
| Trio indispensable (test de retrait) | Chacun mortel au retrait | **9/10** |
| Claude mis en valeur (hackathon Anthropic) | Diagnostic différentiel falsifiable (composition, pas parsing) | **9/10** |
| Démontrable en 48h | Cœur prouvé §3 ; démo à divergence visible sans événement rare | **8,5/10** |
| Fait bouger l'aiguille | Attaque le NRR — l'euro le plus lourd du B2B | **8,5/10** |
| Effet-WOW jury | 2 emails opposés depuis des données internes identiques + poll live | **9/10** |
| Unicité (récit inoccupé) | La jonction interne×externe n'existe nulle part | **8,5/10** |
| Honnêteté / anti-slop | « Silence expliqué », indéterminé assumé, pas de score bidon | **9/10** |

---

## 9. Pourquoi elle bat l'idée précédente (APPEL / réactivation deals perdus)

| Axe | APPEL (rejeté) | SECOND AVIS |
|---|---|---|
| **Douleur dirigeant** | Upside d'AE sur du pipe mort — problème d'équipe, pas de board | **NRR = valorisation. Le CEO saigne.** Retenir coûte 5× moins qu'acquérir |
| **Fréquence vécue** | 1-2 déclencheurs/trimestre (objection loggée × compte coté × contradiction) | **20-40 % du book silencieux en permanence** — douleur hebdomadaire, universelle |
| **Effet-WOW** | Un email avec citation, conditionnel à un match rare | **Deux emails opposés depuis des données internes identiques**, divergence en 30 s, poll live |
| **Dépendance fatale** | Le champ « motif de perte » du CRM (rempli au hasard) | Usage (exportable) + Sillage réel. **Zéro dépendance au texte CRM pourri** |

---

## 10. Portefeuille de secours (issus des survivants)

- **Second Domino** — attaquer les concurrents d'un compte qui vient de lever, pendant que
  tous les SDR spamment le lauréat. Meilleur WOW de repli. *Parade : démo sur un marché connu
  (fintech, dev tools) pour neutraliser le risque d'hallucination sur niche.*
- **Seat Debt Collector** — écart licences/effectif chiffré en euros d'upsell : le business
  case le plus lisible pour un jury. *Reframe : FullEnrich sert au multithreading (nouveau VP
  du département en croissance), pas au cold email.*

---

## 11. Les 3 risques majeurs & parades

1. **Sillage rend des dossiers vides en live** → 5 « indéterminé », démo plate. *Parade :
   pré-scouter 15-20 entreprises à signaux récents riches, en retenir 5 ; poll live sur
   domaines vérifiés ; garder volontairement 1 indéterminé (preuve d'honnêteté).*
2. **Le jury attaque « diagnostic = heuristiques habillées »** → *Parade : zéro score numérique ;
   chaque verdict cite ses preuves datées + sa condition de falsification ; « aide au
   diagnostic, pas oracle » ; métrique « silence expliqué » en slide 1.*
3. **Données internes simulées → « garbage in » / comparaison Gainsight** → *Parade : schéma
   d'export réaliste annoncé frontalement ; la partie live est la moitié externe ; « Gainsight
   score l'intérieur, nous sommes la moitié externe ».*

---

## 12. Nom & annexe

- **Nom retenu (à arbitrer) : SECOND AVIS.** Registre du diagnostic médical (le second avis
  externe sur un compte devenu silencieux), crédible côté dirigeant/CS, mémorable.
  Alternatives : **CONTRECHAMP** (le champ inverse — ce que la caméra interne ne voit pas),
  **L'AUTRE MOITIÉ** (la moitié externe du health score).
- **Méthode & coût.** Exploration de masse Fable 5 (streaming curl, robuste au mur de
  connexion Mac). 941 douleurs → 52 clusters → 308 concepts → 22 réfutés → 14 survivants.
  ~13,5 $ sur 100. Fichiers : `diagnostic.py`, `proof-diagnostic.txt`, `exploration/`.
- **Sécurité.** La clé API a été exposée en chat → à **rotationner** après le hackathon.
