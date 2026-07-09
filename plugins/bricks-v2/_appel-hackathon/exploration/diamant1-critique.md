# CRITIQUE ADVERSARIALE — « LA MATRICE A MORDU UN DOIGT, PAS LA MAIN »

---

## 1. BIAIS DE CONFIRMATION : le sacrifice de C5 est un rituel, pas une preuve

**Le tour de passe-passe est élégant mais visible.** La matrice rétrograde C5 (la thèse BRICKS *originale*) et brandit ce sacrifice comme certificat d'impartialité. Puis elle couronne... « les comptes connus qui mutent dehors, un seul moteur, les trois moments du cycle de vie ». Relisez le brief BRICKS : *« un seul moteur, les deux sens du cycle de vie »*. **Le verdict final est le slogan actuel de BRICKS avec un mot changé.** On a sacrifié la thèse d'il y a six mois pour introniser la thèse d'aujourd'hui. C'est un anti-biais de façade.

**Preuves internes de biais, dans les chiffres mêmes :**

- **Le double standard C5/C2 est flagrant.** C5 est exécuté pour « verdict invérifiable en 48h ». Mais un churn évité à 60-90 jours est *exactement aussi invérifiable en 48h*. C2 garde pourtant Démo = 8. Même critère, deux traitements. Si on applique la règle de C5 à C2 honnêtement, C2 démontre une *détection* + un *plan*, jamais un *outcome* — Démo réel : 6.
- **L'unicité de C2 à 9 est indéfendable.** La note C1 dit « le jury croira l'avoir déjà vu (Clari/Gong) » et le pénalise. Or **la homepage entière de UserGems est littéralement le pitch C2** : champion parti chez un client = risque de churn + nouveau pipeline, y compris le « re-signer le champion dans sa nouvelle boîte » — qui est présenté ici comme le moment wow de la démo alors que c'est *la* feature phare de UserGems (et de Champify). L'affirmation « personne ne l'utilise ainsi » est factuellement fausse et sera démontée en 10 secondes par tout juré qui connaît le marché. Unicité réelle de C2 : **6, pas 9**. Ce seul ajustement fait passer C2 de 41 à 38 — derrière C1 et C3.
- **La grille elle-même est biaisée.** Un cinquième du score total est « Unicité des 3 outils » — c'est-à-dire *« à quel point le problème flatte notre stack »*. On a noté les douleurs à l'aune des outils, puis conclu que la douleur gagnante colle merveilleusement aux outils. Circularité structurelle.
- **La « convergence des 6 lentilles » est une pseudo-triangulation.** Les 6 lentilles sortent du même pipeline, avec BRICKS dans le contexte. Six sorties du même système qui convergent, ce n'est pas six témoins indépendants — c'est un même prior échantillonné six fois. Vendre ça comme « le signal de convergence le plus fort de l'exploration » est du slop méthodologique.
- **Chiffres non sourcés = munitions pour le jury.** « 30-50% des churns ont des causes organisationnelles », « conversion 3-5× », « latence 9 jours » : aucune source. Un juré RevOps demandera « d'où sort le 30-50% ? » et le château tremble.

---

## 2. ANGLES MANQUÉS

1. **Le single-threading — la CAUSE, pas le symptôme.** C1 et C2 sont les conséquences d'une seule maladie : le deal/compte tient sur UNE relation. La douleur amont — *« cartographier et multi-threader le comité d'achat AVANT que le champion parte »* — est absente de la matrice. Et c'est FullEnrich (search à 0,25 crédit = cartographie de comité quasi gratuite) + Claude (qui manque dans l'organigramme ?) en rôle principal. Trou réel.
2. **L'expansion enterrée sous le churn.** La détection de filiale, la promotion de power-user, le M&A : Sillage a une demi-taxonomie tournée vers le *whitespace d'expansion*, et la matrice la range en sous-clause de C2. Un radar d'expansion est une histoire plus heureuse, plus démontrable (l'opportunité existe *maintenant*, pas dans 90 jours) et moins occupée que le radar churn.
3. **Le non-usage des signaux passés comme actif de démo.** Personne n'a noté que C3 est le SEUL cluster où le signal déclencheur est *déjà arrivé* (une levée du mois dernier est un fait daté, interrogeable ce week-end). C2 et C1 parient sur des événements *futurs* pendant la fenêtre de démo — le doc l'admet en « risque principal ». C3 n'a pas ce risque. Cet avantage décisif n'apparaît nulle part dans le scoring.
4. **L'onboarding/time-to-value** comme cause n°1 de churn réel — invisible aux 3 outils, certes, mais son absence de la liste des « écartées » suggère qu'on n'a challengé que les douleurs confortables à écarter.

---

## 3. LE VÉTÉRAN REVOPS FACE À C2 : « J'ai déjà trois radars que personne ne regarde »

Ce qu'il dirait, mot pour mot :

