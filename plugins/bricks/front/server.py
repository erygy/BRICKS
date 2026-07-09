#!/usr/bin/env python3
"""Bricks front server — local web UI over the current workspace's database.

Serves the Clay-like table UI (index.html) plus a small JSON API that reuses the
plugin's own tools (tools/core/workspace.py, db.py, envfile.py), so every
mutation goes through exactly the same code paths as the skills.

Run from the user's project root (the directory that contains ./bricks):
    python3 server.py [--port 4321] [--root bricks]

If the port is busy, the next free port is tried (up to +20). On success:
    Bricks UI -> http://127.0.0.1:<port>

Endpoints:
    GET  /                          the UI
    GET  /api/ping                  {"app": "bricks"} — detect a running server
    GET  /api/status                current workspace + tables (UI-shaped JSON)
    GET  /api/table/<name>          {"headers": [...], "rows": [[...], ...]}
    POST /api/table/<name>/remove   {"ids": [3, 7]} — delete rows by _id
    POST /api/workspace/switch      {"name": "<workspace>"} — switch current
    GET  /api/settings              engine keys status (~/.bricks/env) — MASKED
    POST /api/settings              {"key": "...", "value": "..."} — store one key

Rows are addressed by the reserved `_id` column, never by row number. The front
hides `_`-prefixed columns. Binds to 127.0.0.1 only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

FRONT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(FRONT_DIR)
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "tools", "core"))  # workspace, db, envfile

import workspace as ws  # noqa: E402
import db as dbtool     # noqa: E402
import envfile          # noqa: E402

PORT_SCAN_RANGE = 20
ROOT = "bricks"  # overridden by --root in main()


class ApiError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _api_status() -> dict:
    """workspace.status() reshaped into what index.html expects:
    a top-level `currentWorkspace` string, a `current` object carrying the
    workspace's tables, and a flat `workspaces` list of names."""
    st = ws.status(ROOT)
    current = st.get("current")
    out = {
        "initialized": st.get("initialized", False),
        "currentWorkspace": current,
        "workspaces": st.get("workspaces", []),
    }
    if current and current in out["workspaces"]:
        out["current"] = {
            "name": current,
            "path": st.get("path"),
            "db": st.get("db"),
            "tables": st.get("tables", []),
            "context": st.get("context", []),
        }
    return out


def _db_path() -> str:
    """Resolve the current workspace's bricks.db, or raise ApiError."""
    st = ws.status(ROOT)
    if not st.get("initialized"):
        raise ApiError(409, "Bricks is not initialized here — run /bricks:workspace new <name>")
    if not st.get("current"):
        raise ApiError(409, "No current workspace — run /bricks:workspace new <name>")
    path = st.get("db")
    if not path or not os.path.isfile(path):
        raise ApiError(404, "no database yet in this workspace — run a find first")
    return path


def _read_table(name: str) -> dict:
    """Headers + rows (as strings) straight from the workspace database."""
    if not dbtool.IDENT_RE.match(name):
        raise ApiError(400, f"invalid table name: {name!r}")
    path = _db_path()
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise ApiError(500, f"cannot open database: {exc}") from None
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        if not exists:
            raise ApiError(404, f"table not found: {name}")
        cursor = conn.execute(f'SELECT * FROM "{name}"')
        headers = [c[0] for c in cursor.description]
        rows = [["" if v is None else str(v) for v in r] for r in cursor]
    finally:
        conn.close()
    return {"table": name, "headers": headers, "rows": rows}


def _switch_workspace(name) -> dict:
    """Switch the current workspace via the same code path as the skill."""
    if not isinstance(name, str) or not name.strip():
        raise ApiError(400, '"name" must be a non-empty string')
    try:
        ws.switch(name, ROOT)
    except ws.WorkspaceError as exc:
        raise ApiError(400, str(exc)) from None
    return _api_status()


def _remove_rows(name: str, ids) -> dict:
    if not isinstance(ids, list) or not ids:
        raise ApiError(400, '"ids" must be a non-empty list of _id values')
    if not dbtool.IDENT_RE.match(name):
        raise ApiError(400, f"invalid table name: {name!r}")
    try:
        result = dbtool.remove(_db_path(), name, ids)
    except dbtool.DbError as exc:
        raise ApiError(400, str(exc)) from None
    return {"ok": True, "table": name, "removed": result["removed"], "rows": result["rows"]}


