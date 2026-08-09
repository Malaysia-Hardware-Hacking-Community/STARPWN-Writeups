#!/usr/bin/env python3
"""
Time_To_Intercept_V2 - Hohmann Transfer Solver
Same math as V1; reconnects on scenarios whose required wait time
exceeds the 24h cap (86400 s), per the challenge description.
"""
import socket
import math
import re

HOST = "0.cloud.chals.io"
PORT = 19717
MU = 398600.4418

def solve_hohmann(r1, r2, phase_deg):
    a_t = (r1 + r2) / 2
    v1 = math.sqrt(MU / r1)
    v_p = math.sqrt(MU * (2 / r1 - 1 / a_t))
    dv_ms = (v_p - v1) * 1000
    TOF = math.pi * math.sqrt(a_t**3 / MU)
    T_target = 2 * math.pi * math.sqrt(r2**3 / MU)
    T_us = 2 * math.pi * math.sqrt(r1**3 / MU)
    omega_us = 360 / T_us
    omega_target = 360 / T_target
    omega_rel = omega_us - omega_target
    required_phase = (180 - omega_target * TOF) % 360
    phase_diff = (required_phase - phase_deg) % 360
    wait_time = phase_diff / omega_rel
    return dv_ms, wait_time

def read_until_prompt(sock):
    buf = b""
    sock.settimeout(5)
    while b"> " not in buf:
        c = sock.recv(4096)
        if not c:
            raise EOFError
        buf += c
    return buf.decode(errors="replace")

def drain(sock):
    out = b""
    sock.settimeout(3)
    try:
        while True:
            c = sock.recv(4096)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    return out.decode(errors="replace")

def main():
    for conn in range(50):
        try:
            s = socket.create_connection((HOST, PORT), timeout=10)
            banner = read_until_prompt(s)
            radii = re.findall(r'Orbital Radius:\s*([\d.]+)\s*km', banner)
            ph = float(re.search(r'Phase Angle:\s*([\d.]+)\s*degrees', banner).group(1))
            r1, r2 = sorted(float(x) for x in radii)
        except Exception as e:
            print(f"conn {conn}: parse/connect error {e!r}")
            continue

        dv, wait = solve_hohmann(r1, r2, ph)
        if wait > 86400:
            print(f"conn {conn}: r1={r1:.1f} r2={r2:.1f} ph={ph:.1f} wait={wait:.0f}s >24h -> reconnect")
            s.close()
            continue

        s.settimeout(5)
        s.sendall(f"{dv:.3f} {wait:.3f}\n".encode())
        resp = drain(s)
        s.close()

        m = re.search(r'STARPWN\{[^}]+\}', resp)
        if m:
            print(f"conn {conn}: r1={r1:.1f} r2={r2:.1f} ph={ph:.1f} dv={dv:.3f} wait={wait:.0f}")
            print(f"FLAG: {m.group(0)}")
            return
        print(f"conn {conn}: no flag (wait={wait:.0f}s)")

if __name__ == "__main__":
    main()
