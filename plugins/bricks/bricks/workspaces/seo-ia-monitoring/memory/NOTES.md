# Working notes — seo-ia-monitoring

> Free-form working memory for this workspace. Skills append decisions,
> context and open questions here, newest entries at the bottom.

- 2026-07-10 — /bricks:onboard : offre + ICP v1 + personas (CMO, Founder/CEO)
  persistés. Phase 3 concurrents SAUTÉE sur demande utilisateur — table
  competitors vide, l'interception (intercept.py) et la watchlist Sillage
  concurrent resteront inertes tant qu'elle n'est pas remplie. Kill rules et
  champion encore « à confirmer » ; proof points et ton de voix en TODO.

- 2026-07-10 — Sourcing P1 (partiel) : FullEnrich OK via MCP après déblocage
  connecteur. 2 exports CSV payés (100 rows, 25 crédits) mais TÉLÉCHARGEMENT
  BLOQUÉ par la politique réseau de l'environnement (app.fullenrich.com refusé
  par le proxy, liens valides jusqu'au 2026-07-11T14:09Z). Fallback : 2×10 via
  search_companies (0 crédit) → staging → import_p1.py → 19 companies insérées
  (1 sans domaine sautée), qualify_status=pending. Crédits restants : ~320.

- 2026-07-10 — Qualif P2 (qualify-2026-07-10) : 19 rows failed, AUCUN crédit
  dépensé. Transport SDK impossible dans ce conteneur (auth session par FD non
  réutilisable + root bloque skip-permissions) ; transport API = 401 (pas
  d'ANTHROPIC_API_KEY). Reprise : clé dans ~/.bricks/env + BRICKS_AGENT_TRANSPORT=api,
  puis re-lancer le runner avec --retry-failed (statuts = checkpoint).
