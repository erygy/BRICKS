# Test scientifique BRICKS → MemoVAL — protocole PRÉ-ENREGISTRÉ

Date : 2026-07-08. Objet : vérifier que BRICKS lance une campagne outbound de A à Z
(sourcing → firmographie → signaux → scoring → drafts) et mesurer sa PERTINENCE,
avant la présentation de demain. Seuils fixés AVANT le run complet.

## Cas de test
- Produit vendu (offre) : **MemoVAL**.
- ICP : PME FR indépendantes, CA 1,5–10 M€, dirigeant 58–68 ans, société >15 ans,
  secteurs à fort savoir tacite ; intention = transmission plausible sous 1–3 ans.
- Workspace : `memoval-outbound` (isolé, root scratchpad).

## Contraintes environnement (constatées, non négociables)
- ❌ Pas de `~/.bricks/env` → FullEnrich (emails vérifiés) et Bright Data (scraping) INDISPONIBLES.
- ❌ MCP fullenrich / brightdata non connectés → lane web-researcher indisponible.
- ✅ Lanes GRATUITES vivantes : API gouv recherche-entreprises (200), Google News RSS.
- Conséquence : on teste le **cœur gratuit** de BRICKS. Le `find` shippé (FullEnrich/BrightData)
  est remplacé par la découverte via l'API gouv ouverte (fidèle à la philosophie open-data
  de BRICKS, signalé comme substitution). L'obtention d'emails de contact est HORS PÉRIMÈTRE
  testable ici (documenté, pas compté comme échec du produit).

## Hypothèses & seuils (pré-enregistrés)
- **H1 Sourcing** : ≥ 50 PME candidates sourcées sur les filtres ICP structurels. [PASS/FAIL]
- **H2 Précision ICP** : sur un échantillon aléatoire de 20 comptes sourcés+enrichis,
  ≥ 60 % sont de vrais prospects MemoVAL (juge adversarial, rubrique explicite).
  < 40 % ⇒ sourcing = bruit. [seuil 60 %]
- **H3 Couverture firmo** : SIREN + effectif + ≥1 dirigeant résolus pour ≥ 80 % des lignes.
  (mesuré sur données gouv-sourcées ET sur résolution firmo.py par nom.)
- **H4 Précision signaux** : parmi les comptes portant un signal presse, ≥ 50 % sont
  de vrais positifs (l'article concerne bien l'entreprise ET touche transmission/
  retraite/cession/anniversaire). Le RAPPEL est inconnaissable (pas de vérité terrain) — dit honnêtement.
- **H5 Discrimination du ranking** : rank-accounts produit ≥ 3 tiers distincts et le
  tier supérieur ≤ 70 % des comptes (≠ l'échec « ranking plat » de hiring-test-b).
- **H6 Qualité drafts** : sur le top N comptes, moyenne ≥ 7/10 (rubrique adversariale :
  structure CPPC, < 100 mots, why_now personnalisé et SOURCÉ, zéro fait halluciné,
  zéro survente L121) ; ≥ 80 % des drafts sans aucun fait inventé.
- **Coût / latence** : crédits dépensés (≈ 0 attendu) + wall-time par étape, reportés.

## Règle de verdict
- 🟢 VERT : H1, H2, H5, H6 passent + H4 au moins partiel.
- 🟠 AMBRE : la chaîne tourne mais 1 hypothèse-clé (H2 ou H6) échoue.
- 🔴 ROUGE : la chaîne casse, ou sourcing = bruit (H2 < 40 %), ou drafts hallucinés.
- H3 = bonus (n'inverse pas le verdict).

## Fidélité au système
- Tous les writes DB via `db.py --db <abs>` (CONVENTIONS §5), statuts pending/running/done.
- Outils réels : workspace.py, db.py, firmo.py, news.py, rank.py (rank-accounts), score.py si applicable.
- Drafts uniquement (messages status=draft) — rien n'est envoyé (doctrine write-outreach).
- Gates : big-spend §8 non déclenché (lanes gratuites) ; data-plane §10 (la masse reste en base, pas dans le contexte).
