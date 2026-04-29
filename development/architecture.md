# System Architecture

## Overview

YaO is a 7-layer music production pipeline. Each layer has clear responsibilities and strict downward-only dependency flow. Layer boundaries are enforced by `tools/architecture_lint.py` using AST analysis.

## Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 6: Verification (verify/)                             │
│   Music linting, evaluation, constraint checking, diffing   │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering (render/)                                │
│   MIDI writing, audio rendering, stems, iteration mgmt      │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Perception (perception/) [planned]                 │
│   Reference matching, aesthetic judgment substitutes         │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Generation (generators/)                           │
│   Rule-based, stochastic, generator registry                │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Foundation (schema/ + ir/ + reflect/)              │
│   Specs, IR types, provenance — shared across all layers    │
├─────────────────────────────────────────────────────────────┤
│ Layer 0: Constants (constants/)                             │
│   Instrument ranges, MIDI mappings, scales, chords          │
└─────────────────────────────────────────────────────────────┘
```

## Dependency Rules

| Source Layer | May Import From |
|-------------|----------------|
| constants (0) | nothing |
| schema (1) | constants |
| ir (1) | constants |
| reflect (1) | constants |
| generators (2) | constants, schema, ir, reflect |
| perception (4) | constants, schema, ir, generators |
| render (5) | constants, schema, ir, generators, perception |
| verify (6) | constants, schema, ir, generators, perception, render |
| cli (consumer) | everything in yao |

## Design Decision: IR and Provenance at Layer 1

See [ADR-0001](../docs/design/0001-layer-architecture.md). IR types (`Note`, `ScoreIR`) and provenance types (`ProvenanceRecord`, `ProvenanceLog`) are foundational shared types, not upper-layer components. Every layer produces and consumes them.

## Library Confinement

| Library | Allowed In | Prohibited Elsewhere |
|---------|-----------|---------------------|
| `pretty_midi` | ir/, render/ | Generators, verify, schema |
| `music21` | ir/, verify/ | Generators, render, schema |
| `librosa` | verify/ | All other layers |
| `pyloudnorm` | verify/ | All other layers |

## Data Flow

```
composition.yaml  ──→  CompositionSpec  ──→  GeneratorBase.generate()
trajectory.yaml   ──→  TrajectorySpec   ──┘        │
                                                    ▼
                                          (ScoreIR, ProvenanceLog)
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                              write_midi()    lint_score()    evaluate_score()
                              write_stems()   analyze_score() check_constraints()
                                    │         diff_scores()
                                    ▼
                              full.mid, stems/*.mid
                              analysis.json, provenance.json
```

## Module Map

### Layer 0: Constants
- `constants/midi.py` — PPQ, default velocity/tempo, GM program numbers
- `constants/instruments.py` — `InstrumentRange` for 46 instruments
- `constants/music.py` — 13 scales, 14 chord types, dynamics→velocity map

### Layer 1: Schema
- `schema/composition.py` — `CompositionSpec`, `SectionSpec`, `InstrumentSpec`, `GenerationConfig`
- `schema/trajectory.py` — `TrajectorySpec`, `TrajectoryDimension`, `Waypoint`
- `schema/constraints.py` — `Constraint`, `ConstraintsSpec` (must/must_not/prefer/avoid)
- `schema/references.py` — `ReferencesSpec` (aesthetic reference library)
- `schema/negative_space.py` — `NegativeSpaceSpec` (intentional silence)
- `schema/production.py` — `ProductionSpec` (LUFS, stereo, reverb)
- `schema/loader.py` — YAML loading and project spec assembly

### Layer 1: IR
- `ir/note.py` — `Note` frozen dataclass (pitch, beat, duration, velocity, instrument)
- `ir/score_ir.py` — `Part`, `Section`, `ScoreIR` (the central data structure)
- `ir/timing.py` — All beat↔tick↔second conversions
- `ir/notation.py` — Note name↔MIDI number, key parsing, scale generation
- `ir/harmony.py` — `ChordFunction`, `ChordProgression`, `realize()`, diatonic quality
- `ir/motif.py` — `Motif`, transpose, invert, retrograde, augment, diminish
- `ir/voicing.py` — `Voicing`, parallel fifths/octaves detection, voice distance

### Layer 1: Reflect
- `reflect/provenance.py` — `ProvenanceRecord`, `ProvenanceLog` (append-only, queryable)

### Layer 2: Generators
- `generators/base.py` — `GeneratorBase` ABC: `generate() → (ScoreIR, ProvenanceLog)`
- `generators/registry.py` — `@register_generator()`, `get_generator()`, `available_generators()`
- `generators/rule_based.py` — Deterministic scale-based generation
- `generators/stochastic.py` — Seeded randomness with temperature control, contour shaping, section-aware chord progressions, walking bass

### Layer 5: Rendering
- `render/midi_writer.py` — `ScoreIR` → PrettyMIDI → .mid
- `render/audio_renderer.py` — MIDI → WAV via fluidsynth (best-effort)
- `render/stem_writer.py` — Per-instrument MIDI stem files
- `render/iteration.py` — Versioned output directories (v001, v002, ...)

### Layer 6: Verification
- `verify/music_lint.py` — Range, overlap, velocity, duration, tempo checks
- `verify/analyzer.py` — `AnalysisReport` with note stats, lint results
- `verify/evaluator.py` — `EvaluationReport` across structure, melody, harmony
- `verify/diff.py` — `ScoreDiff` with added, removed, and modified notes
- `verify/constraint_checker.py` — Evaluate constraints (density, pitch limits, parallel fifths, rest ratio)

### CLI
- `cli/main.py` — Click commands: compose, render, validate, evaluate, diff, explain, new-project
