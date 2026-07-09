# BRICKS V4 — SPEC UX/UI D'EXÉCUTION

### Le moteur de déplacement concurrentiel, rendu opérable en 4 écrans

> **Nature du document.** Spec d'implémentation, pas de code. Chaque écran est décrit assez
> finement pour être construit fidèlement dans le front existant (`plugins/bricks/front/index.html`,
> React 18 + htm, servi en localhost par `front/server.py`). On **étend** le design system en place,
> on n'en jette rien. Toute règle citée `(rule-name)` renvoie à `ui-ux-pro-max`.
>
> **Ancrage réel.** La table Clay-like existe déjà (`columnType`, `Cell`, chips `s-*`, workspace
> switcher, action-bar flottante, modale settings `/api/settings`, polling 4 s, sélection par `_id`).
> Le modèle de données V4 est fixé : `rivals` (concurrents) → `stolen_targets` (clients de
> concurrents, `provenance="stolen"`) + comptes `provenance="cold"` → `flags` (événements datés) →
> `dossiers` (démarchages). Trois arbres de score : **FIT** (IN/BAND/OUT), **FENÊTRE**
> (OUVERTE/TIÈDE/FERMÉE), **LEVIER** (failles concurrent). Objet miné : `{client, evidence,
> relation, certainty}`.

---

## 0. FONDATIONS TRANSVERSES (à lire avant les 4 écrans)

### 0.1 Extension du design system (tokens à ajouter)

Le fichier `:root` actuel définit `--bg #121212`, `--card #171717`, `--border #2a2a2a`,
`--accent #ff5722`, `--text/#ddd /#888 /#666`, `--radius 12px`, thème clair `#f4f4f2`. On **ajoute**
uniquement des tokens sémantiques — jamais de hex brut dans les composants `(color-semantic)`.

```
/* --- TIERS (qualité prospect, arbre FIT) --- */
--tier-a:      #22c55e;  --tier-a-soft:  rgba(34,197,94,.14);   /* IN,  premium */
--tier-b:      #f59e0b;  --tier-b-soft:  rgba(245,158,11,.14);  /* BAND, à qualifier */
--tier-c:      #6b7280;  --tier-c-soft:  rgba(107,114,128,.14); /* OUT, écarté */

/* --- FENÊTRE (timing, arbre FLAGS) --- */
--window-open: #ff5722;  --window-open-soft: var(--accent-soft);  /* OUVERTE = orange = agir MAINTENANT */
--window-warm: #eab308;  --window-warm-soft: rgba(234,179,8,.12); /* TIÈDE  = cumul en cours */
--window-cold: #3a3a3a;  --window-cold-soft: rgba(255,255,255,.04);/* FERMÉE = veille passive */

/* --- PROVENANCE (froid vs volé) --- */
--prov-stolen: #f43f5e;  --prov-stolen-soft: rgba(244,63,94,.12); /* client d'un concurrent */
--prov-cold:   #64748b;  --prov-cold-soft:   rgba(100,116,139,.12);/* sourcing froid */

/* --- CERTITUDE de l'evidence (minage) --- */
--cert-high:   #4ade80;  --cert-mid: #fbbf24;  --cert-low: #6b7280;

/* --- surfaces additionnelles --- */
--card-2:      #1b1b1b;  /* sous-carte (panneau brief, cellule enrichie) */
--rail:        #151515;  /* rails latéraux (nav entités, chatbot) */
--focus-ring:  rgba(255,87,34,.55);
```

**Règle d'or couleur** : le TIER dit la **qualité** (vert→gris), la FENÊTRE dit l'**urgence**
(orange = maintenant). L'orange BRICKS est **réservé** à « agir » — fenêtre ouverte, CTA primaire,
onglet actif. On ne le gaspille pas en décor `(primary-action, effects-match-style)`.

### 0.2 Système de composants partagés (la bibliothèque V4)

Ces composants apparaissent sur ≥2 écrans. Ils sont spécifiés **une fois** ici, réutilisés partout.
Jamais deux implémentations divergentes du même badge `(consistency, icon-style-consistent)`.

| Composant | Anatomie | États | Règle |
|---|---|---|---|
| **`<TierBadge>`** | pastille ronde 18px + lettre (A/B/C) + label optionnel ; fond `--tier-x-soft`, texte `--tier-x` | A / B / C / `—` (non scoré) | Jamais couleur seule → **toujours la lettre** `(color-not-only)`. Tooltip = score brut + bande. |
| **`<ScoreBar>`** | barre 0–100, hauteur 6px, radius 3px, remplissage dégradé discret ; valeur en tabular-nums à droite | `loading` (shimmer), `valeur`, `null` (piste grise « — ») | `number-tabular` sur la valeur. Fond `--border`, remplissage teinté par bande FIT. Pas d'anim >400ms `(duration-timing)`. |
| **`<WindowPill>`** | pill 999px, point pulsant + texte (Ouverte / Tiède / Fermée) | ouverte (point orange pulsant 0.8s), tiède (point ambre statique), fermée (point gris) | Le **pouls** ne joue que sur OUVERTE, et se coupe sous `prefers-reduced-motion` `(reduced-motion, motion-meaning)`. |
| **`<SignalChip>`** | pill compacte : icône famille + libellé court + date relative (« il y a 3j ») | tier A (bord orange), B (ambre), C (gris), `new` (point plein) | Cliquable → ouvre la preuve du signal. Max 40 car., ellipsis + tooltip `(truncation-strategy)`. |
| **`<ProvenanceTag>`** | micro-tag texte : « Volé à {rival} » (rose) ou « Froid » (ardoise) | stolen / cold | Sur `stolen`, le nom du rival est un lien vers la fiche rival. |
| **`<CertaintyDot>`** | point 8px : vert (haute) / ambre (moyenne) / gris (basse) | 3 niveaux | Accolé à toute donnée minée. Tooltip = le mot + « fondé sur citation ». |
| **`<EvidenceQuote>`** | filet gauche 2px orange + texte italique dim + source | — | Le **cœur anti-hallucination** : toute affirmation minée montre sa citation. Réutilisé écran 3 et 4. |
| **`<StatusChip>`** | **existe déjà** : `.chip.s-*` (pending/running/done/failed/draft/sent/disqualified…) | vocabulaire figé (CONVENTIONS §5) | On **ne crée pas** de nouveau vocabulaire de statut. On réutilise `s-*`. |
| **`<Btn>`** | 3 variantes existantes : `.btn-accent` (primaire), `.btn-ghost` (secondaire), `.btn-toolbar` (dense), `.btn-danger` | hover, active, disabled (opacity .45), loading (spinner + libellé) | 1 seul primaire par écran `(primary-action)`. Loading = disabled + spinner `(loading-buttons)`. |
| **`<SidePanel>`** | tiroir droit 420px, overlay scrim 50%, slide-in depuis la droite 180ms | ouvert / fermé / chargement | Focus trap, Échap ferme, focus rendu au déclencheur `(escape-routes, modal-escape)`. |
| **`<KeyState>`** | ligne clé API : point ok/manquant + label + masque 4 car. + input password | ok / manquante / en cours de save / erreur | **Existe déjà** dans la modale settings. On l'étend écran 1. |

**Icônes** : jeu unique, stroke 1.5px, style outline (Lucide-like en SVG inline). **Zéro emoji
structurel** — les emojis actuels (`🔍 ⚙ ↻ 📭`) sont tolérés en placeholders mais à remplacer par
SVG à la refonte `(no-emoji-icons)`. Familles de signaux = un pictogramme dédié par famille
(recrutement, refonte, budget, départ sponsor, salon…), cohérents en poids de trait.

