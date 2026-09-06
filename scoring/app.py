"""Packet Creek scoring service.

Phase 0: schema + health + stub endpoints so the gateway route and the UI HUD
have something to talk to. Phase 1 fills in flag generation/injection, the
signed-cookie auth, `POST /api/score/{arm,submit}`, the score formula, and the
leaderboard, and starts publishing pkt/score/events on a valid submission.
"""
from __future__ import annotations

import pathlib
import sqlite3

from flask import Flask, jsonify

DB_PATH = pathlib.Path("/data/scoring.db")
SCHEMA = pathlib.Path(__file__).with_name("schema.sql")

app = Flask(__name__)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript(SCHEMA.read_text())


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/score/leaderboard")
def leaderboard():
    with db() as conn:
        rows = conn.execute(
            "SELECT u.name, s.best_run_total, s.total, s.fastest_full_clear_s "
            "FROM scores s JOIN users u ON u.id = s.user_id "
            "ORDER BY s.best_run_total DESC LIMIT 25"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/score/arm")
def arm():
    return {"accepted": False, "detail": "scoring arrives in phase 1"}, 501


@app.post("/api/score/submit")
def submit():
    return {"accepted": False, "detail": "scoring arrives in phase 1"}, 501


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8001, threaded=True)
