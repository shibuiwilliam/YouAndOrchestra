# PROJECT.md — You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*
> *Document version: 2.0 — incorporates Phase 1.5 multi-genre foundation*

---

## 0. The Essence of the Project

**You and Orchestra (YaO)** is an **agentic music production environment** built on Claude Code. Unlike a typical "AI music tool" that emits a single piece of music from a black box, YaO is structured as **a team of role-specialized AI subagents (the Orchestra) directed by a human (You = Conductor)**.

Every design decision in YaO follows from a single proposition:

> **Music production is not a one-off act of inspiration; it is a reproducible, improvable creative engineering process.**

For this reason, YaO treats music as **code, specs, tests, diffs, and provenance** before treating it as audio. We call this the **Music-as-Code** philosophy.

YaO version 2.0 extends version 1.0 in one critical direction: **multi-genre quality at scale**. Where version 1.0 was implicitly biased toward Western tonal chamber and pop music, version 2.0 introduces a Tonal System abstraction, a Sound Design layer, an enforced cognitive protocol, and a richer subagent roster — all designed to make YaO equally capable across genres ranging from baroque counterpoint to deep house, modal jazz to ambient drone, J-pop to Indian classical music.

---

## 1. Metaphor: You and Orchestra

Every concept in YaO maps onto an orchestral metaphor. Internalizing this mapping is the shortest path to using YaO correctly.

| YaO Concept | Orchestral Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human project owner |
| **Score** | Sheet music | YAML specs in `specs/` |
| **Orchestra Members** | Section players | Subagents (Composer, Critic, Theorist, etc.) |
| **Concertmaster** | Lead violinist | Producer Subagent (overall coordinator) |
| **Rehearsal** | Run-through | Generate–evaluate–adapt loop |
| **Library** | Sheet music archive | `references/` (rights-cleared anchor pieces) |
| **Performance** | Live performance | Rendered final audio |
| **Recording** | Recording session | `outputs/` artifacts |
| **Critic** | Resident critic | Adversarial Critic Subagent |
| **Ensemble Template** | Group format (string quartet, big band, DJ duo) | First-class genre-aware role configuration |

The Conductor (you) does not write every note. The Conductor's job is to **clarify intent, give direction, make decisions during rehearsal, and guarantee the quality of the final performance**. YaO brings this division of labor to AI-assisted music production.

---

## 2. Design Principles

Every implementation decision in YaO is judged against these **five non-negotiable principles**. They are repeated in CLAUDE.md and must be reconciled with every change to the codebase.

### Principle 1: The agent is an environment, not a composer
YaO is "a 10×-faster human composition environment", not "an AI that composes music". Full automation is not a goal; accelerating and extending human creative judgment is.

### Principle 2: Every decision must be explainable
Every generated note, chord, and arrangement choice carries a reason. These reasons are persisted in the Provenance Graph as an audit trail that can be queried, reviewed, and modified.

### Principle 3: Constraints liberate creativity
Explicit specs (YAML), reference libraries, negative-space designs, and theory rules are scaffolding, not cages. Unbounded freedom produces paralysis; bounded freedom produces music.

### Principle 4: Design the time axis before the notes
A piece is first sketched as **trajectory curves on the time axis** (tension, density, valence, predictability), and only then are notes filled in. This ensures structural coherence.

### Principle 5: The human ear is the final truth
No matter how sophisticated automated metrics become, listener experience is the ultimate judge. Subagents **support** human judgment; they do not **replace** it.

---

## 3. Architecture: 8-Layer Model

YaO v2.0 introduces a new layer (Sound Design) between IR and Render, and elevates Perception from "planned" to first-class. The result is an 8-layer pipeline; each layer has an independent input/output contract and can be swapped or tested in isolation.

```
┌─────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                          │
│   Cross-project learning, user style profiling           │
├─────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                        │
│   Structural, harmonic, rhythmic, acoustic evaluation    │
│   Adversarial critique, idiomaticity checks              │
├─────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                      │
│   MIDI → audio (per stem + mixdown), score PDF, live    │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute  (NEW in v2.0)           │
│   Reference matching, psychological mapping, surprise    │
│   model — substitutes for "the LLM cannot hear"          │
├─────────────────────────────────────────────────────────┤
│ Layer 3.5: Sound Design  (NEW in v2.0)                  │
│   Synthesis patches, effect chains, sample packs         │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)               │
│   ScoreIR, harmony, motif, voicing, timing, notation     │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                            │
│   Rule-based, stochastic, loop_evolution, Markov,        │
│   constraint solver, AI-bridge (planned)                 │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                  │
│   YAML specs, dialog input, sketch input, schemas        │
├─────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                      │
│   Instrument ranges, MIDI maps, scales, chords, dynamics │
└─────────────────────────────────────────────────────────┘
```

Inter-layer dependency flows strictly downward: lower layers know nothing of upper layers. Swapping Layer 2 from rule-based to a neural model leaves Layer 1 untouched.

### Why Layers 4 and 3.5 Are Required for Multi-Genre Quality

**Layer 4 (Perception Substitute) closes the "the LLM cannot hear" gap.** Without it, the system optimizes formal metrics (note counts, consonance ratios) that have no robust correlation with listener satisfaction. With it, the Conductor can act on whether the music sounds *good*, not just whether it is *correct*.

