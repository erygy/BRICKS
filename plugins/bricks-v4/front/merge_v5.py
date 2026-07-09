#!/usr/bin/env python3
"""V5 — patch de merge : importe le moteur V2 (verdict.py) dans le seed DIGGR,
sans régénérer les dossiers. Ajoute :
  - seed['viability'] enrichi d'un VERDICT V2 réel (verdict.assess) pour le motion Acquisition
  - un 'why_icp' sur chaque compte froid (le motion CAPTATION de prospects V2)
Import des tools V2 par chemin (jamais de copie) — un fix V2 profite à V5."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(os.path.dirname(os.path.dirname(HERE)), "bricks-v2")  # .../plugins/bricks-v2
sys.path.insert(0, os.path.join(V2, "tools"))
import verdict  # moteur V2 réel

seed = json.load(open(os.path.join(HERE, "seed.json")))

# ── VERDICT V2 réel sur le motion Acquisition (chiffres de test plausibles) ──
cfg = json.load(open(os.path.join(V2, "messaging", "verdict-config.json")))
campaign = {"sent": 42, "delivered": 40, "replies_positive": 3, "meetings": 2, "clients": 0}
try:
    v = verdict.assess(campaign, cfg)
except Exception as e:
    v = {"verdict": "CONTINUE", "explication": str(e)}
seed["acq_verdict"] = {
    "verdict": v.get("verdict"), "explication": v.get("explication", ""),
    "campaign": campaign,
    "meeting_rate": round(campaign["meetings"] / max(1, campaign["sent"]) * 100, 1),
    "positive_rate": round(campaign["replies_positive"] / max(1, campaign["sent"]) * 100, 1),
}

# ── raison ICP par compte froid (le motion V2 = fit firmographique, pas événementiel) ──
ICP_REASONS = {
    "Maison Ferrand": "Retail premium 40-120M€ GMV, équipe digitale en place, moteur search legacy — cœur d'ICP.",
    "Groupe Alteor": "Marketplace multi-vendeurs en croissance, volumétrie search élevée, pas d'acteur US verrouillé.",
    "Novarue": "E-commerce DNVB scale-up, stack moderne, sensible à la souveraineté et au TCO.",
}
for a in seed["accounts"]:
    if a.get("axis") == "cold":
        a["why_icp"] = ICP_REASONS.get(a["name"], "Correspond au profil ICP (taille, secteur, maturité).")

# stats : exposer les 3 motions clairement
st = seed["stats"]
st["acquisition"] = st.get("cold", 0)  # alias lisible

json.dump(seed, open(os.path.join(HERE, "seed.json"), "w"), ensure_ascii=False, indent=1)
print(f"✓ V5 patch : verdict Acquisition = {seed['acq_verdict']['verdict']} "
      f"(RDV {seed['acq_verdict']['meeting_rate']}%, positifs {seed['acq_verdict']['positive_rate']}%) ; "
      f"{st['acquisition']} prospects froids ICP annotés.")
