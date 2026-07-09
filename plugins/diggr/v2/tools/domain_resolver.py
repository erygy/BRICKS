#!/usr/bin/env python3
"""domain_resolver — résolution nom d'entreprise → domaine web, ZÉRO CLÉ. Stdlib only.

LE chaînon de jointure de Bricks V2 : Sillage et FullEnrich identifient les
entreprises par DOMAINE (jamais par SIREN). Sans domaine résolu, un compte
est scorable sur le registre mais invisible des signaux et de l'enrichissement.

Stratégie (gratuite, polie, vérifiée) :
  1. DuckDuckGo lite (html.duckduckgo.com — HTML sans JS, accessible curl)
     avec « "NOM" ville » → candidats de domaines, annuaires blacklistés.
  2. Heuristiques de slug directes (nomcollé.fr, nom-tirets.fr, .com) —
     un domaine qui répond (même 403/WAF) et matche le nom est un candidat.
  3. VÉRIFICATION : fetch de la page d'accueil → les tokens du nom doivent
     apparaître dans le titre/corps (la ville = bonus). Pas de vérité
     vérifiable → confiance dégradée, jamais inventée.

Confiances : high (contenu vérifié) · medium (slug-match fort mais contenu
invérifiable, ex. WAF 403) · none (aucun candidat crédible). Un compte
`none` n'est PAS poussé chez Sillage (quota à vie — pas de gaspillage).

CLI :
  domain_resolver.py resolve --in companies.json --out results.jsonl
                     [--limit 20] [--sleep 1.0]
  domain_resolver.py one --name "EGS CLIM" --ville LYON
Entrée : JSON/JSONL/payload db.py select — champs _id, name, ville.
Sortie : {_id, name, domain, domain_confidence, domain_evidence} ;
`db.py modify --updates -` prêt à l'emploi (receipt en fin).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15")

DIRECTORY_BLACKLIST = (
    "societe.com", "verif.com", "pappers.fr", "annuaire-entreprises",
    "lesentreprises.com", "pagesjaunes.fr", "linkedin.com", "facebook.com",
    "infogreffe", "bodacc", "kompass", "manageo", "figaro", "societe.ninja",
    "checkdirigeant", "dnb.com", "wikipedia", "indeed", "duckduckgo.com",
    "youtube.com", "instagram.com", "leboncoin", "mappy", "yelp",
    "entreprises.gouv", "data.gouv", "datagouv", "score3", "b-reputation",
    "rubypayeur", "creditsafe", "ellisphere", "solvabilite", "annuaire",
    "documents.clerk", "opencorporates", "tripadvisor", "trustpilot",
    "glassdoor", "welcometothejungle", "batiweb", "houzz", "travaux.com",
    "helloartisan", "trouver-un-artisan", "123devis", "quechoisir",
)

STOPWORDS = {"sa", "sas", "sarl", "eurl", "ets", "ste", "societe", "société",
             "entreprise", "groupe", "de", "du", "des", "la", "le", "les",
             "et", "d", "l", "france"}


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _tokens(name: str) -> list[str]:
    base = re.split(r"[(]", name)[0]  # retire les alias entre parenthèses
    words = re.findall(r"[A-Za-zÀ-ÿ0-9]+", _strip_accents(base).lower())
    return [w for w in words if w not in STOPWORDS and (len(w) >= 2 or w.isdigit())]


def _fetch(url: str, timeout: float = 8.0) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "fr"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(200_000).decode("utf-8", errors="replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def _ddg_candidates(query: str) -> list[str]:
    """Domaines candidats depuis DuckDuckGo lite, annuaires exclus, ordonnés."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    status, body = _fetch(url)
    if status != 200:
        return []
    hrefs = re.findall(r"uddg=([^&\"]+)", body)
    domains, seen = [], set()
    for h in hrefs:
        try:
            target = urllib.parse.unquote(h)
            dom = urllib.parse.urlparse(target).netloc.lower().removeprefix("www.")
        except Exception:
            continue
        if not dom or dom in seen:
            continue
        if any(b in dom or b in target.lower() for b in DIRECTORY_BLACKLIST):
            continue
        seen.add(dom)
        domains.append(dom)
    return domains[:4]


def _slug_candidates(name: str) -> list[str]:
    toks = _tokens(name)
    if not toks:
        return []
    joined, dashed = "".join(toks[:3]), "-".join(toks[:3])
    cands = []
    for stem in dict.fromkeys([joined, dashed]):
        if len(stem) < 4:
            continue
        for tld in (".fr", ".com"):
            cands.append(stem + tld)
    return cands