**Layer 3.5 (Sound Design) closes the "MIDI is not music" gap.** Modern music — anything past 1980 — is half timbre. Treating timbre as a General MIDI program number cannot represent the difference between an 808 kick and an acoustic kick, or between a dusty lo-fi piano and a Bösendorfer recital. With Sound Design as a first-class concept, YaO can render genres where timbre defines the genre.

---

## 4. Directory Structure (v2.0)

```
yao/
├── CLAUDE.md                       # Instructions to Claude Code
├── PROJECT.md                      # This document
├── README.md                       # User quickstart
├── pyproject.toml
├── Makefile
├── uv.lock
│
├── .claude/
│   ├── commands/                   # Custom slash commands
│   │   ├── compose.md
│   │   ├── arrange.md
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md
│   │   ├── explain.md
│   │   ├── regenerate-section.md
│   │   ├── sketch.md
│   │   └── tweak.md                # NEW v2.0 — natural-language adjustments
│   │
│   ├── agents/                     # Subagent definitions
│   │   ├── _protocol.md            # NEW v2.0 — message format, arbitration
│   │   ├── producer.md
│   │   ├── composer.md             # Lead Voice Composer (renamed)
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   ├── sound-designer.md       # NEW v2.0
│   │   ├── sample-curator.md       # NEW v2.0
│   │   ├── texture-composer.md     # NEW v2.0
│   │   ├── beatmaker.md            # NEW v2.0
│   │   └── loop-architect.md       # NEW v2.0
│   │
│   ├── skills/                     # Domain knowledge modules
│   │   ├── genres/
│   │   │   ├── _template.md        # NEW v2.0 — Skill standard
│   │   │   ├── cinematic.md
│   │   │   ├── lo_fi_hiphop.md     # NEW v2.0
│   │   │   ├── pop_japan.md        # NEW v2.0
│   │   │   ├── ambient.md          # NEW v2.0
│   │   │   ├── deep_house.md       # NEW v2.0
│   │   │   ├── pop_western.md      # NEW v2.0
│   │   │   └── (Tier 2 / 3 genres added incrementally)
│   │   │
│   │   ├── theory/
│   │   │   ├── voice-leading.md
│   │   │   ├── reharmonization.md
│   │   │   ├── counterpoint.md
│   │   │   ├── modal-interchange.md
│   │   │   ├── modal-harmony.md    # NEW v2.0 — non-functional harmony
│   │   │   ├── microtonal.md       # NEW v2.0
│   │   │   └── atonal-techniques.md # NEW v2.0 — 12-tone, set theory
│   │   │
│   │   ├── instruments/
│   │   │   ├── piano.md
│   │   │   ├── strings.md
│   │   │   ├── drums.md
│   │   │   ├── synths.md
│   │   │   ├── voice.md            # NEW v2.0
│   │   │   └── playability/        # NEW v2.0 — physical constraints
│   │   │       ├── violin.yaml
│   │   │       ├── piano.yaml
│   │   │       └── ...
│   │   │
│   │   └── psychology/
│   │       ├── tension-resolution.md
│   │       ├── valence-arousal.md  # NEW v2.0
│   │       ├── memorability.md
│   │       ├── surprise-and-expectation.md  # NEW v2.0
│   │       └── flow-and-attention.md         # NEW v2.0
│   │
│   ├── guides/                     # Developer guidance (v1.0 retained)
│   │   ├── architecture.md
│   │   ├── coding-conventions.md
│   │   ├── music-engineering.md
│   │   ├── testing.md
│   │   └── workflow.md
│   │
│   └── hooks/                      # Auto-executed scripts
│       ├── pre-commit-lint.sh
│       ├── post-generate-render.sh
│       ├── post-generate-critique.sh
│       └── update-provenance.sh
│
├── specs/
│   ├── projects/
│   │   └── <project_name>/
│   │       ├── intent.md
│   │       ├── composition.yaml
│   │       ├── tonal_system.yaml   # NEW v2.0 (or nested in composition)
│   │       ├── trajectory.yaml
│   │       ├── references.yaml
│   │       ├── negative-space.yaml
│   │       ├── sound_design.yaml   # NEW v2.0
│   │       ├── arrangement.yaml    # only when arranging
│   │       └── production.yaml
│   │
│   ├── templates/
│   │   ├── minimal.yaml
│   │   ├── bgm-90sec.yaml
│   │   ├── cinematic-3min.yaml
│   │   ├── lofi-loop-2min.yaml     # NEW v2.0
│   │   ├── ambient-5min.yaml       # NEW v2.0
│   │   ├── deep-house-club.yaml    # NEW v2.0
│   │   ├── pop-jp-3min.yaml        # NEW v2.0
│   │   └── trajectory-example.yaml
│   │
│   └── fragments/                  # NEW v2.0 — composable spec fragments
│       ├── progressions/
│       ├── grooves/
│       └── timbres/
│
├── src/
│   └── yao/
│       ├── constants/              # Layer 0
│       ├── schema/                 # Layer 1
│       │   ├── composition.py
│       │   ├── tonal_system.py     # NEW v2.0
│       │   ├── trajectory.py
│       │   ├── constraints.py
│       │   ├── references.py       # NEW v2.0
│       │   ├── sound_design.py     # NEW v2.0
│       │   ├── duration.py         # NEW v2.0 — polymorphic duration
│       │   └── ensemble.py         # NEW v2.0 — ensemble templates
│       │
│       ├── ir/                     # Layer 3
│       │   ├── score_ir.py
│       │   ├── note.py
│       │   ├── harmony.py          # multi-system realize()
│       │   ├── motif.py
│       │   ├── voicing.py
│       │   ├── timing.py
│       │   └── notation.py         # extended for cents offset
│       │
│       ├── generators/             # Layer 2
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── rule_based.py
│       │   ├── stochastic.py
│       │   ├── loop_evolution.py   # NEW v2.0
│       │   ├── markov.py           # planned
│       │   ├── constraint_solver.py # planned
│       │   └── ai_bridge.py        # planned
│       │
│       ├── sound_design/           # Layer 3.5 — NEW v2.0
│       │   ├── patches/
│       │   ├── effects/
│       │   ├── samples/
│       │   └── vst_bridge.py
│       │
│       ├── perception/             # Layer 4 — NEW v2.0
│       │   ├── reference_matcher.py
│       │   ├── psych_mapper.py
│       │   ├── surprise_model.py
│       │   ├── style_vector.py
│       │   └── feature_extractors/
│       │
│       ├── render/                 # Layer 5
│       │   ├── midi_writer.py
│       │   ├── stem_writer.py
│       │   ├── audio_renderer.py
│       │   ├── lilypond_writer.py
│       │   └── strudel_emitter.py
│       │
│       ├── verify/                 # Layer 6
│       │   ├── music_lint.py
│       │   ├── analyzer.py
│       │   ├── evaluator.py        # genre-conditional
│       │   ├── idiomaticity.py     # NEW v2.0
│       │   ├── singability.py      # NEW v2.0
│       │   ├── seamlessness.py     # NEW v2.0
│       │   ├── diff.py
│       │   └── constraint_checker.py
│       │
│       ├── reflect/                # Layer 7 + cross-cutting provenance
│       │   ├── provenance.py
│       │   ├── feedback_loop.py
│       │   └── style_profile.py    # planned
│       │
│       ├── conductor/              # Orchestration engine
│       │   ├── conductor.py
│       │   ├── feedback.py
│       │   ├── result.py
│       │   ├── protocol.py         # NEW v2.0 — six-phase enforcement
│       │   └── adaptations/        # NEW v2.0 — strategy library
│       │       ├── base.py
│       │       ├── transpose_section.py
│       │       ├── instrument_swap.py
│       │       ├── texture_change.py
│       │       └── ...
│       │
│       └── cli/
│
├── references/                     # Aesthetic reference library
│   ├── catalog.yaml
│   ├── midi/
│   ├── musicxml/
│   └── extracted_features/
│
├── outputs/
│   └── projects/
│       └── <project>/
│           ├── iterations/
│           │   └── v001/
│           │       ├── stems/
│           │       │   ├── *.mid       # symbolic per stem
│           │       │   └── *.wav       # audio per stem (NEW v2.0)
│           │       ├── full.mid
│           │       ├── audio.wav
│           │       ├── score.musicxml
│           │       ├── score.pdf
│           │       ├── analysis.json
│           │       ├── evaluation.json
│           │       ├── critique.md
│           │       └── provenance.json
│           └── final/
│
├── soundfonts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── music_constraints/
│   ├── scenarios/
│   ├── golden/
│   └── helpers.py
│
├── tools/
│   └── architecture_lint.py
│
└── docs/
    ├── design/
    ├── tutorials/
    └── glossary.md
```

