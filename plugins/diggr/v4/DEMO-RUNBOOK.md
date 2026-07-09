# BRICKS V4 — RUNBOOK DE DÉMO (live, ~4 min)

> Lancer avant de monter sur scène :
> ```bash
> cd ~/Documents/Bricks/plugins/bricks-v4/front && python3 server.py
> ```
> Ouvrir **http://127.0.0.1:8970**. Tout est pré-chargé (23 comptes, 23 dossiers, signaux réels) —
> **aucune dépendance réseau pendant la démo**, sauf le chatbot (voir §5, fallback géré).

---

## La phrase d'ouverture (le pitch en 1 ligne)
> « Bricks ne prospecte pas le marché. Il surveille **les clients et les prospects de vos
> concurrents**, et vous dit lesquels démarcher **maintenant** — avec le dossier prêt. »

## Le fil (4 écrans, 4 temps)

### ① RADAR — « voici le champ de bataille » (45 s)
- Ouvre sur **Radar**. Montre les 5 tuiles : **Captation** (clients de concurrents) vs
  **Interception** (prospects qui les évaluent) — *« les deux façons de voler un client »*.
- Pointe **« Volume estimé : 76/sem »** → *« ce n'est pas 1 démarchage tous les 6 mois :
  à 800 comptes surveillés, ~76 démarchages qualifiés par semaine »* (chiffre réel, taxonomie de 257 flags).
- Descends sur **un board concurrent** (Algolia) : sa **faille exploitable** + ses clients
  (colonne Captation) et ses prospects (colonne Interception), chacun avec sa **fenêtre**.

### ② La lentille à 2 axes (10 s)
- Clique **Captation** puis **Interception** dans la barre du haut → tout se filtre.
  *« Deux motions, deux messages : "passez chez nous" vs "avant de signer, comparez". »*

### ③ COMPTES — « le poste de travail » (30 s)
- Onglet **Comptes**. *« Chaque compte est scoré sur deux axes séparés — jamais mélangés :
  FIT = la qualité (barre + tier A/B/C), FENÊTRE = le timing (Ouverte = agir maintenant). »*
- Trie par **Fit**, montre la colonne **Concurrent** (à qui on le vole). Clic sur **The Hershey Company**.

### ④ BRIEF — « le dossier, prêt » (le cœur, 90 s)
- Le dossier s'affiche **instantanément**. Lis la **headline** (générée par Claude, ancrée sur
  le vrai signal : appel d'offres + hausse de prix Algolia).
- Montre la **preuve citée** (EvidenceQuote) → *« tout est sourcé, zéro invention »*.
- Fais défiler : **signaux clés**, **axes stratégiques**, **membres à contacter** (le rôle +
  ce que FullEnrich doit trouver), **message pré-rédigé** → clique **Copier**.
- **Les leviers** viennent de la faille du concurrent. *« On ne dénigre jamais — on soulage. »*

### ⑤ LE CHATBOT — le moment « waouh » (45 s)
- Dans le rail droit, tape *« Pourquoi ce compte maintenant ? »* → réponse nette, sourcée.
- Puis pose une question **hors-dossier** : *« Quel est le budget IT exact ? »* →
  **il s'abstient** : « Ce n'est pas dans le dossier… enrichir via FullEnrich ». 
  *« C'est ça, notre moat : il refuse d'inventer. »*

### Clôture (15 s)
- Reviens sur **Installation** (wizard 3 étapes) : *« Nouveau client : il décrit sa boîte,
  l'IA détecte ses concurrents, on mine leurs clients. 45 minutes de setup. »*

---

## Ce qui est RÉEL (à dire si on te challenge)
- Le **minage des clients de concurrents** est prouvé **live sur Sillage** (ta clé) : 50 posts
  LinkedIn réels d'Algolia/Devoteam → 10 clients extraits avec citation. `_proofs/proof-mining.txt`.
- Les **signaux** viennent d'une taxonomie **réelle de 257 flags** classés, 12 packs d'agents Sillage prêts.
- Les **dossiers** et le **chatbot** sont **générés par Claude**, ancrés sur ces faits.
- **FullEnrich MCP connecté**, **Sillage REST live**.

## Ce qui est démo/ordres de grandeur (à assumer)
- L'entreprise « Lumen Search », les CA/effectifs et les scores de fit sont synthétisés pour la
  démo. En prod : fit calculé par `score_v2.py` (V2, l'arbre `_data/fit-displacement-tree.json`
  existe), firmo par registre/FullEnrich, minage industrialisé (posts+site+avis).

## Filet de sécurité
- **Le chatbot** est le seul appel réseau live. Si la connexion lâche, il affiche
  « connexion instable, réessayez » (pas de fausse réponse). Répète la question, ou reste sur
  les dossiers (pré-chargés, instantanés).
- Si le port 8970 est pris, le serveur prend le suivant (regarde la ligne « Bricks V4 -> … »).
