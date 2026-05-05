# Design: Ensemble Groove

## Problem

Per-instrument rhythm with a single swing parameter is not groove. Groove is the ensemble-wide microtiming and velocity feel that makes music breathe.

## Solution

GrooveProfile as a frozen dataclass applied to all instruments via GrooveApplicator.

## GrooveProfile Fields

| Field | Type | Description |
|-------|------|-------------|
| `microtiming` | dict[int, float] | 16th-note position (0–15) → ms offset [-50, 50] |
| `velocity_pattern` | dict[int, float] | 16th position → velocity multiplier |
| `ghost_probability` | float | [0, 1] — chance of ghost notes |
| `swing_ratio` | float | 0.5 = straight, 0.667 = triplet swing |
| `timing_jitter_sigma` | float | ms σ for humanization |
| `apply_to_all_instruments` | bool | False restricts groove to drums only |

## Pipeline Position

```
Note Realizer → DynamicsShape → GrooveApplicator → Humanize → MIDI Write
```

## Library

20 genre profiles in `grooves/*.yaml`. Loaded via `load_groove(name)`:

jazz_swing, bossa_nova, funk_16th, lofi_hiphop, edm_4onfloor, reggae_one_drop, trap_double_time, rock_backbeat, pop_straight, j_pop_tight, ambient_fluid, cinematic_legato, waltz_viennese, shuffle_blues, samba, afrobeat, new_orleans_second_line, drum_n_bass, flamenco_bulerias, bollywood_filmi

## Critique Rules

- `groove_inconsistency`: groove-dependent genre with no groove applied
- `microtiming_flatness`: all hits at zero microtiming in long pieces
- `ensemble_groove_conflict`: swing mismatch with genre expectations

## Files

- `src/yao/ir/groove.py` — GrooveProfile
- `src/yao/generators/groove_applicator.py` — apply_groove()
- `src/yao/schema/groove.py` — GrooveSpec
- `src/yao/verify/critique/groove_rules.py` — 3 critique rules
- `grooves/*.yaml` — 20 groove definitions