---

## 5. The Orchestra: Subagent Roster (v2.0)

YaO v2.0 expands the subagent roster from seven to twelve. The seven original subagents remain, but five new subagents handle genres where the original roster's assumptions (melody-first, harmonic-functional, acoustic-instrument) do not apply. **Not all subagents are active for every composition** — the `ensemble_template` selects a coherent subset.

### 5.1 Producer (concertmaster, always active)
**Responsibility:** Coordinate all subagents, arbitrate conflicts, dialogue with the conductor (human), make final decisions.
**Inputs:** Outputs of all active subagents + human feedback.
**Outputs:** Final production decisions, instructions for the next iteration.
**Privilege:** Sole subagent that can override others.
**Evaluation criterion:** Fidelity to `intent.md`.
**Arbitration priority** (top to bottom):
1. `intent.md` alignment
2. Hard constraints (`must` / `must_not`)
3. Active genre Skill recommendations
4. Expected evaluator score improvement
5. Subagent default preferences (Composer or its replacement is the default tiebreaker)

### 5.2 Composer (Lead Voice Composer)
**Active for:** Genres with a clear lead voice (classical, jazz, pop, rock, folk).
**Inactive for:** Genres without lead voice (deep house, ambient, drone, plunderphonics).
**Responsibility:** Generate melody, theme, large-scale structure.
**Inputs:** `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`, active genre Skill.
**Outputs:** Score IR (motifs, melodic lines, structural outline).
**Forbidden:** Choosing instruments or final voicings (those belong to Orchestrator).
**Evaluation criterion:** Motif memorability, repetition/variation balance, fit to trajectory.

