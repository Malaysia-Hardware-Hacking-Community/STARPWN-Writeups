---
title: Connect_The_Dots
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: Space Communications & RF
points: 500
flag_format: "starpwn{[A-Za-z_]+}"
author: "gluppler"
---

## Connect_The_Dots

### Initial Findings
The challenge provides a raw PRISM data file (`PRISM_S03_B10-30_20260830.raw`) containing GPS tracks for a fleet of drones. The scenario states: "Every night, each drone patrols its assigned block, following its route with clockwork precision. But tonight, one unit broke the formation. Can you trace where did it go?"

The flag format is an expanded acronym: `starpwn{Expanded_Acronym}`.

Analysis of the raw data reveals 34 unique drone IDs. Parsing the binary format (0xFD sync byte, length, type=1, drone ID at offset 7-9) extracts timestamp, latitude, longitude, altitude, and relative altitude for each position report.

A visualization of all drone tracks (`tracks_all.png`) shows multiple drones patrolling rectangular blocks. One drone (labeled "Drone 4" in the visualization) deviates from its patrol pattern and spells out **BVLOS** in its flight path.

### Exploit PoC
The raw data is parsed to extract all drone tracks. Drone tracks are segmented by time gaps (>5000 ms). Most drones show straight-line patrol patterns (transit segments). One drone (Drone 4) contains short, high-turning segments that form letters when rendered.

The letters spelled by Drone 4's anomalous flight path read: **B-V-L-O-S**

BVLOS is a standard aviation acronym for **Beyond Visual Line Of Sight**, referring to drone operations where the pilot cannot visually see the aircraft.

### Reproduction Steps
1. Parse `PRISM_S03_B10-30_20260830.raw`:
   - Sync on 0xFD byte
   - Read length (byte 1)
   - Extract drone ID from bytes 7-9 (little-endian)
   - For type=1 packets with payload >=20 bytes, unpack timestamp, lat, lon, alt, rel_alt (little-endian: Iiiii)
   - Convert lat/lon from 1e7 degrees to decimal

2. Render all drone tracks on a map (equirectangular projection centered at 36.14°N)

3. Identify the drone that breaks formation (Drone 4 in the visualization)

4. Extract the letter-stroke segments (high turning rate, low speed)

5. Read the spelled acronym: **BVLOS**

6. Expand per flag format: `starpwn{Beyond_Visual_Line_Of_Sight}`

### Flag
`starpwn{Beyond_Visual_Line_Of_Sight}`
