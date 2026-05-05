# Design Note 0006: Six-Phase Cognitive Protocol Enforcement

> PR-6 | Status: Implemented | Date: 2026-05-05

## Problem

The six cognitive phases were documented but not enforced in code. Phases could
be skipped silently, leading to structurally directionless compositions.

## Solution

1. Created `Phase` IntEnum (1-6) in `src/yao/conductor/protocol.py`.

2. Defined `PHASE_REQUIRED_ARTIFACTS` mapping each phase to its required outputs.

3. Added `PhaseIncompleteError` to `src/yao/errors.py` with `phase` and
   `missing_artifacts` attributes.

4. Implemented enforcement functions:
   - `check_phase_artifacts()` — verifies artifacts exist for a phase
   - `validate_phase_transition()` — ensures sequential phase progression
   - `get_previous_phase()` / `get_required_artifacts()` — query helpers

5. The `force=True` parameter on `validate_phase_transition` allows debug
   bypassing with a warning (maps to future `--force-phase` CLI flag).

## Phase Artifacts

| Phase | Required Artifacts |
|---|---|
| 1. Intent Crystallization | intent.md |
| 2. Architectural Sketch | trajectory.yaml |
| 3. Skeletal Generation | score_skeleton.json |
| 4. Critic-Composer Dialogue | critique_round_1.md, selected_skeleton.json |
| 5. Detailed Filling | full.mid, stems/ |
| 6. Listening Simulation | analysis.json, evaluation.json, critique.md |

## Files

- `src/yao/conductor/protocol.py` — Phase enum and enforcement functions
- `src/yao/errors.py` — PhaseIncompleteError
- `tests/unit/test_phase_protocol.py` — 28 tests
