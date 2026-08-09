#!/usr/bin/env python3
"""Silent_Beacon — CCSDS telemetry parser + flag extraction.

The capture contains CCSDS Space Packets delimited by ASM sync marker
0x1ACFFC1D. Three APIDs interleave: 50 (SYSLOG ASCII), 100 (HK_NOMINAL,
14-byte payload documented in telemetry_dictionary.json), 200 (ADCS_STATUS,
layout unknown).

Hidden message: HK packets whose `mode` byte is outside the valid range
(0-7) actually carry ASCII flag chars in mode & 0x7F. Sort by CCSDS
sequence count to reassemble.
"""
import struct

data = open('capture.bin', 'rb').read()
ASM = bytes.fromhex('1acffc1d')

packets = []
i = 0
while True:
    j = data.find(ASM, i)
    if j == -1:
        break
    hdr = data[j+4:j+10]
    apid = (hdr[0] << 8 | hdr[1]) & 0x7FF
    seq = (hdr[2] << 8 | hdr[3]) & 0x3FFF
    length = (hdr[4] << 8 | hdr[5]) + 1
    packets.append((apid, seq, data[j+10:j+10+length]))
    i = j + 1

print(f"[*] {len(packets)} packets, ASM {ASM.hex()}, APIDs: "
      f"{sorted({a for a, _, _ in packets})}")

anom = [(seq, p[12]) for a, seq, p in packets if a == 100 and p[12] > 7]
anom.sort()
flag = ''.join(chr(m & 0x7F) for _, m in anom)
print(f"[*] {len(anom)} anomalous HK packets (mode outside 0-7)")
print(f"[+] FLAG: {flag}")
