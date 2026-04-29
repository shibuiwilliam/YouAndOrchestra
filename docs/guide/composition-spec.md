# Composition Spec Reference

The `composition.yaml` file defines everything about what to generate.

## Full Schema

```yaml
title: "My Piece"              # Required
genre: "general"                # Optional, default: general
key: "C major"                  # Required format: "Note Scale"
tempo_bpm: 120                  # 20–300 BPM
time_signature: "4/4"           # "N/D" format
total_bars: 0                   # 0 = sum of sections

instruments:                    # At least one required
  - name: piano                 # Must match known instrument
    role: melody                # melody, harmony, bass, rhythm, pad

sections:                       # At least one required
  - name: intro
    bars: 8                     # Must be positive
    dynamics: "mf"              # ppp, pp, p, mp, mf, f, ff, fff
    tempo_bpm: 100              # Optional: override per section
    time_signature: "3/4"       # Optional: override per section
    key: "G major"              # Optional: override per section

generation:                     # Optional
  strategy: "rule_based"        # rule_based, stochastic
  seed: 42                      # Integer, for stochastic reproducibility
  temperature: 0.5              # 0.0–1.0, stochastic variation control
```

## Supported Keys

Any combination of root note + scale type:

**Root notes:** C, C#, D, D#, E, F, F#, G, G#, A, A#, B (also Db, Eb, Gb, Ab, Bb)

**Scale types:** major, minor, harmonic_minor, melodic_minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic_major, pentatonic_minor, blues, whole_tone, chromatic

## Dynamics

| Marking | Velocity | Description |
|---------|----------|-------------|
| ppp | 16 | Extremely soft |
| pp | 33 | Very soft |
| p | 49 | Soft |
| mp | 64 | Moderately soft |
| mf | 80 | Moderately loud |
| f | 96 | Loud |
| ff | 112 | Very loud |
| fff | 127 | Extremely loud |

## Validation

Run `yao validate <spec.yaml>` to check your spec without generating.
