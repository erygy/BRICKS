#!/usr/bin/env python3
"""outreach_send — l'envoi RÉEL, sous triple clé. Stdlib only (smtplib/imaplib).

Le chaînon qui transforme des drafts en premiers clients — sans jamais
sacrifier la doctrine V1 « rien ne part sans un humain » :

  CLÉ 1  dry-run PAR DÉFAUT : `send` sans --live n'envoie RIEN (il montre).
  CLÉ 2  GO campagne : --live exige --campaign-approved "<nom-campagne>"
         (l'humain a vu template + exemples + volumes — SEND-GUARD).
  CLÉ 3  caps codés : max N envois/jour (défaut 20 — délivrabilité d'un
         compte perso), fenêtre horaire, suppression list, stop sur replied.

Boucle complète : messages(status='approved') → SMTP → status='sent'
(+sent_at) → `check-replies` (IMAP) → matche les From → status='replied'
+ TOUTE la séquence du contact est gelée (plus une touche) → les événements
nourrissent verdict.py (assess) — la campagne EST l'expérience.

Config ~/.bricks/env (chmod 600) :
  SMTP_HOST=smtp.gmail.com  SMTP_PORT=587  SMTP_USER=...  SMTP_PASS=...
  SMTP_FROM="Thomas Jebabli <thomas@...>"
  IMAP_HOST=imap.gmail.com  IMAP_USER=...  IMAP_PASS=...
  (Gmail : mot de passe d'application, pas le mot de passe du compte.)

CLI :
  outreach_send.py send --db bricks.db [--live --campaign-approved NOM]
                   [--cap 20] [--window 08:30-18:30]
  outreach_send.py check-replies --db bricks.db [--since-days 7]
  outreach_send.py status --db bricks.db
  outreach_send.py export-campaign --db bricks.db --out campaign.json
        (→ compte sent/replies/meetings pour verdict.py assess)
"""

from __future__ import annotations

import argparse
import datetime as dt
import email
import email.utils
import imaplib
import json
import os
import re
import smtplib
import sqlite3
import sys
import time
from email.header import decode_header
from email.mime.text import MIMEText

ENV_FILE = os.path.expanduser("~/.bricks/env")


def _env(key: str) -> str | None:
    if os.environ.get(key):
        return os.environ[key]
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def _db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _ensure_columns(con, table, cols):
    existing = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
    for c, typ in cols.items():
        if c not in existing:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {c} {typ}")
    con.commit()


def _in_window(window: str) -> bool:
    try:
        lo, hi = window.split("-")
        now = dt.datetime.now().strftime("%H:%M")
        return lo <= now <= hi
    except ValueError:
        return True


# --------------------------------------------------------------------------
# SEND
# --------------------------------------------------------------------------

