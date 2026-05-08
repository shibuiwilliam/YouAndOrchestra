# PROJECT.md — You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## 0. The Essence of the Project

**You and Orchestra (YaO)** is an **agentic music production environment** that runs on Claude Code. Unlike typical "AI music tools" that emit audio from a single black box, YaO is structured around **multiple AI subagents with distinct roles, conducted by a human (You = Conductor)**.

Every design decision in YaO is subordinate to one proposition:

> **Music production is not a one-off, intuitive activity. It is a reproducible and improvable engineering practice.**

For this reason, YaO treats music as **code, specifications, tests, diffs, and provenance** before treating it as audio files. We call this the **Music-as-Code** philosophy.

YaO does not aim to be the cheapest or fastest music generator. It aims to be the **most musical, most explainable, most genre-faithful, and most genuinely diverse** open music production environment available — the one a serious composer, sound designer, or game audio team would actually use day-to-day.

The phrase-first pipeline gives YaO genre-faithful melodies. The Combination Stack ensures those melodies are not merely faithful but also varied, harmonically coupled, and structurally distinct across runs and across genres.

---

## 1. The Metaphor: You and Orchestra

Every concept in YaO maps onto an orchestral metaphor. Internalizing these correspondences is the shortest path to using YaO well.

| YaO component | Orchestral metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human who owns the project |
| **Score** | Sheet music | Composition specs in `specs/*.yaml` |
| **Orchestra Members** | Players | Individual subagents (Composer, Critic, Theorist, etc.) |
| **Concertmaster** | Concertmaster | Producer subagent (overall coordinator) |
| **Rehearsal** | Rehearsal | Generate–evaluate–revise iteration loop |
| **Library** | Music library | Reference catalog in `references/` |
| **Performance** | Live performance | Final rendered audio |
| **Recording** | Recording | Artifacts in `outputs/` |
| **Critic** | Critic | Adversarial Critic subagent |
| **Style Encyclopedia** | Encyclopedia of styles | The 30+ genre Skills in `.claude/skills/genres/` |
| **Players' Schooling** | Conservatory training | The `MelodicProfile` registry |
| **Rehearsal Conversations** | Players cueing each other | The Listening-Agent Dialog Graph |
| **Genre Atlas** | Map of stylistic territories | The Genre Vector Space |

The conductor (You) does not write every note. The conductor's job is to **clarify intent, give direction to the players, make decisions during rehearsal, and ensure the quality of the performance**. YaO brings this division of labor to AI, while leaving every meaningful judgment in the hands of the human.

---

## 2. Design Principles

Every implementation decision in YaO is evaluated against the following **eight non-negotiable principles**.

### Principle 1: The Agent Is an Environment, Not a Composer

YaO is not "an AI that writes music"—it is "an environment that makes a human composer ten times faster." The goal is to accelerate and extend human creative judgment, not to fully automate it.

### Principle 2: Every Decision Must Be Explainable

Every generated note, chord, and arrangement decision carries a recorded "why." This is persisted as a Provenance Graph and remains traceable, reviewable, and editable.

### Principle 3: Constraints Liberate Creativity

Explicit constraints—YAML specs, reference libraries, genre profiles, negative space—act as scaffolding rather than cages. Unlimited freedom produces paralysis.

### Principle 4: Time-Axis Design Precedes Note Design

A piece is first designed as a **trajectory through time**—curves of tension, density, and emotional valence. Notes are filled in afterward. This produces music with structural meaning.

### Principle 5: The Human Ear Is the Final Truth

No matter how refined the automated metrics, the human listening experience is the final judge. The agent **supports** rather than **replaces** human judgment.

### Principle 6: Phrase Structure Precedes Note Selection

A melody is not a sequence of notes. It is a sequence of **phrases**, each of which has a function (statement, question, answer), a target pitch, and a cadence. Notes are derived from phrase structure, not the reverse.

### Principle 7: Genre Is a Constellation, Not a Label

A genre is not "scale + chord palette + tempo." It is a **multi-dimensional constellation** of interval distributions, rhythmic patterns, ornament profiles, phrase length conventions, cadence preferences, and idiomatic motif transformations. The `MelodicProfile` is the structural representation of this constellation.

### Principle 8: Diversity Through Combination, Not Just Material

A diverse output is not produced by enlarging the material library; it is produced by **dynamically combining, interpolating, dialoguing, and developing** the materials already present. The Combination Stack (Section 3.4) is the architectural enforcement of this principle. Adding a new genre profile or rhythm template is helpful; building a new mechanism that recombines all existing materials is multiplicatively more helpful.

This principle has three operational consequences:

1. **Melody, harmony, and rhythm cannot be generated independently.** They must be coupled through shared intermediate representations. The Harmonic-Melodic Coupling Layer (Section 3.4.1) makes melody choices conditional on the active harmony at every metric position.
2. **A genre is a position in a continuous space, not an enum value.** Two genres can be blended, interpolated, or contrasted. The Genre Vector Space (Section 3.4.4) provides the geometry.
3. **Long-form pieces require thematic recurrence with transformation.** Recurring without transformation is repetition; transforming without recurring is wandering. The Theme Recurrence Graph (Section 3.4.6) plans both.

---

## 3. Architecture

YaO has four nested architectural levels. Each has independent input/output contracts and is interchangeable and testable.

1. The **8-Layer Macro Architecture** (Section 3.1) governs the entire codebase
2. The **4-Layer Melody Pipeline** (Section 3.2) lives inside Layer 2, structuring how melodies are generated
3. The **MelodicProfile-Driven Genre System** (Section 3.3) parameterizes genre at every layer
4. The **Combination Stack** (Section 3.4) sits between the Melody Pipeline and the surrounding Layer 2 generators, ensuring that materials combine into diverse, coherent, and harmonically coupled output

### 3.1 The 8-Layer Macro Architecture

An explicit **Combination & Coupling** layer sits between Layer 2 (raw generation) and Layer 3 (IR). This formalizes the dependencies introduced by chord-aware melody, voice-leading optimization, reharmonization, and inter-instrument dialog.

```
┌───────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                            │
│   Production history, user style profiles, community-     │
│   shared profile updates, corpus-learned model registry   │
├───────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                          │
│   Music lint, structural/melodic/harmonic/acoustic        │
│   evaluation, score diff, genre-specific adversarial      │
│   critique, conformity & coherence scores, melody–        │
│   harmony alignment score, voice-leading-smoothness       │
│   score, polyrhythmic-coherence score                     │
├───────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                        │
│   MIDI writing (with microtonal pitch-bend), stem export, │
│   audio rendering (FluidSynth), score notation, live-     │
│   code emission                                           │
├───────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                            │
│   Reference matching, psychology-grounded mappings,       │
│   style-vector arithmetic                                 │
├───────────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)                 │
│   ScoreIR, Phrase, Skeleton, MelodyLine, Motif, Voicing,  │
│   Harmony, HarmonicContext, Trajectory, PhraseShape,      │
│   ThemeRecurrence, GenreVector,                           │
│   PolyrhythmTexture, HarmonicMelodyConstraints,           │
│   RhythmEvent (with functional labels), MotifNetwork      │
├───────────────────────────────────────────────────────────┤
│ Combination & Coupling Layer                              │
│   Harmonic-Melodic Coupling, Voice-Leading Optimizer,     │
│   Reharmonization Engine, Modulation Planner, Genre-      │
│   Vector Blender, Listening-Agent Dialog, Theme           │
│   Recurrence Planner, Variable Harmonic Rhythm            │
├───────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                              │
│   Pluggable generators (rule_based, stochastic,           │
│   phrase_aware, markov_v2, rhythm_markov, polyrhythm);    │
│   contains the 4-Layer Melody Pipeline                    │
├───────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                    │
│   YAML specs, dialogue input, sketch input, intent        │
│   parsing into StructuredIntent, intent-to-spec building, │
│   genre_blend spec, harmonic_devices override,            │
│   features feature-flag block                             │
├───────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                        │
│   Instrument ranges, MIDI mappings, scales (28),          │
│   chord types, dynamics, MelodicProfile registry,         │
│   RhythmTemplate registry, GrooveProfile registry,        │
│   HarmonicDevice library, IdiomaticGesture                │
│   library, MarkovModel YAML registry (pitch + rhythm +    │
│   contour)                                                │
└───────────────────────────────────────────────────────────┘
```

