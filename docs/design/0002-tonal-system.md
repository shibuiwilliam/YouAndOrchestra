# Design Note 0002 — Tonal System Abstraction

## Problem Statement

**Finding C1** (Western Tonal Music Bias): The schema treats `key: <pitch> <major|minor>`
as the canonical tonal description. The evaluator's consonance metrics assume 12-EDO
major/minor as the only valid system. This breaks blues (b3 is a feature), modal jazz,
drone/ambient (low pitch class variety is intentional), microtonal, and atonal music.

## Files to Add

- `src/yao/schema/tonal_system.py` — Pydantic TonalSystem model
- `tests/unit/test_tonal_system.py` — schema validation tests
- `tests/tonal_systems/` — genre-appropriate scoring tests

## Files to Modify

- `src/yao/schema/composition.py` — add optional `tonal_system` field, auto-promote legacy `key`
- `src/yao/ir/harmony.py` — per-system dispatch in `realize()`
- `src/yao/ir/notation.py` — extend Pitch concept for cents offset support
- `src/yao/render/midi_writer.py` — pitch-bend emission for non-zero cents
- `src/yao/verify/evaluator.py` — tonal_system-aware consonance/variety metrics
- `src/yao/generators/legacy_adapter.py` — ensure tonal_system is passed through

## Backward Compatibility

- Legacy specs with `key: "D minor"` auto-promote to `tonal_system: { kind: tonal_major_minor, key: D, mode: minor }`
- All existing tests continue to pass unchanged
- New field is Optional; None means legacy behavior

## New Tests Required

- TonalSystem schema validation (all kinds)
- Auto-promotion of legacy `key` string
- Blues spec scores higher on appropriateness than diatonic version
- Drone spec not penalized for low pitch_class_variety
- Harmony realize dispatch per system kind

## Acceptance Criteria (from IMPROVEMENT.md)

- A blues spec with prominent b3 scores higher on tonal_system_appropriateness
  than a strictly diatonic version
- A drone spec with one pitch class for 90 seconds is not flagged for low pitch_class_variety

## Risks and Rollback

- Medium risk: touches schema, IR, evaluator, and render layers
- Rollback: remove TonalSystem, revert evaluator to non-conditional
- Mitigation: TonalSystem is Optional, so existing code paths work without it
