---
name: score-v2
description: Scorer un univers contre un arbre de signaux (intervalles pessimiste/attendu/optimiste, bandes IN/BAND/OUT), contrôler l'identifiabilité, produire le plan VOI. Le score est du CODE (score_v2.py) — cette skill est le protocole d'usage, pas le calcul.
---

# score-v2 — protocole

Le calcul vit dans `tools/score_v2.py` (déterministe, rejouable, auditable).
La skill encadre son usage :

1. **Avant** : `score_v2.py check --tree` — zéro erreur, zéro warning de
   sensibilité (fidelity>coverage = confusion précision/sensibilité, retour
   CRITIC).
2. **Run** : exporter l'univers (`db.py select … --limit -1`) + l'évidence
   (`db.py select evidence`) → `score_v2.py run --today <date-du-jour>` →
   receipt d'identifiabilité. Verdict ≠ ok → STOP, retour CRITIC, on ne
   dépense rien sur un score mort.
3. **Commit** : scores → `db.py modify companies --updates -` (colonnes
   pessimistic/expected/optimistic/band/salvage + top_contributors JSON).
   L'évidence est append-only : un score se recalcule à toute date.
4. **VOI** : `score_v2.py voi --budget <B>` — le plan ne contient QUE la
   bande. Le passer au VERIFIER avec UN GO groupé (§8).
5. **Repêchage** : les `salvage=true` (gate mort, évidence extraordinaire)
   partent en revue HUMAINE — c'est le détecteur de thèse trop étroite
   (cas prouvé : Ponant Technologies, tuée par le kill sectoriel, remontée
   par son signal de cession réel).
6. **Décomposition exigée** : toute liste livrée à un humain montre, par
   entreprise, les 3 contributeurs dominants + leurs evidence_url. Un score
   sans explication n'est pas livrable.