Layer dependencies flow strictly from bottom to top. Lower layers cannot import from higher ones. This is mechanically enforced by `make arch-lint`, an AST-based import checker. The Combination & Coupling layer sits between Layer 2 and Layer 3 and may import only from Layers 0–2.

When you add a new module, the first decision is **which layer does it belong to**. Use these questions:

- Does it only define values? → Layer 0
- Does it parse user input or build a spec from intent? → Layer 1
- Does it generate raw notes from scratch? → Layer 2
- Does it transform, couple, blend, or optimize already-generated material? → Combination & Coupling layer
- Does it represent musical structure? → Layer 3
- Does it substitute for aesthetic perception? → Layer 4
- Does it produce a consumable output (MIDI, audio, score)? → Layer 5
- Does it evaluate, lint, or critique? → Layer 6
- Does it learn from history? → Layer 7

### 3.2 The 4-Layer Melody Pipeline (within Layer 2)

The single most consequential architectural decision is the separation of **what a melody is** from **how the notes that realize it are chosen**. This is implemented as a four-layer sub-pipeline within Layer 2.

```
┌─────────────────────────────────────────────────┐
│  Layer M4: Ornament & Articulation              │
│  Grace notes, trills, slides, bends, legato/    │
│  staccato, microtiming offsets, ghost notes     │
│  Idiomatic gestures applied per instrument      │
├─────────────────────────────────────────────────┤
│  Layer M3: Surface Realization                  │
│  Passing tones, neighbor tones, anticipations,  │
│  appoggiaturas; rhythm template application;    │
│  velocity from dynamics + trajectory            │
├─────────────────────────────────────────────────┤
│  Layer M2: Skeleton Generation                  │
│  Chord-tone targets, voice-leading paths,       │
│  phrase-contour realization, harmonic outlining │
│  Now consumes HarmonicMelodyConstraints from    │
│  the Coupling Layer                             │
├─────────────────────────────────────────────────┤
│  Layer M1: Phrase & Motif Plan                  │
│  Phrase boundaries, cadence types, motif        │
│  selection and transformation strategy          │
└─────────────────────────────────────────────────┘
```

Each layer consumes inputs from the Combination & Coupling layer:

- **M2** consumes `HarmonicMelodyConstraints` from the Coupling Layer (Section 3.4.1) for chord-aware pitch selection
- **M3** uses genre-conditioned rhythm Markov models (Section 3.4.5) when selected via `MelodicProfile.rhythm_strategy: markov`
- **M4** applies the `IdiomaticGesture` library (Section 3.4.7) per instrument
- **M1** consumes `PhraseShape` plans from the long-form coherence layer (Section 3.4.6) when the spec calls for explicit phrase shaping

The existing `phrase_aware` generator continues to orchestrate M1→M2→M3→M4. The Coupling Layer adds inputs but does not change the layer ordering.

### 3.3 The MelodicProfile-Driven Genre System

Genres are not labels; they are structured profiles that parameterize every decision in the melody pipeline.

```python
# src/yao/schema/melodic_profile.py

class MelodicProfile(BaseModel):
    """Genre-specific parameters for melody generation."""
    genre: str
    description: str
    scale_preferences: dict[str, float]
    interval_distribution: IntervalDistribution
    chord_tone_targeting: float          # 0.0–1.0
    chromaticism_level: float            # 0.0–1.0
    syncopation_level: float             # 0.0–1.0
    phrase_length_distribution: PhraseLengthDistribution
    cadence_patterns: list[CadencePattern]
    rhythm_templates: list[RhythmTemplate]
    ornament_profile: OrnamentProfile
    typical_ranges: dict[str, tuple[str, str]]
    motif_length_bars: float
    motif_recurrence_rate: float
    motif_transformations: dict[str, float]
    groove_profile_name: str
    anti_patterns: list[AntiPattern]

    # Extended profile fields
    melody_markov_model: str | None        # e.g. "bebop_3gram"
    melody_markov_temperature: float = 0.7
    melody_markov_stickiness: float = 0.6
    rhythm_markov_model: str | None        # e.g. "jazz_swing_8th"
    harmonic_system: HarmonicSystem = HarmonicSystem.FUNCTIONAL
    reharmonization_intensity: float = 0.0
    modulation_preferences: ModulationPreferences | None = None
    polyrhythm_default: PolyrhythmConfig | None = None
    idiomatic_gesture_intensity: float = 0.5
    coupling_style: CouplingStyle = CouplingStyle.COMMON_PRACTICE
```

YaO ships with **30+ genre profiles** organized in three tiers.

Profiles are **composable**. A user can specify:

```yaml
genre:
  primary: bebop_jazz
  secondary: lofi_hiphop
  blend_ratio: 0.7
```

`blend_profiles(primary, secondary, ratio)` produces a weighted average of all distributions and scalar parameters. This generalizes to **n-way blending** through the Genre Vector Space (Section 3.4.4).

### 3.4 The Combination Stack

The Combination Stack is the architectural answer to the seven bottlenecks identified in `IMPROVEMENT.md`. It is a set of seven cooperating modules in the Combination & Coupling layer that turn YaO's rich material library into deeply diverse output.

```
                      ┌──────────────────────────────────────┐
                      │   Composer / Harmony Theorist /      │
                      │   Rhythm Architect (Subagents)       │
                      └──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
  ┌─────────────────────┐                            ┌─────────────────────┐
  │ Phrase Plan (M1)    │                            │ Chord Progression   │
  │ Motif Library       │                            │ + Cadences          │
  └─────────────────────┘                            └─────────────────────┘
            │                                                     │
            ▼                                                     ▼
  ┌────────────────────────────────────────────────────────────────────┐
  │                   COMBINATION & COUPLING LAYER                     │
  │                                                                    │
  │  3.4.1  Harmonic-Melodic Coupling   ◄──────  3.4.2  Voice Leading │
  │         (HarmonicMelodyConstraints)                Optimizer       │
  │                                                                    │
  │  3.4.3  Reharmonization & Modulation Engine                        │
  │                                                                    │
  │  3.4.4  Genre Vector Space (blending, interpolation)               │
  │                                                                    │
  │  3.4.5  Rhythm Markov Pipeline (parallel to M2-M3)                 │
  │                                                                    │
  │  3.4.6  Theme Recurrence Graph (long-form coherence)               │
  │                                                                    │
  │  3.4.7  Listening-Agent Dialog (turn-based generation)             │
  └────────────────────────────────────────────────────────────────────┘
            │
            ▼
  ┌─────────────────────┐
  │ Skeleton (M2) →     │ ──► Melody Line (M3) ──► Ornamented (M4) ──► ScoreIR
  │ Voice-Led Voicings  │
  └─────────────────────┘
```

#### 3.4.1 Harmonic-Melodic Coupling (`yao.coupling.harmonic_melody`)

**Purpose**: Resolve bottleneck B2 (melody–harmony decoupling). Make every melody-pitch decision conditional on the chord active at that metric position.

**Inputs**: A `ChordProgression` with `ChordEvent`s, a `MelodicProfile`, the active `CouplingStyle`.

**Output**: A `HarmonicMelodyConstraints` object per metric position.

```python
# src/yao/ir/harmonic_melody_constraints.py

@dataclass(frozen=True)
class HarmonicMelodyConstraints:
    chord_tones: tuple[MidiNote, ...]
    available_extensions: tuple[MidiNote, ...]
    avoid_notes: tuple[MidiNote, ...]
    target_resolutions: dict[MidiNote, MidiNote]
    style: CouplingStyle

    def score_pitch(self, pitch: MidiNote, position: PositionLabel) -> float:
        """0.0 = serious clash; 1.0 = excellent fit."""
        ...
```

`CouplingStyle` enumerates how strictly the coupling is enforced and which avoidance rules apply:

- `COMMON_PRACTICE` — classical voice leading, P4-over-major-triad penalized on strong beats
- `JAZZ` — extensions favored, 11-over-V7 penalized, blue notes neutral
- `BLUES` — b3, b5, b7 are blue notes, not avoid notes
- `MODAL` — no avoid notes; all scale tones equal
- `RAGA` / `MAQAM` — pitch hierarchy from `TonalSystem.cadence_strength`

