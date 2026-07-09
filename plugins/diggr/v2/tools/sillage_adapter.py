#!/usr/bin/env python3
"""sillage_adapter — couche anti-corruption Sillage pour Bricks V2. Stdlib only.

Le modèle opérationnel RÉEL de Sillage (doc publique getsillage.com, 08/07/2026) :
Sillage n'est PAS un moteur de découverte firmographique — c'est un moteur de
DÉTECTION DE SIGNAUX sur une liste de comptes qu'on lui fournit :

    1. push_top_accounts(domaines/LinkedIn)      [async : 202 → poll]
    2. upsert_persona(thèse)                     [oriente les agents]
    3. ensure_agents(détecteurs)                 [8 types : keyword_detection,
       job_posting_keyword_detection, job_update, competitor, partner,
       customer, influencer, champion]
    4. launch_signal_run() → poll                [PAS de webhook : poller]
    5. query_signals(curseur)                    [→ évidence pour score_v2]

⚠️ Sillage ne connaît PAS le SIREN. Identité = domaine / handle LinkedIn.
La jointure registre↔Sillage↔FullEnrich passe par la RÉSOLUTION DE DOMAINE
(étape du pipeline, cf. resolve_domains — mock ici, engine V1 web au Day-1).

Backends :
  - MockSillage : univers réel du field-test 08/07 + signaux synthétiques
    DÉTERMINISTES (seed fixe) — toute la chaîne tourne aujourd'hui.
  - RestSillage : base https://api.getsillage.com, Bearer ~/.bricks/env
    SILLAGE_API_KEY. Chemins v2 dans schema/sillage.endpoints.json — statut
    documented|to_confirm ; le rituel Day-1 (DAY1-SILLAGE.md) télécharge
    l'OpenAPI (/api/v1/docs/spec) et gèle les to_confirm.
  - MCP (recommandé en session) : https://api.getsillage.com/api/mcp/v2,
    OAuth — outils sillage_v2_*. discover_from_mcp_tools() transforme la
    liste des outils MCP en catalogue de capacités.

CLI :
  sillage_adapter.py mock-demo            # chaîne complète sur l'univers mock
  sillage_adapter.py compile --tree T     # arbre → specs d'agents Sillage
  sillage_adapter.py discover --tools-json F  # outils MCP → capabilities.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
V2ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(V2ROOT, "fixtures")
SCHEMA = os.path.join(V2ROOT, "schema")

REST_BASE = "https://api.getsillage.com"
MCP_URL = "https://api.getsillage.com/api/mcp/v2"
ENV_FILE = os.path.expanduser("~/.bricks/env")

SIGNAL_KINDS = ["keyword_detection", "job_posting_keyword_detection", "job_update",
                "competitor", "partner", "customer", "influencer", "champion"]


def _env(key: str) -> str | None:
    if os.environ.get(key):
        return os.environ[key]
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1]
    return None


class NotConfigured(RuntimeError):
    """Levée par RestSillage tant que la clé/les endpoints ne sont pas confirmés."""


# --------------------------------------------------------------------------
# Compilation : arbre de signaux → configuration Sillage
# --------------------------------------------------------------------------

def compile_agent_specs(tree: dict) -> list[dict]:
    """Extrait des proxies source=sillage les AGENTS à créer chez Sillage.

    Un proxy `sillage.agents.keyword_detection` avec value=[mots-clés] devient
    un agent keyword_detection portant ce pack de mots-clés ; idem pour les
    offres d'emploi. job_update n'a pas de mots-clés (suivi de contacts).
    """
    specs = {}
    for sig in tree.get("signals", []):
        for p in sig.get("proxies", []):
            if p.get("source") != "sillage":
                continue
            cap = p.get("capability", "")
            kind = cap.split(".")[-1]
            if kind not in SIGNAL_KINDS:
                continue
            key = kind
            spec = specs.setdefault(key, {"kind": kind, "keywords": [],
                                          "feeds_proxies": []})
            if isinstance(p.get("value"), list) and kind.endswith("keyword_detection"):
                spec["keywords"].extend(v for v in p["value"] if v not in spec["keywords"])
            spec["feeds_proxies"].append({"proxy_id": p["id"], "signal_id": sig["id"]})
    return list(specs.values())


def signals_to_evidence(signals: list[dict], tree: dict, domain_index: dict) -> list[dict]:
    """Signaux Sillage → lignes d'évidence score_v2 (company_id, proxy_id, value, date, url).

    domain_index : domaine → company_id (issu de la résolution de domaine).
    Mapping : type de signal + mots-clés trouvés → les proxies que ce type nourrit.
    """
    routes = {}
    for spec in compile_agent_specs(tree):
        for f in spec["feeds_proxies"]:
            routes.setdefault(spec["kind"], []).append(f)
    out, unmatched = [], 0
    for s in signals:
        kind = s.get("signal_type", "")
        snake = "".join("_" + c.lower() if c.isupper() else c for c in kind).lstrip("_")
        cid = domain_index.get((s.get("company_domain") or "").lower())
        if cid is None:
            unmatched += 1
            continue
        for f in routes.get(snake, []):
            out.append({"company_id": cid, "proxy_id": f["proxy_id"], "value": True,
                        "event_date": (s.get("signal_date") or s.get("detected_at", ""))[:10],
                        "evidence_url": s.get("source_url")})
    if unmatched:
        out.append({"_receipt": f"{unmatched} signaux sans domaine joignable (résolution à compléter)"})
    return out


def resolve_domains(companies: list[dict], mode: str = "mock") -> dict:
    """name → domaine. MOCK UNIQUEMENT (démo) : domaine synthétique déterministe,
    collisions suffixées bruyamment. En PROD, la résolution passe par l'engine V1
    (runner.py --tools web) ou FullEnrich company/search — cf. DAY1 §C : ce mock
    ne doit JAMAIS servir de fallback réel (empoisonnement d'évidence, red-team B3)."""
    if mode != "mock":
        raise RuntimeError("resolve_domains: seul le mode mock est implémenté ici — "
                           "en prod, utiliser l'engine V1 web (DAY1 §C), jamais ce stub")
    index, collisions = {}, 0
    for c in companies:
        slug = "".join(ch for ch in (c.get("name") or "").lower() if ch.isalnum())[:24]
        dom, n = f"{slug}.fr", 2
        while dom in index:
            collisions += 1
            dom = f"{slug}-{n}.fr"; n += 1
        index[dom] = c["_id"]
    if collisions:
        print(json.dumps({"warning": f"{collisions} collisions de domaines mock suffixées"}),
              file=sys.stderr)
    return index


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------

class MockSillage:
    """Backend mock déterministe : signaux synthétiques plausibles sur l'univers réel."""

    def __init__(self, universe_path=os.path.join(FIXTURES, "mock-universe.jsonl")):
        self.accounts, self.agents, self.runs = [], [], 0
        self.universe = [json.loads(l) for l in open(universe_path, encoding="utf-8") if l.strip()]

    def capabilities(self):
        return json.load(open(os.path.join(FIXTURES, "sillage.capabilities.json"), encoding="utf-8"))

    def push_top_accounts(self, accounts):
        self.accounts.extend(accounts)
        return {"accepted": len(accounts), "status": "ingesting(202→poll)",
                "quota_note": "trial = cap à vie (top-account-quota-exceeded)"}

    def upsert_persona(self, thesis):
        return {"ok": True, "persona": thesis.get("persona", {}).get("role")}

    def ensure_agents(self, specs):
        self.agents = [{"id": f"agt_{i}", **s} for i, s in enumerate(specs, 1)]
        return self.agents

    def launch_signal_run(self):
        self.runs += 1
        return f"run_{self.runs}"

    def poll_signal_run(self, run_id):
        return {"id": run_id, "state": "completed"}

    def query_signals(self, cursor=None, limit=100):
        """~8 % des comptes émettent un job_posting DG, ~4 % un post transmission.
        Déterministe : hash(domaine) — jamais de random sans seed (rejouabilité)."""
        sigs = []
        for a in self.accounts:
            h = int(hashlib.sha1(a["domain"].encode()).hexdigest(), 16)
            if h % 100 < 8:
                sigs.append({"id": f"sig_jp_{h % 10**8}", "signal_type": "jobPostingKeywordDetection",
                             "company_domain": a["domain"], "signal_date": "2026-06-20",
                             "detected_at": "2026-07-01",
                             "source_url": f"https://jobs.example/{a['domain']}",
                             "excerpt": "recrute un directeur d'exploitation"})
            if h % 100 >= 96:
                sigs.append({"id": f"sig_kw_{h % 10**8}", "signal_type": "keywordDetection",
                             "company_domain": a["domain"], "signal_date": "2026-06-28",
                             "detected_at": "2026-07-02",
                             "source_url": f"https://linkedin.com/posts/{a['domain']}",
                             "data": {"keywords_found": ["transmission", "passer la main"]}})
        return sigs[:limit], None


class RestSillage:
    """Backend REST v2 — Bearer sk_live_. Chemins dans schema/sillage.endpoints.json ;
    ceux marqués to_confirm lèvent NotConfigured tant que le Day-1 ne les a pas gelés."""

    def __init__(self):
        self.key = _env("SILLAGE_API_KEY")
        if not self.key:
            raise NotConfigured(
                "SILLAGE_API_KEY absent de ~/.bricks/env — au Day-1 : Settings → API Keys "
                "(génération parfois à activer par le support), ou utiliser le MCP OAuth : "
                f"claude mcp add --transport http sillage {MCP_URL}")
        with open(os.path.join(SCHEMA, "sillage.endpoints.json"), encoding="utf-8") as f:
            self.endpoints = json.load(f)

    def _call(self, name, payload=None, method="POST"):
        ep = self.endpoints["endpoints"].get(name)
        if not ep:
            raise NotConfigured(f"endpoint {name!r} inconnu du manifest")
        if ep.get("status") == "to_confirm":
            raise NotConfigured(
                f"endpoint {name!r} = {ep['path']} NON CONFIRMÉ — Day-1 : télécharger "
                f"l'OpenAPI ({REST_BASE}/api/v1/docs/spec) et geler le chemin réel")
        req = urllib.request.Request(
            REST_BASE + ep["path"], method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            # RFC 9457 problem+json : remonter structuré, jamais crasher le batch.
            body = e.read().decode(errors="replace")
            try:
                problem = json.loads(body)
            except json.JSONDecodeError:
                problem = {"raw": body[:400]}
            return {"ok": False, "status": e.code, "problem": problem,
                    "retry_after": e.headers.get("Retry-After"),
                    "request_id": e.headers.get("X-Request-Id")}

    def capabilities(self):
        return json.load(open(os.path.join(FIXTURES, "sillage.capabilities.json"), encoding="utf-8"))

    def push_top_accounts(self, accounts):
        return self._call("top_accounts_add", {"accounts": accounts})

    def upsert_persona(self, thesis):
        return self._call("persona_upsert", {"description": thesis.get("statement")})

    def ensure_agents(self, specs):
        return [self._call("agents_create", s) for s in specs]

    def launch_signal_run(self):
        return self._call("signal_runs_launch", {})

    def poll_signal_run(self, run_id):
        return self._call("signal_runs_get", {"id": run_id}, method="GET")

    def query_signals(self, cursor=None, limit=100):
        payload = {"limit": limit}
        if cursor:
            payload["cursor"] = cursor
        r = self._call("signals_query", payload)
        return r.get("data", []), (r.get("meta") or {}).get("next_cursor")


# --------------------------------------------------------------------------
# Découverte MCP → catalogue de capacités
# --------------------------------------------------------------------------

def discover_from_mcp_tools(tools: list[dict]) -> dict:
    """Liste d'outils MCP (name/description/inputSchema) → capabilities.json.
    Day-1 : exporter la liste des outils sillage_v2_* et la passer ici."""
    caps = []
    for t in tools:
        name = t.get("name", "")
        if not name.startswith("sillage"):
            continue
        kind = ("signal_kind" if "signal" in name
                else "enrichment" if "enrich" in name or "mapping" in name
                else "search_filter" if any(k in name for k in ("account", "watchlist", "persona"))
                else "company_field")
        caps.append({"key": f"mcp.{name}", "kind": kind,
                     "params": (t.get("inputSchema") or {}).get("properties", {}),
                     "cost_class": 1, "status": "confirmed",
                     "notes": (t.get("description") or "")[:140]})
    return {"source": "sillage", "transport": "mcp",
            "discovered_at": "REMPLIR-AU-DAY1", "identity_key": "company_domain|linkedin",
            "capabilities": caps, "quotas": {}, "probe_log": []}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_mock_demo(_args):
    tree = json.load(open(os.path.join(FIXTURES, "memoval-signals.json"), encoding="utf-8"))
    thesis = json.load(open(os.path.join(FIXTURES, "memoval-thesis.json"), encoding="utf-8"))
    sil = MockSillage()
    icp = [c for c in sil.universe if c.get("status") == "new"]
    index = resolve_domains(icp)
    inv = {v: k for k, v in index.items()}
    print(json.dumps({"1_resolution_domaines": {"comptes": len(icp), "résolus_mock": len(index)}},
                     ensure_ascii=False))
    r = sil.push_top_accounts([{"domain": inv[c["_id"]]} for c in icp if c["_id"] in inv])
    print(json.dumps({"2_push_top_accounts": r}, ensure_ascii=False))
    print(json.dumps({"3_persona": sil.upsert_persona(thesis)}, ensure_ascii=False))
    specs = compile_agent_specs(tree)
    agents = sil.ensure_agents(specs)
    print(json.dumps({"4_agents": [{"kind": a["kind"], "keywords": a["keywords"][:4],
                                    "nourrit": [f["proxy_id"] for f in a["feeds_proxies"]]}
                                   for a in agents]}, ensure_ascii=False, indent=2))
    run = sil.launch_signal_run()
    state = sil.poll_signal_run(run)
    sigs, _ = sil.query_signals()
    print(json.dumps({"5_signal_run": state, "signaux": len(sigs)}, ensure_ascii=False))
    ev = signals_to_evidence(sigs, tree, index)
    receipt = [e for e in ev if "_receipt" in e]
    ev = [e for e in ev if "_receipt" not in e]
    out = os.path.join(FIXTURES, "mock-sillage-evidence.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for e in ev:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(json.dumps({"6_evidence_pour_score_v2": {"lignes": len(ev), "out": out,
                                                   "notes": receipt}}, ensure_ascii=False))


def cmd_compile(args):
    tree = json.load(open(args.tree, encoding="utf-8"))
    print(json.dumps(compile_agent_specs(tree), ensure_ascii=False, indent=2))


def cmd_discover(args):
    tools = json.load(open(args.tools_json, encoding="utf-8"))
    caps = discover_from_mcp_tools(tools if isinstance(tools, list) else tools.get("tools", []))
    out = args.out or os.path.join(FIXTURES, "sillage.capabilities.discovered.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(caps, f, ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, "capabilities": len(caps["capabilities"]), "out": out},
                     ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — adapter Sillage")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mock-demo")
    p = sub.add_parser("compile"); p.add_argument("--tree", required=True)
    p = sub.add_parser("discover"); p.add_argument("--tools-json", required=True); p.add_argument("--out")
    args = ap.parse_args(argv)
    {"mock-demo": cmd_mock_demo, "compile": cmd_compile, "discover": cmd_discover}[args.cmd](args)


if __name__ == "__main__":
    main()
