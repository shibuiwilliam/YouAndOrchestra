# PROJECT.md — You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*
>
> **Document version**: 2.0
> **Updated**: 2026-05-04
> **Status**: Forward-looking design integrating IMPROVEMENT.md remediations

---

## 0. The Essence of YaO

**You and Orchestra (YaO)** is an **agentic music production environment** built on Claude Code. Unlike conventional "AI music tools" that emit music from a single black box, YaO conducts **a division-of-labor among multiple specialized AI agents (Orchestra Members)** under the direction of a human (You = Conductor).

All YaO design subordinates to one proposition:

> **Music production is not a one-shot intuitive act, but a reproducible and improvable creative-engineering process.**

For this reason, YaO treats music **as code, specifications, tests, diffs, and provenance** before treating it as audio files. We call this the **Music-as-Code philosophy**.

YaO v2.0 extends this philosophy with a critical realization: **the implicit defaults of "melody + harmony + 4/4 + 12-tone equal temperament + uniform velocity" are not universal**. They are one tradition among many. YaO v2.0 makes these dimensions explicit, modular, and genre-aware so that the system can authentically produce music from across the world's traditions — from Balkan 7/8 dances to Arabic maqam improvisations to J Dilla-grooved lo-fi hip-hop.

---

## 1. The Metaphor: You and Orchestra

Every YaO concept maps to an orchestra metaphor. Internalizing this correspondence is the shortest path to using YaO correctly.

| YaO Component | Orchestra Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human project owner |
| **Score** | Sheet Music | YAML specs in `specs/*.yaml` |
| **Orchestra Members** | Players | Subagents (Composer, Critic, Theorist, etc.) |
| **Concertmaster** | Lead Player | Producer Subagent (overall coordinator) |
| **Rehearsal** | Practice | Generate-evaluate-adapt iteration loop |
| **Library** | Sheet Music Archive | `references/` for reference compositions |
| **Performance** | Live Show | Rendered final audio |
| **Recording** | Studio Capture | Artifacts in `outputs/` |
| **Critic / Reviewer** | Music Critic | Adversarial Critic Subagent |
| **Style Library** | Repertoire Tradition | GenreProfile YAML database |
| **Tuning Standards** | Pitch Reference | TuningSystem IR |
| **Time Discipline** | Conductor's Beat | MeterSpec + GrooveProfile IR |
| **Performance Practice** | Articulation Tradition | Articulation IR |

The Conductor (You) does not write every note. The Conductor's job is to **clarify intent, direct the players, judge during rehearsal, and ensure the quality of the performance**. YaO brings this division of labor into AI.

---

## 2. Design Principles

All YaO implementation decisions are tested against these **six immutable principles**. They are also transcribed to CLAUDE.md as agent decision criteria.

### Principle 1: The Agent is an Environment, Not a Composer

YaO aspires to be "an environment that makes human composition 10× faster," not "an AI that writes songs." Full automation is rejected; the goal is to accelerate and augment human creative judgment.

### Principle 2: Demand Explainability for Every Decision

Every generated note, chord, and arrangement decision records its rationale. This is persisted as a Provenance Graph, traceable, reviewable, and revisable.

### Principle 3: Constraints Liberate, They Do Not Constrain

Explicit specs (YAML), reference libraries, and negative space designs function as scaffolding, not cages. Unlimited freedom paralyzes; structure liberates.

### Principle 4: Time-Axis First (Generalized)

**v2.0 generalization**: Music is first designed as **time-axis trajectories** — not only tension/density curves, but also **meter changes, groove profiles, articulation envelopes, and tuning systems**. Notes are filled in only after these time-axis decisions are committed. This produces structurally meaningful music in any tradition.

### Principle 5: The Human Ear is the Final Truth

No matter how refined automated metrics become, the human listening experience is the final judge. Agents **support, not replace** human judgment.

### Principle 6: Vertical Alignment

The expressiveness of the **input** (spec), the depth of the **processing** (pipeline), and the resolution of the **output evaluation** must advance together. Deepening any one alone is wasted. Every release must demonstrate progress on all three.

---

## 3. Architecture: The 8-Layer Model

