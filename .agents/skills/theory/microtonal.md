---
topic: microtonal_tuning
applies_to: [generation, rendering, evaluation]
---

# Microtonal Tuning — Theory Skill

## Overview

Most Western music uses 12-EDO (12 Equal Divisions of the Octave), where
each semitone is exactly 100 cents. Many world music traditions use tunings
where intervals are NOT multiples of 100 cents.

## Key Concepts

- **Cent**: 1/100th of a 12-EDO semitone. 1200 cents = 1 octave.
- **Quarter-tone**: 50 cents. Used in Arabic maqam system.
- **Just Intonation**: Pure harmonic ratios (e.g., 3/2 = 702 cents for a fifth).
- **Non-equal temperament**: Intervals vary (gamelan pelog/slendro).

## YaO Tuning Module

All pitch-to-cents conversions go through `yao.ir.tuning.Tuning`:
- `cents_from_a4(midi, offset)` — absolute cents from A4
- `midi_from_cents(cents)` — nearest MIDI note + bend offset
- `pitch_bend_from_cents(cents)` — MIDI pitch bend value
- `scale_pitches_cents(root, scale, octaves)` — generate scale pitches

## MIDI Rendering Modes

| Mode | Behavior | Use For |
|---|---|---|
| `per_instrument` | Round to 12-EDO, warn on loss | Standard Western music |
| `channel_per_note` | Each note gets its own channel + pitch bend | Microtonal with standard synths |
| `mpe` | MPE protocol (channels 2-16) | MPE-compatible synths |

## Supported Scales

### Western 12-EDO
All intervals are multiples of 100 cents. No pitch bend needed.

### Hindustani Raga
- Raga Darbari: komal Ga (~280 cents) requires microtonal rendering
- Raga Yaman: equivalent to Lydian, fits 12-EDO
- Raga Bhairav: fits 12-EDO

### Arabic Maqam
- Maqam Rast: quarter-tones at 3rd (350c) and 7th (1050c)
- Maqam Bayati: quarter-flat 2nd (150c)
- Require `channel_per_note` or `mpe` mode

### Gamelan
- Pelog: 7-tone, non-equal intervals
- Slendro: 5-tone, near-equidistant (~240 cents)
- Highly variable between ensembles

## Limitations

- MIDI 1.0 pitch bend: ±50 cent precision per channel
- MPE: 15 simultaneous notes maximum (channels 2-16)
- Not all synths support MPE or per-channel tuning
