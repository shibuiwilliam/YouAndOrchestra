# Design: Hook IR + Phrase-Level Dynamics

## Problem

Compositions lack memorable centerpieces. Even surprising music feels formless without hooks and dynamics shaping.

## Solution

### Hook IR

- `Hook`: frozen dataclass with deployment strategy, appearances list, distinctive_strength [0,1]
- `DeploymentStrategy`: rare / frequent / withhold_then_release / ascending_repetition
- `HookPlan`: embedded in MusicalPlan, references MotifSeed by id
- `BarPosition`: section + bar for precise hook placement

### DynamicsShape

Per-section velocity curve for phrase-level dynamics:

| Shape | Description |
|-------|-------------|
| `crescendo` | Gradual increase |
| `decrescendo` | Gradual decrease |
| `arch` | Rise to peak then fall |
| `hairpin` | Quick swell and release |
| `steady` | Constant level |

`velocity_multiplier(position)` returns the curve value at any point. `BarAccent` provides beat-level emphasis.

## Critique Rules

- `hook_overuse`: hook appears too frequently (>60% of sections)
- `hook_underuse`: hook appears fewer than 3 times
- `hook_misplacement`: hook in intro without withhold_then_release strategy
- `flat_phrase_dynamics`: sections ≥3 bars without dynamics_shape or accents

## Files

- `src/yao/ir/hook.py` — Hook, DeploymentStrategy, HookPlan, BarPosition
- `src/yao/ir/dynamics_shape.py` — DynamicsShape, DynamicsShapeType, BarAccent
- `src/yao/schema/hooks.py` — HooksSpec
- `src/yao/verify/critique/hook_rules.py` — 3 hook rules
- `src/yao/verify/critique/dynamics_rules.py` — flat_phrase_dynamics rule
