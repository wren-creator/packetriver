"""The Diner's open Wi-Fi "access point".

Serves a cleartext rewards portal (:80) and a toy POP3 mailbox (:110). Nothing
here is encrypted - that is the lesson. A patron container logs in and reads
mail over this segment every few seconds; an attacker on the same segment who
ARP-spoofs their way between the patron and this box sees all of it, including
the flag sitting in the patron's inbox.

Also runs a lightweight ARP-storm watcher: a raw AF_PACKET socket counting ARP
replies. A burst (the attacker's arpspoof) publishes an Alert-heat event on the
bus - noisy layer-2 is noisy.
"""
from __future__ import annotations

import os
import socket
import ssl
import threading
import time

import paho.mqtt.client as mqtt
from flask import Flask, request

TLS = os.environ.get("NETLAB_TLS", "0") == "1"      # segmented build: encrypt everything
_CERT, _KEY = "/app/tls.crt", "/app/tls.key"

FLAG = "PKTR{diner_wifi_flag_missing}"
try:
    with open("/run/secret/diner_wifi/flag.txt") as fh:
        FLAG = fh.read().strip()
except OSError:
    pass

PORTAL_USER = os.environ.get("PORTAL_USER", "diner_guest")
PORTAL_PASS = os.environ.get("PORTAL_PASS", "Rewards2026")
MQTT_HOST = os.environ.get("MQTT_HOST", "bus")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))

# the one message in the patron's mailbox; the reconciliation code is the flag
MAIL = (
    "From: rewards@thepacketriverdiner.example\r\n"
    "To: booth7@thepacketriverdiner.example\r\n"
    "Subject: your loyalty statement\r\n"
    "\r\n"
    "Thanks for dining with us. This month's reconciliation code is\r\n"
    f"{FLAG}\r\n"
    "Show it at the register for a free coffee.\r\n"
    ".\r\n"
)

# --- MQTT (Alert-heat only) -------------------------------------------------
_cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="netlab")
if os.environ.get("MQTT_USER"):
    _cli.username_pw_set(os.environ["MQTT_USER"], os.environ.get("MQTT_PASS", ""))


def _mqtt_loop():
    while True:
        try:
            _cli.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            _cli.loop_start()
            return
        except OSError:
            time.sleep(2)


def _bump_heat(reason: str):
    # no "effect" key -> simmap's bus handler just adds heat for the severity
    _cli.publish("pkt/score/events",
                 '{"severity": "loud", "source": "netlab", "detail": "%s"}' % reason)
    print(f"[netlab] arp storm -> heat bump ({reason})")


# --- ARP-poisoning watcher --------------------------------------------
# No raw socket needed: poll the kernel ARP cache. Remember the first MAC seen
# for each neighbour on this segment; if it flips to a different MAC, someone is
# spoofing (arpspoof rewriting our entry for the patron -> the attacker's MAC).
def arp_watch():
    seen: dict[str, str] = {}
    last_alert = 0.0
    while True:
        time.sleep(2)
        try:
            with open("/proc/net/arp") as fh:
                next(fh)
                rows = [r.split() for r in fh]
        except OSError:
            continue
        for parts in rows:
            if len(parts) < 4:
                continue
            ip, mac = parts[0], parts[3]
            if mac == "00:00:00:00:00:00" or not ip.startswith("172.31.60."):
                continue
            prev = seen.get(ip)
            if prev is None:
                seen[ip] = mac
            elif mac != prev and time.time() - last_alert > 20:
                _bump_heat(f"arp entry for {ip} flipped {prev} -> {mac}")
                last_alert = time.time()
                seen[ip] = mac


# --- toy POP3 ----------------------------------------------------------
def pop3_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 995 if TLS else 110))
    srv.listen(8)
    ctx = None
    if TLS:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(_CERT, _KEY)
    while True:
        conn, _ = srv.accept()
        if ctx:
            try:
                conn = ctx.wrap_socket(conn, server_side=True)
            except OSError:
                conn.close()
                continue
        threading.Thread(target=_pop3_session, args=(conn,), daemon=True).start()


def _pop3_session(conn):
    f = conn.makefile("rwb", buffering=0)
    try:
        f.write(b"+OK Packet River Diner POP3 ready\r\n")
        for raw in f:
            line = raw.decode(errors="replace").strip()
            verb = line.split(" ")[0].upper() if line else ""
            if verb == "USER":
                f.write(b"+OK\r\n")
            elif verb == "PASS":
                f.write(b"+OK mailbox ready\r\n")
            elif verb == "STAT":
                f.write(f"+OK 1 {len(MAIL)}\r\n".encode())
            elif verb == "LIST":
                f.write(f"+OK 1 messages\r\n1 {len(MAIL)}\r\n.\r\n".encode())
            elif verb == "RETR":
                f.write(f"+OK {len(MAIL)} octets\r\n".encode())
                f.write(MAIL.encode())
            elif verb == "QUIT":
                f.write(b"+OK bye\r\n")
                break
            else:
                f.write(b"+OK\r\n")
    except OSError:
        pass
    finally:
        conn.close()


# --- the rewards portal ----------------------------------------------
app = Flask(__name__)
_PAGE = ("<!doctype html><meta charset=utf-8><title>The Packet River Diner - Guest Wi-Fi</title>"
         "<style>body{{font:15px/1.6 system-ui;background:#f4efe4;color:#3a3226;"
         "max-width:420px;margin:60px auto;padding:0 20px}}"
         "input{{display:block;width:100%;margin:6px 0;padding:8px}}"
         "button{{padding:8px 18px;background:#b9642f;color:#fff;border:0}}</style>"
         "<h1>Diner Guest Wi-Fi</h1>{body}")


@app.get("/")
def index():
    return _PAGE.format(body=(
        "<p>Open network, no password. Sign in to the rewards portal for perks.</p>"
        "<form method=post action=/login>"
        "<input name=user placeholder='rewards username'>"
        "<input name=pass type=password placeholder='rewards password'>"
        "<button>Sign in</button></form>"))


@app.post("/login")
def login():
    if request.form.get("user") == PORTAL_USER and request.form.get("pass") == PORTAL_PASS:
        return _PAGE.format(body="<p>+OK signed in. Enjoy your visit.</p>")
    return _PAGE.format(body="<p>Sign-in failed.</p>"), 401


@app.get("/health")
def health():
    return "ok"


if __name__ == "__main__":
    _mqtt_loop()
    threading.Thread(target=arp_watch, daemon=True).start()
    threading.Thread(target=pop3_server, daemon=True).start()
    if TLS:
        print(f"[netlab] AP up (TLS): portal :443, POP3S :995 - MITM sees ciphertext")
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(_CERT, _KEY)
        app.run(host="0.0.0.0", port=443, threaded=True, use_reloader=False, ssl_context=ctx)
    else:
        print(f"[netlab] AP up: portal :80 ({PORTAL_USER}), POP3 :110, flag in the mailbox")
        app.run(host="0.0.0.0", port=80, threaded=True, use_reloader=False)
