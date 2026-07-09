---
name: sillage-connect
description: Le rituel de connexion Sillage (Day-1, ~15 min) — connecter le MCP/la clé, DÉCOUVRIR les capacités réelles, geler les endpoints to_confirm, re-mapper l'arbre (BROKER), valider par requêtes-étalons, campagne fumée. À lancer dès que l'accès Sillage arrive.
---

# sillage-connect — rituel du jour J

Suivre `DAY1-SILLAGE.md` (racine du plugin) pas à pas. Résumé exécutable :

1. **Connecter** : `claude mcp add --transport http sillage
   https://api.getsillage.com/api/mcp/v2` (OAuth) — ou clé `sk_live_` dans
   `~/.bricks/env` (SILLAGE_API_KEY=...).
2. **Lire les quotas D'ABORD** : `sillage_v2_get_rate_limit` + setup-state
   (`sillage://setup-state`). Trial = cap à VIE sur les top accounts : décider
   du contingent AVANT tout push.
3. **Découvrir** : exporter la liste des outils MCP →
   `sillage_adapter.py discover --tools-json tools.json` →
   `sillage.capabilities.discovered.json`. Télécharger l'OpenAPI
   (`api.getsillage.com/api/v1/docs/spec`) → geler les `to_confirm` de
   `schema/sillage.endpoints.json` (chemins réels + payloads par type de
   signal — seuls keywordDetection est documenté en exemple).
4. **Re-mapper** : `@v2-broker` sur l'arbre avec le catalogue découvert —
   proxies presumed → confirmed/absent ; les absents redeviennent
   inobservables (questions), le système reste entier.
5. **Requêtes-étalons** (3 golden queries à réponse connue) : pousser 20
   comptes du field-test 08/07 dont le domaine est vérifié, lancer un signal
   run, vérifier que les signaux reviennent joignables par domaine.
   Recouvrement anormalement bas = mapping d'identité faux, PAS la thèse.
6. **Campagne fumée** : thèse MemoVAL, 50 comptes max du contingent, agents
   compilés depuis l'arbre, un run, `signals_to_evidence` → `score_v2.py run`
   — vérifier que des entreprises BOUGENT de bande. Zéro envoi.
7. **Receipt final** : quotas, capacités confirmées/absentes, latence réelle
   d'un run, coût observé, contingent consommé. → `memory/state.json` +
   NOTES.md datées.
