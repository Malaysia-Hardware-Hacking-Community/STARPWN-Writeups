---
title: "Silent_Beacon"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Space Communications & RF"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# STARPWN 2026 — Silent_Beacon

**Category:** Forensics / Protocol Decoding (CCSDS Telemetry)
**Flag:** `STARPWN{h0us3k33p1ng_4n0m4ly}`
**Status:** SOLVED

## Scenario

A Titan Corp CubeSat went silent after a suspected cyber intrusion. The
last telemetry burst from the ground station was saved as `capture.bin` —
raw CCSDS packets buried in line noise, multiple APIDs interleaved.
Recover the lost telemetry using `telemetry_dictionary.json`.

## Files

| File | Purpose |
|------|---------|
| `capture.bin` | 5835-byte raw bitstream, 124 ASM-framed CCSDS packets |
| `packet_ids.txt` | Partial APID directory (only APIDs 50, 100, 200 recovered) |
| `telemetry_dictionary.json` | Full decode dictionary for APID 100 only |
| `solve.py` | Parser + flag extraction script (reproducible solve) |

## Investigation

### 1. Frame sync

Every CCSDS packet starts with the Attached Sync Marker (ASM)
`0x1ACFFC1D` (4 bytes). Scanning `capture.bin` for that marker yields
**124 packets** — every one is cleanly framed (no bit errors).

### 2. Primary header decode (CCSDS 133.0-B-2)

6-byte primary header after the ASM:

```
00 64 | c0 2b | 00 0d
|--|   |---|  |---|
v1     seq    len
```

- **Version/APID word:** version(3b) type(1b) sec-hdr-flag(1b) APID(11b)
  → `0x064` = APID 100
- **Sequence flags (2b) + count (14b):** all packets unsegmented
  (`0b11`), sequence count = packet order within each APID stream
- **Packet data length field:** length-1 → 14-byte payload for APID 100

Interleaved APIDs found:

| APID | Mnemonic | Count | Payload |
|------|----------|-------|---------|
| 50 | SYSLOG | 14 | variable ASCII ("GPS LOCK 4SVS", "INIT OK", …) |
| 100 | HK_NOMINAL | 89 | 14-byte housekeeping (fully documented) |
| 200 | ADCS_STATUS | 21 | 8-byte, layout unknown (dead end — random data) |

### 3. HK_NOMINAL decode (APID 100)

Struct format `>HhhhHHBB` (big-endian), per dictionary:

```text
seq= 0 sid=1000 temp_obc= 16.1C temp_bat= 18.6C temp_sol= 46.4C
     vbus=7.545V ibus=18.3mA mode=SAFE err=0x00
...
seq=43 sid=1043 temp_obc= 24.4C temp_bat= 16.9C temp_sol=-55.2C
     vbus=7.407V ibus=13.4mA mode=0x70 INVALID err=0x8c
```

89/89 packets have complete sequence counts 0–88. Telemetry looks
physically plausible (temps, voltages) — the cover story is real.

### 4. Finding the anomaly

The `mode` field has a valid range 0–7 per the dictionary. **29 of 89
HK packets have `mode` bytes outside that range** — and every one of
them also sets bit 7 of `error_flags`. That statistical signature is
too consistent to be noise: the 8th bit is a *hidden-channel marker*.

Dropping bit 7 of the `mode` byte (`mode & 0x7F`) yields printable
ASCII. Sorting the 29 packets by CCSDS sequence count reassembles the
message:

```text
S T A R P W N { h 0 u s 3 k 3 3 p 1 n g _ 4 n 0 m 4 l y }
```

## Flag

```
STARPWN{h0us3k33p1ng_4n0m4ly}
```

("housekeeping anomaly" — the hidden channel rode inside housekeeping
telemetry the whole time.)

## Key Insight / Lessons

- **Stego inside fixed-width protocol fields:** when a documented enum
  field (mode 0–7) suddenly shows values in 0x80–0xF8, and error flags
  uniformly have bit 7 set, treat the top bit as a marker and the rest
  as payload.
- **Always decode with the provided dictionary first** — the "invalid"
  values are the interesting ones, not a parsing mistake.
- **Sequence counts give you back ordering** even when packets are
  interleaved in the file — sort by APID-local CCSDS sequence count.
- The ASM `0x1ACFFC1D` framing meant a trivial, unambiguous parser:
  no sync-fallback logic needed.

## Reproduction

```bash
python3 solve.py
# [*] 124 packets, ASM 1acffc1d, APIDs: [50, 100, 200]
# [*] 29 anomalous HK packets (mode outside 0-7)
# [+] FLAG: STARPWN{h0us3k33p1ng_4n0m4ly}
```