### 0.3 Navigation globale entre les 4 écrans

**Décision d'architecture** : la topbar 54px reste la constante absolue (brand + workspace pills +
actions à droite). Sous elle, on remplace les `.tabs` par-table actuels par une **navigation primaire
à 4 destinations**, alignée sur le pipeline mental de l'utilisateur, pas sur les tables SQL.

```
┌─ TOPBAR 54px ────────────────────────────────────────────────────────────────┐
│ ■ Bricks   │  ● workspace-A  ○ workspace-B     …     ⌕  ⚙  ☀/☾  ↻   synced 14:2│
├─ NAV PRIMAIRE (barre orange sous l'actif, réutilise .tab) ─────────────────────┤
│  Installation   ·   Comptes (table)   ·   Radar (données)   ·   [Brief: contextuel]│
└────────────────────────────────────────────────────────────────────────────────┘
```

- **Installation** (écran 1) — visible en permanence mais **grisée avec un point d'alerte** tant que
  la config n'est pas complète ; devient un simple accès « réglages » une fois faite.
- **Comptes** (écran 2) — la table Clay, vue par défaut après config. C'est la vue « travail ».
- **Radar** (écran 3) — la vue données évolutive multi-entités (concurrents / flags / tiers).
- **Brief** (écran 4) — **destination contextuelle** : n'apparaît dans la nav que lorsqu'un compte
  est ouvert (deep-link `#/brief/{account_id}`). Sinon on y entre par clic sur une ligne.
  `(deep-linking, nav-state-active)`.

Règles : placement de nav **identique sur toutes les vues** `(navigation-consistency)` ; l'actif est
marqué par la barre orange + poids 600 `(nav-state-active)` ; on **ne mélange pas** sidebar + tabs au
même niveau `(avoid-mixed-patterns)` — la sidebar historique reste désactivée. Chaque écran a une URL
hash pour retour/partage `(deep-linking)`. Retour = restaure scroll + filtres + tri
`(state-preservation)` — critique sur la table (voir §2).

**Le fil conducteur (le parcours global)** : *Installation → l'IA détecte les concurrents → je les
valide → le moteur mine leurs clients dans **Comptes** → le **Radar** me montre où sont les fenêtres
ouvertes → je clique un compte chaud → **Brief** me donne le dossier + je démarche.* Chaque écran doit
rendre évident « où je suis dans ce fil » et « quelle est la prochaine action ».

### 0.4 Micro-interactions transverses (rythme unifié)

Un seul jeu de durées/easing pour tout le produit `(motion-consistency)` :
- Entrées 180ms ease-out ; sorties ~120ms ease-in (sortie plus rapide que l'entrée) `(exit-faster-than-enter)`.
- Hover d'état : 120ms (déjà en place sur `.tab`, `.btn-*`).
- Apparition de lignes/cartes en flux : stagger 30–40ms/item, cap à ~8 items visibles `(stagger-sequence)`.
- **Jamais** animer width/height : `transform`/`opacity` uniquement `(transform-performance, layout-shift-avoid)`.
- Toute animation interruptible, jamais bloquante `(interruptible, no-blocking-animation)`.
- `prefers-reduced-motion` coupe pouls, stagger, slides → remplacés par apparition instantanée `(reduced-motion)`.

---

# ÉCRAN 1 — INSTALLATION / ONBOARDING

## (a) Job-to-be-done & parcours

**JTBD** : « Je viens d'installer Bricks. En un seul passage guidé, je veux décrire mon entreprise
assez précisément pour que le moteur trouve mes vrais concurrents, brancher mes 3 clés API, et voir
le moteur me proposer une première liste de concurrents que je corrige — pour arriver à un radar qui
me ressemble, pas à un formulaire mort. »

**Persona** : dirigeant B2B ou responsable commercial. Pas technique sur les clés API (il faut le
tenir par la main : où cliquer, quoi coller). Impatient : il veut voir de la valeur (les concurrents
détectés) avant d'avoir tout rempli.

**Parcours** :
```
Entrée (1er lancement, aucune config)
 → Étape 1 : PROFIL entreprise (description libre + champs dérivés)
 → Étape 2 : CLÉS API (Anthropic obligatoire, Sillage + FullEnrich pour la veille/enrichissement)
 → Étape 3 : CONCURRENTS DÉTECTÉS (l'IA propose 8–15, je valide/retire/ajoute)  ← le moment "waouh"
 → Sortie : "Lancer le minage" → bascule sur Comptes avec un état de chargement peuplant la table
```
Point de sortie secondaire : quitter à tout moment (config sauvegardée en brouillon,
`form-autosave`), reprendre plus tard depuis la nav « Installation » qui porte le point d'alerte.

**Décision structurante — multi-étapes vs formulaire long ?**
→ **Wizard 3 étapes**, pas un formulaire fleuve. Raison : les 3 blocs ont des natures différentes
(saisie libre / secrets / validation IA), l'étape 3 **dépend** des étapes 1–2 (il faut le profil +
la clé Anthropic pour détecter), et un stepper donne un sentiment de progression + un point de reprise
`(multi-step-progress, progressive-disclosure)`. MAIS chaque étape reste **courte et scannable** —
pas de wizard à 9 écrans. On révèle progressivement, on n'ensevelit pas d'entrée `(progressive-disclosure)`.

## (b) Architecture d'information & hiérarchie visuelle

Conteneur centré `max-width: 720px`, aéré (le seul écran non pleine-largeur — c'est un moment calme,
pas un poste de travail). Hiérarchie : **stepper** (état du parcours) > **titre d'étape** (l'objectif
en 1 phrase) > **le champ actif** > aides contextuelles (dim). Une action primaire par étape, en bas
à droite, collante `(primary-action)`.

## (c) Wireframe décrit — zones & au-dessus de la ligne de flottaison

```
TOPBAR (constante)
────────────────────────────────────────────────────────────────
        ●━━━━━━━━●──────────○           ← STEPPER 3 nœuds, trait orange rempli jusqu'à l'étape active
        Profil    Clés API   Concurrents    (nœud fait = ✓ vert, actif = orange plein, à venir = creux)
────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │  Titre d'étape (18px, 600)                                │   ← AU-DESSUS DE LA FLOTTAISON
  │  Sous-titre explicatif (13px, dim)                        │
  │                                                            │
  │  [ zone de champs de l'étape ]                            │
  │                                                            │
  │  … (scroll interne si besoin, jamais la page) …           │
  ├──────────────────────────────────────────────────────────┤
  │  ← Précédent                         [ Continuer → ]      │   ← barre d'action collante (sticky)
  └──────────────────────────────────────────────────────────┘
```

