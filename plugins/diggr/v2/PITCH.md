# PITCH — BRICKS V2 au hackathon (3 minutes + démo live)

> **Ancré sur le brief officiel, rien d'autre.** La question du brief :
> *« what does AI-native revenue look like when you actually build it? »*
> Le but : des **production-ready GTM agents** ; les archétypes cités :
> outreach sequencers, ICP scoring engines, CRM auto-updaters, pipeline
> risk monitors ; le critère : *« if it moves the needle for sales teams,
> it qualifies »* ; la stack : Claude + Sillage + FullEnrich.
> Thèse du pitch : les autres montreront des outils qui PROSPECTENT ;
> BRICKS est le seul système qui DÉCIDE.

## Le mapping brief → preuve (les 3 personas du brief, servies une par une)

| Persona du brief | Ce que BRICKS lui donne | La preuve live |
|---|---|---|
| **B2B founder** | « Mon business est-il viable ? » → verdict OUI/NON codé | `verdict.py` + GTM-TEST à ~100 € |
| **GTM engineer / RevOps** | Les 4 archétypes sur UN moteur + coût par décision | `demo_e2e.py` (0,4 s) + ledger |
| **Sales rep & exec** | Qui contacter, pourquoi, quoi dire, quel deal défendre | bandes IN + next-best-action |

## Le narratif (3 minutes)

**0:00 — Le problème que tout le monde a mal posé.** « Tous les outils GTM
enrichissent une liste qu'on leur donne. Mais la question d'un fondateur
n'est pas "enrichis ma liste" — c'est "QUI achèterait mon produit, pourquoi,
et est-ce que ce business est viable ?" »

**0:30 — Ce que BRICKS fait d'unique (les 5 différences structurelles) :**
1. **Signal-natif, pas liste-natif** : un concept devient une thèse
   falsifiable, décomposée en signaux nécessaires (3 couches, latent→proxy) ;
   c'est l'arbre qui DÉCIDE qui est dans la liste.
2. **Un score qui connaît son ignorance** : intervalles [pessimiste,
   optimiste] → bandes IN/BAND/OUT ; le budget (crédits FullEnrich, checks)
   ne se dépense QUE là où il peut changer une décision (VOI). Capital
   allocation appliqué à la prospection.
3. **Un moteur de VERDICT intégré** : test séquentiel bayésien, seuils codés
   — le système répond à « dois-je continuer ? » avec des chiffres, y
   compris NON. Aucun outil GTM ne fait ça.
4. **La connaissance capitalise** : chaque campagne recalibre l'arbre ;
   les kill-rules ne sont plus jetables, elles deviennent un actif.
5. **Économiquement irréfutable** : RDV qualifié à ~130 € charge complète
   (21 € cash) vs 250-500 € en agence, 4 000 €/mois de burn SDR ;
   5,4× moins cher que Clay en cash — ET Clay ne score pas l'ICP.

**1:30 — La preuve (pas la promesse).** « On ne vous montre pas une démo
jouet : on a testé scientifiquement, deux fois, avec des juges adversariaux.
V1 : 45 % de précision de ciblage, montée à 75 % en 3 corrections humaines.
V2 : **90 % du premier coup, zéro correction** — parce que la connaissance
des échecs est encodée dans l'arbre. Mails 8,5/10, zéro hallucination,
zéro crédit dépensé. Et le repêchage a retrouvé la seule entreprise en
signal réel de cession que nos propres règles avaient écrasée. »

**2:15 — La démo live** (voir minute-par-minute ci-dessous).

**2:45 — La chute.** « Demain matin, ce système lance un vrai test
go-to-market : 176 PME, 14 jours, ~100 € tout compris, verdict OUI/NON
codé d'avance. Un client le rembourse 45 fois. BRICKS ne génère pas des
leads — il rend la question "mon business est-il viable ?" falsifiable. »

## La démo live (4 minutes, tout est réel)

| t | Action | Ce que le public voit |
|---|---|---|
| 0:00 | `score_v2.py demo` | 303 PME réelles scorées en <5 s, bandes IN/BAND/OUT, identifiabilité |
| 0:45 | UI Bricks (tableau) | colonnes signaux clés, groupées par axe — « le tableau qui pense » |
| 1:30 | `score_v2.py voi --budget 60` | le plan d'achat d'information : chaque check peut changer une bande |
| 2:15 | `messaging_factory.py compile-prompt` + un mail | l'évidence → le mail ; ressources fermées = zéro hallucination |
| 3:00 | `verdict.py demo` | les 3 scénarios : VIABLE (P=0,93 que IN batte le témoin, coût/RDV 56 €), silence→CONTINUE, n=15→ABSTENTION |
| 3:40 | `GTM-TEST-MEMOVAL.md` | le test réel qui part demain — lettres postées le jour du hackathon |

## Objections anticipées (réponses en une phrase)

- *« C'est du prompt engineering. »* → Le scoring est du code pur
  déterministe (22 tests) ; le LLM ne touche ni les faits ni les chiffres —
  design-time et rédaction seulement, sous ressources fermées.
- *« 90 % sur 20, c'est peu. »* → Exact, et le système le DIT lui-même :
  abstention sous n=25, intervalles partout ; c'est le seul outil qui
  affiche son incertitude au lieu de la cacher.
- *« Sillage/FullEnrich ne sont pas branchés. »* → Adapters écrits sur les
  docs officielles, smoke test FullEnrich à 0 crédit prêt, rituel de
  connexion de 45 min (DAY1) — et le mock a tourné E2E ce soir.
- *« Ça marche pour MemoVAL, et pour autre chose ? »* → Le concept entre en
  langage naturel ; l'arbre est régénéré par les agents pour toute thèse ;
  la plomberie (V1) et le cerveau (V2) sont agnostiques au produit.

## La grande idée (repositionnement stack — ajouté 09/07)

**« Un seul moteur, l'autre sens du cycle de vie. »** Scorer QUI achète et scorer
QUEL deal meurt, c'est le même calcul bayésien sur la même donnée Sillage. V2 ne
colle pas 4 outils — il pointe UN cerveau (`score_v2.py`) dans les deux directions
du revenue et écrit tout dans le CRM. Les 4 archétypes du brief, un moteur :

| Archétype du brief | Brique V2 | État |
|---|---|---|
| ICP scoring engine | `score_v2.py` (intervalles + bandes + VOI) | 95 % — le joyau |
| Outreach sequencer | `messaging_factory` + `outreach_send` | 70 % |
| CRM auto-updater | `crm_adapter.py` (upsert Account+Task par domaine) | construit |
| Pipeline risk monitor | `pipeline_monitor.py` (le MÊME moteur, arbre de risque) | construit |

**Exploitation de la stack imposée (analyse Opus adversariale) : V2 7,7/10 vs V1 3,0/10**
— Claude 9 vs 4 (jonctions de jugement, pas copywriter), Sillage 7 vs 0 (les 8 types
ontologisés : achat ET risque), FullEnrich 8 vs 5 (garde VOI). La démo `demo_e2e.py`
rejoue les 4 archétypes en 0,4 s, 0 crédit.

## La phrase d'ancrage

**« Les autres enrichissent une liste et espèrent que Sillage la réveille.
BRICKS est le seul système où les 3 piliers forment une seule boucle de décision —
et il surveille vos deals qui dérapent pendant qu'il trouve les prochains. »**
