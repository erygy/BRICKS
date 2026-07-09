# DEMO — le fil de test complet, de l'ICP à l'envoi

Exemple de bout en bout : **NovaRank** (nom fictif — remplace par le vrai),
agence SEO spécialisée **référencement sur les IA** (AEO/GEO) : faire citer
et recommander ses clients par ChatGPT/OpenAI et Gemini. Biais
différenciant : beaucoup de **RP marketing** — créer des mentions de marque
sur les réseaux sociaux et dans les sources que les IA lisent.

Chaque étape = UN prompt à coller dans la session Claude Code (repo BRICKS
ouvert ; plugin installé : les skills répondent aussi en `/bricks:…`).
Les chiffres de preuve sont des **hypothèses démo assumées**.

---

## 0 — Prérequis (2 min, une fois)

```
Vérifie les prérequis du pipeline : workspace courant, clés moteur
(python3 tools/providers/sillage.py test-auth et
python3 tools/providers/emelia.py test-auth), et ouvre l'interface.
```

Attendu : les deux `test-auth` répondent `ok:true` ; l'UI est sur
http://127.0.0.1:4321. Clé manquante → panneau ⚙ de l'interface.

---

## 1 — P0 · Onboard (l'interview — offre, ICP, concurrents)

```
Onboarde-moi (skills/onboard). On lance le GTM de NovaRank : agence SEO
spécialisée dans le référencement sur les intelligences artificielles
(AEO/GEO) — on fait en sorte que nos clients soient cités et recommandés
par ChatGPT/OpenAI et Gemini quand un utilisateur pose une question de
leur domaine. Notre biais différenciant : beaucoup de RP marketing — on
fabrique des mentions de marque sur les réseaux sociaux et dans les
sources que les IA lisent, en particulier Gemini et OpenAI ; là où les
agences SEO classiques optimisent des pages, nous on installe la marque
dans les réponses des IA. Preuves (démo) : +40 % de citations IA en 90
jours sur 12 clients ; ×3 sur le trafic « AI referral » d'un e-commerçant.
Ton : direct, tutoiement, français, zéro jargon.

ICP v1 à challenger : e-commerce et SaaS français, 20 à 500 salariés,
dépendants de l'acquisition organique. Kill rules : moins de 20 salariés ;
agences SEO/marketing (concurrents) ; hors France-Belgique-Suisse.
Décideur : CMO | Directeur Marketing | Head of Digital | Head of
Acquisition. Champion : Head of SEO | SEO Manager | Content Manager.
```

Puis, quand la Phase 3 demande les concurrents :

```
Mes 5 concurrents directs : Eskimoz, Semji, Primelis, Noiise, Ad's up
Consulting. Résous-les via FullEnrich, drafte les why_we_win (notre angle :
RP + mentions IA vs SEO on-page classique) et propose les interest_score.
```

Attendu : `context/offer.md`, `context/icp.md`, `context/personas/*`
remplis ; table `competitors` écrite (5 lignes, dédup domain) ; receipt
« v1 falsifiable ». Vérifie dans l'UI : onglet competitors.

---

## 2 — P1 · Sourcing (FullEnrich → CSV → companies)

```
Source l'ICP : via FullEnrich (export_companies), exporte ~50 entreprises
e-commerce/SaaS France 20-500 salariés, télécharge le CSV dans le staging/
du workspace, puis importe-le : python3 seed/import_p1.py --csv <fichier>.
Receipt : lues / sans domaine / insérées / doublons — max 3 exemples.
```

Attendu : `companies` se remplit, `source='fullenrich_search'`,
`qualify_status='pending'` armé partout. Pas de domaine = pas de ligne.

---

## 3 — P2 · Qualification (la porte unique)

```
Lance la porte P2 (skills/surveil, section Qualification) : runner --ai
sur les companies qualify_status='pending', critères STATIQUES d'icp.md
uniquement (liste d'exclusion Sillage incluse dans le prompt), preview 10.
```

→ Vérifier les 10 receipts dans l'UI (verdicts + raisons), puis :

```
GO — commit la qualification.
```

Attendu : `icp_verdict`/`icp_reason`/`fit_score` posés ; les rejetées
restent en base. Un verdict qui cite un recrutement ou un post = mauvais
verdict, on resserre.

---

## 4 — P3 · Surveillance (Sillage)