**Étape 1 — PROFIL** (au-dessus de la flottaison : le grand champ de description)
```
  Décrivez votre entreprise en quelques phrases                    [label visible]
  ┌────────────────────────────────────────────────────────────┐
  │ (textarea 5 lignes) Ce que vous vendez, à qui, ce qui vous  │  ← le champ moteur : ce texte
  │ distingue. Plus c'est précis, meilleurs seront les          │    nourrit la détection concurrents
  │ concurrents détectés.                                       │
  └────────────────────────────────────────────────────────────┘
        └─ hint persistant sous le champ (pas un placeholder seul) (input-labels)

  ── Champs dérivés (l'IA pré-remplit après la description, éditables) ──────
  Secteur / catégorie   [__________]      Marché géo      [France ▾]
  Services / offres     [chips éditables: Design ✕  Branding ✕  + ajouter]
  Positionnement        [__________]      Ton de la marque [Direct ▾]
  ICP (client idéal)    [textarea 2 lignes]
```
Micro-interaction clé : quand la description dépasse ~40 mots, un bouton discret **« Pré-remplir avec
l'IA ✨ »** apparaît sous la textarea ; clic → les champs dérivés se peuplent en cascade
(stagger 40ms), chacun avec un liseré « suggéré » qu'on peut accepter/éditer. C'est le premier signe
que le moteur *comprend*.

**Étape 2 — CLÉS API** (réutilise le composant `<KeyState>` déjà en prod, source `/api/settings`)
```
  Branchez le moteur                                    [3 clés — 1 requise]
  ┌─ ● Anthropic — le cerveau du moteur           REQUISE ──────────────┐
  │   ○ non configurée                                                   │
  │   Comment l'obtenir : console.anthropic.com → API Keys ↗            │
  │   [ coller la clé …………………………… ]  [ Enregistrer ]                   │
  └─────────────────────────────────────────────────────────────────────┘
  ┌─ ● Sillage — les signaux (veille des fenêtres)   recommandée ───────┐
  │   ✓ configurée ····k9x2   [ Remplacer… ]                            │
  └─────────────────────────────────────────────────────────────────────┘
  ┌─ ● FullEnrich — contacts (au moment du démarchage)  optionnelle ────┐
  │   ○ non configurée   [ coller… ] [ Enregistrer ]                    │
  └─────────────────────────────────────────────────────────────────────┘
```
Chaque ligne porte : **rôle en langage produit** (« le cerveau », « les signaux », « les contacts »),
son **niveau d'exigence** (requise/recommandée/optionnelle), l'état (point vert ok / gris manquant),
le **how** + lien direct (déjà dans `envfile.py`), et l'input password. Feedback de validation : au
clic Enregistrer → spinner → **ping réel de la clé** (appel de vérif léger) → point passe au vert +
micro-flash de succès, OU message d'erreur inline « clé refusée par l'API » avec chemin de
récupération `(error-clarity, error-recovery, submit-feedback)`. La valeur n'est jamais réaffichée
(4 derniers car. seulement — comportement déjà en place).