YaO v2.0 organizes into **8 strictly separated layers**. Each layer has independent input/output contracts and is exchangeable and testable in isolation.

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                               │
│   Learn from production history, update user preferences     │
├──────────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                             │
│   Auto-evaluation, adversarial critique, genre-aware         │
│   metrics, audio-domain perceptual analysis                  │
├──────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                           │
│   MIDI / audio / score writing, microtonal MIDI,             │
│   articulation keyswitch, stem export                        │
├──────────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                               │
│   Reference-driven aesthetic anchoring,                      │
│   psychology mapping, audio feature extraction               │
├──────────────────────────────────────────────────────────────┤
│ Layer 3.5: Musical Plan IR (MPIR)                            │
│   SongFormPlan, HarmonyPlan, MotifPlan,                      │
│   ArrangementPlan, DrumPlan — the "why" layer                │
├──────────────────────────────────────────────────────────────┤
│ Layer 3: Score IR + Domain IR                                │
│   ScoreIR, MeterSpec, GrooveProfile,                         │
│   TuningSystem, Articulation, ExpressionCurve                │
├──────────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                                 │
│   Pluggable generators: rule_based, stochastic,              │
│   markov, constraint_solver; ensemble routing                │
├──────────────────────────────────────────────────────────────┤
│ Layer 1: Specification + GenreProfile                        │
│   YAML specs (v1, v2, v3), GenreProfile schema,              │
│   spec composability (extends, overrides, fragments)         │
├──────────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                           │
│   Instrument ranges, MIDI mappings, scales, chords           │
└──────────────────────────────────────────────────────────────┘
```

### Dependency Rule

Lower layers do **not** know about upper layers. Cross-layer imports are forbidden. The architecture lint tool (`make arch-lint`) enforces this via AST analysis.

### Comparison with v1.0

| Layer | v1.0 | v2.0 |
|---|---|---|
| 0 | Implicit | **Explicit Constants layer** |
| 1 | YAML spec | YAML + **GenreProfile** + **composability** |
| 2 | Generators | Generators + **ensemble routing** |
| 3 | ScoreIR | ScoreIR + **MeterSpec** + **GrooveProfile** + **TuningSystem** + **Articulation** |
| 3.5 | (not present) | **MPIR** — formalized |
| 4 | Stub | **Implemented** with reference matching, audio features, psychology |
| 5 | MIDI/audio | + **microtonal MIDI**, **keyswitch routing** |
| 6 | Verify | + **genre-aware**, **audio-domain**, **arrangement diff** |
| 7 | Reflect | + **A/B audition feedback**, **style profile learning** |

---

## 4. Directory Structure

```
yao/
├── PROJECT.md                          # Full design (this file)
├── CLAUDE.md                           # Agent operational rules
├── VISION.md                           # Target architecture roadmap
├── FEATURE_STATUS.md                   # Single source of truth
├── README.md                           # User quickstart
├── pyproject.toml
├── Makefile
│
├── .claude/
│   ├── commands/                       # Slash commands
│   ├── agents/                         # Subagent definitions (7)
│   ├── skills/
│   │   ├── genres/                     # 12+ genre profiles (Markdown + YAML)
│   │   ├── theory/                     # Voice leading, counterpoint, etc.
│   │   ├── instruments/                # Per-instrument vocabulary
│   │   ├── psychology/                 # Empirical music psychology
│   │   ├── grooves/                    # Groove profiles (Markdown form)
│   │   ├── tunings/                    # Tuning system documentation
│   │   ├── meters/                     # Meter family documentation
│   │   └── aesthetics/                 # "Great vs OK" per genre
│   ├── guides/                         # Developer guides
│   └── hooks/                          # Pre-commit, post-generate
│
├── specs/
│   ├── projects/                       # User compositions
│   ├── templates/                      # v1, v2, v3 templates
│   └── fragments/                      # Reusable spec fragments
│       ├── genres/
│       ├── grooves/
│       ├── meters/
│       ├── tunings/
│       └── instrumentation/
│
├── src/
│   ├── yao/
│   │   ├── conductor/                  # Orchestration engine
│   │   ├── constants/                  # Layer 0
│   │   ├── schema/                     # Layer 1: Pydantic models
│   │   │   ├── composition.py          # v1 + v2 + v3
│   │   │   ├── genre_profile.py        # GenreProfile schema
│   │   │   ├── meter.py                # MeterSpec schema
│   │   │   ├── groove.py               # GrooveProfile schema
│   │   │   ├── tuning.py               # TuningSystem schema
│   │   │   ├── articulation.py         # Articulation schema
│   │   │   └── composability.py        # extends/overrides/fragments
│   │   ├── ir/                         # Layer 3
│   │   │   ├── score_ir.py
│   │   │   ├── note.py
│   │   │   ├── meter.py                # MeterSpec IR
│   │   │   ├── groove.py               # GrooveProfile IR
│   │   │   ├── tuning.py               # TuningSystem IR
│   │   │   ├── articulation.py         # Articulation, ExpressionCurve
│   │   │   ├── timing.py               # Meter-aware
│   │   │   ├── notation.py
│   │   │   ├── voicing.py              # Tuning-aware
│   │   │   ├── harmony.py
│   │   │   ├── motif.py
│   │   │   ├── trajectory.py
│   │   │   └── plan/                   # Layer 3.5: MPIR
│   │   ├── generators/                 # Layer 2
│   │   │   ├── rule_based.py
│   │   │   ├── stochastic.py
│   │   │   ├── markov.py               # NEW
│   │   │   ├── constraint_solver.py    # NEW
│   │   │   ├── drum_patterner.py
│   │   │   ├── counter_melody.py
│   │   │   └── ensemble.py             # NEW: per-part routing
│   │   ├── perception/                 # Layer 4
│   │   │   ├── audio_features.py       # librosa-based
│   │   │   ├── use_case_eval.py        # Use-case targeting
│   │   │   ├── reference_matcher.py    # Stage 3
│   │   │   ├── psych_mapper.py         # Russell circumplex
│   │   │   └── style_vector.py
│   │   ├── render/                     # Layer 5
│   │   │   ├── midi_writer.py          # Microtonal-capable
│   │   │   ├── stem_writer.py
│   │   │   ├── audio_renderer.py
│   │   │   ├── articulation_router.py  # NEW: keyswitch routing
│   │   │   └── musicxml_writer.py
│   │   ├── verify/                     # Layer 6
│   │   │   ├── lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py            # Genre-aware weights
│   │   │   ├── critique/               # 30+ rules
│   │   │   ├── diff.py
│   │   │   └── constraints.py
│   │   ├── arrange/                    # Arrangement engine
│   │   │   ├── source_extractor.py     # MIDI → SourcePlan
│   │   │   ├── style_vector_ops.py     # Vector arithmetic
│   │   │   ├── preservation.py         # Preservation contracts
│   │   │   └── arrangement_diff.py     # Markdown diff
│   │   └── reflect/                    # Layer 7
│   │       ├── provenance.py           # Causal graph
│   │       ├── feedback.py
│   │       └── style_profile.py        # User style learning
│   └── cli/                            # CLI commands
│
├── references/
│   ├── catalog.yaml
│   ├── midi/
│   └── extracted_features/
│
├── drum_patterns/
│   ├── grooves/                        # GrooveProfile YAMLs
│   └── meters/                         # Per-meter pattern families
│
├── tunings/                            # TuningSystem YAMLs
│   ├── 12tet.yaml
│   ├── just_intonation.yaml
│   ├── maqam_rast.yaml
│   ├── pelog.yaml
│   ├── werckmeister_3.yaml
│   └── partch_43.yaml
│
├── outputs/                            # Generated artifacts
├── soundfonts/                         # Audio rendering
├── gallery/                            # Curated examples per genre
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── scenarios/
│   ├── music_constraints/
│   ├── golden/
│   └── genre_coverage/                 # NEW: per-genre validation
├── tools/
│   ├── architecture_lint.py
│   ├── feature_status_check.py
│   ├── genre_calibrator.py             # NEW: parameter sweep
│   └── skill_sync.py
└── docs/
    ├── design/
    ├── genres/                         # NEW: per-genre user guide
    ├── recipes/                        # NEW: purpose-driven recipes
    ├── tutorials/
    └── glossary.md
