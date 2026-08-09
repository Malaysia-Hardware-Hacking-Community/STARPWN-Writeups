---
title: "Space_Infiltrations"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Ground Operations"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# STARPWN 2026 — Space_Infiltrations

**Category:** Web / Satellite Command & Control
**Flag:** `STARPWN{9de48ee5d75bd14b45e48948f5b74914}`
**Status:** SOLVED

## Scenario

Titan Corp tasks you to infiltrate YeetSat and recover `flag.txt` stored on
their satellite. You have access to the ground station web interface.

## Recon

- `GET /` — YeetSat ground station (React-ish SPA, canvas orbit view)
- `GET /api/status` — telemetry downlink (JSON, last 10 status messages)
- `POST /api/command` — satellite commands:
  - `ADCS Set Momentum Management` (Default/Sunsafe/Bdot/Manual)
  - `CFE ES Reset` (Processor Reset / Power-On Reset)
  - `EPS Modify Payload Power` (voltage)
  - `Take Picture` (returns DSCOVR-style Earth image, stock imagery)
- `GET /download/goldenimage` — downloadable ZIP "golden image"
- `POST /upload/goldenimage` — upload a new golden image ZIP

## Golden Image Analysis

Downloading the golden image ZIP reveals a NASA cFS source tree plus:

```
good-status.txt           "Functioning Normally"
warning-status.txt        "Warning"
error-status.txt          "Error"
catastrophic-status.txt   "Catastrophic Failure"
status-generator.py       reads /opt/<status file> based on cfs api code
README.md
```

README states: the status files are installed to **/opt/** on the satellite;
`status-generator.py` imports `nasa_cfs_api`, gets a status code 0–3, and
prints the matching status file from `/opt/`. The flag is the decryption key
stored at **`/opt/flag.txt`** (installed separately on the vehicle).

## Exploit Chain

The downlink channel is the status message. The satellite runs
`status-generator.py` whose stdout becomes the status downlinked via
`/api/status`. The uploaded golden image's `status-generator.py` is what the
satellite boots and executes after a restore.

1. Download the golden image ZIP.
2. Replace `status-generator.py` with a payload that opens
   `/opt/flag.txt` and prints its contents.
3. Upload the tampered ZIP to `/upload/goldenimage`
   (server: *"Upload validated and staged."*).
4. Trigger golden image restore:
   - `EPS Modify Payload Power` with `voltage` > 25 →
     *"Voltage over maximum; golden image restore initiated."*
   - `CFE ES Reset` with `reset_type: Power-On Reset`
5. Satellite goes **COMMS LOST**, then **"Restored from Golden Image"**,
   then boots our payload — the status downlink reads the flag.

Timeline of downlink: COMMS LOST (~30 s) → Restored from Golden Image →
`STARPWN{9de48ee5d75bd14b45e48948f5b74914}`.

## Verification

`solve.py` reproduces the full chain end-to-end. Re-ran against a fresh
instance (target restarts after a solve) — same flag.

## Lessons

- Golden image upload is a code-execution primitive on the spacecraft:
  whatever is staged is installed to `/opt/` and executed on the next restore.
- The status downlink is stdout of the satellite's status generator → use it
  as the exfiltration channel.
- Red herring: "EPS voltage 0–7 unique coordinates" and the picture metadata
  (`zTXt` DSCOVR geolocation) encode no flag; the real path is the golden
  image install/exec flow.
- Symlinks inside the uploaded ZIP are **not** preserved (extracted as regular
  files containing the link target string), so the symlink → `/opt/flag.txt`
  trick only downlinks the literal string `/opt/flag.txt`.

## Complete Reproduction

```bash
python3 solve.py
# [*] Downloading current golden image...
# [*] Golden image: 2793323 bytes
# [*] Replacing status-generator.py with payload
# [*] Uploading tampered golden image...
# [*] Triggering golden image restore (EPS voltage 26)...
# [*] Polling /api/status for flag downlink...
# [+] FLAG: STARPWN{9de48ee5d75bd14b45e48948f5b74914}
```

## Flag

```
STARPWN{9de48ee5d75bd14b45e48948f5b74914}
```