# --------------------------------------------------------------------------
# Fiche & week endpoints (read: db.py only; write: outreach approve only)
# --------------------------------------------------------------------------

def _safe_rows(path: str, table: str, where: str | None = None) -> list[dict]:
    """Tolerant select — tables and columns are dynamic, absence is data."""
    try:
        return dbtool.select(path, table, where=where, limit=-1)["rows"]
    except dbtool.DbError:
        return []


def _by_id(rows: list[dict]) -> dict:
    return {str(r["_id"]): r for r in rows}


def _int_id(value) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid id: {value!r}") from None


def _graph(table: str, row_id: int) -> dict:
    """The FK sub-graph of one company or contact — the SAME screen for both
    (contract: le graphe = les FK, rien d'autre)."""
    path = _db_path()
    if table not in ("companies", "contacts"):
        raise ApiError(400, "graph is defined for companies and contacts only")
    center_rows = _safe_rows(path, table, f"_id={row_id}")
    if not center_rows:
        raise ApiError(404, f"{table} row {row_id} not found")
    center = center_rows[0]

    if table == "contacts":
        company = None
        cid = str(center.get("company_id") or "").strip()
        if cid.isdigit():
            found = _safe_rows(path, "companies", f"_id={int(cid)}")
            company = found[0] if found else None
        contacts = (_safe_rows(path, "contacts", f"company_id='{int(cid)}'")
                    if cid.isdigit() else [center])
    else:
        company = center
        contacts = _safe_rows(path, "contacts", f"company_id='{row_id}'")

    company_key = str((company or {}).get("_id") or "")
    contact_ids = {str(c["_id"]) for c in contacts}
    signals = []
    seen = set()
    if company_key:
        for s in _safe_rows(path, "signals", f"company_id='{int(company_key)}'"):
            seen.add(str(s["_id"]))
            signals.append(s)
    for c in sorted(contact_ids, key=int):
        for s in _safe_rows(path, "signals", f"contact_id='{int(c)}'"):
            if str(s["_id"]) not in seen:
                seen.add(str(s["_id"]))
                signals.append(s)
    signals.sort(key=lambda s: str(s.get("signal_date") or ""), reverse=True)

    comp_ids = sorted({int(str(s.get("competitor_id")))
                       for s in signals
                       if str(s.get("competitor_id") or "").strip().isdigit()})
    competitors = (_safe_rows(path, "competitors",
                              f"_id IN ({','.join(map(str, comp_ids))})")
                   if comp_ids else [])

    outreach = []
    for c in sorted(contact_ids, key=int):
        outreach.extend(_safe_rows(path, "outreach", f"contact_id='{int(c)}'"))

    return {"ok": True, "entity": table, "center": center,
            "company": company, "contacts": contacts,
            "signals": signals, "competitors": competitors,
            "outreach": outreach}


_WEEK_COLS = ["week", "contact", "position", "company", "phone", "email",
              "priority_tier", "priority_score", "why_now", "strategy",
              "status", "audit_score", "draft_status"]


def _week() -> dict:
    """The 'To contact this week' view — outreach ⋈ contacts ⋈ companies.
    Table-shaped so the existing grid renders it; `_`-prefixed columns stay
    hidden but ride along for the click-through (contract: le front lit tout
    via db.py, il n'écrit QUE outreach.status draft→approved)."""
    path = _db_path()
    queue = _safe_rows(path, "outreach")
    contacts = _by_id(_safe_rows(path, "contacts"))
    companies = _by_id(_safe_rows(path, "companies"))
    queue.sort(key=lambda r: (str(r.get("week") or ""),
                              -float(str((contacts.get(str(r.get("contact_id")))
                                          or {}).get("priority_score") or 0)
                                     if str((contacts.get(str(r.get("contact_id")))
                                             or {}).get("priority_score") or "")
                                     .replace(".", "", 1).lstrip("-").isdigit()
                                     else 0)))
    headers = ["_outreach_id", "_contact_id"] + _WEEK_COLS
    rows = []
    for q in queue:
        contact = contacts.get(str(q.get("contact_id"))) or {}
        company = companies.get(str(contact.get("company_id"))) or {}
        rows.append([
            str(q.get("_id")), str(contact.get("_id") or ""),
            q.get("week") or "", contact.get("full_name") or "",
            contact.get("position") or "", company.get("name") or "",
            contact.get("phone") or "", contact.get("email") or "",
            contact.get("priority_tier") or "",
            contact.get("priority_score") or "",
            contact.get("why_now") or "", q.get("strategy") or "",
            q.get("status") or "", q.get("audit_score") or "",
            q.get("draft_status") or ""])
    return {"table": "to_contact_this_week", "headers": headers,
            "rows": [["" if v is None else str(v) for v in r] for r in rows]}


