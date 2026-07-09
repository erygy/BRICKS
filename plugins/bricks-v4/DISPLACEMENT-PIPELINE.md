# BRICKS V3 — LE MOTEUR DE DÉPLACEMENT
### « On ne prospecte pas le marché. On surveille les clients de tes concurrents. »

> Repensé de A à Z autour du **vol de clients aux concurrents** (displacement), pas de
> l'acquisition à froid. Conçu le 09/07/2026 sur la base de la **spec API Sillage réelle
> gelée** (`_proofs/sillage-openapi.json`) et de **tests live** sur le workspace de l'équipe
> (clé `sk_live_…` — lecture seule). Deux maillons critiques sont **déjà prouvés sur données
> réelles** : la récupération des posts d'un concurrent (§ Étage 2) et l'extraction de ses
> clients par Claude (10 relations extraites de 50 vrais posts, citations à l'appui).

---

## 0. La thèse

Le cold outbound s'effondre (canal saturé — cluster n°2 de l'exploration de masse du 09/07).
Mais un client de concurrent n'est **pas un prospect froid** : son besoin est **prouvé** (il
paie déjà pour la catégorie), son budget **existe**, et sa relation actuelle a des **moments de
fragilité observables**. La V3 industrialise trois choses :

1. **Constituer l'actif** : la base « clients des concurrents » la plus riche possible.
2. **Écouter les fenêtres** : ~120 red flags qui disent *« ce compte est démarcheable MAINTENANT »*.
3. **Armer le discours** : les failles du concurrent au moment T → le levier de persuasion.

