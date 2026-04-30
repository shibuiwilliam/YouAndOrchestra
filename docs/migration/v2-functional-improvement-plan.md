# Functional Improvement Plan

> Date: 2026-04-30
> Focus: Close vertical alignment gaps — make the plan layer actually affect output

## P1: Harmony planner tension-responsive chord selection
- **Gap**: Chord selection cycles through palette by modulo, ignoring tension
- **Fix**: At high tension (>0.6), prefer dominant/secondary-dominant chords from palette;
  at low tension (<0.4), prefer tonic/subdominant. Mid-range uses normal cycling.
- **Impact**: Plans become musically meaningful — not just stored data
- **Risk**: Low — deterministic change, golden tests will need regeneration

## P2: Conductor v2 pipeline integration
- **Gap**: Conductor uses legacy get_generator() path, never builds MusicalPlan
- **Fix**: Add compose_from_spec_v2() that uses PlanOrchestrator + NoteRealizer.
  Keep existing compose_from_spec() as-is for v1 backward compat.
- **Impact**: CLI `yao conduct` can use the v2 pipeline when given v2 specs
- **Risk**: Medium — affects user-facing CLI path, needs careful testing

## P3: Quality score in conductor feedback
- **Gap**: quality_score exists but conductor ignores it
- **Fix**: Include quality_score in ConductorResult output and log
- **Impact**: Users see a meaningful score, not just pass_rate