Layer M2 of the melody pipeline now calls `derive_constraints(chord, key, profile, style)` for every skeleton-note candidate and combines the score with the existing `chord_tone_targeting` weight.

This single change is, per `IMPROVEMENT.md`, the **largest single quality win** available to YaO.

#### 3.4.2 Voice-Leading Optimizer (`yao.coupling.voice_leading`)

**Purpose**: Resolve the half-implementation noted in B4. Voice-leading **detection** exists; the optimizer adds **optimization** during chord realization.

**Inputs**: A previous voicing, a target `ChordFunction`, voice count, `VoicingConstraints`.

**Output**: An optimized voicing that minimizes total voice motion subject to constraints (no parallel 5ths/8ves, no voice crossing, range-respecting, octave-leap-avoiding).

**Algorithm**: Hungarian assignment over inversions for small voice counts; dynamic programming over consecutive chords for full progressions.

```python
def optimal_voicing_transition(
    prev_voicing: list[MidiNote],
    next_chord: ChordFunction,
    voice_count: int = 4,
    constraints: VoicingConstraints = ...,
) -> list[MidiNote]: ...
```

The Orchestrator subagent calls this for every harmonic instrument. The result is Bach-chorale-grade voicings rather than naive root-position chords.

#### 3.4.3 Reharmonization & Modulation Engine (`yao.coupling.reharmonization`, `yao.coupling.modulation`)

**Purpose**: Resolve B4 fully. The base chord cycling becomes one starting point; reharmonization and modulation produce harmonic motion beyond what the basic stochastic generator can achieve.

**Reharmonization operations** (12 in total):

```python
class ReharmonizationOperation(StrEnum):
    SECONDARY_DOMINANT = "secondary_dominant"       # I → V/ii → ii
    TRITONE_SUBSTITUTION = "tritone_substitution"   # V7 → bII7
    DIATONIC_SUBSTITUTION = "diatonic_substitution" # I → iii
    MODAL_INTERCHANGE = "modal_interchange"         # IV → iv
    EXTENSION_ADD = "extension_add"
    SUS_CHORD = "sus_chord"
    CHROMATIC_APPROACH = "chromatic_approach"
    II_V_INSERTION = "ii_V_insertion"
    BACKDOOR_PROGRESSION = "backdoor"
    NEAPOLITAN = "neapolitan"
    AUGMENTED_SIXTH = "augmented_sixth"
    COLTRANE_CHANGES = "coltrane_changes"
```

Each operation is a function `(progression, position) → progression` with style-specific applicability rules. A `ReharmonizationConstraints` object protects the existing melody — operations that would introduce intolerable melody-chord clashes are filtered out before application.

**Modulation strategies** (7 in total):

```python
class ModulationStrategy(StrEnum):
    PIVOT_CHORD = "pivot_chord"
    DIRECT = "direct"
    CHROMATIC = "chromatic"
    SEQUENTIAL = "sequential"
    ENHARMONIC = "enharmonic"
    COMMON_TONE = "common_tone"
    THIRD_RELATION = "third_relation"
```

The `ModulationPlanner` subagent runs in Phase 5 of the cognitive protocol; the result populates the previously empty `HarmonyPlan.modulations` field.

Genre-specific preferences (for example, cinematic music heavily uses `THIRD_RELATION` per Wagner/Williams convention) live in each genre profile under `modulation_preferences`.

#### 3.4.4 Genre Vector Space (`yao.coupling.genre_vector`)

**Purpose**: Resolve B5 (genre as exclusive label). Embed each genre profile as a point in a 12–16 dimensional feature space so that genres can be **blended, interpolated, contrasted, and queried by neighbors**.

```python
@dataclass(frozen=True)
class GenreVector:
    coordinates: tuple[float, ...]    # 12–16 dims
    component_genres: dict[str, float] = field(default_factory=dict)

    @classmethod
    def blend(cls, *weighted: tuple[GenreProfile, float]) -> GenreVector: ...

    def nearest_neighbors(self, registry: GenreRegistry, k: int = 3) -> list[GenreProfile]: ...

    def to_melodic_profile(self) -> MelodicProfile: ...
```

Dimensions include `swing_ratio`, `syncopation_density`, `chord_complexity`, `chord_extension_avg`, `rhythmic_subdivision`, `dynamic_range`, `timbral_brightness`, `instrumental_density`, `melodic_chromaticism`, `phrase_length_avg`, `tempo_typical`, `structural_repetition`, `microtonality`, `polyrhythm_intensity`.

Specs may now use:

```yaml
genre_blend:
  - {profile: bossa_nova, weight: 0.6}
  - {profile: drum_n_bass, weight: 0.3}
  - {profile: cinematic, weight: 0.1}
```

The result is a single synthesized `MelodicProfile`. Discrete fields (instruments, chord palette) use weighted random selection; numeric fields interpolate linearly. The original 2-way `blend_profiles()` becomes a special case.

#### 3.4.5 Rhythm Markov Pipeline (`yao.coupling.rhythm_markov`)

**Purpose**: Resolve B1 and B7 (static rhythm pools, shallow rhythm structure). Run n-gram Markov models over a 16th-note grid alongside the existing template-based rhythm system, with the model selected via the active `MelodicProfile.rhythm_markov_model`.

The state space is small enough (`2^N positions × bar position`) that 4-gram smoothed models are practical:

```yaml
# src/yao/generators/markov_models/rhythm/jazz_swing_8th.yaml
metadata:
  name: jazz_swing_8th
  n_gram_order: 4
  resolution: 16th
  swing_ratio: 0.67
  source: "Hand-derived from common bebop figures (Levine 1995)"
transitions:
  "0,000": {onset: 0.92, rest: 0.08}
  "2,100": {onset: 0.40, rest: 0.60}
  ...
```

The `RhythmMarkovGenerator` is registered alongside `phrase_aware` and is used by Layer M3 when the active profile selects it. The existing static template path remains valid; both coexist.

A parallel **Polyrhythm Engine** (`yao.coupling.polyrhythm`) generates polyrhythmic textures (3:4, 4:5, 7:5, hemiola, Yoruba phase-shifts, Afrobeat interlock) when `polyrhythm_default` is enabled in the genre profile.

#### 3.4.6 Theme Recurrence Graph (`yao.coupling.theme_recurrence`)

**Purpose**: Resolve B3 partially. Long-form pieces require thematic returns with transformation; without this, a 2-minute piece sounds like four separate 30-second pieces glued together.

```python
@dataclass(frozen=True)
class ThemeRecurrence:
    source_section: str
    source_bars: tuple[int, int]
    target_section: str
    target_bars: tuple[int, int]
    transformation: MotifTransformation
    transformation_params: dict[str, Any]

@dataclass(frozen=True)
class ThemeRecurrenceGraph:
    edges: tuple[ThemeRecurrence, ...]
```

Auto-generated by `plan_theme_recurrences(form, motifs)` according to song-form conventions:

- **AABA** — A theme appears 3 times (identity, identity, ornamented variation)
- **Sonata** — exposition → fragmentation/sequence in development → transposed recapitulation
- **Rondo** — A returns multiple times, each slightly varied
- **Through-composed** — themes only transform, never literally recur

The existing `recall_melody_from` field in `SectionSpec` becomes one edge type within this richer graph.

The companion **PhraseShape Generator** (`yao.coupling.phrase_shape`) handles intra-section structure (8-bar period, 8-bar sentence, 12-bar blues, 16-bar ballad).

#### 3.4.7 Listening-Agent Dialog (`yao.coupling.listening_dialog`)

**Purpose**: Resolve B6 (independent per-instrument generation). Replace parallel per-instrument generation with **turn-based generation**, where later instruments respond to what earlier instruments have already played.

```python
class ListeningGenerator(ABC):
    def generate_next_phrase(
        self,
        own_history: list[Note],
        ensemble_history: dict[str, list[Note]],
        current_chord: ChordFunction,
        section: SectionSpec,
    ) -> list[Note]: ...
```

The role-priority order for generation:

```
bass → drums → harmony → melody_primary → melody_secondary → fills
```

