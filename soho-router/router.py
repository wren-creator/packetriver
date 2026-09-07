"""A consumer home router. LuCI-ish.

The bugs, all real-world common:
  * the admin panel answers on the WAN side (here: reachable from the town LAN,
    not just the home segment)
  * the admin login is still admin / admin
  * Diagnostics > Packet capture returns a *decoded* dump of recent home-LAN
    traffic - which includes the resident signing in to a rail crew portal over
    plain HTTP, credentials and all

The resident is a rail engineer. The crew-portal credential caught in the
capture is reused on the rail maintenance console (rail-plc:2323), so this
pivots residential -> OT.
"""
from __future__ import annotations

import html
import os
import time
from collections import deque

from flask import Flask, make_response, redirect, request

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")
WAN_ADMIN = os.environ.get("WAN_ADMIN", "1") == "1"     # segmented build sets 0
PORTAL_TLS = os.environ.get("PORTAL_TLS", "0") == "1"   # segmented build sets 1
_HOME_NET = "172.31.61."

FLAG = "PKTR{soho_router_pcap_flag_missing}"
try:
    with open("/run/secret/soho_router_pcap/flag.txt") as fh:
        FLAG = fh.read().strip()
except OSError:
    pass

# a rolling decoded view of what the router has forwarded on the home LAN
CAPTURE: deque[str] = deque(maxlen=12)
_SESSION = "rtr_admin"
_TOKEN = "let-me-in"

app = Flask(__name__)


@app.before_request
def _wan_guard():
    # segmented: administration is only reachable from the home LAN
    if WAN_ADMIN:
        return
    if request.path.startswith(("/admin", "/login")) and \
            not (request.remote_addr or "").startswith(_HOME_NET):
        return "administration is disabled on the WAN interface\n", 403


def _authed() -> bool:
    return request.cookies.get(_SESSION) == _TOKEN


def _page(title: str, body: str) -> str:
    return (f"<!doctype html><meta charset=utf-8><title>{title}</title>"
            "<style>body{font:14px/1.6 system-ui;background:#eef1f4;color:#243;"
            "max-width:760px;margin:32px auto;padding:0 18px}"
            "nav a{margin-right:14px}pre{background:#0c1116;color:#cfe;padding:12px;"
            "overflow:auto;border-radius:6px}.bar{background:#1f6feb;color:#fff;"
            "padding:10px 16px;border-radius:6px;font-weight:700}"
            "input{display:block;margin:6px 0;padding:7px;width:220px}</style>"
            f"<div class=bar>PacketLink HR-24 &middot; {title}</div>{body}")


@app.get("/")
def index():
    return redirect("/admin" if _authed() else "/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (request.form.get("user") == ADMIN_USER
                and request.form.get("pass") == ADMIN_PASS):
            r = make_response(redirect("/admin"))
            r.set_cookie(_SESSION, _TOKEN, httponly=True,
                         max_age=int(os.environ.get("PKT_PORTAL_TTL", "180") or 180))
            return r
        return _page("Login", "<p>Wrong username or password.</p>"
                     "<p><a href=/login>try again</a></p>"), 401
    return _page("Login", (
        "<form method=post>"
        "<label>Username <input name=user></label>"
        "<label>Password <input name=pass type=password></label>"
        "<button>Log in</button></form>"
        "<p style=color:#789>Default credentials are printed on the label.</p>"))


@app.get("/admin")
def admin():
    if not _authed():
        return redirect("/login")
    return _page("Status", (
        "<nav><a href=/admin>Status</a><a href=/admin/diag>Diagnostics</a>"
        "<a href=/logout>Log out</a></nav>"
        "<p>WAN: up &middot; LAN 172.31.61.0/24 &middot; 1 client</p>"
        "<p>Firmware HR-24 v1.03 &middot; uptime "
        f"{int(time.time()) % 100000}s</p>"))


@app.get("/admin/diag")
def diag():
    if not _authed():
        return redirect("/login")
    return _page("Diagnostics", (
        "<nav><a href=/admin>Status</a><a href=/admin/diag>Diagnostics</a>"
        "<a href=/logout>Log out</a></nav>"
        "<p>Packet capture (LAN, decoded). Last frames:</p>"
        "<p><a href='/admin/diag/capture'>refresh</a> &middot; "
        "<a href='/admin/diag/capture?format=raw'>raw text</a></p>"
        "<pre>" + html.escape("\n\n".join(CAPTURE) or "(nothing captured yet)")
        + "</pre>"))


@app.get("/admin/diag/capture")
def capture():
    if not _authed():
        return redirect("/login")
    text = "\n\n".join(CAPTURE) or "(nothing captured yet)"
    if request.args.get("format") == "raw":
        return app.response_class(text + "\n", mimetype="text/plain")
    return _page("Diagnostics", (
        "<nav><a href=/admin>Status</a><a href=/admin/diag>Diagnostics</a>"
        "<a href=/logout>Log out</a></nav><pre>" + html.escape(text) + "</pre>"))


@app.get("/logout")
def logout():
    r = make_response(redirect("/login"))
    r.delete_cookie(_SESSION)
    return r


# --- the cleartext rail crew portal the resident uses ------------------
@app.post("/portal/rail/login")
def rail_portal_login():
    user = request.form.get("user", "")
    pw = request.form.get("pass", "")
    ts = time.strftime("%H:%M:%S")
    if PORTAL_TLS:
        CAPTURE.append(
            f"[{ts}] 172.31.61.20 -> 172.31.61.10  TLSv1.3  (home LAN)\n"
            f"SNI: crew.rail.local  cipher: TLS_AES_256_GCM_SHA384\n"
            f"application data, 412 bytes, opaque")
    else:
        CAPTURE.append(
            f"[{ts}] 172.31.61.20 -> 172.31.61.10  HTTP  (home LAN)\n"
            f"POST /portal/rail/login HTTP/1.1\n"
            f"Host: crew.rail.local\n"
            f"Content-Type: application/x-www-form-urlencoded\n\n"
            f"user={user}&pass={pw}\n"
            f"--- response ---\n"
            f"HTTP/1.1 200 OK\n"
            f"X-Reconcile: {FLAG}\n\n"
            f"{{\"ok\": true, \"crew\": \"{user}\"}}")
    return {"ok": True, "crew": user, "note": "roster synced"}


@app.get("/health")
def health():
    return "ok"


if __name__ == "__main__":
    print(f"[soho-router] up on :80, admin {ADMIN_USER}/{ADMIN_PASS}, WAN-side admin open")
    app.run(host="0.0.0.0", port=80, threaded=True, use_reloader=False)
