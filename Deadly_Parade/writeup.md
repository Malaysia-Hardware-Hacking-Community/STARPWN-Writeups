---
title: "Deadly Parade"
ctf: "STARPWN (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Communications & RF"
points: 500
flag_format: "starpwn{[A-Za-z_]+}"
author: "gluppler"
---

# Deadly Parade

## Summary

A 207 MB SLL2 pcap of an ArduPilot SITL MAVLink v2 session (10 drones + GCS over
UDP). GPS jammers hidden somewhere in Las Vegas kill 3 drones mid-flight. The flag
is the name of the place the jammers were hidden: **Echo Trail Park**.

## Solution

### Step 1: Locate the GPS-loss events

Parse the SLL2 pcap and decode MAVLink v2 (`0xFD` magic, sysid 1-10 = drones,
255 = GCS). For each drone, follow `msgid 24 GPS_RAW_INT` fixes (lat@8, lon@12,
`satellites_visible`@29) in time order. When satellite count drops from `10` to
`3`, that drone has been jammed; the last fix before the drop is its position at
loss. Cross-check with `msgid 253 STATUSTEXT`: the same three drones log
`"EKF Failsafe: changed to LAND Mode"` followed by `"SIM Hit ground"`.

Lost drones: **2, 3, 5** — their last valid fixes are:

| drone | last valid fix |
|---|---|
| 2 | (36.0924472, -115.2422068) |
| 3 | (36.0778972, -115.2440034) |
| 5 | (36.0997052, -115.2478434) |

### Step 2: Triangulate the jammer = circumcenter

All three crashed while flying the same due-west leg, so their loss points are
≈equidistant from a single jammer. Compute the circumcenter of the triangle in a
local metric projection:

```
jammer (circumcenter): (36.086804, -115.263054)
dist to drone 2: 1975.6 m
dist to drone 3: 1977.8 m
dist to drone 5: 1981.4 m
```

A ~2 km-radius omni jammer at this point kills all three drones and no surviving
drone ever comes within 2.66 km of it (consistent).

### Step 3: Reverse-geocode

OSM Overpass `way(around:400,36.086804,-115.263054)["leisure"="park"]` → the only
park is **Echo Trail Park** (OSM way `210546119`, center 36.0868969,-115.2633634;
5655 W Buffalo Dr, Russell & Buffalo, Spring Valley, Las Vegas). Circumcenter is
**29.6 m** from the park center; all three crash points are 1.99-2.01 km from the
park. The jammers were hidden in the park.

### Complete solve script

```python
#!/usr/bin/env python3
"""Deadly_Parade: GPS-jam triangulation from MAVLink SITL pcap."""
import struct, sys, math

def iter_packets(f):
    hdr = f.read(24)
    assert hdr[:4] == b'\xd4\xc3\xb2\xa1', "not classic LE pcap"
    while True:
        rec = f.read(16)
        if len(rec) < 16:
            break
        ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', rec)
        data = f.read(incl_len)
        if len(data) < incl_len:
            break
        if len(data) < 20 or struct.unpack_from('>H', data, 0)[0] != 0x0800:
            continue
        ip_start = 20
        ihl = (data[ip_start] & 0x0f) * 4
        if data[ip_start + 9] != 17:
            continue
        udp_start = ip_start + ihl
        sport, dport, ulen, _ = struct.unpack_from('>HHHH', data, udp_start)
        yield ts_sec + ts_usec / 1e6, data[udp_start + 8: udp_start + ulen]

def parse_mavlink2(buf):
    i = 0
    while i < len(buf):
        if buf[i] != 0xFD:
            i += 1
            continue
        if i + 10 > len(buf):
            break
        length, incompat = buf[i + 1], buf[i + 2]
        sysid = buf[i + 5]
        msgid = struct.unpack_from('<I', buf, i + 7)[0] & 0xFFFFFF
        pstart = i + 10
        pend = pstart + length
        crc_end = pend + 2 + (13 if incompat & 0x01 else 0)
        if crc_end > len(buf):
            break
        yield msgid, sysid, buf[pstart:pend]
        i = crc_end

def to_meters(pts):
    lat0 = sum(p[0] for p in pts) / len(pts)
    lon0 = sum(p[1] for p in pts) / len(pts)
    return [( (lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
              (lat - lat0) * 110540.0 ) for lat, lon in pts]

def circumcenter(pts):
    (x1, y1), (x2, y2), (x3, y3) = pts
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    return ux, uy

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def main(pcap):
    last_fix, sats, crashes = {}, {}, {}
    with open(pcap, 'rb') as f:
        for ts, payload in iter_packets(f):
            for msgid, sysid, p in parse_mavlink2(payload):
                if sysid in (255, 0):
                    continue
                if msgid == 24 and len(p) >= 30:
                    n = p[29]
                    if n >= 10 and sysid not in sats:
                        sats[sysid] = n
                        last_fix[sysid] = (struct.unpack_from('<i', p, 8)[0] / 1e7,
                                           struct.unpack_from('<i', p, 12)[0] / 1e7)
                elif msgid == 253:
                    text = bytes(c for c in p[1:] if c != 0).decode(errors='ignore')
                    if 'Hit ground' in text:
                        crashes[sysid] = text
    pts = [last_fix[d] for d in sorted(crashes) if d in last_fix]
    assert len(pts) == 3, f"expected 3 crash points, got {len(pts)}"
    lat0 = sum(p[0] for p in pts) / 3
    lon0 = sum(p[1] for p in pts) / 3
    mx, my = circumcenter(to_meters(pts))
    cx = lat0 + my / 110540.0
    cy = lon0 + mx / (111320.0 * math.cos(math.radians(lat0)))
    print("crashed drones:", sorted(crashes))
    for d, (la, lo) in zip(sorted(crashes), pts):
        print(f"  drone {d}: last fix ({la:.7f}, {lo:.7f})  dist {haversine(cx, cy, la, lo):.1f} m")
    print(f"jammer (circumcenter): ({cx:.6f}, {cy:.6f})")
    print(f"dist to Echo Trail Park center: {haversine(cx, cy, 36.0868969, -115.2633634):.1f} m")
    print("FLAG: starpwn{Echo_Trail_Park}")

if __name__ == '__main__':
    main(sys.argv[1])
```

Output:

```
crashed drones: [2, 3, 5]
  drone 2: last fix (36.0924472, -115.2422068)  dist 1975.6 m
  drone 3: last fix (36.0778972, -115.2440034)  dist 1977.8 m
  drone 5: last fix (36.0997052, -115.2478434)  dist 1981.4 m
jammer (circumcenter): (36.086804, -115.263054)
dist to Echo Trail Park center: 29.6 m
FLAG: starpwn{Echo_Trail_Park}
```

## Flag

```
starpwn{Echo_Trail_Park}
```
