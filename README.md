# BRICKS — marketplace de plugins GTM pour Claude Code

Deux moteurs GTM open-source, **installables indépendamment** depuis cette
même marketplace :

| Plugin | C'est quoi | Doc |
|---|---|---|
| [`bricks`](plugins/bricks/) | **Signal Interceptor** (v3) — l'agent qui surveille comptes & concurrents (Sillage), intercepte les prospects qui discutent avec un concurrent, qualifie à une porte ICP unique, score le WHY NOW preuves à l'appui, prépare la file de la semaine, rédige/audite et envoie (Emelia). UI locale : tables, file « to contact this week », fiche cold-call avec graphe. | [README](plugins/bricks/README.md) · [DEMO](plugins/bricks/DEMO.md) |
| [`diggr`](plugins/diggr/) | **Diggr** — la lignée Bricks v2 : workspace management, find / enrich / transform sur SQLite par workspace, plus le front Diggr (`v4/`) et les expérimentations v2 (`v2/` — agents, schémas, scoring). | [v4/DEMO-RUNBOOK](plugins/diggr/v4/DEMO-RUNBOOK.md) |

> ⚠️ **Ce repo n'est PAS le repo de soumission du hackathon.**
> Règle de l'événement : « Build entirely during the event. No prior commits. »
> Ce dépôt sert de référence/fondation ; le jour J, on repart d'un repo vierge
> (ou on le déclare comme dépendance open-source créditée SI les organisateurs
> valident explicitement).

## Installer

```
/plugin marketplace add erygy/BRICKS
/plugin install bricks@bricks     # le Signal Interceptor (v3)
/plugin install diggr@bricks      # la lignée v2/v4 — indépendant du premier
```

Chaque plugin a son manifeste (`plugins/<nom>/.claude-plugin/plugin.json`),
son MCP (`.mcp.json`), ses hooks, ses skills et ses tools — rien n'est
partagé entre les deux à l'exécution.

## Structure

```
.claude-plugin/marketplace.json   la marketplace (2 plugins)
plugins/
  bricks/                         Signal Interceptor v3 (le produit courant)
  diggr/                          Diggr — plugin fonctionnel (lignée v2)
    v4/                           le front Diggr (displacement) + landing + data
    v2/                           expérimentations (agents, schémas, fixtures)
CLAUDE.md                         instructions de dev du repo (contrat 5 tables)
```

## Développer

Le contrat des 5 tables, les règles moteur et la propriété des chemins de
`bricks` vivent dans [CLAUDE.md](CLAUDE.md) (racine). Le fil de test complet
P0→P7 : [plugins/bricks/DEMO.md](plugins/bricks/DEMO.md). En session de dev
sur ce repo, les commandes s'exécutent depuis `plugins/bricks/` (ou avec le
préfixe `plugins/bricks/…`).