def _approve(outreach_id: int) -> dict:
    """The front's ONLY write (contract): outreach.status draft → approved.
    The blocking audit is enforced here too: audit_score < 70 never passes."""
    path = _db_path()
    rows = _safe_rows(path, "outreach", f"_id={outreach_id}")
    if not rows:
        raise ApiError(404, f"outreach row {outreach_id} not found")
    row = rows[0]
    status = str(row.get("status") or "").strip()
    if status != "draft":
        raise ApiError(409, f"seuls les drafts s'approuvent (statut actuel : "
                            f"{status or '∅'})")
    score = str(row.get("audit_score") or "").strip()
    if score.isdigit() and int(score) < 70:
        raise ApiError(409, f"audit bloquant : score {score} < 70 — resserre "
                            "le draft et re-lance l'audit")
    try:
        dbtool.modify(path, "outreach",
                      updates=[{"_id": outreach_id, "status": "approved"}])
    except dbtool.DbError as exc:
        raise ApiError(400, str(exc)) from None
    return {"ok": True, "_id": outreach_id, "status": "approved"}


def _set_setting(payload: dict) -> dict:
    """Store one engine key in ~/.bricks/env; the value is never echoed."""
    try:
        return envfile.set_key(payload.get("key"), payload.get("value"))
    except ValueError as exc:
        raise ApiError(400, str(exc)) from None


class Handler(BaseHTTPRequestHandler):
    server_version = "BricksFront/0.2"

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_index(self) -> None:
        with open(os.path.join(FRONT_DIR, "index.html"), "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html"):
                self._send_index()
            elif path == "/api/ping":
                self._send_json(200, {"app": "bricks", "root": os.path.abspath(ROOT)})
            elif path == "/api/status":
                self._send_json(200, _api_status())
            elif path == "/api/settings":
                self._send_json(200, envfile.status())
            elif path == "/api/week":
                self._send_json(200, _week())
            elif path.startswith("/api/graph/"):
                match = re.fullmatch(r"/api/graph/([a-z_]+)/(\d+)", path)
                if not match:
                    raise ApiError(400, "expected /api/graph/<table>/<id>")
                self._send_json(200, _graph(match.group(1),
                                            _int_id(match.group(2))))
            elif path.startswith("/api/table/"):
                self._send_json(200, _read_table(path[len("/api/table/"):]))
            else:
                self._send_json(404, {"ok": False, "error": f"no such endpoint: {path}"})
        except ApiError as exc:
            self._send_json(exc.code, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        match = re.fullmatch(r"/api/table/([^/]+)/remove", path)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as exc:
                raise ApiError(400, f"invalid JSON body: {exc}") from None
            approve = re.fullmatch(r"/api/outreach/(\d+)/approve", path)
            if path == "/api/workspace/switch":
                self._send_json(200, _switch_workspace(payload.get("name")))
            elif path == "/api/settings":
                self._send_json(200, _set_setting(payload))
            elif approve:
                self._send_json(200, _approve(_int_id(approve.group(1))))
            elif match:
                self._send_json(200, _remove_rows(match.group(1), payload.get("ids")))
            else:
                raise ApiError(404, f"no such endpoint: {path}")
        except ApiError as exc:
            self._send_json(exc.code, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args) -> None:
        pass  # keep background-task output quiet


def main(argv=None) -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Bricks front server (local only).")
    parser.add_argument("--port", type=int, default=4321)
    parser.add_argument("--root", default="bricks", help="Bricks data root (default: ./bricks)")
    args = parser.parse_args(argv)
    ROOT = args.root

    for port in range(args.port, args.port + PORT_SCAN_RANGE):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        except OSError:
            continue
        print(f"Bricks UI -> http://127.0.0.1:{port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.server_close()
        return 0

    print(json.dumps({"ok": False,
                      "error": f"no free port in {args.port}..{args.port + PORT_SCAN_RANGE - 1}"}),
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