Each follower agent receives the leader's notes as input and may react: *complement*, *echo*, *syncopate against*, *fill the gap*. The `RhythmicDialogGraph` (in IR) records the causal edges.

This is the most architecturally invasive change and is gated behind a feature flag (`features.listening_agents: true`). The parallel-generation path remains valid for users who do not enable it.

A companion `IdiomaticGesture` library (in `src/yao/constants/idiomatic_gestures/*.yaml`) provides per-instrument body-language patterns (violin trills, sax altissimo, sitar meend, shakuhachi mura-iki) that the M4 ornament layer applies based on instrument and genre.

### 3.5 Layer Interaction Diagram

To make the relationships explicit, here is how the layers interact during a single `compose` call:

```
[ Layer 1: spec parsing ]
         │
         ▼
[ Layer 2: phrase_aware generator initialized ]
         │
         ├─► Layer 0: load MelodicProfile, GenreVector, MarkovModels, Devices
         │
         ▼
[ M1: Phrase plan + motif germs ]
         │
         ▼
[ Harmony Theorist generates ChordProgression ]
         │
         ▼
[ 3.4.6 Theme Recurrence Graph ]
         │
         ▼
[ 3.4.3 Reharmonization & Modulation Engine ]        (opt-in)
         │
         ▼
[ 3.4.1 Harmonic-Melodic Coupling ─► Constraints ]
         │
         ▼
[ M2: Skeleton — constrained by 3.4.1 ]
         │
         ▼
[ 3.4.2 Voice-Leading Optimizer ─► voicings ]
         │
         ▼
[ 3.4.5 Rhythm Markov / 3.4.6 PhraseShape ]          (opt-in)
         │
         ▼
[ M3: Surface realization ]
         │
         ▼
[ 3.4.7 Listening-Agent Dialog reorders generation ]  (opt-in)
         │
         ▼
[ M4: Ornament + IdiomaticGestures ]
         │
         ▼
[ Layer 6: evaluate, including new metrics ]
```

Every Combination-Stack module is **opt-in via feature flag or genre profile setting**. The default configuration enables Sections 3.4.1, 3.4.2, and 3.4.6 (the P0/P1 wins) and leaves the others off until they are validated.

---

## 4. Directory Structure

The directory layout includes the Combination Stack and its supporting data files.

```
yao/
├── CLAUDE.md
├── PROJECT.md
├── IMPROVEMENT.md
├── README.md
├── pyproject.toml
├── Makefile
├── uv.lock
│
├── .claude/
│   ├── commands/
│   │   ├── compose.md
│   │   ├── arrange.md
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md
│   │   ├── explain.md
│   │   ├── regenerate-section.md
│   │   ├── sketch.md
│   │   ├── reharmonize.md                             │   │   ├── modulate.md                                │   │   ├── blend-genres.md                            │   │   └── render.md
│   ├── agents/
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   ├── modulation-planner.md                      │   │   └── producer.md
│   ├── skills/
│   │   ├── genres/                                    # 30+ paired md/yaml files
│   │   ├── theory/
│   │   │   ├── voice-leading.md
│   │   │   ├── reharmonization.md                     │   │   │   ├── modulation.md                          │   │   │   ├── counterpoint.md
│   │   │   ├── modal-interchange.md
│   │   │   ├── phrase-structure.md
│   │   │   └── cadence-design.md
│   │   ├── instruments/
│   │   │   └── idiomatic-gestures.md                  │   │   └── psychology/
│   ├── guides/
│   │   ├── architecture.md
│   │   ├── coding-conventions.md
│   │   ├── music-engineering.md
│   │   ├── melody-pipeline.md
│   │   ├── genre-profiles.md
│   │   ├── combination-stack.md                       │   │   ├── chord-aware-melody.md                      │   │   ├── voice-leading-optimizer.md                 │   │   ├── reharmonization-engine.md                  │   │   ├── genre-vector-space.md                      │   │   ├── rhythm-markov.md                           │   │   ├── listening-agents.md                        │   │   ├── testing.md
│   │   └── workflow.md
│   └── hooks/
│
├── specs/
│   ├── projects/
│   ├── templates/
│   │   ├── ...
│   │   ├── jazz-blend-cinematic.yaml
│   │   └── reharmonization-demo.yaml                  │   └── fragments/
│
├── src/
│   ├── yao/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── types.py
│   │   ├── constants/
│   │   │   ├── instruments.py
│   │   │   ├── scales.py
│   │   │   ├── chords.py
│   │   │   ├── dynamics.py
│   │   │   ├── midi.py
│   │   │   ├── melodic_profiles/
│   │   │   ├── rhythms/
│   │   │   ├── grooves.py
│   │   │   ├── harmonic_devices/
│   │   │   └── idiomatic_gestures/
│   │   ├── schema/
│   │   │   ├── composition.py
│   │   │   ├── trajectory.py
│   │   │   ├── constraints.py
│   │   │   ├── negative_space.py
│   │   │   ├── references.py
│   │   │   ├── production.py
│   │   │   ├── melodic_profile.py
│   │   │   ├── genre_blend.py
│   │   │   └── features.py
│   │   ├── ir/
│   │   │   ├── score_ir.py
│   │   │   ├── note.py
│   │   │   ├── motif.py
│   │   │   ├── voicing.py
│   │   │   ├── harmony.py
│   │   │   ├── timing.py
│   │   │   ├── notation.py
│   │   │   ├── phrase.py
│   │   │   ├── skeleton.py
│   │   │   ├── melody_line.py
│   │   │   ├── harmonic_context.py
│   │   │   ├── harmonic_melody_constraints.py
│   │   │   ├── phrase_shape.py
│   │   │   ├── theme_recurrence.py
│   │   │   ├── genre_vector.py
│   │   │   ├── polyrhythm.py
│   │   │   ├── rhythm_event.py
│   │   │   └── motif_network.py
│   │   ├── coupling/
│   │   │   ├── __init__.py
│   │   │   ├── harmonic_melody.py
│   │   │   ├── voice_leading.py
│   │   │   ├── reharmonization.py
│   │   │   ├── modulation.py
│   │   │   ├── genre_vector.py
│   │   │   ├── rhythm_markov.py
│   │   │   ├── polyrhythm.py
│   │   │   ├── theme_recurrence.py
│   │   │   ├── phrase_shape.py
│   │   │   ├── listening_dialog.py
│   │   │   └── idiomatic_gestures.py
│   │   ├── generators/
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── rule_based.py
│   │   │   ├── stochastic.py
│   │   │   ├── markov_v2.py
│   │   │   ├── rhythm_markov.py
│   │   │   ├── polyrhythm.py
│   │   │   ├── markov_models/
│   │   │   │   ├── pitch/
│   │   │   │   ├── rhythm/
│   │   │   │   └── contour/
│   │   │   └── melody/
│   │   ├── perception/
│   │   ├── render/
│   │   ├── verify/
│   │   │   ├── music_lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py
│   │   │   ├── diff.py
│   │   │   ├── constraints.py
│   │   │   ├── genre_critic.py
│   │   │   ├── conformity.py
│   │   │   ├── memorability.py
│   │   │   ├── melody_harmony_alignment.py
│   │   │   ├── voice_leading_smoothness.py
│   │   │   └── polyrhythm_coherence.py
│   │   ├── reflect/
│   │   └── conductor/
│   └── cli/
│
├── references/
├── outputs/
├── soundfonts/
├── tests/
│   ├── unit/
│   │   ├── coupling/
│   │   │   ├── test_harmonic_melody.py
│   │   │   ├── test_voice_leading.py
│   │   │   ├── test_reharmonization.py
│   │   │   ├── test_modulation.py
│   │   │   ├── test_genre_vector.py
│   │   │   ├── test_rhythm_markov.py
│   │   │   ├── test_theme_recurrence.py
│   │   │   ├── test_phrase_shape.py
│   │   │   └── test_listening_dialog.py
│   │   ├── ir/
│   │   ├── generators/
│   │   ├── schema/
│   │   ├── verify/
│   │   ├── conductor/
│   │   └── reflect/
│   ├── integration/
│   ├── music_constraints/
│   ├── scenarios/
│   │   ├── test_chord_aware_melody.py
│   │   ├── test_voice_leading_quality.py
│   │   ├── test_reharmonization_diversity.py
│   │   ├── test_genre_blend_output.py
│   │   └── test_listening_agent_dialog.py
│   ├── golden/
│   └── helpers.py
├── tools/
│   ├── architecture_lint.py
│   ├── extract_groove.py
│   └── learn_markov_from_corpus.py
└── docs/
    ├── design/
    │   ├── 0010-chord-aware-melody.md
    │   ├── 0011-voice-leading-optimizer.md
    │   ├── 0012-reharmonization-engine.md
    │   ├── 0013-genre-vector-space.md
    │   ├── 0014-rhythm-markov-pipeline.md
    │   ├── 0015-listening-agents.md
    │   └── 0016-theme-recurrence.md
    ├── tutorials/
    ├── reference/
    └── glossary.md
```

