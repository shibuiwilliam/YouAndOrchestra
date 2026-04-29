# Specification System

## Overview

YaO uses YAML-based specifications to define compositions. All specs are Pydantic-validated, git-diffable, and fully documented.

## Core Spec Files

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
Not sad — more like comfortable loneliness.
```

## Additional Spec Files (when relevant)

| File | Schema | Used When |
|------|--------|-----------|
| `constraints.yaml` | `ConstraintsSpec` | Custom constraint rules |
| `references.yaml` | `ReferencesSpec` | Aesthetic reference works |
| `negative-space.yaml` | `NegativeSpaceSpec` | Intentional silence design |
| `production.yaml` | `ProductionSpec` | Mix/master parameters |
| `arrangement.yaml` | _(planned)_ | Arrangement transformations |

## Templates

Located in `specs/templates/`:

| Template | Description |
|----------|-------------|
| `minimal.yaml` | 8 bars, solo piano, simplest possible spec |
| `bgm-90sec.yaml` | 90-second BGM, piano + bass, 4 sections |
| `cinematic-3min.yaml` | 3-minute cinematic, 4 instruments, 6 sections |
| `trajectory-example.yaml` | Trajectory curves demonstration |

## Project Structure

```
specs/projects/my-song/
  ├── composition.yaml    # Required
  ├── intent.md           # Recommended
  ├── trajectory.yaml     # Optional
  └── constraints.yaml    # Optional

outputs/projects/my-song/
  └── iterations/
      ├── v001/
      │   ├── full.mid
      │   ├── stems/
      │   ├── analysis.json
      │   └── provenance.json
      └── v002/
```

## Validation

All specs are validated via Pydantic at load time:
- `CompositionSpec.from_yaml(path)` — validates all fields, key, tempo range, dynamics
- `TrajectorySpec.from_yaml(path)` — validates waypoint values in [0, 1]
- Validation failures raise `SpecValidationError` with field name and actionable message

CLI validation: `yao validate specs/projects/my-song/composition.yaml`
