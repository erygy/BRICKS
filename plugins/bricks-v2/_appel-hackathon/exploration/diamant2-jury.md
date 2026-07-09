# DÉLIBÉRÉ DU JURY — TROIS TÊTES, TROIS COUPERETS

---

## ⚖️ JUGE A — L'ORGANISATEUR (« montrez-moi le trio, pas trois démos côte à côte »)

**Mon test est mécanique : je retire un outil, je regarde si le système meurt ou boite.**

| | Retrait Sillage | Retrait Claude | Retrait FullEnrich | Note |
|---|---|---|---|:---:|
| **S1 Tribunal** | Mort (retour au nurture calendaire) | Mort (la polarité raison×événement est LE produit) | Boiterie grave (dossier envoyé à un fantôme) | **8,5** |
| **S2 Demi-Vie** | Boiterie (les fenêtres peuvent s'appuyer sur des dates CRM) | Boiterie (des priors d'intervalle, ça se code en dur) | Quasi-indolore | **5** |
| **S6 Revanche** | Mort (double surveillance prospect+concurrent = usage Sillage inédit) | Boiterie (la fenêtre de renouvellement, c'est de l'arithmétique) | Boiterie | **7** |

**S1 gagne mon barème, et l'argument des 20 secondes est réel** : *même levée, trois verdicts opposés selon la raison de perte* — c'est la démonstration la plus propre que j'aie vue de « Claude fait quelque chose qu'une table de règles ne peut pas faire ». Dans un hackathon Anthropic, c'est un tir dans le mille.

**Ma faille sur S1, et elle est structurelle** : votre point de fierté — « zéro pari de fraîcheur, les falsificateurs sont des événements déjà survenus » — est en tension directe avec la nature de Sillage, qui est un moteur de **surveillance prospective** (push comptes → poll signaux *à venir*). Si vos falsificateurs sont tous historiques, alors dans la démo, Sillage est un **mock déguisé en outil** et je vous le ferai avouer sur scène. La parade existe mais elle est exigeante : pousser un sous-ensemble de comptes **réels** en début de hackathon, montrer au moins un signal Sillage **live** arrivé pendant les 48h, et assumer le reste en replay daté. Sans ça, votre « trio indispensable » n'est indispensable que sur slide. Deuxième réserve, mineure : FullEnrich à 1,25 crédit par réouverture, c'est une garniture, pas un pilier — le VOI qui *refuse* d'enrichir est plus démonstratif que l'enrichissement lui-même. Mettez le refus à l'écran.

**S2 seul viole mon critère éliminatoire** (Sillage optionnel). **S6 a le plus bel usage Sillage de la salle** (deux domaines par deal) mais Claude y est sous-employé.

---

## 🧾 JUGE B — LE VÉTÉRAN REVOPS (« j'ai déjà 47 alertes par jour, merci »)

**Ce que je paie vs ce que j'admire poliment :**

- **S2 Demi-Vie : 4/10.** Un ticket qui expire, c'est une jolie UX de la retenue. Je ne paie pas pour de l'ordonnancement, je paie pour du jugement. En couche, oui ; en produit, non.
- **S6 Revanche : 7/10.** Là, vous touchez un nerf. La fenêtre de renouvellement du concurrent, mes meilleurs AE la calculent **à la main dans un Google Sheet** — c'est le signe le plus sûr qu'une douleur est réelle. Mais 20-30% de couverture, c'est une feature, pas une ligne budgétaire.
- **S1 Tribunal : 7,5/10** — la note la plus haute que je donne, et voici pourquoi elle n'est pas plus haute.

Le cimetière closed-lost est le plus gros actif dormant de mon CRM, vous avez raison. Personne ne re-teste les objections, vous avez raison. Le **refus de rouvrir** est votre vrai différenciateur — la dernière chose dont j'ai besoin, c'est d'un système qui crame mes comptes une deuxième fois, et « 195 laissés dormir avec justification » est la première phrase de pitch qui me parle depuis longtemps.

**Mon objection qui tue, et vous la connaissez déjà à moitié** : *garbage in, verdict out*. Dans mon vrai CRM, 40 à 60% des raisons de perte sont vides, « Other », ou « no decision » recopié par lassitude. Votre tribunal ne juge que ce qui a été plaidé. Vous avez l'abstention comme parade — bien — mais si votre taux d'abstention réel est de 60%, votre produit est un **audit de l'hygiène de mes raisons de perte**, pas une machine à ressusciter des deals. C'est peut-être un produit aussi, mais ce n'est pas celui que vous pitchez. Exigence : montrez-moi le triptyque sur des raisons de perte **sales et représentatives**, pas trois cas choisis — et affichez le taux d'abstention comme une métrique de fierté, pas comme un aveu. Deuxième pique : votre « 20-30% de contacts partis » présenté en estimation, c'est honnête ; ne le laissez pas glisser en fait pendant le pitch, je le relèverai.