### 5.3 Harmony Theorist
**Active for:** All genres with a harmonic dimension.
**Responsibility:** Chord progressions, modulation, secondary dominants, cadences, reharmonization.
**Inputs:** Composer's melody draft, `composition.yaml.harmony`, active genre Skill.
**Outputs:** Harmony IR (functional notation + concrete voicing candidates).
**Evaluation criterion:** Functional integrity, tension resolution, genre fit.

### 5.4 Rhythm Architect
**Active for:** Genres without a dedicated Beatmaker (acoustic, classical, jazz).
**Responsibility:** Drum patterns, groove, syncopation, fills.
**Inputs:** `composition.yaml.rhythm`, active genre Skill.
**Outputs:** Rhythm IR for all parts.
**Evaluation criterion:** Groove feel, humanness, inter-section contrast.

### 5.5 Orchestrator
**Active for:** All genres.
**Responsibility:** Instrument assignment, voicing, register placement, counter-melody.
**Inputs:** Outputs from Composer, Harmony, Rhythm (or their replacements).
**Outputs:** Complete Score IR (per-instrument fully populated parts).
**Evaluation criterion:** Frequency-space conflict avoidance, idiomaticity, texture density.

### 5.6 Adversarial Critic
**Active for:** All genres.
**Responsibility:** Find every weakness; never praise.
**Inputs:** Any artifact in the pipeline.
**Outputs:** `critique.md` with severity-ranked issues.
**Critique observatory:** clichés, structural boredom, emotional misalignment, derivative similarity to known works, idiomatic violations, genre-frame breaks.
**Evaluation criterion:** Coverage and specificity of weaknesses found.

### 5.7 Mix Engineer
**Active for:** All genres when audio rendering is enabled.
**Responsibility:** Stereo placement, dynamics, frequency masking resolution, loudness (LUFS).
**Inputs:** Orchestrator output + `production.yaml`.
**Outputs:** Mix instruction sheet for each track (EQ / compression / reverb / pan).
**Evaluation criterion:** LUFS target, frequency balance, stereo width.

### 5.8 Sound Designer (NEW v2.0)
**Active for:** Electronic, ambient, lo-fi, modern pop, hybrid orchestral, and any genre where timbre defines identity.
**Responsibility:** Synth patches, filter modulation, effect chains, timbre evolution.
**Inputs:** `sound_design.yaml`, active genre Skill's default sound design.
**Outputs:** Per-instrument synthesis specs and effect chains.
**Evaluation criterion:** Timbre coherence, genre frame fit, frequency-spectrum design.

### 5.9 Sample Curator (NEW v2.0)
**Active for:** Hip-hop, house, plunderphonics, sample-based electronic music.
**Responsibility:** Sample selection, chop/repitch/timestretch decisions, sample layering.
**Inputs:** Sample library, project intent.
**Outputs:** Sample assignments with edit instructions.
**Evaluation criterion:** Genre fit, copyright safety, layering coherence.

### 5.10 Texture Composer (NEW v2.0)
**Active for:** Ambient, drone, dark ambient, sound art, contemporary classical.
**Responsibility:** Long-form pad/drone design, slow modulation, spectral evolution.
**Inputs:** Trajectory (especially density and spectral curves), `intent.md`.
**Outputs:** Texture descriptions in IR, including continuous-time events.
**Evaluation criterion:** Spectral evolution coherence, attention sustain, no abrupt discontinuities.

### 5.11 Beatmaker (NEW v2.0)
**Active for:** Trap, drum-and-bass, footwork, breakbeat, lo-fi hip-hop.
**Responsibility:** 808 patterns, swing/shuffle, ghost notes, micro-timing, hi-hat rolls.
**Inputs:** Tempo, genre Skill's groove templates.
**Outputs:** Drum and bass parts in IR.
**Evaluation criterion:** Groove pocket, swing accuracy, 808 sub-bass placement.

### 5.12 Loop Architect (NEW v2.0)
**Active for:** EDM, house, techno, ambient, hip-hop, game BGM.
**Responsibility:** Core loop + variation strategy, build/drop/breakdown structure, layer evolution.
**Inputs:** `arrangement` block layout, `trajectory.yaml`.
**Outputs:** Loop layer assignments, evolution timeline.
**Evaluation criterion:** Seamlessness, evolution interest, build/drop impact.

### 5.13 Ensemble Templates

The active subagent set is determined by `ensemble_template`:

```yaml
ensemble_template: classical_chamber
# active: producer, composer, harmony_theorist, rhythm_architect, orchestrator,
#         adversarial_critic, mix_engineer
```

```yaml
ensemble_template: hip_hop_producer
# active: producer, sample_curator, beatmaker, loop_architect, sound_designer,
#         orchestrator, mix_engineer, adversarial_critic
# inactive: composer, harmony_theorist, rhythm_architect
```

```yaml
ensemble_template: ambient_solo
# active: producer, texture_composer, sound_designer, mix_engineer,
#         adversarial_critic
# inactive: composer, harmony_theorist, rhythm_architect, beatmaker, loop_architect
```

```yaml
ensemble_template: custom
active_subagents: [...]
inactive_subagents: [...]
```

The Producer validates that the active set is coherent for the declared genre.

---

## 6. Compositional Cognitive Protocol: 6 Phases (Enforced in v2.0)

