# System Architecture

## Overview

YaO is a layered music production pipeline with 8 layers (0 through 7) plus intermediate layers 3.5 and 4.5. Each layer has clear responsibilities and strict downward-only dependency flow. Layer boundaries are enforced by `tools/architecture_lint.py` using AST analysis.

## Layer Model

```
+--------------------------------------------------------------+
| Conductor (conductor/)                                       |
|   Feedback loop: generate -> evaluate -> adapt -> regenerate |
+--------------------------------------------------------------+
| Layer 7: Reflection & Learning (reflect/, agents/)           |
|   Provenance (causal graph), style profiles, agent backends  |
+--------------------------------------------------------------+
| Layer 6: Verification & Critique (verify/)                   |
|   Evaluation (6 dims), aesthetic metrics, 35 critique rules, |
|   ensemble constraints, acoustic divergence, constraint check |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel        |
+--------------------------------------------------------------+
| Layer 4.5: Performance Expression (generators/performance/)  |
|   Articulation, dynamics curves, microtiming, CC curves      |
+--------------------------------------------------------------+
| Layer 4: Perception (perception/)                            |
|   Audio features (LUFS, spectral), surprise scorer,          |
|   StyleVector, use-case eval, listening simulator            |
+--------------------------------------------------------------+
| Layer 3.5: Musical Plan IR (ir/plan/)                        |
|   SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan,          |
|   ArrangementPlan, DrumPattern, HookPlan, ConversationPlan   |
+--------------------------------------------------------------+
| Layer 3: Score IR (ir/)                                      |
|   Note, Part, Section, ScoreIR, harmony, motif, voicing,     |
|   hook, dynamics_shape, groove, conversation, tension_arc,   |
|   meter, tuning, expression                                  |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Plan generators, V2 note realizers, melodic strategies,    |
|   reactive fills, frequency clearance, groove applicator     |
+--------------------------------------------------------------+
| Layer 1: Specification (schema/, sketch/)                    |
|   Specs (v1+v2+v3), NL compiler (EN+JP), hooks, groove,     |
|   conversation, tension_arcs, genre profiles, arrangement    |
+--------------------------------------------------------------+
| Layer 0: Constants (constants/)                              |
|   46 instruments, 28 scales, 20 forms, 14 chords, MIDI maps |
+--------------------------------------------------------------+
```

## Dependency Rules

| Source Layer | May Import From |
|---|---|
| constants (0) | nothing |
| schema (1) | constants |
| sketch (1.5) | constants, schema |
| ir (3, 3.5) | constants |
| reflect (7) | constants, ir |
| generators (2) | constants, schema, ir, reflect |
| perception (4) | constants, schema, ir |
| render (5) | constants, schema, ir, perception |
| verify (6) | constants, schema, ir, perception |
| agents (7) | constants, schema, ir, reflect, subagents |
| arrange | constants, schema, ir, perception, verify |
| feedback | constants, schema, ir |
| conductor | all layers |
| cli | everything in yao |

## V2 Pipeline (Current Default -- 9 Steps)

```
User Input (NL or YAML)
    |
    v
SpecCompiler (3-stage: LLM -> Keyword -> Default; EN + JP)
    |
    v
PlanOrchestrator (9 steps)
    |
    +-- Step 1:   FormPlanner       -> SongFormPlan + TensionArcs
    +-- Step 2:   HarmonyPlanner    -> HarmonyPlan
    +-- Step 3:   Composer          -> MotifPlan + PhrasePlan + HookPlan
    +-- Step 4:   DrumPatterner     -> DrumPattern + GrooveProfile
    +-- Step 5:   Orchestrator      -> ArrangementPlan
    +-- Step 5.5: ConversationDir.  -> ConversationPlan
    |
    v
=== MusicalPlan Complete ===
    |
    v
Critic Gate (MPIR-level: 35 rules + ensemble constraints)
    |
    v
NoteRealizer V2 (100% plan consumption -- no legacy adapter)
    |
    v
GrooveApplicator (ensemble-wide microtiming + velocity)
    |
    v
Performance Pipeline (articulation, dynamics, microtiming, CC)
    |
    v
Renderer (MIDI / WAV / MusicXML / LilyPond / Reaper / Strudel)
    |
    v
Listening Simulator (Step 7.5: PerceptualReport extraction)
    |
    v
Evaluator (6 dimensions: structure, melody, harmony, aesthetic, arrangement, acoustics)
    |
    v
Conductor Feedback Loop (up to 3 iterations + audio loop)
```

