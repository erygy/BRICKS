#!/usr/bin/env bash
# verify.sh — « trust but verify » : lance TOUTE la chaîne V2 en une commande,
# zéro clé, zéro dépendance (stdlib Python 3). Un collaborateur qui clone le
# repo prouve les affirmations du HANDOFF en ~1 minute.
#
#   cd plugins/bricks-v2 && bash verify.sh
#
# Chaque étape affiche PASS/FAIL ; sortie non-zéro si une étape casse.

set -u
cd "$(dirname "$0")"
T=tools
ok=0; ko=0
step () { # step "libellé" "commande…"
  printf "  %-46s " "$1"
  if out=$(eval "$2" 2>&1); then echo "PASS"; ok=$((ok+1)); else echo "FAIL"; ko=$((ko+1)); echo "$out" | tail -3 | sed 's/^/      /'; fi
}

echo "── BRICKS V2 · vérification de bout en bout ──"
step "tests du noyau de scoring (22 assertions)"   "python3 $T/test_score_v2.py | grep -q 'assertions OK'"
step "scoring + VOI sur 303 PME réelles"           "python3 $T/score_v2.py demo | grep -q '\"IN\"'"
step "chaîne Sillage complète (mock E2E)"          "python3 $T/sillage_adapter.py mock-demo | grep -q evidence"
step "fabrique de messages (signaux clés→ressources)" "python3 $T/messaging_factory.py demo | grep -q ressources"
step "moteur de verdict (3 scénarios)"             "python3 $T/verdict.py demo | grep -q SIGNAL_VIABLE"
step "résolution de domaine zéro-clé (1 cas)"      "python3 $T/domain_resolver.py one --name 'EGS CLIM' --ville LYON | grep -q confidence"
step "arbre de risque valide (check propre)"       "python3 $T/score_v2.py check --tree fixtures/retention-signals.json | grep -q '\"warnings\": \\[\\]'"
step "pipeline risk monitor (le MÊME moteur)"      "python3 $T/pipeline_monitor.py demo | grep -q 'À_RISQUE'"
step "CRM writeback (acquisition + rétention)"     "python3 $T/crm_adapter.py demo | grep -q comptes_upsertes"
step "démo E2E — 4 archétypes, 1 moteur, 3 piliers" "python3 $T/demo_e2e.py | grep -q '4 archétypes'"

echo "────────────────────────────────────────────"
echo "  $ok PASS · $ko FAIL"
[ "$ko" -eq 0 ] && echo "  ✓ chaîne V2 vérifiée de bout en bout, zéro clé." || echo "  ✗ voir les FAIL ci-dessus."
exit "$ko"