def _verify(domain: str, name: str, ville: str | None) -> tuple[str, str]:
    """→ (confiance, évidence). QUALITÉ AVANT RAPPEL : un nom court/générique
    (SEMA, ELEC…) ne peut JAMAIS valider un domaine sans la ville dans le
    contenu — un faux domaine empoisonne l'évidence ET gaspille le quota
    Sillage. Un patronyme rare (≥6 car.) peut valider seul en medium."""
    toks = _tokens(name)
    if not toks:
        return "none", "nom sans tokens exploitables"
    distinctive = [t for t in toks if len(t) >= 6]
    dom_slug = re.sub(r"[^a-z0-9]", "", domain.split(".")[0])
    slug_hits = sum(1 for t in toks if t in dom_slug)
    slug_strong = (slug_hits >= 2) or any(t in dom_slug for t in distinctive)
    for scheme in ("https://", "http://"):
        status, body = _fetch(scheme + domain, timeout=7)
        if status == 200 and body:
            low = _strip_accents(body).lower()
            content_hits = sum(1 for t in toks if t in low)
            distinctive_hit = any(t in low for t in distinctive)
            ville_hit = bool(ville) and _strip_accents(ville).lower() in low
            full = content_hits >= len(toks)  # tout le nom est dans la page
            if (content_hits >= 2 and ville_hit) or (full and distinctive_hit and ville_hit):
                return "high", f"contenu vérifié ({content_hits}/{len(toks)} tokens + ville)"
            if (content_hits >= 2 and full) or (distinctive_hit and ville_hit):
                return "high", f"contenu vérifié ({content_hits}/{len(toks)} tokens)"
            if distinctive_hit and slug_strong:
                return "medium", "token distinctif (≥6 car.) dans slug et contenu"
            return "none", ("page vivante mais correspondance trop faible "
                            f"({content_hits}/{len(toks)} tokens, ville={'oui' if ville_hit else 'non'})")
        if status in (401, 403, 405, 429, 503) and slug_strong and distinctive:
            return "medium", f"domaine vivant (HTTP {status}, WAF) + slug distinctif"
    if slug_strong:
        return "none", "slug plausible mais domaine injoignable"
    return "none", "aucune correspondance"


def resolve_one(name: str, ville: str | None, sleep_s: float = 1.0) -> dict:
    tried = []
    # 1. recherche DDG
    q = f'"{re.split(r"[(]", name)[0].strip()}" {ville or ""}'.strip()
    for cand in _ddg_candidates(q):
        conf, ev = _verify(cand, name, ville)
        tried.append(cand)
        if conf in ("high", "medium"):
            return {"domain": cand, "domain_confidence": conf,
                    "domain_evidence": f"ddg:{ev}"}
        time.sleep(0.3)
    time.sleep(sleep_s)  # politesse DDG
    # 2. heuristiques slug directes
    for cand in _slug_candidates(name):
        if cand in tried:
            continue
        conf, ev = _verify(cand, name, ville)
        if conf in ("high", "medium"):
            return {"domain": cand, "domain_confidence": conf,
                    "domain_evidence": f"slug:{ev}"}
    return {"domain": None, "domain_confidence": "none",
            "domain_evidence": f"{len(tried)} candidats testés, aucun vérifié"}


def load_rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    try:
        obj = json.loads(text)
        return obj.get("rows", obj) if isinstance(obj, dict) else obj
    except json.JSONDecodeError:
        return [json.loads(l) for l in text.splitlines() if l.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — résolution de domaines zéro-clé")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("resolve")
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--sleep", type=float, default=1.0)
    p = sub.add_parser("one")
    p.add_argument("--name", required=True)
    p.add_argument("--ville")
    args = ap.parse_args(argv)

    if args.cmd == "one":
        r = resolve_one(args.name, args.ville)
        print(json.dumps({"name": args.name, **r}, ensure_ascii=False, indent=2))
        return

    rows = load_rows(args.infile)[: args.limit]
    out, stats = [], {"high": 0, "medium": 0, "none": 0}
    t0 = time.time()
    with open(args.out, "w", encoding="utf-8") as f:
        for i, row in enumerate(rows, 1):
            r = resolve_one(row.get("name", ""), row.get("ville"), args.sleep)
            rec = {"_id": row.get("_id"), "name": row.get("name"), **r}
            stats[r["domain_confidence"]] += 1
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(json.dumps({"i": i, "name": row.get("name", "")[:30],
                              "domain": r["domain"],
                              "conf": r["domain_confidence"]}, ensure_ascii=False),
                  file=sys.stderr)
            time.sleep(args.sleep)
    print(json.dumps({"ok": True, "resolved": stats, "n": len(rows),
                      "elapsed_s": round(time.time() - t0, 1), "out": args.out,
                      "regle": "seuls high/medium sont poussés chez Sillage (quota à vie)"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
