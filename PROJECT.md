# You and Orchestra (YaO) — PROJECT.md v2.0

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## Document Status

This is **PROJECT.md v2.0**, a revised design document succeeding v1.0.

**Core change from v1.0**: YaO introduces the **Musical Plan IR (MPIR)** as the central middle-layer abstraction. This addresses the "vertical alignment problem" identified in the integrated design review — the gap between expressive specifications, generation logic, and evaluation depth that previously prevented individual improvements from compounding.

**Philosophical evolution**: YaO's original "Music-as-Code" philosophy is sharpened into **"Music-as-Plan"** — the recognition that what makes music compelling is decided in the *planning* phase, before any note is written. Code, tests, and version control are tools; *the plan* is the substance.

This document describes the **target state**. Current implementation status is tracked separately in the **Capability Matrix** (see Section 4) and updated continuously, never aspirationally.

---

## Table of Contents

0. [Project Essence](#0-project-essence)
1. [Metaphor: You and Orchestra](#1-metaphor-you-and-orchestra)
2. [Five Inviolable Principles](#2-five-inviolable-principles)
3. [The Vertical Alignment Principle](#3-the-vertical-alignment-principle)
4. [Capability Matrix (Single Source of Truth)](#4-capability-matrix-single-source-of-truth)
5. [Architecture: 8-Layer Model](#5-architecture-8-layer-model)
6. [Musical Plan IR — The Heart of YaO](#6-musical-plan-ir--the-heart-of-yao)
7. [Specification Layer (Input)](#7-specification-layer-input)
8. [Generation Pipeline (7 Steps)](#8-generation-pipeline-7-steps)
9. [Verification & Critique](#9-verification--critique)
10. [Perception Substitute Layer](#10-perception-substitute-layer)
11. [Arrangement Engine](#11-arrangement-engine)
12. [Rendering & Production](#12-rendering--production)
13. [The Orchestra: Subagent Design](#13-the-orchestra-subagent-design)
14. [Cognitive Protocol: 6 Phases × 7 Steps](#14-cognitive-protocol-6-phases--7-steps)
15. [Custom Commands](#15-custom-commands)
16. [Skills & Knowledge](#16-skills--knowledge)
17. [Hooks & Automation](#17-hooks--automation)
18. [MCP Integration](#18-mcp-integration)
19. [Quality Assurance](#19-quality-assurance)
20. [Directory Structure](#20-directory-structure)
21. [Roadmap (180-day Plan)](#21-roadmap-180-day-plan)
22. [Quick Start](#22-quick-start)
23. [File Formats & Interoperability](#23-file-formats--interoperability)
24. [Ethics & Licensing](#24-ethics--licensing)
25. [Document Roles](#25-document-roles)
26. [Future Architecture Extensions](#26-future-architecture-extensions)
27. [Glossary](#27-glossary)
28. [Closing](#28-closing)

---

## 0. Project Essence

**You and Orchestra (YaO)** is an **agentic music production environment built on Claude Code**. Unlike a generic "AI music tool" that emits music from a black box, YaO is a structured environment in which **a human (You = Conductor) directs multiple specialized AI agents (Orchestra Members) through a transparent, layered, auditable production pipeline**.

YaO's entire design is subordinate to one proposition:

> **Music production is not a one-shot intuitive act. It is a reproducible, improvable engineering process — and at its heart lies a *plan*.**

For this reason, YaO treats music as **plan, code, specification, test, diff, and provenance** before treating it as audio. We call this the **Music-as-Plan philosophy**.

---

## 1. Metaphor: You and Orchestra

Every concept in YaO maps to an orchestra metaphor. Internalizing this mapping is the shortest route to using YaO correctly.

| YaO Component | Orchestral Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human owning the project |
| **Score** | Sheet music | YAML specs in `specs/` |
| **Plan** | Conductor's annotated score | Musical Plan IR (`MPIR`) |
| **Orchestra Members** | Players | Subagents (Composer, Critic, Theorist, …) |
| **Concertmaster** | First-chair coordinator | Producer Subagent |
| **Rehearsal** | Iterative refinement | Generate-evaluate-adapt-regenerate loop |
| **Library** | Orchestra's score library | `references/` (rights-cleared only) |
| **Performance** | Concert | Final rendered audio |
| **Recording** | Recording session | `outputs/iterations/` |
| **Critic** | External reviewer | Adversarial Critic Subagent |
| **Score Markings** | Articulations, dynamics | Trajectory + arrangement layers |

The Conductor does not write every note. The Conductor's job is to **clarify intent, direct the players, judge during rehearsal, and guarantee the quality of the performance**. YaO ports this division of labor into AI.

---

## 2. Five Inviolable Principles

Every implementation decision in YaO is judged against these five principles. They are repeated in `CLAUDE.md` as enforcement rules.

### Principle 1: The agent is an environment, not a composer
YaO is not "AI that writes songs." It is "an environment that makes a human's composition 10× faster." Full automation is not the goal; augmenting the human creative judgment is.

### Principle 2: Every decision is explainable
Every generated note, chord, and arrangement choice carries a *why* in the Provenance Graph — persistent, queryable, traceable.

### Principle 3: Constraints liberate
Specs, references, and negative-space designs are not cages. They are scaffolds. Unlimited freedom produces paralysis.

### Principle 4: Plan before notes (time-axis first)
Trajectory curves and structural plans are designed *first*. Notes fill the structure *second*. This is the heart of Music-as-Plan.

### Principle 5: The human ear is the final truth
However sophisticated the metrics, the human listening experience is the final judge. Agents *inform*, never *replace*, human judgment.

---

## 3. The Vertical Alignment Principle

YaO's architecture is governed by a sixth, meta-level principle that emerged from design review:

> **The expressiveness of the input, the depth of the processing, and the resolution of the evaluation must advance together. Deepening one alone is wasted.**

This principle resolves a real risk: every individual improvement (richer DSL, smarter generator, better critic) becomes ineffective if the other two layers cannot match it.

| Layer | Question |
|---|---|
| **Input** | Can the spec express what we want? |
| **Processing** | Can the pipeline transform that intent into a plan, then into notes? |
| **Output** | Can we evaluate and critique the result with the same precision? |

We commit to advancing all three layers in lockstep across every release.

---

## 4. Capability Matrix (Single Source of Truth)

This matrix is the **single authoritative description of what YaO can and cannot do**. It is updated with every PR, never aspirationally. README.md, CLAUDE.md, and PROJECT.md all link here rather than restating capabilities.

Status legend: ✅ Implemented · 🟢 Working but limited · 🟡 Partial · ⚪ Designed, not started · 🔴 Identified gap

| Area | Feature | Status | CLI | Claude Cmd | Tests | Notes |
|---|---|---|---|---|---|---|
| **Spec / Input** | composition.yaml v1 | ✅ | compose | /compose | yes | Pydantic v1 schema with sections, instruments, generation config |
| | composition.yaml v2 (rich DSL) | 🟢 | validate-spec | — | yes | limitation: schema implemented; no plan generators consume it yet |
| | intent.md as first-class artifact | 🟢 | new-project | — | yes | limitation: parsed with keyword extraction; no NL→emotion inference yet |
| | trajectory.yaml multi-dimensional | 🟢 | --trajectory | — | yes | limitation: 5 dims defined (tension/density/predictability/brightness/register_height); generators respond to tension-velocity only |
| | constraints with scoping | ✅ | (in spec) | — | yes | must/must_not/prefer/avoid × global/section/instrument/bars |
| | NL → Spec compiler (sketch state machine) | 🟡 | conduct | /sketch | yes | limitation: keyword matching in Conductor only; no state machine |
| **Plan IR** | SongFormPlan | ✅ | — | — | yes | SectionPlan + SongFormPlan with section_at_bar, serialization |
| | HarmonyPlan with functions/cadences | ✅ | — | — | yes | ChordEvent + HarmonicFunction + CadenceRole + ModulationEvent |
| | MotifPlan / PhrasePlan | ⚪ | — | — | no | Skeleton files only; Phase beta |
| | DrumPattern IR | 🔴 | — | — | no | Skeleton file only; Phase beta |
| | ArrangementPlan | ⚪ | — | — | no | Skeleton file only; Phase beta |
| | MusicalPlan (integrated) | 🟢 | — | — | yes | limitation: form + harmony populated; motifs/arrangement/drums still None |
| **Generation** | rule_based generator (v1, spec→notes) | ✅ | compose | — | yes | Legacy path preserved; also wrapped as NoteRealizer |
| | stochastic generator (v1, spec→notes) | ✅ | compose | — | yes | Legacy path preserved; also wrapped as NoteRealizer |
| | generator registry (legacy) | ✅ | — | — | yes | @register_generator for v1 compat |
| | plan generator registry | ✅ | — | — | yes | @register_plan_generator; form + harmony planners |
| | note realizer registry | ✅ | — | — | yes | @register_note_realizer; rule_based + stochastic |
| | form planner (rule_based) | ✅ | — | — | yes | Spec sections → SongFormPlan with roles/climax |
| | harmony planner (rule_based) | ✅ | — | — | yes | Spec harmony → HarmonyPlan with chord events/cadences |
| | plan orchestrator | ✅ | — | — | yes | Runs form → harmony planners, builds MusicalPlan |
| | legacy adapter (v1→v2 bridge) | ✅ | — | — | yes | v1 CompositionSpec → v2 pipeline; deprecated Phase β |
| | markov generator | ⚪ | — | — | no | Phase beta |
| | constraint_satisfaction generator | ⚪ | — | — | no | Phase beta |
| | motif developer (plan-level) | 🔴 | — | — | no | Requires MPIR |
| | counter-melody generator | 🔴 | — | — | no | Requires MPIR + ArrangementPlan |
| | drum patterner | 🔴 | — | — | no | Requires DrumPattern IR |
| **Critique** | rule-based critique engine (30+) | 🔴 | — | /critique | no | /critique command exists but delegates to LLM prose, not rules |
| | role-based evaluation | 🔴 | — | — | no | — |
| | MetricGoal type system | ✅ | — | — | yes | 7 goal types: AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN, MATCH_CURVE, RELATIVE_ORDER, DIVERSITY |
| | RecoverableDecision logging | ✅ | — | — | yes | 9 known codes; integrated with ProvenanceLog and both generators |
| **Perception** | Stage 1: audio features (LUFS, spectral) | 🔴 | — | — | no | perception/ has only __init__.py |
| | Stage 2: use-case targeted evaluation | 🔴 | — | — | no | — |
| | Stage 3: reference matching (abstract) | 🔴 | — | — | no | — |
| **Arrangement** | source MIDI analysis | 🔴 | — | — | no | arrange/ directory does not exist |
| | preservation/transformation plan | 🔴 | — | — | no | — |
| | style vector operations | 🔴 | — | — | no | — |
| | arrangement engine | ⚪ | — | /arrange | no | /arrange command exists; no engine code; no CLI command |
| | arrangement diff report | 🔴 | — | — | no | — |
| **Rendering** | MIDI writer + stems | ✅ | render | /render | yes | midi_writer.py + stem_writer.py |
| | audio renderer (FluidSynth) | ✅ | render | /render | yes | audio_renderer.py; requires FluidSynth install |
| | MIDI reader | ✅ | — | — | yes | midi_reader.py; loads MIDI back to ScoreIR |
| | iteration management | ✅ | — | — | yes | iteration.py; v001/v002/... versioning |
| | MusicXML writer | ⚪ | — | — | no | — |
| | LilyPond writer | ⚪ | — | — | no | — |
| | Strudel emitter | ⚪ | — | — | no | — |
| | Production manifest + mix chain | 🔴 | — | — | no | — |
| **Conductor** | basic generate-evaluate-adapt | ✅ | conduct | — | yes | conductor.py + feedback.py + result.py |
| | multi-candidate conductor | 🔴 | — | — | no | — |
| | section regeneration | ✅ | regenerate-section | /regenerate-section | yes | — |
| **Subagents** | 7 definitions (.claude/agents/) | ✅ | — | (all) | n/a | Prompt definitions only; no runtime impl |
| | Composer impl | 🔴 | — | — | no | — |
| | Adversarial Critic impl | 🔴 | — | /critique | no | /critique is LLM-prose, not rule-based |
| | Producer impl | 🔴 | — | — | no | — |
| **IR / Core** | ScoreIR (Note, Section, Part) | ✅ | — | — | yes | Frozen dataclasses |
| | Harmony (Roman numerals, realize) | ✅ | — | — | yes | harmony.py |
| | Motif (5 transforms) | ✅ | — | — | yes | motif.py |
| | Voicing (voice leading, parallel 5ths) | ✅ | — | — | yes | voicing.py |
| | Timing (tick/beat/second) | ✅ | — | — | yes | timing.py |
| | Notation (name↔MIDI) | ✅ | — | — | yes | notation.py |
| | Provenance (append-only, queryable) | ✅ | explain | /explain | yes | provenance.py |
| | Error hierarchy | ✅ | — | — | yes | errors.py (YaOError + 5 subclasses) |
| **Verify** | Music linter | ✅ | — | — | yes | lint.py |
| | Score analyzer | ✅ | — | — | yes | analyzer.py |
| | Evaluator (5-dimension) | ✅ | evaluate | — | yes | evaluator.py; uses tolerance-based checks |
| | Score diff | ✅ | diff | — | yes | diff.py with modified note tracking |
| | Constraint checker | ✅ | — | — | yes | Part of verify pipeline |
| **DAW / MCP** | Reaper integration | ⚪ | — | — | no | Phase gamma |
| **Live** | improvisation mode | ⚪ | — | — | no | Phase delta |
| **Skills** | genre skills | 🟡 | — | — | n/a | limitation: 1 of 12 target (cinematic only) |
| | theory skills | 🟡 | — | — | n/a | limitation: 1 of target set (voice-leading only) |
| | instrument skills | 🟡 | — | — | n/a | limitation: 1 of 38 target (piano only) |
| | psychology skills | 🟡 | — | — | n/a | limitation: 1 of target set (tension-resolution only) |
| **QA** | unit tests | ✅ | make test-unit | — | yes | 212 unit tests across 18 files |
| | integration tests | ✅ | make test-integration | — | yes | 2 tests |
| | scenario tests | ✅ | make test | — | yes | 10 tests |
| | music constraint tests | ✅ | make test-music | — | yes | 7 tests (parameterized across instruments) |
| | golden MIDI tests | ✅ | make test-golden | — | yes | 6 goldens: 3 specs × 2 realizers, bit-exact comparison |
| | subagent eval tests | 🔴 | — | — | no | — |
| | architecture lint | ✅ | make arch-lint | — | yes | tools/architecture_lint.py |
| | capability matrix check | 🔴 | — | — | no | tools/capability_matrix_check.py does not exist yet |

When you read this document and see a feature described, **always cross-reference this matrix** for actual availability.

---

## 5. Architecture: 8-Layer Model

YaO v1.0 had a 7-layer architecture. **v2.0 introduces Layer 3.5 — the Plan Layer**, which holds the new Musical Plan IR. This is the most significant structural change.

```
┌────────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                             │
│   Provenance, history, user style profiles                 │
├────────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                           │
│   Lint, eval, diff, adversarial critique, MetricGoals      │
├────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering & Production                            │
│   MIDI / audio / MusicXML / LilyPond / mix / master        │
├────────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                             │
│   Audio features / psych mapping / reference matching      │
├────────────────────────────────────────────────────────────┤
│ Layer 3.5: Musical Plan IR (MPIR) ★ NEW IN v2.0            │
│   SongForm / Harmony / Motif / Phrase / Drum / Arrange     │
├────────────────────────────────────────────────────────────┤
│ Layer 3: Score IR (notes)                                  │
│   ScoreIR, Note, Part, Section — concrete music data       │
├────────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategies                             │
│   Plan generators + Note realizers (rule/stoch/markov/CSP) │
├────────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                     │
│   YAML schemas, intent.md, trajectory, constraints         │
├────────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                         │
│   Instrument ranges, scales, chord types, MIDI mappings    │
└────────────────────────────────────────────────────────────┘
```

### Key dependency rules

- Lower layers know nothing of higher layers
- The new **Layer 3.5 (MPIR)** sits *above* concrete Score IR, because plans are more abstract than notes
- The previous "Generators → ScoreIR" path becomes a two-step path: **Generators → MPIR → ScoreIR**
- Library restrictions remain unchanged: `pretty_midi` only in `ir/` and `render/`, `music21` only in `ir/` and `verify/`, `librosa` only in `verify/` and `perception/`

### Why a new layer

The integrated review identified that previously, generators jumped directly from spec to notes, leaving no inspectable middle representation. This made it impossible for the Adversarial Critic to inspect "the plan" — only the final notes — which limits the depth of critique. The Plan layer fixes this fundamental gap.

---

## 6. Musical Plan IR — The Heart of YaO

### 6.1 Why a Plan IR exists

A musical plan answers questions that pure notes cannot:

- *Why* does this section exist? (form intent)
- *Why* does this chord follow that one? (functional role)
- *Why* does this phrase echo the earlier one? (motif lineage)
- *Why* does this drum pattern fit the arrangement? (groove role)

Notes are *what*. Plans are *why*. Critique without plans is shallow; critique with plans is precise.

### 6.2 Structure of MPIR

`src/yao/ir/plan/` defines the following frozen dataclasses:

```python
@dataclass(frozen=True)
class SongFormPlan:
    sections: list[SectionPlan]      # name, bars, role, dynamics
    climax_section_id: str
    energy_curve: TrajectoryCurve
    density_curve: TrajectoryCurve
    tension_curve: TrajectoryCurve
    predictability_curve: TrajectoryCurve

@dataclass(frozen=True)
class ChordEvent:
    section_id: str
    start_beat: float
    duration_beats: float
    roman: str                                  # e.g. "V7/V"
    function: HarmonicFunction                  # tonic / subdom / dom / predom
    tension_level: float                        # [0,1]
    cadence_role: CadenceRole | None            # half / authentic / plagal / deceptive

@dataclass(frozen=True)
class HarmonyPlan:
    chord_events: list[ChordEvent]
    cadences: dict[str, CadenceType]            # section_id → cadence type
    modulations: list[ModulationEvent]
    tension_resolution_points: list[TimePoint]

@dataclass(frozen=True)
class Motif:
    id: str
    rhythm_shape: tuple[float, ...]             # IOIs
    interval_shape: tuple[int, ...]             # semitone intervals
    identity_strength: float                    # how distinctive it is

@dataclass(frozen=True)
class MotifTransform:
    type: Literal["sequence", "inversion", "retrograde", "augmentation",
                  "diminution", "varied"]
    params: dict                                # transform-specific

@dataclass(frozen=True)
class MotifPlan:
    seeds: list[Motif]
    transformations: dict[str, list[MotifTransform]]  # motif_id → transforms

@dataclass(frozen=True)
class PhrasePlan:
    section_id: str
    bars_per_phrase: float
    motif_sequence: list[str]                   # motif ids in order
    contour: ContourShape
    cadence_strength: float
    call_response_role: Literal["call", "response", "none"]

@dataclass(frozen=True)
class DrumHit:
    time: Beat
    duration: Beat
    kit_piece: KitPiece                         # kick / snare / hat / ...
    velocity: int
    microtiming_ms: float = 0.0

@dataclass(frozen=True)
class DrumPattern:
    id: str
    genre: str
    time_signature: str
    hits: list[DrumHit]
    swing: float
    humanize: float
    fills_at: list[FillLocation]

@dataclass(frozen=True)
class ArrangementLayer:
    instrument: str
    role: Role                                  # melody / bass / harmony / counter / pad
    register: str                               # "low" | "mid" | "high"
    density_factor: float
    pattern_family: str
    active_sections: list[str]

@dataclass(frozen=True)
class ArrangementPlan:
    layers: list[ArrangementLayer]
    counter_melody_lines: list[CounterMelodySpec]
    drum_pattern: DrumPattern
    texture_curve: TrajectoryCurve

@dataclass(frozen=True)
class MusicalPlan:
    """The integrated middle representation. The crown jewel of v2.0."""
    intent_normalized: NormalizedIntent
    form: SongFormPlan
    harmony: HarmonyPlan
    motifs_phrases: MotifAndPhraseAssignment
    arrangement: ArrangementPlan
    drums: DrumPattern
    trajectory: MultiDimensionalTrajectory
    provenance: ProvenanceLog
```

### 6.3 What MPIR enables

| Capability | Mechanism |
|---|---|
| **Plan-level critique** | Adversarial Critic operates on MPIR, not just final MIDI |
| **Multi-candidate selection** | Generate N plans; critic ranks; producer integrates |
| **Section-level surgery** | Edit one section's plan, re-realize only that section |
| **Arrangement engine** | Source MIDI → SourcePlan → operations → TargetPlan → notes |
| **Subagent division** | Composer owns MotifPlan, Harmony Theorist owns HarmonyPlan, etc. |
| **Style transfer** | Compute style vectors over plans, not over raw notes |
| **Provenance precision** | "Why this note?" → trace through plan, not just generator seed |

### 6.4 Plan ↔ Score relationship

The Score IR (Layer 3) remains. MPIR (Layer 3.5) does *not* replace it; it *plans* it.

```
MPIR  → (Note Realizer generators) → ScoreIR → (renderers) → MIDI/audio
```

The Score IR holds concrete notes; MPIR holds the rationale. Both are versioned; both are diffable.

---

## 7. Specification Layer (Input)

YaO completely describes a piece via **8 input artifacts**, all version-controlled, all human-readable.

| File | Format | Role |
|---|---|---|
| `intent.md` | Markdown | The piece's *soul* in 1–3 sentences of natural language |
| `composition.yaml` | YAML (v2 schema) | Detailed musical specification |
| `trajectory.yaml` | YAML | Multi-dimensional time-axis curves |
| `references.yaml` | YAML | Aesthetic anchors (positive + negative) |
| `negative-space.yaml` | YAML | Designed silence, gaps, textural omissions |
| `arrangement.yaml` | YAML | Arrangement-mode parameters (when arranging) |
| `production.yaml` | YAML | Mixing/mastering targets, use-case |
| `provenance.json` | JSON | Auto-generated, append-only decision log |

### 7.1 composition.yaml v2

The v2 schema is structured into clear sections, each addressing a different musical concern:

```yaml
version: "2"

identity:
  title: "Neon Morning"
  purpose: "product demo bgm"
  duration_sec: 90
  loopable: true

global:
  key: "D major"
  bpm: 128
  time_signature: "4/4"
  genre: "future_pop"

emotion:
  valence: 0.8         # bright ↔ dark
  energy: 0.75
  tension: 0.45
  warmth: 0.6
  nostalgia: 0.3

form:
  sections:
    - id: intro
      bars: 4
      density: 0.25
    - id: verse
      bars: 8
      density: 0.45
    - id: chorus
      bars: 8
      density: 0.9
      climax: true

melody:
  range: { min: "A3", max: "E5" }
  contour: "arch"
  motif:
    length_beats: 2
    repetition_rate: 0.65
    variation_rate: 0.35
  intervals:
    stepwise_ratio: 0.7
    max_leap: "P5"
  phrase:
    bars_per_phrase: 4
    call_response: true

harmony:
  complexity: 0.55
  chord_palette: [I, V, vi, IV, ii, "V/V"]
  cadence:
    verse: "half"
    chorus: "authentic"
  harmonic_rhythm:
    verse: "1 chord per bar"
    chorus: "2 chords per bar"

rhythm:
  groove: "four_on_the_floor"
  swing: 0.08
  syncopation: 0.35

drums:                                     # ★ first-class in v2
  pattern_family: "pop_8beat"
  swing: 0.1
  ghost_notes_density: 0.3
  fills_at: ["pre_chorus_end", "bridge_end"]

arrangement:
  instruments:
    drums: { role: rhythm, pattern_family: electro_pop }
    bass:  { role: bass, motion: "root_octave_passing" }
    pad:   { role: harmony, voicing: "wide" }
    lead:  { role: melody, articulation: "pluck" }
  counter_melody:
    enabled_sections: [chorus_repeat, bridge]

production:
  use_case: "youtube_bgm"                   # ★ drives perception layer
  target_lufs: -16
  stereo_width: 0.7
  vocal_space_reserved: true

constraints:
  - { kind: must, rule: "melody_within_range", scope: global, severity: error }
  - { kind: must, rule: "chorus_density > verse_density", scope: section_relation }
  - { kind: prefer, rule: "motif_repetition_rate in [0.5, 0.8]", scope: "section:verse" }
  - { kind: avoid, rule: "consecutive_leaps > 2", scope: "instrument:violin" }

generation:
  strategy: stochastic
  seed: 42
  temperature: 0.5
```

### 7.2 trajectory.yaml — multi-dimensional

Trajectories are not optional. They are the time-axis declaration of the piece's emotional and structural arc:

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.4], [32, 0.85], [48, 0.6], [64, 0.3]]
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, chorus: 0.9, bridge: 1.0 }
  predictability:
    type: linear
    target: 0.65
    variance: 0.15
  brightness:                                # ★ new in v2
    type: bezier
    waypoints: [[0, 0.4], [32, 0.85], [64, 0.5]]
  register_height:                           # ★ new in v2
    type: stepped
    sections: { verse: 0.45, chorus: 0.7 }
```

Every Plan Generator (Section 8) consumes the trajectory as a control signal. A high tension at bar 32 must affect:
- Harmony (more secondary dominants, borrowed chords)
- Melody (higher pitch, more leaps, fewer rests)
- Rhythm (more subdivision, syncopation)
- Arrangement (more active layers, wider register)
- Dynamics (louder velocities)

If only velocity changes when tension changes, **the trajectory is not being respected** — this is a regression test in CI.

### 7.3 intent.md — first-class artifact

A free-form natural-language statement of the piece's purpose. Maximum 3 sentences. This is the **final court of appeal** — when automated metrics conflict, intent.md decides which one matters.

> Example: *"Early summer morning, forward-looking anticipation toward a new challenge, with a faint trace of anxiety. Not too cheerful, not too sentimental — a neutral lift."*

The Sketch-to-Spec dialogue (Section 15) crystallizes intent.md from the user's first messages.

---

## 8. Generation Pipeline (7 Steps)

YaO v2.0 replaces the v1.0 "spec → notes" leap with a **7-step pipeline** that produces the MPIR before any note is written.

```
[Step 1: Form Planner]      Spec + Trajectory  →  SongFormPlan
      ↓
[Step 2: Harmony Planner]                       →  HarmonyPlan
      ↓
[Step 3: Motif Developer]                       →  MotifPlan + PhrasePlan
      ↓
[Step 4: Drum Patterner]                        →  DrumPattern
      ↓
[Step 5: Arranger]                              →  ArrangementPlan
      ↓
═══ MUSICAL PLAN COMPLETE — Critic Gate ═══

      ↓
[Step 6: Note Realizer]     MPIR  →  ScoreIR
      ↓
[Step 7: Renderer]          ScoreIR  →  MIDI / Audio / Score
```

### Critic Gate

Between Step 5 and Step 6, the **Adversarial Critic operates on MPIR**. Findings can:

- Propose plan-level edits (loop back to Step 1–5)
- Reject the entire plan and request a different candidate
- Approve and pass to realization

This is where YaO's quality leap happens. Critique at the plan level prevents the system from carefully realizing a fundamentally weak plan.

### Step 6 Note Realizer

The existing rule_based and stochastic generators are **repositioned** as Note Realizers. They no longer consume the spec directly; they consume the MPIR. New realizers (Markov, constraint_satisfaction) can be added without changing earlier steps.

### Determinism

Every step is seeded; every step records its provenance. The combination `(spec, trajectory, seed_per_step)` is sufficient to reproduce any output bit-for-bit.

---

## 9. Verification & Critique

### 9.1 Three pillars

YaO's evaluation system rests on three pillars:

#### Pillar 1: MetricGoal type system

Replaces the v1.0 `abs(score - target) <= tolerance` single rule with a polymorphic family of judgment types:

```python
class MetricGoalType(str, Enum):
    AT_LEAST       = "at_least"        # higher is better
    AT_MOST        = "at_most"         # lower is better
    TARGET_BAND    = "target_band"     # near a target
    BETWEEN        = "between"         # range
    MATCH_CURVE    = "match_curve"     # curve follow
    RELATIVE_ORDER = "relative_order"  # section ordering
    DIVERSITY      = "diversity"       # variance/entropy
```

This eliminates absurd cases like "consonance ratio is too high, so it failed."

#### Pillar 2: Role-based × Rule-based critique

Every critique rule belongs to a `Role` (melody, bass, harmony, rhythm, arrangement, structure) × `Severity` (critical / major / minor / suggestion) matrix. The 30+ rules currently planned include:

- **Structural**: ClimaxAbsence, SectionMonotony, FormImbalance, LoopabilityFailure
- **Melodic**: ClicheMotif, PhraseClosureWeakness, ContourMonotony, MemorabilityProxy
- **Harmonic**: ClicheProgression, VoiceCrossing, CadenceWeakness, ParallelFifths, SecondaryDominantAbsence, ModalIntermixOpportunity
- **Rhythmic**: RhythmicMonotony, SyncopationLack, DownbeatAmbiguity, GrooveInconsistency
- **Bass**: RootSupportFailure, KickConflict, RegisterInstability
- **Arrangement**: FrequencyCollision, TextureCollapse, BuildupAbsence, LayerImbalance
- **Emotional**: IntentDivergence, TrajectoryViolation, MoodIncongruence

Each rule emits a structured `Finding`:

```python
@dataclass
class Finding:
    rule_id: str
    severity: Literal["critical", "major", "minor", "suggestion"]
    role: Role
    issue: str                       # e.g. "chorus_lacks_lift"
    evidence: dict                   # numerical proof
    location: SongLocation | None    # bar / section / instrument
    recommendation: dict             # concrete fixes per role
```

This is **machine-actionable** by Claude Code, not free-text the LLM has to parse.

#### Pillar 3: Recoverable Decision

When the system must compromise (e.g., a walking bass note falls below the instrument range), it does *not* silently clamp. It records:

```python
@dataclass
class RecoverableDecision:
    code: str                        # "BASS_NOTE_OUT_OF_RANGE"
    severity: Literal["info", "warning", "error"]
    original_value: Any
    recovered_value: Any
    reason: str
    musical_impact: str              # human-readable consequence
    suggested_fix: list[str]         # upstream remedies
```

These decisions become first-class items in the Provenance Log and surface in evaluation reports. The next iteration's adapter can address them directly.

### 9.2 Use-case driven evaluation

Evaluation is parameterized by `production.use_case`. A piece tagged `youtube_bgm` adds tests for vocal-range space; `game_bgm` adds loop-seam smoothness; `advertisement` adds hook-entry-time; `study` adds dynamic stability.

### 9.3 Golden tests

For every supported template + seed, a known-good MIDI is committed under `tests/golden/`. CI regenerates and compares; intentional changes require explicit golden-update PRs with audio diffs.

---

## 10. Perception Substitute Layer

YaO's most distinctive (and previously empty) layer. It exists because **LLMs cannot listen**. Layer 4 substitutes for hearing.

### 10.1 Three stages, three approaches

| Stage | Approach | Tools |
|---|---|---|
| **1. Audio features** | Empirical objective metrics | librosa, pyloudnorm |
| **2. Use-case targeting** | Purpose-driven evaluation | YaO domain rules |
| **3. Reference matching** | Style-vector comparison | Computed feature vectors |

### 10.2 Stage 1 (audio features)

After audio rendering, extract:
- LUFS (integrated, short-term, momentary)
- Peak, RMS, dynamic range
- Spectral centroid, rolloff, flatness
- Onset density per section
- Tempo stability (ms drift)
- Frequency band energy ratios

These produce a `PerceptualReport` that adds objective dimensions to the structural/symbolic evaluation.

### 10.3 Stage 2 (use-case targeting)

```yaml
use_case: youtube_bgm
  → vocal_space_score, loopability, fatigue_risk, lufs_target_match
use_case: game_bgm
  → loop_seam_smoothness, tension_curve_match, repetition_tolerance
use_case: advertisement
  → hook_entry_time (< 7s), energy_peak_position, short_form_memorability
use_case: study_focus
  → low_distraction_score, dynamic_stability, predictability
```

### 10.4 Stage 3 (reference matching, abstract only)

References are **abstract feature vectors**, never raw audio similarity. Allowed comparisons:
- tempo, density curve, spectral balance, section energy, groove profile

Forbidden comparisons (hard-coded blocks):
- melody, chord progression, identifiable hooks

This is enforced by the schema (`do_not_copy:` is a fixed allowlist of comparison axes; deviating raises a schema error).

### 10.5 Listening Simulation

The Conductor's final phase invokes the Perception Layer to simulate listening. Divergence between the predicted experience and `intent.md` triggers regeneration of the offending sections.

---

## 11. Arrangement Engine

The arrangement engine is **YaO's single most differentiated capability**. Anyone can generate fresh music; few systems can read existing music, understand it, and transform it under explicit preservation/transformation contracts.

### 11.1 Pipeline

```
[Input]      MIDI / MusicXML / (optionally audio with stems)
   ↓
[Analyzer]   Section detection, melody extraction, chord estimation,
             motif detection, role classification
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
[Note Realizer]  → ScoreIR → MIDI/audio
   ↓
[Arrangement Diff]   Markdown report: preserved / changed / risks
   ↓
[Evaluation]
```

### 11.2 Why MPIR enables arrangement

The decision to introduce MPIR (Layer 3.5) was driven significantly by arrangement's needs. Arrangement at the *note level* is brittle — pitch substitution, tempo stretching, instrument remapping. Arrangement at the *plan level* is robust — preserve the harmonic function, vary the voicing; preserve the motif identity, vary the rhythm shape.

### 11.3 Arrangement spec

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
      swing: 0.35
      groove: "laid_back"
    orchestration:
      drums: "dusty_kit"
      bass: "warm_upright"

  evaluate:
    original_preservation_weight: 0.5
    transformation_strength_weight: 0.3
    musical_quality_weight: 0.2
```

### 11.4 Arrangement Diff

Every arrangement run produces a Markdown diff comparable to git diffs:

```markdown
# Arrangement Diff (v003)

## Preserved
- Main hook melodic similarity: 0.91 ✓
- Section form: unchanged ✓
- Chord function similarity: 0.82 ✓

## Changed
- BPM: 128 → 86
- Groove: straight pop → swung lo-fi
- Chords: triads → 7th/9th voicings (35% reharm depth)
- Bass: root → walking with passing tones
- Drums: four-on-floor → laid-back backbeat

## Risks (Adversarial Critic)
- chorus_energy_drop: dropped more than requested (target -20%, actual -38%)
- register_shift: melody preserved but feels lower due to instrumentation
```

---

## 12. Rendering & Production

### 12.1 Multi-format output

| Format | Use | Engine |
|---|---|---|
| MIDI | Universal exchange | pretty_midi |
| WAV / FLAC | Listening, distribution | FluidSynth + mix chain |
| MusicXML | DAW import, notation | music21 |
| LilyPond / PDF | Print-quality scores | lilypond CLI |
| Strudel | Browser instant audition | string emitter |

### 12.2 Production Manifest

Every iteration's rendering is governed by a `production.yaml` Production Manifest:

```yaml
production_manifest:
  sample_rate: 44100
  bit_depth: 24
  target_lufs: -16

  buses:
    drums:    { gain_db: -3, compression: "light" }
    bass:     { gain_db: -5, mono: true }
    harmony:  { gain_db: -8, reverb_send: 0.25 }
    melody:   { gain_db: -4, delay_send: 0.15 }

  mastering:
    normalize_lufs: true
    limiter_ceiling_db: -1.0
    stereo_width: 0.7
```

### 12.3 Mix chain

`src/yao/render/production/mix_chain.py` applies per-stem and bus processing using `pedalboard` (Spotify's open-source plugin host). EQ, compression, reverb, panning, and limiting are all parameterizable.

### 12.4 Stems and DAW handoff

Every iteration produces:
- Per-instrument MIDI stems
- Per-instrument audio stems
- (Optionally) DAW project file (Reaper `.RPP` initially)

---

## 13. The Orchestra: Subagent Design

### 13.1 The seven players

| Subagent | Owns | Inputs | Outputs |
|---|---|---|---|
| **Composer** | Motifs, phrases, themes | intent, spec, trajectory | MotifPlan, PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences | spec, motif plan | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves | spec, genre | DrumPattern |
| **Orchestrator** | Instruments, voicings, counter-melody | all plans above | ArrangementPlan |
| **Mix Engineer** | Production manifest | spec, ScoreIR | mix instructions |
| **Adversarial Critic** | Finding weaknesses | MPIR (or ScoreIR) | list[Finding] |
| **Producer** | Coordination, final judgment | all of the above + intent | decisions, escalations |

### 13.2 Critic is special

The Adversarial Critic **never praises**. Its sole purpose is to find weaknesses. Producer balances critique against intent.

### 13.3 Producer is the single point of authority

Only Producer can override another subagent's output. This prevents agent-agent infinite loops.

### 13.4 Subagent → Pipeline mapping

```
Step 1 Form Planner       ← Producer (form is meta)
Step 2 Harmony Planner    ← Harmony Theorist
Step 3 Motif Developer    ← Composer
Step 4 Drum Patterner     ← Rhythm Architect
Step 5 Arranger           ← Orchestrator
Critic Gate               ← Adversarial Critic
Step 6 Note Realizer      ← Composer (low-level)
Step 7 Renderer           ← Mix Engineer
```

---

## 14. Cognitive Protocol: 6 Phases × 7 Steps

YaO v1.0 had a **6-phase cognitive protocol** (Intent → Architectural Sketch → Skeletal → Critic Dialogue → Filling → Listening). YaO v2.0 keeps this protocol and **maps it onto the 7-step pipeline**, resolving v1.0's ambiguity:

| Cognitive Phase | Pipeline Steps |
|---|---|
| 1. Intent Crystallization | (pre-pipeline) → finalize `intent.md` |
| 2. Architectural Sketch | Step 1 (Form Planner) + trajectory.yaml |
| 3. Skeletal Generation | Steps 2–5 produce 5 candidate plans |
| 4. Critic-Composer Dialogue | Critic Gate selects/integrates winning plan |
| 5. Detailed Filling | Steps 6–7 realize and render |
| 6. Listening Simulation | Perception Layer evaluates → divergence triggers replan |

This eliminates the v1.0 ambiguity where Phase 4 ("dialogue") had no concrete pipeline mechanism.

### Multi-candidate generation

Step 3's "5 candidates" is a real implementation, not a metaphor. The Conductor instantiates 5 parallel pipelines through Steps 2–5 with different seeds. The Critic ranks all five plans; the Producer either picks a winner or instructs Composer to merge strengths.

---

## 15. Custom Commands

| Command | Status (v2.0 target) | Purpose |
|---|---|---|
| `/sketch` | Full impl | NL → spec dialogue (state machine) |
| `/compose <project>` | Multi-candidate | Generate using full pipeline |
| `/critique <iteration>` | Plan-level | Rule-based adversarial critique |
| `/regenerate-section <project> <section>` | Plan-aware | Replan only affected section |
| `/morph <from> <to> <bars>` | Plan-vector op | Interpolate between two plans |
| `/improvise <input>` | Live mode | Real-time accompaniment (Phase 5) |
| `/explain <element>` | Plan-traced | Trace decision through MPIR provenance |
| `/diff <iter_a> <iter_b>` | Plan + score | Diff at plan and score levels |
| `/render <iteration>` | Production-aware | Apply manifest, render audio |
| `/arrange <project>` | Full engine | MIDI in → arranged MIDI out + diff |
| `/preview` | New | In-memory instant playback |
| `/watch <spec>` | New | File-watch + auto-regenerate + auto-play |
| `/annotate <iteration>` | New | Browser UI for time-tagged feedback |

Each command has a corresponding `.claude/commands/<name>.md` definition.

### Command implementations link to capability matrix

If the matrix says a command is `🟡 Partial`, the command tells the user. We do not pretend.

---

## 16. Skills & Knowledge

### 16.1 Genre Skills (target: 12 in Phase β)

```
.claude/skills/genres/
├── cinematic.md          ✅
├── lofi_hiphop.md        🔴
├── j_pop.md              🔴
├── neoclassical.md       🔴
├── ambient.md            🔴
├── jazz.md               🔴
├── edm.md                🔴
├── folk.md               🔴
├── game_bgm.md           🔴
├── anime_bgm.md          🔴
├── rock.md               🔴
├── orchestral.md         🔴
```

Each genre Skill has both a **Markdown form** (for Subagent prompts) and a **YAML form** (for programmatic Generator use). They never desync because the YAML is generated from the Markdown front-matter.

### 16.2 Theory Skills

`.claude/skills/theory/` covers voice leading, reharmonization, counterpoint, modal interchange, secondary dominants, etc. Each entry has examples and counter-examples; rules are tagged with genre dependencies.

### 16.3 Instrument Skills

Each of the 38+ supported instruments has a Skill with range, idiomatic patterns, articulation, frequency profile, and characteristic phrases.

### 16.4 Psychology Skills

Empirical music-psychology mappings (Krumhansl, Huron, Juslin & Sloboda) for the Perception Layer's psych mapper.

---

## 17. Hooks & Automation

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | git commit | YAML schema check, music21 lint, golden test smoke |
| `post-generate-render` | after `compose`/`arrange` | Auto-render audio, auto-write critique |
| `post-generate-critique` | after generation | Run rule-based critique, persist `critique.json` |
| `update-provenance` | any plan/score change | Append to provenance log |
| `spec-changed-show-diff` | edit spec | Show what changed musically (MPIR-level) |

Hooks ensure the Capability Matrix discipline: even if an agent forgets, the hook does not.

---

## 18. MCP Integration

| MCP Target | Purpose | Status |
|---|---|---|
| **Reaper DAW** | Project file read/write, track layout | Phase γ |
| **Sample library** | Search/fetch drum samples, one-shots | Phase γ |
| **Reference DB** | Rights-cleared reference catalog | Phase γ |
| **MIDI controller** | Live mode input | Phase δ |
| **SoundFont/VST host** | Tone rendering | Phase γ |
| **Cloud storage** | Artifact backup, team share | Phase δ |

Each MCP integration is gated on the corresponding capability flag.

---

## 19. Quality Assurance

### 19.1 Three-tier testing

| Tier | Purpose | Examples |
|---|---|---|
| **Unit / Integration** | Module correctness | 226+ tests, current |
| **Golden MIDI** | Detect unintended musical regression | Fixed seed × spec → expected MIDI |
| **Subagent Eval** | LLM-as-Judge for Subagent prompt regression | Bad-piece fixtures → expected critique |

### 19.2 Sound-First culture (enforced)

- **PR template requires audio sample** for any change touching generators or rendering
- **Showcase auto-update**: GitHub Actions regenerates `docs/showcase/` weekly from canonical templates; visible regression = visible failure
- **Maintainer dogfooding**: every project demo, video, and announcement uses YaO-generated music

### 19.3 Document discipline

- Every PR that changes a feature must update the **Capability Matrix**
- Aspirational claims that aren't in the matrix are removed from README and PROJECT
- The matrix is the single source of truth

---

## 20. Directory Structure

```
yao/
├── CLAUDE.md                          # Agent-facing rules
├── PROJECT.md                         # This document
├── README.md                          # 30-second quickstart only
├── pyproject.toml
├── Makefile
│
├── .claude/
│   ├── commands/                      # /sketch /compose /critique /arrange /...
│   ├── agents/                        # 7 subagent definitions
│   ├── skills/
│   │   ├── genres/                    # 12 target
│   │   ├── theory/
│   │   ├── instruments/
│   │   └── psychology/
│   ├── guides/                        # architecture/coding/music/testing/workflow
│   └── hooks/                         # 5 hooks
│
├── specs/
│   ├── projects/<project>/
│   │   ├── intent.md
│   │   ├── composition.yaml           # v2 schema
│   │   ├── trajectory.yaml
│   │   ├── references.yaml
│   │   ├── negative-space.yaml
│   │   ├── arrangement.yaml           # arrangement mode only
│   │   └── production.yaml
│   ├── templates/                     # 4+ templates
│   └── fragments/                     # reusable spec fragments (Phase δ)
│
├── src/
│   ├── yao/
│   │   ├── constants/                 # Layer 0
│   │   ├── schema/                    # Layer 1
│   │   ├── ir/
│   │   │   ├── score_ir.py            # Layer 3 (notes)
│   │   │   ├── plan/                  # ★ Layer 3.5 (NEW)
│   │   │   │   ├── song_form.py
│   │   │   │   ├── harmony.py
│   │   │   │   ├── motif.py
│   │   │   │   ├── phrase.py
│   │   │   │   ├── drums.py
│   │   │   │   ├── arrangement.py
│   │   │   │   └── musical_plan.py
│   │   │   ├── trajectory.py
│   │   │   ├── timing.py
│   │   │   └── notation.py
│   │   ├── reflect/                   # Provenance (cross-cutting)
│   │   ├── generators/                # Layer 2
│   │   │   ├── plan/                  # ★ NEW: produce MPIR
│   │   │   │   ├── form_planner.py
│   │   │   │   ├── harmony_planner.py
│   │   │   │   ├── motif_developer.py
│   │   │   │   ├── drum_patterner.py
│   │   │   │   └── arranger.py
│   │   │   └── note/                  # produce ScoreIR from MPIR
│   │   │       ├── rule_based.py
│   │   │       ├── stochastic.py
│   │   │       ├── markov.py          # Phase β
│   │   │       └── constraint_solver.py # Phase β
│   │   ├── perception/                # Layer 4 (Stage 1/2/3)
│   │   ├── render/                    # Layer 5
│   │   │   ├── midi_writer.py
│   │   │   ├── audio_renderer.py
│   │   │   ├── musicxml_writer.py     # ★ NEW
│   │   │   ├── lilypond_writer.py     # ★ NEW
│   │   │   ├── strudel_emitter.py     # ★ NEW
│   │   │   └── production/            # ★ NEW: manifest, mix chain
│   │   ├── verify/                    # Layer 6
│   │   │   ├── critique/              # ★ NEW: rule-based critique
│   │   │   │   ├── registry.py
│   │   │   │   ├── melodic.py
│   │   │   │   ├── harmonic.py
│   │   │   │   ├── rhythmic.py
│   │   │   │   └── ...
│   │   │   ├── metric_goal.py         # ★ NEW
│   │   │   ├── recoverable.py         # ★ NEW
│   │   │   ├── lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py
│   │   │   └── diff.py
│   │   ├── arrange/                   # ★ NEW: Layer 5.5 — arrangement
│   │   │   ├── analyzer.py
│   │   │   ├── plan_extractor.py
│   │   │   ├── style_vector.py
│   │   │   ├── transformer.py
│   │   │   └── differ.py
│   │   ├── conductor/
│   │   │   ├── conductor.py
│   │   │   ├── multi_candidate.py     # ★ NEW
│   │   │   └── feedback.py
│   │   ├── sketch/                    # ★ NEW
│   │   │   ├── dialogue.py            # state machine
│   │   │   └── compiler.py            # NL → spec
│   │   └── errors.py
│   └── cli/
│
├── drum_patterns/                     # ★ NEW: 12+ genre drum YAML
├── references/
│   ├── catalog.yaml                   # rights status required
│   ├── extracted_features/
│   └── (audio/MIDI excluded from repo)
├── soundfonts/                        # gitignored
├── outputs/                           # gitignored
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── music_constraints/
│   ├── scenarios/
│   ├── golden/                        # ★ NEW
│   └── subagent_evals/                # ★ NEW
├── tools/
│   ├── architecture_lint.py
│   └── capability_matrix_check.py     # ★ NEW
└── docs/
    ├── for-musicians/                 # ★ NEW: tutorials
    ├── for-developers/
    ├── design/                        # ADRs
    └── showcase/                      # ★ NEW: dogfood pieces
```

---

## 21. Roadmap (180-day Plan)

The roadmap is organized around the **vertical alignment principle**: each phase advances input, processing, and evaluation together.

### Phase α (Days 1–30): The Foundation of Alignment

**Goal**: Build the scaffolding so that the three layers can advance in lockstep.

- [ ] **Capability Matrix** introduced and adopted in README, PROJECT, CLAUDE
- [ ] **composition.yaml v2 schema** designed and Pydantic-implemented
- [ ] **intent.md and trajectory.yaml** integrated as first-class artifacts
- [ ] **Musical Plan IR (MPIR)** minimal version: SongFormPlan + HarmonyPlan
- [ ] **MetricGoal** type system implemented
- [ ] **RecoverableDecision** logging mechanism
- [ ] **Golden test infrastructure**

**Milestone**: existing rule_based generator works through composition v2 → MPIR(form+harmony) → Note Realizer 3-stage pipeline. Capability matrix accurate.

### Phase β (Days 31–75): Plan-Layer Maturity & Mechanized Critique

**Goal**: Complete the Plan IR; mechanize critique.

- [ ] MotifPlan / PhrasePlan / DrumPattern / ArrangementPlan implemented
- [ ] Motif Developer Generator (plan-level)
- [ ] Drum Patterner + 12 `drum_patterns/*.yaml`
- [ ] Adversarial Critic: 30+ rules across 6 roles
- [ ] Trajectory wired as common control signal across all Plan Generators
- [ ] Multi-candidate Conductor (5 candidates → critic-rank → producer-pick)
- [ ] Markov + constraint_solver Note Realizers
- [ ] Subagent eval harness

**Milestone**: Adversarial Critic generates structured findings against MPIR (e.g., "chorus uses cliche I-V-vi-IV without secondary dominants — recommend V/V"). Multi-candidate conductor demonstrably picks better plans.

### Phase γ (Days 76–120): Differentiation — Perception & Arrangement

**Goal**: Implement YaO's distinctive layers.

- [ ] Perception Stage 1 (audio features, librosa + pyloudnorm)
- [ ] Perception Stage 2 (use-case targeted: BGM/Game/Ad/Study)
- [ ] Counter-melody Generator
- [ ] 12 Genre Skills with paired Markdown + YAML
- [ ] **Arrangement Engine** (the marquee feature):
  - SourcePlan extractor
  - Style vector operations
  - Preservation/transformation contract
  - TargetPlan realizer
  - Arrangement Diff Markdown report
- [ ] MusicXML / LilyPond writers
- [ ] Reference Matcher (Stage 3, abstract features only)

**Milestone**: existing MIDI → arranged MIDI in different genre, with structured diff explaining what was preserved and what changed. Use-case driven evaluation switching observably.

### Phase δ (Days 121–180): Production Readiness

**Goal**: Real-project-grade output and operations.

- [ ] Production Manifest + Mix Chain (pedalboard)
- [ ] Sketch-to-Spec dialogue state machine
- [ ] Instant audition: `yao preview`, `yao watch`
- [ ] Strudel emitter (browser-side instant audition)
- [ ] `yao annotate` browser UI for time-tagged feedback
- [ ] mkdocs site complete: `for-musicians/`, `for-developers/`
- [ ] Showcase: 10+ canonical YaO pieces, weekly auto-updated
- [ ] Reaper MCP integration (initial)
- [ ] Spec composability (`extends:`, `overrides:`, `fragments/`)

**Milestone**: a commercial BGM creator can use YaO end-to-end and import the result into a DAW for finishing.

### Phase ε (Continuous): Reflection & Community

- Reflection Layer (Layer 7) for user style profiles
- Community reference library shared format
- Live improvisation mode
- AI music model bridges (Stable Audio, MusicGen) for texture

---

## 22. Quick Start

### 22.1 Setup

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
```

### 22.2 First piece

```bash
make new-project NAME=my-first-song

# Launch Claude Code
claude

# In Claude Code:
> /sketch
> "A calm piano piece for a rainy night cafe, 90 seconds, slightly melancholic"
> (dialogue refines spec)
> /compose my-first-song
> /critique my-first-song
> /regenerate-section my-first-song chorus
> /render my-first-song
```

### 22.3 Arranging an existing piece

```bash
cp my_song.mid specs/projects/my-arrangement/source.mid
> /arrange my-arrangement --target-genre lofi_hiphop --preserve melody
```

---

## 23. File Formats & Interoperability

| Use | Format | Why |
|---|---|---|
| Music data | MIDI, MusicXML | Universal, all DAWs |
| Score | LilyPond → PDF | Engraving quality |
| Spec | YAML | Human + git friendly |
| MPIR | JSON | Programmatic + schema-validatable |
| Provenance | JSON (append-only log) | Graph-friendly |
| Audio | WAV (work), FLAC/MP3 (release) | Standard |
| Live | Strudel string | Browser instant |

We use existing standards. Custom formats are introduced only when no standard suffices.

---

## 24. Ethics & Licensing

### 24.1 References must be cleared

`references/catalog.yaml` requires a `rights_status` field for every entry. Unknown-status pieces are forbidden. Pre-commit hook enforces this.

### 24.2 No artist-name imitation

The schema **rejects** identifying artist references in style fields:

```yaml
# ✗ Blocked at schema validation
style: "Joe Hisaishi style"

# ✓ Required form
style:
  features:
    - "wide open string voicings"
    - "ascending stepwise motifs"
    - "major-minor ambiguity"
    - "meditative tempos"
```

### 24.3 Output rights

YaO-generated pieces' rights belong to the user. If `provenance.json` shows extreme reference influence (>0.85 similarity on multiple axes), a warning is emitted.

### 24.4 Transparency

Every output includes a `provenance.json` summary listing:
- Generator strategy and seed
- Reference influences (with similarity scores)
- Subagent decisions
- Recoverable decisions taken

---

## 25. Document Roles

To prevent the v1.0 problem of overlapping content:

| Document | Single role | Forbidden content |
|---|---|---|
| `README.md` | 30-second quickstart | Philosophy, principles |
| `PROJECT.md` (this) | Design philosophy + architecture | Implementation status (link to matrix) |
| `CLAUDE.md` | Inviolable dev rules | Re-explanation of principles (link here) |
| Capability Matrix | Authoritative status of every feature | Aspirational entries |
| `docs/for-musicians/` | User tutorials | Internals |
| `docs/for-developers/` | Dev guides | User concerns |
| `docs/design/<NNNN>-*.md` | ADRs | Anything not a decision |
| `docs/showcase/` | Dogfooded pieces | Marketing copy |

The Capability Matrix is the **single mutable truth source for what works**. README, PROJECT, CLAUDE all link to it instead of restating capabilities.

---

## 26. Future Architecture Extensions

### 26.1 Project runtime (stateful sessions)
Replace stateless CLI with a `ProjectRuntime` that holds generation cache, feedback queue, undo/redo stack. Phase ε.

### 26.2 Backend-agnostic agent protocol
Abstract `AgentRole`, `AgentContext`, `AgentOutput` Python protocols; Claude Code becomes one adapter among possible others. Phase ε.

### 26.3 Spec composability
`extends:`, `overrides:`, `specs/fragments/` for reusable spec parts. Phase δ.

### 26.4 Reflection layer (Layer 7)
User style profiles learned from feedback history; cross-project pattern mining. Phase ε.

### 26.5 Generic creative-domain framework
Abstract YaO patterns (intent-as-code, trajectory, plan IR, adversarial critic, provenance) into a domain-agnostic toolkit. Phase ε+.

---

## 27. Glossary

**Conductor (You)** — the human owning the project; the final judge.

**Orchestra** — the collection of subagents.

**Score** — the YAML+Markdown specs.

**MPIR (Musical Plan IR)** — Layer 3.5; the central abstraction of v2.0; a complete pre-realization plan of the piece.

**Trajectory** — multi-dimensional time-axis curves (tension/density/predictability/brightness/register).

**Aesthetic Reference Library** — rights-cleared reference pieces compared on abstract features only.

**Perception Substitute Layer** — Layer 4; substitutes for the AI's inability to listen.

**Provenance** — append-only decision log; every generated element traceable.

**Adversarial Critic** — subagent whose only job is to find weaknesses; never praises.

**Negative Space** — designed silence/gaps/omissions; absence as composition.

**Style Vector** — multi-dimensional feature representation of a genre or piece, used in arrangement.

**Iteration** — versioned generation result (v001, v002, …).

**Music Lint** — automated detection of music-theory violations.

**Sketch-to-Spec** — interactive dialogue that crystallizes natural-language intent into YAML.

**RecoverableDecision** — logged compromise; a non-silent fallback with full musical context.

**MetricGoal** — typed evaluation goal (AT_LEAST / TARGET_BAND / MATCH_CURVE / …) replacing one-size-fits-all tolerance checks.

**Capability Matrix** — the authoritative status table of every YaO feature.

**Vertical Alignment** — the principle that input expressiveness, processing depth, and evaluation resolution must advance together.

**Music-as-Plan** — YaO's evolved philosophy: the plan, not the code, is the substance.

---

## 28. Closing

YaO v2.0 makes a bet:

> **The future of agentic music production lies not in better generators, but in deeper *plans*.**

A black-box generator can produce surprising notes. Only a planning system can produce music that has *reasons*. Reasons are what humans listen for, edit, argue about, and share.

By introducing the Musical Plan IR as the heart of the architecture, YaO becomes the only environment where:

- The Conductor (you) can inspect, edit, and critique the plan before any note is written
- The Orchestra (subagents) divide labor along the planning structure, not along arbitrary code modules
- The Critic operates with surgical precision because plans are inspectable
- Arrangement becomes principled transformation, not pitch-shuffling
- Provenance is meaningful, because the *why* of every note traces back to a plan element

This is what we mean by "Music-as-Plan." This is what makes YaO different from any AI music tool that has come before.

---

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to plan, perform, and grow with you.*

---

**Project: You and Orchestra (YaO)**
*PROJECT.md version: 2.0*
*Supersedes: PROJECT.md v1.0 (2026-04-27)*
*Last revised: 2026-04-29*