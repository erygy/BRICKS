#!/usr/bin/env python3
"""Appel Fable 5 robuste face au mur de connexion Mac→Anthropic.
Streaming via curl (SSE) : les tokens circulent en continu, la connexion ne se
fait plus couper au repos ('Remote end closed'). La clé passe par un fichier de
config curl (-K), jamais en argv (invisible dans ps). Réflexion Fable = toujours
active (l'API refuse thinking:disabled) ; les deltas de réflexion sont ignorés,
seuls les text_delta sont accumulés."""
import json, os, time, subprocess, tempfile

def _key():
    for line in open(os.path.expanduser("~/.bricks/env")):
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.strip().split("=", 1)[1]
    raise SystemExit("clé absente dans ~/.bricks/env")

_KEY = _key()
_CFG = os.path.expanduser("~/.bricks/_curlcfg")
with open(_CFG, "w") as _f:
    _f.write('header = "x-api-key: %s"\n' % _KEY)
    _f.write('header = "anthropic-version: 2023-06-01"\n')
    _f.write('header = "content-type: application/json"\n')
os.chmod(_CFG, 0o600)

def call(user, system=None, max_tokens=9000, label="", retries=5):
    body = {"model": "claude-fable-5", "max_tokens": max_tokens, "stream": True,
            "messages": [{"role": "user", "content": user}]}
    if system:
        body["system"] = system
    for att in range(retries):
        bf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir="/tmp")
        json.dump(body, bf); bf.close()
        try:
            p = subprocess.run(
                ["curl", "-sS", "-N", "--max-time", "600",
                 "--retry", "2", "--retry-connrefused",
                 "-X", "POST", "https://api.anthropic.com/v1/messages",
                 "-K", _CFG, "-d", "@" + bf.name],
                capture_output=True, text=True, timeout=650)
            txt = []; itok = otok = 0; stop = ""; err = None
            for line in p.stdout.splitlines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    ev = json.loads(payload)
                except Exception:
                    continue
                t = ev.get("type")
                if t == "message_start":
                    itok = ev.get("message", {}).get("usage", {}).get("input_tokens", 0)
                elif t == "content_block_delta":
                    d = ev.get("delta", {})
                    if d.get("type") == "text_delta":
                        txt.append(d.get("text", ""))
                elif t == "message_delta":
                    otok = ev.get("usage", {}).get("output_tokens", otok)
                    stop = ev.get("delta", {}).get("stop_reason", stop) or stop
                elif t == "error":
                    err = ev.get("error", {})
            full = "".join(txt)
            os.unlink(bf.name)
            if full.strip():
                return {"label": label, "text": full, "in": itok, "out": otok,
                        "stop": stop or "end_turn"}
            # vide : coupure connexion ou erreur API → retry avec backoff
            if err and att == retries - 1:
                return {"label": label, "in": 0, "out": 0, "stop": "error",
                        "text": "[ERREUR API %s] %s" % (err.get("type"), str(err.get("message", ""))[:200])}
            time.sleep(3 * (att + 1)); continue
        except Exception as e:
            try:
                os.unlink(bf.name)
            except Exception:
                pass
            if att < retries - 1:
                time.sleep(3 * (att + 1)); continue
            return {"label": label, "text": "[ERREUR %s]" % e, "in": 0, "out": 0, "stop": "error"}
    return {"label": label, "text": "[ERREUR retries épuisés]", "in": 0, "out": 0, "stop": "error"}