`yao compose` and `yao conduct` execute six phases **in strict order**. v2.0 enforces this in code via `conductor/protocol.py`; phases cannot be skipped without `--force-phase` (debug only). This prevents the most common LLM failure mode: starting to write notes before the structure has been designed.

### Phase 1: Intent Crystallization
Distill the user's input (dialog / YAML / sketch) into a 1–3 sentence statement of essence. Ambiguity is not allowed. Persisted in `intent.md`.

> Example: *"Early-summer morning. The forward-leaning anticipation of a new challenge, with a faint thread of anxiety. Fresh but not saccharine, sentimental but not heavy."*

**Required artifact:** `intent.md`.

### Phase 2: Architectural Sketch
Draw the time-axis trajectories (tension / density / valence / predictability / genre-specific axes such as filter cutoff for EDM) **before any notes are written**. Persisted in `trajectory.yaml`.

**Required artifact:** `trajectory.yaml`.

### Phase 3: Skeletal Generation
Composer (or replacement subagent) generates 5–10 candidate "seeds": chord progressions and main thematic elements at ~60% completeness. Diversity is required.

**Required artifact:** `score_skeleton.json` containing all candidates.

### Phase 4: Critic-Composer Dialogue
The Adversarial Critic attacks every candidate. The Producer judges, selects the strongest candidate, or instructs the Composer to synthesize a new candidate combining strengths.

**Required artifacts:** `critique_round_1.md`, `selected_skeleton.json`.

### Phase 5: Detailed Filling
Harmony, Rhythm/Beatmaker, Orchestrator, Sound Designer fill in the chosen skeleton. Every decision is recorded in Provenance.

**Required artifacts:** `full.mid`, `stems/*.mid` (and `stems/*.wav` if Sound Design active).

### Phase 6: Listening Simulation
The Perception Substitute Layer "listens" and measures distance from the original intent (Phase 1). If the gap exceeds threshold, the relevant section is regenerated. Final outputs include `critique.md` and `evaluation.json`.

**Required artifacts:** `analysis.json`, `evaluation.json`, `critique.md`.

Each phase logs entry and exit markers to `provenance.json`. Skipping a phase raises `PhaseIncompleteError`.

---

## 7. Parameter Specifications (v2.0)

YaO v2.0 expands the spec from 8 files to 9, adding `sound_design.yaml` and integrating `tonal_system` into `composition.yaml`.

### 7.1 `intent.md` (natural language, 1–3 sentences)
The essence of the piece. The ground truth for all later decisions.

### 7.2 `composition.yaml` (composition parameters)
Now includes a nested `tonal_system`:

```yaml
title: "Rainy Café"
duration: { bars: 60 }            # or { seconds: 90 } or { loops: 8, base: { bars: 4 } }
tempo_bpm: 90

tonal_system:                     # NEW v2.0 — replaces flat `key`
  kind: tonal_major_minor         # or: modal, pentatonic, blues,
                                  #     microtonal, atonal, drone, raga, maqam
  key: D
  mode: minor

time_signature: "4/4"             # or "free" for unmetered music
ensemble_template: classical_chamber

instruments:
  - name: piano
    role: melody
  - name: cello
    role: bass

sections:
  - name: intro
    duration: { bars: 4 }
    dynamics: pp
  - name: verse
    duration: { bars: 8 }
    dynamics: mp

generation:
  strategy: stochastic
  seed: 42
  temperature: 0.5
```

For prog rock or polymeter:

```yaml
sections:
  - name: bridge
    duration: { bars: 16 }
    meter_changes:
      - { at_bar: 0, time_signature: "7/8" }
      - { at_bar: 4, time_signature: "4/4" }
      - { at_bar: 8, time_signature: "5/4" }
parts:
  - name: clave
    time_signature: "3/2"          # part-level polymeter
```

### 7.3 `trajectory.yaml` (time-axis curves)
Tension, density, valence, predictability — Bezier, stepped, or linear curves. Genre-specific axes (filter_cutoff, brightness, polyrhythmic_density) supported via plugins.

### 7.4 `references.yaml` (NEW v2.0 schema)
Positive and negative aesthetic anchors:

```yaml
positive:
  - file: references/midi/anchor_001.mid
    weight: 0.7
    extract: [voice_leading_smoothness, motivic_density, surprise_index]
negative:
  - file: references/midi/cliche_001.mid
    anti_weight: 0.5
    avoid: [predictable_progression, stock_drum_pattern]
```

All references must have rights status in `references/catalog.yaml`. Unverified files are not loaded.

### 7.5 `negative-space.yaml`
Silences, frequency gaps, deliberate texture removal — operationalized in v2.0 with constraint enforcement and an evaluator metric `negative_space_compliance`.

### 7.6 `arrangement.yaml` (only for arrangement mode)
Source piece input, preservation list, transformation list, avoid list.

### 7.7 `sound_design.yaml` (NEW v2.0)
Synthesis patches and effect chains per instrument:

```yaml
instruments:
  - name: piano
    synthesis:
      kind: sample_based
      pack: "felt_piano_close_mic"
      velocity_layers: 4
    effect_chain:
      - { type: eq, bands: [...] }
      - { type: tape_saturation, drive: 0.3 }
      - { type: convolution_reverb, ir: "abbey_road_studio_2.wav", wet: 0.25 }

  - name: lead_synth
    synthesis:
      kind: subtractive
      oscillators: [{ wave: saw }, { wave: saw, detune_cents: 7 }]
      filter: { type: low_pass, cutoff_hz: 2400, resonance: 0.4 }
```