```

---

## 5. The Orchestra: Subagent Design

### 5.1 The Seven Players

YaO v2.0 keeps the seven subagents introduced in v1.0, with expanded responsibilities to consume the new IRs.

#### 5.1.1 Composer
- **Responsibility**: Melody, motif, theme, structural outline
- **Inputs**: `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`, **GenreProfile**, **MeterSpec**
- **Outputs**: `MotifPlan`, `PhrasePlan` (Score IR motifs and phrase structure)
- **Forbidden**: Instrument selection, final voicing (Orchestrator's job)
- **v2.0 additions**: Must respect MeterSpec for phrase boundaries; consult GenreProfile for melody contour preferences

#### 5.1.2 Harmony Theorist
- **Responsibility**: Chord progressions, modulations, cadences, reharmonization
- **Inputs**: Composer's melody draft, harmony section of spec, **TuningSystem**, **GenreProfile**
- **Outputs**: `HarmonyPlan` (chord events with function, tension, cadence role)
- **v2.0 additions**: Functions correctly in non-12TET tunings; respects genre-specific signature/forbidden progressions

#### 5.1.3 Rhythm Architect
- **Responsibility**: Drum patterns, grooves, syncopation, fills
- **Inputs**: Spec rhythm section, **MeterSpec**, **GrooveProfile**, GenreProfile
- **Outputs**: `DrumPattern` (now meter- and groove-aware)
- **v2.0 additions**: Generates patterns in any meter; applies microtiming offsets from groove profiles

#### 5.1.4 Orchestrator
- **Responsibility**: Instrument assignment, voicing, register placement, counter-melody
- **Inputs**: All plans above, GenreProfile, **per-instrument articulation vocabulary**
- **Outputs**: `ArrangementPlan` with articulation choices
- **v2.0 additions**: Selects articulations from each instrument's vocabulary; manages frequency space across instrument register decisions

#### 5.1.5 Adversarial Critic
- **Responsibility**: Find every weakness; never praise
- **Inputs**: MPIR (preferred) or Score IR (fallback)
- **Outputs**: `critique.md` with structured `Finding` objects (severity, evidence, location, recommendation)
- **v2.0 additions**: Genre-specific critique rules from GenreProfile; aesthetic critique via Perception Layer; metric drift detection; arrangement-mode critique

#### 5.1.6 Mix Engineer
- **Responsibility**: Stereo placement, dynamics, frequency balance, loudness management
- **Inputs**: Orchestrator output + production parameters
- **Outputs**: Mix instructions per track (EQ, compression, reverb, panning)
- **v2.0 additions**: Genre-aware production chains from GenreProfile (e.g., lo-fi vinyl simulation, trap sidechain)

#### 5.1.7 Producer
- **Responsibility**: Coordination, conflict resolution, final judgment, dialogue with Conductor (human)
- **Inputs**: All subagent outputs + human feedback
- **Outputs**: Final decisions, escalation requests
- **Privilege**: Only subagent who can override others
- **v2.0 additions**: Consults Vertical Alignment Principle when balancing input/processing/evaluation; escalates when GenreProfile is incomplete

### 5.2 Subagent ↔ Pipeline Mapping

```
Step 1 Form Planner       ← Producer (form is meta)
Step 2 Harmony Planner    ← Harmony Theorist
Step 3 Motif Developer    ← Composer
Step 4 Drum Patterner     ← Rhythm Architect
Step 5 Arranger           ← Orchestrator
═══ Critic Gate ═══       ← Adversarial Critic (operates on MPIR)
Step 6 Note Realizer      ← Composer (low-level, ensemble routing)
Step 7 Renderer           ← Mix Engineer
Post-render Critique      ← Adversarial Critic (operates on audio features)
```

### 5.3 The Critic is Special

The Adversarial Critic **never praises**. Its sole purpose is to find weaknesses — structurally, aesthetically, and genre-specifically. The Producer balances critique against intent. This adversarial structure prevents the system from optimizing into self-satisfaction.

---

## 6. The Cognitive Protocol: 6 Phases × 7 Steps

YaO's `/compose` and `/arrange` commands enforce **6 cognitive phases** mapped onto the **7-step generation pipeline**. This eliminates the "agent jumps straight to writing notes" failure pattern.

| Cognitive Phase | Pipeline Steps | Goal |
|---|---|---|
| 1. Intent Crystallization | (pre-pipeline) | Finalize `intent.md` in 1–3 sentences |
| 2. Architectural Sketch | Step 1 (Form Planner) + trajectory.yaml | Draw time-axis trajectories before any notes |
| 3. Skeletal Generation | Steps 2–5 (5 candidate plans) | Generate 5 MPIR candidates with diverse seeds |
| 4. Critic-Composer Dialogue | Critic Gate ranks/selects | Critic ranks; Producer selects winner or merges |
| 5. Detailed Filling | Steps 6–7 | Realize MPIR → Score IR → MIDI/audio |
| 6. Listening Simulation | Perception Layer | Audio-feature evaluation; divergence triggers replan |

### Multi-Candidate Generation

In Phase 3, the Conductor instantiates **5 parallel pipelines** through Steps 2–5 with different seeds. The Critic at the Critic Gate ranks all five plans. The Producer either selects a winner or instructs Composer to merge strengths from multiple candidates into a new plan.

This is not a metaphor. It is implemented in `conductor/multi_candidate.py` and exposed via `--candidates 5` on the CLI.

---

## 7. Specification Layer: 11 YAML Document Types

YaO v2.0 describes a composition through the following **11 YAML documents** — all version-controlled, all diffable.

### 7.1 `intent.md` (Natural Language)
The composition's essence in 1–3 sentences. The final ground truth for all decisions.

### 7.2 `composition.yaml` (Composition Parameters)
Key, tempo, meter, form, genre, instrumentation, sections. v3 schema introduces explicit `meter_spec`, `tuning_system`, and `genre_profile_ref` fields.

```yaml
# v3 example
schema_version: 3
title: "Mediterranean Storm"

genre_profile: balkan_dance              # references GenreProfile YAML

meter:
  default:
    numerator: 7
    denominator: 8
    grouping: [3, 2, 2]
  changes:
    - { at_bar: 32, numerator: 4, denominator: 4 }    # mid-piece change

tuning:
  system: "12tet"                       # default; could be "maqam_rast" etc.

groove:
  default: "balkan_kopanitsa"           # references GrooveProfile

sections:
  - name: intro
    bars: 8
    dynamics: mp
    meter_override: { numerator: 3, denominator: 4 }   # this section in 3/4
