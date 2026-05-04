# Design: Ensemble Groove (Phase γ.4)

## Problem
v1.0 treats rhythm per-instrument with a single swing parameter. Groove — the ensemble-wide microtiming and velocity feel — is missing.

## Solution
GrooveProfile as a frozen dataclass in Layer 3.5, applied to all instruments via GrooveApplicator in Layer 2.

## GrooveProfile
- `microtiming`: dict[int, float] — 16th-note position (0–15) → ms offset
- `velocity_pattern`: dict[int, float] — 16th position → velocity multiplier
- `ghost_probability`: float — [0, 1]
- `swing_ratio`: float — 0.5 = straight, 0.667 = triplet swing
- `timing_jitter_sigma`: float — ms σ for humanization
- `apply_to_all_instruments`: bool — False restricts groove to drums only

## Pipeline Position
Step 6 (Note Realizer) → DynamicsShape → **GrooveApplicator** → Humanize → MIDI Write

## Library
12 genre profiles in `grooves/*.yaml`. Loaded via `load_groove(name)`.

## Critique Rules
- `groove_inconsistency`: groove-dependent genre with no groove
- `microtiming_flatness`: all hits at zero microtiming in long pieces
- `ensemble_groove_conflict`: swing mismatch with genre expectations
