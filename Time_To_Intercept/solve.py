#!/usr/bin/env python3
"""
Satellite Intercept Challenge - Hohmann Transfer Solver
Connects to the service and computes delta-v and wait time dynamically.
"""
import socket
import math
import re
import sys
import time

HOST = "0.cloud.chals.io"
PORT = 34039
MU = 398600.4418  # km^3/s^2

def solve_hohmann(r1, r2, phase_current_deg):
    """
    Compute Hohmann transfer delta-v and wait time.
    
    r1, r2: orbit radii in km (r1 < r2)
    phase_current_deg: current phase angle in degrees (us - target)
    Returns: (delta_v_ms, wait_time_s)
    """
    # 1. Hohmann transfer delta-v (first burn at perigee)
    a_t = (r1 + r2) / 2  # transfer orbit semi-major axis
    v1 = math.sqrt(MU / r1)  # circular velocity at r1
    v_p = math.sqrt(MU * (2/r1 - 1/a_t))  # velocity at perigee of transfer
    dv_km_s = v_p - v1
    dv_ms = dv_km_s * 1000  # m/s
    
    # 2. Time of flight for half transfer (perigee to apogee)
    T_t = 2 * math.pi * math.sqrt(a_t**3 / MU)
    TOF = T_t / 2
    
    # 3. Target's angular velocity
    T_target = 2 * math.pi * math.sqrt(r2**3 / MU)
    omega_target_deg = 360 / T_target  # deg/s
    
    # 4. Our angular velocity
    T_us = 2 * math.pi * math.sqrt(r1**3 / MU)
    omega_us_deg = 360 / T_us  # deg/s
    
    # 5. Relative angular velocity (us minus target)
    omega_rel = omega_us_deg - omega_target_deg  # deg/s (positive since we're faster)
    
    # 6. Required phase at burn (us_angle - target_angle)
    # At arrival, we're at apogee = 180° from perigee
    # Target must also be there: target_angle_burn + omega_target * TOF = us_angle_burn + 180°
    # phase_at_burn = us_angle_burn - target_angle_burn = 180° - omega_target * TOF
    required_phase_at_burn = 180 - omega_target_deg * TOF
    required_phase_at_burn = required_phase_at_burn % 360
    
    # 7. Wait time
    # Phase changes at rate omega_rel (us faster, so phase increases)
    # phase(t) = phase_current + omega_rel * t
    # We want phase(t) = required_phase_at_burn (mod 360)
    # Phase difference to cover (always positive, going forward)
    phase_diff = (required_phase_at_burn - phase_current_deg) % 360
    wait_time = phase_diff / omega_rel if omega_rel != 0 else 0
    
    return dv_ms, wait_time

def main():
    sock = socket.create_connection((HOST, PORT), timeout=30)
    sock.settimeout(30)
    f = sock.makefile('rwb')
    
    for attempt in range(5):
        # Read until we see the prompt
        lines = []
        while True:
            line = f.readline()
            if not line:
                print("Connection closed")
                return
            line = line.decode('utf-8', errors='replace').strip()
            lines.append(line)
            if "Enter your calculated intercept parameters" in line:
                break
        
        # Parse telemetry
        r1 = r2 = phase = None
        
        for line in lines:
            if "Orbital Radius:" in line and "YOUR" in " ".join(lines[max(0, lines.index(line)-3):lines.index(line)+1]):
                # Extract radius from "Orbital Radius: XXXX.XXX km"
                r1 = float(re.search(r'Orbital Radius:\s*([\d.]+)\s*km', line).group(1))
            elif "Orbital Radius:" in line and "TARGET" in " ".join(lines[max(0, lines.index(line)-3):lines.index(line)+1]):
                r2 = float(re.search(r'Orbital Radius:\s*([\d.]+)\s*km', line).group(1))
            elif "Phase Angle:" in line:
                phase = float(re.search(r'Phase Angle:\s*([\d.]+)\s*degrees', line).group(1))
        
        # Fallback: parse all orbital radii and phases
        if r1 is None or r2 is None or phase is None:
            for line in lines:
                m = re.search(r'Orbital Radius:\s*([\d.]+)\s*km', line)
                if m:
                    val = float(m.group(1))
                    if r1 is None or val < r1:
                        r1 = val
                    if r2 is None or val > r2:
                        r2 = val
                m = re.search(r'Phase Angle:\s*([\d.]+)\s*degrees', line)
                if m:
                    phase = float(m.group(1))
        
        if any(v is None for v in [r1, r2, phase]):
            print("Failed to parse telemetry!")
            for l in lines:
                print(l)
            return
        
        print(f"Attempt {attempt+1}: r1={r1:.3f} km, r2={r2:.3f} km, phase={phase:.3f} deg")
        
        dv, wait = solve_hohmann(r1, r2, phase)
        
        cmd = f"{dv:.3f} {wait:.3f}\n"
        print(f"Sending: {cmd.strip()}")
        f.write(cmd.encode())
        f.flush()
        
        # Read response - wait for it
        response_lines = []
        for _ in range(50):
            try:
                line = f.readline()
                if not line:
                    break
                line = line.decode('utf-8', errors='replace')
                response_lines.append(line)
                print(line.strip())
                if "SUCCESS" in line or "intercepted" in line.lower() or "FLAG" in line or "flag" in line or "Attempt" in line or "Delta-v error" in line or "Wait time error" in line:
                    # Keep reading for flag
                    if "SUCCESS" in line or "FLAG" in line or "flag" in line:
                        for _ in range(20):
                            try:
                                line2 = f.readline()
                                if line2:
                                    line2 = line2.decode('utf-8', errors='replace')
                                    print(line2.strip())
                                    if "FLAG" in line2 or "flag" in line2 or "STARPWN" in line2:
                                        break
                            except:
                                break
                    break
            except socket.timeout:
                break
        
        response = "".join(response_lines)
        
        if "SUCCESS" in response or "intercepted" in response.lower() or "FLAG" in response or "flag" in response:
            print("SUCCESS!")
            break
    
    f.close()
    sock.close()

if __name__ == "__main__":
    main()