```

### 7.3 `trajectory.yaml` (Time-Axis Curves)
Five trajectory dimensions: tension, density, predictability, brightness, register_height.

### 7.4 `references.yaml` (Aesthetic References)
Positive and negative reference compositions. Comparison axes restricted to **abstract features** (tempo, density curve, spectral balance) — never melody or chord progressions.

### 7.5 `negative-space.yaml` (Silence Design)
Phrase breath marks, pre-climax silence, frequency gaps, deliberate texture drops.

### 7.6 `arrangement.yaml` (Arrangement Mode)
Source file, preservation contract, transformation contract, evaluation weights.

### 7.7 `production.yaml` (Mix and Master)
LUFS target, stereo width, reverb, EQ chain. Genre-aware defaults from GenreProfile.

### 7.8 `provenance.json` (Auto-Generated)
Causal graph of every generation decision. Read-only for humans; appended automatically.

### 7.9 `genre_profile.yaml` (Genre Definition, NEW in v2.0)
The numeric backbone of genre identity. See Section 9.

### 7.10 `meter_spec.yaml` (Meter Definition, NEW in v2.0)
Reusable meter specifications. Referenced by `composition.yaml`.

### 7.11 `groove_profile.yaml` (Groove Definition, NEW in v2.0)
Microtiming and velocity offsets. Referenced by `composition.yaml`.

### 7.12 Spec Composability (NEW in v2.0)
v3 specs can compose from fragments:

```yaml
extends:
  - fragments/genres/lofi_hiphop.yaml
  - fragments/grooves/j_dilla.yaml
  - fragments/instrumentation/jazz_trio.yaml

overrides:
  tempo_bpm: 95
  meter:
    numerator: 5
    denominator: 4
```

---

## 8. New Domain IRs in v2.0

### 8.1 MeterSpec IR

```python
@dataclass(frozen=True)
class MeterSpec:
    numerator: int                          # 4, 3, 6, 5, 7, 11, ...
    denominator: int                        # 4, 8, 16, ...
    grouping: tuple[int, ...]               # (3, 2, 2) for 7/8 long-short-short
    is_compound: bool                        # 6/8, 9/8, 12/8 are compound
    pulse_unit: str                          # "quarter", "eighth", "dotted_quarter"
    metric_accents: tuple[float, ...]        # weight per pulse position
```

The `grouping` field disambiguates `7/8 (3,2,2)` (Bartók) from `7/8 (2,2,3)` (Bulgarian *kopanitsa*) from `7/8 (2,3,2)` (Greek *kalamatianos*) — these sound entirely different.

### 8.2 GrooveProfile IR

```python
@dataclass(frozen=True)
class GrooveProfile:
    name: str
    timing_offsets: dict[BeatPosition, float]   # ms offsets per beat position
    velocity_offsets: dict[BeatPosition, int]
    timing_jitter_ms: float                      # principled randomness
    velocity_jitter: int
    per_instrument_offset: dict[str, float]     # snare delays differently
    swing_curve: tuple[float, ...] | None        # subdivision-level swing
```

Initial library of 15 grooves: `j_dilla_drunken`, `motown_pushed`, `bossa_clave`, `swing_60`, `swing_67`, `latin_clave_son`, `latin_clave_rumba`, `funk_pocket`, `trap_modern`, `dnb_amen`, `reggae_one_drop`, `afrobeat_tony_allen`, `nola_second_line`, `dilla_brokenbeat`, `straight`.

### 8.3 TuningSystem IR

```python
@dataclass(frozen=True)
class TuningSystem:
    name: str
    cents_deviation: dict[int, float]      # MIDI note → cents from 12TET
    ratios: tuple[float, ...] | None       # for Just Intonation
    notes_per_octave: int = 12              # 24 quarter-tone, 53 for 53-EDO
    base_frequency_hz: float = 440.0
    requires_mpe: bool = False              # MIDI Polyphonic Expression
```

Initial systems: `12tet`, `just_intonation_5_limit`, `pythagorean`, `mean_tone_quarter`, `werckmeister_3`, `kirnberger_3`, `maqam_rast`, `pelog`, `slendro`, `partch_43`, `bohlen_pierce`, `53_edo`.

### 8.4 Articulation and ExpressionCurve IR

```python
@dataclass(frozen=True)
class Articulation:
    name: str                              # "staccato", "legato", "marcato", "pizz"
    duration_factor: float                 # 1.0 normal, 0.5 staccato, 1.0 legato
    velocity_modifier: int
    keyswitch: int | None                  # MIDI keyswitch for sample libs
    cc_changes: list[tuple[int, int]]      # (cc_num, value) for VST control

@dataclass(frozen=True)
class ExpressionCurve:
    cc_number: int                         # 1 modwheel, 11 expression, 64 sustain
    waypoints: tuple[tuple[Beat, int], ...] # (beat, value) pairs
    interpolation: str = "linear"           # or "bezier", "stepped"
```

### 8.5 Extended Note IR

```python
@dataclass(frozen=True)
class Note:
    pitch: MidiNote
    start: Beat
    duration: Beat
    velocity: Velocity
    # v2.0 additions:
    articulation: Articulation | None = None
    expression: tuple[ExpressionCurve, ...] = ()
    tuning_offset_cents: float = 0.0       # microtonal deviation
    microtiming_offset_ms: float = 0.0     # groove-derived
```

Backward compatibility: All new fields are optional with safe defaults.

---

## 9. The GenreProfile System

A **GenreProfile** is the numeric backbone of a genre's identity. It drives generator defaults, evaluation weights, and critic thresholds. Each GenreProfile is paired with a Markdown Skill document (for Subagent prompts) — and the YAML is **derived from the Markdown front-matter** to prevent desync.

### 9.1 GenreProfile YAML Schema

```yaml
schema_version: 1
identity:
  name: "Lo-fi Hip-Hop"
  family: "hip-hop"
  parent: null                           # for inheritance
  origin: "early 2010s, J Dilla legacy"

tempo:
  central: 82
  range: [70, 95]
  drift_tolerance: 0.05

meter:
  default: "4/4"
  alternates: ["6/8 (rare)"]

tuning:
  default: "12tet"

groove:
  default: "j_dilla_drunken"
  swing: { value: 0.58, range: [0.50, 0.65] }
  micro_timing:
    snare_offset_ms: { mean: -18, std: 8 }
    hat_offset_ms: { mean: 0, std: 12 }

