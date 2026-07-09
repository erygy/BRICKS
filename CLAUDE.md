# BRICKS-FINAL — règles du repo

Base curée de Bricks-v2 (voir README.md pour le périmètre gardé/jeté et les
briques à construire), distribuée comme **plugin Claude Code** — l'architecture
d'origine est conservée : manifeste `.claude-plugin/plugin.json`, hook
SessionStart (`hooks/hooks.json` → `tools/core/session_start.py`), MCP servers
dans `.mcp.json`, skills namespacées `/bricks:*`, chemins via
`${CLAUDE_PLUGIN_ROOT}`, workspaces `bricks/` par répertoire de travail.

## Les règles qui survivent

1. **La logique vit dans les tools, jamais dans les skills.** Un besoin
   nouveau = un provider ou un skill qui orchestre — jamais du code enfoui
   dans un SKILL.md, jamais de SQL écrit à la main dans la conversation.

2. **`db.py` est la seule porte vers la base.** Tables/colonnes dynamiques,
   `_id` réservé, colonne `X_status` appariée à toute colonne enrichie
   (`pending|running|done|not_found|failed`). Écritures en vagues
   (`modify --updates '[...]'`), jamais un appel par ligne.

3. **La porte de fer : preview → GO → commit.** Tout batch passe par
   `runner.py run … --preview 10`, UN GO explicite, puis `--commit`.
   Les statuts sont le checkpoint ; re-lancer reprend, ne repaie pas.

4. **Un chemin par capacité.** Sourcing = CSV sur disque →
   `db.py import-csv --key`. Enrichissement = pass-through (`import-csv`/
   `modify`) OU pipeline `runner.py` — jamais de boucle par ligne en session.

5. **La conversation décide ; les fichiers portent.** Jamais de masse de
   lignes dans le contexte — receipts, max 3 lignes d'échantillon.

Contrat runtime détaillé : `CONVENTIONS.md`. Référence outil par outil
(deux modes d'appel, CLI et fonctions) : `skills/tools-guide/SKILL.md`.

## Spécifique à cette base

- **Transport IA au hackathon : la voie API** (`BRICKS_AGENT_TRANSPORT=api` +
  `ANTHROPIC_API_KEY` dans `~/.bricks/env`). Ne pas utiliser `agent.py --web`
  (Bright Data, non-sponsor).
- **Données externes : sponsors d'abord.** Découverte et coordonnées =
  FullEnrich ; décideurs et signaux = Sillage (provider à écrire, pattern
  `fullenrich.py` : CLI JSON stdout + fonction `step(row, ctx, args)`).
- Les skills gardées contiennent des références à des briques jetées —
  liste assumée dans le README ; ne pas « réparer » au fil de l'eau, elles
  seront distillées en 4 skills maigres (onboard / surveil / prioritize /
  outreach).
