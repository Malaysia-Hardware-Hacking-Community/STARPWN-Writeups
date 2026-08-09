---
title: "DEAD_LIGHT"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: misc
difficulty: medium
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# DEAD_LIGHT

## Summary

A 1024×1024 RGB PNG with 12-fold radial symmetry hides a flag in the divergence between RGB channel peak radii. Converting to polar coordinates linearizes the 12 guide-lights into vertical lines; tracking each channel's peak radius per angle reveals the Blue channel lags/leads Red/Green clockwise. Offsets from the factory radius at the 12 clock positions encode the flag.

## Solution

### Step 1: Polar Transform + Channel Separation

The image has 12 bright guide-lights in a ring around a dark center. A Cartesian→polar transform (radius 0–511, angle 0–359°) converts the circular features into 12 vertical lines at 0°, 30°, …, 330°. The clue "Never let all three ghosts vote on the same pixel" means to analyze R, G, B independently — find each channel's peak radius (brightest pixel) at every angle.

```python
#!/usr/bin/env python3
"""DEAD_LIGHT solve: polar transform + channel peak-radius divergence."""
from PIL import Image
import numpy as np

img = Image.open("deadlight-preview.png")
arr = np.array(img)  # 1024x1024x3
cx, cy = 512, 512

# Cartesian -> polar
polar = np.zeros((512, 360, 3), dtype=np.uint8)
for r in range(512):
    for a in range(360):
        ang = a * 2 * np.pi / 360
        x = int(cx + r * np.cos(ang))
        y = int(cy + r * np.sin(ang))
        if 0 <= x < 1024 and 0 <= y < 1024:
            polar[r, a] = arr[y, x]

# Peak radius per channel per angle
peak = {}
for ch_idx, ch_name in [(0, "R"), (1, "G"), (2, "B")]:
    col = polar[:, :, ch_idx]
    peak[ch_name] = [col[:, a].argmax() for a in range(360)]

# 12 clock positions (guide lights)
angles_12 = [i * 30 for i in range(12)]
factory = 288  # mean peak radius ≈ factory coordinate

offsets = [peak["B"][a] - factory for a in angles_12]
flag = "".join(chr((o + 256) % 256) for o in offsets)
print(f"[+] FLAG: {flag}")
```

**Output:**
```
[+] FLAG: STARPWN{DEAD_SIGN_RETURNS}
```

## Flag

```
STARPWN{DEAD_SIGN_RETURNS}
```