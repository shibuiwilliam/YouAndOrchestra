# System Architecture

## Overview

YaO is a layered music production pipeline. Each layer has clear responsibilities and strict downward-only dependency flow. Layer boundaries are enforced by `tools/architecture_lint.py` using AST analysis.

## Layer Model

```
+--------------------------------------------------------------+
| Conductor (conductor/)                                       |
|   Feedback loop: generate -> evaluate -> adapt -> regenerate |
+--------------------------------------------------------------+
| Layer 6: Verification (verify/)                              |
|   Music linting, evaluation, constraint checking, diffing,   |
|   MetricGoal, RecoverableDecision tracking                   |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI writing/reading, audio rendering, stems, iterations   |
+--------------------------------------------------------------+
| Layer 4: Perception (perception/) [planned]                  |
|   Reference matching, aesthetic judgment substitutes         |
+--------------------------------------------------------------+
| Layer 3a: Composition Plan IR (ir/plan/) [v2.0]                 |
|   SongFormPlan, HarmonyPlan, MusicalPlan                     |
|   Structural/harmonic decisions BEFORE notes are placed      |
+--------------------------------------------------------------+
| Layer 3b: Score IR (ir/)                                      |
|   Note, Part, Section, ScoreIR, harmony, motif, voicing      |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Plan generators + note realizers, pluggable registry       |
+--------------------------------------------------------------+
| Layer 1: Foundation (schema/ + reflect/)                     |
|   Specs (v1 + v2), provenance, recoverable decisions         |
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
| ir (3a, 3b) | constants |
| reflect (1) | constants |
| generators (2) | constants, schema, ir, reflect |
| perception (4) | constants, schema, ir, generators |
| render (5) | constants, schema, ir, generators, perception |
| verify (6) | constants, schema, ir, generators, perception, render |
| conductor | all layers |
| cli (consumer) | everything in yao |

## Design Decision: IR and Provenance at Foundation

See [ADR-0001](../docs/design/0001-layer-architecture.md). IR types (`Note`, `ScoreIR`) and provenance types (`ProvenanceRecord`, `ProvenanceLog`) are foundational shared types, not upper-layer components. Every layer produces and consumes them.

## Library Confinement

| Library | Allowed In | Prohibited Elsewhere |
|---------|-----------|---------------------|
| `pretty_midi` | ir/, render/ | Generators, verify, schema |
| `music21` | ir/, verify/ | Generators, render, schema |
| `librosa` | verify/, perception/ | All other layers |
| `pyloudnorm` | verify/, perception/ | All other layers |
| `pedalboard` | render/production/ | All other layers |

## Data Flow

### v2.0 Pipeline (Plan-First)

The v2.0 architecture introduces a two-stage generation process. Structural and harmonic decisions are made in the **Plan** stage (Layer 3a), before any concrete notes are placed.

```
composition.yaml  -->  CompositionSpec  -->  Conductor
trajectory.yaml   -->  TrajectorySpec   --+     |
                                               v
                                     PlanGenerator.plan()
                                               |
                                               v
                                     MusicalPlan (CPIR)
                                        - SongFormPlan
                                        - HarmonyPlan
                                        - (MotifPlan, DrumPlan — planned)
                                               |
                                     [Critic Gate — validates plan]
                                               |
                                               v
                                     NoteRealizer.realize()
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

### Legacy Pipeline (Phase α transitional)

During Phase α, the legacy generators (`rule_based`, `stochastic`) still accept specs directly but are being repositioned as Note Realizers. They may internally construct a minimal CPIR and pass through it. After Phase α, the direct spec-to-ScoreIR path will be removed.

```
CompositionSpec  -->  GeneratorBase.generate()  -->  (ScoreIR, ProvenanceLog)
```

## Module Map

### Layer 0: Constants
- `constants/midi.py` -- PPQ (220), default velocity (80), default BPM (120), GM program numbers (46 mappings)
- `constants/instruments.py` -- `InstrumentRange` for 40 instruments across 9 families
- `constants/music.py` -- 14 scales, 14 chord types, 12 section types, dynamics-to-velocity map

### Layer 1: Schema
- `schema/composition.py` -- v1: `CompositionSpec`, `SectionSpec`, `InstrumentSpec`, `GenerationConfig`
- `schema/composition_v2.py` -- v2: `CompositionSpecV2` with 11 sections (identity, global, emotion, form, melody, harmony, rhythm, drums, arrangement, production, constraints)
- `schema/trajectory.py` -- `TrajectorySpec`, `TrajectoryDimension`, `Waypoint`
- `schema/intent.py` -- `IntentSpec` (emotional/functional goals)
- `schema/constraints.py` -- `Constraint`, `ConstraintsSpec` (must/must_not/prefer/avoid)
- `schema/references.py` -- `ReferencesSpec` (aesthetic reference library)
- `schema/negative_space.py` -- `NegativeSpaceSpec` (intentional silence)
- `schema/production.py` -- `ProductionSpec` (LUFS, stereo, reverb)
- `schema/project.py` -- `ProjectSpec` (loader for project directories)
- `schema/loader.py` -- YAML loading, auto-detect v1/v2, project spec assembly

### Layer 1: Reflect
- `reflect/provenance.py` -- `ProvenanceRecord`, `ProvenanceLog` (append-only, queryable)
- `reflect/recoverable.py` -- `RecoverableDecision` for traceable fallback logging
- `reflect/recoverable_codes.py` -- Error codes for recovery classification

