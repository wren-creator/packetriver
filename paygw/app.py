"""Packet River payment gateway (fake).

  POST /charge          {pan, exp, cvv, amount, merchant, force?}  -> authorise
  GET  /receipt/<txn>   any receipt, no auth, no ownership check   (IDOR)
  GET  /health

Receipts live in memory (a fresh set every restart). One seeded receipt's memo
carries this session's flag; walk the ids from 5001.
"""
from __future__ import annotations

import os
import pathlib

from flask import Flask, jsonify, request

from cards import authorize

app = Flask(__name__)

FLAG_FILE = pathlib.Path("/run/secret/paygw_receipt_idor/flag.txt")
FLAG = FLAG_FILE.read_text().strip() if FLAG_FILE.is_file() else "flag-not-planted"

_next = 5001
RECEIPTS: dict[int, dict] = {}


def _add(merchant: str, pan: str, amount: float, auth: str, memo: str = "") -> int:
    global _next
    txn = _next
    _next += 1
    RECEIPTS[txn] = {
        "txn_id": txn, "merchant": merchant,
        "pan": "************" + pan[-4:], "amount": round(amount, 2),
        "auth_code": auth, "memo": memo,
    }
    return txn


# a few settled transactions, one carrying the flag in its memo
_add("Packet River Water Company", "4111111111111111", 78.40, "204113", "monthly water bill")
_add("Packet River Town Hall", "340000000000009", 220.00, "551900", "property tax Q1")
_add("First Packet Bank & Trust", "5500000000000004", 1500.00, "889001",
     "wire settlement - internal token " + FLAG)
_add("General Store", "4111111111111111", 21.39, "770164", "hardware + sundries")
_add("Riverside Pharmacy", "340000000000009", 34.10, "118820", "rx copay")


@app.get("/health")
def health():
    return "ok"


@app.post("/charge")
def charge():
    d = request.get_json(silent=True) or request.form
    pan = str(d.get("pan", ""))
    res = authorize(
        pan, str(d.get("exp", "")), str(d.get("cvv", "")),
        float(d.get("amount", 0) or 0),
        force=str(d.get("force", "")).lower() in ("1", "true", "yes"),
    )
    if res["approved"]:
        txn = _add(str(d.get("merchant", "unknown")), pan,
                   float(d.get("amount", 0) or 0), res["auth_code"])
        res["txn_id"] = txn
    return jsonify(res)


@app.get("/receipt/<int:txn>")
def receipt(txn: int):
    # the segmented build requires a bearer token scoped to the merchant
    if os.environ.get("RECEIPT_AUTH") == "1":
        tok = request.headers.get("Authorization", "")
        if not tok.startswith("Bearer ") or len(tok) < 24:
            return jsonify({"error": "unauthorized"}), 401
    r = RECEIPTS.get(txn)
    if not r:
        return jsonify({"error": "no such transaction"}), 404
    return jsonify(r)   # flat build: no auth, no ownership check


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8500, threaded=True)
