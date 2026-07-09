<p align="center">
  <img src="plugins/bricks-v4/front/diggr-logo.svg" alt="DIGGR" width="230" />
</p>

<p align="center">
  <strong>Creusez l'or de vos concurrents.</strong><br/>
  Le moteur de conquête concurrentielle : DIGGR déterre les clients et prospects de vos concurrents — avec la preuve, le bon moment, et les coordonnées vérifiées.
</p>

<p align="center">
  <code>Claude</code> · <code>Sillage</code> · <code>FullEnrich</code>
</p>

---

> **Vos concurrents publient la liste de leurs meilleurs clients.**
> DIGGR la déterre — et vous dit lequel démarcher **maintenant**.

Pendant que la prospection classique brasse tout le marché à froid, DIGGR part d'une évidence : **vos meilleurs futurs clients ne sont pas des inconnus — ils sont déjà chez vos concurrents**, éduqués, budgétés, convaincus par votre marché. DIGGR les identifie à partir de signaux **publics**, avec la **citation source**, et ne remonte que les comptes réellement démarcheables aujourd'hui.

---

## Trois façons de creuser

DIGGR unifie **deux mondes** — le déplacement concurrentiel et l'acquisition — dans une seule interface, autour de trois axes :

| Axe | Verbe | La cible | Le signal type |
|---|---|---|---|
| 🔴 **Captation** | Voler | un client **déjà** chez un concurrent | « Ravis de travailler avec [concurrent] » → client identifié |
| 🔵 **Interception** | Devancer | un prospect qui **évalue** un concurrent | RFP, demande de démo publique, comparatif en cours |
| 🟣 **Acquisition** | Sourcer | un profil **ICP** encore froid | levée de fonds, recrutement clé, migration de stack |

Chaque compte est scoré sur **deux axes séparés, jamais mélangés** : le **FIT** (qualité, IN/BAND/OUT → tier A/B/C) et la **FENÊTRE** (timing — *Ouverte* = agir maintenant).

---

## La stack — chaque outil est indispensable

| Outil | Rôle | Testé en réel |
|---|---|---|
| **Claude** | Raisonnement, dossiers de démarchage **ancrés** (chaque fait sourcé), chatbot qui **s'abstient** plutôt que d'inventer | ✅ |
| **Sillage** | Les signaux d'intention publics : 257 types taxonomisés, minage des clients d'un concurrent depuis ses posts | ✅ minage live prouvé (post → clients cités) |
| **FullEnrich** | Les coordonnées vérifiées, au prix minimal, uniquement quand le compte est chaud | ✅ enrichissement réel → email *DELIVERABLE* |

Retirez un outil, le système tombe : sans Sillage plus de vérité extérieure ; sans Claude du bruit ; sans FullEnrich un dossier envoyé à un fantôme.

---

## Lancer la démo (moins de 2 minutes)

```bash
git clone -b diggr https://github.com/erygy/BRICKS.git
cd BRICKS/plugins/bricks-v4/front
python3 server.py            # → http://127.0.0.1:8970
```

> Sur Mac, double-cliquez simplement **`Lancer DIGGR.command`** (dans `plugins/bricks-v4/front/`) : il démarre le serveur et ouvre le navigateur.
>
> Les clés API (Claude, Sillage, FullEnrich) se posent dans l'écran **Installation**, ou dans `~/.bricks/env`. Sans clé, l'interface tourne quand même (démo pré-chargée) ; avec les clés, le chatbot et la détection de concurrents sont **live**.

**Le script minute par minute** de la démo : [`plugins/bricks-v4/DEMO-RUNBOOK.md`](plugins/bricks-v4/DEMO-RUNBOOK.md).

---

## Les 4 écrans

- **Installation** — un assistant en 3 étapes : profil de l'entreprise → clés API → **l'IA détecte vos concurrents** (à valider).
- **Comptes** — la table de travail : axe, concurrent, FIT (barre + tier), FENÊTRE, signaux. Triable, filtrable par axe.
- **Radar** — le pilotage : où sont les **fenêtres ouvertes**, un board **par concurrent** (ses clients à capter, ses prospects à intercepter, sa faille exploitable), et la **viabilité du motion** (moteur de verdict bayésien).
- **Brief** — le dossier d'un compte sur **un seul écran** : signaux clés, axes stratégiques, membres à contacter, **message pré-rédigé**, leviers — **plus un chatbot ancré** qui répond uniquement sur les faits du dossier et s'abstient sinon (zéro hallucination).

Et une **landing de présentation** prête à l'emploi : [`plugins/bricks-v4/landing/`](plugins/bricks-v4/landing/) (statique, ouvrable directement).

---

## Réel vs démonstration (en toute transparence)

- **Réel** : le minage des clients de concurrents (prouvé live sur Sillage), la taxonomie de **257 signaux**, tous les **dossiers et le chatbot générés par Claude**, l'enrichissement **FullEnrich** (email vérifié *DELIVERABLE*).
- **Démo** : l'entreprise d'exemple, les firmographies et certains scores sont synthétisés pour la présentation. En production, le FIT est calculé par le moteur de scoring signal-natif, les firmo viennent d'un registre / FullEnrich, et le minage est industrialisé.

---

## Structure du projet

```
plugins/bricks-v4/
├── front/            L'application DIGGR (React + htm, serveur Python) — le cockpit
│   ├── index.html    Les 4 écrans + le chatbot ancré
│   ├── server.py     API : seed, chatbot (Claude), détection concurrents, clés
│   └── Lancer DIGGR.command   double-clic → démo
├── landing/          La landing page de présentation (statique)
├── _data/            257 signaux classés, failles concurrent, clients minés (réels)
├── _proofs/          Spec Sillage gelée + preuve de minage live
├── FUSION-V4.md      Le merge des deux moteurs (déplacement × acquisition)
├── V5-MERGE-PLAN.md  Le plan d'architecture
└── DEMO-RUNBOOK.md   Le script de démo (4 min)

plugins/bricks-v2/    Le moteur importé (scoring signal-natif, verdict, fabrique de messages)
```

---

## Preuves

- **Minage live** : 50 posts LinkedIn réels d'un concurrent → 10 clients extraits **avec citation** (`plugins/bricks-v4/_proofs/`).
- **FullEnrich** : clé vérifiée (2500 crédits), enrichissement réel renvoyant un **email vérifié *DELIVERABLE***.
- **Viabilité** : à ~1000 comptes surveillés, la taxonomie produit **~35 signaux forts/jour**, soit un flux quotidien de comptes à démarcher — pas un fichier qui pourrit.

---

<p align="center"><sub>DIGGR — conquête concurrentielle · construit sur un moteur GTM signal-natif · Claude · Sillage · FullEnrich</sub></p>
