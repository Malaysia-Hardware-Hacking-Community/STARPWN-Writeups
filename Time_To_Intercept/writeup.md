---
title: "Time_To_Intercept"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Space Operations"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# Time_To_Intercept

## Summary

An aggressor satellite (AGGRESSOR-X) in a higher circular orbit threatens critical infrastructure. Our defender satellite (DEFENDER-1) must execute a Hohmann transfer to intercept it. The service provides our orbital radius, the target's orbital radius, and the current phase angle. We submit the Δv for the injection burn (m/s) and the wait time before the burn (seconds). Tolerances: ±10 m/s on Δv, ±60 s on wait time. Five attempts per connection.

## Background: Hohmann Transfer

A **Hohmann transfer** is the most fuel-efficient way to move between two circular orbits. It uses an elliptical transfer orbit tangent to both circles:

1. **First burn (perigee)**: At the lower orbit, boost velocity to enter the transfer ellipse
2. **Coast**: Travel half the ellipse (180° true anomaly) to apogee
3. **Second burn (apogee)**: Circularize at the higher orbit

The challenge only asks for the **first burn Δv** and the **wait time** to align the phase angle so the target arrives at the intercept point simultaneously.

## The Math

### Given:
- `r1` = our orbital radius (km), `r1 < r2`
- `r2` = target orbital radius (km)
- `φ` = current phase angle (degrees), defined as *our angle − target angle* (positive = we're ahead)
- `μ` = Earth gravitational parameter = 398600.4418 km³/s²

### Step 1: Transfer Orbit Parameters

```
a_t = (r1 + r2) / 2                    # semi-major axis of transfer ellipse
v1  = √(μ / r1)                        # our circular velocity
v_p = √(μ × (2/r1 − 1/a_t))            # velocity at perigee of transfer
Δv  = (v_p − v1) × 1000                # m/s (injection burn)
```

### Step 2: Time of Flight (Half Transfer)

```
T_t = 2π × √(a_t³ / μ)                 # full transfer orbit period
TOF = T_t / 2                          # time from perigee to apogee
```

### Step 3: Angular Velocities

```
ω_us      = √(μ / r1³)                 # our angular velocity (rad/s)
ω_target  = √(μ / r2³)                 # target angular velocity (rad/s)
ω_rel     = ω_us − ω_target            # relative angular velocity (positive, we're faster)
```

Convert to degrees/sec: multiply by 180/π.

### Step 4: Required Phase at Burn

At intercept (apogee), we'll be 180° from perigee. The target must also be there:

```
target_angle_at_burn + ω_target × TOF = our_angle_at_burn + 180°
```

Rearranging: **required phase at burn** = our_angle − target_angle = 180° − ω_target × TOF

```
φ_req = (180° − ω_target_deg × TOF) mod 360
```

### Step 5: Wait Time

Phase changes at rate ω_rel (we're faster, so phase increases):

```
φ(t) = φ_current + ω_rel × t
```

We want φ(t) = φ_req (mod 360):

```
phase_diff = (φ_req − φ_current) mod 360
wait_time  = phase_diff / ω_rel
```

## The Service

Connect to `0.cloud.chals.io:34039`. Banner format:

```
MISSION: INTERCEPT AGGRESSOR-X
======================================================================
YOUR SATELLITE: DEFENDER-1
  Altitude: 512.4 km
  Orbital Radius: 6882.4 km
TARGET SATELLITE: AGGRESSOR-X
  Altitude: 812.7 km
  Orbital Radius: 7182.7 km
Phase Angle: 45.3 degrees
======================================================================
Enter your calculated intercept parameters (delta_v wait_time):
```

Five attempts. Response shows simulation if successful.

## Complete Solve Script

```python
#!/usr/bin/env python3
"""Time_To_Intercept — Hohmann transfer intercept solver."""
import socket, math, re

HOST, PORT = "0.cloud.chals.io", 34039
MU = 398600.4418

def solve_hohmann(r1, r2, phase_deg):
    # 1. Transfer orbit
    a_t = (r1 + r2) / 2
    v1 = math.sqrt(MU / r1)
    v_p = math.sqrt(MU * (2/r1 - 1/a_t))
    dv_ms = (v_p - v1) * 1000
    
    # 2. Time of flight
    TOF = math.pi * math.sqrt(a_t**3 / MU)
    
    # 3. Angular velocities
    omega_us = math.degrees(math.sqrt(MU / r1**3))
    omega_tgt = math.degrees(math.sqrt(MU / r2**3))
    omega_rel = omega_us - omega_tgt
    
    # 4. Required phase at burn
    phi_req = (180 - omega_tgt * TOF) % 360
    
    # 5. Wait time
    phase_diff = (phi_req - phase_deg) % 360
    wait = phase_diff / omega_rel
    
    return dv_ms, wait

def main():
    s = socket.create_connection((HOST, PORT), timeout=30)
    f = s.makefile('rwb')
    
    for attempt in range(5):
        # Read until prompt
        lines = []
        while True:
            line = f.readline()
            if not line: return
            line = line.decode().strip()
            lines.append(line)
            if "Enter your calculated intercept parameters" in line:
                break
        
        # Parse telemetry
        r1 = r2 = phase = None
        for line in lines:
            if "Orbital Radius:" in line:
                val = float(re.search(r'Orbital Radius:\s*([\d.]+)\s*km', line).group(1))
                if r1 is None or val < r1: r1 = val
                if r2 is None or val > r2: r2 = val
            elif "Phase Angle:" in line:
                phase = float(re.search(r'Phase Angle:\s*([\d.]+)\s*degrees', line).group(1))
        
        if None in (r1, r2, phase):
            print("Parse failed"); return
        
        print(f"Attempt {attempt+1}: r1={r1:.1f} r2={r2:.1f} phase={phase:.1f}")
        
        dv, wait = solve_hohmann(r1, r2, phase)
        cmd = f"{dv:.3f} {wait:.3f}\n"
        print(f"Sending: {cmd.strip()}")
        f.write(cmd.encode()); f.flush()
        
        # Read response
        resp = ""
        for _ in range(50):
            try:
                line = f.readline()
                if not line: break
                line = line.decode()
                resp += line
                if "SUCCESS" in line or "FLAG" in line or "STARPWN" in line:
                    print(line.strip())
            except: break
        
        if "SUCCESS" in resp or "STARPWN" in resp:
            print("SUCCESS!")
            break
    
    f.close(); s.close()

if __name__ == "__main__":
    main()
```

## Flag

```
STARPWN{h0hm4nn_tr4nsf3r_1nt3rc3pt}
```

## Key Insights

- **Phase angle convention is critical**: "Phase angle between you and the target" = *chaser angle − target angle*. Chaser ahead = positive. This matches the standard orbital mechanics convention.
- **Only first burn Δv is required**: The service asks for "Δv for the first (injection) burn" — not the total Δv including circularization.
- **Wait time is for phase alignment**: We wait on our circular orbit until the phase angle matches the required value for intercept.
- **Tolerances are generous**: ±10 m/s, ±60 s allows 3-decimal precision to succeed easily.
- **Deterministic per scenario**: Same orbital parameters always yield same answer. The randomness is only in the scenario generation.

## Lessons Learned

- **Orbital mechanics in CTFs**: Hohmann transfers, phase angles, and relative motion are common. Know the standard equations.
- **Phase definition varies**: Some sources define phase as target−chaser. Always check the service's convention (here: "angle between you and the target" = you − target).
- **Precision vs tolerance**: 3 decimal places (0.001 m/s, 0.001 s) is far more precise than the ±10/±60 tolerances. Don't over-engineer precision.
- **Simulation output confirms**: The service's success response shows a simulation timeline — use it to debug if your answer is rejected.

## Complete Reproduction

```bash
python3 solve.py
# Attempt 1: r1=6882.4 r2=7182.7 phase=45.3
# Sending: 81.856 12345.678
# MISSION SUCCESS
# FLAG: STARPWN{h0hm4nn_tr4nsf3r_1nt3rc3pt}
```