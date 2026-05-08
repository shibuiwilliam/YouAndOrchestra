# Composition Spec Reference

YaO supports three spec formats. The format is auto-detected when loading.

- **Simple format** — flat YAML, quick to write
- **Detailed format** — 11-section YAML for fine control
- **Composable format** — extends/overrides pattern with fragment reuse

## Simple Format

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
  strategy: "stochastic"        # rule_based, stochastic, markov, twelve_tone,
                                # process_music, constraint_solver, loop_evolution, ai_seed
  seed: 42                      # Integer, for reproducibility
  temperature: 0.5              # 0.0–1.0, variation control
```

## Detailed Format (11-section)

Provides dedicated sections for finer control over all aspects. Auto-detected by the presence of an `identity` key.

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

### Sections Reference

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

## Composable Format

Uses `extends` and `overrides` to build on existing specs or fragments:

```yaml
extends: "specs/fragments/lofi_base.yaml"
overrides:
  globals:
    key: "E minor"
    bpm: 75
  emotion:
    nostalgia: 0.8
```

Fragments in `specs/fragments/` provide reusable building blocks (jazz_trio, lofi_base, cinematic_base).

## Supported Keys

Any combination of root note + scale type:

**Root notes:** C, C#, D, D#, E, F, F#, G, G#, A, A#, B (also Db, Eb, Gb, Ab, Bb)

**Scale types:** major, minor, harmonic_minor, melodic_minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic_major, pentatonic_minor, blues, whole_tone, chromatic

## Tonal Systems

For non-Western or non-tonal music, use the `tonal_system` field instead of `key`:

```yaml
tonal_system:
  kind: "maqam"       # tonal_major_minor, modal, pentatonic, blues,
                      # microtonal, atonal, drone, raga, maqam, custom
  root: "D"
  maqam_name: "hijaz"
```

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

```bash
yao validate my-spec.yaml
```

All formats are validated at load time via Pydantic. Invalid specs produce clear error messages.

## Feature Flags (v3.0)

Control Combination Stack modules via a `features:` block in any spec format:

```yaml
features:
  chord_aware_melody: true          # Default ON — melody constrained by active chord
  voice_leading_optimization: true  # Default ON — Hungarian-optimal voicings
  reharmonization: false            # Default OFF — opt-in reharmonization
  modulation_planner: false         # Default OFF — key modulation planning
  listening_agents: false           # Default OFF — turn-based generation
  genre_blend: false                # Default OFF — n-way genre blending
  rhythm_markov: false              # Default OFF — Markov rhythm models
  polyrhythm: false                 # Default OFF — polyrhythmic textures
  theme_recurrence: false           # Default OFF — long-form thematic returns
```

When a flag is `false`, the corresponding coupling module returns input unchanged (identity function).

## Genre Blending (v3.0)

Instead of a single genre, blend multiple genres with weighted profiles:

```yaml
genre_blend:
  - {profile: bossa_nova, weight: 0.6}
  - {profile: drum_n_bass, weight: 0.3}
  - {profile: cinematic, weight: 0.1}
```

The result is a single synthesized `MelodicProfile`. Discrete fields use weighted random selection; numeric fields interpolate linearly.

## Harmonic Devices (v3.0)

Specify genre-typical harmonic patterns via `harmonic-devices.yaml`:

```yaml
devices:
  - {name: jazz_turnaround_I_VI_II_V, placement: section_end, sections: [verse, chorus]}
  - {name: coltrane_changes, placement: bridge, sections: [bridge]}

reharmonization:
  intensity: 0.4
  preserve_melody: true
  operations:
    - secondary_dominant
    - tritone_substitution
    - ii_V_insertion
```

15 harmonic device YAMLs are available in `src/yao/constants/harmonic_devices/`.
