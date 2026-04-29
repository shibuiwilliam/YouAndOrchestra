# System Architecture

## Overview

YaO is a 7-layer music production pipeline. Each layer has clear responsibilities and strict downward-only dependency flow. Layer boundaries are enforced by `tools/architecture_lint.py` using AST analysis.

## Layer Model

```
+-------------------------------------------------------------+
| Conductor (conductor/)                                       |
|   Feedback loop: generate -> evaluate -> adapt -> regenerate |
+--------------------------------------------------------------+
| Layer 6: Verification (verify/)                              |
|   Music linting, evaluation, constraint checking, diffing    |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI writing/reading, audio rendering, stems, iterations   |
+--------------------------------------------------------------+
| Layer 4: Perception (perception/) [planned]                  |
|   Reference matching, aesthetic judgment substitutes         |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Rule-based, stochastic, generator registry                 |
+--------------------------------------------------------------+
| Layer 1: Foundation (schema/ + ir/ + reflect/)               |
|   Specs, IR types, provenance -- shared across all layers    |
+--------------------------------------------------------------+
| Layer 0: Constants (constants/)                              |
|   Instrument ranges, MIDI mappings, scales, chords           |
+--------------------------------------------------------------+
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
| conductor | all layers |
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
composition.yaml  -->  CompositionSpec  -->  Conductor
trajectory.yaml   -->  TrajectorySpec   --+     |
                                               v
                                     GeneratorBase.generate()
                                               |
                                               v
                                     (ScoreIR, ProvenanceLog)
                                               |
                         +---------------------+---------------------+
                         v                     v                     v
                   write_midi()          lint_score()          evaluate_score()
                   write_stems()         analyze_score()       check_constraints()
                         |               diff_scores()
                         v                     |
                   full.mid                    v
                   stems/*.mid           EvaluationReport
                                               |
                                    [if failing metrics]
                                               v
                                     suggest_adaptations()
                                               |
                                               v
                                     apply_adaptations() -> modified spec
                                               |
                                               v
                                     regenerate (loop up to max_iterations)
```

## Module Map

### Layer 0: Constants
- `constants/midi.py` -- PPQ (220), default velocity (80), default BPM (120), GM program numbers (46 mappings)
- `constants/instruments.py` -- `InstrumentRange` for 38 instruments across 9 families
- `constants/music.py` -- 14 scales, 14 chord types, 12 section types, dynamics-to-velocity map

### Layer 1: Schema
- `schema/composition.py` -- `CompositionSpec`, `SectionSpec`, `InstrumentSpec`, `GenerationConfig`
- `schema/trajectory.py` -- `TrajectorySpec`, `TrajectoryDimension`, `Waypoint`
- `schema/constraints.py` -- `Constraint`, `ConstraintsSpec` (must/must_not/prefer/avoid)
- `schema/references.py` -- `ReferencesSpec` (aesthetic reference library)
- `schema/negative_space.py` -- `NegativeSpaceSpec` (intentional silence)
- `schema/production.py` -- `ProductionSpec` (LUFS, stereo, reverb)
- `schema/loader.py` -- YAML loading and project spec assembly

### Layer 1: IR
- `ir/note.py` -- `Note` frozen dataclass (pitch, beat, duration, velocity, instrument)
- `ir/score_ir.py` -- `Part`, `Section`, `ScoreIR` (the central data structure)
- `ir/timing.py` -- All beat<->tick<->second conversions
- `ir/notation.py` -- Note name<->MIDI number, key parsing, scale generation
- `ir/harmony.py` -- `ChordFunction`, `ChordProgression`, `realize()`, diatonic quality
- `ir/motif.py` -- `Motif`, transpose, invert, retrograde, augment, diminish
- `ir/voicing.py` -- `Voicing`, parallel fifths/octaves detection, voice distance

### Layer 1: Reflect
- `reflect/provenance.py` -- `ProvenanceRecord`, `ProvenanceLog` (append-only, queryable)

### Layer 2: Generators
- `generators/base.py` -- `GeneratorBase` ABC: `generate() -> (ScoreIR, ProvenanceLog)`
- `generators/registry.py` -- `@register_generator()`, `get_generator()`, `available_generators()`
- `generators/rule_based.py` -- Deterministic scale-based generation
- `generators/stochastic.py` -- Seeded randomness with temperature control, contour shaping, section-aware chord progressions, walking bass, 12 rhythm patterns

### Layer 5: Rendering
- `render/midi_writer.py` -- `ScoreIR` -> PrettyMIDI -> .mid
- `render/midi_reader.py` -- .mid -> ScoreIR (inverse of writer, for analysis and section regeneration)
- `render/audio_renderer.py` -- MIDI -> WAV via fluidsynth (best-effort)
- `render/stem_writer.py` -- Per-instrument MIDI stem files
- `render/iteration.py` -- Versioned output directories (v001, v002, ...)

### Layer 6: Verification
- `verify/music_lint.py` -- Range, overlap, velocity, duration, tempo checks (7 rules)
- `verify/analyzer.py` -- `AnalysisReport` with note stats, lint results
- `verify/evaluator.py` -- `EvaluationReport` across 5 dimensions (structure, melody, harmony, arrangement, acoustics) with 8 metrics
- `verify/diff.py` -- `ScoreDiff` with added, removed, and modified notes
- `verify/constraint_checker.py` -- Evaluate constraints (density, pitch limits, parallel fifths, rest ratio)

### Conductor
- `conductor/conductor.py` -- `Conductor` with `compose_from_description()`, `compose_from_spec()`, `regenerate_section()`, mood-to-key mapping (22 moods), instrument keyword mapping (11 groups)
- `conductor/feedback.py` -- `suggest_adaptations()`, `apply_adaptations()`, maps 8 failing metrics to spec changes
- `conductor/result.py` -- `ConductorResult` with score, spec, paths, analysis, evaluation, iteration history

### CLI
- `cli/main.py` -- Click commands: conduct, compose, regenerate-section, render, validate, evaluate, diff, explain, new-project
