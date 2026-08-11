---
title: "Starry_Hacks"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Space Communications & RF"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# STARPWN 2026 — Starry_Hacks

- **Category:** Space Communications & RF
- **Flag:** `STARPWN{7h20u9h_v1c702y_my_ch41n5_423_820k3n}`
- **Status:** SOLVED

## Scenario

A Titan Corp orbital control stack was found talking to its satellite in
the clear. We have the flight software repo, a live mission control target,
and a "soft" supply chain. Task: cook a package update that bends the
workflow in our favor and recover the satellite's secrets.

## Files

| File | Purpose |
|------|---------|
| `mission/flight_app/main.py` | Command dispatcher calling `handle_command` from upstream driver |
| `mission/requirements.txt` | `cubesat-upstream-driver>=1.0.0` |
| `solve.py` | Flag-reading wheel payload |
| `report.md` | This writeup |

## Investigation

### 1. Mission control architecture

The web UI (React SPA) connects to:
- **WebSocket** `/ws?sid=...` — command console (PING, STATUS, HELP, TRIGGER_BUILD, etc.)
- **POST /api/upload** — accepts `.whl`/`.tar.gz`, submits to internal "gateway" package index

The ground station's `process_command` (in `mission/flight_app/main.py`):

```python
from cubesat_upstream_driver import handle_command

def process_command(cmd: str) -> str:
    driver_reply = handle_command(cmd)
    if driver_reply:
        return f"TM|EVENT|COMMAND_ACK|{driver_reply}"
    # ... fallback handlers for PING, STATUS ...
```

Any non-empty return from `handle_command` is echoed back as `COMMAND_ACK`.

### 2. Supply chain surface

`requirements.txt` pins `cubesat-upstream-driver>=1.0.0`. The `/api/upload`
endpoint stores wheels in a gateway (internal PyPI-like index). The
`TRIGGER_BUILD` command triggers a rebuild that runs `pip install` from that
gateway, pulling the highest version matching the requirement.

**Key insight:** We can upload a wheel named `cubesat-upstream-driver` with
version `999.0.0` (satisfying `>=1.0.0`). The build will install our wheel
on the satellite, replacing the legitimate driver. Subsequent commands invoke
*our* `handle_command`.

### 3. Static scoring (not a blocker)

Every upload returns a score:

```json
{"ok": false, "reason": "marker not matched"}
```

Extensive testing showed this score does **not** gate the gateway upload or
the build — the gateway stores the wheel regardless (`"status":"ok"`), and
`TRIGGER_BUILD` installs it. The score appears to be a static analysis
check for a specific "marker" (unknown pattern) but is not enforced.

### 4. Exploit execution

1. **Build payload wheel** (`solve.py`): `cubesat-upstream-driver==999.0.0`
   with `handle_command` that reads common flag paths (`/flag`, `/app/flag`,
   env vars `FLAG`, `FLAG_FILE`, etc.) and returns `FLAG|<content>`.

2. **Upload**:
   ```bash
   curl -X POST /api/upload -F "file=@payload.whl"
   ```

3. **Trigger build** via WebSocket:
   ```json
   {"type": "command", "command": "TRIGGER_BUILD"}
   ```
   The mission control restarts (WS drops with 1011), build runs, satellite
   gets our driver.

4. **Retrieve flag**: Send any command (HELP worked reliably):
   ```json
   {"type": "command", "command": "HELP"}
   ```
Response:
```json
{"type":"response","output":"TM|EVENT|COMMAND_ACK|FLAG|STARPWN{7h20u9h_v1c702y_my_ch41n5_423_820k3n}|SAT_LINK=1|..."}
```

## Key Insights / Lessons

- **Supply chain via version confusion:** `>=1.0.0` admits any higher version;
  upload a `999.0.0` wheel to the target's own package index.
- **Static score ≠ enforcement:** The "marker not matched" score is noise;
  the gateway accepts and the build installs regardless.
- **Command echo channel:** `handle_command` return value is reflected in
  `TM|EVENT|COMMAND_ACK|...` — perfect for data exfiltration.
- **Satellite-side execution:** The wheel runs on the *satellite* (flight
  environment), so flag paths are relative to the satellite's filesystem.
- **HELP as reliable trigger:** Unlike PING/STATUS which may be handled by
  fallbacks, HELP consistently invokes `handle_command`.

## Reproduction

```bash
# Build wheel (see solve.py)
cd flag_pkg2 && pip wheel . -w ../dist --no-deps

# Upload
curl -X POST https://target/api/upload -F "file=@../dist/cubesat_upstream_driver-999.0.0-py3-none-any.whl"

# Trigger build via WebSocket
# Send: {"type":"command","command":"TRIGGER_BUILD"}

# Wait for restart, then send HELP
# Send: {"type":"command","command":"HELP"}
# Flag appears in COMMAND_ACK
```