### 7.8 `production.yaml`
Master bus chain, target LUFS, stereo width.

### 7.9 `provenance.json` (auto-generated)
Append-only decision log. v2.0 adds `agent`, `phase`, `confidence`, `alternatives_rejected`, and `skill_referenced` fields per entry.

---

## 8. Custom Commands (Conductor's Baton)

| Command | Purpose | Active Subagents |
|---|---|---|
| `/sketch` | Sketch → spec dialog mode | Producer |
| `/compose <project>` | Generate from spec, all 6 phases | Per ensemble template |
| `/conduct <description>` | Natural-language → spec → loop | Per ensemble template |
| `/arrange <project>` | Transform existing composition | Orchestrator + Critic + Sound Designer |
| `/critique <iteration>` | Critique existing artifact | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section | Composer/replacement + Producer |
| `/morph <from> <to> <bars>` | Interpolate between two pieces | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment (planned) | Composer + Rhythm |
| `/explain <element>` | Explain a generation decision | Producer (queries Provenance) |
| `/diff <iter_a> <iter_b>` | Show musical diff between iterations | Verifier |
| `/render <iteration>` | Render MIDI → audio + score | Mix Engineer + Sound Designer |
| `/tweak` | Natural-language adjustments (NEW v2.0) | Per ensemble template |

`/tweak` example:

```
> /tweak rainy-cafe --section chorus --more "energetic" --less "mechanical"
> /tweak rainy-cafe --bars 17-24 --add "syncopation" --reduce "drum density"
```

Tweaks are parsed into spec deltas and run through partial regeneration.

---

## 9. Skills (Player Domain Knowledge)

Skills live in `.claude/skills/` and are referenced by subagents during their decisions.

### 9.1 Genre Skills (NEW v2.0 — standardized template)

Every Genre Skill follows the standard template (see §10). The Tier-1 set ships with v2.0:

- `cinematic` (refactored to v2.0 template)
- `lo_fi_hiphop`
- `pop_japan`
- `pop_western`
- `ambient`
- `deep_house`

Tier-2 and Tier-3 genres are added incrementally. See §10.3 for the full roadmap.

### 9.2 Theory Skills
Voice leading, reharmonization, counterpoint, modal interchange, microtonal techniques (NEW v2.0), atonal techniques (NEW v2.0). Each Skill notes exception rules and genre dependencies.

### 9.3 Instrument Skills
Per-instrument range, idiomatic playing, timbral character, and **physical playability** (NEW v2.0). Playability data is structured YAML consumed by the Orchestrator subagent.

### 9.4 Psychology Skills
Tension–resolution, valence–arousal mapping (NEW v2.0), memorability, surprise and expectation (NEW v2.0), flow and attention (NEW v2.0). Encode empirical findings from Juslin, Huron, Krumhansl.

---

## 10. Genre Skill Template Standard (NEW v2.0)

Every Genre Skill must follow this template. Skills that do not are not loaded by the Conductor.

```markdown
---
genre_id: deep_house
display_name: "Deep House"
parent_genres: [house, electronic_dance]
related_genres: [tech_house, lo_fi_house, garage]
typical_use_cases: [club_dance, late_night_chill]
ensemble_template: hip_hop_producer
default_subagents:
  active: [sound_designer, beatmaker, loop_architect, mix_engineer, producer]
  inactive: [composer, harmony_theorist]
---

## Defining Characteristics
(bullet list of canonical features)

## Required Spec Patterns
(YAML fragment of expected `composition.yaml` settings)

## Idiomatic Chord Progressions
(list with Roman-numeral notation; or modal cells, or sample-based notation)

## Idiomatic Rhythms
(ASCII drum-grid notation)

## Anti-Patterns
(used by Adversarial Critic — what would break the genre frame)

## Reference Tracks
(rights-cleared MIDI/MusicXML in `references/`)

## Default Sound Design
(YAML fragment of `sound_design.yaml` defaults)

## Evaluation Weight Adjustments
(multipliers applied to base evaluator weights)

## Default Trajectories
(YAML fragment of `trajectory.yaml` defaults)
```

### 10.1 Tier 1 — High Demand (ships with v2.0)
1. `cinematic` (expanded: hybrid orchestral)
2. `lo_fi_hiphop` (80–95 BPM, jazzy chords, vinyl noise)
3. `pop_japan` (J-pop verse / pre-chorus / chorus / D-melody)
4. `pop_western` (verse-chorus pop, hooks, lyric meter)
5. `ambient` (drone, texture, long form)
6. `deep_house` (4/4, 118–125 BPM, jazzy 7th/9th chords)

### 10.2 Tier 2 — Diversity (added in subsequent releases)
7. `jazz_standard` (ii-V-I, swing, improv hints)
8. `metal` (riff-based, palm mute, power chords)
9. `country` (chord wheel, pedal steel approximation)
10. `bossa_nova` (clave, jazz harmonization)
11. `gospel` (4-part voicing, call & response)
12. `rock_classic` (power-chord-driven, AABA)

