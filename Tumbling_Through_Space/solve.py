#!/usr/bin/env python3
"""
Satellite Detumbling Challenge Solver
Connects to the ADCS service and computes control torques to detumble.
"""
import socket
import math
import sys
import time

HOST = "0.cloud.chals.io"
PORT = 26864

def solve_detumble(Ixx, Iyy, Izz, omega_x, omega_y, omega_z):
    """Compute torques to cancel angular momentum."""
    # Angular momentum
    Lx = Ixx * omega_x
    Ly = Iyy * omega_y
    Lz = Izz * omega_z
    
    L_mag = math.sqrt(Lx**2 + Ly**2 + Lz**2)
    
    # Torque T = -L / t, with |T| <= 1.0
    # Need t >= |L| to keep |T| <= 1.0
    t = max(L_mag, 5.0)  # at least |L| seconds, minimum 5s
    
    Tx = -Lx / t
    Ty = -Ly / t
    Tz = -Lz / t
    
    # Verify magnitude
    T_mag = math.sqrt(Tx**2 + Ty**2 + Tz**2)
    if T_mag > 1.0:
        # Scale down if slightly over
        scale = 1.0 / T_mag
        Tx *= scale
        Ty *= scale
        Tz *= scale
        T_mag = 1.0
        t = L_mag / T_mag  # Adjust time
    
    return Tx, Ty, Tz, t

def main():
    sock = socket.create_connection((HOST, PORT), timeout=30)
    f = sock.makefile('rwb')
    
    for attempt in range(5):
        # Read until we see the telemetry
        lines = []
        while True:
            line = f.readline()
            if not line:
                print("Connection closed")
                return
            line = line.decode('utf-8', errors='replace').strip()
            lines.append(line)
            if "Enter control torques" in line:
                break
        
        # Parse telemetry from the last output
        Ixx = Iyy = Izz = None
        omega_x = omega_y = omega_z = None
        
        for line in lines:
            if "Ixx =" in line:
                Ixx = float(line.split("=")[1].strip())
            elif "Iyy =" in line:
                Iyy = float(line.split("=")[1].strip())
            elif "Izz =" in line:
                Izz = float(line.split("=")[1].strip())
            elif "omega_x =" in line:
                omega_x = float(line.split("=")[1].strip())
            elif "omega_y =" in line:
                omega_y = float(line.split("=")[1].strip())
            elif "omega_z =" in line:
                omega_z = float(line.split("=")[1].strip())
        
        if any(v is None for v in [Ixx, Iyy, Izz, omega_x, omega_y, omega_z]):
            print("Failed to parse telemetry!")
            for l in lines:
                print(l)
            return
        
        print(f"Attempt {attempt+1}: I=({Ixx:.3f},{Iyy:.3f},{Izz:.3f}) omega=({omega_x:.3f},{omega_y:.3f},{omega_z:.3f})")
        
        Tx, Ty, Tz, t = solve_detumble(Ixx, Iyy, Izz, omega_x, omega_y, omega_z)
        
        cmd = f"{Tx:.6f} {Ty:.6f} {Tz:.6f} {t:.2f}\n"
        print(f"Sending: {cmd.strip()}")
        f.write(cmd.encode())
        f.flush()
        
        # Read response
        time.sleep(0.5)
        response = f.read(4096).decode('utf-8', errors='replace')
        print(response)
        
        if "SUCCESS" in response or "stabilized" in response or "|omega|" in response and "0.00" in response:
            print("SUCCESS!")
            break
        if "FLAG" in response or "flag" in response:
            print("FLAG FOUND!")
            break
    
    f.close()
    sock.close()

if __name__ == "__main__":
    main()