def cmd_send(a):
    con = _db(a.db)
    _ensure_columns(con, "messages", {"sent_at": "TEXT", "send_error": "TEXT"})
    sup = set(filter(None, (a.suppress or "").lower().split(",")))
    today = dt.date.today().isoformat()
    already = con.execute(
        "SELECT COUNT(*) FROM messages WHERE status='sent' AND substr(sent_at,1,10)=?",
        (today,)).fetchone()[0]
    budget = max(0, a.cap - already)

    rows = con.execute(
        "SELECT m.rowid AS rid, m.* FROM messages m WHERE m.status='approved' "
        "AND m.channel='email' ORDER BY m.send_day, m.rowid").fetchall()
    # gel des contacts déjà en replied : plus une touche
    frozen = {r["company_id"] for r in con.execute(
        "SELECT DISTINCT company_id FROM messages WHERE status='replied'")}
    queue = []
    for r in rows:
        to = (r["to_email"] if "to_email" in r.keys() else None)
        if not to:
            continue
        if to.lower() in sup or r["company_id"] in frozen:
            continue
        queue.append(r)
    queue = queue[:budget]

    receipt = {"mode": "LIVE" if a.live else "DRY-RUN", "cap_jour": a.cap,
               "deja_envoyes_aujourdhui": already, "en_file_approved": len(rows),
               "eligibles_dans_le_budget": len(queue),
               "fenetre": a.window, "dans_fenetre": _in_window(a.window)}

    if not a.live:
        receipt["apercu"] = [{"to": q["to_email"], "subject": q["subject"],
                              "body_head": (q["body"] or "")[:90]} for q in queue[:3]]
        receipt["rappel"] = ("RIEN n'a été envoyé. Pour envoyer : --live "
                             "--campaign-approved '<nom>' (= le GO campagne du SEND-GUARD).")
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return

    if not a.campaign_approved:
        raise SystemExit(json.dumps({"ok": False, "error":
            "--live exige --campaign-approved '<nom-campagne>' — le GO humain "
            "de niveau campagne n'est pas contournable (SEND-GUARD)."}))
    if not _in_window(a.window):
        raise SystemExit(json.dumps({"ok": False, "error":
            f"hors fenêtre d'envoi {a.window} — relancer dans la fenêtre "
            "(les dirigeants lisent le matin ; la nuit = spam)"}))

    host, port = _env("SMTP_HOST"), int(_env("SMTP_PORT") or 587)
    user, pw, sender = _env("SMTP_USER"), _env("SMTP_PASS"), _env("SMTP_FROM")
    if not all((host, user, pw, sender)):
        raise SystemExit(json.dumps({"ok": False, "error":
            "SMTP_HOST/SMTP_USER/SMTP_PASS/SMTP_FROM manquants dans ~/.bricks/env"}))

    sent, errors = 0, 0
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(user, pw)
        for q in queue:
            msg = MIMEText(q["body"], "plain", "utf-8")
            msg["Subject"] = q["subject"] or "prise de contact"
            msg["From"] = sender
            msg["To"] = q["to_email"]
            msg["Message-ID"] = email.utils.make_msgid(domain=sender.split("@")[-1].rstrip(">"))
            try:
                smtp.send_message(msg)
                con.execute("UPDATE messages SET status='sent', sent_at=? WHERE rowid=?",
                            (dt.datetime.now().isoformat(timespec="seconds"), q["rid"]))
                con.commit()
                sent += 1
                time.sleep(a.pause)   # espacement humain — jamais de rafale
            except Exception as e:  # un échec ne tue pas le batch
                con.execute("UPDATE messages SET send_error=? WHERE rowid=?",
                            (str(e)[:200], q["rid"]))
                con.commit()
                errors += 1
    receipt.update({"envoyes": sent, "erreurs": errors,
                    "campagne": a.campaign_approved})
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------
# CHECK-REPLIES (IMAP) — détecter les réponses, geler les séquences
# --------------------------------------------------------------------------

def _decode(h) -> str:
    if not h:
        return ""
    parts = decode_header(h)
    return "".join(p.decode(c or "utf-8", errors="replace") if isinstance(p, bytes)
                   else p for p, c in parts)