### 10.3 Tier 3 — Cultural Breadth
13. `kpop` (multi-section, key changes)
14. `latin_salsa` (clave, horn section)
15. `afrobeat` (polyrhythm, long form)
16. `indian_classical` (raga, tala — depends on tonal system + microtonal)
17. `chiptune` (square/pulse, retro-game)
18. `synthwave` (analog nostalgia, 80s production)
19. `trap` (808s, hi-hat rolls, half-time)
20. `dnb` (170 BPM, breakbeat science)

### 10.4 Authorship Policy
Each Skill must be authored or reviewed by a human with composition experience in the target genre. LLM-only Skills produce clichés. Contribution flow:
1. Musician submits Skill draft + ≥ 3 example MIDI files + 1 project YAML.
2. Code maintainer wires the Skill into the registry, adds a regression test.
3. Borderline classifications are discussed in PRs (e.g., is "future bass" Tier-2 or Tier-3?).

---

## 11. Hooks (Auto-execution)

Hooks are scripts whose execution is **guaranteed** regardless of whether Claude Code or the user remembers to run them. They protect quality even under agent forgetfulness.

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | git commit | music21 theory lint, YAML schema validation |
| `post-generate-render` | After generation | MIDI → audio + score (per stem if Sound Design active) |
| `post-generate-critique` | After generation | Run Adversarial Critic |
| `update-provenance` | After any change | Refresh Provenance Graph |

---

## 12. MCP Integration

YaO is designed to connect with the following MCP servers:

| MCP Endpoint | Use |
|---|---|
| **DAW (Reaper preferred)** | Project file r/w, automatic track layout |
| **Sample library** | Drum sample / one-shot / loop search |
| **Reference music DB** | Rights-cleared anchor metadata + feature search |
| **MIDI controller** | Live improv mode input |
| **VST/SoundFont host** | Timbre rendering |
| **Cloud storage** | Backup, team sharing |

---

## 13. Quality Assurance: Evaluation Dimensions

The evaluator computes scores across six dimensions (v2.0 adds Perception). Genre Skills declare weight adjustments.

### 13.1 Structure
Section contrast, climax position, density curve fit, repetition balance, loopability.

### 13.2 Melody
Range fit, motif memorability, singability, phrase closure, contour variety.

### 13.3 Harmony
Chord function fit (genre-aware), tension resolution, complexity match, cadence strength. **Tonal system aware** (v2.0): blues `consonance_ratio` includes ♭3 as expected; drone is exempt from "low pitch class variety".

### 13.4 Arrangement (when arranging)
Instrument role clarity, frequency conflict risk, original preservation, transformation strength.

### 13.5 Acoustics
BPM accuracy, beat stability, LUFS target, spectral balance, onset density.

### 13.6 Perception (NEW v2.0)
Reference distance (positive anchor proximity, negative anchor distance), psychological alignment (predicted arousal/valence vs intent), surprise index (within target band).

Each dimension carries numerical targets and tolerance bands. Threshold violations are flagged by the Adversarial Critic.

---

## 14. Roadmap (Revised in v2.0)

### Phase 0 (complete) — Environment, MVP skeleton

### Phase 1 (complete) — Parameter-driven symbolic composition
8-file spec, 6-phase protocol (documented), Composer / Harmony / Rhythm / Orchestrator subagents, music21-based analysis, baseline evaluator.

### Phase 1.5 (NEW v2.0) — Multi-Genre Foundation (6–10 weeks)
- **PR-1**: Genre Skill template standardization + 6 Tier-1 Skills
- **PR-2**: Tonal System abstraction (replaces flat `key`)
- **PR-5**: Subagent Protocol standardization (`agents/_protocol.md`)
- **PR-6**: Six-Phase Protocol enforcement in code

### Phase 2 (revised) — Perception + Sound Design (5–7 weeks)
- **PR-3**: Sound Design Layer MVP (Layer 3.5)
- **PR-4**: Reference-Driven Evaluation (Layer 4 perception)

### Phase 3 (revised) — Arrangement + Loop/Vocal (3–4 weeks)
- **PR-7**: Loop-First Generator + modular arrangement
- **PR-8**: Vocal Track support
- Arrangement Engine (reharmonization, regrooving, reorchestration)

### Phase 4 — Advanced Features (1–2 months)
Sketch-to-Spec dialog enhancement, Markov / constraint solver / AI-bridge generators, live coding integration (Strudel / Sonic Pi), evolutionary multi-candidate generation.

### Phase 5 — Production Integration (2–3 months)
DAW connection (Reaper), AI music model bridge (Stable Audio), live improv mode, user style learning.

### Phase 6 — Reflection & Learning (continuous)
Layer 7 reflection in production, per-user style profiles, community reference library standard.

---

## 15. Quickstart

