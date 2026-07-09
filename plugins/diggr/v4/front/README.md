# BRICKS V4 — Cockpit de déplacement concurrentiel (interface)

Interface complète du moteur V4, en **identité visuelle EuroGuide** (dark, glassmorphisme,
mesh animé, Inter + JetBrains Mono, accents joyaux). Deux axes produits intégrés partout :
**Captation** (voler un client d'un concurrent, rose) et **Interception** (devancer la
signature d'un prospect qui évalue un concurrent, cyan).

## Lancer
```bash
cd plugins/bricks-v4/front
python3 build_seed.py     # (re)génère seed.json — briefs générés par Fable 5 (clé ~/.bricks/env)
python3 server.py         # → http://127.0.0.1:8970
```
Sans clé Anthropic, l'interface tourne quand même (le chatbot et la détection de concurrents
affichent un message « clé requise »). Avec la clé, tout est live.

## Les 4 écrans
1. **Installation** — wizard 3 étapes : Profil entreprise → Clés API (état masqué) →
   Concurrents détectés par l'IA (bouton « Re-détecter » = appel Fable réel `/api/detect-rivals`).
2. **Comptes** — table interactive : axe (Captation/Interception), concurrent, **FIT** (barre
   de score + tier A/B/C), **FENÊTRE** (Ouverte/Tiède/Fermée), nb de signaux. Tri sur chaque
   colonne, filtre, lentille d'axe. Clic sur une ligne → le Brief.
3. **Radar** — la vue de pilotage : stats (captation/interception/fenêtres/tier A/volume
   estimé), file « À démarcher maintenant » (fenêtres ouvertes), et un **board par concurrent**
   scindé en deux colonnes Captation | Interception, avec la **faille exploitable** du rival.
4. **Brief** — 1 écran pour un compte : hero (headline + EvidenceQuote), signaux clés, axes
   stratégiques, membres clés à contacter (+ justification + ce que FullEnrich doit trouver),
   message pré-rédigé (copiable), chiffres clés, leviers — **et un chatbot ancré** (rail droit)
   qui répond UNIQUEMENT sur les faits du dossier et **s'abstient** sinon (façon MemoVAL).

## Données — réel vs démo
- **Réel** : les concurrents Algolia/Devoteam et leurs clients (Frasers Group, Hershey, Stena
  Line, Liberty Global…) sont **minés live** depuis Sillage (`_proofs/proof-mining.txt`). Les
  signaux viennent de la **taxonomie réelle de 257 flags** (`_data/flags_ranked.json`), les
  failles de `_data/failles.json`. Les briefs et les réponses du chatbot sont **générés par
  Fable 5 en vrai**, ancrés sur ces faits.
- **Démo / ordres de grandeur** : l'entreprise « Lumen Search », les firmo (CA/effectif) et les
  scores de fit sont synthétisés de façon déterministe pour la démonstration. En production, le
  fit vient de `score_v2.py` (V2) et les firmo d'un registre/FullEnrich.

## API du serveur
| Endpoint | Rôle | Outil réel |
|---|---|---|
| `GET /api/seed` | tout le jeu de données | — |
| `POST /api/ask` | chatbot ancré (par compte), s'abstient hors-dossier | **Claude/Fable** |
| `POST /api/detect-rivals` | détection de concurrents (onboarding) | **Claude/Fable** |
| `GET/POST /api/settings` | clés API (masquées, jamais renvoyées en clair) | `~/.bricks/env` |

## Robustesse
Appels Claude via `fable_api.py` (**streaming curl**, robuste au mur de connexion Mac). Si
Claude ne répond pas, le serveur renvoie un état d'erreur propre (pas de faux « réponse »).
Les clés sont stockées `chmod 600`, jamais renvoyées en clair, jamais committées.

> Le front V1 (`plugins/bricks/front/`) reste intact — V4 est un cockpit distinct et additif.
