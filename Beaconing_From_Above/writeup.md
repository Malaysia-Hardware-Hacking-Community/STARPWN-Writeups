---
title: "Beaconing_From_Above"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Space Communications & RF"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# Beaconing_From_Above

## Summary

An old amateur radio recording (`beacon.wav`, 82 seconds, 22.05 kHz mono) from a long-dormant CubeSat was provided. The audio contains Morse code (CW) beeps. The Morse **decodes directly to the flag payload** — four words: `B34C0N`, `D3C0D3D`, `V14`, `R4D10`. Join with underscores and wrap in `STARPWN{...}`.

## The Audio File

```bash
file beacon.wav
# beacon.wav: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 22050 Hz
```

- Duration: ~82 seconds
- Sample rate: 22,050 Hz
- 16-bit signed PCM

When played, you hear a clear repeating pattern of CW (Morse) tones — a satellite beacon transmitting its message.

## Solution

### Step 1: Listen / Identify Mode

Open `beacon.wav` in any audio player. You hear distinct on/off keying — classic Morse code (CW). This is the signal type.

### Step 2: Decode with a Morse Decoder

Use any CW/Morse audio decoder:

- **Online (easiest)**: https://morsecode.world/international/decoder/audio-decoder-adaptive.html
- **Desktop**: fldigi, CW Skimmer, G4FON Koch Trainer
- **CLI**: `morse-decoder-audio` (various GitHub projects)

Upload `beacon.wav` and decode.

### Step 3: Decoder Output

The decoder outputs (repeating loop):

```
B34C0N D3C0D3D V14 R4D10
```

**This is already the flag payload.** The Morse encodes digits `3`, `4`, `0`, `1` as individual characters (`...--`, `....-`, `-----`, `.----`), not as letters.

The challenge description confirms: *"The decoded message is uppercase A-Z and digits."* — so digits appear literally in the Morse.

### Step 4: Format the Flag

Four payload words → join with single underscores → wrap:

```
STARPWN{B34C0N_D3C0D3D_V14_R4D10}
```

## Why This Works

The satellite beacon transmits its identifier/status in Morse. The message **is** the flag payload. No translation step needed — the decoder gives you exactly what goes in the flag.

## Lessons Learned

- **Morse decodes to exactly what was sent**: If the sender keyed digits, the decoder outputs digits. Don't "translate" the output — the output *is* the payload.
- **Challenge spec tells you the alphabet**: "uppercase A-Z and digits" = the Morse alphabet includes 0-9. Expect digits in the output.
- **Four words = four underscores**: Count the word groups in the decoder output.
- **Use the right tool**: Morse → CW decoder. Don't try to manually transcribe unless necessary.

## Complete Reproduction

1. Go to https://morsecode.world/international/decoder/audio-decoder-adaptive.html
2. Choose `beacon.wav` → Decode
3. Read output: `B34C0N D3C0D3D V14 R4D10`
4. Format: `STARPWN{B34C0N_D3C0D3D_V14_R4D10}`

## Flag

```
STARPWN{B34C0N_D3C0D3D_V14_R4D10}
```