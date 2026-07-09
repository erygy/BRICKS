#!/usr/bin/env python3
"""BRICKS V4 — serveur du cockpit de déplacement concurrentiel.

Sert l'interface (index.html) + une API JSON adossée aux VRAIES données
(seed.json, assemblé depuis le minage live Sillage + la taxonomie de 257 flags)
et aux VRAIS outils (Fable 5 via l'API pour le chatbot ancré et la détection de
concurrents ; clés API dans ~/.bricks/env, jamais renvoyées en clair).

Deux axes produits, présents partout : CAPTATION (voler un client d'un concurrent)
et INTERCEPTION (devancer la signature d'un prospect qui évalue un concurrent).

    python3 server.py [--port 8970]
Bind 127.0.0.1 uniquement.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ENV = os.path.expanduser("~/.bricks/env")

try:
    from fable_api import call as fable_call
    HAVE_FABLE = True
except Exception:
    HAVE_FABLE = False

# clés gérées + aide (l'utilisateur non-technique doit savoir où cliquer)
KEYS = [
    {"name": "ANTHROPIC_API_KEY", "label": "Claude (Anthropic)", "required": True,
     "how": "console.anthropic.com → API Keys", "role": "Le cerveau : détection, diagnostic, rédaction."},
    {"name": "SILLAGE_API_KEY", "label": "Sillage", "required": True,
     "how": "app.getsillage.com → Settings → API Keys", "role": "Les signaux : veille des clients & prospects des concurrents."},
    {"name": "FULLENRICH_API_KEY", "label": "FullEnrich", "required": False,
     "how": "app.fullenrich.com → API (ou MCP OAuth)", "role": "Les coordonnées : le bon contact, au bon moment."},
]

def seed():
    with open(os.path.join(HERE, "seed.json"), encoding="utf-8") as f:
        return json.load(f)

def read_env():
    vals = {}
    if os.path.isfile(ENV):
        for line in open(ENV, encoding="utf-8"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); vals[k.strip()] = v.strip()
    return vals

def settings_status():
    vals = read_env()
    out = []
    for k in KEYS:
        v = vals.get(k["name"], "")
        out.append({**k, "present": bool(v),
                    "masked": (v[:3] + "…" + v[-4:]) if len(v) > 8 else ("•" * len(v) if v else "")})
    return {"keys": out}

def set_key(name, value):
    if not name or not isinstance(name, str):
        raise ValueError("clé invalide")
    if name not in {k["name"] for k in KEYS}:
        raise ValueError(f"clé inconnue: {name}")
    os.makedirs(os.path.dirname(ENV), exist_ok=True)
    vals = read_env(); vals[name] = (value or "").strip()
    with open(ENV, "w", encoding="utf-8") as f:
        for k, v in vals.items():
            f.write(f"{k}={v}\n")
    os.chmod(ENV, 0o600)
    return settings_status()

def _json_from(txt, opener="{"):
    closer = "}" if opener == "{" else "]"
    s = txt.find(opener)
    if s < 0: return None
    depth = 0; instr = False; esc = False
    for i in range(s, len(txt)):
        c = txt[i]
        if esc: esc = False; continue
        if c == "\\": esc = True; continue
        if c == '"': instr = not instr
        elif not instr:
            if c == opener: depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    try: return json.loads(txt[s:i + 1])
                    except Exception: return None
    return None

# ── CHATBOT ANCRÉ (façon MemoVAL) : répond UNIQUEMENT sur les faits du dossier, sinon s'abstient ──
def account_facts(acc, brief):
    lines = [f"Compte : {acc['name']} ({acc['domain']})",
             f"Axe : {'CAPTATION (client de '+str(acc.get('rival'))+')' if acc.get('axis')=='client' else ('INTERCEPTION (prospect évaluant '+str(acc.get('rival'))+')' if acc.get('axis')=='prospect' else 'prospect froid')}",
             f"Preuve/intent : {acc.get('evidence') or '—'} (certitude : {acc.get('certainty') or 'n/a'})",
             f"FIT : bande {acc['fit']['band']}, score attendu {acc['fit']['expected']} (borne basse {acc['fit']['pessimistic']}, haute {acc['fit']['optimistic']}), tier {acc['fit']['tier']}",
             f"Firmo (ordres de grandeur) : CA {acc['firmo']['ca_eur']}, {acc['firmo']['effectif']} employés, {acc['firmo']['pays']}",
             f"Fenêtre : {acc['window']['state']}"]
    for fl in acc["window"]["flags"]:
        lines.append(f"  · signal « {fl['name']} » (force {fl['strength']}/10, il y a {fl['days_ago']}j) — {fl.get('evidence','')}")
    fa = acc.get("faille_rival") or {}
    if fa.get("name"):
        lines.append(f"Faille du concurrent {acc.get('rival')} : {fa.get('name')} — levier : {fa.get('levier','')}")
    if brief:
        lines.append("Dossier : " + brief.get("headline", ""))
        for ax in brief.get("strategic_axes", []): lines.append(f"  axe : {ax.get('axis')} — {ax.get('why')}")
        for lv in brief.get("levers", []): lines.append(f"  levier : {lv.get('lever')} ({lv.get('proof')})")
        for m in brief.get("key_members", []): lines.append(f"  contact : {m.get('role')} — {m.get('why')}")
        for kf in brief.get("key_figures", []): lines.append(f"  chiffre : {kf.get('figure')} ({kf.get('note')})")
    return "\n".join(lines)

ASK_SYS = ("Tu es l'assistant de démarchage de Lumen Search, greffé sur le dossier d'UN compte. Tu réponds "
 "UNIQUEMENT à partir des FAITS DU DOSSIER ci-dessous. Si l'information n'y est pas, tu le dis franchement "
 "(« Ce n'est pas dans le dossier — il faudrait enrichir via FullEnrich / lancer un run Sillage ») et tu "
 "n'inventes RIEN. Tu es concis (2-5 phrases), concret, orienté action commerciale. Tu ne dénigres jamais le "
 "concurrent. Français.")

def ask(payload):
    acc_id = payload.get("account_id"); q = (payload.get("question") or "").strip()
    if not q: raise ValueError("question vide")
    s = seed()
    acc = next((a for a in s["accounts"] if a["id"] == acc_id), None)
    if not acc: raise ValueError("compte inconnu")
    if not HAVE_FABLE or not read_env().get("ANTHROPIC_API_KEY"):
        return {"answer": "Clé Anthropic absente — le chatbot a besoin de la clé Claude (écran Installation).",
                "grounded": False}
    facts = account_facts(acc, s.get("briefs", {}).get(acc_id))
    u = f"FAITS DU DOSSIER :\n{facts}\n\n===\nQUESTION : {q}\n\nRéponds à partir des faits ci-dessus uniquement."
    r = fable_call(u, system=ASK_SYS, max_tokens=1200, label="ask")
    txt = (r.get("text") or "").strip()
    if not txt or txt.startswith("[ERREUR"):
        return {"answer": "Le service Claude n'a pas répondu (connexion instable). Réessayez dans un instant.",
                "grounded": False, "error": True, "account": acc["name"]}
    return {"answer": txt, "grounded": True, "account": acc["name"]}

# ── GÉNÉRATION DE DOSSIER À LA DEMANDE (n'importe quel compte → brief Fable, axis-aware) ──
_BRIEF_CACHE = {}
BRIEF_SYS = ("Tu es l'analyste de démarchage de Lumen Search (moteur de recherche e-commerce IA, souverain "
 "européen, installé en 2 semaines, alternative frugale aux moteurs US). Factuel, sans slop, tu n'inventes "
 "pas de chiffres précis (ordres de grandeur, tu marques les inconnues). JSON STRICT uniquement.")

def generate_brief(payload):
    acc_id = payload.get("account_id")
    s = seed()
    if acc_id in s.get("briefs", {}):
        return {"brief": s["briefs"][acc_id], "cached": True}
    if acc_id in _BRIEF_CACHE:
        return {"brief": _BRIEF_CACHE[acc_id], "cached": True}
    acc = next((a for a in s["accounts"] if a["id"] == acc_id), None)
    if not acc: raise ValueError("compte inconnu")
    if not HAVE_FABLE or not read_env().get("ANTHROPIC_API_KEY"):
        return {"error": "Clé Anthropic absente — le dossier a besoin de la clé Claude (écran Installation)."}
    rival = acc.get("rival") or ""; fa = acc.get("faille_rival") or {}
    flags_txt = "; ".join(f"{f['name']} (force {f['strength']}, il y a {f['days_ago']}j)" for f in acc["window"]["flags"]) or "aucun flag daté"
    if acc.get("axis") == "prospect":
        situ = (f"COMPTE : {acc['name']} ({acc['domain']}) — PROSPECT qui ÉVALUE {rival} (pas encore client).\n"
                f"AXE = INTERCEPTION : arriver avant la signature, sans dénigrer {rival}.\nSignal d'intent : « {acc.get('evidence','')} »\n")
        msg = "un email d'INTERCEPTION de 6-8 lignes : se placer dans leur évaluation, proposer une comparaison factuelle, jamais dénigrer, signé Thomas"
    else:
        situ = (f"COMPTE : {acc['name']} ({acc['domain']}) — CLIENT de {rival}.\nAXE = CAPTATION : le déplacer via un signal de fenêtre + la faille du concurrent.\nPreuve du minage : « {acc.get('evidence','')} »\n")
        msg = "un email de CAPTATION de 6-8 lignes qui accroche sur le signal et le levier, jamais dénigrant, signé Thomas"
    u = (situ + f"Firmo : CA {acc['firmo']['ca_eur']}, {acc['firmo']['effectif']} employés, {acc['firmo']['pays']}.\n"
         f"Signaux de fenêtre : {flags_txt}\nFaille de {rival} : {fa.get('name','')} — {fa.get('what','')} (levier : {fa.get('levier','')}).\n\n"
         "Produis le dossier. JSON STRICT :\n"
         '{"headline":"pourquoi ce compte MAINTENANT selon l_axe","key_signals":[{"label":"...","reading":"..."}],'
         '"strategic_axes":[{"axis":"...","why":"..."}],"key_members":[{"role":"le RÔLE (pas un nom)","why":"...","enrich":"ce que FullEnrich doit trouver"}],'
         '"key_figures":[{"figure":"ordre de grandeur","note":"source/limite"}],'
         f'"pre_written_message":"{msg}","levers":[{{"lever":"...","proof":"..."}}]}}')
    r = fable_call(u, system=BRIEF_SYS, max_tokens=4500, label="brief")
    d = _json_from(r.get("text", ""), "{")
    if not d:
        return {"error": "Claude n'a pas répondu (connexion). Réessayez."}
    d["account_id"] = acc_id; d["axis"] = acc.get("axis")
    _BRIEF_CACHE[acc_id] = d
    return {"brief": d, "cached": False}

# ── DÉTECTION DE CONCURRENTS (onboarding, le moment waouh) ──
DETECT_SYS = ("Tu es l'analyste concurrentiel de Bricks. À partir de la description d'une entreprise, tu listes "
 "ses concurrents B2B les plus directs (ceux qui servent les MÊMES clients). Tu donnes un domaine plausible et "
 "une raison courte. Zéro slop, pas de faux concurrents. Sortie JSON STRICTE.")

def detect_rivals(payload):
    desc = (payload.get("description") or "").strip()
    if len(desc) < 20: raise ValueError("décris ton entreprise en quelques phrases d'abord")
    if not HAVE_FABLE or not read_env().get("ANTHROPIC_API_KEY"):
        return {"rivals": [], "error": "Clé Anthropic absente."}
    sector = payload.get("sector", "")
    u = (f"ENTREPRISE : {desc}\nSecteur : {sector}\n\nListe 8 à 12 concurrents directs. JSON STRICT :\n"
         '[{"name":"...","domain":"...","why":"pourquoi c_est un concurrent direct (1 phrase)"}]')
    r = fable_call(u, system=DETECT_SYS, max_tokens=3000, label="detect")
    arr = _json_from(r.get("text", ""), "[") or []
    return {"rivals": arr}

class ApiError(Exception):
    def __init__(self, code, msg): super().__init__(msg); self.code = code

class Handler(BaseHTTPRequestHandler):
    server_version = "BricksV4/1.0"

    def _json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def _file(self, name, ctype):
        p = os.path.join(HERE, name)
        if not os.path.isfile(p): return self._json(404, {"error": "not found"})
        with open(p, "rb") as f: body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html"): self._file("index.html", "text/html; charset=utf-8")
            elif path == "/seed.json": self._file("seed.json", "application/json; charset=utf-8")
            elif path == "/api/ping": self._json(200, {"app": "bricks-v4", "fable": HAVE_FABLE})
            elif path == "/api/settings": self._json(200, settings_status())
            elif path == "/api/seed": self._json(200, seed())
            else: self._json(404, {"error": f"no endpoint: {path}"})
        except ApiError as e: self._json(e.code, {"error": str(e)})
        except Exception as e: self._json(500, {"error": str(e)})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            try: payload = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError: raise ApiError(400, "invalid JSON")
            if path == "/api/settings": self._json(200, set_key(payload.get("key"), payload.get("value")))
            elif path == "/api/ask": self._json(200, ask(payload))
            elif path == "/api/brief": self._json(200, generate_brief(payload))
            elif path == "/api/detect-rivals": self._json(200, detect_rivals(payload))
            else: raise ApiError(404, f"no endpoint: {path}")
        except (ApiError, ValueError) as e:
            self._json(getattr(e, "code", 400), {"error": str(e)})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def log_message(self, *a): pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8970)
    args = ap.parse_args()
    for port in range(args.port, args.port + 20):
        try: srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        except OSError: continue
        print(f"Bricks V4 -> http://127.0.0.1:{port}", flush=True)
        try: srv.serve_forever()
        except KeyboardInterrupt: srv.server_close()
        return 0
    print("no free port", file=sys.stderr); return 1

if __name__ == "__main__":
    sys.exit(main())
