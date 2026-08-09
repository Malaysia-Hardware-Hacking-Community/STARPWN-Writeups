---
title: "Oversized_Downlink"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Misc"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# Oversized_Downlink

## Summary

A PNG image (`downlink.png`, 256×256 pixels) was provided, supposedly a thumbnail of Earth limb imagery from a satellite downlink. The challenge description noted: "the on-bus bandwidth telemetry shows it was larger than a normal thumbnail of this size should be." This hinted at hidden data — the image file size was abnormally large for its dimensions, suggesting steganography.

## The Image File

```bash
file downlink.png
# downlink.png: PNG image data, 256 x 256, 8-bit/color RGB, non-interlaced

ls -lh downlink.png
# 171K downlink.png  ← 171 KB for a 256×256 RGB image is suspicious
```

A normal 256×256 RGB PNG (8-bit) should be ~20-50 KB compressed. 171 KB suggests extra data hidden in the image.

## What is LSB Steganography?

**Least Significant Bit (LSB) steganography** hides data by modifying the lowest bit of each color channel (R, G, B) in each pixel. Since changing the LSB alters the color value by only ±1 (out of 256), the image looks identical to human eyes but carries hidden bits.

For a 256×256 RGB image:
- 256 × 256 × 3 channels = 196,608 bits available
- = 24,576 bytes of hidden payload capacity

## Solution Approach

### Step 1: Quick Visual Inspection

Open `downlink.png` in any image viewer. It looks like a normal Earth limb photo — curved horizon, black space, blue atmosphere. No visible artifacts.

### Step 2: Use Aperi'Solve (Automated Stego Analysis)

[Aperi'Solve](https://aperisolve.fr/) is a web-based steganography analysis platform. It runs multiple tools automatically:

1. Upload `downlink.png` to https://aperisolve.fr/
2. Wait for analysis (typically 10-30 seconds)
3. Check the **Zsteg** section in results

### Step 3: Zsteg Findings

Zsteg (a tool for detecting LSB steganography in PNG/BMP) reported:

```
b1,rgb,lsb,xy       .. text: "STARPWN{lsb_st3g0_1n_th3_d0wnl1nk_ch4nnel}"
```

This means: **Blue channel, RGB order, LSB, X-Y pixel order** → the hidden text is the flag.

### Step 4: Verify with Command Line (Optional)

```bash
# Install zsteg
gem install zsteg

# Run locally
zsteg downlink.png
```

Output:
```
b1,rgb,lsb,xy       .. text: "STARPWN{lsb_st3g0_1n_th3_d0wnl1nk_ch4nnel}"
b1,rgb,msb,xy       .. text: "..." (noise)
b2,rgb,lsb,xy       .. file: ...
...
```

The `b1` means "bit 1" (the least significant bit), `rgb` means all three channels, `lsb` = least significant bit first, `xy` = left-to-right, top-to-bottom pixel order.

### Step 5: Extract the Flag

The flag is directly readable from the Zsteg output:

```
STARPWN{lsb_st3g0_1n_th3_d0wnl1nk_ch4nnel}
```

## Why This Works

The satellite downlink image was used as a carrier for covert data. The ground station noticed the file size anomaly ("larger than a normal thumbnail") — that's the operational security clue. In real life, this could be an insider threat exfiltrating data through apparently innocent imagery.

LSB stego is the most basic image steganography:
- **Pros**: Simple, high capacity, visually invisible
- **Cons**: Trivially detected by statistical analysis (chi-square, RS analysis) and tools like Zsteg

## Lessons Learned

- **File size anomalies are red flags**: A 256×256 PNG should not be 171 KB. Always check `ls -lh` and compare to expected sizes.
- **Aperi'Solve is a great first pass**: It runs 10+ stego tools in parallel (zsteg, steghide, exiftool, binwalk, strings, foremost, etc.) and summarizes findings.
- **Zsteg is the go-to for PNG LSB**: Purpose-built for this exact scenario.

## Complete Reproduction

### Web (Aperi'Solve):
1. Go to https://aperisolve.fr/
2. Upload `downlink.png`
3. Scroll to **Zsteg** section
4. Read flag: `STARPWN{lsb_st3g0_1n_th3_d0wnl1nk_ch4nnel}`

### Command Line:
```bash
gem install zsteg
zsteg downlink.png
# b1,rgb,lsb,xy       .. text: "STARPWN{lsb_st3g0_1n_th3_d0wnl1nk_ch4nnel}"
```

## Flag

```
STARPWN{lsb_st3g0_1n_th3_d0wnl1nk_ch4nnel}
```
