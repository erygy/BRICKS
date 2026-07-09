# front/ — the local web UI

A Clay-like table view over the current workspace's `bricks.db`, plus the
**fiche** (the ONE detail screen, company- or contact-centered) and the
**« To contact this week »** queue. Launched by the `/bricks:interface`
skill.

- `server.py` — a stdlib HTTP server (127.0.0.1 only) that reuses
  `tools/core/{workspace,db,envfile}.py`, so the UI never drifts from what
  the skills write. Run: `python3 server.py [--port 4321] [--root bricks]`.
- `index.html` — single-file React UI (CDN esm.sh). Loads the theme before
  first paint, polls every 4 s.

## Screens

- **Tables** — one tab per table (sort, filters, selection, delete,
  CSV/XLSX export). Status columns render as chips (§4 vocabulary).
- **📞 To contact this week** — `outreach ⋈ contacts ⋈ companies`, sorted
  by week then priority score. Read-only (no checkboxes); click a row to
  open the contact's fiche.
- **La fiche** (click any companies/contacts/week row — same screen, two
  entry points): WHY NOW banner + dated evidence (the faisceau), the FK
  graph as SVG (center entity, decision-makers/company around, competitors
  dashed, signal dots — orange = fresh ≤ 60 days), signals list (stale ones
  dimmed), colleagues/decision-makers with tier, clickable coordinates,
  outreach cards with expandable drafts and the **Approve** button.
  Graph nodes navigate to the clicked entity's fiche.
- **⚙ Settings** — the engine keys panel (`~/.bricks/env`, chmod 600,
  values masked, list rendered from `envfile.KNOWN_KEYS`).

## JSON API

| Endpoint | Rôle |
|---|---|
| `GET /api/ping` | `{"app": "bricks", "root": …}` — detect a running server |
| `GET /api/status` | workspace courant + tables |
| `GET /api/table/<name>` | headers + rows (colonnes `_`-préfixées cachées côté UI) |
| `POST /api/table/<name>/remove` | `{"ids": […]}` — delete by `_id` |
| `GET /api/week` | la file de la semaine, jointe et triée (table-shaped) |
| `GET /api/graph/<companies\|contacts>/<id>` | le sous-graphe FK d'une entité (center, company, contacts, signals, competitors, outreach) |
| `POST /api/outreach/<id>/approve` | **la SEULE écriture front** (contrat) : `status draft→approved` ; refuse en 409 si `audit_score < 70` ou si la ligne n'est pas `draft` |
| `POST /api/workspace/switch` | changer de workspace |
| `GET/POST /api/settings` | clés moteur (masquées) |

Rows are addressed by the reserved `_id`. Reads go through `db.py`
(read-only SQLite for tables, function mode elsewhere); the front writes
NOTHING else — enrichment and sends are triggered by the skills, not the UI.
