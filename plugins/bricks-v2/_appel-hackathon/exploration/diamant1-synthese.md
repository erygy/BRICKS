# SYNTHÈSE — MATRICE DES DOULEURS GTM
*Consolidation des 6 lentilles. Règle appliquée : chaque score d'UNICITÉ répond à « un jury pourrait-il dire "Clay/UserGems/Clari fait déjà ça" ? ». Anti-biais : les douleurs proches de BRICKS ne reçoivent aucun bonus — et l'une d'elles est explicitement rétrogradée.*

---

## 1. LA MATRICE (8 clusters dédoublonnés)

| # | Cluster | Sources (lentilles) | Persona principal | Sévérité /10 | Fréquence /10 | Unicité des 3 outils /10 | Démo 48h /10 | Wow jury /10 | **TOTAL /50** |
|---|---------|--------------------|-------------------|:---:|:---:|:---:|:---:|:---:|:---:|
| **C2** | **Le désert post-signature** — churn découvert dans l'email de résiliation, champion parti chez le client, radar NRR inexistant | F#4, SG#6, Contrarian#4 | Founder / CRO | 9 | 7 | **9** | 8 | 8 | **41** |
| **C1** | **Le deal qui meurt en silence** — champion parti, concurrent entré, pipeline zombie, forecast fiction | F#2, F#6, GTM#3, Sales#D1/D5/D6, W#5.5, C#3 | Founder / VP Sales | 9 | 9 | 8 | 8 | 6 | **40** |
| **C4** | **La fusion N signaux → 1 décision par compte** — déluge d'alertes, latence 9 jours, comptes cramés par 4 séquences, signal orphelin de destinataire | GTM#1/#4, SG#1/#2/#3/#4 | RevOps / GTM eng. | 9 | 9 | 9 | 7 | 6 | **40** |
| **C3** | **Le cimetière des closed-lost** — la fenêtre de tir manquée, le nurture temporel au lieu d'événementiel | Sales#D7, W#5.7 | AE / Founder | 8 | 6 | 9 | 7 | 9 | **39** |
| **C6** | **Les crédits brûlés avant toute décision** — enrichissement en batch, listes mortes, coût du faux positif | GTM#2/#5, W#5.2, C#7 | RevOps | 7 | 8 | 8 | 9 | 5 | **37** |
| **C8** | **Le CRM fiction vs la réalité extérieure** — 30% de champs périmés, "reality diff" | GTM#3, C#5 | RevOps | 7 | 8 | 7 | 8 | 6 | **36** |
| **C5** | **Le pari de segment payé plein tarif** — 35k€ et un trimestre pour apprendre qu'un segment est mort | F#1, W#5.1/#5.3 | Founder | 9 | 5 | 8 | **5** | 7 | **34** |
| **C7** | **Le message signal-aware mais argument-free** — le signal cité comme accroche, jamais comme argument | Sales#D3, SG#5, C#1 | SDR | 7 | 9 | **5** | 9 | **4** | **34** |

### Notes de scoring (transparence)
- **C1 Wow = 6** : douleur la plus forte en fréquence×intensité, mais Clari/Gong/UserGems occupent le récit — le jury croira l'avoir déjà vu. Et c'est le cluster le plus proche de BRICKS : score tenu volontairement sévère.
- **C5 Démo = 5** : rétrogradé **malgré** sa proximité avec la thèse BRICKS originale. Mesurer la densité de signaux sur 3×100 domaines explose le quota d'essai Sillage, et un verdict de segment est invérifiable en 48h. Douleur réelle (9/10), problème indémontrable ce week-end. C'est la preuve la plus visible que cette matrice n'est pas un miroir de BRICKS.
- **C7 Unicité = 5** : n'importe quel LLM bien prompté fait 80% du travail ; c'est un **module** de tous les autres clusters, pas un projet. 80% des équipes du hackathon feront exactement ça.
- **C4** : score élevé mais c'est un **mécanisme**, pas un problème vendable seul — il devient la salle des machines du gagnant.

