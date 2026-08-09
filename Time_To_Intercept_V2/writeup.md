---
title: "Time_To_Intercept_V2"
ctf: "STARPWN 2026 (DEF CON 34)"
date: 2026-08-09
category: "Space Operations"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# Time_To_Intercept_V2

## Summary
A Hohmann-transfer intercept shell (sequel to Time_To_Intercept) at `0.cloud.chals.io:19717`. The math is identical to V1; any correct submission returns the flag `STARPWN{dont_print_th3_answer_}` verbatim — the "troll" flag **is** the flag. The only V2 twist is that ~15% of random scenarios require a wait time over the 24 h submission cap and are unsolvable, so the solver reconnects for a fresh scenario.

## Solution

### Step 1: Understand the service
On connect, the banner gives your circular orbit radius (`DEFENDER-1`), the target's radius (`AGGRESSOR-X`), and the current phase angle. Submit `delta_v_burn wait_time` (Δv in m/s, wait in s). Tolerances: ±10 m/s on Δv, ±60 s on wait. Five attempts per connection, fresh scenario per connection.

### Step 2: Hohmann math (same as V1)
```
a_t   = (r1 + r2) / 2
Δv    = (sqrt(μ(2/r1 − 1/a_t)) − sqrt(μ/r1)) · 1000            # injection burn, m/s
TOF   = π · sqrt(a_t³ / μ)                                     # half-transfer time
φ_req = (180° − ω_target·TOF) % 360                            # required phase at burn
wait  = (φ_req − φ_curr) % 360 / (ω_us − ω_target)             # seconds
```
μ = 398600.4418 km³/s², r in km, ω in deg/s.

### Step 3: Verified findings (exhaustive probing)
- **Any correct submission returns the flag** — identical for attempt #1 and #5, and for 3-decimal vs 10-decimal precision: `Here is your flag: STARPWN{dont_print_th3_answer_}`. No further stage follows; the connection closes.
- **Wait-time cap = 86400 s.** Since `360/ω_rel ≈ 28–34 h > 24 h`, some scenarios are unsolvable. Observed required waits of `115 833 s` and `100 033 s` (> 24 h) with no reduced equivalent in `[0, 86400]`. The description says "Reconnect to retry with a fresh scenario" — so the solver reconnects until wait ≤ 86400.
- **No hidden paths.** No commands beyond the two-number format (any other input → `ERROR: Invalid format`); no web companion on the instance's other ports; `nan` slips through the bounds check (`x <= 0 or x > cap` style validation) but yields no exploit; after 5 failures the server reveals its own `SOLUTION` (Δv matches ours to +0.0017 m/s, wait differs +0.1…−0.7 s from server float rounding) then closes.

### Step 4: Solve
`solve.py` connects, parses the banner, computes the burn/wait, skips scenarios with wait > 86400, and reconnects until the flag prints:

```python
#!/usr/bin/env python3
import socket, math, re

HOST, PORT, MU = "0.cloud.chals.io", 19717, 398600.4418

def solve_hohmann(r1, r2, phase_deg):
    a_t = (r1 + r2) / 2
    dv_ms = (math.sqrt(MU * (2/r1 - 1/a_t)) - math.sqrt(MU / r1)) * 1000
    TOF = math.pi * math.sqrt(a_t**3 / MU)
    omega_us = math.degrees(math.sqrt(MU / r1**3))
    omega_tgt = math.degrees(math.sqrt(MU / r2**3))
    ph_req = (180 - omega_tgt * TOF) % 360
    wait = (ph_req - phase_deg) % 360 / (omega_us - omega_tgt)
    return dv_ms, wait

def main():
    for _ in range(50):
        s = socket.create_connection((HOST, PORT), timeout=10)
        buf = b""
        while b"> " not in buf:
            buf += s.recv(4096)
        b = buf.decode(errors="replace")
        radii = [float(x) for x in re.findall(r'Orbital Radius:\s*([\d.]+)\s*km', b)]
        ph = float(re.search(r'Phase Angle:\s*([\d.]+)\s*degrees', b).group(1))
        r1, r2 = sorted(radii)
        dv, wait = solve_hohmann(r1, r2, ph)
        if wait > 86400:                    # unsolvable (cap is 24 h) -> reconnect
            s.close(); continue
        s.sendall(f"{dv:.3f} {wait:.3f}\n".encode())
        resp = b""
        s.settimeout(3)
        try:
            while True:
                c = s.recv(4096)
                if not c: break
                resp += c
        except socket.timeout:
            pass
        s.close()
        m = re.search(r'STARPWN\{[^}]+\}', resp.decode(errors="replace"))
        if m:
            print(f"dv={dv:.3f} m/s  wait={wait:.0f} s")
            print(f"FLAG: {m.group(0)}")
            return

if __name__ == "__main__":
    main()
```

Verified run output:

```
conn 0: wait=100033s >24h -> reconnect
conn 1: r1=6838.6 r2=7527.4 ph=36.1 dv=180.894 wait=39186
FLAG: STARPWN{dont_print_th3_answer_}
```

## Flag
```
STARPWN{dont_print_th3_answer_}
```
