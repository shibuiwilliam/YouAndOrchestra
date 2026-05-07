# PROJECT.md — You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## 0. The Essence of the Project

**You and Orchestra (YaO)** is an **agentic music production environment** that runs on Claude Code. Unlike typical "AI music tools" that emit audio from a single black box, YaO is structured around **multiple AI subagents with distinct roles, conducted by a human (You = Conductor)**.

Every design decision in YaO is subordinate to one proposition:

> **Music production is not a one-off, intuitive activity. It is a reproducible and improvable engineering practice.**

For this reason, YaO treats music as **code, specifications, tests, diffs, and provenance** before treating it as audio files. We call this the **Music-as-Code** philosophy.

YaO does not aim to be the cheapest or fastest music generator. It aims to be the **most musical, most explainable, and most genre-faithful** open music production environment available — the one a serious composer, sound designer, or game audio team would actually use day-to-day.

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

The conductor (You) does not write every note. The conductor's job is to **clarify intent, give direction to the players, make decisions during rehearsal, and ensure the quality of the performance**. YaO brings this division of labor to AI, while leaving every meaningful judgment in the hands of the human.

---

## 2. Design Principles

Every implementation decision in YaO is evaluated against the following **seven non-negotiable principles**. The first five were established at project inception; the last two were added to make reliable melody generation and genre diversity architecturally necessary, not optional.

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

A melody is not a sequence of notes. It is a sequence of **phrases**, each of which has a function (statement, question, answer), a target pitch, and a cadence. Notes are derived from phrase structure, not the reverse. The Phrase-First Pipeline (Section 3.2) is the architectural enforcement of this principle.

### Principle 7: Genre Is a Constellation, Not a Label

A genre is not "scale + chord palette + tempo." It is a **multi-dimensional constellation** of interval distributions, rhythmic patterns, ornament profiles, phrase length conventions, cadence preferences, and idiomatic motif transformations. The `MelodicProfile` (Section 3.3) is the structural representation of this constellation.

---

## 3. Architecture

YaO has three nested architectural levels. Each has independent input/output contracts and is interchangeable and testable.

1. The **7-Layer Macro Architecture** (Section 3.1) governs the entire codebase
2. The **4-Layer Melody Pipeline** (Section 3.2) lives inside Layer 2, structuring how melodies are generated
3. The **MelodicProfile-Driven Genre System** (Section 3.3) parameterizes genre at every layer

### 3.1 The 7-Layer Macro Architecture

```
┌───────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                            │
│   Learning from production history; user preferences;     │
│   style profiles; community-shared profile updates        │
├───────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                          │
│   Music lint, structural/melodic/harmonic/acoustic        │
│   evaluation, score diff, genre-specific adversarial      │
│   critique, motif coherence and genre conformity scoring  │
├───────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                        │
│   MIDI writing, stem export, audio rendering (FluidSynth),│
│   score notation (MusicXML, LilyPond, PDF), live-code     │
│   emission (Strudel)                                      │
├───────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                            │
│   Aesthetic judgment substitutes: reference matching,     │
│   psychology-grounded mappings, style-vector arithmetic   │
├───────────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)                 │
│   ScoreIR, Phrase, Skeleton, MelodyLine, Motif, Voicing,  │
│   Harmony, HarmonicContext, Trajectory                    │
├───────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                              │
│   Pluggable generators (rule_based, stochastic,           │
│   phrase_aware); contains the 4-Layer Melody Pipeline     │
├───────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                    │
│   YAML specs, dialogue input, sketch input, intent        │
│   parsing into StructuredIntent, intent-to-spec building  │
├───────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                        │
│   Instrument ranges, MIDI mappings, scales, chord types,  │
│   dynamics, MelodicProfile registry, RhythmTemplate       │
│   registry, GrooveProfile registry                        │
└───────────────────────────────────────────────────────────┘
```

Layer dependencies flow strictly from bottom to top. Lower layers cannot import from higher ones. This is mechanically enforced by `make arch-lint`, an AST-based import checker.

When you add a new module, the first decision is **which layer does it belong to**. Use these questions:

- Does it only define values? → Layer 0
- Does it parse user input or build a spec from intent? → Layer 1
- Does it generate notes? → Layer 2
- Does it represent musical structure? → Layer 3
- Does it substitute for aesthetic perception? → Layer 4
- Does it produce a consumable output (MIDI, audio, score)? → Layer 5
- Does it evaluate, lint, or critique? → Layer 6
- Does it learn from history? → Layer 7

### 3.2 The 4-Layer Melody Pipeline (within Layer 2)

The single most consequential architectural decision in YaO is the separation of **what a melody is** from **how the notes that realize it are chosen**. This is implemented as a four-layer sub-pipeline within Layer 2.

