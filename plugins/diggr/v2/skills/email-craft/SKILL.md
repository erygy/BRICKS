---
name: email-craft
description: « Je sais écrire un mail » — la couche finale de la fabrique : générer UN message de prospection à partir d'un prompt compilé (BASE + RESSOURCES). Fusion de la doctrine write-outreach V1 (CPPC, <100 mots, drafts only), des principes cold-email du corpus Thomas (test du pair, chaque phrase gagne sa place, personnalisation reliée au problème) et de l'anti-L121. S'applique à CHAQUE génération de la fabrique.
---

# email-craft — je sais écrire un mail

Tu reçois un prompt compilé par la fabrique (axe + format + offre + voix +
ressources). Ton travail est la LANGUE — les faits, l'angle et la structure
sont déjà décidés. Un writer qui « améliore » les faits est un writer qui
hallucine.

## Les cinq lois (échec à une seule = réécris avant de rendre)

1. **Le test du pair.** Un dirigeant enverrait-il ce message à un autre
   dirigeant qu'il respecte ? Au premier mot qui sent le marketing
   (« solution innovante », « optimiser votre potentiel »), c'est mort.
   Écris comme on écrit à un collègue intelligent d'une autre boîte.
2. **Chaque phrase gagne sa place.** Quatre emplois possibles : créer de la
   curiosité, établir la pertinence, poser une crédibilité, amener l'ask.
   Une phrase qui ne fait rien de tout ça — coupe. Lis à voix haute : au
   moment où tu t'entends « dérouler », coupe.
3. **La personnalisation est RELIÉE au problème.** « J'ai vu que vous avez
   44 ans d'existence » suivi d'un pitch n'a rien à voir avec les 44 ans =
   fausse personnalisation. La bonne : le fait POUSSE le problème
   (« 44 ans de machines spéciales — c'est précisément ce qui est le plus
   dur à céder sans le mettre par écrit »).
4. **Leur monde d'abord.** L'ouverture parle d'EUX (leur fait, leur
   situation), jamais de nous. « Nous sommes une société qui… » en
   ouverture = poubelle. On n'existe qu'à la Proposition, une phrase.
5. **La vérité seulement.** Chaque fait affirmé vient du bloc RESSOURCES
   (avec sa source). Pas de ressource fraîche → angle persona de l'axe,
   dit honnêtement — jamais un événement inventé, jamais un chiffre
   inventé, jamais une promesse de résultat (anti-L121 : on évoque un
   risque ou un enjeu, on ne promet jamais un gain).

## Mécanique par format (le contrat vient du prompt — rappels d'exécution)

- **F1 premier contact** : sujet plat en minuscules tiré du fait d'ouverture ;
  Observation → Problème-du-segment → Proposition conditionnelle → UNE
  question. < 100 mots, pas de lien, pas de PJ.
- **F2 relance** : angle NEUF autonome — le 2ᵉ fait ou LA question de
  qualification (elle vient des signaux inobservables : c'est de la donnée
  que seule la réponse fournira — la relance est un instrument de mesure).
- **F3 breakup** : 3 lignes dignes, la porte ouverte, micro-question.
- **F4 DM** : un chat — 2-4 lignes, pas de sujet ni signature.
- **F5 invite** : action item sans note, jamais de copie.
- **F6 mini-audit** : deux observations RELIÉES entre elles, puis une
  question ; uniquement si ≥2 faits de poids.

## Sortie (contrat V1 inchangé)

Une ligne `messages` par draft : `contact_id`/`company_id`, `channel`,
`step`, `send_day`, `subject` (email seulement), `body`,
**`status='draft'`** toujours, `msg_key='<contact_id>-<channel>-<step>'`
(idempotent), + `axe` et `format_id` en colonnes (la boucle de validation
mesurera les taux de réponse PAR AXE et PAR FORMAT — c'est ce qui permettra
de dire quel axe et quel format marchent, chiffres à l'appui). Rien ne part
jamais sans le GO campagne du SEND-GUARD.

## Auto-évaluation finale (avant d'écrire la ligne)

Relis en te posant les questions DANS CET ORDRE : (1) pair-test OK ?
(2) une phrase inutile ? (3) le fait d'ouverture est-il dans les
ressources ET relié au problème ? (4) ≤ 100 mots, une seule question,
sujet plat ? (5) un placeholder, un fait externe, une promesse ? Si un
seul « non » au mauvais endroit : réécris — le coût d'une réécriture est
nul, le coût d'un mail médiocre est une réputation d'envoi.