### Douleurs écartées (honnêteté brutale — à dire au jury)
| Douleur | Pourquoi hors périmètre |
|---|---|
| Attribution revenue (GTM#6, SG#7) | Les touchpoints marketing et l'outcome CRM sur 6 mois sont invisibles aux 3 outils. Le revendiquer = slop. |
| Effondrement du canal outbound (C#2) | Problème de commons/incitations. Les 3 outils, mal utilisés, l'**aggravent**. |
| Compétence en rendez-vous (C#6, F#3 partiel) | Territoire Gong ; zéro rôle pour Sillage et FullEnrich. Peut-être la plus grosse douleur du marché en absolu — mais hors du droit de jouer. |
| Diagnostic PMF (F#5) | Si le verdict est « c'est le produit », aucun outil n'aide. |

---

## 2. CLASSEMENT

1. **C2 — Le désert post-signature (41)**
2. **C1 — Le deal qui meurt en silence (40)**
3. **C4 — Fusion signaux → décision (40)** *(mécanisme transversal)*
4. **C3 — Le cimetière des closed-lost (39)**
5. C6 — Crédits brûlés (37) *(argument de pricing, renfort des autres)*
6. C8 — CRM fiction (36) *(sous-produit gratuit de C1+C2)*
7. C5 — Pari de segment (34)
8. C7 — Message argument-free (34) *(module, pas projet)*

**Observation structurante** : C1, C2 et C3 sont **la même douleur à trois moments du cycle de vie** — *un compte que vous connaissez déjà (deal vivant, client signé, deal perdu) mute à l'extérieur du CRM, et personne ne le voit*. Et C4 est le mécanisme qui les sert tous. Les 6 lentilles, parties de personas différents, convergent vers ce point sans se concerter : c'est le signal de convergence le plus fort de toute l'exploration.

---

## 3. LES 3 MEILLEURS « HOW MIGHT WE »

### HMW 1 (C2) — *Le radar du revenu acquis*
> **Comment pourrions-nous donner aux dirigeants B2B un radar organisationnel sur leur portefeuille client, qui voit le churn 60-90 jours avant l'email de résiliation — et qui transforme chaque départ de champion en pipeline neuf ?**

| Outil | Pilier |
|---|---|
| **Sillage** | La moitié de sa taxonomie est littéralement conçue pour ça et personne ne l'utilise ainsi : agents `customer`, `champion`, `competitor`, `job_update` + M&A + changement de direction, pointés sur la liste **fermée et stable** des domaines clients — usage parfait du push→poll asynchrone ET du quota limité. |
| **Claude** | Trie chaque événement en trois verdicts : *risque de churn* (plan de défense) / *opportunité d'expansion* (power-user promu, filiale détectée) / *nouveau logo* (le champion parti est le meilleur lead du monde, conversion 3-5× le cold). |
| **FullEnrich** | Double gâchette : identifier le **successeur** du champion dans le compte (email vérifié = 1 crédit) ET retrouver le **champion dans sa nouvelle boîte** (dont le domaine repart dans Sillage — boucle vertueuse). Mobile à 10 crédits seulement si le renouvellement en jeu le justifie. |

### HMW 2 (C1 + C4) — *La mutation → la décision en <24h*
> **Comment pourrions-nous transformer chaque mutation externe d'un compte du pipe (champion parti, concurrent entré, gel d'embauches) en UNE décision arbitrée — agir / attendre / escalader / fermer proprement — avec preuve datée, contact vérifié et brouillon, en moins de 24h au lieu de 9 jours ?**

| Outil | Pilier |
|---|---|
| **Sillage** | Multi-signal natif sur un même domaine (8 types d'agents) : la matière première de la composition, que les mono-signaux (UserGems, Bombora) n'ont pas. |
| **Claude** | Le seul maillon capable de **composer** : pondérer, dater, détecter les contradictions, fusionner 4 alertes en 1 verdict par compte avec 1 owner — et rendre la mort d'un deal *opposable* sans accuser le rep (résout l'incitation à cacher les zombies). |
| **FullEnrich** | Bras armé conditionnel, sollicité **après** le verdict uniquement (search 0,25 → email 1 → mobile 10, arbitré par la valeur du deal) ; la dédup 3 mois sert de suppression anti-cramage côté contacts. |

### HMW 3 (C3) — *Réveiller le cimetière*
> **Comment pourrions-nous surveiller les centaines de closed-lost dormants du CRM et rouvrir un deal au moment exact où un événement falsifie la raison de la perte (« pas de budget » × levée de 20M = objection morte) ?**

| Outil | Pilier |
|---|---|
| **Sillage** | Le cas d'usage rêvé de l'asynchrone : push 200 closed-lost une fois, poll pour toujours. Levée, nouveau dirigeant, vague d'embauche, migration tech = autant de falsificateurs d'objections. |
| **Claude** | Le croisement que personne ne fait : *raison de perte historique × signal nouveau → l'objection tient-elle encore ?* Puis le message de ré-entrée qui référence l'historique sans être creepy. |
| **FullEnrich** | Indispensable : 8-18 mois après, 20-30% des contacts ont bougé — re-vérification à 1 crédit, nouveau décideur si besoin. |

---

## 4. LE VERDICT : LE PROBLÈME LE PLUS FORT

## → **« Les comptes que vous possédez déjà mutent à l'extérieur de votre CRM — et vous l'apprenez toujours trop tard. »**
### Fer de lance : **HMW 1 (le radar post-signature)**, avec HMW 2 et HMW 3 comme extensions du même moteur.

**Pourquoi c'est le plus douloureux :**
- **L'euro le plus lourd du B2B.** 1 point de NRR pèse plus que tout l'outbound du trimestre ; acquérir coûte 5-25× retenir ; un churn de compte-clé est *existentiel* (10/10) pour un founder concentré. Et la mécanique est implacable : ~20% de turnover annuel des champions = 1 compte sur 5 perd son sponsor **chaque année**, découvert via un auto-reply.
- **Le plus gros écart douleur/attention du marché.** Tout le stack GTM (et 90% du hackathon) regarde l'acquisition. Les health scores CS regardent l'usage produit — aveugles aux causes organisationnelles (rachat, nouveau CFO, concurrent qui rôde) qui expliquent 30-50% des churns.

**Pourquoi c'est le mieux exploitable par CES 3 outils (et pas d'autres) :**
1. **Chaque outil est irremplaçable.** Sans Sillage : pas de vérité extérieure. Sans Claude : du bruit dans Slack (le fossé signal→action documenté par la lentille RevOps). Sans FullEnrich : un signal orphelin de destinataire. UserGems détecte mais ne décide ni n'agit ; Gainsight voit l'usage, pas le monde ; aucun concurrent ne couvre la chaîne détection→verdict→contact→brouillon.
2. **Les contraintes techniques deviennent des atouts.** Liste fermée de domaines = quota Sillage respecté ; asynchrone push→poll = mode capteur naturel (la fenêtre se compte en jours) ; grille FullEnrich = fonction de coût que Claude optimise (logique VOI démontrée, pas racontée).
3. **Démontrable en 3 minutes** : « Ce client à 120k€ ARR : champion parti détecté vendredi, remplaçant venu de chez votre concurrent identifié pour 1 crédit, verdict *risque élevé + plan*, et le champion re-signable dans sa nouvelle boîte — un churn évité ET un lead neuf, même signal. »

**Vérification anti-biais (explicite) :**
- Ce choix **n'est pas** la thèse BRICKS d'origine (le pari de segment, C5) — celle-ci est classée 7e/8, rétrogradée pour infaisabilité de démo malgré sa douleur 9/10. La matrice a mordu la main qui la nourrit.
- La convergence vers « les comptes connus qui mutent dehors » est apparue **dans les 6 lentilles indépendamment** (founder #2/#4, RevOps #3, sales #D1/#D7, signal-gap #4/#6, waste #5.5, contrarian #4). Si BRICKS n'existait pas, c'est ce qu'il faudrait construire ce week-end. Le fit BRICKS (VOI, verdict, deux sens du cycle) est ici une **conséquence heureuse**, pas la prémisse.
- **Limites à assumer devant le jury** (ça crédibilise tout le reste) : couverture de détection ~40-60% (les morts internes — politique, budget coupé en silence — restent invisibles) ; l'historique relationnel vit dans le CRM de l'utilisateur, à injecter ; et aucun outil ne résoudra la question organisationnelle « qui possède le renouvellement ? » — on rend le signal impossible à ignorer, pas l'organigramme intelligent.

**Risque principal & mitigation :** la fraîcheur des signaux sur la fenêtre de démo. → Peupler le portefeuille de démo avec des comptes de secteurs à haute vélocité d'événements (scale-ups financées), lancer les runs Sillage **avant** la présentation, et démontrer la couche décision en live sur les résultats du poll.