```
┌─────────────────────────────────────────────────┐
│  Layer M4: Ornament & Articulation              │
│  Grace notes, trills, slides, bends, legato/    │
│  staccato, microtiming offsets, ghost notes     │
├─────────────────────────────────────────────────┤
│  Layer M3: Surface Realization                  │
│  Passing tones, neighbor tones, anticipations,  │
│  appoggiaturas; rhythm template application;    │
│  velocity from dynamics + trajectory            │
├─────────────────────────────────────────────────┤
│  Layer M2: Skeleton Generation                  │
│  Chord-tone targets, voice-leading paths,       │
│  phrase-contour realization, harmonic outlining │
├─────────────────────────────────────────────────┤
│  Layer M1: Phrase & Motif Plan                  │
│  Phrase boundaries, cadence types, motif        │
│  selection and transformation strategy          │
└─────────────────────────────────────────────────┘
```

#### Layer M1: Phrase & Motif Plan

**Purpose**: Define the logical structure of the melody before any pitches are chosen.

**Inputs**: `CompositionSpec`, `Trajectory`, `MelodicProfile`

**Output**: `PhrasePlan`

**Key types** (in `src/yao/ir/phrase.py`):

```python
class PhraseFunction(Enum):
    STATEMENT = "statement"
    QUESTION = "question"
    ANSWER = "answer"
    DEVELOPMENT = "development"
    RECAPITULATION = "recapitulation"
    CODA = "coda"

class CadenceType(Enum):
    AUTHENTIC = "authentic"
    HALF = "half"
    PLAGAL = "plagal"
    DECEPTIVE = "deceptive"
    PHRYGIAN = "phrygian"
    NONE = "none"

@dataclass(frozen=True)
class Phrase:
    start_bar: int
    end_bar: int
    function: PhraseFunction
    cadence: CadenceType
    motif_id: str | None
    motif_transformation: str | None
    target_pitch: int | None
    contour_archetype: str  # 'arch', 'descending', 'wave', 'ascending'

@dataclass(frozen=True)
class PhrasePlan:
    phrases: tuple[Phrase, ...]
    motif_library: dict[str, Motif]
```

**Algorithm**:

1. Determine phrase boundaries from section length and trajectory (genre-typical: classical 4+4, jazz 4+4+4+4, rock 8-bar)
2. Assign each phrase a function (typical A-section: STATEMENT + QUESTION + STATEMENT + ANSWER)
3. Generate 1–3 germ motifs for the entire piece
4. For each phrase, select which motif to use and which transformation to apply
5. Plan cadence locations (major cadences at section boundaries, sub-cadences within sections)

#### Layer M2: Skeleton Generation

**Purpose**: Generate the structural pitches that anchor the melody to the harmony.

**Inputs**: `PhrasePlan`, `HarmonyProgression`, `MelodicProfile`

**Output**: `Skeleton`

**Algorithm**:

