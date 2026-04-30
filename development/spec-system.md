# Specification System

## Overview

YaO uses YAML-based specifications to define compositions. All specs are Pydantic-validated, git-diffable, and fully documented. YaO supports two spec formats: **v1** (simple, flat) and **v2** (detailed, 11-section).

## v1 Spec Format

### `composition.yaml` (required)

The primary spec file. Defines what to generate.

```yaml
title: "My Piece"
genre: "cinematic"
key: "D minor"
tempo_bpm: 80
time_signature: "4/4"
total_bars: 48

instruments:
  - name: piano
    role: melody        # melody, harmony, bass, rhythm, pad
  - name: cello
    role: bass

sections:
  - name: intro
    bars: 8
    dynamics: "pp"      # ppp, pp, p, mp, mf, f, ff, fff
  - name: verse
    bars: 16
    dynamics: "mf"
  - name: chorus
    bars: 16
    dynamics: "f"
  - name: outro
    bars: 8
    dynamics: "mp"

generation:
  strategy: stochastic  # rule_based, stochastic
  seed: 42              # reproducibility (stochastic only)
  temperature: 0.5      # 0.0=conservative, 1.0=adventurous
```

Sections can also have per-section overrides for `tempo_bpm`, `time_signature`, and `key`.

## v2 Spec Format

The v2 format provides 11 dedicated sections for finer control. YaO auto-detects the format based on the presence of an `identity` key.

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
  valence: 0.3        # 0.0=negative, 1.0=positive
  energy: 0.4         # 0.0=calm, 1.0=energetic
  tension: 0.3        # 0.0=relaxed, 1.0=tense
  warmth: 0.7         # 0.0=cold, 1.0=warm
  nostalgia: 0.5      # 0.0=modern, 1.0=nostalgic

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
  contour: arch        # arch, ascending, descending, wave
  range: [60, 84]      # MIDI note range

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
| `emotion` | Valence, energy, tension, warmth, nostalgia (all 0-1) |
| `form` | Sections with bar counts and dynamics |
| `melody` | Contour, range, motif definitions |
| `harmony` | Progressions, voicing rules |
| `rhythm` | Patterns, syncopation level |
| `drums` | Kit selection, patterns |
| `arrangement` | Instrumentation, layering |
| `production` | LUFS target, stereo width, effects |
| `constraints` | Musical rules (must/must_not/prefer/avoid) |

## Additional Spec Files (when relevant)

| File | Schema | Used When |
|------|--------|-----------|
| `trajectory.yaml` | `TrajectorySpec` | Shaping musical parameters over time |
| `intent.md` | Natural language | Describing the composition's purpose |
| `constraints.yaml` | `ConstraintsSpec` | Custom constraint rules (must/must_not/prefer/avoid) |
| `references.yaml` | `ReferencesSpec` | Aesthetic reference works (positive/negative polarity) |
| `negative-space.yaml` | `NegativeSpaceSpec` | Intentional silence design |
| `production.yaml` | `ProductionSpec` | Mix/master parameters (LUFS, stereo width, reverb) |

### `trajectory.yaml` (optional)

Shapes musical parameters over time, independent of note content.

```yaml
trajectories:
  tension:
    type: bezier         # bezier, stepped, linear
    waypoints: [[0, 0.2], [16, 0.85], [32, 0.6], [48, 0.3]]
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, chorus: 0.9, outro: 0.3 }
  predictability:
    target: 0.65
    variance: 0.15
```

### `intent.md` (recommended)

Natural language description of the composition's intent. 1-3 sentences. This is the human's voice — never auto-generated.

```markdown
# My Piece

A melancholic piano piece for a rainy afternoon. Builds slowly from
quiet contemplation to a bittersweet climax, then fades to silence.
Not sad -- more like comfortable loneliness.
```

## Templates

Located in `specs/templates/`:

### v1 Templates

| Template | Description |
|----------|-------------|
| `minimal.yaml` | 8 bars, solo piano, C major, 120 BPM — simplest possible spec |
| `bgm-90sec.yaml` | 90-second BGM, piano + acoustic bass, 4 sections, dynamic arc |
| `cinematic-3min.yaml` | 3-minute cinematic in D minor, 4 instruments, 6 sections |
| `trajectory-example.yaml` | Trajectory curves demonstration (bezier, stepped, linear) |

### v2 Templates

| Template | Description |
|----------|-------------|
| `v2/bgm-90sec-pop.yaml` | Pop-style BGM with emotion, form, melody, and production sections |
| `v2/cinematic-3min.yaml` | Full cinematic with trajectory, constraints, and all 11 sections |
| `v2/loopable-game-bgm.yaml` | Seamlessly looping game music with loop-aware constraints |

## Example Projects

YaO ships with example projects in `specs/projects/`, covering styles from classical piano trio to hard rock game BGM. Each includes `composition.yaml` and `intent.md`.

## Project Structure

```
specs/projects/my-song/
  +-- composition.yaml    # Required (v1 or v2)
  +-- intent.md           # Recommended
  +-- trajectory.yaml     # Optional
  +-- constraints.yaml    # Optional

outputs/projects/my-song/
  +-- iterations/
      +-- v001/
      |   +-- full.mid
      |   +-- stems/
      |   +-- analysis.json
      |   +-- evaluation.json
      |   +-- provenance.json
      +-- v002/
```

## Validation

All specs are validated via Pydantic at load time:
- `CompositionSpec.from_yaml(path)` — validates all fields, key, tempo range (20-300 BPM), dynamics
- `TrajectorySpec.from_yaml(path)` — validates waypoint values in [0, 1]
- Validation failures raise `SpecValidationError` with field name and actionable message
- v1/v2 format is auto-detected by `load_composition_spec_auto()`

CLI validation: `yao validate specs/projects/my-song/composition.yaml`

Loading helpers:
```python
from yao.schema.loader import (
    load_composition_spec,       # v1 only
    load_composition_spec_auto,  # auto-detect v1/v2
    load_trajectory_spec,
    load_project_specs,
)
```
