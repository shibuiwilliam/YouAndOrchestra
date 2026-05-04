# Design: Tension Arcs (Phase γ.1)

## Problem
Macro trajectory curves shape the piece at the section level, but local drama (2–8 bar structures) is uncontrolled. Tension builds and releases need first-class plan representation.

## Solution
TensionArc as a frozen dataclass in Layer 3.5 (MPIR), embedded in HarmonyPlan.

## Structure
- `TensionArc`: id, location (section + bar range), pattern, target_release, intensity, mechanism
- `ArcLocation`: section + bar_start + bar_end (1-indexed)
- `ArcRelease`: section + bar (where the arc resolves)
- `TensionPattern`: linear_rise, dip, plateau, spike, deceptive

## Schema
`tension_arcs.yaml` (Layer 1) defines arcs. Cross-validated against composition.yaml section names.

## Invariants
- Span must be 2–8 bars
- Intensity in [0, 1]
- Section references must exist in SongFormPlan
- Deceptive arcs may omit target_release; others should have one

## Critique Integration
- `tension_arc_unresolved`: flags non-deceptive arcs without release points
- `surprise_deficit`: uses arc count as proxy for piece variety
- `surprise_overload`: flags excessive arc coverage (>80% of bars)