1. Fix phrase target pitches first (where each phrase "aims")
2. Working backward from each target, place skeleton notes every beat or two
3. Each skeleton note prefers chord tones of the current chord
4. At chord boundaries, prefer voice-leading-friendly pitches (smooth half-step or whole-step motion to the next chord's tones)
5. Skeleton notes are placed such that the motif contour emerges naturally

This step is responsible for ensuring melody and harmony are **deeply coupled**, not merely co-existing. It is the architectural answer to the question "why does this melody fit these chords?"

#### Layer M3: Surface Realization

**Purpose**: Fill in the surface notes that decorate the skeleton.

**Inputs**: `Skeleton`, `RhythmTemplate`, `MelodicProfile`

**Output**: `MelodyLine`

**Algorithm**:

1. Connect skeleton notes with passing tones (stepwise motion through the genre's preferred scale)
2. Place neighbor tones for embellishment
3. Insert appoggiaturas before strong beats per genre profile
4. Apply the rhythm template for attack positions
5. Use the genre's interval distribution to choose final pitches

#### Layer M4: Ornament & Articulation

**Purpose**: Add the expressive surface that makes a melody feel alive.

**Inputs**: `MelodyLine`, `OrnamentProfile`, `GrooveProfile`

**Output**: `OrnamentedMelodyLine`

**Algorithm**:

1. Apply genre-specific ornaments (grace notes, trills, slides, bends) per the ornament profile
2. Distribute articulations (legato vs. staccato vs. accent) per genre conventions
3. Apply microtiming offsets to create groove (jazz swing, hip-hop laid-back, Latin clave displacement)
4. Add ghost notes around strong-beat targets where appropriate

#### Generator Implementation

The four layers are orchestrated by `PhraseAwareGenerator`, registered alongside the existing generators:

```python
# src/yao/generators/melody/phrase_aware.py

@register_generator("phrase_aware")
class PhraseAwareGenerator(GeneratorBase):
    def generate(self, spec: CompositionSpec) -> tuple[ScoreIR, ProvenanceLog]:
        profile = self._load_melodic_profile(spec.genre)

        phrase_plan = self._plan_phrases(spec, profile)
        provenance.record("M1_phrase_plan", phrase_plan, ...)

        skeleton = self._generate_skeleton(phrase_plan, spec.harmony, profile)
        provenance.record("M2_skeleton", skeleton, ...)

        melody = self._realize_surface(skeleton, profile)
        provenance.record("M3_surface", melody, ...)

        ornamented = self._add_ornaments(melody, profile)
        provenance.record("M4_ornament", ornamented, ...)

        score = self._to_score_ir(ornamented, spec)
        return score, provenance
```

Each layer records its decisions in provenance, enabling the `/explain` command to trace any musical element back to its origin.

The existing `rule_based` and `stochastic` generators remain available unchanged. Migration to `phrase_aware` is opt-in via the spec's `generation.strategy` field.

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
```

YaO ships with **30+ genre profiles** organized in three tiers:

- **Tier 1**: Western art music (Baroque, Classical, Romantic, Modern), Jazz (Bebop, Modal, Fusion), Pop (Ballad, Dance), Lo-Fi Hip-Hop
- **Tier 2**: Rock (Classic, Progressive), Metal (Traditional, Djent), Folk, Country, Blues, Bluegrass, Electronic (House, Ambient)
- **Tier 3**: J-Pop subgenres, K-Pop, Latin (Bossa, Salsa), Indian Classical, Celtic, Middle Eastern, Chinese Traditional, Japanese Traditional

Profiles are **composable**. A user can specify:

```yaml
genre:
  primary: bebop_jazz
  secondary: lofi_hiphop
  blend_ratio: 0.7
```

`blend_profiles(primary, secondary, ratio)` produces a weighted average of all distributions and scalar parameters. This enables compositions that cross genre boundaries.

---

## 4. Directory Structure

```
yao/
├── CLAUDE.md                      # Operational contract for Claude Code
├── PROJECT.md                     # This file (full project design)
├── README.md                      # User-facing quick start
├── pyproject.toml                 # Python deps
├── Makefile                       # Main commands
├── uv.lock
│
├── .claude/
│   ├── commands/                  # Slash commands
│   │   ├── compose.md
│   │   ├── arrange.md
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md
│   │   ├── explain.md
│   │   ├── regenerate-section.md
│   │   ├── sketch.md
│   │   └── render.md
│   ├── agents/                    # Subagent definitions
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   └── producer.md
│   ├── skills/                    # Knowledge modules
│   │   ├── genres/                # 30+ paired md/yaml files
│   │   │   ├── bebop-jazz.md
│   │   │   ├── bebop-jazz.yaml
│   │   │   ├── jpop-ballad.md
│   │   │   ├── jpop-ballad.yaml
│   │   │   ├── classical-romantic.md
│   │   │   ├── classical-romantic.yaml
│   │   │   ├── lofi-hiphop.md
│   │   │   ├── lofi-hiphop.yaml
│   │   │   ├── ... (26+ more)
│   │   │   └── japanese-traditional.yaml
│   │   ├── theory/
│   │   │   ├── voice-leading.md
│   │   │   ├── reharmonization.md
│   │   │   ├── counterpoint.md
│   │   │   ├── modal-interchange.md
│   │   │   ├── phrase-structure.md
│   │   │   └── cadence-design.md
│   │   ├── instruments/
│   │   └── psychology/
│   ├── guides/                    # Developer guides
│   │   ├── architecture.md
│   │   ├── coding-conventions.md
│   │   ├── music-engineering.md
│   │   ├── melody-pipeline.md
│   │   ├── genre-profiles.md
│   │   ├── testing.md
│   │   └── workflow.md
│   └── hooks/                     # Auto-execution hooks
│
├── specs/
│   ├── projects/                  # User compositions
│   ├── templates/                 # Spec templates
│   └── fragments/                 # Reusable spec fragments
│
├── src/
│   ├── yao/
│   │   ├── __init__.py
│   │   ├── errors.py              # Custom exception hierarchy
│   │   ├── types.py               # Domain type aliases
│   │   ├── constants/             # Layer 0
│   │   │   ├── instruments.py
│   │   │   ├── scales.py
│   │   │   ├── chords.py
│   │   │   ├── dynamics.py
│   │   │   ├── midi.py
│   │   │   ├── melodic_profiles/  # 30+ YAML files
│   │   │   ├── rhythms/           # 30+ rhythm templates
│   │   │   └── grooves.py         # GrooveProfile presets
│   │   ├── schema/                # Layer 1
│   │   │   ├── composition.py
│   │   │   ├── trajectory.py
│   │   │   ├── constraints.py
│   │   │   ├── negative_space.py
│   │   │   ├── references.py
│   │   │   ├── production.py
│   │   │   └── melodic_profile.py
│   │   ├── ir/                    # Layer 3
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
│   │   │   └── harmonic_context.py
│   │   ├── generators/            # Layer 2
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── rule_based.py
│   │   │   ├── stochastic.py
│   │   │   └── melody/            # 4-layer pipeline
│   │   │       ├── __init__.py
│   │   │       ├── phrase_aware.py
│   │   │       ├── motif_developer.py     # M1
│   │   │       ├── skeleton.py             # M2
│   │   │       ├── selector.py             # HarmonicMelodicSelector
│   │   │       ├── outline.py              # OutlineGenerator
│   │   │       ├── surface.py              # M3
│   │   │       ├── ornament.py             # M4
│   │   │       └── groove.py               # GrooveProfile application
│   │   ├── perception/            # Layer 4
│   │   ├── render/                # Layer 5
│   │   ├── verify/                # Layer 6
│   │   │   ├── music_lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py
│   │   │   ├── diff.py
│   │   │   ├── constraints.py
│   │   │   ├── genre_critic.py
│   │   │   ├── conformity.py     # KL divergence, motif coherence
│   │   │   └── memorability.py
│   │   ├── reflect/               # Layer 7
│   │   └── conductor/
│   │       ├── conductor.py
│   │       ├── feedback.py
│   │       ├── result.py
│   │       ├── intent_parser.py
│   │       └── intent_to_spec.py
│   └── cli/
│
├── references/
│   ├── catalog.yaml
│   ├── midi/
│   ├── musicxml/
│   ├── motifs/                    # Reusable motif library
│   │   ├── catalog.yaml
│   │   └── *.json
│   └── extracted_features/
│
├── outputs/                       # Generated artifacts (git-ignored)
├── soundfonts/                    # Audio rendering (git-ignored)
├── tests/
│   ├── unit/
│   │   ├── generators/
│   │   │   └── melody/
│   │   ├── schema/
│   │   ├── ir/
│   │   ├── verify/
│   │   ├── conductor/
│   │   └── reflect/
│   ├── integration/
│   ├── music_constraints/
│   ├── scenarios/                 # Genre-specific scenario tests
│   ├── golden/                    # Snapshot tests
│   └── helpers.py
├── tools/                         # Architecture lint, dev tools
└── docs/
    ├── design/                    # ADR-style decision records
    ├── tutorials/
    ├── reference/
    └── glossary.md
```

---

## 5. The Orchestra: Subagent Design

Each subagent has its own context, tool permissions, and evaluation axes. They operate independently and are integrated by the Producer.

### 5.1 Composer

- **Responsibility**: Generate the phrase plan, motifs, and primary melodic line via the 4-layer melody pipeline
- **Inputs**: `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`, the active `MelodicProfile`
- **Outputs**: A populated Score IR containing `PhrasePlan`, `Skeleton`, `MelodyLine`, `OrnamentedMelodyLine`, and motif assignments
- **Forbidden**: Instrument selection and final voicing (Orchestrator's domain)
- **Pipeline ownership**: Owns Layer M1 (phrase planning) and orchestrates calls to M2–M4
- **Evaluation axes**: Motif memorability, balance of repetition and variation, fidelity to the trajectory, motif coherence score ≥ 0.5

### 5.2 Harmony Theorist

- **Responsibility**: Design chord progressions, modulations, secondary chords, cadences; supply `HarmonicContext` for each metric position
- **Inputs**: Composer's phrase plan, `composition.yaml` harmony section, the genre's `cadence_patterns`
- **Outputs**: A complete chord progression IR with functional notation and concrete voicing candidates; a per-beat `HarmonicContext` series
- **Critical role for the melody pipeline**: The Composer's Layer M2 cannot run without the Harmony Theorist's `HarmonicContext`
- **Evaluation axes**: Functional consistency, tension resolution, genre fit, voice-leading smoothness

### 5.3 Rhythm Architect

- **Responsibility**: Design drum patterns, grooves, syncopation, fills; provide `GrooveProfile` for the piece
- **Inputs**: `composition.yaml` rhythm section, the genre's `rhythm_templates` and `groove_profile`
- **Outputs**: Rhythm IR (rhythmic placement for all instruments), the active `GrooveProfile`
- **Evaluation axes**: Groove, human feel, contrast between sections, swing-ratio fidelity to genre

### 5.4 Orchestrator

- **Responsibility**: Assign instruments, decide voicings, manage range placement, design countermelodies
- **Inputs**: Outputs from Composer, Harmony, and Rhythm
- **Outputs**: Complete Score IR with all parts assigned to instruments
- **Evaluation axes**: Frequency-space collision avoidance, idiomatic instrument use, textural density, countermelody quality

### 5.5 Adversarial Critic

- **Responsibility**: Discover and report every weakness — never praises
- **Inputs**: Any generated artifact at any stage; the genre's `anti_patterns` list
- **Outputs**: `critique.md` with severity-rated issues (`critical`, `major`, `minor`, `hint`); structured fix suggestions
- **Genre specialization**: Each genre Skill provides anti-pattern definitions specific to that genre. The Critic loads these via `GenreCritic` and applies them in addition to universal critiques.
- **Evaluation axes**: Comprehensiveness and specificity of issue detection

### 5.6 Mix Engineer

- **Responsibility**: Stereo placement, dynamics, frequency-masking resolution, loudness management
- **Inputs**: Orchestrator's output + production parameters
- **Outputs**: Mix instructions (per-track EQ/compression/reverb/pan settings)
- **Evaluation axes**: LUFS target compliance, frequency balance, stereo width

### 5.7 Producer

- **Responsibility**: Overall integration, prioritization, dialogue with the conductor (human), final decisions
- **Inputs**: All subagent outputs + human feedback + Critic's reports
- **Outputs**: Final production decisions, instructions for the next iteration
- **Privilege**: The only subagent that can reject or send back another subagent's output
- **Evaluation axes**: Fidelity to `intent.md`, balanced integration of all subagents' work

---

## 6. The 6-Phase Compositional Cognitive Protocol

The `/compose` and `/arrange` commands force Claude Code to execute the following six phases **in order**.

### Phase 1: Intent Crystallization

From user input (dialogue, YAML, sketch, or natural-language description), parse into a `StructuredIntent` and articulate the essence of the piece in 1–3 sentences. Commit to `intent.md`. The intent parser handles complex descriptions and produces multi-dimensional emotional and stylistic vectors (Section 11.3).

### Phase 2: Architectural Sketch

Draw the time-axis trajectories (tension / density / valence / predictability) **first**. Select or blend the appropriate `MelodicProfile` for the genre. Complete `trajectory.yaml`. No notes yet.

### Phase 3: Skeletal Generation

The Composer produces 5–10 candidate phrase plans + motif germs. Each candidate is run through Layer M1 only (no skeleton or surface yet). Variation comes from different seed values and motif choices.

### Phase 4: Critic-Composer Dialogue

The Adversarial Critic attacks all candidates with both universal and genre-specific anti-patterns. The Producer judges and selects the strongest candidate, or commissions a hybrid that synthesizes strengths.

### Phase 5: Detailed Filling

The chosen phrase plan flows through Layers M2 → M3 → M4. The Harmony Theorist supplies harmonic context. The Rhythm Architect supplies rhythm and groove templates. The Orchestrator assigns instruments. Every decision is recorded in provenance.

### Phase 6: Listening Simulation

The Perception Substitute Layer "listens" to the finished piece, computing genre conformity score, motif coherence score, and memorability proxy. Deviation from `intent.md` is measured. If deviation exceeds threshold, the Conductor identifies the offending section and triggers regeneration of just that section. Final outputs: `critique.md`, `analysis.json`, `evaluation.json`, `provenance.json`.

---

## 7. Parameter Specifications

YaO fully describes a piece using **9 files**. All are version-controlled.

### 7.1 `intent.md` — Natural-language intent

Free-form prose stating the essence of the piece in 1–3 sentences.

### 7.2 `composition.yaml` — Composition parameters

Key, mode, tempo, time signature, form, genre (single or blended), instrumentation, sections.

```yaml
title: "Rainy Cafe"
key: "D minor"
mode: "natural_minor"
tempo_bpm: 90
time_signature: "4/4"

genre:
  primary: lofi_hiphop
  secondary: jazz_modal
  blend_ratio: 0.7

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

```yaml
override:
  base: bebop_jazz
  modifications:
    chromaticism_level: 0.85
    motif_recurrence_rate: 0.6
```

### 7.9 `provenance.json` — Append-only generation history

Auto-generated. Records every decision at every layer (M1–M4 for melody, plus harmony, rhythm, orchestration). Queryable via `/explain`.

---

## 8. Custom Commands

| Command | Purpose | Primary subagents |
|---|---|---|
| `/compose <project>` | Generate a new piece | Composer → all |
| `/arrange <project>` | Arrange an existing piece | Orchestrator + Critic |
| `/critique <iteration>` | Critique an artifact | Adversarial Critic with genre specialization |
| `/regenerate-section <project> <section>` | Regenerate one section | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate two musical states | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment | Composer + Rhythm |
| `/explain <element>` | Trace generation decisions | Producer (provenance lookup) |
| `/diff <iter_a> <iter_b>` | Show musical diff | Verifier |
| `/render <iteration>` | MIDI to audio + score | Mix Engineer |
| `/sketch` | Sketch-to-spec dialogue mode | Producer + intent parser |
| `/conduct "<description>"` | Full agentic pipeline from natural language | All |

---

## 9. Skills

### 9.1 Genre Skills (30+)

Each genre Skill consists of:

- A **Markdown file** with: overview, historical context, characteristic features (form, tempo, harmony, melody, rhythm, instrumentation, production), anti-patterns, required reference works, implementation hints, related genres, sub-style notes, and music-theoretical citations
- A **YAML companion** containing the complete `MelodicProfile`
- A **reference catalog entry** in `references/catalog.yaml`
- A **scenario test** in `tests/scenarios/test_<genre>.py`

Adding a new genre requires all four artifacts.

### 9.2 Theory Skills

Harmony, counterpoint, reharmonization, modal interchange, phrase structure, cadence design.

### 9.3 Instrument Skills

Per-instrument range, idiomatic playing techniques, timbre, physical constraints, characteristic phrase patterns.

### 9.4 Psychology Skills

Empirical mappings from music psychology (Juslin, Huron, Krumhansl). Includes `intent-parsing.md` documenting how natural-language descriptions map to `StructuredIntent`.

---

## 10. Hooks

| Hook | Timing | Action |
|---|---|---|
| `pre-commit-lint` | Before `git commit` | Music21 lint, YAML schema validation, melodic profile validation, architecture lint |
| `post-generate-render` | After generation completes | Auto-render MIDI to audio and score |
| `post-generate-critique` | After generation completes | Always invoke Adversarial Critic with genre specialization |
| `update-provenance` | After any change | Update Provenance Graph |
| `genre-skill-validate` | When `.claude/skills/genres/*.md` changes | Verify paired YAML exists, schema validates, anti-patterns are well-formed |

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

The constraint checker runs at Layer 6 and reports violations to the Conductor.

### 11.2 The Provenance Graph

`provenance.json` is append-only. Every entry records timestamp, layer, decision, input, output, rationale, and agent.

```json
{
  "timestamp": "2026-05-07T10:23:11Z",
  "layer": "M2_skeleton",
  "decision": "select_target_pitch",
  "input": {"phrase_id": "p3", "current_chord": "Cmaj7"},
  "output": {"target_pitch": 67, "chord_relation": "5th"},
  "rationale": "phrase function ANSWER + chord_tone_targeting=0.75 + voice_leading_target",
  "agent": "composer-subagent"
}
```

### 11.3 The Intent Parser

```python
@dataclass(frozen=True)
class StructuredIntent:
    valence: float        # -1.0 to +1.0
    arousal: float        # 0.0 to 1.0
    tension: float        # 0.0 to 1.0
    warmth: float         # -1.0 to +1.0
    nostalgia: float      # 0.0 to 1.0
    genre_candidates: list[tuple[str, float]]
    use_case: str
    duration_seconds: float
    loopable: bool
    instruments_mentioned: list[str]
    tempo_hint: str | None
    mood_keywords: list[str]
    raw_description: str
```

The parser uses a hybrid approach: rule-based keyword extraction first, then Claude API call for nuanced interpretation, with confidence-weighted merge. Output flows through `IntentToSpec` to produce a complete `CompositionSpec`.

The intent parser also performs **mode selection** by mapping `valence + warmth + nostalgia` to the appropriate scale (Dorian, Phrygian, Lydian, Mixolydian, etc.) per the genre's `scale_preferences`.

### 11.4 The Genre Critic

```python
class GenreCritic:
    def critique(self, score: ScoreIR, genre: str) -> CritiqueReport:
        skill = self.skills.load(genre)
        anti_patterns = skill.parse_anti_patterns()
        issues = []
        for pattern in anti_patterns:
            check = self._check_pattern(score, pattern)
            if check.violated:
                issues.append(Issue(
                    severity=pattern.severity,
                    category=pattern.category,
                    description=pattern.description,
                    location=check.location,
                    suggestion=pattern.fix_suggestion,
                ))
        return CritiqueReport(genre=genre, issues=issues)
```

When the Critic flags `critical` issues, the Conductor consults the Skill's fix recipes and adapts the spec before regenerating.

---

## 12. Quality Assurance: Evaluation Metrics

YaO evaluates artifacts across **eight dimensions**. Scores are saved to `evaluation.json`.

### 12.1 Structural Evaluation
Section contrast, climax position, density-curve fidelity, repetition balance, loopability.

### 12.2 Melodic Evaluation
Range fit, motif memorability, singability, phrase-ending closure, contour variation.

### 12.3 Harmonic Evaluation
Chord function consistency, tension resolution, harmonic complexity vs. parameters, cadence strength.

### 12.4 Arrangement Evaluation (when applicable)
Instrument-role clarity, frequency-collision risk, original-preservation rate (arrangement mode), transformation strength.

### 12.5 Acoustic Evaluation
BPM match, beat stability, LUFS target, spectral balance, onset density.

### 12.6 Genre Conformity (NEW)
KL divergence between actual and target distributions for: interval distribution, phrase length distribution, chord-tone targeting rate, syncopation level. Aggregated as `overall_genre_conformity` (target ≥ 0.7).

### 12.7 Motif Coherence (NEW)
Quantifies thematic unity through motif recurrence and variation balance. Each genre has a target range (lo-fi: 0.7–0.9; bebop: 0.3–0.5; classical: 0.5–0.7).

### 12.8 Memorability Proxy (NEW)
Combines pitch-sequence autocorrelation, contour predictability, and average cadence strength.

Each metric has a numeric target and tolerance. Out-of-range values trigger Adversarial Critic intervention.

---

## 13. Development Roadmap

### Past Phases (complete)

- **Phase 0** (2 weeks): Project structure, MVP skeleton, basic MIDI generation, SoundFont rendering
- **Phase 1** (1 month): Parameter-driven symbolic composition; rule_based + stochastic generators; Conductor feedback loop; provenance; CLI; Claude Code commands and agent definitions; constraint system; section regeneration; 226+ tests
- **Phase 2** (completed 2026-05-07): Phrase-first generation foundation — `MelodicProfile` schema + 5 Tier-1 genre profiles (bebop_jazz, j_pop_ballad, classical_romantic, lofi_hiphop, rock_classic); `Phrase`, `PhrasePlan`, `Skeleton`, `MelodyLine`, `HarmonicContext` IR types; 4-layer melody pipeline (M1: MotifDevelopmentPlanner, M2: SkeletonGenerator, M3: SurfaceRealizer, M4: OrnamentEngine); `phrase_aware` generator registered; profile blending; 176 new tests (2978 total)

### Active Phase

- **Phase 3: Motif Development + Harmonic Coupling** (1 month)
  - `MotifDevelopmentPlanner`, `HarmonicMelodicSelector`, `OutlineGenerator`
  - All 13 motif transformations wired into generation
  - Motif library persistence
  - Acceptance: `motif_coherence_score >= 0.5` on 32-bar pieces

- **Phase 4: Rhythm and Microtiming** (1 month)
  - 30+ rhythm templates organized by genre
  - `GrooveProfile` engine
  - Microtiming application in M4
  - Ghost note system
  - Acceptance: jazz pieces measure swing ratio 0.65 ± 0.02

- **Phase 5: Genre Expansion + Critic Specialization** (2 months)
  - 30+ genre profiles total (Tiers 2 and 3)
  - `GenreCritic` with anti-pattern checks per genre
  - Conductor uses genre-specific feedback recipes
  - Genre conformity scoring integrated into evaluation
  - Acceptance: 30+ genres generate; conformity ≥ 0.7

- **Phase 6: Intent Parsing + Blending** (1 month)
  - `IntentParser` (rule-based + Claude API hybrid)
  - `IntentToSpec` automatic spec construction
  - Genre blending
  - Mode selection via emotional vector
  - Acceptance: complex descriptions produce appropriate specs

- **Phase 7: Perception Substitute MVP** (1–2 months)
  - Reference matcher (cosine similarity in feature space)
  - Psychology mapper (Juslin/Huron-grounded)
  - Style vector arithmetic
  - Acceptance: Layer 4 returns non-trivial signals

- **Phase 8: Production Integration** (2–3 months)
  - DAW integration (Reaper)
  - Live improvisation mode
  - User preference learning seeds
  - AI music model bridges (Stable Audio, MusicGen)

- **Phase 9: Reflection and Learning** (ongoing)
  - Layer 7 in operation
  - Per-user style profiles
  - Community profile sharing standards

### User-Value Milestones

| Milestone | User value | Phases involved |
|---|---|---|
| **1. Describe & Hear** | "Write a description and listen immediately" | Phase 1 ✅ |
| **2. Iterate & Improve** | "Tell it what's wrong; it gets better" | Phase 1 + Phase 5 |
| **3. Genre Faithful** | "Sounds like the genre I asked for" | Phase 2–5 |
| **4. Coherent Piece** | "Has unity, not just notes" | Phase 3 |
| **5. Real Groove** | "Feels alive, not robotic" | Phase 4 |
| **6. My Style** | "Learns my preferences" | Phase 7 + Phase 9 |
| **7. Production Ready** | "Output usable in real projects" | Phase 8 |

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

The intent parser builds a complete spec, the phrase-first pipeline generates, evaluation iterates until quality metrics pass.

### 14.3 YAML Path

```bash
make new-project NAME=my-first-song
# Edit specs/projects/my-first-song/composition.yaml
yao compose specs/projects/my-first-song/composition.yaml --strategy phrase_aware
yao render outputs/projects/my-first-song/iterations/v001/full.mid
```

### 14.4 Interactive Path (Claude Code)

```
> /sketch a mysterious puzzle game BGM, minimal and looping
> /compose my-puzzle-bgm
> /critique my-puzzle-bgm
> /regenerate-section my-puzzle-bgm chorus
```

### 14.5 Arrange an Existing Piece

```bash
cp my_song.mid specs/projects/my-arrangement/source.mid
> /arrange my-arrangement --style "lo-fi hip-hop"
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
| Motif library | JSON | Reusable, indexable |

Custom formats are avoided. Only what cannot be represented in existing standards is defined minimally.

---

## 16. Ethics and Licensing

### 16.1 Reference Library Licensing
Only rights-cleared works. License status recorded in `references/catalog.yaml`.

### 16.2 Artist Imitation
Specifying "in the style of [active artist]" is discouraged. Use abstract feature descriptions.

### 16.3 Cultural Appropriation Protocols
World music genres require source citations, practitioner review, explicit cultural context, and warnings against mass commercial generation when culturally inappropriate.

### 16.4 Generated Work Rights
Rights belong to the user by default. Warning emitted when reference influence is unusually high.

### 16.5 Transparency
Every generated artifact records that it was produced by YaO and lists the aesthetic anchors and genre profiles in `provenance.json`.

---

## 17. Relationship to CLAUDE.md

`CLAUDE.md` contains short, prescriptive operational rules. `PROJECT.md` (this file) contains the full design and philosophy. **Conflict resolution: CLAUDE.md > PROJECT.md > other docs.**

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this file) | Humans + agents | Design, philosophy, architecture |
| `CLAUDE.md` | Agents primarily | Invariant rules, current phase, escalation |
| `README.md` | Humans | Quick start |
| `docs/design/*.md` | Humans + agents | ADR-style decision records |
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

---

## 19. Glossary

**Conductor** — The human who owns the project; final decision-maker.

**Orchestra** — The collective of subagents.

**Score** — The YAML files in `specs/`; complete description of a piece.

**Score IR** — Implementation-ready intermediate representation.

**Trajectory** — Characteristic curve over time (tension, density, etc.).

**Phrase** — A musical unit with function, target pitch, and cadence.

**Motif** — A short melodic-rhythmic idea developed across a piece.

**Skeleton** — Structural pitches anchoring a melody to its harmony.

**MelodyLine** — Realized melody after surface filling.

**OrnamentedMelodyLine** — Expressive surface with ornaments and microtiming.

**MelodicProfile** — Genre-specific parameters governing melody generation.

**HarmonicContext** — Harmonic state at a given metric position.

**GrooveProfile** — Microtiming and velocity offsets characterizing a feel.

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

---

## 20. The World YaO Aims For

YaO is not a project where AI makes music. It is **infrastructure for humans and AI to co-create music, each contributing what they do best**.

- Humans contribute **intent, judgment, and sensibility**
- AI contributes **theoretical knowledge, iteration speed, and exhaustive record-keeping**
- YaO is **the place where these are made into a structured collaborative process**

The phrase-first pipeline, the genre profile system, the intent parser, and the genre-specialized critic together aim for a single goal: **given any genre or mood, produce a piece that respects the genre, has internal coherence, expresses the user's intent, and varies meaningfully from one generation to the next**.

Great music remains, ultimately, **the expression of a human soul**. YaO aims to make that expression **faster, deeper, more diverse, and more reproducible**.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.1*
*Last updated: 2026-05-07*
*v2.1: Phase 2 complete — phrase-first pipeline implemented, 5 Tier-1 profiles active, 2978 tests green. Phase 3 active.*
*v2.0: Integrated phrase-first melody pipeline, MelodicProfile-driven genre system, intent parser, genre-specialized critic, and extended evaluation metrics into the core design.*
