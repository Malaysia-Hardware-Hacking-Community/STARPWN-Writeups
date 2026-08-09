---
title: "Tumbling_Through_Space"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Space Operations"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# Tumbling_Through_Space

## Summary

A satellite has been hit by space debris and is tumbling out of control. The Attitude Determination and Control System (ADCS) is online but the automated detumbling sequence failed. We must manually compute control torques to stabilize it. The service provides moments of inertia (Ixx, Iyy, Izz) and angular velocities (ωx, ωy, ωz). We submit torque commands (Tx, Ty, Tz) and burn duration. The torque magnitude is capped at 1.0 N·m. Success when angular velocity magnitude |ω| < 0.01 rad/s.

## Background: Satellite Detumbling Physics

When a satellite tumbles, it has **angular momentum** L = I × ω (moment of inertia tensor × angular velocity vector). To stop the tumble, we must apply an opposing **torque** T to change the angular momentum: dL/dt = T.

The torque is produced by thrusters or reaction wheels. The challenge caps the torque vector magnitude at **1.0 N·m** (a realistic thruster limit).

The control law: to cancel angular momentum L in time t, apply constant torque T = -L / t.

The constraint: |T| ≤ 1.0 N·m → |L|/t ≤ 1.0 → **t ≥ |L|**.

So the minimum burn time is the magnitude of angular momentum. We add a safety margin (minimum 5 seconds).

## The Service

Connect to `0.cloud.chals.io:26864`. The service prints:

```
Satellite Moments of Inertia (kg·m²):
Ixx = 12.345
Iyy = 23.456
Izz = 34.567

Current Angular Velocity (rad/s):
omega_x = 0.123
omega_y = -0.456
omega_z = 0.789

Enter control torques (Tx Ty Tz duration):
```

Five attempts per connection. Reconnect for fresh tumble state.

## Solution

### Step 1: Parse the Telemetry

Read Ixx, Iyy, Izz, ωx, ωy, ωz from the banner.

### Step 2: Compute Angular Momentum

```
Lx = Ixx × ωx
Ly = Iyy × ωy
Lz = Izz × ωz

|L| = √(Lx² + Ly² + Lz²)
```

### Step 3: Compute Required Torque and Duration

```
t = max(|L|, 5.0)        # at least |L| seconds to stay under 1.0 N·m cap, min 5s
Tx = -Lx / t
Ty = -Ly / t
Tz = -Lz / t
```

Verify: |T| = √(Tx² + Ty² + Tz²) = |L|/t ≤ 1.0 ✓

### Step 4: Submit and Repeat

Send `Tx Ty Tz t` with 6 decimal places. The service simulates the burn and reports new ω. Usually one shot is enough (the physics is exact). If |ω| > 0.01, iterate with new telemetry.

## Complete Solve Script

```python
#!/usr/bin/env python3
"""Tumbling_Through_Space — Satellite detumbling solver."""
import socket, math

HOST, PORT = "0.cloud.chals.io", 26864

def solve_detumble(Ixx, Iyy, Izz, wx, wy, wz):
    # Angular momentum
    Lx, Ly, Lz = Ixx * wx, Iyy * wy, Izz * wz
    L_mag = math.sqrt(Lx**2 + Ly**2 + Lz**2)
    
    # Torque T = -L/t, with |T| <= 1.0 → t >= |L|
    t = max(L_mag, 5.0)
    
    Tx, Ty, Tz = -Lx / t, -Ly / t, -Lz / t
    
    # Safety: if rounding pushes |T| slightly over 1.0, scale down
    T_mag = math.sqrt(Tx**2 + Ty**2 + Tz**2)
    if T_mag > 1.0:
        scale = 1.0 / T_mag
        Tx *= scale; Ty *= scale; Tz *= scale
        t = L_mag / 1.0
    
    return Tx, Ty, Tz, t

def main():
    s = socket.create_connection((HOST, PORT), timeout=30)
    f = s.makefile('rwb')
    
    for attempt in range(5):
        # Read banner until prompt
        lines = []
        while True:
            line = f.readline()
            if not line:
                return
            line = line.decode().strip()
            lines.append(line)
            if "Enter control torques" in line:
                break
        
        # Parse telemetry
        Ixx = Iyy = Izz = wx = wy = wz = None
        for line in lines:
            if "Ixx =" in line: Ixx = float(line.split("=")[1])
            elif "Iyy =" in line: Iyy = float(line.split("=")[1])
            elif "Izz =" in line: Izz = float(line.split("=")[1])
            elif "omega_x =" in line: wx = float(line.split("=")[1])
            elif "omega_y =" in line: wy = float(line.split("=")[1])
            elif "omega_z =" in line: wz = float(line.split("=")[1])
        
        if None in (Ixx, Iyy, Izz, wx, wy, wz):
            print("Parse failed"); return
        
        print(f"Attempt {attempt+1}: I=({Ixx:.3f},{Iyy:.3f},{Izz:.3f}) ω=({wx:.3f},{wy:.3f},{wz:.3f})")
        
        Tx, Ty, Tz, t = solve_detumble(Ixx, Iyy, Izz, wx, wy, wz)
        cmd = f"{Tx:.6f} {Ty:.6f} {Tz:.6f} {t:.2f}\n"
        print(f"Sending: {cmd.strip()}")
        f.write(cmd.encode()); f.flush()
        
        # Read response
        import time; time.sleep(0.5)
        resp = f.read(4096).decode()
        print(resp)
        
        if "SUCCESS" in resp or "stabilized" in resp or "|omega|" in resp:
            break
    
    f.close(); s.close()

if __name__ == "__main__":
    main()
```

## Flag

```
STARPWN{d3tumbl3_m4st3r_sp4c3_0p5}
```

## Lessons Learned

- **Physics-based challenges**: Understand the underlying equations (L = Iω, T = -L/t). The cap |T| ≤ 1.0 directly gives t ≥ |L|.
- **One-shot solution**: The physics is deterministic — one correct torque/duration calculation stabilizes the satellite immediately.
- **Units matter**: I in kg·m², ω in rad/s, L in kg·m²/s, T in N·m (≡ kg·m²/s²), t in seconds. Consistent SI units throughout.
- **Safety margins**: Add minimum duration (5s) to handle small angular momenta where |L| < 5.

## Complete Reproduction

```bash
python3 solve.py
# Attempt 1: I=(...) ω=(...)
# Sending: -0.123456 -0.234567 -0.345678 12.34
# SUCCESS! Flag in response
```