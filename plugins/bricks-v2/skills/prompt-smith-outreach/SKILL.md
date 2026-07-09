---
name: prompt-smith-outreach
description: « Je sais créer des prompts pour écrire des mails » — l'art de compiler un PROMPT D'AXE puis un prompt de génération sur mesure (BASE = AXE × FORMAT, nourri des RESSOURCES). Utilisé par l'AXE-MAPPER pour chaque axe, et par la fabrique pour chaque entreprise. Fusion de la doctrine write-outreach V1 et des frameworks cold-email du corpus.
---

# prompt-smith-outreach — je sais créer des prompts pour écrire des mails

Un bon mail sort d'un bon prompt, et un bon prompt est un OBJET COMPILÉ :
rien d'improvisé au moment de la génération. Cette skill définit comment
écrire les deux étages de prompts de la fabrique
(`tools/messaging_factory.py`).

## Étage 1 — le PROMPT D'AXE (écrit par l'AXE-MAPPER, un par axe)

Le prompt d'axe est l'HISTOIRE DU SEGMENT en 6-10 lignes, qui sera injectée
dans tous les prompts de génération de cet axe. Il contient, dans cet ordre :

1. **Qui ils sont** — le portrait du sous-segment en une phrase concrète
   (« des industriels de 25-70 ans d'ancienneté dont le dirigeant approche
   la sortie et vient de recruter un second »).
2. **Ce que le signal clé dit d'eux** — l'interprétation métier du signal
   qui les groupe (pas le nom technique : « ils délèguent — c'est presque
   toujours l'année où l'on commence à penser à la suite »).
3. **La douleur d'axe** — la déclinaison de la douleur de la thèse POUR ce
   segment, dans les mots du segment.
4. **L'angle d'ouverture recommandé** — comment le fait-signal devient une
   observation d'email (OPPA), avec UN exemple d'ouverture réussie et UN
   contre-exemple (l'ouverture créepy ou décorative à éviter).
5. **Le registre** — ce que ce segment tolère (direct ? technique ?) et ne
   tolère pas (jargon SaaS, flatterie).
6. **Les pièges de l'axe** — 2-3 erreurs spécifiques (ex. axe « délégation
   en cours » : ne JAMAIS suggérer que le dirigeant part — c'est lui qui
   le dira).

Interdits du prompt d'axe : aucun fait d'entreprise individuelle (ça vient
des RESSOURCES), aucune promesse chiffrée, aucun modèle de mail complet
(le format s'en charge — un prompt d'axe qui contient un template produit
des clones).

## Étage 2 — le prompt de génération (compilé par la fabrique, un par mail)

La fabrique assemble : PROMPT D'AXE + CONTRAT DE FORMAT (formats.json) +
DIGEST OFFRE + VOIX + BLOC RESSOURCES + AUTO-CONTRÔLE. Ta responsabilité
quand tu touches au template (`PROMPT_TEMPLATE`) :

1. **Les ressources sont fermées** : le prompt doit dire explicitement que
   tout fait hors bloc RESSOURCES n'existe pas. C'est LA défense
   anti-hallucination (héritée du field-test : 100 % sans invention).
2. **L'auto-contrôle est un contrat de sortie** : 5 critères max,
   vérifiables, dont le test du pair et l'anti-L121. Un critère
   invérifiable (« sois percutant ») est du bruit — supprime.
3. **Ordre des blocs immuable** : axe → format → offre → voix → ressources →
   contrôle. Le modèle lit le contexte AVANT les données : inverser dégrade.
4. **Une seule sortie demandée** : un mail (sujet + corps + signature), pas
   trois variantes. Les variantes se demandent par des runs séparés
   (déterminisme du pipeline, un prompt = un draft = un msg_key).
5. **Digest, jamais dump** : offre ≤ 900 caractères, voix ≤ 400. Un prompt
   de génération > 2 500 mots noie le contrat de format.

## Le critère de réussite

Deux entreprises du MÊME axe avec des ressources différentes doivent donner
deux mails visiblement différents ; deux entreprises d'axes différents ne
doivent jamais être confondables. Si les sorties se ressemblent, le prompt
d'axe raconte trop (il écrit le mail à la place du format) ou les ressources
sont trop pauvres (retour VOI/enrichissement, pas rustine de prompt).
