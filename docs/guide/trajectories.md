# Trajectory System

Trajectories define how musical parameters change over time, independent of the notes themselves. This is YaO's implementation of **Principle 4: time-axis first**.

## Dimensions

| Dimension | Controls | Effect |
|-----------|----------|--------|
| `tension` | Velocity/dynamics | Higher tension → louder, more intense |
| `density` | Note count per bar | Higher density → more notes |
| `predictability` | Pattern regularity | Higher → more repetitive patterns |
| `brightness` | Timbral quality | Higher → brighter tone selection |
| `register_height` | Octave placement | Higher → notes in higher octaves |

## Interpolation Types

### Bezier (smooth curves)
```yaml
tension:
  type: bezier
  waypoints: [[0, 0.2], [16, 0.85], [32, 0.3]]
```

### Stepped (per-section values)
```yaml
density:
  type: stepped
  sections: { intro: 0.3, verse: 0.5, chorus: 0.9, outro: 0.3 }
```

### Linear (straight interpolation)
```yaml
tension:
  type: linear
  waypoints: [[0, 0.1], [32, 0.9]]
```

### Target (constant value)
```yaml
predictability:
  target: 0.65
  variance: 0.15
```

## Usage

```bash
yao compose my-spec.yaml --trajectory trajectory.yaml
```

## Values

All trajectory values are in the range **0.0 to 1.0**. The generator maps these to musical parameters (e.g., tension 0.5 → base velocity, tension 1.0 → +20% velocity).