```
Mets le monde sous surveillance (skills/surveil) : sillage.py setup
(persona = union des titres d'icp.md + top-20 qualified par fit_score),
watchlist --type competitor (top 5 interest_score), agents avec les
mots-clés pain : "référencement IA", "AEO", "GEO", "citations ChatGPT",
"visibilité Gemini", "trafic organique en baisse", "zero-click", "SEO".
Puis run --lookback 90.
```

Attendu : `tracked='1'` + `sillage_company_id` sur ≤20 comptes,
`watched='1'` + `sillage_entity_id` sur les concurrents, 4 agents créés,
runs lancés (reprise possible : re-lancer `run` ne repaie pas).

---

## 5 — P4 · Pull + leads + interception

```
Pull les signaux (sillage.py pull) puis les décideurs (sillage.py leads).
Receipt par type + combien de competitor* attendent l'interception.
Ensuite lance l'interception en preview 10 (runner --step
tools/steps/intercept.py:step sur intercept_status).
```

→ Vérifier les interceptées (companies `source='competitor_interception'`,
même porte P2), puis :

```
GO — commit l'interception, puis re-lance la qualification P2 sur les
nouvelles pending.
```

---

## 6 — P5 · Scoring (qui appeler, pourquoi maintenant)

```
Priorise (skills/prioritize) : score.py sur companies + contacts —
timing (décroissance), faisceau (signaux du contact ×1.0, collègues et
entreprise ×0.5), fit, persona. Commit les scores, arme
why_now_status='pending' sur les tiers now|week et lance la passe haiku
qui polit les why_now depuis why_now_evidence.
```

Attendu : `priority_score`/`priority_tier`/`why_now`/`why_now_evidence`
posés. Vérifie une fiche dans l'UI : le WHY NOW et le faisceau s'affichent.

---

## 7 — P6 · La file de la semaine (stratégie, budget, drafts, audit)

```
Prépare la file de la semaine (skills/outreach) : crée les lignes outreach
des tiers now, propose la stratégie par contact (email_only | email_call |
call_only). AVANT d'enrichir les coordonnées : annonce le coût FullEnrich
et demande-moi lesquels — je te donnerai les N premiers.
```

→ Répondre par exemple : `GO — enrichis les 5 premiers du tier now.`

```
Rédige les drafts (runner --ai depuis brief_json : emails 1/2/3 +
icebreaker call, doctrine CPPC, <100 mots), puis lance l'audit
indépendant. audit_score < 70 = jamais approved.
```

**Approbation = humaine, dans l'UI** : onglet « 📞 To contact this week »
→ clic sur la ligne → bouton **Approve** (le garde-fou audit refuse les
< 70 avec un 409).

---

## 8 — P7 · Envoi Emelia (boîtes seed uniquement)

```
Envoie les approuvés : emelia.py create-campaign --week <2026-Wnn>, push
(seed guard actif — seules les boîtes EMELIA_SEED_INBOXES passent), start.
Plus tard dans la journée : stats — opened_count/replied reviennent sur
outreach et tu me sors la liste « à appeler ».
```

Fallback zéro-API : `emelia.py export-csv --week <semaine>`.

---

## 9 — Le bouton démo (la séquence jury, 90 secondes)

À répéter une fois avant 16 h. Injecte un signal chaud sur un compte
tracké (officiel, via le provider — pas de SQL) :

```
Injecte le signal démo : python3 tools/providers/sillage.py add-signal
--json '{"sillage_type":"championInboundComment","actor_name":"<ton
champion>","company_domain":"<compte tracké>","summary":"Notre champion
vient de commenter — fenêtre chaude"}'. Puis re-priorise (P5) et montre-moi
la fiche du contact dans l'interface.
```

Effet attendu devant le jury : le contact monte en tier `now`, sa fiche
affiche le nouveau WHY NOW + le faisceau, on clique **Approve**, on push
vers Emelia (boîte seed), on ouvre la boîte : l'email est arrivé.

---

## Ce qu'on vérifie à chaque étape (la grille d'évaluation du test)

1. **Receipts, jamais de dump** — max 3 lignes d'échantillon en chat.
2. **Preview → GO → commit** sur chaque batch (P2, interception, drafts).
3. **Statuts** : re-lancer une étape reprend les `pending`, ne repaie pas.
4. **Zéro fabrication** : pas de domaine inventé, pas de coordonnée
   fabriquée, `not_found` est un résultat.
5. **L'UI suit en direct** (poll 4 s) : tables, fiche, Approve.
