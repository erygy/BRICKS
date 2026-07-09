# Working notes — memoval-outbound

> Free-form working memory for this workspace. Skills append decisions,
> context and open questions here, newest entries at the bottom.

## 2026-07-08 — Run de test scientifique BRICKS (offre = MemoVAL)

Objectif : valider BRICKS de bout en bout (find → firmo → signaux → score/rank →
drafts) sur l'ICP MemoVAL, avant présentation. Lanes payantes indisponibles
(pas de `~/.bricks/env` : FullEnrich + Bright Data OFF) → test du cœur gratuit.

### Funnel
- 303 PME sourcées (API gouv recherche-entreprises, région Auvergne-Rhône-Alpes,
  filtres : PME, CA 1,5–10 M€, dirigeant né 1958–1966, panier NAF).
- 109 disqualifiées par kill rules (77 secteur faible savoir-tacite = ingénierie/
  conseil/CAC ; 21 ancienneté <15 ans ; 11 probables filiales).
- 194 ICP-fit → tiers A=131 / B=55 / C=8.
- 5 drafts CPPC (tier A, dirigeant exécutif nommé) — status=draft, RIEN envoyé.

### Résultats mesurés (protocole pré-enregistré, juges adversariaux)
- Précision ICP (n=20) : **45 % → 65 % → 75 %** sur 3 cycles de patch kill-rules.
- firmo.py (résolution nom→firmographie, n=60) : 82 % high / 17 % none / 2 % ambiguous.
- Couverture firmo (discovery) : SIREN 100 %, dirigeant 100 %, effectif 91 %.
- Signaux news.py : 235 items bruts, 0 signal transmission GENUINE parmi les
  survivants (seul vrai = Ponant Technologies, en secteur exclu).
  → pour MemoVAL le signal est un ÉTAT firmographique, pas un ÉVÉNEMENT presse.
- Drafts (n=5) : 8,4/10, 100 % sans hallucination, CPPC 5/5, anti-L121 conforme.

### Patchs kill-rules issus du field-test (à graver dans icp.md)
1. Blacklist secteurs faible savoir-tacite : NAF 71.xx, 74.90B, 69.xx, 64/66/68.
   ← le trou #1 (45 %→65 %).
2. Filiale de groupe : « … FRANCE » + dirigeant salarié / SA + conseil surveillance.
   Résiduel = filiales à nom d'enseigne étrangère (indétectables sans registre
   groupes = lane payante). ← trou #2 (~75 %→~90 % avec flag manuel).
3. Plancher ancienneté ≥ 15 ans.

### Limites du test (environnement)
- Pas d'emails vérifiés (FullEnrich OFF) : contacts = dirigeants nommés, sans email.
- Fuite géographique : `departement` API ≠ strictement siège → quelques hors-région.
- Champ « dirigeant » parfois = commissaire aux comptes (préférer Président/Gérant/DG).

Prochaine itération : brancher FullEnrich (emails + registre groupes), puis
lancer réellement 30 contacts sur le top tier A.
