# seed/ — sourcing P1 (l'inserteur `companies` côté import)

Le chemin UNIQUE du sourcing (§6 CONVENTIONS.md) : les entreprises
arrivent en **CSV sur disque**, jamais en JSON massif dans la
conversation.

## Le geste P1

1. **Exporter** l'ICP depuis FullEnrich (MCP `export_companies` avec les
   filtres de `context/icp.md`, ou le dashboard) → télécharger le CSV dans
   `bricks/workspaces/<ws>/staging/`.
2. **Importer** :

   ```bash
   python3 seed/import_p1.py --csv bricks/workspaces/<ws>/staging/export.csv
   ```

   Auto-détection des en-têtes usuels ; sinon
   `--map "domain=Website,name=Company Name"`.

## Ce que le script garantit (le contrat, pas plus)

- `domain` normalisé (minuscules, sans protocole ni `www.`) et
  **obligatoire** — pas de domaine résolu = pas de ligne, jamais de
  company fantôme (les sautées sont comptées dans le receipt).
- Colonnes écrites : `name, domain, linkedin_url, headcount, industry,
  geo` (firmo STATIQUE seulement — le dynamique est à Sillage) +
  `source='fullenrich_search'` + **`qualify_status='pending'` armé à
  l'insert** — même porte P2 pour tout le monde.
- Dédup par `domain` (`import-csv --key`) : re-lancer n'insère jamais un
  doublon, ne met jamais à jour.
- CSV nettoyé stagé dans `staging/p1_import_<horodatage>.csv` (audit).

Ensuite : la porte P2 (qualification `runner --ai`, voir `/surveil`) —
puis `sillage.py setup` met les qualifiées sous surveillance.
