# System Architecture

## Overview

YaO is a layered music production pipeline with 8 layers (0 through 7) plus an intermediate Layer 4.5. Each layer has clear responsibilities and strict downward-only dependency flow. Layer boundaries are enforced by `tools/architecture_lint.py` using AST analysis.

## Layer Model

```
+--------------------------------------------------------------+
| Conductor (conductor/)                                       |
|   Feedback loop: generate → evaluate → adapt → regenerate    |
+--------------------------------------------------------------+
| Layer 7: Reflection & Learning (reflect/, agents/)           |
|   Style profiles, subjective ratings, agent backends         |
+--------------------------------------------------------------+
| Layer 6: Verification & Critique (verify/)                   |
|   Evaluation (6 dims), aesthetic metrics, 20 critique rules, |
|   ensemble constraints, constraint checker, lint, diff       |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel        |
+--------------------------------------------------------------+
| Layer 4.5: Performance Expression (generators/performance/)  |
|   Articulation, dynamics curves, microtiming, CC curves      |
+--------------------------------------------------------------+
| Layer 4: Perception (perception/)                            |
|   Audio features, StyleVector (10 fields), use-case eval,    |
|   reference matching                                         |
+--------------------------------------------------------------+
| Layer 3.5: Musical Plan IR (ir/plan/)                        |
|   SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan,          |
|   ArrangementPlan, DrumPattern, MusicalPlan                  |
+--------------------------------------------------------------+
| Layer 3: Score IR (ir/)                                      |
|   Note, Part, Section, ScoreIR, harmony, motif, voicing      |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Plan generators + V2 note realizers (direct plan consumption)|
+--------------------------------------------------------------+
| Layer 1: Specification (schema/, sketch/)                    |
|   Specs (v1+v2), NL compiler (EN+JP), dialogue state         |
+--------------------------------------------------------------+
| Layer 0: Constants (constants/)                              |
|   38 instruments, 14 scales, 17 tuning systems, MIDI maps    |
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
| conductor | all layers |
| cli | everything in yao |

## V2 Pipeline (Current Default)

```
User Input (NL or YAML)
    │
    ▼
SpecCompiler (3-stage: LLM → Keyword → Default)
    │
    ▼
PlanOrchestrator (7 steps)
    │
    ├── Step 1: FormPlanner      → SongFormPlan
    ├── Step 2: HarmonyPlanner   → HarmonyPlan
    ├── Step 3: Composer         → MotifPlan + PhrasePlan
    ├── Step 4: DrumPatterner    → DrumPattern
    └── Step 5: Orchestrator     → ArrangementPlan (with register separation)
    │
    ▼
═══ MusicalPlan Complete ═══
    │
    ▼
Critic Gate (MPIR-level: 20 rules + ensemble constraints)
    │
    ▼
NoteRealizer V2 (100% plan consumption — no legacy adapter)
    │
    ▼
Performance Pipeline (articulation, dynamics, microtiming, CC)
    │
    ▼
Renderer (MIDI / WAV / MusicXML / LilyPond / Reaper / Strudel)
    │
    ▼
Evaluator (6 dimensions: structure, melody, harmony, aesthetic, arrangement, acoustics)
    │
    ▼
Conductor Feedback Loop (up to 3 iterations)
```

## Key Types

| Type | Location | Purpose |
|---|---|---|
| `Note` | ir/note.py | Atomic musical unit (pitch, beat, duration, velocity) |
| `ScoreIR` | ir/score_ir.py | Complete composition (sections → parts → notes) |
| `MusicalPlan` | ir/plan/musical_plan.py | Pre-realization plan (the "why") |
| `StyleVector` | perception/style_vector.py | 10-field copyright-safe style fingerprint |
| `Finding` | verify/critique/types.py | Structured critique output |
| `EnsembleConstraint` | schema/constraints.py | Inter-part constraint |
| `AestheticReport` | verify/aesthetic.py | 4 metric scores (surprise/memorability/contrast/pacing) |
| `ProvenanceLog` | reflect/provenance.py | Append-only decision record |
| `AgentOutput` | subagents/base.py | Universal subagent output |
| `SketchState` | sketch/dialogue_state.py | Multi-turn dialogue persistence |

## Library Confinement

| Library | Allowed In | Prohibited Elsewhere |
|---|---|---|
| `pretty_midi` | ir/, render/ | generators, verify, schema |
| `music21` | ir/, render/ | generators, schema |
| `librosa` | perception/ | all other layers |
| `pyloudnorm` | perception/, mix/ | all other layers |
| `pedalboard` | mix/ | all other layers |
| `anthropic` | agents/anthropic_api_backend.py | everywhere else |
| `sounddevice` | improvise/, cli (preview/watch) | all other layers |
| `torch` | generators/neural/ | all other layers |

## Honesty Enforcement

5 CI tools verify implementation integrity:

| Tool | Checks |
|---|---|
| `honesty-check` | No ✅ features that are actually stubs |
| `backend-honesty` | Stub backends declare `is_stub=True` |
| `plan-consumption` | V2 realizers consume 80%+ of plan fields |
| `skill-grounding` | Genre skills referenced from src/ |
| `critic-coverage` | All severity levels have effective rules |
