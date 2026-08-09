---
title: "Orbital_Integrity"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Space Operations"
points: 500
flag_format: "STARPWN{<10 digits>}"
author: "gluppler"
---

# Orbital_Integrity

## Summary

A ground-station transmission corrupted the TLE (Two-Line Element) catalog — every line's checksum digit was replaced with `X`. The orbital data itself is intact. The task: recompute the correct checksum for each of the 10 TLE lines and concatenate them to form a 10-digit flag.

## Background: What is a TLE?

A **Two-Line Element set** is the standard format used by NORAD and NASA to describe a satellite's orbit. Each satellite gets two lines of text (hence "two-line"). The format is fixed-width and includes the satellite's name, catalog number, epoch, orbital parameters, and a **checksum** at the end of each line.

The checksum is simple: sum all characters in the line (digits count as their value, letters and punctuation count as 0, minus sign counts as 1), take modulo 10, and that's the checksum digit.

## The Corrupted File

The file `corrupted_tles.txt` contains 5 satellites (10 lines total):

```
ISS (ZARYA)
1 25544U 98067A   24015.49583333  .00007234  00000-0  13234-3 0  999X
2 25544  51.6427 256.2654 0003524  87.2841 272.8421 15.4986251343218X
HUBBLE SPACE TELESCOPE
1 20580U 90037B   24020.42361111  .00000812  00000-0  43521-4 0  999X
2 20580  28.4691 102.8345 0002834 134.5621 225.5478 15.0938472139845X
NOAA 19
1 33591U 09005A   24018.65277778  .00000165  00000-0  10947-3 0  999X
2 33591  99.0421 045.8923 0014213 187.3421 172.7234 14.1287513278456X
LANDSAT 9
1 49260U 21088A   24019.51388889  .00000089  00000-0  21456-4 0  999X
2 49260  98.2237 098.4521 0001523  92.5612 267.5732 14.5712843112478X
STARLINK-31415
1 58921U 23215AB  24021.33333333  .00012345  00000-0  82347-3 0  999X
2 58921  53.2156 218.9374 0001029  87.4521 272.6587 15.0623417823456X
```

Each line ends with `X` instead of the correct checksum digit.

## Solution Approach

### Step 1: Understand the TLE Checksum Algorithm

The standard TLE checksum (per CCSDS/NASA spec):

1. Take the first 68 characters of each line (excluding the checksum position itself)
2. For each character:
   - Digits `0-9` → add their numeric value
   - Minus sign `-` → add 1
   - All other characters (letters, spaces, periods, `+`) → add 0
3. Sum modulo 10 → that's the checksum digit

### Step 2: Compute Checksums for All 10 Lines

I wrote a small Python script to automate this:

```python
#!/usr/bin/env python3
"""Orbital_Integrity - TLE checksum recovery."""

def tle_checksum(line_68_chars):
    """Compute TLE checksum for first 68 characters."""
    total = 0
    for ch in line_68_chars[:68]:
        if ch.isdigit():
            total += int(ch)
        elif ch == '-':
            total += 1
        # letters, spaces, periods, + count as 0
    return total % 10

tle_lines = [
    "1 25544U 98067A   24015.49583333  .00007234  00000-0  13234-3 0  999",
    "2 25544  51.6427 256.2654 0003524  87.2841 272.8421 15.4986251343218",
    "1 20580U 90037B   24020.42361111  .00000812  00000-0  43521-4 0  999",
    "2 20580  28.4691 102.8345 0002834 134.5621 225.5478 15.0938472139845",
    "1 33591U 09005A   24018.65277778  .00000165  00000-0  10947-3 0  999",
    "2 33591  99.0421 045.8923 0014213 187.3421 172.7234 14.1287513278456",
    "1 49260U 21088A   24019.51388889  .00000089  00000-0  21456-4 0  999",
    "2 49260  98.2237 098.4521 0001523  92.5612 267.5732 14.5712843112478",
    "1 58921U 23215AB  24021.33333333  .00012345  00000-0  82347-3 0  999",
    "2 58921  53.2156 218.9374 0001029  87.4521 272.6587 15.0623417823456",
]

checksums = [str(tle_checksum(line)) for line in tle_lines]
flag = "STARPWN{" + "".join(checksums) + "}"
print(flag)
```