### Layer 3: Score IR
- `ir/note.py` -- `Note` frozen dataclass (pitch, beat, duration, velocity, instrument)
- `ir/score_ir.py` -- `Part`, `Section`, `ScoreIR` (the central data structure)
- `ir/timing.py` -- All beat<->tick<->second conversions
- `ir/notation.py` -- Note name<->MIDI number, key parsing, scale generation
- `ir/harmony.py` -- `ChordFunction`, `ChordProgression`, `realize()`, diatonic quality
- `ir/motif.py` -- `Motif`, transpose, invert, retrograde, augment, diminish
- `ir/voicing.py` -- `Voicing`, parallel fifths/octaves detection, voice distance
- `ir/trajectory.py` -- `MultiDimensionalTrajectory` with density, tension, energy curves

### Layer 3a: Composition Plan IR (CPIR, v2.0)
- `ir/plan/base.py` -- `PlanNode` abstract base class
- `ir/plan/song_form.py` -- `SongFormPlan` (sections, structure)
- `ir/plan/harmony.py` -- `HarmonyPlan` (chord events, progressions)
- `ir/plan/motif.py` -- `MotifPlan` (planned, Phase beta)
- `ir/plan/phrase.py` -- `PhrasePlan` (planned, Phase beta)
- `ir/plan/drums.py` -- `DrumPlan` (planned, Phase beta)
- `ir/plan/arrangement.py` -- `ArrangementPlan` (planned, Phase beta)
- `ir/plan/musical_plan.py` -- `MusicalPlan` (integrated container, JSON serialization)

### Layer 2: Generators
- `generators/base.py` -- `GeneratorBase` ABC: `generate() -> (ScoreIR, ProvenanceLog)`
- `generators/registry.py` -- `@register_generator()`, `get_generator()`, `available_generators()`
- `generators/rule_based.py` -- Deterministic scale-based generation
- `generators/stochastic.py` -- Seeded randomness with StochasticConfig (15 tunable params), 4 contour algorithms (arch/ascending/descending/wave), 5 chord voicing types, section-aware progressions, walking bass, 12 rhythm patterns
- `generators/legacy_adapter.py` -- Backward compatibility adapter for v1 generators
- `generators/plan/base.py` -- `PlanGeneratorBase` ABC (v2.0)
- `generators/plan/form_planner.py` -- Generates `SongFormPlan` from `CompositionSpec`
- `generators/plan/harmony_planner.py` -- Generates `HarmonyPlan` from spec + form
- `generators/plan/orchestrator.py` -- Generates arrangement/drums (Phase beta)
- `generators/note/base.py` -- `NoteRealizerBase` ABC (v2.0)
- `generators/note/rule_based.py` -- Rule-based note realizer (v2.0)
- `generators/note/stochastic.py` -- Stochastic note realizer (v2.0)

### Layer 5: Rendering
- `render/midi_writer.py` -- `ScoreIR` -> PrettyMIDI -> .mid
- `render/midi_reader.py` -- .mid -> ScoreIR (inverse of writer, for analysis and section regeneration)
- `render/audio_renderer.py` -- MIDI -> WAV via fluidsynth (best-effort)
- `render/stem_writer.py` -- Per-instrument MIDI stem files
- `render/iteration.py` -- Versioned output directories (v001, v002, ...)

### Layer 6: Verification
- `verify/music_lint.py` -- Range, overlap, velocity, duration, tempo checks (7 rules)
- `verify/analyzer.py` -- `AnalysisReport` with note stats, lint results
- `verify/evaluator.py` -- `EvaluationReport` across 3 dimensions (structure, melody, harmony) with 10 metrics + quality_score (1.0-10.0)
- `verify/metric_goal.py` -- `MetricGoal` with 7 typed evaluation modes (AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN, MATCH_CURVE, RELATIVE_ORDER, DIVERSITY)
- `verify/diff.py` -- `ScoreDiff` with added, removed, and modified notes
- `verify/constraint_checker.py` -- Evaluate constraints (density, pitch limits, parallel fifths, rest ratio)
- `verify/critique/` -- Rule-based adversarial critique engine:
  - `base.py` -- `CritiqueRule` ABC with `detect()` method
  - `types.py` -- `Finding` dataclass (rule_id, severity, role, issue, evidence, location, recommendation)
  - `registry.py` -- `CritiqueRuleRegistry` for rule discovery
  - `structural.py` -- 3 rules: climax absence, section monotony, form imbalance
  - `melodic.py` -- 3 rules: cliche motif, contour monotony, phrase closure weakness
  - `harmonic.py` -- 3 rules: cliche progression, voice crossing, cadence weakness
  - `rhythmic.py` -- 1 rule: rhythmic monotony
  - `emotional.py` -- 2 rules: intent divergence, trajectory violation

### Conductor
- `conductor/conductor.py` -- `Conductor` with `compose_from_description()`, `compose_from_spec()`, `regenerate_section()`, mood-to-key mapping (22 moods), instrument keyword mapping (11 groups)
- `conductor/feedback.py` -- `suggest_adaptations()`, `apply_adaptations()`, maps 8 failing metrics to spec changes
- `conductor/result.py` -- `ConductorResult` with score, spec, paths, analysis, evaluation, iteration history

### CLI
- `cli/main.py` -- Click commands: conduct, compose, regenerate-section, render, validate, evaluate, diff, explain, new-project
