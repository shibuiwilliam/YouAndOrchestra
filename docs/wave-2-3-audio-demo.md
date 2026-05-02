# Wave 2.3 Audio Loop Demo

> **Date**: 2026-05-03
> **Purpose**: Demonstrate the Audio Loop's adaptation logic
> **Note**: These scenarios use synthetic PerceptualReports (no actual audio rendering)
> since SoundFont files are not present in the repo.

## Architecture

```
[MIDI loop done] → ConductorResult
    ↓ (enable_audio_loop = True)
[render MIDI → WAV]
    ↓
[PerceptualReport] ← AudioPerceptionAnalyzer
    ↓
[suggest_audio_adaptations()] ← AudioThresholds
    ↓ adaptations?
    ├── Yes → apply → re-render (max 2x)
    └── No → converge, done
```

## Scenarios

### Scenario 1: LUFS Too Quiet

| | Value |
|---|---|
| Input LUFS | -22.0 |
| Target | -16.0 ± 2.0 |
| Deviation | -4.0 (below tolerance) |
| **Adaptation** | `dynamics_adjust`: scale velocities ×1.30 |

### Scenario 2: High Masking Risk

| | Value |
|---|---|
| Masking Risk | 0.50 |
| Threshold | 0.30 |
| **Adaptation** | `register_adjust`: separate colliding parts by 1 octave |

### Scenario 3: Both Issues

| | Value |
|---|---|
| LUFS | -24.0 (too quiet) |
| Masking | 0.60 (too high) |
| **Adaptations** | 1. `dynamics_adjust` (×1.30), 2. `register_adjust` (separate) |

### Scenario 4: Audio Within Tolerance

| | Value |
|---|---|
| LUFS | -15.5 |
| Masking | 0.15 |
| **Result** | 0 adaptations → loop converges immediately |

### Scenario 5: Velocity Scaling Effect

```
Before: velocities = [70, 80, 90, 100]
After:  velocities = [91, 104, 117, 127]  (scale ×1.30, capped at 127)
```

## Safety Mechanisms

| Mechanism | Design |
|---|---|
| Default OFF | `ConductorConfig(enable_audio_loop=False)` |
| Max iterations | `max_audio_iterations=2` (prevents infinite loop) |
| Velocity cap | Clipped to [1, 127] (MIDI range) |
| Pitch cap | Clipped to [0, 127] after register shift |
| SoundFont missing | `RenderError` raised (no silent fallback) |
| Provenance | Each iteration logs LUFS, masking, and adaptations applied |

## Adaptation Types

| Type | Trigger | Effect | Reversible |
|---|---|---|---|
| `dynamics_adjust` | LUFS outside target ± tolerance | Scale all velocities by 0.7–1.3 | Yes (inverse scale) |
| `register_adjust` | masking_risk > threshold | Shift second-highest part down 1 octave | Yes (shift back) |
| `eq_adjust` | spectral imbalance | Modify ProductionManifest EQ | Stretch goal |

## Conclusion

The Audio Loop enables the Conductor to "listen" to rendered audio and automatically correct:
- **Loudness issues** (LUFS normalization via velocity scaling)
- **Frequency masking** (register separation)

This completes the "Listener Panel" metaphor from PROJECT.md §1 — the Conductor now has both structural (MIDI) and acoustic (audio) feedback loops.
