# APPEL — dossier hackathon (dans `bricks-v2`, additif, zéro régression)

Ce dossier est **purement additif** : il ne touche aucun fichier de `bricks` (V1) ni du
reste de `bricks-v2`. C'est le dossier de l'idée gagnante du hackathon IA-GTM
(Anthropic × Sillage × FullEnrich), issue d'une exploration double-diamant sur Fable 5.

## Lire

1. **`DOSSIER-APPEL.md`** — le dossier complet (problème → solution → preuve → plan 48h →
   démo → pitch → scorecard → limites). **Commence ici.**
2. **`proof-triptyque.txt`** — la sortie capturée du cœur (le moment-wow, verdicts réels).
3. **`exploration/`** — les 4 sorties brutes des diamants (synthèse, critique, matrice, jury).

## Faire tourner la preuve (le cœur)

```bash
cd _appel-hackathon
# clé API dans ~/.bricks/env :  ANTHROPIC_API_KEY=sk-ant-...
python3 tribunal.py
```

Attendu : **même levée de 22 M€, trois verdicts opposés** (FALSIFIÉE / INTACTE / ABSTENTION),
chacun raisonné et porteur de son contre-argument, + un compteur de retenue
(*jugés · rouverts · laissés dormir · crédits · 0 token pour le tri*).

## Fichiers

| Fichier | Rôle |
|---|---|
| `tribunal.py` | Le cœur : typage déterministe (0 token) + procès de polarité (Claude, JSON strict) + gate VOI + démo triptyque |
| `fable_api.py` | Appel Fable 5 **streaming/curl** — robuste au mur de connexion Mac→Anthropic ; clé via fichier de config curl (jamais en argv) |
| `DOSSIER-APPEL.md` | Le dossier stratégique complet |
| `proof-triptyque.txt` | La preuve capturée |
| `exploration/*.md` | La trace intégrale du double-diamant |

## Merge dans le produit

Rien à merger tel quel : c'est un **dossier + une preuve de concept**. Quand vous
industrialisez APPEL, chaque étape du §5 (« plan de construction ») réutilise une brique
`bricks-v2` existante (`score_v2`, `verdict`, `messaging_factory`, `sillage_adapter`,
`fullenrich_adapter`, `crm_adapter`, `domain_resolver`) + le seul composant neuf =
`tribunal.py` (typage + polarité). Additif, avec bump de version (Rule 3).

> Sécurité : `fable_api.py` lit la clé depuis `~/.bricks/env`. Ne jamais committer de clé.
> La clé actuellement utilisée a été exposée en chat → à **rotationner** après le hackathon.
