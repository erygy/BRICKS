#!/usr/bin/env python3
"""V3 — CALCUL DE VIABILITÉ (déterministe, 0 token).
Question de Thomas : « pas 1 démarchage tous les six mois — des flags en
abondance au quotidien ». On calcule le volume de flags/jour à partir des
fréquences honnêtes estimées par flag (freq_per_1000_month), pour plusieurs
tailles d'univers, et le volume de DÉMARCHAGES qualifiés qui en sort."""
import json, os, sys

S = os.path.dirname(os.path.abspath(__file__))
flags = json.load(open(f"{S}/flags_ranked.json")) if os.path.exists(f"{S}/flags_ranked.json") else json.load(open(f"{S}/flags_raw.json"))

def num(x, d=0.0):
    try: return float(x)
    except Exception: return d

# hygiène : ne compter que les flags détectables (Sillage ou autre source nommée)
usable = [f for f in flags if (f.get("sillage") or {}).get("detectable") or f.get("other_detection")]
sill = [f for f in usable if (f.get("sillage") or {}).get("detectable")]
freq_total = sum(num(f.get("freq_per_1000_month")) for f in usable)          # occurrences /1000 comptes /mois
freq_sill = sum(num(f.get("freq_per_1000_month")) for f in sill)
freq_strong = sum(num(f.get("freq_per_1000_month")) for f in usable if num(f.get("strength")) >= 7)

print("═" * 76)
print("  V3 · VIABILITÉ — volume de flags (fréquences honnêtes par flag, sommées)")
print("═" * 76)
print(f"  flags utilisables : {len(usable)}/{len(flags)} (dont {len(sill)} détectables via Sillage)")
print(f"  intensité totale  : {freq_total:.0f} occurrences /1000 comptes /mois")
print(f"    dont Sillage    : {freq_sill:.0f} · dont flags FORTS (≥7/10) : {freq_strong:.0f}")
print()
print("  Taille de l'univers (clients de concurrents surveillés) → flags/jour :")
print(f"  {'univers':>10} | {'flags/jour':>10} | {'forts/jour':>10} | {'démarchages qualifiés/sem*':>26}")
for n in (200, 500, 1000, 2000, 5000):
    per_day = freq_total * n / 1000 / 30
    strong_day = freq_strong * n / 1000 / 30
    # démarchage qualifié : flag fort OU cumul de 2+ flags sur le même compte (approx 60% des forts + 10% du reste)
    qualified_week = (strong_day * 0.6 + (per_day - strong_day) * 0.10) * 7
    print(f"  {n:>10} | {per_day:>10.1f} | {strong_day:>10.1f} | {qualified_week:>26.0f}")
print()
print("  * démarchage qualifié = flag fort actionné + garde-fous (dédup compte, fenêtre, faux positifs).")
print()
# construction de l'univers : combien de comptes atteignables ?
print("  Construction de l'univers (ordre de grandeur par CONCURRENT) :")
print("    posts LinkedIn minés (validé live : ~0,2 client/post × 300-800 posts) : 60-160")
print("    site web (logos, cas clients, portfolio)                              : 20-120")
print("    avis G2/Capterra/Trustpilot (si SaaS)                                  : 20-200")
print("    offres d'emploi des clients citant l'outil                             : 10-50")
print("    presse / marchés publics / événements co-brandés                       : 10-60")
print("    → par concurrent : ~100-400 clients identifiables · 8-12 concurrents = univers 800-4 800")