## Key Types

| Type | Location | Purpose |
|---|---|---|
| `Note` | ir/note.py | Atomic musical unit (pitch, beat, duration, velocity + optional articulation, tuning offset, microtiming) |
| `ScoreIR` | ir/score_ir.py | Complete composition (sections -> parts -> notes) |
| `MusicalPlan` | ir/plan/musical_plan.py | Pre-realization plan (the "why" behind every note) |
| `CompositionSpecV2` | schema/composition_v2.py | 11-section spec (identity, globals, emotion, form, melody, harmony, rhythm, drums, arrangement, production, constraints) |
| `ConversationPlan` | ir/conversation.py | Inter-instrument dialogue plan |
| `GrooveProfile` | ir/groove.py | Ensemble-wide microtiming + velocity pattern |
| `Hook` | ir/hook.py | Memorable fragment with deployment strategy |
| `DynamicsShape` | ir/dynamics_shape.py | Phrase-level velocity curve |
| `TensionArc` | ir/tension_arc.py | Short-range tension-resolution structure |
| `MeterSpec` | ir/meter.py | Time signature + beat groupings + metric accents |
| `NoteExpression` | ir/expression.py | Performance layer (legato, accent, glissando, pedal) |
| `SurpriseAnalysis` | perception/surprise.py | Per-note surprise scores |
| `PerceptualReport` | perception/audio_features.py | Acoustic analysis (LUFS, spectral, temporal) |
| `StyleVector` | perception/style_vector.py | 6-field copyright-safe style fingerprint |
| `Finding` | verify/critique/types.py | Structured critique output |
| `Pin` | feedback/pin.py | Localized user feedback |
| `SongForm` | constants/forms.py | Song form template (sections + bar counts) |
| `ProvenanceLog` | reflect/provenance.py | Append-only causal decision graph |
| `AgentOutput` | subagents/base.py | Universal subagent output |
| `GenreProfile` | schema/genre_profile.py | Genre-specific defaults (tempo, harmony, instruments, etc.) |

## Library Confinement

| Library | Allowed In | Prohibited Elsewhere |
|---|---|---|
| `pretty_midi` | ir/, render/ | generators, verify, schema |
| `music21` | ir/, render/ | generators, schema |
| `librosa` | perception/, verify/acoustic/ | all other layers |
| `pyloudnorm` | perception/, mix/ | all other layers |
| `pedalboard` | mix/ | all other layers |
| `anthropic` | agents/anthropic_api_backend.py | everywhere else |
| `sounddevice` | improvise/, cli (preview/watch) | all other layers |
| `torch` | generators/neural/ | all other layers |
| `mido` | improvise/ | all other layers |
| `fastapi` | annotate/, audition/ | all other layers |

## Honesty Enforcement

5 CI tools verify implementation integrity:

| Tool | Command | Checks |
|---|---|---|
| Honesty check | `make honesty-check` | No features marked stable that are actually stubs |
| Backend honesty | `make backend-honesty` | Stub backends declare `is_stub=True` |
| Plan consumption | `make plan-consumption` | V2 realizers consume 80%+ of plan fields |
| Skill grounding | `make skill-grounding` | Genre skills referenced from src/ |
| Critic coverage | `make critic-coverage` | All severity levels have effective rules |
