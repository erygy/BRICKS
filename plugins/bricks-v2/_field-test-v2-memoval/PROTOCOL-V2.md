# Test scientifique BRICKS V2 → MemoVAL — protocole PRÉ-ENREGISTRÉ

Date : 2026-07-08 (nuit). Objet : lancer V2 de A→Z sur le MÊME cas que V1
(vendre MemoVAL), mesurer sa pertinence, et le COMPARER à V1. Seuils fixés
AVANT les juges.

## Conditions (identiques à V1, pour une comparaison honnête)
- **Univers CONSTANT** : les 303 mêmes PME que le test V1 (chargées sans les
  verdicts V1 — V2 repart du brut). La SEULE variable est le cerveau V2.
- **Mêmes lanes gratuites** : firmographie API gouv + presse (déjà en base).
  FullEnrich et Bright Data toujours indisponibles (pas de clés).
- **Sillage** : indisponible → signaux Sillage SIMULÉS (mock déterministe),
  CLAIREMENT étiquetés — la capacité réelle Sillage n'est PAS prouvée ici ;
  ce qui est prouvé, c'est la machinerie qui consommera ces signaux.
- **Mêmes juges adversariaux, mêmes grilles** que V1 (précision ICP + qualité
  mails) → chiffres directement comparables.

## ⚠️ Honnêteté centrale (à déclarer dans le verdict)
L'arbre de signaux V2 a été construit EN ENCODANT les leçons du field-test V1
(ingénierie = anti-signal → gate P ; filiale ; plancher d'ancienneté). Donc
« V2 réussit du premier coup » n'est PAS de la magie : c'est de la
**CAPITALISATION** (la connaissance devient un actif réutilisable). La
comparaison juste n'est donc pas « V2 1er run (45 %?) vs V1 1er run (45 %) »
mais **« V2 1er run vs V1 FINAL après 3 patchs (75 %) »** — la question :
V2 atteint-il le meilleur de V1 SANS l'itération manuelle par campagne ?

## Hypothèses & seuils (pré-enregistrés)
- **HV1 Chaîne complète** : V2 tourne thèse→tree→score→VOI→tableau→axes→mails
  sans crash, 0 crédit. [PASS/FAIL]
- **HV2 Précision ICP de la bande IN** : ≥ 75 % (égaler le V1 final), juge
  adversarial MÊME grille, n=20. [seuil 75 %]
- **HV3 Zéro-patch** : nombre de cycles de correction de kill-rules EN COURS
  de run = 0 (vs 3 en V1). [seuil 0]
- **HV4 Discrimination** : bandes non dégénérées (IN>0, OUT>0, chacune ≤80 %)
  + intervalles informatifs (pess<opt sur la bande).
- **HV5 VOI décision-first** : 100 % des checks planifiés peuvent changer de
  bande (flips≥1).
- **HV6 Qualité mails** : moyenne ≥ 8,4/10 (égaler/battre V1), juge MÊME
  grille ; ET différenciation par axe (deux axes → mails non-confondables).
- **HV7 Profondeur** : les mails V2 exploitent l'AXE (segment-histoire) — un
  atout que V1 (template plat unique) n'avait pas. Jugé qualitativement.
- **Coût / latence** reportés.

## Métriques de COMPARAISON V1 ↔ V2 (tableau final)
| Dimension | V1 | V2 |
|---|---|---|
| Sourcing | 303 (API gouv) | 303 (idem) |
| Sélection | 194 ICP-fit | bande IN |
| Patchs manuels nécessaires | 3 | à mesurer |
| Précision ICP (même juge) | 75 % (après 3 patchs) | à mesurer |
| Modèle de signal | état firmo implicite | signaux nécessaires 3 couches, explicites |
| Priorisation | tiers plats A/B/C | intervalles + bandes + VOI |
| Messaging | 5 CPPC template unique | fabrique axes×formats |
| Qualité mails (même juge) | 8,4/10 | à mesurer |
| Réutilisabilité | kill-rules jetables/campagne | arbre de signaux = actif |
| Coût | 0 crédit | 0 crédit |

## Règle de verdict
- 🟢 VERT : HV1+HV2+HV6 passent ET HV3=0 → « V2 atteint le meilleur de V1
  sans itération manuelle, + capitalise + segmente l'outreach ».
- 🟠 AMBRE : chaîne OK mais précision ou qualité sous le niveau V1.
- 🔴 ROUGE : chaîne casse, ou précision < 60 %, ou mails hallucinés.

## Fidélité au système
Outils réels V2 (score_v2, messaging_factory, sillage_adapter mock) + agents
(axe-mapper Opus 4.8) + skills (email-craft). db.py porte unique, statuts,
drafts only. Sillage mock étiqueté. Rien n'est envoyé.