- **« Mon problème n'est pas la détection, c'est la propriété. »** Le doc l'avoue lui-même en note de bas de page (« aucun outil ne résoudra qui possède le renouvellement ») puis fait comme si de rien n'était. Un radar de plus qui pousse des alertes dans une organisation où le renouvellement n'a pas d'owner, c'est du bruit premium. La douleur C2 est réelle ; elle est **organisationnelle avant d'être informationnelle**, et les 3 outils n'y touchent pas.
- **« 40-60% de couverture, vous êtes sérieux ? »** Un radar anti-churn qui rate un churn sur deux se fait désinstaller au premier churn manqué. La confiance dans un système de détection de risque est asymétrique : un faux négatif détruit ce que dix vrais positifs ont construit. Cette limite, « assumée pour crédibiliser », est en réalité **disqualifiante pour ce cas d'usage précis** — et tolérable pour d'autres (rater une réouverture closed-lost ne coûte rien : elle était déjà perdue).
- **« C'est le plus démontrable, pas le plus douloureux. »** Sur le portefeuille d'un founder cible du hackathon (30-80 clients), un départ de champion c'est quelques événements *par trimestre*. Douleur existentielle quand elle frappe, oui — mais fréquence vécue faible. La mitigation proposée (peupler la démo de scale-ups à haute vélocité) est l'aveu que **la démo sera mise en scène** parce que le phénomène est trop rare pour se produire naturellement en 48h.
- **« Et Claude fait quoi, exactement ? »** Dans HMW1, le rôle de Claude est un tri en trois buckets — un prompt, pas de l'orchestration. Pour un hackathon *organisé par Anthropic*, c'est le cluster où Claude est le plus remplaçable. Dans HMW3, Claude fait un raisonnement non-commodité (*raison de perte historique × signal nouveau → l'objection tient-elle encore ?*). Le jury Anthropic notera la différence.

---

## 4. SPÉCIFICITÉ : un problème, ou trois produits avec un slogan ?

Le verdict « fer de lance HMW1 + extensions HMW2 et HMW3 » est **du scope creep déguisé en vision**. En 48h, « le même moteur pour trois moments du cycle de vie » produit trois demi-démos. Le framing choisi (« les comptes mutent dehors ») est une *catégorie*, pas un problème — assez large pour englober UserGems, Gainsight, Clari et Champify à la fois, donc assez large pour qu'on vous colle chacune de ces étiquettes. Trop générique en haut, et en dessous, C2 seul est trop occupé.

Le point de spécificité maximale de toute la matrice est ailleurs, et il était sous vos yeux avec le **Wow = 9 le plus haut du tableau sensé** : *la falsification d'objection*. « Perdu pour "pas de budget" × levée de 20M€ = l'objection est morte, datée, prouvée. » Personne n'occupe ce récit-là. UserGems tracke les contacts des closed-lost, oui — mais **personne ne raisonne sur la raison de perte**. C'est étroit, nommable en une phrase, et le raisonnement est Claude-natif.

---

## 5. CLASSEMENT RÉVISÉ & RECOMMANDATION

| Rang | Problème | Verdict révisé |
|---|---|---|
| **1** | **C3 — Le cimetière des closed-lost** (*falsification d'objection*) | Seul cluster où : le signal déclencheur est déjà dans le passé (zéro risque de fraîcheur), le récit est inoccupé (personne ne croise raison de perte × événement), Claude fait un vrai raisonnement, FullEnrich est *indispensable* (20-30% de contacts périmés à 8-18 mois), la liste fermée respecte le quota Sillage, et l'échec ne coûte rien (le deal était déjà mort). Fréquence 6 assumée : pour un hackathon, la démontrabilité honnête bat la fréquence. |
| **2** | **C1+C4 — La mutation → décision <24h** | Douleur la plus fréquente, mécanisme C4 excellent — mais récit occupé (Clari/Gong) et le verdict « fermer proprement » est invérifiable en démo. À garder comme extension racontée, pas construite. |
| **3** | **C2 — Le désert post-signature** | Rétrogradé. Unicité réelle 6 (collision frontale UserGems, y compris sur le moment « wow » de la démo), outcome indémontrable en 48h (même règle que C5), problème d'ownership non adressable, couverture 40-60% disqualifiante pour un radar de risque, rôle de Claude le plus mince des trois. Douleur réelle ; mauvais terrain de bataille ce week-end. |

**RECOMMANDATION FINALE : attaquer C3 au diamant solution, reformulé ainsi :**

> **« Chaque raison de perte est une hypothèse datée sur le monde. Nous surveillons le monde, et le jour où un événement la falsifie, nous rouvrons le deal — avec la preuve, le bon contact re-vérifié, et le brouillon. »**

C'est falsifiable (ADN BRICKS *mérité*, pas plaqué), Claude y est le héros (croisement raison × signal, impossible en règles), Sillage y est en usage rêvé (push 200 domaines morts, poll), FullEnrich y est non-négociable (les contacts ont pourri), et la démo de 3 minutes se fait sur des événements *réels et déjà survenus*. Économiquement : le closed-lost est le plus gros actif dormant de tout CRM — CAC déjà payé, relation déjà tiède, coût marginal quasi nul.

**Honnêteté à conserver devant le jury** (sinon vous reproduisez le biais que je viens de casser) : les raisons de perte CRM sont sales dans la vraie vie (mock assumé) ; UserGems tracke *les contacts* des closed-lost — votre différence est le raisonnement sur *l'objection*, dites-le en une phrase avant qu'on vous le demande ; et une réouverture n'est pas un deal gagné — votre métrique de démo est « objection falsifiée + preuve datée + brouillon », rien de plus. C'est suffisant pour gagner.