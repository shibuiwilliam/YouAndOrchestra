# Design: Tension Arcs

## Problem

Macro trajectory curves shape the piece at the section level, but local drama (2–8 bar structures) is uncontrolled. Tension builds and releases need first-class plan representation.

## Solution

TensionArc as a frozen dataclass, embedded in HarmonyPlan.

## Structure

- `TensionArc`: id, location (section + bar range), pattern, target_release, intensity, mechanism
- `ArcLocation`: section + bar_start + bar_end (1-indexed)
- `ArcRelease`: section + bar (where the arc resolves)
- `TensionPattern`: linear_rise, dip, plateau, spike, deceptive

## Schema

`tension_arcs.yaml` defines arcs. Cross-validated against composition.yaml section names at load time.

## Invariants

- Span must be 2–8 bars
- Intensity in [0, 1]
- Section references must exist in SongFormPlan
- Deceptive arcs may omit target_release; others must have one

## Critique Integration

- `tension_arc_unresolved`: flags non-deceptive arcs without release points
- `surprise_deficit`: uses arc count as proxy for piece variety
- `surprise_overload`: flags excessive arc coverage (>80% of bars)

## Files

- `src/yao/ir/tension_arc.py` — TensionArc, ArcLocation, ArcRelease, TensionPattern
- `src/yao/schema/tension_arcs.py` — TensionArcsSpec
- `src/yao/verify/critique/tension_rules.py` — TensionArcUnresolvedDetector