harmony:
  preferred_chord_extensions: ["maj7", "min7", "9", "11", "13"]
  modulation_frequency: 0.1
  key_preferences: ["minor", "modal_minor"]
  cliche_progressions_to_avoid: ["I-V-vi-IV"]
  signature_progressions: ["ii7-V7-Imaj7", "iv7-V7-i7"]

melody:
  range_octaves: 1.5
  contour: ["arch", "wave"]
  syncopation: { mean: 0.45 }
  pentatonic_bias: 0.4

drums:
  default_pattern: "lofi_boom_bap"
  kick_density: { mean: 2.5, range: [1.5, 4] }
  snare_position: ["beat_2", "beat_4"]
  ghost_notes: 0.3

instrumentation:
  required: ["drums", "bass"]
  signature: ["rhodes", "felt_piano", "sub_bass", "vinyl_noise"]
  optional: ["sax_sample", "guitar_chord", "vocal_chop"]
  forbidden: ["modern_synth_lead", "trap_808"]

articulation_defaults:
  piano: ["legato", "soft_pedal"]
  bass: ["fingered", "muted"]

production:
  filter_chain:
    - { type: "lowpass", cutoff: 8000, resonance: 0.2 }
    - { type: "saturator", drive: 0.3 }
    - { type: "vinyl_simulation", crackle: 0.4 }
  sidechain: false
  stereo_width: 0.6
  bit_reduction: { enabled: true, depth: 12 }
  target_lufs: -14

evaluation:
  weights:
    structure: 0.20
    melody: 0.15
    harmony: 0.20
    rhythm: 0.30
    timbre: 0.15
  bonus_metrics:
    - { name: "vinyl_authenticity", target: 0.7 }
    - { name: "j_dilla_groove_match", target: 0.6 }

generator_assignments:
  drums: { strategy: "markov", model: "j_dilla_corpus" }
  bass: { strategy: "constraint_solver", strict_function: true }
  melody: { strategy: "stochastic", temperature: 0.4 }
  pad: { strategy: "rule_based", template: "minor_pentatonic" }

aesthetic_critique:
  - rule: "must_have_imperfection"
    description: "At least one of: vinyl noise, tape wobble, slight detuning"
    severity: major
  - rule: "no_perfect_quantization"
    description: "Drums must show microtiming variance > 5ms std"
    severity: major
```

### 9.2 GenreProfile Inheritance

`lofi_hiphop` extends `hip_hop` extends `groove_based`. Common features inherit; differences are stated explicitly. This keeps the genre tree maintainable as it grows from 12 to 50+ genres.

### 9.3 Initial GenreProfile Library (v2.0 Target: 24)

| Family | Profiles |
|---|---|
| Western Classical | classical, baroque, romantic, contemporary_classical, neoclassical |
| Cinematic | cinematic_orchestral, cinematic_hybrid, video_game_orchestral |
| Jazz | jazz_ballad, bebop, fusion, modal_jazz |
| Pop / Rock | j_pop, k_pop, pop, rock_classic, indie_rock, math_rock |
| Electronic | techno, house, trance, ambient, idm |
| Hip-Hop | hip_hop, lofi_hiphop, trap, dnb |
| World Music | bossa_nova, samba, balkan_dance, indian_classical, gamelan, arabic_maqam |
| Folk | acoustic_folk, celtic_folk |
| Game/8-bit | game_8bit_chiptune |

### 9.4 Genre Calibration

`make calibrate-genres` runs a parameter sweep:
1. Generate 100 specs per genre, sampling within profile ranges
2. Run through Conductor
3. Extract audio features via librosa
4. Compare to reference compositions in the genre
5. Update profile values if drift is detected

This is continuous calibration — running periodically as the system evolves.

---

## 10. The Generation Pipeline (v2.0)

```
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: Form Planner    Spec + Trajectory + GenreProfile         │
│                                  ↓                                │
│                          SongFormPlan (with MeterSpec)            │
├──────────────────────────────────────────────────────────────────┤
│ Step 2: Harmony Planner                                           │
│                                  ↓                                │
│                          HarmonyPlan (tuning-aware)               │
├──────────────────────────────────────────────────────────────────┤
│ Step 3: Motif Developer                                           │
│                                  ↓                                │
│                          MotifPlan + PhrasePlan                   │
├──────────────────────────────────────────────────────────────────┤
│ Step 4: Drum Patterner   meter + groove + genre                   │
│                                  ↓                                │
│                          DrumPattern (meter-aware, groove-aware)  │
├──────────────────────────────────────────────────────────────────┤
│ Step 5: Arranger         articulation defaults from genre         │
│                                  ↓                                │
│                          ArrangementPlan                          │
├──────────────────────────────────────────────────────────────────┤
│ ════════════ MUSICAL PLAN COMPLETE — Critic Gate ════════════     │
│                                                                   │
│       Adversarial Critic operates on MPIR                        │
│       Findings → plan-level edits OR plan rejection              │
├──────────────────────────────────────────────────────────────────┤
│ Step 6: Note Realizer    ensemble routing per part                │
│                                  ↓                                │
│                          ScoreIR (with articulation, microtiming) │
├──────────────────────────────────────────────────────────────────┤
│ Step 7: Renderer         MIDI (with pitch_bend if microtonal)     │
│                                  ↓                                │
│                          MIDI / Audio / Score                     │
├──────────────────────────────────────────────────────────────────┤
│ Post-Render Critique     audio features via librosa               │
│                                  ↓                                │
│                          PerceptualReport                         │
│                          → if divergent, replan offending sections│
└──────────────────────────────────────────────────────────────────┘
```

### Determinism

Every step is seeded; every step records its provenance. The combination `(spec, trajectory, genre_profile, seed_per_step)` is sufficient to reproduce any output bit-for-bit.

---

## 11. Layer 4: Perception Substitute

The Perception Substitute Layer addresses YaO's most distinctive challenge: **LLMs cannot listen**. Layer 4 substitutes for hearing through three stages.

### 11.1 Stage 1: Audio Feature Extraction

After audio rendering, extract via librosa and pyloudnorm:
- LUFS (integrated, short-term, momentary)
- Peak, RMS, dynamic range
- Spectral centroid, rolloff, flatness
- Onset density per section
- Tempo stability (ms drift)
- Frequency band energy ratios (sub, low, mid, high)

These produce a `PerceptualReport` with objective acoustic dimensions.

### 11.2 Stage 2: Use-Case Targeting

```python
USE_CASE_EVALUATIONS = {
    "youtube_bgm": [vocal_space, loopability, fatigue_risk, lufs_target],
    "game_bgm": [loop_seam_smoothness, tension_curve_match, repetition_tolerance],
    "advertisement": [hook_entry_under_7s, energy_peak_position, memorability],
    "study_focus": [low_distraction, dynamic_stability, predictability],
    "concert_hall": [dynamic_range, climactic_arc, sustained_tension],
    "club_dj_set": [beatmatchable_intro, energy_floor, mix_in_out],
}
```

### 11.3 Stage 3: Reference Matching (Abstract Features Only)

Compute style vectors and compare to references. Comparison axes are restricted to **abstract features** (tempo, density curve, spectral balance, section energy, groove profile). Forbidden axes (melody, chord progression, identifiable hooks) are enforced at the schema level — deviating raises a schema error.

### 11.4 Affective Computing-Derived Emotional Evaluation

Use Russell's circumplex model (valence × arousal) to map music to a 2D emotional space. Compare to coordinates declared in `intent.md`. Mapping function grounded in Juslin & Sloboda's *Handbook of Music and Emotion*.

---

## 12. The Arrangement Engine

### 12.1 Pipeline

```
[Input]      MIDI / MusicXML / (audio with stems)
   ↓