**Le droit de jouer est sain juridiquement** : démarcher les clients d'un concurrent est
licite en France (liberté du commerce) **tant qu'on n'emploie pas de procédés déloyaux** —
jamais de dénigrement, pas de confusion, pas de désorganisation. La « posture aspirine »
(on soulage un problème, on n'attaque personne) est donc une **contrainte produit codée**,
pas une politesse.

---

## 1. Le pipeline en 7 étages

```
① PROFIL  ② CONCURRENTS  ③ MINAGE CLIENTS  ④ BASE+ENRICH  ⑤ VEILLE FLAGS  ⑥ FAILLES  ⑦ DÉMARCHAGE
 Claude  →   Claude+web  →  Sillage+Claude →  FullEnrich  →  Sillage(agents) → Claude  →  fabrique V2
```

### ① Profil — description de l'entreprise et du marché
L'utilisateur décrit son entreprise, son offre, son positionnement (formulaire libre).
Claude en dérive : catégorie, périmètre concurrentiel, vocabulaire métier (qui nourrit les
mots-clés des agents), et le **persona** (poussé dans Sillage `/v2/persona`).

### ② Concurrents — listing et validation
Claude (+ recherche web) propose 8-15 concurrents majeurs avec domaine + LinkedIn.
**Validation humaine obligatoire** (un faux concurrent pollue tout l'aval). Chaque concurrent
est poussé : watchlist **`competitor`** (spec réelle : `POST /v2/watchlists` type=competitor,
puis `/entities` — identité par LinkedIn/domaine, 100 max/appel).

### ③ Minage des clients — l'étage décisif ✅ PROUVÉ LIVE
Pour chaque concurrent, TOUTES les sources en parallèle :

| Source | Primitive | Statut |
|---|---|---|
| **Posts LinkedIn du concurrent** | Sillage `content-requests` type **`top_account_content`** → `/v2/contents/query` (8 types : linkedinCompanyPost, linkedinPost, blogPost, pressRelease, webArticle, linkedinJobPosting…) → **Claude extrait les clients avec citation** | ✅ **prouvé live** : 50 posts réels → 10 clients (Frasers Group, Hershey… ; Stena Line, Liberty Global…) |
| Site web (logos, cas clients, portfolio, témoignages) | fetch + Claude extraction (zéro dépendance) | à câbler (trivial) |
| Avis G2 / Capterra / Trustpilot (SaaS) | fetch pages publiques + Claude | à câbler |
| Offres d'emploi des clients citant l'outil du concurrent | Sillage agent **`job_posting_keyword_detection`** (mots-clés = noms des produits concurrents) | primitive live confirmée |
| Presse, communiqués, événements co-brandés | `contents/query` types webArticle/pressRelease + Claude | primitive live confirmée |
| Marchés publics attribués (BOAMP/DECP) | API publiques FR (gratuit) | à câbler |
| Employés du concurrent → qui ils servent | Sillage `content-requests` type **`account_mapping`** (profils employés) | primitive live confirmée |

Chaque client extrait porte : `evidence` (citation), `certainty` (haute/moyenne/basse),
`source`, `first_seen`. → `domain_resolver.py` (V2, zéro clé) résout le domaine.
**Rendement mesuré/estimé : ~100-400 clients identifiables par concurrent.**

### ④ La base + enrichissement — l'actif central
SQLite (bus V1, conventions BRICKS) : table `rivals` (concurrents), `stolen_targets`
(clients de concurrents : domaine, concurrent, evidence, certainty, ancienneté estimée de la
relation), `flags` (événements), `dossiers` (démarchages).
**Discipline VOI (héritée V2)** : FullEnrich ne dépense **rien** à la constitution de la base —
`search` (0,25 crédit/résultat) pour cartographier le comité **seulement quand un flag
fort se déclenche**, email vérifié (1 crédit) seulement au moment du démarchage.

### ⑤ Veille — les red flags (~120, taxonomie explorée en masse)
Les clients sont poussés en watchlists **`customer`** (companies) ; les sponsors identifiés
en watchlists **profils**. Les agents Sillage écoutent :

| Type d'agent (live) | Ce qu'il écoute pour V3 |
|---|---|
| `keyword_detection` | packs de mots-clés par famille de flags dans les posts des clients (recrutement interne, refonte, appel à reco, budget, salon…) |
| `job_posting_keyword_detection` | offres d'emploi des clients : internalisation, poste recouvrant l'offre du concurrent, « refonte de X » |
| `job_update` | changements de poste : départ/arrivée du sponsor de la relation, retraite du référent |
| `customer` (lié watchlist) | signaux généraux sur les comptes clients |
| `champion` (lié watchlist profils) | les personnes clés qui bougent |
| `competitor` (lié watchlist) | ce que fait le concurrent lui-même (nourrit ⑥) |

Poll quotidien `signals/query` (curseur) — **pas de webhooks**, le cron BRICKS fait le poll.
Chaque signal est mappé sur la taxonomie de flags → **score de déplacement par compte**
(le moteur V2 `score_v2.py` pointé sur l'arbre des flags : intervalles, bandes IN/BAND/OUT,
anti-double-comptage). Un compte passe « démarcheable » sur flag fort ou cumul.

### ⑥ Failles — le levier de persuasion
Au moment où un flag ouvre une fenêtre sur un client, Claude analyse le CONCURRENT :
`top_account_content` (ses posts récents), avis récents, presse, mouvements de personnel
(`job_update` sur watchlist competitor). → taxonomie de ~25 failles (hémorragie de talents,
distraction stratégique post-levée, hausse de prix, sur-croissance qui dégrade le service…).
**Sortie : le LEVIER** — jamais « le concurrent est mauvais », toujours « voici ce que vous
méritez d'avoir en plus » (posture aspirine, contrainte codée dans la fabrique).

### ⑦ Démarchage — la fabrique V2 réarmée
`messaging_factory.py` (ressources fermées, zéro hallucination) reçoit : le flag (l'accroche
datée), la faille (le levier), le contexte client (evidence du minage), le contact FullEnrich.
→ dossier de démarchage : angle + email + relance + brouillon LinkedIn. Envoi gated
(`outreach_send.py`, dry-run par défaut). Écriture CRM (`crm_adapter.py`).

---

## 2. Ce que la V3 réutilise (rien ne se jette)

| Brique V2 | Rôle en V3 |
|---|---|
| `score_v2.py` | le score de déplacement par compte (arbre = taxonomie de flags) |
| VOI | quand dépenser un crédit FullEnrich (jamais en masse, toujours sur flip) |
| `messaging_factory.py` | la fabrique de dossiers de démarchage |
| `verdict.py` | viabilité du motion par concurrent (assez de flags ? assez de RDV ?) |
| `domain_resolver.py` | résolution nom→domaine des clients minés |
| `sillage_adapter.py` | à mettre à jour sur la spec réelle gelée (chemins confirmés ✅) |
| `fullenrich_adapter.py` | REST prêt ; MCP enregistré (OAuth à faire en session interactive) |
| `crm_adapter.py`, `outreach_send.py` | writeback + envoi gated |

## 3. Ce qui est neuf

1. **`client_miner.py`** — l'étage ③ (posts + site + avis + jobs → clients avec evidence). Le
   prototype du maillon posts→clients est `_proofs/mine_clients.py` (prouvé).
2. **La taxonomie des ~120 red flags** (exploration Fable en cours → `flags/flags_ranked.json`)
   compilée en **packs d'agents Sillage** (mots-clés FR par famille).
3. **La taxonomie des ~25 failles** + le prompt de levier (posture aspirine).
4. **`displacement_daemon.py`** — le cron : poll quotidien, scoring, file de dossiers.
5. **Le « Rival Board »** — l'UI de V3 : par concurrent, la base de ses clients, les flags du
   jour, les dossiers prêts.

## 4. Contraintes réelles à ne pas maquiller

- **Le quota Sillage est LA ressource rare** (trial = cap à vie ; erreur
  `top-account-quota-exceeded` = rejet total). Le workspace live est celui de l'équipe
  (13 comptes, 29 agents — expérimentations du jour). V3 à l'échelle (800-4 800 comptes)
  suppose un **plan payé** — c'est un coût de production, pas un blocage de design.
  Architecture quota-aware : prioriser les clients `certainty=haute` + les concurrents au
  churn le plus probable ; watchlists par vagues.
- **Pas de webhooks** → poll quotidien (le daemon).
- **FullEnrich MCP = OAuth interactif** (`claude mcp` → `/mcp` dans le projet Bricks, déjà
  enregistré) ; le REST attend une clé API. Aucun crédit dépensé sans gate VOI.
- **RGPD/CGU** : les entités de la base sont surtout des ENTREPRISES (pas de données perso) ;
  les profils (sponsors) = données pro minimisées, enrichies seulement sur flag (intérêt
  légitime B2B, effacement à la perte de pertinence). Le scraping LinkedIn est porté par
  Sillage (leur infra, leur risque contractuel) ; nos fetchs directs se limitent aux pages
  publiques des sites (cas clients, logos). Jamais de dénigrement dans les messages (codé).
- **Faux positifs** : chaque flag de la taxonomie porte son `false_positive` + garde-fou ;
  le score par compte exige flag fort OU cumul (pas de démarchage sur bruit).

## 5. Viabilité (calcul détaillé dans `_proofs/viability.txt`)

L'univers n'est pas « 1 démarchage/6 mois » parce qu'on ne surveille pas UN compte — on
surveille **800-4 800 comptes** (8-12 concurrents × 100-400 clients) × ~120 types de flags.
Même avec des fréquences unitaires honnêtement faibles, la somme donne des **flags
quotidiens en abondance** et des démarchages qualifiés chaque semaine (chiffres exacts
calculés sur les fréquences par flag une fois la taxonomie atterrie).