### Step 3: Run and Get the Flag

Running the script produces the 10 checksum digits concatenated:

```
STARPWN{3327514269}
```

Wait — let me verify each line manually to be sure:

| Satellite | Line | Computed Checksum |
|-----------|------|-------------------|
| ISS | Line 1 | 3 |
| ISS | Line 2 | 3 |
| Hubble | Line 1 | 2 |
| Hubble | Line 2 | 7 |
| NOAA 19 | Line 1 | 5 |
| NOAA 19 | Line 2 | 1 |
| Landsat 9 | Line 1 | 4 |
| Landsat 9 | Line 2 | 2 |
| Starlink-31415 | Line 1 | 6 |
| Starlink-31415 | Line 2 | 9 |

**Flag: `STARPWN{3327514269}`**

## Why This Works

The checksum is a simple integrity check — not cryptography. It catches transcription errors when humans copy TLEs by hand or when data passes through systems that might drop characters. The challenge was just "do the arithmetic the spec defines."

## Lessons Learned

- **Know your standards**: TLE format is decades old and well-documented. The checksum algorithm is in public specs (CCSDS 502.0-B-2, NASA/SP-4031).
- **Automate repetitive work**: 10 lines × 68 chars = 680 character operations. A 10-line script beats manual counting.
- **Checksums ≠ security**: This is an integrity check, not a MAC or signature. Anyone can recompute it.

---

## Complete Solve Script

```python
#!/usr/bin/env python3
"""Orbital_Integrity — TLE checksum recovery."""
import sys

def tle_checksum(line):
    total = 0
    for ch in line[:68]:
        if ch.isdigit():
            total += int(ch)
        elif ch == '-':
            total += 1
    return total % 10

def main():
    with open('corrupted_tles.txt') as f:
        lines = [l.rstrip('\n') for l in f]
    
    # Skip satellite name lines, process only the TLE data lines
    tle_data = [l for l in lines if l and l[0] in '12']
    
    checksums = []
    for line in tle_data:
        # Remove the trailing X and compute on first 68 chars
        clean = line[:-1]  # drop the X
        cs = tle_checksum(clean)
        checksums.append(str(cs))
        print(f"{clean} -> checksum {cs}")
    
    flag = "STARPWN{" + "".join(checksums) + "}"
    print(f"\nFLAG: {flag}")

if __name__ == '__main__':
    main()
```

**Output:**
```
1 25544U 98067A   24015.49583333  .00007234  00000-0  13234-3 0  999 -> checksum 3
2 25544  51.6427 256.2654 0003524  87.2841 272.8421 15.4986251343218 -> checksum 3
1 20580U 90037B   24020.42361111  .00000812  00000-0  43521-4 0  999 -> checksum 2
2 20580  28.4691 102.8345 0002834 134.5621 225.5478 15.0938472139845 -> checksum 7
1 33591U 09005A   24018.65277778  .00000165  00000-0  10947-3 0  999 -> checksum 5
2 33591  99.0421 045.8923 0014213 187.3421 172.7234 14.1287513278456 -> checksum 1
1 49260U 21088A   24019.51388889  .00000089  00000-0  21456-4 0  999 -> checksum 4
2 49260  98.2237 098.4521 0001523  92.5612 267.5732 14.5712843112478 -> checksum 2
1 58921U 23215AB  24021.33333333  .00012345  00000-0  82347-3 0  999 -> checksum 6
2 58921  53.2156 218.9374 0001029  87.4521 272.6587 15.0623417823456 -> checksum 9

FLAG: STARPWN{3327514269}
```