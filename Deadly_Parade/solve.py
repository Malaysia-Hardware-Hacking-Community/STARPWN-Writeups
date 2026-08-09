#!/usr/bin/env python3
"""Deadly_Parade: GPS-jam triangulation from MAVLink SITL pcap.

Method:
  1. Per drone, follow msgid 24 (GPS_RAW_INT, lat@8 lon@12) fixes in time order.
  2. When satellite count (byte 29) drops from >=10 to <10, the previous fix is
     the LAST VALID POSITION before the jammer killed that drone's GPS.
  3. Drones that actually crashed are identified via msgid 253 STATUSTEXT
     ("EKF Failsafe ... LAND Mode" + "SIM Hit ground").
  4. The jamming source must be equidistant from the crash points -> circumcenter
     of the last-valid-fix triangle.
  5. Reverse-geocode the circumcenter -> named place = flag.
"""
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
        if len(data) < 20:
            continue
        if struct.unpack_from('>H', data, 0)[0] != 0x0800:   # IPv4 only
            continue
        ip_start = 20
        ihl = (data[ip_start] & 0x0f) * 4
        if data[ip_start + 9] != 17:                          # UDP
            continue
        udp_start = ip_start + ihl
        sport, dport, ulen, _ = struct.unpack_from('>HHHH', data, udp_start)
        yield ts_sec + ts_usec / 1e6, sport, dport, data[udp_start + 8: udp_start + ulen]

def parse_mavlink2(buf):
    i = 0
    while i < len(buf):
        if buf[i] != 0xFD:
            i += 1
            continue
        if i + 10 > len(buf):
            break
        length = buf[i + 1]
        incompat = buf[i + 2]
        sysid = buf[i + 5]
        msgid = struct.unpack_from('<I', buf, i + 7)[0] & 0xFFFFFF
        pstart = i + 10
        pend = pstart + length
        crc_end = pend + 2
        if incompat & 0x01:
            crc_end += 13
        if crc_end > len(buf):
            break
        yield msgid, sysid, buf[pstart:pend]
        i = crc_end

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def to_meters(pts):
    lat0 = sum(p[0] for p in pts) / len(pts)
    lon0 = sum(p[1] for p in pts) / len(pts)
    return [( (lon - lon0) * 111320.0 * math.cos(math.radians(lat0)), (lat - lat0) * 110540.0 ) for lat, lon in pts]

def circumcenter(pts):                      # pts already in local meters
    (x1, y1), (x2, y2), (x3, y3) = pts
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    return ux, uy

def main(pcap):
    last_fix = {}      # drone -> (lat, lon) before sat drop
    sats = {}          # drone -> current satellite count
    crashes = {}       # drone -> "Hit ground"
    with open(pcap, 'rb') as f:
        for ts, sport, dport, payload in iter_packets(f):
            for msgid, sysid, p in parse_mavlink2(payload):
                if sysid in (255, 0):
                    continue
                if msgid == 24 and len(p) >= 30:                 # GPS_RAW_INT
                    n = p[29]
                    if n >= 10:
                        sats[sysid] = n
                        last_fix[sysid] = (struct.unpack_from('<i', p, 8)[0] / 1e7,
                                           struct.unpack_from('<i', p, 12)[0] / 1e7)
                    elif sysid in last_fix and sysid not in sats:  # first drop already recorded
                        pass
                    elif sysid in last_fix and sats.get(sysid, 0) >= 10:
                        sats[sysid] = n                          # freeze: keep last valid fix
                elif msgid == 253:
                    text = bytes(c for c in p[1:] if c != 0).decode(errors='ignore')
                    if 'Hit ground' in text:
                        crashes[sysid] = text
    print(f"drones that crashed: {sorted(crashes)}")
    print(f"drones with a valid pre-jam fix: {sorted(last_fix)}")
    pts = [last_fix[d] for d in sorted(crashes) if d in last_fix]
    assert len(pts) == 3, f"expected 3 crash points, got {len(pts)}"
    lat0 = sum(p[0] for p in pts) / 3
    lon0 = sum(p[1] for p in pts) / 3
    mx, my = circumcenter(to_meters(pts))
    cx = lat0 + my / 110540.0
    cy = lon0 + mx / (111320.0 * math.cos(math.radians(lat0)))
    print(f"\ncrash points (last valid GPS fix):")
    for (la, lo), d in zip(pts, sorted(crashes)):
        if d in last_fix:
            print(f"  drone {d:2d}: ({la:.7f}, {lo:.7f})")
    print(f"\njammer (circumcenter): ({cx:.6f}, {cy:.6f})")
    for la, lo in pts:
        print(f"  distance from jammer: {haversine(cx, cy, la, lo):.1f} m")
    park = (36.086897, -115.263363)      # Echo Trail Park, 5655 W Buffalo Dr
    print(f"\ndistance circumcenter -> Echo Trail Park: {haversine(cx, cy, *park):.1f} m")
    for la, lo in pts:
        print(f"  distance crash point -> Echo Trail Park: {haversine(*park, la, lo):.1f} m")
    print("\nFLAG: starpwn{Echo_Trail_Park}")

if __name__ == '__main__':
    main(sys.argv[1])
