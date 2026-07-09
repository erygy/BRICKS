# SECOND AVIS — dossier hackathon (dans `bricks-v2`, additif, zéro régression)

Idée gagnante issue d'une **exploration de masse** sur Fable 5 (941 douleurs → 52 clusters →
308 concepts → 22 finalistes réfutés → 14 survivants → verdict). Le diagnostic différentiel
du silence client : *« Gainsight lit l'intérieur ; SECOND AVIS est la moitié externe du
health score. »* Purement additif — ne touche aucun fichier de `bricks` (V1).

## Lire
1. **`DOSSIER-SECOND-AVIS.md`** — le dossier complet (douleur → solution → preuve → plan 48h →
   démo → pitch → scorecard → pourquoi ça bat l'idée précédente → limites). **Commence ici.**
2. **`pitch-secondavis.html`** — le one-pager visuel (registre diagnostic). Ouvrable hors-ligne.
3. **`proof-diagnostic.txt`** — la sortie capturée du cœur (5 verdicts divergents + 2 emails).
4. **`exploration/`** — la trace réelle : verdict du stratège, 52 clusters, 308 concepts scorés,
   22 finalistes réfutés, stats.

## Faire tourner la preuve
```bash
cd _secondavis-hackathon        # clé API dans ~/.bricks/env (ANTHROPIC_API_KEY=...)
python3 diagnostic.py
```
Attendu : **même silence interne → verdicts divergents** (BÉNIN / TOXIQUE / INDÉTERMINÉ),
chacun citant sa preuve datée et sa condition de falsification, + **deux emails opposés**
générés depuis le même silence interne.

## Fichiers
| Fichier | Rôle |
|---|---|
| `diagnostic.py` | Le cœur : silence interne figé (0 token) + diagnostic différentiel (Claude, JSON) + 2 messages opposés |
| `fable_api.py` | Appel Fable 5 streaming/curl (robuste au mur de connexion Mac) |
| `DOSSIER-SECOND-AVIS.md` | Le dossier stratégique complet |
| `pitch-secondavis.html` | Le pitch visuel (+ `pitch-secondavis.artifact.html` = variante pour publication) |
| `proof-diagnostic.txt` | La preuve capturée |
| `exploration/*` | La trace intégrale de l'exploration de masse |

## Plan de construction (48h)
Voir §5 du dossier. ~70 % des briques existent déjà dans `bricks-v2` (`score_v2`,
`sillage_adapter`, `fullenrich_adapter`, `messaging_factory`, `crm_adapter`, `domain_resolver`) ;
le seul composant neuf = `diagnostic.py`. Additif, avec bump de version (Rule 3).

> Sécurité : `fable_api.py` lit la clé depuis `~/.bricks/env`. Ne jamais committer de clé.
> La clé actuellement utilisée a été exposée en chat → **rotationner** après le hackathon.

## Lien avec l'itération précédente
La 1re idée (`_appel-hackathon/` — réactivation de deals perdus / falsification d'objection)
a été **écartée par l'exploration de masse** : trop étroite (douleur d'AE, 1-2 déclencheurs/
trimestre), dépendante d'un champ CRM pourri. SECOND AVIS vise une douleur de **dirigeant**
(NRR), **permanente** (20-40 % du book), avec une démo plus robuste. Le dossier APPEL reste
archivé comme portefeuille de secours et trace de méthode.
