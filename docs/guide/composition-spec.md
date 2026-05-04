# Composition Spec Reference

YaO supports two spec formats: **v1** (simple, flat) and **v2** (detailed, 11-section). The format is auto-detected when loading.

## v1 Format (Simple)

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
  strategy: "rule_based"        # rule_based, stochastic, rule_based_v2, stochastic_v2,
                                # markov, twelve_tone, process_music, constraint_solver
  seed: 42                      # Integer, for reproducibility
  temperature: 0.5              # 0.0–1.0, variation control
```

## v2 Format (Detailed)

The v2 format provides 11 dedicated sections for finer control over all aspects of a composition. Auto-detected by the presence of an `identity` key.

```yaml
identity:
  title: "Rainy Cafe"
  purpose: "Background music for a cafe scene"
  duration_sec: 90
  loopable: false

globals:
  key: "D minor"
  bpm: 90
  time_signature: "4/4"
  genre: "ambient"

emotion:
  valence: 0.3                  # 0.0=negative, 1.0=positive
  energy: 0.4                   # 0.0=calm, 1.0=energetic
  tension: 0.3                  # 0.0=relaxed, 1.0=tense
  warmth: 0.7                   # 0.0=cold, 1.0=warm
  nostalgia: 0.5                # 0.0=modern, 1.0=nostalgic

form:
  sections:
    - name: intro
      bars: 4
      dynamics: pp
    - name: verse
      bars: 8
      dynamics: mp
    - name: chorus
      bars: 8
      dynamics: f
    - name: outro
      bars: 4
      dynamics: pp

melody:
  contour: arch                 # arch, ascending, descending, wave
  range: [60, 84]               # MIDI note range

harmony:
  progressions: ["I-IV-V-I"]
  voicing_rules: []

rhythm:
  patterns: []
  syncopation: 0.2

drums:
  kit: "acoustic"
  patterns: []

arrangement:
  instruments:
    - name: piano
      role: melody
    - name: cello
      role: bass

production:
  lufs_target: -14.0
  stereo_width: 0.7

constraints:
  - type: must_not
    rule: parallel_fifths
    scope: global
    severity: error
```

### v2 Sections

| Section | Purpose |
|---------|---------|
| `identity` | Title, purpose, duration, loopability |
| `globals` | Key, BPM, time signature, genre |
| `emotion` | Valence, energy, tension, warmth, nostalgia (all 0.0-1.0) |
| `form` | Sections with bar counts and dynamics |
| `melody` | Contour, range, motif definitions |
| `harmony` | Progressions, voicing rules |
| `rhythm` | Patterns, syncopation level |
| `drums` | Kit selection, patterns |
| `arrangement` | Instrumentation, layering |
| `production` | LUFS target, stereo width, effects |
| `constraints` | Musical rules (must/must_not/prefer/avoid) |

### v2 Templates

Three templates are available in `specs/templates/v2/`:

| Template | Description |
|----------|-------------|
| `bgm-90sec-pop.yaml` | Pop-style BGM with emotion, form, melody, and production sections |
| `cinematic-3min.yaml` | Full cinematic with trajectory, constraints, and all 11 sections |
| `loopable-game-bgm.yaml` | Seamlessly looping game music with loop-aware constraints |

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

Run `yao validate <spec.yaml>` to check your spec without generating. Both v1 and v2 formats are validated at load time via Pydantic.

```python
from yao.schema.loader import load_composition_spec_auto

# Auto-detects v1 or v2
spec = load_composition_spec_auto(Path("my-spec.yaml"))
```
