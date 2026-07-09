# DIGGR V5 — Plan de merge V2 × V4 (le meilleur des deux mondes)

> But : une seule interface (DIGGR, identité or, l'UI V4) qui réunit **les deux motions** —
> le **DÉPLACEMENT** (V4 : voler les clients/prospects des concurrents) **et la CAPTATION de
> nouveaux prospects** (V2 : sourcing froid + scoring ICP signal-natif + fabrique de messages +
> verdict de viabilité). Merge **strictement constructif, zéro régression**.

## 1. Le principe anti-« mix maladroit »
V2 et V4 ne se concurrencent pas — ils remplissent deux cases d'une même matrice de motion :

| Motion | D'où vient la cible | Apporté par | Axe DIGGR |
|---|---|---|---|
| **Captation de client** | client d'un concurrent | V4 | `client` (rose) |
| **Interception de prospect** | prospect qui évalue un concurrent | V4 | `prospect` (cyan) |
| **Acquisition froide** | sourcing marché (ICP), pas de concurrent | **V2** | `cold` (ardoise) — *aujourd'hui thin, V2 le rend riche* |

→ Le merge = **rendre l'axe `cold` first-class** en y branchant toute la machinerie V2, à côté des
deux axes de déplacement. Un 3ᵉ onglet de lentille « Acquisition » rejoint « Captation / Interception ».

## 2. Ce que V2 importe dans DIGGR (sans rien réécrire)
Import par chemin (`../bricks-v2/tools`), jamais de copie — un fix V2 profite à V5.

| Brique V2 | Rôle en V5 | Point d'entrée UI |
|---|---|---|
| `score_v2.py` + arbre ICP | **le FIT réel** (remplace le fit déterministe de démo) — intervalles, bandes, VOI | barre de fit + tier, partout |
| `messaging_factory.py` | fabrique de messages à ressources fermées (déjà l'esprit du Brief) | bloc « message pré-rédigé » du Brief |
| `verdict.py` | **verdict de viabilité** d'un motion (OUI/NON bayésien) | nouvelle carte « Viabilité » sur le Radar, par axe/concurrent |
| sourcing froid (API gouv/firmo) | peupler l'axe `cold` avec de vraies PME ICP | écran Comptes, provenance `cold` |
| `domain_resolver`, adapters Sillage/FullEnrich | déjà partagés | plomberie |

## 3. Séquence de merge (ordre de moindre régression)
1. **Câbler `score_v2` sur le FIT** (calibrer l'arbre `_data/fit-displacement-tree.json` pour un
   étalement IN/BAND/OUT correct — le point identifié comme « à finir »). Les 3 axes utilisent le
   même moteur, arbres différents (déplacement vs ICP froid).
2. **Brancher `verdict.py`** → carte « Viabilité du motion » (par axe et par concurrent) sur le Radar.
3. **Ouvrir l'axe Acquisition** : sourcing froid ICP → comptes `cold` scorés par l'arbre ICP V2 →
   même Brief, message via `messaging_factory`.
4. **Lentille à 3 axes** (Captation · Interception · Acquisition) + filtres partout.
5. **Gate de non-régression** : `bash bricks-v2/verify.sh` reste 10/10 ; l'UI V4 reste intacte ;
   aucun fichier V1/V2 modifié (sauf mise à jour coordonnée de l'adapter Sillage sur la spec réelle).

## 4. Test réel — EUROBRAND (protocole)
**Contexte capté (eurobrand.fr, 09/07)** : agence de **rebranding / naming / identité visuelle**
(naming+INPI, logo, site, brand book, brand kit). Positionnement : *« aider les repreneurs à
optimiser l'image de l'entreprise qu'ils viennent d'acquérir »*. Zone : FR/DE/IT/ES/CH/BE. ICP :
repreneurs, PME en rebranding, startups, restaurateurs, conseil/patrimoine. Clients réf. : Opus
Group, Neptune LED, Hornet Medical, Tiempo Secure, Buddey, Institution Saint François Sainte Cécile…
Appartient au **Jebabli Group** (branche Jebabli Studio).

**Pipeline complet à faire tourner sur Eurobrand :**
1. **Profil** (onboarding) : la description Eurobrand ci-dessus.
2. **Concurrents** (Claude/Fable) : autres agences de branding/naming servant les repreneurs/PME.
3. **Minage** (Sillage réel) : clients de ces agences (posts LinkedIn → extraction Claude, prouvé live).
4. **Signaux** : appliquer la taxonomie de flags **adaptée au métier agence** (recrutement d'un
   designer interne chez un client d'agence = internalisation ; rebranding annoncé ; levée ;
   nouveau dirigeant repreneur = signal d'or pour Eurobrand).
5. **Interception** : entreprises qui évaluent une agence concurrente (RFP identité visuelle, offre
   d'emploi « brand manager », post « on cherche une agence »).
6. **Acquisition froide (V2)** : repreneurs récents (BODACC cessions) = ICP natif d'Eurobrand.
7. **Scoring FIT+FENÊTRE**, **Brief + message**, **verdict de viabilité**.
8. **Assertion de fiabilité** : chaque affirmation du Brief citée/sourcée, chatbot qui s'abstient,
   zéro hallucination — sur données Eurobrand réelles.

**Note métier importante** : Eurobrand cible les **repreneurs** — c'est le pont naturel avec MemoVAL
(cession/reprise). Le signal-or d'Eurobrand = *« une entreprise vient d'être rachetée »* (BODACC),
pas seulement « client d'un concurrent ». Le test doit intégrer cet axe cession.

## 5. Garanties
- Branche `diggr` sur `erygy/BRICKS` (déjà poussée : push V4 + rebrand DIGGR).
- Chaque étape de merge = commit atomique + vérif preview + `verify.sh` vert.
- Aucune régression sur les 4 écrans DIGGR existants (validés, console 0 erreur).