def cmd_check_replies(a):
    con = _db(a.db)
    _ensure_columns(con, "messages", {"replied_at": "TEXT", "reply_from": "TEXT"})
    host = _env("IMAP_HOST")
    user, pw = _env("IMAP_USER") or _env("SMTP_USER"), _env("IMAP_PASS") or _env("SMTP_PASS")
    if not all((host, user, pw)):
        raise SystemExit(json.dumps({"ok": False, "error":
            "IMAP_HOST/IMAP_USER/IMAP_PASS manquants dans ~/.bricks/env"}))

    sent_rows = con.execute(
        "SELECT rowid AS rid, company_id, to_email FROM messages "
        "WHERE status='sent' AND to_email IS NOT NULL").fetchall()
    watch = {}
    for r in sent_rows:
        watch.setdefault(r["to_email"].lower(), []).append(r)
    if not watch:
        print(json.dumps({"ok": True, "note": "aucun message 'sent' à surveiller"}))
        return

    since = (dt.date.today() - dt.timedelta(days=a.since_days)).strftime("%d-%b-%Y")
    M = imaplib.IMAP4_SSL(host)
    M.login(user, pw)
    M.select("INBOX", readonly=True)
    _, data = M.search(None, f'(SINCE "{since}")')
    ids = data[0].split()
    hits = []
    for mid in ids[-300:]:                       # borne de politesse
        _, msg_data = M.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        raw = msg_data[0][1].decode("utf-8", errors="replace")
        m = email.message_from_string(raw)
        frm = email.utils.parseaddr(_decode(m.get("From")))[1].lower()
        if frm in watch:
            hits.append((frm, _decode(m.get("Subject")), m.get("Date")))
    M.logout()

    replied_contacts = set()
    for frm, subj, date in hits:
        for r in watch[frm]:
            con.execute("UPDATE messages SET status='replied', replied_at=?, reply_from=? "
                        "WHERE rowid=?", (date, frm, r["rid"]))
            replied_contacts.add(r["company_id"])
    # GEL : toute la séquence des contacts qui ont répondu (plus une touche)
    for cid in replied_contacts:
        con.execute("UPDATE messages SET status='frozen' WHERE company_id=? "
                    "AND status IN ('approved','draft')", (cid,))
    con.commit()
    print(json.dumps({"ok": True, "reponses_detectees": len(hits),
                      "contacts_geles": len(replied_contacts),
                      "detail": [{"from": h[0], "subject": h[1][:60]} for h in hits[:10]],
                      "rappel": "qualifier chaque réponse à la main : "
                                "positive → meetings dans campaign.json ; negative → suppression"},
                     ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------
# STATUS / EXPORT-CAMPAIGN
# --------------------------------------------------------------------------

def cmd_status(a):
    con = _db(a.db)
    rows = con.execute("SELECT status, COUNT(*) n FROM messages GROUP BY status").fetchall()
    print(json.dumps({"messages": {r["status"]: r["n"] for r in rows}},
                     ensure_ascii=False, indent=2))


def cmd_export(a):
    con = _db(a.db)
    sent = con.execute("SELECT COUNT(*) FROM messages WHERE status IN "
                       "('sent','replied','frozen')").fetchone()[0]
    replied = con.execute("SELECT COUNT(DISTINCT company_id) FROM messages "
                          "WHERE status='replied'").fetchone()[0]
    camp = {"sent": sent, "delivered": sent, "replies": replied,
            "replies_positive": None, "meetings": None, "clients": None,
            "_a_remplir_main": ("replies_positive/meetings/clients se qualifient "
                                "à la MAIN (une réponse n'est pas forcément positive) "
                                "— puis verdict.py assess --campaign ce fichier"),
            "costs": {"fullenrich_credits": 0, "eur_per_credit": 0.20,
                      "api_eur": 0.0, "human_hours": 0.0, "eur_per_hour": 50.0}}
    json.dump(camp, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, "out": a.out, "sent": sent, "replied": replied}))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bricks V2 — envoi réel sous triple clé")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("send")
    p.add_argument("--db", required=True)
    p.add_argument("--live", action="store_true")
    p.add_argument("--campaign-approved")
    p.add_argument("--cap", type=int, default=20)
    p.add_argument("--window", default="08:30-18:30")
    p.add_argument("--pause", type=float, default=45.0)
    p.add_argument("--suppress", help="emails à exclure, séparés par des virgules")
    p = sub.add_parser("check-replies")
    p.add_argument("--db", required=True)
    p.add_argument("--since-days", type=int, default=7)
    p = sub.add_parser("status"); p.add_argument("--db", required=True)
    p = sub.add_parser("export-campaign")
    p.add_argument("--db", required=True); p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    {"send": cmd_send, "check-replies": cmd_check_replies,
     "status": cmd_status, "export-campaign": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
