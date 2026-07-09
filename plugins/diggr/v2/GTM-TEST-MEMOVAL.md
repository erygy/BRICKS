# GTM-TEST MEMOVAL — le test de viabilité en 14 jours (exécutable dès demain)

> Protocole issu des agents BUSINESS + GROWTH (08/07, seuils codés dans
> `messaging/verdict-config.json`), outillé par la chaîne V2 complète.
> Objectif : à J+14, un VERDICT — OUI / NON / il manque N contacts — plus,
> si OUI, les premiers clients en pipeline. Budget cash : **~74 € les 2 vagues**.

## Le dispositif expérimental

| Population | Traitement | Rôle |
|---|---|---|
| **26 IN** | Séquence complète : lettre papier + 3 emails + 2-3 appels + SMS | Le cœur du test |
| **top-90 BAND** (triés par score) | Email seul, 2 bras A/B d'axe (45/45) | Test du message + comparaison |
| **100 OUT** | Intouchés | Témoin passif du scoring |

Le méta-test (l'expérience n°1) : **IN doit battre BAND ≥2×** en réponses
positives — c'est le test du moteur de scoring lui-même, pas seulement de
MemoVAL. `verdict.py` calcule P(IN bat témoin) en continu.

## Calendrier (contraintes réelles : 14/07 férié, congés bâtiment ~25/07)

- **J1 · mer 09/07 (hackathon)** — Matin : délivrabilité (mail-tester ≥9/10,
  seeds Gmail/Outlook/**Orange**) · FullEnrich sur 26 IN + top-90 BAND
  (~116 crédits) · push Sillage (contingent) · récupérer les **fixes** des
  26 IN (annuaire-entreprises/PagesJaunes/site — 1 h, le canal le plus
  rentable). Après-midi : canari 10 emails BAND (jamais sur les IN) +
  **POSTER les 26 lettres « Personnel & Confidentiel »** (enveloppe
  manuscrite, timbre réel, 1 page signée main ; 40-60 €).
- **J2 · jeu 10/07** — email #1 IN lot A (13, fenêtre 7h50-9h30) + 12 BAND.
- **J3 · ven 11/07** — email #1 IN lot B + 12 BAND. Répondre aux réponses < 1 h.
- **J4 · sam 12/07** *(option)* — 5-8 appels 9h-11h (patrons BTP à l'atelier,
  sans standard).
- **J5-J6 · dim-lun férié** — zéro envoi, traiter les réponses.
- **J7 · mar 15/07** — **vague téléphone 1** : 12-15 appels IN (7h45-8h45 et
  17h30-18h15), accroche « je vous appelle suite à mon courrier » ;
  appel manqué → SMS de courtoisie annonçant le rappel. + 25 emails BAND.
- **J8 · mer 16/07** — 10-12 appels IN restants + 25 emails BAND (fin A/B).
- **J9 · jeu 17/07** — email #2 aux IN muets (angle neuf, 3-4 lignes).
- **J10-J12** — vague téléphone 2 (créneaux appris de l'EXPÉ 3) + relances BAND.
- **J13-J14 · 22-23/07** — breakups + `export-campaign` → **`verdict.py assess`**.

## Les commandes (la boucle quotidienne, ~30 min/jour)

```bash
T=plugins/bricks-v2/tools
python3 $T/domain_resolver.py resolve --in in_band.json --out domains.jsonl   # une fois
python3 $T/fullenrich_adapter.py smoke && python3 $T/fullenrich_adapter.py enrich --in contacts.json
python3 $T/outreach_send.py send --db bricks.db                      # DRY-RUN (montre)
python3 $T/outreach_send.py send --db bricks.db --live --campaign-approved "memoval-v2-j1" --cap 25
python3 $T/outreach_send.py check-replies --db bricks.db             # matin et soir
python3 $T/outreach_send.py export-campaign --db bricks.db --out campaign.json
# qualifier à la main replies_positive/meetings dans campaign.json, puis :
python3 $T/verdict.py assess --campaign campaign.json
python3 $T/verdict.py ledger --campaign campaign.json                # coût/RDV en live
```

## Les seuils du verdict (codés, non négociables pendant le test)

- **OUI précoce (dès J+7)** : ≥4 réponses positives OU ≥3 RDV tenus sur 60.
- **OUI ferme (N=120)** : ≥4 RDV OU ≥5 réponses positives.
- **NON (N≥120)** : 0 RDV ET ≤1 réponse positive → falsification de CE motion
  (pas du produit) : pivot canal (prescripteur), d'axe ou de persona.
- **CONTINUE** : zone grise → vague 2 (+60) ; à N=180 encore gris = signal
  faible négatif.
- **Abstention** : aucun taux affiché sous n=25 (doctrine).

## Les 4 preuves de viabilité (au-delà des taux — toutes requises pour un OUI plein)

1. **Quantitatif** : seuils ci-dessus.
2. **Objections** : des « non » de VENTE (trop cher / pas maintenant) = sain ;
   ≥3 objections de PERTINENCE (« je ne vois pas le problème ») = la thèse
   ICP est fausse, plus grave qu'un taux bas.
3. **Willingness-to-pay** : ≥1 prospect qui en RDV discute le COMMENT
   (déploiement, données), pas le POURQUOI-si-cher.
4. **Canal prescripteur** : toute mention spontanée d'expert-comptable /
   notaire / CGP = signal B2B2B qui vaut plus que 3 RDV directs.
   Règle dure : taux corrects MAIS 0 willingness-to-pay = **NON** quand même.

## Codes de la cible (dirigeants 60+, non négociables)

Vouvoiement, « Monsieur », formule complète, zéro emoji, **zéro Calendly**
(choix fermé : « jeudi 8h ou vendredi 12h30 ? »), signature avec ligne fixe
ET adresse postale, vocabulaire de **continuité** (jamais « cession »/
« vendre » au premier contact), proposer de **venir à l'atelier** (rayon
1h30 de Lyon). Les 3 questions-démo comme accroche orale : « Qui est votre
client le plus rentable depuis 2019 ? Quel chantier a le plus dérapé ?
Qu'est-ce que seul votre chef d'atelier sait faire ? »

## Budget total du test

| Poste | Cash |
|---|---|
| FullEnrich (~116 emails + qq mobiles) | ~30 € |
| Lettres (26 × timbre+enveloppe) | 40-60 € |
| API LLM (scoring + fabrique) | ~8 € |
| **Total 14 jours, 2 vagues, 176 contacts traités** | **~100 €** |

Un seul client = 4 500 € + 249 €/mois → le test se rembourse **45×**.
