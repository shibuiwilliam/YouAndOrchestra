# Layer Architecture

YaO uses a strict layered architecture with downward-only dependencies. Each layer can only import from layers below it. This is enforced by `make arch-lint`.

**v3.0** introduces **Layer 2.5: Combination & Coupling** (`src/yao/coupling/`) between Layer 2 and Layer 3. This layer houses 13 modules that transform, couple, blend, and optimize already-generated material.

---

## Layer Diagram

```
Layer 0    constants/         → (nothing)
Layer 1    schema/            → constants
Layer 1    ir/                → constants
Layer 1    reflect/           → constants (cross-cutting)
Layer 2    generators/        → constants, schema, ir, reflect
Layer 2.5  coupling/          → constants, schema, ir, generators (NEW v3.0)
Layer 3.5  sound_design/     → constants, schema, ir
Layer 4    perception/        → constants, schema, ir, generators
Layer 5    render/            → constants, schema, ir, generators, sound_design, perception
Layer 6    verify/            → constants, schema, ir, generators, sound_design, perception, render
           conductor/         → all of the above
```

---

## Layer Details

### Layer 0: Constants

Hardcoded musical values. No dependencies.

- 46 standard instruments with MIDI ranges and GM program numbers
- 8 custom cultural instruments (shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney)
- 28 scale definitions (EDO, Japanese, maqam, raga, gamelan, just intonation)
- 20 song forms (AABA, verse-chorus, rondo, blues, J-pop, game BGM, ambient...)
- 14 chord types, MIDI constants, genre profiles
- 15 harmonic device YAMLs (v3.0: `constants/harmonic_devices/`)

### Layer 1: Specification + IR + Reflect

**Schema** — Pydantic models for YAML spec validation:

- CompositionSpec (v1 simple, v2 detailed 11-section, v3 composable with extends/overrides)
- TonalSystem (10 kinds), TimeSignatureSpec, TrajectorySpec
- ConstraintsSpec, IntentSpec, FeedbackSpec
- HooksSpec, GrooveSpec, ConversationSpec, TensionArcsSpec
- ReferencesSpec, ArrangementSpec, PinsSpec
- ProductionSpec, SoundDesignSpec
- UnifiedGenreProfile (14 nested sections)

**IR** — Frozen dataclasses for internal representation:

- ScoreIR (Note, Part, Section) — the core musical document
- Motif (invert, retrograde, transpose), Harmony, Voicing
- Trajectory (5-dim), TensionArc, DynamicsShape
- GrooveProfile, Hook, ConversationPlan, Vocal
- MeterSpec, RhythmSystem, Tuning
- Plan IRs: SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan, DrumPlan, ArrangementPlan, MusicalPlan

**Reflect** — Cross-cutting provenance:

- ProvenanceLog (append-only causal graph)
- RecoverableDecision (9 registered codes)
- UserStyleProfile (preference learning)

### Layer 2: Generation

Composition algorithms that produce `(ScoreIR, ProvenanceLog)`.

**Note-level generators** (8):
rule_based, stochastic, markov, twelve_tone, process_music, constraint_solver, loop_evolution, ai_seed

**Markov models** (v3.0): `markov_models/pitch/`, `markov_models/rhythm/`, `markov_models/contour/`

**Specialized generators**:
drum_patterner (15 patterns), counter_melody, melodic_strategies (8), reactive_fills, frequency_clearance, groove_applicator, conversation_director

### Layer 2.5: Combination & Coupling *(NEW v3.0)*

Modules that transform, couple, blend, or optimize already-generated material. All feature-flagged.

- `coupling/harmonic_melody.py` — `derive_constraints()` for chord-aware melody
- `coupling/voice_leading.py` — Hungarian-assignment voicing optimization
- `coupling/reharmonization.py` — 12 reharmonization operations
- `coupling/modulation.py` — 7 modulation strategies
- `coupling/genre_vector.py` — N-way genre blending
- `coupling/rhythm_markov.py` — Genre-conditioned rhythm generation
- `coupling/polyrhythm.py` — Multi-layer polyrhythmic textures
- `coupling/theme_recurrence.py` — Long-form thematic return planning
- `coupling/phrase_shape.py` — Intra-section phrase structures
- `coupling/listening_dialog.py` — Turn-based inter-instrument generation
- `coupling/idiomatic_gestures.py` — Per-instrument body-language patterns
- `coupling/harmonic_devices.py` — Genre-typical harmonic gestures

**Import rules**: may import from Layers 0, 1, 2, and other coupling modules only. Never from Layers 3+.

**Plan generators**:
form_planner, harmony_planner, motivic_planner, orchestrator