[Source Extractor]   Section detection, melody extraction,
                     chord estimation, motif detection,
                     role classification, groove extraction
   ↓
[SourcePlan] = MPIR of input piece
   ↓
[Preservation Plan]   melody, hook rhythm, chord function, form
[Transformation Plan] genre, bpm, reharm, regroove, reorch
   ↓
[Style Vector Op]
   target_plan = source_plan
                 - vec(source_genre)
                 + vec(target_genre)
                 ⊕ preservation_constraints
   ↓
[TargetPlan] = MPIR of arranged piece
   ↓
[Note Realizer]  → ScoreIR → MIDI / audio
   ↓
[Arrangement Diff]   Markdown report: preserved / changed / risks
   ↓
[Evaluation]
```

### 12.2 Why MPIR Enables Arrangement

Arrangement at the *note level* is brittle — pitch substitution, tempo stretching, instrument remapping. Arrangement at the *plan level* is robust — preserve the harmonic function, vary the voicing; preserve the motif identity, vary the rhythm shape.

### 12.3 Arrangement Spec

```yaml
arrangement:
  input:
    file: "inputs/original.mid"
    rights_status: "owned_or_licensed"        # required field

  preserve:
    melody:        { enabled: true, similarity_min: 0.85 }
    hook_rhythm:   { enabled: true, similarity_min: 0.80 }
    chord_function:{ enabled: true, similarity_min: 0.75 }
    form:          { enabled: true }

  transform:
    target_genre: "lofi_hiphop"
    bpm: { mode: "set", value: 86 }
    harmony:
      reharmonization_level: 0.35
      add_7ths: true
    rhythm:
      target_groove: "j_dilla_drunken"        # NEW in v2.0
    orchestration:
      drums: "dusty_kit"
      bass: "warm_upright"
    tuning:                                    # NEW in v2.0
      target_system: "12tet"

  evaluate:
    original_preservation_weight: 0.5
    transformation_strength_weight: 0.3
    musical_quality_weight: 0.2