### 15.1 Setup

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
```

### 15.2 First piece — natural language

```bash
yao conduct "a calm piano piece in D minor for studying, 90 seconds"
```

The Conductor parses the description, picks an ensemble template, walks the 6 phases, and iterates until quality thresholds pass.

### 15.3 First piece — Claude Code interactive

```bash
$ claude
> /sketch
> "Late-night lo-fi for studying. Mellow, looping, around 2 minutes"
# (dialog narrows the spec; Producer + Sound Designer are activated)
> /compose late-night-study
> /critique late-night-study
> /tweak late-night-study --section drop --less "busy"
```

### 15.4 Arrange an existing piece

```bash
cp my_song.mid specs/projects/my-song-arrangement/source.mid
> /arrange my-song-arrangement
```

---

## 16. File Formats and Interoperability

| Use | Format | Reason |
|---|---|---|
| Symbolic music | MIDI (.mid), MusicXML (.xml) | Industry standard, all DAW support |
| Score | LilyPond (.ly), PDF | High-quality auto-rendered notation |
| Specs | YAML | Human-readable, git-friendly |
| IR | JSON | Programmatic, schema-validated |
| Provenance | JSON | Graph structure |
| Audio | WAV (production), FLAC/MP3 (distribution) | Standard support |
| Live coding | Strudel pattern strings | Browser-instant playback |

Custom formats are minimized. New formats are introduced only when no standard format suffices.

---

## 17. Ethics and Licensing

### 17.1 Training data and references
The reference library contains **only rights-cleared works**. Each entry's license status is recorded in `references/catalog.yaml`. Unverified files cannot be added.

### 17.2 Artist imitation
Specifying a particular living artist's name is not recommended. Use abstract feature descriptions instead:

> ✗ "in the style of [Artist Name]"
> ✓ "wide open string voicings, ascending motifs, major-minor ambivalence, contemplative tempo"

### 17.3 Output rights
Music generated by YaO belongs to the user. If reference influence is unusually high, a warning is issued.

### 17.4 Transparency
Each generated piece's `provenance.json` records that it was generated with YaO, plus the list of aesthetic anchors consulted.

---

## 18. Relationship to CLAUDE.md

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this document) | Humans + Claude Code | Full design, philosophy, architecture |
| `CLAUDE.md` | Claude Code | Operational rules, prohibitions, pointers |
| `README.md` | Humans | Quickstart, minimal usage |
| `.claude/guides/*.md` | Developers + Claude Code | Specific topical guides (architecture, coding, music engineering, testing, workflow) |
| `docs/design/*.md` | Humans + Claude Code | Architecture decision records |

**Conflict resolution order**: CLAUDE.md > PROJECT.md > guides > other docs.

---

## 19. Future Architectural Extensions

Not yet implemented; planned for evaluation.

### 19.1 Project Runtime Layer
Stateful sessions with generation cache, feedback queue, and undo/redo.

### 19.2 Abstract Agent Protocol
Decouple subagent definitions from Claude Code. A Python protocol (`AgentRole`, `AgentContext`, `AgentOutput`) lets Claude Code be one adapter among potentially many.

### 19.3 Immediate Feedback Path
Sub-second preview from spec change to audio — required for true tweaking UX.

### 19.4 Spec Composability
`specs/fragments/` for reusable progressions / grooves / timbres. `extends:` and `overrides:` keywords for spec composition.

### 19.5 Continuous Conductor Mode (`yao conduct-interactive`)
TUI for live BPM, dynamics, section navigation. Each tweak triggers section-level partial regeneration.

---

## 20. Glossary

**Conductor** — The human, project owner, final arbiter.
**Orchestra** — Collective term for active subagents.
**Score** — YAML specs in `specs/`.
**Score IR** — Internal representation of the Score for code consumption.
**Trajectory** — Time-axis curves (tension, density, valence, predictability, …).
**Aesthetic Reference Library** — Anchor pieces in `references/`.
**Perception Substitute Layer** — Layer 4. Compensates for "the LLM cannot hear".
**Provenance** — Append-only log of every generation decision.
**Adversarial Critic** — Critique-only subagent.
**Negative Space** — Silence and absence, designed deliberately.
**Style Vector** — Multi-dimensional feature representation of a genre or style.
**Iteration** — Versioned generation result (`v001`, `v002`, …).
**Music Lint** — Theory and constraint violation detection.
**Sketch-to-Spec** — Dialog flow from natural language to YAML.
**Tonal System** (v2.0) — The harmonic framework (tonal, modal, pentatonic, blues, microtonal, atonal, drone, raga, maqam, custom).
**Sound Design** (v2.0) — First-class concept of timbre, synthesis, and effect chains.
**Ensemble Template** (v2.0) — Genre-specific configuration of which subagents are active.
**Idiomaticity** (v2.0) — Whether a passage is *playable* / *natural* on its instrument, beyond mere range.
**Singability** (v2.0) — Whether a vocal line can be sung without strain.
**Seamlessness** (v2.0) — Whether a loop can repeat without audible discontinuity.

---

## 21. Closing: The World YaO Aims For

YaO is not a project to "have AI make music". It is infrastructure for **humans and AI to co-create music**, each contributing what they do best.

- Humans bring **intent, taste, and judgment**.
- AI brings **theoretical breadth, iteration speed, and exhaustive recordkeeping**.
- YaO is **the structured environment in which these collaborate**.

Great music remains, in the end, an expression of the human spirit. YaO seeks to make that expression **faster, deeper, more reproducible** — and, in v2.0, **across a broader range of musical traditions** than any single human can master alone.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve, in any genre.*

---

**Project: You and Orchestra (YaO)**
*PROJECT.md version: 2.0*
*Incorporates IMPROVEMENT.md findings C1–C6, Q1–Q5, A1–A3*
*Last updated: 2026-05-05*