---

## 5. The Orchestra: Subagent Design

Subagent responsibilities include consuming Combination-Stack outputs. Below are the subagents and their roles.

### 5.1 Composer

- **Responsibility**: Generate the phrase plan, motifs, and primary melodic line via the 4-layer melody pipeline
- **Inputs**: `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`, the active `MelodicProfile` (possibly a blended `GenreVector`), the `ThemeRecurrenceGraph`, and `HarmonicMelodyConstraints` from the Coupling Layer
- **Outputs**: Score IR containing `PhrasePlan`, `Skeleton` (now constrained), `MelodyLine`, `OrnamentedMelodyLine`
- **Forbidden**: Instrument selection and final voicing (Orchestrator's domain)
- **Pipeline ownership**: Owns Layer M1 and orchestrates calls to M2–M4
- **Evaluation axes**: Motif memorability, balance of repetition and variation, fidelity to the trajectory, motif coherence ≥ 0.5, melody–harmony alignment ≥ 0.7

### 5.2 Harmony Theorist

- **Responsibility**: Design chord progressions, modulations, secondary chords, cadences; supply `HarmonicContext` for each metric position
- **Inputs**: Composer's phrase plan, `composition.yaml` harmony section, the genre's `cadence_patterns`, and `modulation_preferences`
- **Outputs**: A complete chord progression IR; per-beat `HarmonicContext`; a populated `HarmonyPlan.modulations`
- **Critical role**: The Composer's M2 cannot run without `HarmonicContext`, AND the Coupling Layer's `derive_constraints()` cannot run without it
- **Evaluation axes**: Functional consistency, tension resolution, genre fit, voice-leading smoothness, modulation appropriateness

### 5.3 Rhythm Architect

- **Responsibility**: Design drum patterns, grooves, syncopation, fills; provide `GrooveProfile`
- **Inputs**: `composition.yaml` rhythm section, the genre's `rhythm_templates`, `groove_profile`, `rhythm_markov_model`, `polyrhythm_default`
- **Outputs**: Rhythm IR (placement for all instruments), the active `GrooveProfile`, `PolyrhythmTexture` when enabled
- **Evaluation axes**: Groove, human feel, contrast between sections, swing-ratio fidelity, polyrhythm coherence when enabled

### 5.4 Orchestrator

- **Responsibility**: Assign instruments, decide voicings, manage range placement, design countermelodies
- **Inputs**: Outputs from Composer, Harmony, and Rhythm
- **Outputs**: Complete Score IR with all parts assigned; voicings produced by the Voice-Leading Optimizer
- **Evaluation axes**: Frequency-space collision avoidance, idiomatic instrument use, textural density, voice-leading smoothness ≥ 0.75

### 5.5 Adversarial Critic

- **Responsibility**: Discover and report every weakness — never praises
- **Inputs**: Any generated artifact; the genre's `anti_patterns` list; the active `CouplingStyle` for context-appropriate critique
- **Outputs**: `critique.md` with severity-rated issues; structured fix suggestions
- **Genre specialization**: Each genre Skill provides anti-pattern definitions; the Critic loads via `GenreCritic`
- **Critique categories include**: melody–harmony alignment, voice-leading violations, reharmonization-melody clashes, genre-blend incoherence, listening-dialog conversational flow

### 5.6 Mix Engineer

- **Responsibility**: Stereo placement, dynamics, frequency masking, loudness
- **Inputs**: Orchestrator's output + production parameters
- **Outputs**: Mix instructions
- **Evaluation axes**: LUFS target, frequency balance, stereo width

### 5.7 Modulation Planner

- **Responsibility**: Plan key modulations across the piece per the trajectory, song form, and genre preferences
- **Inputs**: `composition.yaml`, `trajectory.yaml`, active `MelodicProfile.modulation_preferences`
- **Outputs**: A `ModulationPlan` consumed by the Harmony Theorist when populating `HarmonyPlan.modulations`
- **Evaluation axes**: Voice leading at modulation points, distance-from-tonic appropriateness, conventional vs. distant modulation per genre

### 5.8 Producer

- **Responsibility**: Overall integration, prioritization, dialogue with the human, final decisions
- **Inputs**: All subagent outputs + human feedback + Critic's reports
- **Outputs**: Final production decisions, instructions for the next iteration
- **Privilege**: The only subagent that can reject or send back another's output
- **Evaluation axes**: Fidelity to `intent.md`, balanced integration

---

## 6. The 6-Phase Compositional Cognitive Protocol

The `/compose` and `/arrange` commands force Claude Code to execute six phases **in order**. Combination-Stack steps are integrated into Phases 3 and 5.

### Phase 1: Intent Crystallization

Parse user input into a `StructuredIntent` and articulate the essence of the piece in 1–3 sentences. Commit to `intent.md`. The intent parser produces multi-dimensional emotional and stylistic vectors.

### Phase 2: Architectural Sketch

Draw the time-axis trajectories first. Select or blend the appropriate `MelodicProfile`. Complete `trajectory.yaml`. When `genre_blend` is specified, compute the blended `GenreVector` and project to a synthesized profile.

### Phase 3: Skeletal Generation

The Composer produces 5–10 candidate phrase plans + motif germs. Simultaneously, the Modulation Planner drafts a `ModulationPlan`, the Theme Recurrence Graph is computed, and the Harmony Theorist drafts the chord progression. The Coupling Layer derives `HarmonicMelodyConstraints` for each candidate.

### Phase 4: Critic-Composer Dialogue

The Adversarial Critic attacks all candidates with universal and genre-specific anti-patterns (including melody–harmony alignment violations and reharmonization clashes). The Producer judges and selects the strongest candidate, or commissions a hybrid.

### Phase 5: Detailed Filling

The chosen phrase plan flows through M2 → M3 → M4. M2 consumes `HarmonicMelodyConstraints`, the Voice-Leading Optimizer produces voicings, the Rhythm Markov pipeline (or static templates) realizes rhythm, the Reharmonization Engine optionally enriches harmony, and Listening-Agent Dialog (when enabled) runs in turn-based order.

### Phase 6: Listening Simulation

The Perception Substitute Layer "listens" to the finished piece. It computes melody–harmony alignment, voice-leading smoothness, and polyrhythm coherence alongside other scores. Out-of-range scores trigger targeted regeneration.

---

## 7. Parameter Specifications

YaO fully describes a piece using **11 files**. All are version-controlled.

### 7.1 `intent.md` — Natural-language intent

Free-form prose stating the essence in 1–3 sentences.

### 7.2 `composition.yaml` — Composition parameters

Key, mode, tempo, time signature, form, genre (single or blended), instrumentation, sections.

```yaml
title: "Rainy Cafe"
key: "D minor"
mode: "natural_minor"
tempo_bpm: 90
time_signature: "4/4"

# either genre.primary/secondary/blend_ratio, OR genre_blend list
genre_blend:
  - {profile: lofi_hiphop, weight: 0.6}
  - {profile: jazz_modal, weight: 0.3}
  - {profile: cinematic, weight: 0.1}

instruments:
  - {name: piano, role: melody}
  - {name: cello, role: bass}
  - {name: drums, role: rhythm}

sections:
  - {name: intro, bars: 4, dynamics: pp}
  - {name: verse, bars: 8, dynamics: mp}
  - {name: chorus, bars: 8, dynamics: f}
  - {name: outro, bars: 4, dynamics: pp}

generation:
  strategy: phrase_aware
  seed: 42
  temperature: 0.5

# feature flags
features:
  chord_aware_melody: true
  voice_leading_optimization: true
  reharmonization: false
  modulation_planner: false
  listening_agents: false
  genre_blend: true
  rhythm_markov: false
  polyrhythm: false
  theme_recurrence: true
```

### 7.3 `trajectory.yaml` — Time-axis trajectories

Tension, density, valence, predictability over time.

### 7.4 `references.yaml` — Aesthetic reference library

Positive and negative reference works.

### 7.5 `negative-space.yaml` — Negative space

What is *not* played.

### 7.6 `arrangement.yaml` — Arrangement parameters (arrangement only)

### 7.7 `production.yaml` — Mix and mastering

### 7.8 `melodic-profile.override.yaml` — Optional profile overrides

### 7.9 `harmonic-devices.yaml` — Harmonic device selection

```yaml
devices:
  - {name: jazz_turnaround_I_VI_II_V, placement: section_end, sections: [verse, chorus]}
  - {name: gospel_walkup, placement: intro_to_verse, sections: [intro]}
  - {name: coltrane_giant_steps_cycle, placement: bridge, sections: [bridge]}

reharmonization:
  intensity: 0.4
  preserve_melody: true
  operations:
    - secondary_dominant
    - tritone_substitution
    - ii_V_insertion
```

### 7.10 `modulation-plan.yaml` — Modulation specifications

```yaml
modulations:
  - bar: 32
    from_key: "D minor"
    to_key: "F major"
    strategy: pivot_chord
    pivot_chord: "F"
  - bar: 48
    from_key: "F major"
    to_key: "D minor"
    strategy: direct
```

### 7.11 `provenance.json` — Append-only generation history

Auto-generated. Records every decision at every layer (M1–M4 + Coupling Layer modules). Queryable via `/explain`.

---

## 8. Custom Commands

| Command | Purpose | Primary subagents |
|---|---|---|
| `/compose <project>` | Generate a new piece | Composer → all |
| `/arrange <project>` | Arrange an existing piece | Orchestrator + Critic |
| `/critique <iteration>` | Critique an artifact | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate two musical states | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment | Composer + Rhythm |
| `/explain <element>` | Trace generation decisions | Producer (provenance) |
| `/diff <iter_a> <iter_b>` | Show musical diff | Verifier |
| `/render <iteration>` | MIDI to audio + score | Mix Engineer |
| `/sketch` | Sketch-to-spec dialogue | Producer + intent parser |
| `/conduct "<description>"` | Full agentic pipeline from natural language | All |
| `/reharmonize <iteration> <intensity>` | Apply reharmonization to existing piece | Harmony Theorist + Critic |
| `/modulate <iteration> <bar> <to_key>` | Add a modulation | Modulation Planner + Harmony |
| `/blend-genres <genres...>` | Generate using a genre blend | Composer (with `GenreVector`) |

---

## 9. Skills

### 9.1 Genre Skills (30+)

Each genre Skill consists of:

- A Markdown file with overview, historical context, characteristic features (form, tempo, harmony, melody, rhythm, instrumentation, production), anti-patterns, required reference works, implementation hints, related genres, sub-style notes, and music-theoretical citations
- A YAML companion with a complete `MelodicProfile` (including `melody_markov_model`, `rhythm_markov_model`, `harmonic_system`, `modulation_preferences`, `polyrhythm_default`, `idiomatic_gesture_intensity`, `coupling_style`)
- A reference catalog entry in `references/catalog.yaml`
- A scenario test in `tests/scenarios/test_<genre>.py`

Adding a new genre requires all four artifacts.

### 9.2 Theory Skills

Harmony, counterpoint, reharmonization, modulation, modal interchange, phrase structure, cadence design.

### 9.3 Instrument Skills

Per-instrument range, idiomatic playing techniques, timbre, physical constraints, characteristic phrase patterns. `idiomatic-gestures.md` documents the `IdiomaticGesture` library and how the M4 layer applies it.

### 9.4 Psychology Skills

Empirical mappings from music psychology (Juslin, Huron, Krumhansl). Includes `intent-parsing.md`.

---

## 10. Hooks

| Hook | Timing | Action |
|---|---|---|
| `pre-commit-lint` | Before `git commit` | Music21 lint, YAML schema validation, melodic profile validation, architecture lint |
| `post-generate-render` | After generation | Auto-render MIDI to audio and score |
| `post-generate-critique` | After generation | Always invoke Adversarial Critic with genre specialization |
| `update-provenance` | After any change | Update Provenance Graph |
| `genre-skill-validate` | When `.claude/skills/genres/*.md` changes | Verify paired YAML, schema, anti-patterns |
| `coupling-stack-validate` | When `src/yao/coupling/*.py` changes | Coupling layer import-direction lint, feature-flag presence check |
| `markov-model-validate` | When `markov_models/**/*.yaml` changes | Schema validation, license attribution check, distribution sanity check |

---

## 11. Layer-Specific Sub-Architectures

### 11.1 The Constraint System

Constraints are scoped rules with severity. Defined inline in `composition.yaml`:

```yaml
constraints:
  - {type: must_not, rule: parallel_fifths, scope: global, severity: error}
  - {type: must_not, rule: "note_above:C6", scope: "instrument:piano", severity: warning}
  - {type: prefer, rule: "max_density:4", scope: "section:intro", severity: hint}
```

### 11.2 The Provenance Graph

`provenance.json` is append-only. Every entry records timestamp, layer, decision, input, output, rationale, agent. `caused_by` edges form a causal DAG queryable via `get_causes`/`get_effects`/`trace_ancestry`, covering all Coupling-Stack decisions.

### 11.3 The Intent Parser

```python
@dataclass(frozen=True)
class StructuredIntent:
    valence: float
    arousal: float
    tension: float
    warmth: float
    nostalgia: float
    genre_candidates: list[tuple[str, float]]
    use_case: str
    duration_seconds: float
    loopable: bool
    instruments_mentioned: list[str]
    tempo_hint: str | None
    mood_keywords: list[str]
    raw_description: str
```

The parser uses a hybrid approach: rule-based keyword extraction first, then Claude API call for nuanced interpretation, with confidence-weighted merge.

### 11.4 The Genre Critic

Each genre Skill provides `anti_patterns`; the Critic loads and applies them.

```python
class GenreCritic:
    def critique(self, score: ScoreIR, genre: str) -> CritiqueReport: ...
```

When the Critic flags `critical` issues, the Conductor consults the Skill's fix recipes and adapts the spec before regenerating.

### 11.5 The Combination Stack

The Combination Stack (Section 3.4) is a coordinated set of seven modules in the Combination & Coupling layer. They share three architectural conventions:

1. **All inputs are immutable IR objects.** A coupling module never mutates its inputs.
2. **All outputs are new IR objects with full provenance.** Every decision is recorded with `caused_by` linking back to the input decisions.
3. **All modules are feature-flagged.** Each module checks `composition.features.<flag>` and falls through silently when disabled. The default flags are conservative (only the P0 wins enabled); users opt into experimental modules.

A Coupling-Stack module's import surface is restricted by `arch-lint`: it may import from Layers 0, 1, 2, and other Coupling modules, but not from Layers 3+.

---

## 12. Quality Assurance: Evaluation Metrics

YaO evaluates artifacts across **eleven dimensions**. Scores are saved to `evaluation.json`.

### 12.1 Structural Evaluation
Section contrast, climax position, density-curve fidelity, repetition balance, loopability.

### 12.2 Melodic Evaluation
Range fit, motif memorability, singability, phrase-ending closure, contour variation.

### 12.3 Harmonic Evaluation
Chord function consistency, tension resolution, harmonic complexity vs. parameters, cadence strength.

### 12.4 Arrangement Evaluation
Instrument-role clarity, frequency-collision risk, original-preservation rate (arrangement mode), transformation strength.

### 12.5 Acoustic Evaluation
BPM match, beat stability, LUFS target, spectral balance, onset density.

### 12.6 Genre Conformity
KL divergence vs. target distributions for interval distribution, phrase length, chord-tone targeting, syncopation. Aggregated as `overall_genre_conformity` ≥ 0.7.

### 12.7 Motif Coherence
Quantifies thematic unity through motif recurrence and variation balance. Per-genre target ranges.

### 12.8 Memorability Proxy
Pitch-sequence autocorrelation, contour predictability, average cadence strength.

### 12.9 Melody–Harmony Alignment
For each note, compute the `score_pitch()` of its current chord constraints. Aggregate across the piece. Target: ≥ 0.7 average, ≥ 0.85 on downbeats. This is the metric most closely correlated with subjective "musicality" and is the primary signal that chord-aware melody is working.

### 12.10 Voice-Leading Smoothness
Total voice motion across consecutive chords / theoretical minimum (Hungarian-optimal). Target: ≤ 1.5× minimum for `COMMON_PRACTICE`, ≤ 2.0× for `JAZZ`, ≤ 3.0× for `MODAL`.

### 12.11 Polyrhythm Coherence
When polyrhythm is enabled: each layer's accent pattern should be detectable independently while the ensemble retains a meta-pulse. Computed via cross-correlation of layer accent series. Target: ≥ 0.6.

Each metric has a numeric target and tolerance. Out-of-range values trigger Adversarial Critic intervention.

---

## 13. Development Roadmap

### Completed Work

- **Foundation**: Project structure, MVP skeleton, basic MIDI generation, SoundFont rendering
- **Symbolic Composition**: Parameter-driven composition; rule_based + stochastic generators; Conductor feedback loop; provenance; CLI; constraint system; section regeneration
- **Phrase-First Pipeline**: `MelodicProfile` schema + 5 Tier-1 genre profiles; Phrase/Skeleton/MelodyLine/HarmonicContext IR; 4-layer melody pipeline (M1–M4); `phrase_aware` generator; profile blending; 2978 tests
- **Motif Development**: `MotifDevelopmentPlanner`, `HarmonicMelodicSelector`, `OutlineGenerator`, all 13 motif transformations, motif library persistence

### Active Work — Combination Stack

The Combination Stack is being introduced through a sequence of independently mergeable stages, gated by feature flags and validated by both quantitative and subjective tests.

- **Diversity Foundation** *(active)*
  - **§4.1 Chord-Aware Melody Layer** (`src/yao/coupling/harmonic_melody.py`)
    - Implement `HarmonicMelodyConstraints` IR
    - Implement `derive_constraints()` with the 5 `CouplingStyle` profiles
    - Wire into Layer M2 (`SkeletonGenerator` + `HarmonicMelodicSelector`)
    - `feature.chord_aware_melody` flag (default ON)
    - Acceptance: melody–harmony alignment ≥ 0.7 average across 32-bar pieces
  - **§5.4 Voice-Leading Optimizer** (`src/yao/coupling/voice_leading.py`)
    - Hungarian-assignment voicing transition
    - `VoicingConstraints` schema
    - Wired into Orchestrator subagent
    - Acceptance: voice-leading smoothness ≤ 1.5× minimum for common-practice genres
  - **§5.1 Reharmonization Engine** (`src/yao/coupling/reharmonization.py`)
    - All 12 operations
    - `ReharmonizationConstraints` (melody compatibility)
    - `/reharmonize` slash command
    - Acceptance: reharmonized output passes melody–harmony alignment threshold

- **Genre Diversification** (next)
  - **§4.2 Genre-Specific Markov Models** — 15+ pitch models, 12+ rhythm models, smoothed back-off
  - **§3.1 Rhythm Markov Generator** wired into Layer M3
  - **§5.6 Harmonic Devices Library** — 15+ device YAMLs
  - **§5.2 Modulation Generator** — `ModulationPlanner` subagent
  - Acceptance: per-genre conformity ≥ 0.75 across all 30 profiles; 7+ device categories represented

- **Structural Diversity**
  - **§4.3 Phrase-Shape Generator** — antecedent/consequent, period, sentence, blues, ballad, through-composed
  - **§6.4 Theme Recurrence Graph** — auto-generated from song form
  - **§5.3 Variable Harmonic Rhythm** — per-bar chords-per-bar with trajectory derivation
  - Acceptance: motif coherence in Tier 1 genres reaches profile targets; long-form (>120s) pieces show measurable theme-return structure

- **Cross-Cutting Diversity**
  - **§6.1 Genre Vector Space** — n-way blending, neighbor queries
  - **§4.4 Idiomatic Gestures** — top-5 instruments (violin, piano, sax, trumpet, drums)
  - **§3.2 Polyrhythm Engine** — 3:4, 4:5, 7:5, hemiola, interlock
  - **§3.6 Phrase-Level Fill Arcs** — 7 fill strategies wired by song form
  - Acceptance: genre blends produce profiles distinct from each component; polyrhythm coherence ≥ 0.6 when enabled

- **Advanced Ensemble**
  - **§6.3 Listening Agents** — turn-based generation, opt-in via flag
  - **§6.2 Corpus Learning Pipeline** — `tools/learn_markov_from_corpus.py`
  - **§3.3 Metric Modulation** — ratio-based meter transitions
  - **§4.7 Microtonal Melody** — `tuning_offset_cents` populated by generators, MIDI pitch-bend rendering
  - **§5.5 Non-Functional Harmony** — quartal, quintal, polychord, drone-based
  - **§5.7 Counterpoint Expansion** — 10 counterpoint styles

- **Production Integration**
  - DAW integration (Reaper) — full
  - Live improvisation mode — production-ready
  - User preference learning — Layer 7
  - AI music model bridges (Stable Audio, MusicGen) — neural-seed pipeline

- **Reflection and Learning**
  - Per-user style profiles
  - Community profile sharing standards
  - Adaptive genre profile evolution

### User-Value Milestones

| Milestone | User value | Status |
|---|---|---|
| **1. Describe & Hear** | "Write a description and listen immediately" | ✅ |
| **2. Iterate & Improve** | "Tell it what's wrong; it gets better" | In progress |
| **3. Genre Faithful** | "Sounds like the genre I asked for" | ✅ |
| **4. Coherent Piece** | "Has unity, not just notes" | ✅ |
| **5. Musically Right** | "Melody fits the chords" | **Active** |
| **6. Real Variety** | "Different seeds give genuinely different pieces" | Planned |
| **7. Genre Crossings** | "Bossa-meets-DnB-meets-cinematic actually sounds like that" | Planned |
| **8. Real Groove** | "Feels alive, not robotic" | Planned |
| **9. Long-Form Coherence** | "A 3-minute piece feels unified" | Planned |
| **10. My Style** | "Learns my preferences" | Planned |
| **11. Production Ready** | "Output usable in real projects" | Planned |

---

## 14. Quick Start

### 14.1 Environment Setup

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
```

### 14.2 Natural Language Path

```bash
yao conduct "a calm 90-second piano piece for studying, slightly nostalgic"
```

The intent parser builds a complete spec, the phrase-first pipeline generates with chord-aware melody and voice-leading optimization enabled by default, and evaluation iterates until quality metrics pass.

### 14.3 YAML Path

```bash
make new-project NAME=my-first-song
# Edit specs/projects/my-first-song/composition.yaml
yao compose specs/projects/my-first-song/composition.yaml --strategy phrase_aware
yao render outputs/projects/my-first-song/iterations/v001/full.mid
```

### 14.4 Genre-Blend Path

```bash
yao conduct "bossa-flavored chords with drum and bass rhythm" \
  --blend bossa_nova:0.6,drum_n_bass:0.4
```

The `GenreVector` blender produces a synthesized profile and the resulting piece carries traces of both inputs.

### 14.5 Reharmonization Path

```bash
yao conduct "a simple ballad in C major"
yao reharmonize outputs/projects/.../v001/full.mid --intensity 0.5 --style jazz
```

Reharmonized output preserves the melody and inserts secondary dominants, tritone subs, and ii–V insertions per the chosen intensity.

### 14.6 Interactive Path (Claude Code)

```
> /sketch a mysterious puzzle game BGM, minimal and looping
> /compose my-puzzle-bgm
> /critique my-puzzle-bgm
> /regenerate-section my-puzzle-bgm chorus
> /reharmonize my-puzzle-bgm 0.3
```

---

## 15. File Formats and Interoperability

| Use | Format | Reason |
|---|---|---|
| Music data | MIDI (.mid), MusicXML (.xml) | Industry standard |
| Notation | LilyPond (.ly), PDF | High-quality scores |
| Specs | YAML | Human-readable, git-friendly |
| Intermediate representation | JSON | Machine-readable |
| Provenance | JSON (append-only) | Graph-structured |
| Audio | WAV (production), FLAC/MP3 (distribution) | Standard support |
| Live code | Strudel patterns | Browser-playable |
| Genre profiles | YAML | Composer-readable |
| Markov models | YAML | Composer-auditable |
| Idiomatic gestures | YAML | Composer-readable |
| Harmonic devices | YAML | Composer-readable |
| Motif library | JSON | Reusable, indexable |

Custom formats are avoided. Only what cannot be represented in existing standards is defined minimally.

---

## 16. Ethics and Licensing

### 16.1 Reference Library Licensing
Only rights-cleared works. License status recorded in `references/catalog.yaml`. Corpus-trained Markov models record source, license, and training date.

### 16.2 Artist Imitation
Specifying "in the style of [active artist]" is discouraged. Use abstract feature descriptions or genre profiles.

### 16.3 Cultural Appropriation Protocols
World music genres require source citations, practitioner review, explicit cultural context, and warnings against mass commercial generation when culturally inappropriate. The microtonal pipeline (raga, maqam, gamelan) does not legitimize stripping cultural context.

### 16.4 Generated Work Rights
Rights belong to the user by default. Warning emitted when reference influence is unusually high.

### 16.5 Transparency
Every generated artifact records that it was produced by YaO and lists the aesthetic anchors, genre profiles, active feature flags, blended genre composition, and corpus sources of any used Markov models in `provenance.json`.

---

## 17. Relationship to CLAUDE.md and IMPROVEMENT.md

`CLAUDE.md` contains short, prescriptive operational rules. `PROJECT.md` (this file) contains the full design and philosophy. `IMPROVEMENT.md` contains the audit-derived gap analysis and the priority-ordered improvement list. **Conflict resolution: CLAUDE.md > PROJECT.md > IMPROVEMENT.md > other docs.**

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this file) | Humans + agents | Design, philosophy, architecture |
| `CLAUDE.md` | Agents primarily | Invariant rules, current phase, escalation |
| `IMPROVEMENT.md` | Humans + agents | Gap analysis and priority-ordered improvements |
| `README.md` | Humans | Quick start |
| `docs/design/*.md` | Humans + agents | ADR-style decision records (one per Combination-Stack module) |
| `.claude/guides/*.md` | Agents primarily | Detailed how-to guides |

---

## 18. Future Architectural Extensions

### 18.1 Session Runtime Layer
A `ProjectRuntime` to support iterative production sessions: generation cache, feedback queue, music-level undo/redo.

### 18.2 Abstract Agent Protocol
Backend-agnostic Python protocol so the Claude Code implementation becomes one adapter among many.

### 18.3 Immediate Feedback Path
Inline MIDI playback (`yao preview`), Strudel-based browser preview, direct WAV via `sounddevice`.

### 18.4 Spec Composability
Reusable spec fragments in `specs/fragments/` with `extends:` / `overrides:`.

### 18.5 Adaptive Genre Profile Learning
Layer 7 adapts each user's `MelodicProfile` based on their feedback over time.

### 18.6 Multimodal Input
Hummed audio (transcribed via basic-pitch), uploaded reference MIDI, mood-board images.

### 18.7 Beyond Listening Agents
Continuous Listening Agents — agents that re-evaluate their own decisions when other agents finish, allowing limited backtracking. This breaks current strict turn order; investigate after the basic Listening Agent path stabilizes.

### 18.8 Harmonic Negotiation
A protocol where the Composer and Harmony Theorist iteratively negotiate the chord progression — Composer proposes a melody, Harmony rewrites the chords, Composer revises, etc. Currently the chord progression is fixed before the melody is generated; this opens that decision.

---

## 19. Glossary

**Conductor** — The human who owns the project; final decision-maker.

**Orchestra** — The collective of subagents.

**Score** — The YAML files in `specs/`.

**Score IR** — Implementation-ready intermediate representation.

**Trajectory** — Characteristic curve over time (tension, density, etc.).

**Phrase** — A musical unit with function, target pitch, and cadence.

**PhraseShape** — A planned phrase structure (antecedent/consequent/period/sentence/etc.).

**Motif** — A short melodic-rhythmic idea developed across a piece.

**Skeleton** — Structural pitches anchoring a melody to its harmony.

**MelodyLine** — Realized melody after surface filling.

**OrnamentedMelodyLine** — Expressive surface with ornaments and microtiming.

**MelodicProfile** — Genre-specific parameters governing melody generation.

**HarmonicContext** — Harmonic state at a given metric position.

**HarmonicMelodyConstraints** — Per-position chord-derived rules for melody pitch selection.

**CouplingStyle** — How strict melody-harmony coupling is enforced (common-practice, jazz, blues, modal, raga, maqam).

**GrooveProfile** — Microtiming and velocity offsets characterizing a feel.

**GenreVector** — Multi-dimensional embedding of a genre profile.

**ThemeRecurrenceGraph** — Plan for theme returns and transformations across a piece.

**RhythmEvent** — A rhythmic placement with functional label (downbeat, syncopation, anticipation, hemiola, etc.).

**PolyrhythmTexture** — Multiple rhythmic cycles running simultaneously at different ratios.

**HarmonicDevice** — A genre-typical harmonic gesture (jazz turnaround, gospel walk-up, Coltrane changes, etc.).

**IdiomaticGesture** — An instrument-specific body-language pattern (violin trill, sax altissimo, sitar meend, etc.).

**ListeningAgent** — A generator that produces notes based on what other instruments have already played.

**Combination Stack** — Combination & Coupling layer modules that combine, couple, blend, and dialogue across the existing material library.

**Aesthetic Reference Library** — Reference works as aesthetic anchors.

**Perception Substitute Layer** — Compensates for AI's inability to "hear."

**Provenance** — Traceable record of every generation decision.

**Adversarial Critic** — Critique subagent that deliberately attacks artifacts.

**Genre Critic** — Critic specialized for a specific genre's anti-patterns.

**Negative Space** — Deliberate design of what is not played.

**Style Vector** — Multi-dimensional feature-space representation.

**Iteration** — Versioned generation within a project (`v001`, `v002`, ...).

**Music Lint** — Automatic detection of music-theoretic violations.

**Sketch-to-Spec** — Interactive process from natural-language to YAML spec.

**StructuredIntent** — Multi-dimensional emotional + stylistic vector.

**Genre Conformity** — KL divergence between actual and target distributions.

**Motif Coherence** — Measure of thematic unity through motif recurrence.

**Memorability Proxy** — Estimated melodic memorability from acoustic features.

**Melody–Harmony Alignment** — Average chord-conditioned pitch score across the piece.

**Voice-Leading Smoothness** — Total voice motion / Hungarian-optimal minimum.

**Polyrhythm Coherence** — Cross-correlation-based metric for polyrhythmic textures.

---

## 20. The World YaO Aims For

YaO is not a project where AI makes music. It is **infrastructure for humans and AI to co-create music, each contributing what they do best**.

- Humans contribute **intent, judgment, and sensibility**
- AI contributes **theoretical knowledge, iteration speed, and exhaustive record-keeping**
- YaO is **the place where these are made into a structured collaborative process**

The phrase-first pipeline gives YaO genre-faithful melodies. The Combination Stack turns those melodies into genuinely diverse pieces — across genres (via the Genre Vector Space), across runs (via Markov diversification and listening-agent dialog), across forms (via theme recurrence), and across generations of the same spec (via reharmonization and modulation).

The single goal that unifies every architectural decision:

> **Given any genre or mood, produce a piece that respects the genre, has internal coherence, expresses the user's intent, has melody coupled to harmony, has voice-leading the listener can follow, has thematic returns that feel inevitable rather than mechanical, and varies meaningfully and audibly from one generation to the next — even from the same seed plus a small spec change.**

Great music remains, ultimately, **the expression of a human soul**. YaO aims to make that expression **faster, deeper, more diverse, and more reproducible**.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*

---

**Project: You and Orchestra (YaO)**
*Last updated: 2026-05-08*