**Étape 3 — CONCURRENTS DÉTECTÉS** (le joyau de l'onboarding)
```
  Voici vos concurrents, corrigez-les                  12 détectés · 9 validés
  Un faux concurrent pollue tout le radar. Gardez les vrais.        [ + ajouter ]
  ┌────────────────────────────────────────────────────────────────────┐
  │ ✓  Algolia          algolia.com          [linkedin ↗]   marché ✓  ✕ │  ← ligne validable
  │ ✓  Devoteam         devoteam.com         [linkedin ↗]   marché ✓  ✕ │
  │ ○  Doofinder        doofinder.com        [linkedin ↗]   marché ?  ✕ │  ← doute → non coché par défaut
  │ …                                                                    │
  └────────────────────────────────────────────────────────────────────┘
```
Chaque concurrent proposé montre : nom, domaine, lien LinkedIn (à vérifier d'un clic), un indice de
confiance de la détection, une case validée/non. Les incertains arrivent **décochés** (l'humain
décide activement). « + ajouter » ouvre un champ inline (nom → l'IA résout domaine+LinkedIn). CTA
primaire : **« Lancer le minage sur {n} concurrents »**, actif seulement si ≥1 validé.

## (d) Inventaire des composants réutilisables
`<Stepper>` (nouveau, 3 nœuds) · `<KeyState>` (existant, étendu avec badge d'exigence) · champ
textarea + hint · chips éditables (services) · `<RivalRow>` validable (préfigure la fiche rival de
l'écran 3) · barre d'action sticky · `<Btn>` accent/ghost.

## (e) Micro-interactions & transitions
- Progression du stepper : le trait orange se **remplit** vers le nœud suivant (transform scaleX), le
  nœud atteint fait un petit ✓ (150ms) `(state-transition, motion-meaning)`.
- Pré-remplissage IA : cascade de champs (stagger 40ms), chacun avec liseré « suggéré » pulsant une
  fois puis stable.
- Validation de clé : bouton → spinner inline → point vert + flash `(success-feedback)`.
- Détection concurrents : squelette de 8–12 lignes fantômes (shimmer) pendant l'appel, remplacées en
  flux `(progressive-loading, loading-chart-analogue)`.

## (f) TOUS les états
| État | Rendu |
|---|---|
| **Vide** (1er lancement) | Wizard étape 1, textarea vide avec hint, CTA « Continuer » désactivé jusqu'à saisie minimale. |
| **En cours** (brouillon repris) | On rouvre à la dernière étape atteinte ; champs restaurés (`form-autosave`) ; nav « Installation » porte un point d'alerte. |
| **Chargement — détection** | Étape 3 : squelette de lignes shimmer + « Analyse de votre marché… » ; CTA désactivé. |
| **Clé invalide** | Ligne clé : bord rouge, message inline « Clé refusée par {API} — vérifiez et recollez » + lien how. Le reste du wizard reste utilisable. |
| **Clé manquante requise** | Impossible de passer étape 3 sans Anthropic : CTA désactivé + tooltip « Anthropic requise pour détecter ». Sillage/FullEnrich manquantes → autorisées mais bandeau « veille/enrichissement indisponibles tant que non branchées ». |
| **Succès** | Étape 3 validée → transition vers Comptes ; toast « Minage lancé sur {n} concurrents » ; la table se peuple (voir écran 2, état chargement). |
| **Partiel** (détection ne trouve que 2 concurrents) | Afficher les 2 + encart « Peu de concurrents détectés — enrichissez votre description ou ajoutez-les manuellement », retour étape 1 en 1 clic. |
| **Erreur réseau détection** | Encart erreur + bouton « Réessayer » ; ne perd pas la saisie `(timeout-feedback, error-recovery)`. |

## (g) Pièges UX spécifiques (règles ui-ux-pro-max)
- **Placeholder-as-label** : bannir. Chaque champ (y compris les clés) a un `<label>` visible ;
  le placeholder n'est qu'un exemple `(input-labels, form-labels)`.
- **Champ password + autofill** : `type="password"`, `autocomplete="off"` sur les clés API (déjà en
  place) — on ne veut pas que le gestionnaire de mdp propose de les stocker ailleurs.
- **Wizard qui piège** : toujours « ← Précédent » sans perte de données ; jamais de reset silencieux
  du stack `(back-stack-integrity, sheet-dismiss-confirm)`.
- **Erreur seulement en haut** : les erreurs de clé s'affichent **sous la clé concernée**, pas dans un
  bandeau global orphelin `(error-placement, error-summary)`.
- **Sur-sollicitation d'entrée** : ne pas demander les 8 champs dérivés d'un coup — la description
  libre d'abord, les champs se dérivent, l'utilisateur corrige `(progressive-disclosure)`.
- **Le moment IA doit être réversible** : toute suggestion (champs dérivés, concurrents) est éditable
  et rejetable — l'IA propose, l'humain dispose (cohérent avec « validation humaine obligatoire »
  du pipeline `DISPLACEMENT-PIPELINE §2`).
- **Contraste des états de clé** : point vert/gris + **texte** (« configurée / manquante »), jamais la
  couleur seule `(color-not-only)`.

---

# ÉCRAN 2 — TABLE INTERACTIVE (Comptes)

> Évolution directe de la table existante. On garde la mécanique éprouvée (`columnType`, `Cell`,
> sélection par `_id`, action-bar flottante, polling 4 s, tri, filtres colonnes, export CSV/XLSX) et
> on la **densifie** avec des colonnes typées métier V4 et des actions groupées réelles.

## (a) Job-to-be-done & parcours

**JTBD** : « Face à ma base de comptes (clients de concurrents + froids), je veux scanner rapidement
lesquels valent mon temps *maintenant* — trier par tier, filtrer sur fenêtre ouverte, voir d'un coup
d'œil qui est volé à qui et où l'enrichissement en est — puis agir en masse (enrichir, générer un
dossier, ouvrir le brief) sans quitter la table. »

**Parcours** :
```
Entrée : depuis Installation (minage lancé) ou nav "Comptes"
 → la table se peuple en live (le miner écrit des lignes → polling les fait apparaître)
 → je trie par Tier, je filtre Fenêtre=Ouverte
 → je sélectionne 20 comptes chauds → action groupée "Générer dossiers"
 → OU je clique une ligne → ouvre le Brief (écran 4)
Sortie : Brief d'un compte, ou export, ou Radar pour la vue agrégée
```

## (b) Architecture d'information & hiérarchie visuelle

La table **est** la page (pleine largeur, la carte occupe tout `.table-zone`). Hiérarchie de lecture
horizontale, ordre des colonnes = ordre de décision :

```
[✓] [#] │ Compte │ Tier │ Score │ Fenêtre │ Provenance │ Signaux │ Statut │ Contact │ …enrichissables
         └gelées┘ └──────── zone de DÉCISION (gelée si scroll horizontal) ────────┘  └─ zone data ─┘
```

- **Colonnes gelées** (`position: sticky; left`) : la case à cocher, le numéro, **et la colonne
  Compte**. On scrolle horizontalement les colonnes enrichies sans perdre l'identité de la ligne
  `(scroll-behavior)`. `Tier`/`Score`/`Fenêtre` idéalement gelées aussi (bloc décision), selon largeur.
- **Densité** : bouton densité (Confortable 40px / Compact 32px / Dense 28px) dans la toolbar. Par
  défaut Compact — c'est un poste de travail, la densité prime `(data-density, touch-density)`.
- Hiérarchie visuelle par **type de cellule**, pas par couleur seule `(visual-hierarchy)`.

## (c) Wireframe décrit

```
NAV: Installation · [Comptes] · Radar
┌─ CARD ────────────────────────────────────────────────────────────────────────────┐
│ TOOLBAR: [⌕ recherche globale…]  [Filtres colonnes] [Vues ▾] [Densité ▾]  [⭳ Export]│  ← flex-wrap
│          filtres actifs: (Fenêtre: Ouverte ✕)(Tier: A,B ✕)      142 / 3 480 lignes   │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ✓ # │Compte▾         │Tier│ Score      │Fenêtre   │Provenance    │Signaux    │Statut │  ← thead sticky
│ ─ ─ │(gelé)          │    │            │          │              │           │       │
│ ☑ 1 │ MadeiraMadeira │ A  │ ▓▓▓▓▓▓░ 82 │ ●Ouverte │ Volé·Algolia │ ⚑3  ⌕2   │ draft │  ← ligne
│ ☑ 2 │ Frasers Group  │ A  │ ▓▓▓▓▓░░ 74 │ ●Ouverte │ Volé·Algolia │ ⚑2       │ new   │
│ ☐ 3 │ Stena Line     │ B  │ ▓▓▓░░░░ 48 │ ○Tiède   │ Volé·Devoteam│ ⚑1       │ ⟳ enrich│ ← cellule live
│ ☐ 4 │ ACME SARL      │ C  │ ▓░░░░░░ 21 │ ·Fermée  │ Froid        │ —         │ pending│
│ …   │                │    │            │          │              │           │       │
├────────────────────────────────────────────────────────────────────────────────────┤
│ FOOTER: 142 / 3 480 rows · 11 columns · tri: Score ↓ · updated 14:23              │
└────────────────────────────────────────────────────────────────────────────────────┘
        ╭──────── ACTION-BAR flottante (si sélection) ────────╮
        │ 20 sélectionnés  Effacer │ Enrichir · Générer dossier · Exporter · Supprimer │
        ╰──────────────────────────────────────────────────────╯
```

Au-dessus de la flottaison : la toolbar + les ~12 premières lignes du bloc décision (Compte/Tier/
Score/Fenêtre). L'utilisateur voit **immédiatement** ses comptes chauds triés.

## (d) Types de colonnes V4 (extension de `columnType`)

`columnType()` infère déjà text/number/email/link/status. On **ajoute des types métier**, déclenchés
par nom de colonne (comme `status` l'est déjà), rendus par un `<Cell>` étendu :

| Colonne | Type | Rendu |
|---|---|---|
| `tier` | `tier` | `<TierBadge>` A/B/C |
| `score` / `*_score` | `score` | `<ScoreBar>` 0–100 + valeur tabulaire |
| `window` / `fenetre` | `window` | `<WindowPill>` Ouverte/Tiède/Fermée |
| `provenance` | `provenance` | `<ProvenanceTag>` (Volé·{rival} rose / Froid ardoise) |
| `signals` / `flags` | `signals` | grappe de `<SignalChip>` (max 3 visibles + « +N ») |
| `certainty` | `certainty` | `<CertaintyDot>` + mot |
| `status` / `*_status` | `status` | `.chip.s-*` **(existant, inchangé)** |
| `contact` | `enrich` | vide→bouton « enrichir » ; en cours→cellule live ; rempli→email masqué + `<CertaintyDot>` |
| `email` / `domain` / url | existants | inchangés |

Le tri respecte l'ordre sémantique : Tier A>B>C, Fenêtre Ouverte>Tiède>Fermée (pas alphabétique).
`compareCell` gagne un comparateur par type. `sortable-table` + `aria-sort`.

## (e) Micro-interactions & transitions
- **Mise à jour live** (le miner peuple la table pendant qu'on la regarde) : le polling 4 s existe
  déjà. On l'améliore : les **nouvelles lignes** entrent avec un flash orange doux (background pulse
  1×, 600ms) puis se fondent — l'œil voit « ça bouge » sans reflow `(fade-crossfade, layout-shift-avoid)`.
  Le compteur d'onglet/footer s'incrémente. **Jamais** de saut de scroll pendant qu'on lit
  `(state-preservation)` : les insertions se font sans déplacer la ligne survolée.
- **Cellule d'enrichissement en cours** : sur une cellule `contact` en `⟳ enrich`, un shimmer + point
  ambre pulsant ; à la résolution → crossfade vers l'email masqué + `<CertaintyDot>` `(fade-crossfade)`.
- **Sélection** : ligne `.selected` (fond `--accent-soft`, déjà en place) ; l'action-bar monte
  (`rise` 180ms, déjà en place).
- **Tri** : flèche ↑/↓ orange sur l'en-tête trié (déjà en place) ; le re-tri anime les lignes vers
  leur nouvelle position seulement si <400ms sinon snap `(duration-timing)`.
- **Hover ligne** : `--hover` (déjà). Sur hover, une **poignée d'actions rapides** (⋯) apparaît en fin
  de ligne : « Ouvrir le brief · Enrichir · Générer dossier » — sans quitter la table.

## (f) TOUS les états
| État | Rendu |
|---|---|
| **Vide — pas de workspace** | État existant : « Bricks is not initialized » + commande. Inchangé. |
| **Vide — pas de table** | « Aucun compte encore. Lancez le minage » + CTA renvoyant à Installation §3. (remplace le `/bricks:find` brut par une action UI) |
| **Chargement initial** | Squelette de ~15 lignes (barres shimmer par colonne, respectant la largeur typée) — **pas** un spinner central `(progressive-loading, virtualize-lists)`. |
| **Peuplement live (minage actif)** | Bandeau discret sous la toolbar : « Minage en cours — {n} comptes trouvés · {rival} en cours ⟳ » ; les lignes arrivent en flux. Non bloquant. |
| **Filtre → 0 résultat** | Ligne pleine largeur « Aucune ligne ne correspond aux filtres » (existant) + bouton « Effacer les filtres ». |
| **Cellule enrichie — succès** | email masqué (`j***@acme.com`) + `<CertaintyDot>` vert + tooltip source. |
| **Cellule enrichie — échec/introuvable** | `.chip.s-not_found` « introuvable » ; action « réessayer » au hover. |
| **Action groupée en cours** | boutons action-bar → disabled + spinner + libellé (« Enrichissement… 8/20 ») ; barre de progression fine sur l'action-bar `(loading-buttons, multi-step-progress)`. |
| **Suppression** | confirmation en 2 temps (déjà : « Delete » → « Confirm delete (N) ») ; **ajouter un toast « Undo » 5 s** `(undo-support, confirmation-dialogs)`. |
| **Erreur** | `.error-banner` (existant) sous la topbar ; l'action échouée reste réversible. |
| **Grande table (>1000 lignes)** | Virtualisation des lignes ; le tri/filtre restent sur l'ensemble ; le footer montre « X / total » `(virtualize-lists, large-dataset)`. |

## (g) Pièges UX spécifiques (règles ui-ux-pro-max)
- **Reflow au polling** : le piège n°1. Les updates 4 s ne doivent JAMAIS réordonner/scroller sous les
  doigts. Insertions par `_id`, position de scroll préservée, ligne survolée stable `(content-jumping,
  reduce-reflows, state-preservation)`. La sélection est déjà keyée par `_id` — on préserve ça.
- **Couleur seule pour le tier/fenêtre** : toujours lettre (A/B/C) + mot (Ouverte/Tiède/Fermée)
  `(color-not-only, pattern-texture)`. Un daltonien doit lire le tableau.
- **Chiffres non tabulaires** : scores, comptes de signaux, dates → `font-variant-numeric: tabular-nums`
  (déjà la convention) `(number-tabular)`.
- **En-têtes qui perdent le contexte au scroll** : `thead` sticky (déjà) ; + colonne Compte gelée à
  gauche `(scroll-behavior)`.
- **Sur-largeur des cellules texte** : `max-width` + ellipsis + `title` (déjà en place) — mais fournir
  la valeur complète au survol `(truncation-strategy)`.
- **Action destructive collée aux actions normales** : dans l'action-bar, « Supprimer » est
  visuellement **séparé** (à droite, rouge) des actions constructives `(destructive-emphasis,
  destructive-nav-separation)`.
- **Densité qui casse le tap** : en mode Dense (28px), garder ≥ 44px de zone cliquable réelle sur la
  case/les actions via hit-area étendue `(touch-target-size)`.
- **Filtres invisibles** : les filtres actifs sont affichés en **chips retirables** dans la toolbar
  (pas seulement un compteur), pour que l'utilisateur sache pourquoi il voit 142/3480 `(empty-nav-state
  -analogue, error-clarity)`.

---

# ÉCRAN 3 — RADAR (vue données évolutive multi-entités)

> Là où la table (écran 2) est **une** liste de comptes, le Radar présente les **entités liées** du
> modèle V4 — concurrents (`rivals`), companies (clients volés + froids), signaux (`flags`), tiers,
> modèle de prospection — et surtout **leurs relations** : un concurrent → ses clients → les signaux
> d'un client. C'est la vue « d'où viennent mes comptes et où se passe l'action ».

## (a) Job-to-be-done & parcours

**JTBD** : « Je veux comprendre mon terrain de chasse : quel concurrent est mon meilleur gisement,
quels de ses clients sont en fenêtre ouverte, et pourquoi. Je veux naviguer de haut en bas
(concurrent → client → signal → preuve) et changer d'angle de vue (par tier ? par concurrent ? liste
filtrable ?) selon ce que je cherche. »

**Parcours (navigation entre entités liées)** :
```
Entrée : nav "Radar"
 vue par défaut = BOARD PAR CONCURRENT (rival lanes)
 → je clique un concurrent (Algolia) → panneau/drill : ses clients minés, ses failles du jour
   → je clique un client (MadeiraMadeira) → ses signaux datés + son evidence de minage
     → je clique un signal → sa preuve (citation/source) + "ce compte est démarcheable car…"
       → "Ouvrir le brief" → écran 4
Bascules de vue (segmented control) :
 [ Par concurrent ]  [ Kanban par fenêtre ]  [ Par tier ]  [ Liste ]
Sortie : Brief d'un compte, ou retour Comptes (table)
```

**Décision — quelles vues ?** Trois vues complémentaires, une bascule (segmented control), état
mémorisé par workspace `(state-preservation)` :
1. **Par concurrent (défaut)** — des *lanes* horizontales, une par `rival`, chacune listant ses clients
   (cards compactes) triés par chaleur de fenêtre. Répond à « quel rival est le meilleur gisement ».
2. **Kanban par fenêtre** — 3 colonnes Ouverte / Tiède / Fermée. Répond à « qu'est-ce qui est chaud
   *maintenant*, tous concurrents confondus ». C'est la vue action.
3. **Par tier** — 3 colonnes A / B / C (qualité fit). Répond à « où est la qualité ».
4. **Liste filtrable** — repli vers une table dense (renvoie à l'écran 2 avec un préfiltre) pour qui
   veut tout voir à plat.

## (b) Architecture d'information & hiérarchie visuelle

Modèle mental = **arbre à 3 niveaux** : `Concurrent ▸ Client ▸ Signal ▸ (preuve)`. La navigation est
un **drill-down avec fil d'Ariane** persistant, jamais une perte de contexte `(breadcrumb-web,
drill-down-consistency)`.

```
Radar ▸ Algolia ▸ MadeiraMadeira ▸ ⚑ "refonte du search annoncée"      ← breadcrumb cliquable à chaque niveau
```

Hiérarchie visuelle : niveau 1 (concurrent) = titre de lane + métriques ; niveau 2 (client) = card
avec Tier/Fenêtre/Score ; niveau 3 (signal) = `<SignalChip>` daté ; niveau 4 (preuve) =
`<EvidenceQuote>`. L'urgence (fenêtre ouverte = orange) attire l'œil en premier `(visual-hierarchy)`.

## (c) Wireframe décrit — vue « Par concurrent » (défaut)

```
NAV: Installation · Comptes · [Radar]
┌──────────────────────────────────────────────────────────────────────────────────┐
│ [Par concurrent] [Kanban fenêtre] [Par tier] [Liste]        ⌕ filtrer   ⚑ 34 flags/j│  ← segmented + filtre
│ Radar › tous les concurrents                                                        │  ← breadcrumb
├──────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ ALGOLIA ────────────────── 148 clients · 12 ouverts · gisement ▓▓▓▓▓ ──[détail]┐│  ← LANE (rival)
│ │ ┌MadeiraMadeira─┐ ┌Frasers Group─┐ ┌Hershey──────┐ ┌+ 145 clients──────────────┐││
│ │ │ A  ●Ouverte   │ │ A  ●Ouverte  │ │ B  ○Tiède   │ │ (scroll horizontal)       │││  ← cards clients
│ │ │ ⚑3  82        │ │ ⚑2  74       │ │ ⚑1  55      │ │                           │││    triées par chaleur
│ │ └───────────────┘ └──────────────┘ └─────────────┘ └───────────────────────────┘││
│ └──────────────────────────────────────────────────────────────────────────────────┘│
│ ┌─ DEVOTEAM ───────────────── 96 clients · 4 ouverts · gisement ▓▓▓░░ ──────[détail]┐│
│ │ ┌Stena Line─────┐ ┌Down España───┐ …                                              ││
│ └──────────────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────────┘
```
Au-dessus de la flottaison : le segmented control + la 1re lane (le meilleur gisement en haut, lanes
triées par densité de fenêtres ouvertes). L'utilisateur voit **où chasser** en 2 secondes.

**Drill niveau 2 — clic sur un concurrent** → la lane s'étend OU un `<SidePanel>` droit s'ouvre :
```
┌─ ALGOLIA — le gisement ────────────────────────────[✕]┐
│ 148 clients · 12 fenêtres ouvertes · verdict: bon      │  ← métriques rival (verdict.py par concurrent)
│ ── Failles du concurrent (aujourd'hui) ──────────────  │
│  ⚠ Hausse de prix annoncée (levier)   il y a 2j        │  ← taxonomie failles → LEVIER
│  ⚠ Départs dans l'équipe support       il y a 5j       │
│ ── Ses clients en fenêtre ouverte (12) ──────────────  │
│  • MadeiraMadeira   A  ⚑3   [ouvrir brief →]           │
│  • Frasers Group    A  ⚑2   [ouvrir brief →]           │
│  …                                                     │
└────────────────────────────────────────────────────────┘
```

**Drill niveau 3 — clic sur un client** → panneau signaux datés (préfigure l'écran 4) :
```
MadeiraMadeira ▸ signaux
 ⚑ "Refonte du search annoncée"   TIER A · il y a 3j   [voir preuve ▾]
     └ « …nous lançons un chantier de refonte de notre moteur de recherche… »  — LinkedIn, 06/07
 ⚑ "Recrutement Head of Product"  TIER B · il y a 8j   [voir preuve ▾]
 ⌕ Comité cartographié (2)                              [ouvrir le brief complet →]
```

## (d) Inventaire des composants réutilisables
`<RivalLane>` (nouveau) · `<ClientCard>` (Tier+Fenêtre+Score+compteur signaux) · `<SidePanel>`
(partagé) · `<SignalChip>` + `<EvidenceQuote>` (partagés, cœur écran 4) · `<Breadcrumb>` (nouveau) ·
`<SegmentedControl>` (nouveau, vues) · `<GisementBar>` (= `<ScoreBar>` réétiqueté). Le **Kanban** et
le **Par tier** réutilisent `<ClientCard>` dans des colonnes.

## (e) Micro-interactions & transitions
- **Drill-down** : transition d'échelle (le concurrent cliqué grandit / le panneau slide depuis la
  droite), continuité spatiale — on comprend qu'on *entre* dans l'entité `(shared-element-transition,
  continuity, hierarchy-motion)`. Retour = animation inverse `(navigation-direction)`.
- **Bascule de vue** (segmented) : crossfade du contenu, le control glisse son indicateur orange
  `(fade-crossfade)`.
- **Nouveau flag en live** : sur une `<ClientCard>`, un `<SignalChip>` neuf apparaît avec un point
  plein orange + micro-pouls 1× ; le compteur ⚑ s'incrémente `(motion-meaning)`.
- **Kanban** : les cartes qui changent de fenêtre (Tiède→Ouverte quand un cumul bascule) glissent de
  colonne avec un flash — l'utilisateur *voit* un compte devenir chaud.
- Drag optionnel (déplacer une carte = changer un statut manuel) : seuil de déplacement avant drag
  `(drag-threshold)`, affordance claire `(swipe-clarity)`.

## (f) TOUS les états
| État | Rendu |
|---|---|
| **Vide — aucun concurrent validé** | « Le radar est vide. Validez vos concurrents » + CTA → Installation §3. |
| **Vide — concurrents validés, minage pas fini** | Lanes avec squelette de cards + « Minage en cours… {rival} ⟳ ». |
| **Chargement drill** | Panneau : squelette de la liste clients/signaux `(loading-chart)`. |
| **Concurrent sans client miné** | Lane avec encart « Aucun client identifié pour {rival} — sources épuisées ou concurrent atypique » + « relancer le minage ». |
| **Client sans signal** | Card en fenêtre Fermée, grisée ; drill montre « Aucun signal — sous veille passive ». Pas de card fantôme muette `(empty-data-state)`. |
| **Signal sans preuve exploitable** | `<SignalChip>` marqué « preuve faible » (`<CertaintyDot>` basse) — on n'affiche jamais un signal sans dire ce qui le fonde `(source-grounding)`. |
| **Quota Sillage épuisé** | Bandeau d'avertissement (non bloquant) : « Veille en pause — quota Sillage atteint. Les fenêtres affichées datent de {date} ». Les données restent lisibles `(offline-support, network-fallback)`. |
| **Succès (fenêtre ouverte détectée)** | Card remonte en tête de lane / colonne Ouverte, flash orange, `<WindowPill>` pulse. |
| **Erreur poll** | Icône de sync en erreur dans la topbar + tooltip ; dernière donnée conservée avec horodatage. |

## (g) Pièges UX spécifiques (règles ui-ux-pro-max)
- **Perte de contexte au drill** : breadcrumb obligatoire à chaque niveau, back restaure l'état exact
  `(drill-down-consistency, breadcrumb-web, back-behavior)`.
- **Confondre fit et fenêtre** (le piège de fusion V4) : le Tier (qualité) et la Fenêtre (timing) sont
  **deux badges distincts**, jamais fondus en un score unique — traduit visuellement le « 2 arbres,
  2 scores » de `FUSION-V4 §0`. Ne jamais afficher un « score global » trompeur.
- **Signal sans preuve = hallucination perçue** : tout signal expose sa citation via `<EvidenceQuote>`
  au drill — non négociable `(source-grounding)`.
- **Kanban à colonnes qui débordent** : virtualiser chaque colonne, ne pas rendre 400 cartes
  `(large-dataset, virtualize-lists)`.
- **Trop d'infos par card** : la `<ClientCard>` porte 4 signaux max (Tier, Fenêtre, Score, ⚑N) — le
  reste au drill `(data-density)`.
- **Nav mixte** : le segmented control est le SEUL sélecteur de vue ; pas de doublon avec des tabs
  `(avoid-mixed-patterns)`.
- **Cibles tactiles des cards** : chaque card ≥ 44px de haut, actions au hover avec hit-area étendue
  `(touch-target-size, no-precision-required)`.

---

# ÉCRAN 4 — BRIEF ENTREPRISE (le joyau, 1 seul écran)

> Pour UN compte, tout ce qu'il faut pour décider et démarcher, sur un écran, sans scroll infini.
> 7 blocs denses + un chatbot ancré. C'est l'aboutissement du pipeline : `fit × fenêtre × levier`
> matérialisés, prêts à devenir un `dossier`. Référence de densité maîtrisée : le style « MemoVAL ».

## (a) Job-to-be-done & parcours

**JTBD** : « J'ouvre le brief d'un compte chaud. En un écran, je veux comprendre POURQUOI c'est le
moment (signaux), QUI attaquer (membres clés + justification), AVEC QUEL ANGLE (levier + message
pré-rédigé), et pouvoir creuser en langage naturel (chatbot) sans perdre le contexte — puis lancer le
démarchage. Chaque affirmation doit être traçable à une preuve. »

**Parcours** :
```
Entrée : clic sur une ligne (écran 2) / une card (écran 3) / deep-link #/brief/{id}
 → lecture en Z : signaux (pourquoi maintenant) → membres clés (qui) → levier + message (comment)
 → je vérifie une affirmation → je clique sa source (scroll/highlight vers la preuve)
 → je pose une question au chatbot ("depuis quand sont-ils clients d'Algolia ?")
   → réponse ancrée + citation cliquable
 → j'édite le message pré-rédigé → "Générer le dossier" / "Enrichir le comité" (gate VOI)
Sortie : dossier créé (statut draft→ écran 2), ou retour à la vue d'origine (état préservé)
```

## (b) Architecture d'information & hiérarchie visuelle

**Décision de layout — 7 blocs sans surcharge** : grille **bento asymétrique 2 colonnes** dans une
zone scrollable, + un **chatbot en rail droit persistant** (ne scrolle pas avec le contenu). En-tête
de compte collant en haut. Priorité : ce qui déclenche l'action (signaux + levier + message) occupe la
colonne large et le haut ; le contexte (chiffres, membres) en second.

Ordre de priorité des 7 blocs (= ordre de lecture, du plus décisionnel au plus contextuel) :
1. **Signaux clés** (pourquoi maintenant) — haut, pleine largeur de la colonne principale.
2. **Message clé pré-rédigé** (le livrable) — grand, colonne principale, éditable.
3. **Leviers identifiés** (l'angle : failles concurrent) — à côté/sous les signaux.
4. **Membres clés + justification** (qui, et pourquoi eux).
5. **Axes stratégiques** (l'angle business du compte).
6. **Chiffres clés** (taille, ancienneté relation, secteur).
7. **Chatbot** — rail droit, toujours là.

## (c) Wireframe décrit

```
NAV: … · Brief (contextuel)
┌─ EN-TÊTE COMPTE (sticky) ──────────────────────────────────────────────────────────┐
│ ← MadeiraMadeira   A ●Ouverte   Volé·Algolia   score 82        [Enrichir] [Générer ▸]│  ← identité + CTA primaire
├──────────────────────────────────── SCROLL ZONE ────────────────────┬─ CHATBOT RAIL ┤
│ ┌─ ① SIGNAUX CLÉS ─── pourquoi maintenant ──────────────┐ ┌─ ③ LEVIERS ─┐│ ┌───────────┐│
│ │ ⚑ Refonte du search annoncée   A · il y a 3j  [preuve]│ │ Hausse prix │││ Poser une  ││
│ │ ⚑ Recrutement Head of Product  B · il y a 8j  [preuve]│ │ Algolia →   │││ question   ││
│ │ ⚑ Budget évoqué en post        B · il y a 8j  [preuve]│ │ "vous mérit-│││ sur ce     ││
│ └───────────────────────────────────────────────────────┘ │ ez mieux"   │││ compte     ││
│ ┌─ ② MESSAGE CLÉ (éditable) ────────────────────────────┐ │ [preuve]    │││───────────  ││
│ │ Objet: Votre refonte search — un angle                │ └─────────────┘││ ◦ "depuis  ││
│ │ ─────────────────────────────────────────────────      │ ┌─ ⑤ AXES ────┐││ quand      ││
│ │ Bonjour {prénom}, j'ai vu que MadeiraMadeira…          │ │ · Scale LATAM││ client     ││
│ │ [chaque variable {..} et chaque fait est traçable]     │ │ · Perf mobile│││  d'Algolia?"││
│ │                                     [éditer] [copier]  │ └─────────────┘││            ││
│ └───────────────────────────────────────────────────────┘ ┌─ ⑥ CHIFFRES ┐││ [réponse   ││
│ ┌─ ④ MEMBRES CLÉS ──────────────────────────────────────┐ │ ~500 empl.  │││  ancrée +  ││
│ │ 👤 J. Silva — Head of Product   [pourquoi lui ▾]       │ │ client 3 ans│││  citation] ││
│ │    « sponsor probable de la refonte » + evidence       │ │ e-commerce  │││            ││
│ │ 👤 M. Costa — CTO               [pourquoi lui ▾]       │ └─────────────┘││ [___champ__]││
│ └───────────────────────────────────────────────────────┘                ││    [envoyer]││
└─────────────────────────────────────────────────────────────────────────┴─────────────┘
```

**Au-dessus de la flottaison** : l'en-tête compte (identité + CTA), le bloc ① Signaux (le « pourquoi
maintenant »), le début du ② Message, et le rail chatbot. L'utilisateur sait en 3 secondes : *qui,
pourquoi maintenant, et il a déjà un message*.

**Où vit le chatbot ?** → **rail droit persistant** (largeur ~340px, pleine hauteur sous l'en-tête,
scroll indépendant). Pas une modale (qui masquerait le brief), pas un bloc dans le flux (qui
scrollerait hors de vue). Le rail reste ancré : on lit le brief à gauche, on interroge à droite,
les deux visibles. Sur écran étroit (<1100px), il se replie en bouton flottant « Demander » qui ouvre
un `<SidePanel>` `(adaptive-navigation, progressive-disclosure)`.

**Comment relier une réponse à sa preuve ?** Mécanique unique partout dans l'écran :
- Chaque fait affiché (signal, chiffre, justification de membre) porte un lien **[preuve]** discret.
- Clic → la réponse **surligne + scrolle** vers le `<EvidenceQuote>` correspondant (citation + source
  + date), soit inline (déclencheur d'un accordéon « voir preuve »), soit dans un mini-popover ancré.
- Le **chatbot** répond toujours avec ≥1 citation cliquable en pied de réponse (« Source : LinkedIn,
  06/07 »), au même format `<EvidenceQuote>`. Si aucune preuve → il **s'abstient** explicitement
  (« Je n'ai pas de trace fiable pour l'affirmer ») plutôt que d'inventer. C'est la garde
  anti-hallucination, cohérente avec le principe « ressources fermées » de `messaging_factory`
  (`FUSION-V4 §2`) `(source-grounding)`.

## (d) Inventaire des composants réutilisables
`<AccountHeader>` (sticky, identité + CTA) · `<SignalChip>` + `<EvidenceQuote>` (partagés) ·
`<TierBadge>`/`<WindowPill>`/`<ScoreBar>`/`<ProvenanceTag>` (partagés) · `<MessageCard>` (nouveau,
éditable, variables traçables) · `<LeverCard>` (nouveau, faille→angle, posture aspirine) ·
`<MemberCard>` (nouveau, personne + justification dépliable + evidence) · `<StatCard>` (chiffres) ·
`<ChatRail>` (nouveau) · `<ProofLink>` + `<ProofPopover>` (nouveaux, la mécanique de traçabilité).

## (e) Micro-interactions & transitions
- **Entrée dans le brief** : depuis une card/ligne, transition d'élément partagé (le nom du compte
  grandit vers l'en-tête) `(shared-element-transition, continuity)`.
- **[preuve] → surlignage** : la citation cible se surligne (background orange soft, 800ms puis fond),
  scroll fluide `(motion-meaning)`.
- **Chatbot** : bulle utilisateur (droite) → indicateur « réflexion » (3 points) → réponse en flux
  (streaming), citation apparaît en pied. Réponse ancrable : clic sur la citation → surligne la preuve
  dans le brief à gauche (lien bidirectionnel).
- **Édition message** : passage lecture→édition inline (le bloc devient textarea, variables restent
  colorées) ; « copier » → flash « copié » 1,5 s `(success-feedback)`.
- **« Pourquoi lui ▾ »** : accordéon qui déplie la justification + evidence du membre (150ms).
- **Générer le dossier** : bouton primaire → spinner → toast succès + le compte passe `s-draft` (visible
  au retour sur la table). Envoi reste **gated** (dry-run par défaut, cohérent `outreach_send`).

## (f) TOUS les états
| État | Rendu |
|---|---|
| **Chargement** | Squelette bento : 7 cartes fantômes (shimmer) + rail chatbot avec « Chargement du contexte… ». |
| **Compte froid / hors-fenêtre** | Bandeau haut « Fenêtre fermée — pas de fait de timing récent ». Blocs Signaux/Levier montrent « rien de récent » ; Message pré-rédigé **désactivé** avec explication « pas de flag = pas d'accroche datée » (respecte : pas de démarchage sur bruit, `DISPLACEMENT-PIPELINE §4`). |
| **Levier absent** (fenêtre ouverte mais concurrent sans faille détectée) | `<LeverCard>` : « Aucune faille concurrent détectée — angle générique. Le message s'appuie sur le signal seul. » |
| **Comité non cartographié** | Bloc Membres : « Comité non enrichi » + bouton « Cartographier (0,25 crédit) » — gate VOI explicite, coût affiché avant clic `(confirmation-dialogs)`. |
| **Enrichissement en cours** | Membres : cards shimmer + « Recherche du comité… ». |
| **Message généré — succès** | `<MessageCard>` rempli, variables résolues, chaque fait avec [preuve]. |
| **Chatbot — réponse ancrée** | Réponse + `<EvidenceQuote>` cliquable. |
| **Chatbot — abstention** | « Je n'ai pas de trace fiable pour répondre. Ce que je sais : … » — jamais d'invention `(source-grounding)`. |
| **Chatbot — hors-sujet/hors-périmètre** | « Je ne réponds que sur ce compte » — recentre. |
| **Partiel** (certains blocs vides) | Chaque bloc gère son propre vide sans casser la grille ; jamais de carte muette `(empty-data-state)`. |
| **Erreur génération message** | Message : encart erreur + « Réessayer », le reste du brief reste lisible `(error-recovery)`. |
| **Succès dossier** | Toast + statut `s-draft` + CTA devient « Voir le dossier ». |

## (g) Pièges UX spécifiques (règles ui-ux-pro-max)
- **Surcharge des 7 blocs** : bento asymétrique + priorité stricte ; chaque bloc a **une** idée ; le
  détail est en accordéon/preuve, pas déballé d'emblée `(progressive-disclosure, whitespace-balance,
  data-density)`. Ne jamais mettre 7 blocs de poids égal — la hiérarchie doit dire quoi lire d'abord.
- **Chatbot qui vole la vedette** : il est ancré à droite, ne masque jamais le brief, ne prend pas le
  focus au chargement `(modal-vs-navigation, focus-management)`.
- **Réponse non traçable** : toute affirmation (brief ou chatbot) → [preuve] ou abstention. C'est LE
  piège fatal de crédibilité de cet écran `(source-grounding, error-clarity)`.
- **Dénigrement dans le levier** : le `<LeverCard>` applique la posture aspirine (« vous méritez
  mieux », jamais « le concurrent est mauvais ») — contrainte produit, pas cosmétique (`FUSION-V4 §4`).
- **Message qui semble figé** : rendre l'édition évidente (affordance [éditer] visible), variables
  colorées, copier en 1 clic `(system-controls, primary-action)`.
- **En-tête qui disparaît au scroll** : sticky, garde identité + CTA toujours accessibles
  `(persistent-nav, fixed-element-offset)`.
- **Focus & clavier** : ordre de tabulation = en-tête → blocs dans l'ordre de lecture → chatbot ;
  Échap dans le chatbot ne quitte pas le brief `(keyboard-nav, escape-routes, focus-on-route-change)`.
- **Contraste des citations** : `<EvidenceQuote>` en texte dim mais ≥ 4.5:1 sur `--card-2`
  `(color-accessible-pairs, contrast-readability)`.

---

## ANNEXE — Récapitulatif de la bibliothèque de composants partagés

| Composant | Écrans | Nouveau/Existant |
|---|---|---|
| Topbar (brand + workspace pills + actions) | tous | existant, conservé |
| Nav primaire (4 destinations, barre orange) | tous | évolution de `.tabs` |
| `<TierBadge>` A/B/C | 2,3,4 | nouveau |
| `<ScoreBar>` 0–100 | 2,3,4 | nouveau |
| `<WindowPill>` Ouverte/Tiède/Fermée | 2,3,4 | nouveau |
| `<ProvenanceTag>` Volé/Froid | 2,3,4 | nouveau |
| `<SignalChip>` + `<EvidenceQuote>` | 3,4 | nouveau (cœur anti-hallu) |
| `<CertaintyDot>` | 2,3,4 | nouveau |
| `<StatusChip>` `.chip.s-*` | 2,4 | **existant, vocabulaire figé** |
| `<KeyState>` | 1 | existant, étendu |
| `<Btn>` accent/ghost/toolbar/danger | tous | existant |
| `<SidePanel>` (tiroir droit, focus trap) | 3,4 | nouveau |
| Action-bar flottante | 2 | existant, actions enrichies |
| `<Stepper>` | 1 | nouveau |
| `<SegmentedControl>` (vues) | 3 | nouveau |
| `<Breadcrumb>` (drill entités) | 3 | nouveau |
| `<RivalLane>` / `<ClientCard>` | 3 | nouveau |
| `<MessageCard>`/`<LeverCard>`/`<MemberCard>`/`<StatCard>` | 4 | nouveau |
| `<ChatRail>` + `<ProofLink>`/`<ProofPopover>` | 4 | nouveau |

**Invariants de cohérence (à ne jamais casser)** :
1. Orange = « agir/maintenant » uniquement (fenêtre ouverte, CTA primaire, actif).
2. Tier = qualité (vert→gris) ; Fenêtre = urgence (orange) — **jamais** fondus en un score unique.
3. Toute donnée minée porte sa `<EvidenceQuote>` ou s'abstient — pas d'affirmation sans preuve.
4. Vocabulaire de statut = `s-*` existant, jamais réinventé.
5. Couleur jamais seule : toujours + lettre/mot/icône.
6. Polling live ne provoque jamais reflow/saut de scroll.
7. Un seul CTA primaire par écran ; destructif toujours séparé.
8. Un seul rythme de motion ; `prefers-reduced-motion` respecté partout.
```