```

### 12.4 Arrangement Diff Output

Every arrangement run produces a Markdown diff comparable to git diffs, with sections labeled "Preserved / Changed / Risks / Rejected." Each line is human-auditable.

### 12.5 Failure-Mode Critic Rules for Arrangement

- `register_shift`: melody preserved logically but instrument substitution moves perceptual register
- `groove_collision`: source groove conflicts with target genre conventions
- `rights_concern`: preservation similarity so high that result resembles source
- `transformation_under_target`: requested transformation strength 0.5, achieved 0.2

---

## 13. Custom Commands

| Command | Purpose | Primary Subagent |
|---|---|---|
| `/sketch` | Interactive spec creation through dialogue | Producer |
| `/compose <project>` | Generate from spec with Conductor loop | Composer → all |
| `/arrange <project>` | Transform existing composition | Orchestrator + Critic |
| `/critique <iteration>` | Adversarial feedback on existing iteration | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate between two compositions | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment (live mode) | Composer + Rhythm |
| `/explain <element>` | Trace decision via Provenance Graph | Producer |
| `/diff <iter_a> <iter_b>` | Music-aware diff between iterations | Verifier |
| `/render <iteration>` | Render MIDI to audio/score | Mix Engineer |
| `/audition <project>` | A/B comparison UI in browser | (UI command) |
| `/calibrate <genre>` | Run parameter sweep for genre | (Tool command) |

---

## 14. Skills (Knowledge Modules)

`.claude/skills/` houses structured domain knowledge. Subagents consult these as needed.

### 14.1 Genre Skills (Target: 24)
Each genre has both a Markdown form (Subagent prompts) and a YAML form (programmatic GenreProfile). The YAML is generated from the Markdown front-matter — they cannot desync.

### 14.2 Theory Skills
Voice leading, counterpoint, reharmonization, modal interchange, secondary dominants, modulation techniques. Each entry has examples and counter-examples; rules tagged with genre dependencies.

### 14.3 Instrument Skills
Each of the 38+ supported instruments has a Skill with range, idiomatic patterns, articulation vocabulary, frequency profile, and characteristic phrases.

### 14.4 Psychology Skills
Empirical music-psychology mappings (Krumhansl, Huron, Juslin & Sloboda) for the Perception Layer's psych mapper.

### 14.5 Groove Skills (NEW in v2.0)
Each groove profile has a Markdown explanation — what makes Motown push? Why does Dilla's snare delay sound human? — alongside the YAML profile.

### 14.6 Tuning Skills (NEW in v2.0)
Each tuning system has a Markdown introduction — when to use just intonation, why maqam Rast feels distinctive, what historical temperaments enable in Baroque music.

### 14.7 Meter Skills (NEW in v2.0)
Documentation of meter families: irregular meters, additive meters, compound meters, mixed meters.

### 14.8 Aesthetics Skills (NEW in v2.0)
"Great vs OK per genre" — articulating the difference between competent and memorable in each tradition. For prompt-time consultation by Subagents, not for hard rules.

---

## 15. Hooks (Automated Quality Gates)

Hooks are **scripts that execute regardless of agent memory**. They are the system's defense against agents forgetting their guidelines.

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | git commit | YAML schema check, music21 lint, golden test smoke, GenreProfile validation |
| `post-generate-render` | After generation | Auto-render audio, write critique |
| `post-generate-critique` | After generation | Run rule-based critique, persist `critique.json` |
| `post-arrange-diff` | After arrangement | Generate Arrangement Diff Markdown |
| `update-provenance` | Any plan/score change | Append to causal provenance graph |
| `spec-changed-show-diff` | Edit spec | Show what changed musically (MPIR-level) |
| `genre-profile-validate` | GenreProfile change | Run calibration sanity check |
| `tuning-mpe-check` | Microtonal output | Verify MPE compatibility, warn if not |

---

## 16. MCP Integration

| MCP Target | Purpose | Phase |
|---|---|---|
| **Reaper DAW** | Project file read/write, track layout | gamma |
| **Sample library** | Search/fetch drum samples, one-shots | gamma |
| **Reference DB** | Rights-cleared reference catalog | gamma |
| **MIDI controller** | Live mode input | delta |
| **SoundFont/VST host** | Tone rendering with articulation routing | gamma |
| **Cloud storage** | Artifact backup, team share | delta |
| **Pianoteq** | Microtonal piano rendering | gamma |
| **Csound bridge** | Beyond-MIDI tunings | epsilon |

---

## 17. Quality Evaluation: Genre-Aware Metrics

YaO v2.0 evaluates compositions across **5 dimensions** with **genre-specific weights** (from GenreProfile).

### 17.1 Structure (default 25%, configurable)
Section contrast, climax position, density curve fit, repetition balance, loopability.

### 17.2 Melody (default 30%, configurable)
Range fit, motif memorability, singability, phrase closure, contour variation.

### 17.3 Harmony (default 25%, configurable)
Chord function fit, tension resolution, harmonic complexity match, cadence strength.

### 17.4 Rhythm (NEW in v2.0, default 10%, up to 40% for percussion-centric)
Groove consistency, polyrhythmic density, pattern evolution, microtiming complexity, onset density per beat.

### 17.5 Timbre (NEW in v2.0, default 5%, up to 20% for electronic genres)
Spectral centroid arc, spectral complexity, timbral variety per section, dynamic range, transient density.

### 17.6 Arrangement Mode Additional Metrics
Original preservation rate, transformation strength, instrument role clarity, frequency collision risk.

### 17.7 Acoustic Mode (Layer 4 Output)
LUFS target match, beat stability, spectral balance, onset density.

---

## 18. Development Roadmap (180-Day Plan)

The roadmap follows VISION.md's phase structure, advancing **input, processing, and evaluation** in lockstep per the Vertical Alignment Principle.

### Phase 1.5 (Days 1–14): Pre-Phase-2 Foundation [NEW]
Address the three highest-impact, lowest-effort genre-coverage issues:
- GenreProfile YAML schema strict definition + numeric backfill of 8 genres
- Dynamic evaluation weights from GenreProfile (incl. percussion-centric flag)
- MeterSpec IR + DrumPattern meter-aware refactor

**Milestone**: Compositions in 3/4, 5/4, 6/8, 7/8 generate correctly. Techno and trap evaluate against rhythm-centric metrics.

### Phase 2 (Days 15–60): Plan Layer & Mechanized Critique
- MotifPlan / PhrasePlan / DrumPattern / ArrangementPlan implemented
- Adversarial Critic: 30+ rules across 6 categories
- Multi-candidate Conductor (5 candidates → critic-rank → producer-pick)
- Markov + constraint_solver Note Realizers
- GrooveProfile IR + initial library (15 grooves)
- Articulation IR + Note IR extension
- Spec composability (`extends:`, `overrides:`, `fragments/`)
- Genre Coverage Tests

**Milestone**: Lo-fi hip-hop with J Dilla groove. Cinematic with proper articulation. 24 GenreProfile YAMLs validated.

### Phase 3 (Days 61–105): Differentiation — Perception & Arrangement
- Perception Stage 1 (audio features)
- Perception Stage 2 (use-case targeted)
- Counter-melody Generator
- Arrangement Engine (full):
  - SourcePlan extractor (MIDI → MPIR)
  - Style vector operations
  - Preservation/transformation contract
  - Arrangement Diff Markdown
- Reference Matcher (Stage 3, abstract features only)
- TuningSystem IR + microtonal MIDI rendering

**Milestone**: Existing MIDI → arranged MIDI in different genre, with structured diff. Microtonal scales (maqam, just intonation) generate audibly.

### Phase 4 (Days 106–150): Production Readiness
- Production Manifest + Mix Chain (pedalboard)
- Sketch-to-Spec dialogue state machine
- Strudel emitter (browser-side instant audition)
- A/B Audition UI in browser
- Causal Provenance Graph
- Reaper MCP integration
- 12 additional Genre Skills (target: 24 total)

**Milestone**: Commercial BGM creator can use YaO end-to-end and import into a DAW for finishing.

### Phase 5 (Days 151–180+): Reflection & Continuous Improvement
- Reflection Layer (Layer 7) for user style profiles
- Genre Calibration via parameter sweeps
- Curriculum Learning for Conductor
- Community reference library shared format
- Live improvisation mode

---

## 19. Quickstart

### 19.1 Setup

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
make setup-hooks
```

### 19.2 First Composition

```bash
# Quick natural-language generation
yao conduct "a calm piano piece in D minor for studying, 90 seconds"

# Genre-specific generation with GenreProfile
yao conduct "a Balkan folk dance" --genre balkan_dance

# YAML-based with composability
cat > specs/projects/my-experiment/composition.yaml <<EOF
schema_version: 3
extends:
  - fragments/genres/lofi_hiphop.yaml
overrides:
  meter:
    numerator: 5
    denominator: 4
EOF
yao compose specs/projects/my-experiment/composition.yaml
```

### 19.3 Interactive (Recommended)

```bash
claude
> /sketch a mysterious puzzle game BGM, minimal and looping
> /compose my-puzzle-bgm
> /critique my-puzzle-bgm
> /regenerate-section my-puzzle-bgm bridge
> /audition my-puzzle-bgm                # browser A/B comparison
```

### 19.4 Arrangement Mode