**Performance generators** (4):
articulation_realizer, dynamics_curve_renderer, microtiming_injector, cc_curve_generator

### Layer 3.5: Sound Design

Optional layer for synthesis patches and effect chains.

- Patch (5 synthesis kinds: sample_based, subtractive, fm, wavetable, physical)
- EffectChain + Effect (11 types: eq, compressor, limiter, reverb, delay, tape_saturation, bitcrusher, chorus, phaser, flanger, convolution_reverb)
- Lazy `pedalboard` import — graceful degradation if not installed

### Layer 4: Perception

Audio and symbolic analysis.

- AudioPerceptionAnalyzer (LUFS, spectral, onset density, tempo stability, 7-band energy, masking risk)
- SurpriseScorer (bigram n-gram + Krumhansl tonal hierarchy)
- ReferenceMatcher (SHA256-cached style matching, StyleVector with 6 abstract features)
- ListeningSimulator (post-render perception orchestration)
- UseCaseEvaluator (7 use cases: YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic)
- MoodProfile, PsychMapper

### Layer 5: Rendering

Output generation.

- MIDI writer (PerformanceLayer-aware) + MIDI reader (round-trip)
- Audio renderer (FluidSynth, optional)
- Stem writer (per-instrument MIDI files)
- MusicXML writer (music21)
- LilyPond writer (→ PDF)
- Strudel emitter (live-coding notation)
- Reaper RPP writer (DAW integration)
- Mix chain (per-track EQ/comp/reverb/gain/pan + master LUFS/limiter)

### Layer 6: Verification

Analysis, critique, and evaluation.

- Music lint (parallel fifths, voice leading)
- Evaluator (6-dimension + genre-driven dynamic weights)
- 35 critique rules across 8 roles (structural, harmonic, melodic, rhythmic, arrangement, emotional, memorability, genre_fitness + groove, surprise, hook, dynamics, conversation, metric_drift, tension, acoustic divergence)
- Melody-harmony alignment metric (v3.0: `verify/melody_harmony_alignment.py`)
- Voice-leading smoothness metric (v3.0: `verify/voice_leading_smoothness.py`)
- Constraint checker (range, voice, ensemble)
- Acoustic divergence rules (5: LUFS, spectral imbalance, brightness, energy trajectory, symbolic-acoustic)
- Loopability validator, singability evaluator, seamlessness evaluator
- Aesthetic evaluator, metric goal system (7 goal types)
- Score diff (modified notes tracking)

### Conductor (above all layers)

Orchestration layer.

- Generate-evaluate-adapt loop (up to 3 iterations)
- Six-phase protocol (Intent → Sketch → Skeleton → Dialogue → Filling → Simulation)
- Multi-candidate orchestrator (N parallel candidates, severity-ranked)
- Audio feedback loop (LUFS/spectral adaptations)
- Curriculum learning (failure pattern tracking)
- Subagent message protocol (SubagentMessage dataclass)
- SpecCompiler (NL → spec, 3-stage fallback: LLM → Keyword → Default)

---

## Generation Flow

```
CompositionSpec
  ↓
PlanOrchestrator (9 steps):
  1. FormPlanner        → SongFormPlan
  2. HarmonyPlanner     → HarmonyPlan (with TensionArcs)
  3. MotivicPlanner     → MotifPlan
  4. PhrasePlanner      → PhrasePlan
  5. ConversationDir.   → ConversationPlan
  6. DrumPlanner        → DrumPlan
  7. ArrangePlanner     → ArrangementPlan
  8. HookPlanner        → HookPlan
  9. Assembler          → MusicalPlan
  ↓
Critic Gate (35 rules, severity-ranked)
  ↓
NoteRealizer (rule_based_v2 or stochastic_v2)
  ↓
GrooveApplicator (20 groove profiles)
  ↓
Performance Pipeline (4 realizers)
  ↓
Renderer → MIDI / WAV / MusicXML / LilyPond / Reaper / Strudel
```

---

## Library Confinement

| Library | Allowed In | Purpose |
|---|---|---|
| `pretty_midi` | ir/, render/ | MIDI creation and editing |
| `music21` | ir/, verify/ | Music theory analysis, MusicXML |
| `librosa` | verify/ only | Audio feature analysis |
| `pyloudnorm` | verify/ only | LUFS loudness measurement |
| `pedalboard` | sound_design/, render/audio_renderer.py | VST chain hosting |
| `pydantic` | schema/ | YAML spec validation |
| `numpy/scipy` | ir/, generators/, sound_design/, perception/, render/, verify/ | Numerical computation |
| `click` | cli/ only | CLI framework |

---

## Enforcement

```bash
make arch-lint    # AST-based import checker — CI failure on violation
```