---

## 🔧 JUGE C — L'INGÉNIEUR (« qui code ça d'ici dimanche 14h ? »)

- **S1 Tribunal : 8/10.** C'est la seule des trois où 70% de la plomberie existe déjà (score_v2, VOI, messaging_factory, adapters, writeback) et où le chemin critique restant est **du prompt engineering structuré** (typage d'hypothèse + polarité + procureur/défense), pas de l'infrastructure. Le déterminisme du tri (0 token, 0,4s/303 comptes) est un filet de sécurité de démo inestimable. **Mes trois risques, par ordre de mortalité :**
  1. **Claude live sur scène** = non-déterminisme sur le moment le plus critique (le triptyque). Parade obligatoire : verdicts pré-calculés et cachés pour les 3 deals du script, **plus** un quatrième deal jugé en live pour prouver que ce n'est pas du théâtre. Les deux, pas l'un.
  2. **Quota Sillage** : pousser 200 comptes sur un quota d'essai est un suicide. Architecture imposée : 10-15 comptes réels poussés à H+0 du hackathon (le poll a 48h pour ramener quelque chose de vrai), 185 en mock horodaté via sillage_adapter — dit **explicitement** à l'écran. Le mock avoué survit aux questions ; le mock découvert tue.
  3. **FullEnrich async 30-90s** en live = 90 secondes de silence sur scène. Pré-chauffer via la dédup 3 mois la veille, ou couper sur le log pendant l'attente.
- **S2 Demi-Vie : 9/10 en faisabilité** — un ticket qui expire, c'est une horloge et un `DELETE`. Mais on ne gagne pas un hackathon avec un cron job. Faisable ≠ suffisant.
- **S6 Revanche : 6,5/10.** L'arithmétique de fenêtre est sûre à 100%, mais **deux domaines surveillés par deal double la consommation du quota Sillage** — le concept le plus gourmand précisément sur la ressource la plus rare. En branche à 3-5 deals, oui. En système, non.

**Risque de démo résiduel sur S1** : le moment où un juge dit « faites-le tourner sur *ce* CSV ». Prévoyez ce cas — c'est là que l'abstention massive devient votre alliée si vous l'avez théâtralisée, votre tombeau sinon.

---

# 🏛️ VERDICT CONSOLIDÉ

**L'idée gagnante : S1 — LE TRIBUNAL DE FALSIFICATION**, assemblé tel que proposé (S2 en horloge, S3 en salle des machines, S6 en branche-vedette, S4 en coda). Le jury est unanime sur le classement, pas sur l'indulgence.

**Nom de produit : APPEL** — la cour d'appel du closed-lost, et le seul appel qu'un rep ait envie de passer.

**Phrase-thèse :** *« Chaque raison de perte est une hypothèse datée sur le monde ; APPEL surveille le monde, et quand le monde tue l'objection, il livre le certificat de décès — preuve datée, contact vérifié vivant, brouillon prêt, prix affiché. Quand le monde ne la tue pas, il refuse de rouvrir. »*

**Douleur** : le cimetière closed-lost (C3, sév. 8) traversé par le déluge de signaux non fusionnés (C4, sév. 9) — l'actif le plus riche et le moins travaillé de tout CRM.
**Mécanisme trio, chacun mortel au retrait** : **Sillage** apporte l'événement du monde réel (levée, changement de direction, migration de stack — et pour la branche Revanche, la détresse du concurrent) ; **Claude** rend le seul jugement qu'aucune règle ne rend — la polarité *raison de perte × événement*, avec abstention ; **FullEnrich** garantit, au prix minimal dicté par le VOI, que le certificat de décès n'est pas adressé à un fantôme.

**Pourquoi elle gagne** : parce qu'elle est la seule entrée de la salle dont le climax est un **refus** — 195 deals laissés dormir, un ticket détruit en live, ~15 crédits loggés — dans un hackathon où tous les autres démontreront des systèmes qui envoient plus. Et parce que son moment décisif (même levée, trois verdicts) est la publicité la plus pure possible pour le raisonnement de Claude, devant l'organisateur qui compte.

**Trois conditions non négociables, sous peine de perdre ce qui est gagné sur le papier :**
1. **Au moins un signal Sillage réellement live** (comptes réels poussés à H+0) — sinon le Juge A requalifie le trio en duo + mock.
2. **Le triptyque sur des raisons de perte sales**, taux d'abstention affiché en métrique de fierté — sinon le Juge B plaide *garbage in, verdict out* et gagne.
3. **Verdicts du script pré-cachés + un quatrième deal jugé à froid** — sinon le Juge C regarde Claude improviser sur le moment le plus cher de la démo.

Le tribunal est la bonne idée. Qu'il commence par s'appliquer sa propre jurisprudence : chaque affirmation du pitch doit être un fait démontré, une estimation étiquetée, ou une abstention.