```bash
cp my_song.mid specs/projects/my-arrangement/source.mid
cat > specs/projects/my-arrangement/arrangement.yaml <<EOF
arrangement:
  input: { file: source.mid, rights_status: owned }
  preserve: { melody: { enabled: true, similarity_min: 0.85 } }
  transform:
    target_genre: lofi_hiphop
    target_groove: j_dilla_drunken
EOF
yao arrange my-arrangement
```

---

## 20. File Formats and Interoperability

YaO adopts these standard formats to ensure interoperability with external tools.

| Purpose | Format | Reason |
|---|---|---|
| Music data | MIDI (.mid), MusicXML (.xml) | Industry standard, all DAWs |
| Microtonal MIDI | MPE-encoded MIDI | Hardware/software MPE-compatible |
| Score | LilyPond (.ly), PDF | High-quality typesetting |
| Specs | YAML | Human-readable, git-friendly |
| Intermediate Reps | JSON | Schema-validatable |
| Provenance | JSON (graph structure) | Causal chain expression |
| Audio | WAV (production), FLAC/MP3 (distribution) | Universal support |
| Live coding | Strudel patterns | Browser-instant audition |
| Beyond MIDI | Csound, Faust | Microtonal/spectral that exceed MIDI |

Custom formats are avoided. Only what existing standards cannot express is added minimally.

---

## 21. Ethics and Licensing

### 21.1 Reference Data
References must be **rights-cleared compositions only**. Each is recorded in `references/catalog.yaml` with license status. Unknown-status compositions are excluded.

### 21.2 Artist Imitation
Specifications like "in the style of <named living artist>" are not recommended. Instead, use **abstract feature descriptions**:

> ✗ "Joe Hisaishi style"
> ✓ "Wide open string voicings, ascending motifs, major-minor ambiguity, meditative tempo"

### 21.3 Generated Output Rights
Music generated by YaO is owned by the user, in principle. If the influence of a reference composition exceeds a threshold (computed from style vector similarity), a warning is issued.

### 21.4 Transparency
All generated output should be marked "produced with YaO" along with the list of aesthetic anchors consulted, recorded in `provenance.json`.

### 21.5 Cultural Appropriation Caution
GenreProfiles for non-Western traditions (maqam, gamelan, Indian classical) include cultural context Markdown documents that explain practice traditions, performance contexts, and respect considerations. The system warns when these are used without consultation of the documents.

---

## 22. Document Relationships

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this) | Humans + Agents | Overall design, philosophy, architecture |
| `CLAUDE.md` | Agents primarily | Operational rules, prohibitions, skill pointers |
| `README.md` | Humans primarily | Quickstart, minimal usage |
| `VISION.md` | Humans + Agents | Target architecture, roadmap |
| `FEATURE_STATUS.md` | Humans + Agents | Single source of truth for capabilities |
| `IMPROVEMENT.md` | Humans + Agents | Analysis and improvement plan |
| `docs/design/*.md` | Humans + Agents | Individual design decision records |
| `docs/genres/*.md` | Musicians | Per-genre user guide |
| `docs/recipes/*.md` | Users | Purpose-driven YAML recipes |
| `.claude/guides/*.md` | Developers + Agents | Technical guides (architecture, music, testing) |

---

## 23. Glossary

**Conductor (You)** — The human project owner. Final decision-maker.

**Orchestra** — Collective term for Subagents.

**Score** — YAML documents in `specs/`. Complete description of a composition.

**Score IR** — Intermediate representation that implementations operate on.

**MPIR (Musical Plan IR)** — Layer 3.5; the "why" representation between spec and score.

**Trajectory** — Time-axis curves of musical properties (tension, density, etc.).

**MeterSpec** — Explicit meter representation with grouping and accents.

**GrooveProfile** — Microtiming and velocity offsets that define a genre's feel.

**TuningSystem** — Pitch deviations from 12TET; supports microtonal traditions.

**Articulation** — Performance technique (legato, staccato, etc.) at the note level.

**ExpressionCurve** — Time-varying CC values (modwheel, expression).

**GenreProfile** — Numeric backbone of genre identity; drives generators and evaluators.

**Aesthetic Reference Library** — Reference compositions as aesthetic anchors.

**Perception Substitute Layer** — Layer 4; compensates for "AI cannot listen."

**Provenance** — Causal graph of generation decisions.

**Adversarial Critic** — Subagent that intentionally attacks output.

**Negative Space** — Explicit design of what NOT to play.

**Style Vector** — Multi-dimensional feature vector representing a genre/style.

**Iteration** — Versioned generation within a project (`v001`, `v002`, ...).

**Music Lint** — Auto-detection of music theory and constraint violations.

**Sketch-to-Spec** — Dialogue process from natural-language sketch to YAML spec.

**Vertical Alignment** — Principle that input/processing/evaluation advance together.

**Recoverable Decision** — Logged decision that bypassed strict validation; CI-checked.

**Critic Gate** — Architectural checkpoint between Step 5 and Step 6 where MPIR is critiqued.

**Multi-Candidate Generation** — 5 parallel pipelines yielding 5 plans for Critic ranking.

---

## 24. The Future YaO Imagines

YaO v2.0 is not "an AI that produces music." It is **infrastructure for humans and AI to co-create music, each contributing their distinctive strengths**.

- Humans contribute **intent, judgment, and sensibility**.
- AI contributes **theoretical knowledge, iteration speed, and exhaustive record-keeping**.
- YaO is **the structured collaborative process that makes both possible**.

The expanded scope of v2.0 — meter pluralism, groove authenticity, microtonal traditions, articulation expression, genre-aware evaluation, arrangement transformation — is in service of one principle:

> **The world's musical traditions are diverse; YaO must honor them.**

Western melody and harmony are one tradition. African polyrhythm is another. Arabic maqam, Indian raga, Indonesian gamelan, Bulgarian asymmetric meters, J Dilla's microtiming, J-Pop's bridge conventions — each has its own logic, its own beauty, its own discipline. YaO v2.0 commits to representing these on equal footing.

Great music will always be **the expression of a human soul**. YaO aims to make that expression **faster, deeper, and more reproducible — across every tradition the human soul speaks in**.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve, in every tradition.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Last updated: 2026-05-04*
*Compatible with: Claude Code, Claude Sonnet 4.6+ / Opus 4.7+*
