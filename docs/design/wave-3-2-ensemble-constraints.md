# Design: Wave 3.2 — EnsembleConstraint

> **Date**: 2026-05-03
> **Status**: Implementation
> **Sprint**: Wave 3.2

---

## 1. Problem

The existing constraint system (`Constraint` in constraints.py) operates on single
instruments or global scope. It cannot express inter-part relationships like:
- "Bass and melody must be consonant on downbeats"
- "No two instruments should overlap in the same 1-octave band"
- "Voice leading between parts must avoid parallel fifths"

The Orchestrator Subagent currently just maps spec instruments to sections
without considering frequency separation or inter-part voice leading.

## 2. EnsembleConstraint Types

| Rule ID | Description | Severity |
|---|---|---|
| `ensemble.register_separation` | Adjacent-role instruments must be ≥1 octave apart | warning |
| `ensemble.downbeat_consonance` | Bass + melody consonant (3rd/5th/8ve) on beats 1,3 | error |
| `ensemble.no_parallel_octaves` | No two parts moving in parallel octaves | warning |
| `ensemble.no_frequency_collision` | Active parts must not share >60% of pitch range | warning |
| `ensemble.bass_below_melody` | Bass register must be below melody register | error |

## 3. Implementation Plan

1. Add `EnsembleConstraint` Pydantic model to `constraints.py`
2. Add `EnsembleConstraintChecker` to `constraint_checker.py`
3. Enhance `OrchestratorSubagent` to assign registers with separation
4. Add `EnsembleViolationDetector` critique rule
5. Tests for detection on multi-instrument scores
