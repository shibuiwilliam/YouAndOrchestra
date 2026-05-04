# You and Orchestra (YaO) — PROJECT.md v2.0

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## Document Status

This is **PROJECT.md v2.0**, a comprehensive evolution of the original design document. It preserves the v1.0 philosophical foundation while incorporating eight structural improvements identified through analysis of the v1.0 implementation. Sections marked with **[NEW]** or **[REVISED]** indicate departures from v1.0.

| Document | Purpose | Audience |
|---|---|---|
| **PROJECT.md** (this file) | Full design and target architecture | Humans + Claude Code |
| **CLAUDE.md** | Development rules and operational contract | Claude Code primary |
| **README.md** | Quickstart and user-facing usage | Humans primary |
| **FEATURE_STATUS.md** | Single source of truth for what works today | Humans + Claude Code |
| **VISION.md** | Forward-looking architecture sketches | Humans + Claude Code |

In case of conflict: **CLAUDE.md > PROJECT.md > VISION.md > other docs**.

---

## 0. The Essence of the Project

**You and Orchestra (YaO)** is an **agentic music production environment** running on Claude Code. Unlike conventional "AI composition tools" that emit music from a single black box, YaO is structured around the principle that **a human (You = Conductor) directs multiple specialized AI agents (Orchestra Members) with clearly divided responsibilities**.

Every design decision in YaO is subordinate to a single proposition:

> **Music production is not a one-shot, intuition-bound act, but a reproducible, improvable engineering process.**

For this reason, YaO treats music first as **code, specifications, tests, diffs, and provenance**, before treating it as audio files. We call this the **Music-as-Code** philosophy.

### What v2.0 adds to this essence

The v1.0 essence remains intact. v2.0 sharpens four points that were under-specified in v1.0:

1. **Surprise as a first-class quantity.** Reproducible engineering is necessary but not sufficient for *interesting* music. v2.0 makes "controlled unpredictability" an explicit, measurable design dimension.
2. **Acoustic truth alongside symbolic truth.** v1.0 evaluated music symbolically. v2.0 mandates parallel acoustic evaluation through the Perception Substitute Layer — without it, the system optimizes toward symbolic metrics that diverge from listening experience.
3. **Groove as ensemble-wide structure.** v1.0 treated rhythm per-instrument. v2.0 elevates groove to a cross-instrument layer that propagates through every part.
4. **Conversation as ensemble logic.** v1.0 generated parts in series. v2.0 introduces the Conversation Plan — a model of how instruments listen and respond to one another.

---

## 1. The Metaphor: You and Orchestra

YaO's concepts map onto an orchestra. Internalizing this mapping is the shortest path to using YaO well.

| YaO Component | Orchestra Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human project owner |
| **Score** | The score | YAML specifications under `specs/` |
| **Orchestra Members** | Players | Specialized Subagents (Composer, Critic, Theorist, etc.) |
| **Concertmaster** | Concertmaster | Producer Subagent (overall coordinator) |
| **Rehearsal** | Rehearsal | Generate–evaluate–adapt iteration loop |
| **Library** | Score library | Reference catalog under `references/` |
| **Performance** | Live performance | Final rendered audio |
| **Recording** | Recording | Versioned outputs under `outputs/` |
| **Critic / Reviewer** | Music critic | Adversarial Critic Subagent |
| **Listening Hall** **[NEW]** | Concert hall | Perception Substitute Layer (acoustic evaluation) |
| **Ensemble Conversation** **[NEW]** | Inter-section dialogue | Conversation Plan |

The Conductor (You) does not write every note. The Conductor's job is to **clarify intent, indicate direction to the players, make judgment calls during rehearsal, and guarantee the quality of the performance**. YaO brings this division of labor into AI.

---

## 2. Invariant Design Principles **[REVISED]**

Every implementation decision in YaO is checked against these invariant principles. They are reproduced in CLAUDE.md and serve as the fundamental criteria for agent judgment.

### Principle 1: The agent is an environment, not a composer
YaO is not "an AI that writes songs"; it is "an environment that makes human composition 10× faster". The goal is to accelerate and extend human creative judgment, never to replace it.

### Principle 2: Every decision must be explainable
Every generated note, chord, and arrangement decision carries a recorded reason. These are persisted as the Provenance Graph, which is traceable, reviewable, and modifiable.

### Principle 3: Constraints liberate, not cage
Explicit specifications (YAML), reference libraries, and negative-space designs are scaffolding for creativity, not restrictions. Unbounded freedom produces paralysis.

### Principle 4: Design the time axis before the notes
A composition is first designed as a set of trajectories on the time axis (tension, density, valence, predictability), and notes are filled in afterward. This produces structurally meaningful music.

### Principle 5: The human ear is the final truth
However refined automated evaluation becomes, the human listening experience is the final judge. Agents **support**, not **replace**, human judgment.

### Principle 6: Vertical alignment **[NEW]**
The expressiveness of the input, the depth of the processing, and the resolution of the evaluation must advance together. Deepening one alone is wasted. Every release advances all three layers in lockstep.

### Principle 7: Acoustic truth complements symbolic truth **[NEW]**
Symbolic metrics (stepwise motion ratio, voice-leading correctness, etc.) are necessary but never sufficient. For every symbolic evaluation, an acoustic evaluation must run in parallel, and divergence between the two is a critical signal.

---

## 3. Architecture: The 8-Layer Model **[REVISED]**

YaO v1.0 had a 7-layer architecture. v2.0 inserts an additional layer (Layer 3.5: Plan IR) and revises responsibilities. Each layer has independent input/output contracts and can be replaced or tested in isolation.

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                              │
│   User style profiles, history mining, cross-project        │
│   pattern detection                                          │
├─────────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                            │
│   Symbolic evaluation, acoustic evaluation, adversarial     │
│   critique, constraint checking, music linting, diffing     │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                          │
│   MIDI writing, stem export, audio rendering, MusicXML,     │
│   LilyPond, Strudel emission, iteration management          │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute  [NEWLY POPULATED]           │
│   Audio feature extraction, use-case targeting, abstract    │
│   reference matching, listening simulation                  │
├─────────────────────────────────────────────────────────────┤
│ Layer 3.5: Musical Plan IR (MPIR)  [NEW]                    │
│   SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan,         │
│   DrumPattern, ArrangementPlan, ConversationPlan,           │
│   TensionArc, HookPlan                                      │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Score Intermediate Representation (ScoreIR)        │
│   Note, Part, Section, Voicing, Motif, Timing, Notation     │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                                │
│   Plan generators, Note Realizers (rule-based, stochastic,  │
│   markov, constraint-solver), groove applicator             │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                      │
│   YAML specs (v1, v2), intent.md, trajectory.yaml,          │
│   constraints, references, negative-space, production       │
├─────────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                          │
│   38+ instruments, 20+ scales, 14 chord types, MIDI maps,   │
│   GM drum maps, dynamics tables, form library              │
└─────────────────────────────────────────────────────────────┘
```

Dependencies flow strictly upward: lower layers do not know about upper layers. Adding MPIR (Layer 3.5) between Generation and Score IR resolves the v1.0 ambiguity where generators directly produced notes from specs without an explicit plan-level rationale.

### Why Layer 3.5 (MPIR) was added

A musical plan answers questions that pure notes cannot:

- **Why** does this section exist? (form intent)
- **Why** does this chord follow that one? (functional role)
- **Why** does this phrase echo the earlier one? (motif lineage)
- **Why** does this drum pattern fit the arrangement? (groove role)

Notes are *what*. Plans are *why*. **Critique without plans is shallow; critique with plans is precise**. MPIR is what enables the Adversarial Critic, the Arrangement Engine, and the Section-Level Surgery features to work meaningfully.

---

## 4. Directory Structure **[REVISED]**

```
yao/
├── CLAUDE.md                       # Development rules for Claude Code
├── PROJECT.md                      # This document
├── VISION.md                       # Forward-looking design sketches
├── FEATURE_STATUS.md               # What works today (auto-verified)
├── README.md                       # User quickstart
├── pyproject.toml
├── Makefile
├── .pre-commit-config.yaml
├── .github/workflows/
│   ├── ci.yml
│   ├── audio-regression.yml        # [NEW] weekly acoustic regression
│   └── showcase.yml                # [NEW] weekly auto-generated gallery
│
├── .claude/
│   ├── commands/                   # Slash commands
│   │   ├── compose.md
│   │   ├── arrange.md
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md
│   │   ├── explain.md
│   │   ├── regenerate-section.md
│   │   ├── pin.md                  # [NEW] localized feedback
│   │   └── feedback.md             # [NEW] natural-language feedback
│   ├── agents/                     # Subagent definitions
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── conversation-director.md  # [NEW] ensemble dialogue
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   └── producer.md
│   ├── skills/
│   │   ├── genres/                 # 12+ genres, paired .md + .yaml
│   │   ├── theory/                 # Music theory knowledge
│   │   ├── instruments/            # Per-instrument idioms
│   │   ├── psychology/             # Empirical perception mappings
│   │   ├── grooves/                # [NEW] Genre-specific groove profiles
│   │   ├── forms/                  # [NEW] Song form library
│   │   └── cultures/               # [NEW] Non-Western music traditions
│   ├── guides/                     # Developer guides for Claude Code
│   └── hooks/                      # Auto-execution hooks
│
├── specs/
│   ├── projects/                   # User compositions
│   │   └── <project-name>/
│   │       ├── intent.md
│   │       ├── composition.yaml
│   │       ├── trajectory.yaml
│   │       ├── tension_arcs.yaml   # [NEW] short-range tension structures
│   │       ├── hooks.yaml          # [NEW] hook deployment plan
│   │       ├── conversation.yaml   # [NEW] ensemble dialogue plan
│   │       ├── groove.yaml         # [NEW] groove profile selection
│   │       ├── references.yaml
│   │       ├── negative-space.yaml
│   │       ├── arrangement.yaml    # for arrangement mode
│   │       ├── pins.yaml           # [NEW] user-attached localized feedback
│   │       └── production.yaml
│   ├── templates/                  # v1 + v2 ready-to-use templates
│   │   ├── v1/
│   │   └── v2/
│   └── fragments/                  # [NEW] reusable spec fragments
│
├── src/
│   ├── yao/
│   │   ├── conductor/              # Generate-evaluate-adapt orchestration
│   │   ├── constants/              # Instruments, scales, chords, forms
│   │   ├── schema/                 # Pydantic models
│   │   ├── ir/
│   │   │   ├── score/              # ScoreIR, Note, Voicing, Motif
│   │   │   ├── plan/               # MPIR: SongFormPlan, HarmonyPlan, etc.
│   │   │   ├── tension_arc.py      # [NEW]
│   │   │   ├── hook.py             # [NEW]
│   │   │   ├── conversation.py     # [NEW]
│   │   │   └── groove.py           # [NEW]
│   │   ├── generators/
│   │   │   ├── plan/               # Plan-level generators
│   │   │   ├── note/               # Note Realizers
│   │   │   ├── groove_applicator.py  # [NEW]
│   │   │   ├── reactive_fills.py     # [NEW]
│   │   │   └── frequency_clearance.py # [NEW]
│   │   ├── perception/             # [NEWLY POPULATED] Layer 4
│   │   │   ├── audio_features.py
│   │   │   ├── use_case_targets.py
│   │   │   ├── reference_matcher.py
│   │   │   ├── listening_simulator.py
│   │   │   └── surprise.py
│   │   ├── arrange/                # [NEWLY POPULATED]
│   │   │   ├── extractor.py
│   │   │   ├── operations.py
│   │   │   ├── preservation.py
│   │   │   ├── style_vector.py
│   │   │   └── diff_report.py
│   │   ├── render/
│   │   ├── verify/
│   │   │   ├── critique/           # 30+ rules across 7 roles
│   │   │   ├── evaluator/          # MetricGoal-based
│   │   │   └── acoustic/           # [NEW] acoustic-side verification
│   │   ├── reflect/                # Provenance, RecoverableDecision
│   │   ├── sketch/                 # NL → spec compiler (multilingual)
│   │   ├── feedback/               # [NEW] Pin processing, NL feedback
│   │   ├── runtime/                # [NEW] ProjectRuntime (stateful sessions)
│   │   ├── errors.py
│   │   └── types.py
│   └── cli/
│
├── references/
│   ├── catalog.yaml                # rights status mandatory
│   ├── style_vectors/              # [NEW] precomputed abstract feature vectors
│   └── musicxml/
│
├── grooves/                        # [NEW] Genre-specific groove YAMLs
├── drum_patterns/                  # 12+ genre patterns
├── forms/                          # [NEW] Song form definitions
│
├── outputs/
│   └── projects/<name>/iterations/v<NNN>/
│       ├── full.mid
│       ├── stems/
│       ├── audio.wav
│       ├── score.musicxml
│       ├── score.pdf
│       ├── analysis.json           # symbolic features
│       ├── perceptual.json         # [NEW] acoustic features
│       ├── evaluation.json
│       ├── critique.json
│       ├── plan.json               # [NEW] MPIR snapshot
│       └── provenance.json
│
├── soundfonts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── scenarios/
│   ├── music_constraints/
│   ├── golden/                     # bit-exact MIDI regression
│   ├── audio_regression/           # [NEW] acoustic feature regression
│   └── subagents/                  # [NEW] subagent behavioral tests
│
├── tools/
│   ├── architecture_lint.py
│   ├── feature_status_check.py
│   ├── skill_quality_check.py      # [NEW]
│   ├── check_silent_fallback.py
│   └── regenerate_goldens.py
│
├── gallery/                        # weekly auto-updated showcase
└── docs/
```

---

## 5. The Orchestra: Subagent Design **[REVISED]**

YaO's players have clearly defined roles, inputs, outputs, and prohibitions. Each Subagent has its own context, permitted tools, and evaluation criteria. They operate independently and are integrated by the Producer Subagent.

### 5.1 Composer
**Owns:** Motifs, themes, melodic phrases, structural skeletons
**Inputs:** intent.md, composition.yaml, trajectory.yaml, hooks.yaml, references.yaml
**Outputs:** MotifPlan, PhrasePlan, HookPlan
**Forbidden:** Instrument selection, final voicing, drum patterns
**Evaluation:** Motif memorability, repetition–variation balance, trajectory adherence, hook strength

### 5.2 Harmony Theorist
**Owns:** Chord progressions, modulations, substitutions, cadences, tension arcs
**Inputs:** Composer's melodic skeleton, harmony parameters, tension_arcs.yaml
**Outputs:** HarmonyPlan with TensionArc annotations
**Evaluation:** Functional integrity, tension–resolution dynamics, genre compliance

### 5.3 Rhythm Architect
**Owns:** Drum patterns, grooves, syncopation, fills
**Inputs:** rhythm parameters, genre, GrooveProfile
**Outputs:** DrumPattern + GrooveProfile (the latter applied across the ensemble)
**Evaluation:** Groove feel, humanization quality, inter-section contrast

### 5.4 Orchestrator
**Owns:** Instrument assignment, voicing, register, counter-melody, frequency clearance
**Inputs:** All upstream plans
**Outputs:** Complete ArrangementPlan (per-instrument parts)
**Evaluation:** Frequency-space collision avoidance, idiomatic instrument use, texture density

### 5.5 Conversation Director **[NEW]**
**Owns:** Inter-instrument dialogue, voice focus shifts, reactive fills, call-and-response
**Inputs:** ArrangementPlan + ScoreIR draft
**Outputs:** ConversationPlan
**Evaluation:** Dialogue coherence, primary-voice clarity, fill responsiveness

This Subagent is new in v2.0 and addresses the v1.0 weakness where instruments were generated independently with no inter-listening.

### 5.6 Adversarial Critic
**Owns:** Discovery and articulation of weaknesses
**Inputs:** Any artifact at any stage (MPIR or ScoreIR)
**Outputs:** Structured `Finding` objects with severity, evidence, location, recommendations
**Special trait:** **Never praises**. Detects clichés, structural monotony, emotional incongruity, surprise deficit, hook deficiency, ensemble silence
**Evaluation:** Comprehensiveness and specificity of weakness identification

### 5.7 Mix Engineer
**Owns:** Stereo placement, dynamics processing, frequency masking resolution, loudness management
**Inputs:** Orchestrator's output + production.yaml
**Outputs:** Mix specification (per-track EQ/comp/reverb/pan)
**Evaluation:** LUFS target adherence, frequency balance, stereo width

### 5.8 Producer
**Owns:** Overall integration, prioritization, dialogue with the Conductor (human), final judgment
**Inputs:** All Subagent outputs + human feedback (including pins)
**Outputs:** Final production decisions, instructions for the next iteration
**Special privilege:** Only Producer can override another Subagent's output
**Evaluation:** Fidelity to intent.md

---

## 6. Cognitive Protocol: 6 Phases × 7 Steps **[REVISED]**

The v1.0 6-phase cognitive protocol (Intent → Architectural Sketch → Skeletal → Critic Dialogue → Filling → Listening) is preserved. v2.0 maps it onto a concrete **7-step generation pipeline**, resolving v1.0's ambiguity where Phase 4 ("dialogue") had no concrete pipeline mechanism.

### Pipeline

```
[Step 1: Form Planner]      Spec + Trajectory  →  SongFormPlan + TensionArcs
      ↓
[Step 2: Harmony Planner]                       →  HarmonyPlan
      ↓
[Step 3: Motif Developer]                       →  MotifPlan + PhrasePlan + HookPlan
      ↓
[Step 4: Drum Patterner]                        →  DrumPattern + GrooveProfile
      ↓
[Step 5: Arranger]                              →  ArrangementPlan
      ↓
[Step 5.5: Conversation Director]  [NEW]        →  ConversationPlan
      ↓
═══ MUSICAL PLAN COMPLETE — Critic Gate ═══
      ↓
[Step 6: Note Realizer]     MPIR  →  ScoreIR (with groove applied)
      ↓
[Step 7: Renderer]          ScoreIR  →  MIDI / Audio / Score
      ↓
[Step 7.5: Listening Simulation]  [NEW]    Acoustic features → Perception report
      ↓
[Optional Loopback]   Divergence triggers replanning of offending sections
```

### Cognitive ↔ Pipeline mapping

| Cognitive Phase | Pipeline Step(s) |
|---|---|
| 1. Intent Crystallization | (pre-pipeline) → finalize `intent.md` |
| 2. Architectural Sketch | Step 1 (Form + TensionArc) + trajectory.yaml |
| 3. Skeletal Generation | Steps 2–5 produce 5 candidate plans |
| 4. Critic-Composer Dialogue | Critic Gate ranks/integrates winning plan |
| 5. Detailed Filling | Step 5.5 + Step 6 + Step 7 |
| 6. Listening Simulation | Step 7.5 + optional loopback |

### Multi-Candidate Generation **[NEW]**

The "5 candidates" in Phase 3 is a real implementation. The Conductor instantiates 5 parallel pipelines through Steps 2–5 with different seeds. The Critic ranks all five plans; the Producer picks a winner or instructs the Composer to merge strengths from multiple candidates.

### Critic Gate

Between Step 5.5 and Step 6, the Adversarial Critic operates on the complete MPIR. Findings can:

- Propose plan-level edits (loop back to Steps 1–5)
- Reject the entire plan and request a different candidate
- Approve and pass to realization

This is where YaO's quality leap happens. **Critique at the plan level prevents the system from carefully realizing a fundamentally weak plan.**

---

## 7. Specification Files **[REVISED]**

YaO describes a piece through **12 YAML files** (up from 8 in v1.0). All are version-controlled and git-diffable. New additions are marked **[NEW]**.

### 7.1 `intent.md` (natural language intent)
The essence of the piece in 1–3 sentences. The ultimate ground for every decision.

### 7.2 `composition.yaml` (composition parameters)
Key, tempo, time signature, form, genre, instrumentation, section structure. v2 schema available with 11 dedicated sections (emotion, melody, harmony, rhythm, drums, arrangement, production, etc.).

### 7.3 `trajectory.yaml` (time-axis trajectories)
Tension, density, valence, predictability, brightness, register-height curves. Bezier, stepped, or linear.

### 7.4 `tension_arcs.yaml` **[NEW]**
Short-range (2–8 bar) tension–resolution structures. Decouples local drama from macro trajectories.

```yaml
tension_arcs:
  - id: "approach_chorus"
    location: { section: verse, bars: [5, 8] }
    pattern: linear_rise
    target_release: { section: chorus, bar: 1 }
    intensity: 0.8
    mechanism: secondary_dominant_chain
  - id: "false_resolution"
    location: { section: bridge, bars: [3, 4] }
    pattern: deceptive_cadence
    intended_chord: I
    actual_chord: vi
    intensity: 0.6
```

### 7.5 `hooks.yaml` **[NEW]**
Identifies hooks (memorable 2–4 bar fragments) and prescribes their deployment strategy.

```yaml
hooks:
  - id: "main_hook"
    motif_ref: "M_chorus_main"
    deployment: withhold_then_release
    appearances: ["chorus_1:bar_1", "chorus_2:bar_1", "outro:bar_2"]
    variations_allowed: true
    maximum_uses: 4
    distinctive_strength: 0.9
```

### 7.6 `conversation.yaml` **[NEW]**
The ensemble dialogue plan. Specifies primary voices, accompaniment roles, and inter-instrument response patterns.

```yaml
voice_focus:
  intro:    { primary: piano, accompaniment: [bass] }
  verse:    { primary: vocal_lead, accompaniment: [piano, bass, drums] }
  chorus:   { primary: vocal_lead, doubled_by: [strings], accompaniment: [piano, bass, drums] }
  bridge:   { primary: piano_solo, accompaniment: [strings_pad, bass] }

conversation_events:
  - type: call_response
    initiator: piano
    responder: strings
    location: { section: bridge, bars: [1, 4] }
  - type: fill_in_response
    fill_capable: [drums, percussion]
    trigger: melodic_phrase_end
    minimum_silence_beats: 1.0
```

### 7.7 `groove.yaml` **[NEW]**
Selects or customizes a GrooveProfile for the entire ensemble.

```yaml
groove:
  base: lofi_hiphop      # reference to grooves/lofi_hiphop.yaml
  overrides:
    swing_ratio: 0.58
    timing_jitter_sigma: 6.0
  apply_to_all_instruments: true
```

### 7.8 `references.yaml` (aesthetic reference library)
Positive references (emulate) and negative references (avoid). Each reference declares which abstract features to compare. **Hard-blocked from comparing melody, hook rhythm, or chord progression directly.**

### 7.9 `negative-space.yaml` (negative space)
Designed silence, frequency gaps, textural subtractions.

### 7.10 `arrangement.yaml` (arrangement mode only)
Source input, preservation contract, transformation contract, avoidance list.

### 7.11 `production.yaml` (mix and mastering)
LUFS target, stereo width, reverb amount, dynamic-range target.

### 7.12 `pins.yaml` **[NEW]** (auto-generated from user feedback, not hand-written)
Localized user feedback attached to specific positions in a generated piece.

### 7.13 `provenance.json` (auto-generated, not hand-written)
The complete decision log. Every note, chord, and instrument choice carries its rationale.

---

## 8. Custom Commands **[REVISED]**

| Command | Purpose | Primary Subagent |
|---|---|---|
| `/sketch` | Sketch → spec dialogue (multilingual) | Producer |
| `/compose <project>` | Generate from spec | Composer → all |
| `/arrange <project>` | Arrange existing piece | Orchestrator + Critic |
| `/critique <iteration>` | Adversarial critique | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate between two styles | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment (live mode) | Composer + Rhythm |
| `/explain <element>` | Trace a generation decision | Producer (via Provenance) |
| `/diff <iter_a> <iter_b>` | Music diff between iterations | Verifier |
| `/render <iteration>` | MIDI → audio/score | Mix Engineer |
| `/pin <location> <note>` **[NEW]** | Attach localized feedback | Producer |
| `/feedback "<text>"` **[NEW]** | Natural-language feedback → structured | Producer |
| `/preview <spec>` **[NEW]** | In-memory generate + play | (CLI direct) |
| `/watch <spec>` **[NEW]** | File-watch + auto-regenerate | (CLI direct) |
| `/showcase` **[NEW]** | Generate the weekly canonical set | Conductor |

---

## 9. Skills (the players' background) **[REVISED]**

`.claude/skills/` contains structured domain knowledge that Subagents reference.

### 9.1 Genre Skills (target: 12+)
Each genre is one Skill. Contains typical chord progressions, rhythm patterns, instrumentation, representative reference pieces, clichés to avoid. Each Skill has both a Markdown form (for Subagent prompts) and a YAML form (for programmatic Generator use), generated from a single source via `make sync-skills`.

Current target genres: cinematic, lofi_hiphop, j_pop, neoclassical, ambient, jazz_ballad, game_8bit_chiptune, acoustic_folk, edm, rock, orchestral, anime_bgm.

### 9.2 Theory Skills
Voice leading, reharmonization, counterpoint, modal interchange, secondary dominants, chromaticism. Each entry includes examples and counter-examples; rules are tagged with genre dependencies.

### 9.3 Instrument Skills
Range, idiomatic patterns, articulation, frequency profile, characteristic phrases for each of the 38+ supported instruments.

### 9.4 Psychology Skills
Empirical mappings from music psychology (Krumhansl, Huron, Juslin & Sloboda, Meyer) — tempo and arousal, mode and valence, spectral centroid and brightness perception, expectation and surprise.

### 9.5 Groove Skills **[NEW]**
Genre-specific GrooveProfiles. Each defines microtiming offsets per 16th-note position, velocity patterns, ghost-note probabilities, swing ratios, and humanization parameters.

### 9.6 Form Skills **[NEW]**
The song-form library: AABA, verse-chorus-bridge, rondo, through-composed, intro-loop-outro (game BGM), arch form, minimalist phasing, ternary, binary, fugue, theme-and-variations.

### 9.7 Culture Skills **[NEW]**
Non-Western music traditions: Japanese (in/yo/ritsu/min'yō scales, gagaku idioms), Middle Eastern (maqam systems), Indian (rāga basics), Indonesian (gamelan tuning approximations).

---

## 10. Hooks (automated guarantees)

Hooks are not instructions to Claude Code; they are **scripts whose execution is guaranteed**. The following are mandatory:

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | git commit | Music21 theory lint, YAML schema validation, ruff, mypy |
| `pre-commit-arch` | git commit | Layer boundary check |
| `post-generate-render` | After generate | Auto-render audio + score |
| `post-generate-critique` | After generate | Run rule-based critique, persist `critique.json` |
| `post-generate-perceptual` **[NEW]** | After audio render | Extract acoustic features, persist `perceptual.json` |
| `update-provenance` | Any plan/score change | Append to provenance log |
| `spec-changed-show-diff` | Edit spec | Show what changed musically (MPIR-level) |
| `pin-changed-mark-stale` **[NEW]** | New pin added | Mark current iteration as needing regeneration |

---

## 11. The Eight Structural Improvements **[NEW SECTION]**

This section explicitly describes the eight structural improvements over v1.0 that drive v2.0's design. These are not separate features but cross-cutting concerns realized through the architectural changes above.

### 11.1 Surprise Score and Tension Arcs

The Prosaic Output Problem — "spec-correct but boring" — is addressed through:

- **Surprise Score** (Layer 4): every note is annotated with a predicted-vs-actual divergence, computed via n-gram + Krumhansl tonal hierarchy
- **Tension Arc Primitives** (Layer 3.5): short-range tension-resolution structures as first-class plan objects
- **Hook IR** (Layer 3.5): hooks as Motif specializations with deployment strategies (rare/frequent/withhold-then-release)
- **Phrase-Level Dynamics** (Layer 1): dynamics shapes within sections (crescendo, hairpin, peak position) instead of flat per-section velocity

The Adversarial Critic gains new rules: `surprise_deficit`, `surprise_overload`, `tension_arc_unresolved`, `hook_overuse`, `hook_underuse`.

### 11.2 Acoustic Truth (Perception Layer)

Layer 4 was empty in v1.0. v2.0 populates it with three stages:

**Stage 1 — Audio features.** After audio rendering, extract LUFS, spectral centroid/rolloff/flatness, onset density per section, tempo stability, frequency band ratios. These produce a `PerceptualReport` parallel to the symbolic `EvaluationReport`.

**Stage 2 — Use-case targeting.** Different use cases activate different evaluation axes:

```python
USE_CASE_EVALUATORS = {
    "youtube_bgm":   ["vocal_space_score", "loopability", "fatigue_risk", "lufs_target_match"],
    "game_bgm":      ["loop_seam_smoothness", "tension_curve_match", "repetition_tolerance"],
    "advertisement": ["hook_entry_time_lt_7s", "energy_peak_position", "short_form_memorability"],
    "study_focus":   ["low_distraction_score", "dynamic_stability", "predictability"],
    "cinematic":     ["dynamic_range", "thematic_clarity", "emotional_arc_fit"],
}
```

**Stage 3 — Reference matching (abstract-only).** References are precomputed StyleVectors over tempo distribution, density curve, spectral balance, groove profile, and section energy — never raw audio similarity, never melody, never chord progression. Schema-enforced allowlist prevents accidental copying.

The Adversarial Critic gains the `symbolic_acoustic_divergence` rule: when symbolic evaluation is high but acoustic is low (or vice versa), this is a critical signal that the symbolic layer has optimized away from the listening experience.

### 11.3 Diversity Sources

The mode-collapse risk (every piece sounding similar) is addressed through:

- **Form Library** (Layer 0): 20+ song forms, selectable by `form: aaba_32bar`
- **Harmonic Vocabulary Profiles** (Skills): each genre declares its allowed harmonic palette with weights
- **Melodic Generation Strategies** (Layer 2): contour-based, motif-development, linear-voice, arpeggiated, scalar, call-response, pedal-tone, hocketing
- **Texture / Dissonance / Time-feel parameters** (Layer 1): polyphonic vs homophonic, dissonance level, rubato vs strict

### 11.4 Groove as Ensemble Property

GrooveProfile (Layer 3.5) is applied to **all instruments**, not just drums. Each profile defines:

```python
@dataclass(frozen=True)
class GrooveProfile:
    microtiming: dict[int, float]       # 16th position → ms offset
    velocity_pattern: dict[int, float]  # 16th position → velocity multiplier
    ghost_probability: float
    swing_ratio: float
    timing_jitter_sigma: float
    apply_to_all_instruments: bool = True
```

A `GrooveApplicator` post-processes the ScoreIR before MIDI output. Genre-specific groove libraries live in `grooves/`.

### 11.5 Conversation Plan

The Conversation Director Subagent owns:

- **Voice focus** per section (primary, accompaniment, doublers)
- **Conversation events** (call-response, fill-in-response, tutti, solo break, trade)
- **Reactive fills**: drums and other fill-capable instruments respond to long silences after melodic phrase endings
- **Frequency clearance**: a 2D time × frequency occupancy heatmap of the lead voice; accompaniment is moved out of busy regions

This addresses the v1.0 weakness where instruments were generated independently with no inter-listening.

### 11.6 Three-Tier Feedback Granularity

User feedback now has three granularities:

1. **Spec-level** (existing): change YAML, regenerate everything
2. **Section-level** (existing): `regenerate-section <name>`, preserve everything else
3. **Pin-level** **[NEW]**: attach a comment to a specific (section, bar, beat, instrument), trigger localized regeneration with derived constraints

```bash
yao pin my-song v003 \
  --location "section:chorus,bar:6,beat:3,instrument:piano" \
  --note "this dissonance is too harsh"

yao feedback my-song v003 "the chorus feels weak; I want more impact"
# → Claude Code translates to structured suggestions
```

### 11.7 Multilingual and Multicultural Support

- **Multilingual SpecCompiler**: English (existing), Japanese **[NEW]**, with extensibility for additional languages
- **Extended Scales**: Western (14) + Japanese (in, yo, ritsu, min'yō) + Middle Eastern (hijaz, kurd) + Indian (bhairav)
- **Custom Instrument Profiles**: GM is the default, but custom SF2 paths and idiomatic-technique definitions allow non-Western instruments
- **Optional Microtonal Pitch**: the default `Note.pitch` remains an int (12-TET); a separate `MicrotonalNote` with cent-precise pitch enables alternate tunings without breaking the default path

### 11.8 Arrangement Engine

Arrangement is YaO's most differentiated capability. The pipeline:

```
[Input MIDI/MusicXML]
   ↓
[SourcePlan Extractor]   detects sections, melody, harmony, motifs, roles
   ↓
[SourcePlan = MPIR of input]
   ↓
[Preservation + Transformation Contracts]
   ↓
[Style Vector Operations]
   target = source - vec(source_genre) + vec(target_genre) ⊕ preserve
   ↓
[TargetPlan = MPIR of arrangement]
   ↓
[Note Realizer → ScoreIR → MIDI]
   ↓
[Arrangement Diff Markdown report]
```

Operations include Reharmonization, Regrooving, Reorchestration, TempoTransform, Transposition, StyleTransfer. The Arrangement Diff Markdown shows preserved aspects, changed aspects, and risks (with similarity scores).

---

## 12. Quality Assurance: Evaluation Architecture **[REVISED]**

YaO scores generated music across **two parallel families** of metrics: symbolic and acoustic.

### 12.1 Symbolic Evaluation

Inherited from v1.0 with extensions. 13 metrics across 4 dimensions, each with a typed `MetricGoal`.

| Dimension | Metrics |
|---|---|
| **Structure** | Section contrast, bar count accuracy, section count match, rhythm variety, syncopation ratio, **surprise distribution** [NEW] |
| **Melody** | Pitch range utilization, stepwise motion ratio, contour variety, **hook deployment quality** [NEW] |
| **Harmony** | Pitch class variety, consonance ratio, **tension arc resolution** [NEW] |
| **Arrangement** | Instrument balance, texture density, **conversation coherence** [NEW] |

### 12.2 Acoustic Evaluation **[NEW]**

After audio rendering, the Perception Layer computes:

| Dimension | Metrics |
|---|---|
| **Loudness** | Integrated LUFS, short-term LUFS curve, peak dBFS, crest factor, dynamic range |
| **Spectral** | Centroid, rolloff, flatness, band energy ratios |
| **Temporal** | Onset density per section, tempo stability, rhythmic regularity |
| **Perceptual** | Brightness, warmth, busyness, spectral collision risk |

### 12.3 Use-Case Driven Evaluation **[NEW]**

`composition.yaml` may declare `use_case: youtube_bgm` (or `game_bgm`, `advertisement`, `study_focus`, `cinematic`). This activates use-case-specific metrics in addition to the universal ones.

### 12.4 Symbolic-Acoustic Divergence **[NEW]**

When symbolic evaluation is high (e.g., 8.5/10) but acoustic evaluation is low (e.g., 5/10), this is recorded as a **divergence event** and triggers an Adversarial Critic finding. This catches cases where the symbolic optimization has drifted away from the listening experience — a critical health signal for the entire system.

### 12.5 Adversarial Critique Rules **[REVISED]**

The Critique Registry is expanded from 15 to **30+** rules across 7 categories:

| Category | Rules (target count) |
|---|---|
| **Structural** | 5 — climax absence, section monotony, form imbalance, surprise deficit, surprise overload |
| **Melodic** | 5 — cliche motif, contour monotony, phrase closure weakness, hook overuse, hook underuse |
| **Harmonic** | 5 — cliche progression, voice crossing, cadence weakness, tension arc unresolved, secondary dominant absence in genre that demands it |
| **Rhythmic** | 4 — rhythmic monotony, groove inconsistency, ensemble groove conflict, microtiming flatness |
| **Arrangement** | 5 — frequency collision, texture collapse, conversation silence, primary voice ambiguity, fill absence at phrase ends |
| **Emotional** | 3 — intent divergence, trajectory violation, valence-mode conflict |
| **Acoustic** **[NEW]** | 3+ — symbolic-acoustic divergence, LUFS target violation, spectral imbalance |

Each rule emits a `Finding` with severity (critical / major / minor / suggestion), evidence, location, and recommendation — machine-actionable, not free text.

---

## 13. Development Roadmap **[REVISED]**

The roadmap is organized around the **vertical alignment principle** (Principle 6): each phase advances input expressiveness, processing depth, and evaluation resolution **together**.

### Phase α (Days 1–30): Foundation Alignment ✅ Complete

- 7-layer architecture, Pydantic schemas, ScoreIR, rule-based and stochastic generators, MIDI writer, Conductor, CLI, Claude Code commands and Subagents (7 each), 8 genre Skills, 4 domain Skills.

### Phase β (Days 31–75): Plan Maturity and Mechanized Critique ✅ Complete

- MPIR (SongFormPlan, HarmonyPlan), MotifPlan, PhrasePlan, DrumPattern, ArrangementPlan, MetricGoal type system, RecoverableDecision logging, 15 critique rules, multi-candidate Conductor, 643 tests, golden MIDI regression.

### Phase γ (Days 76–120): Differentiation — Quality and Acoustic Truth **[REVISED]**

**Goal:** Address the eight structural gaps. Make the output musically interesting and acoustically verified.

- **Perception Layer Stage 1** (audio features extraction, librosa + pyloudnorm)
- **Perception Layer Stage 2** (use-case targeted evaluation: BGM/Game/Ad/Study/Cinematic)
- **Surprise Score** computation and `surprise_deficit` / `surprise_overload` critique rules
- **Tension Arcs** as first-class plan objects with `tension_arcs.yaml`
- **Hook IR** with deployment strategies and `hooks.yaml`
- **Phrase-Level Dynamics** schema and Note Realizer support
- **GrooveProfile** + 12 genre-specific groove YAMLs + `GrooveApplicator`
- **Conversation Director Subagent** + `ConversationPlan` + `conversation.yaml`
- **Reactive Fills** + Frequency Clearance generators
- **Multilingual SpecCompiler** (Japanese first, then framework for additional languages)
- **Extended Scales** (Japanese, Middle Eastern, Indian) and Form Library (20+ forms)
- **Critique Rules** expanded to 30+

**Milestone:** A `study_focus` BGM and a `cinematic` orchestral piece are both generated and acoustically verified. Symbolic-acoustic divergence detection is demonstrated. The same intent.md generates 5 distinct candidate plans through multi-candidate generation.

### Phase δ (Days 121–180): The Marquee Feature — Arrangement **[REVISED]**

**Goal:** Implement the Arrangement Engine, YaO's signature differentiator.

- **SourcePlan Extractor** (section detection, melody extraction, harmony estimation, motif detection, role classification)
- **Arrangement Operations** (Reharmonization, Regrooving, Reorchestration, TempoTransform, Transposition, StyleTransfer)
- **Preservation Contract** with similarity thresholds and machine-checkable enforcement
- **Style Vector** abstract operations
- **Arrangement Diff** Markdown reporting
- **MusicXML / LilyPond writers**
- **Reference Matcher** Stage 3 (abstract-only)
- **Three-tier feedback** (`pin`, `feedback`)
- **Reaper MCP** (initial integration)
- **Spec composability** (`extends:`, `overrides:`, `fragments/`)

**Milestone:** A piano sketch is arranged into lo-fi hip-hop, into orchestral cinematic, and into bossa nova — each with a structured diff explaining what was preserved and what was changed. Pins enable user-driven local revision.

### Phase ε (Days 181–270): Production-Grade Operations

**Goal:** Real-project-grade output and operational maturity.

- **Production Manifest + Mix Chain** (pedalboard)
- **Sketch-to-Spec dialogue state machine**
- **Strudel emitter** for browser-side instant audition
- **`yao annotate`** browser UI for time-tagged feedback
- **Audio regression tests** in CI
- **Weekly Showcase** auto-generated to GitHub Pages
- **Subagent behavioral tests**
- **Skill quality checker**
- **mkdocs site complete**: `for-musicians/`, `for-developers/`
- **ProjectRuntime** (stateful sessions with cache, undo/redo, feedback queue)

**Milestone:** A commercial BGM creator can use YaO end-to-end, render to audio, and import the result into a DAW for finishing.

### Phase ζ (Continuous): Reflection and Community

- **Reflection Layer (Layer 7)**: user style profiles learned from feedback history
- **Cross-project pattern mining**
- **Community reference library** (shared StyleVector format)
- **Live improvisation mode** (MIDI controller input)
- **AI music model bridges** (Stable Audio, MusicGen) for texture generation under YaO's structural control
- **Backend-agnostic agent protocol** (Claude Code as one adapter)
- **Generic creative-domain framework** (extracting the YaO patterns: intent-as-code, trajectory, plan IR, adversarial critic, provenance)

---

## 14. Strategic Insight: Beyond Music **[NEW SECTION]**

YaO's design pattern is not music-specific. It is a **general framework for structured human–AI creative collaboration**. The mappings:

| YaO Pattern | General Pattern | Other Domains |
|---|---|---|
| Score (YAML spec) | **Intent-as-Code** | UI design specs, narrative structure, game level design |
| Trajectory | **Time-axis quality curves** | Video pacing, presentation arcs, UX journeys |
| Tension Arc | **Local dramatic structure** | Story scenes, ad spots, lecture sections |
| Hook IR | **Memorable centerpiece artifact** | Brand taglines, key visuals, signature moves |
| Plan IR (MPIR) | **Why-layer between intent and artifact** | Architecture decision records for any creative work |
| Adversarial Critic | **Adversarial review** | Code review, design critique, writing feedback |
| Provenance Graph | **Decision genealogy** | All AI-assisted creative work |
| 6-phase cognitive protocol | **Structured creative protocol** | Any domain where "don't dive into implementation" matters |
| Conversation Plan | **Multi-actor coordination model** | Multi-character writing, multi-product brand orchestration |

These abstractions are intentionally factorable. The current scope is music, but the architectural patterns are designed to be liftable. **Phase ζ explicitly considers this lifting as a research direction.**

---

## 15. Performance Expectations **[REVISED]**

| Operation | v1.0 Target | v2.0 Target | Notes |
|---|---|---|---|
| Load YAML spec | <100ms | <100ms | Pydantic validation |
| Generate 8-bar piece | <1s | <1s | Both generators |
| Generate 64-bar piece | <5s | <5s | Stochastic may vary |
| **Generate 5 candidates (multi-candidate)** **[NEW]** | — | <15s | Parallel pipelines |
| Write MIDI file | <200ms | <200ms | pretty_midi |
| **Render audio (90s piece)** **[NEW]** | — | <10s | FluidSynth |
| **Extract acoustic features** **[NEW]** | — | <3s | librosa per piece |
| Run full lint | <500ms | <500ms | All lint rules |
| **Run all tests** | <5s | <30s | ~1500 tests projected |
| Architecture lint | <1s | <1s | AST parsing |
| **Audio regression test (10 pieces)** **[NEW]** | — | <5min | Acceptable in CI |

Performance budgets are not soft suggestions. The Adversarial Critic includes a `performance_regression` rule.

---

## 16. File Format and Interoperability

YaO adopts the following standard formats. Custom formats are introduced only when no existing standard suffices.

| Use | Format | Reason |
|---|---|---|
| Music data | MIDI (.mid), MusicXML (.xml) | Industry standard, full DAW support |
| Score | LilyPond (.ly), PDF | High-quality engraving |
| Specifications | YAML | Human-readable, git-friendly |
| Intermediate representations | JSON | Schema-validatable |
| Provenance | JSON | Graph structure |
| Audio (production) | WAV | Lossless |
| Audio (distribution) | FLAC, MP3 | Compressed standards |
| Live coding | Strudel pattern strings | Browser-native immediate playback |
| Style vectors | JSON | Cross-project shareability |

---

## 17. Ethics and Licensing

### 17.1 Training data and references
The reference library contains **only rights-cleared works**. Each entry in `references/catalog.yaml` declares its license status; entries without status cannot be used.

### 17.2 Artist mimicry
"In the style of [living artist]" is **not** supported. Use abstract feature descriptions instead:

> ✗ "Like Joe Hisaishi"
> ✓ "Wide open string voicings, ascending motifs, major-minor oscillation, contemplative tempo"

This is not just guidance; the StyleVector schema's `do_not_copy` field is a hard-coded allowlist. Attempting to compare melodies, hook rhythms, or chord progressions raises a schema error.

### 17.3 Output rights
Music generated by YaO belongs to the user. When reference influence is excessively high (StyleVector cosine similarity > 0.85 to a single reference across multiple axes), YaO emits a warning.

### 17.4 Transparency
We recommend that every YaO output is published with the `provenance.json` summary, declaring:

- "Generated with YaO"
- The aesthetic anchors referenced
- The genre Skills used
- The Subagents involved

---

## 18. Failure Modes and Operational Discipline **[NEW SECTION]**

Recognizing failure modes is half the work. This section names the failure modes YaO design explicitly defends against.

### 18.1 Mode collapse
**Symptom:** Every generation feels similar.
**Defense:** Multi-candidate generation, Form Library, Harmonic Vocabulary Profiles, Melodic Generation Strategy diversity, multiple Generator strategies (rule-based, stochastic, markov, constraint-solver).

### 18.2 Symbolic optimization drift
**Symptom:** Symbolic scores rise but listening experience degrades.
**Defense:** Parallel acoustic evaluation, Symbolic-Acoustic Divergence rule, weekly audio regression in CI.

### 18.3 Cliché convergence
**Symptom:** Every chord progression is I-V-vi-IV.
**Defense:** Adversarial Critic `cliche_progression` rule, harmonic vocabulary weights per genre, secondary dominant injection prompts.

### 18.4 Surprise deficit
**Symptom:** Spec-correct but predictable, boring.
**Defense:** Surprise Score, `surprise_deficit` critique rule, Tension Arcs, Hook IR with `withhold_then_release` strategy.

### 18.5 Frequency masking
**Symptom:** Multiple instruments fight for the same band; mix sounds muddy.
**Defense:** Frequency Clearance generator, `frequency_collision` critique rule, spectral collision risk in Perceptual Report.

### 18.6 Ensemble silence
**Symptom:** Instruments do not respond to one another; the piece feels mechanical.
**Defense:** Conversation Director Subagent, ConversationPlan, Reactive Fills, `conversation_silence` critique rule.

### 18.7 Cultural monoculture
**Symptom:** The system only produces Western pop-flavored music.
**Defense:** Extended scale library, multilingual SpecCompiler, custom instrument profiles, Culture Skills.

### 18.8 Rights drift
**Symptom:** A reference of unclear status sneaks into the catalog.
**Defense:** Schema-required `rights_status` field, abstract-only StyleVectors (no raw audio comparison), `do_not_copy` allowlist enforced at schema level.

### 18.9 Provenance erosion
**Symptom:** Generated music exists but no one can explain why.
**Defense:** `GeneratorBase.generate()` returns `(ScoreIR, ProvenanceLog)` as a single tuple; the layer architecture makes "skipping provenance" structurally impossible.

### 18.10 Layer boundary erosion
**Symptom:** Generators start importing from `verify`; the architecture rots.
**Defense:** AST-based architecture lint runs in pre-commit and CI; violations cannot be merged.

### 18.11 Test rot
**Symptom:** Tests are skipped, fail silently, or are removed.
**Defense:** No `@pytest.mark.skip` without an Issue link; ratchet on test count in CI; weekly audio regression.

### 18.12 Performance creep
**Symptom:** Generation time slowly grows over months.
**Defense:** Performance budget table in PROJECT.md and CLAUDE.md; the `performance_regression` test in CI.

---

## 19. Quickstart **[REVISED]**

### 19.1 Installation

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-hooks         # Install pre-commit hooks
make setup-soundfonts    # SoundFont setup (first time)
```

### 19.2 First piece via natural language

```bash
yao conduct "a calm piano piece in D minor for studying, 90 seconds"
```

### 19.3 First piece via Claude Code (recommended)

```bash
claude
> /sketch
> "I want background music for a rainy night cafe scene, with piano and cello,
>  a bit melancholy but not depressing, about 90 seconds"
> # ...interactive dialogue completes the spec
> /compose my-rainy-cafe
> # ...generation, evaluation, critique, audio rendering happen automatically
> /critique my-rainy-cafe
> # ...adversarial findings shown
> /pin my-rainy-cafe v001 --location "section:bridge,bar:3" --note "feels too busy"
> /regenerate-section my-rainy-cafe bridge
```

### 19.4 Arranging an existing piece

```bash
cp my_song.mid specs/projects/my-song-arr/source.mid
yao arrange my-song-arr --target-genre lofi_hiphop --preserve melody,form
# ...arrangement diff Markdown report is generated
```

### 19.5 Iteration with a watcher

```bash
yao watch specs/projects/my-rainy-cafe/composition.yaml
# Edit the spec; on each save, regenerate and play automatically
```

---

## 20. Glossary **[REVISED]**

**Conductor (You)** — The human project owner. The final judge.

**Orchestra** — The collective of Subagents.

**Score** — The full set of YAML files describing a piece, under `specs/`.

**ScoreIR** — The internal representation of concrete notes (Layer 3).

**MPIR (Musical Plan IR)** — The plan-level representation between specs and notes (Layer 3.5). The "why" of a composition.

**Trajectory** — Time-axis curves over a piece: tension, density, valence, predictability, brightness, register-height.

**Tension Arc** — A short-range (2–8 bar) tension–resolution structure. **[NEW]**

**Hook** — A memorable 2–4 bar fragment with a deployment strategy. **[NEW]**

**Aesthetic Reference Library** — The catalog of reference pieces and their abstract feature vectors.

**StyleVector** — An abstract numeric vector representing a piece's style — never raw audio similarity, never melody. **[NEW]**

**Perception Substitute Layer** — Layer 4. The mechanism that compensates for AI's inability to literally listen.

**Provenance** — The append-only decision log. Every note has a rationale.

**Adversarial Critic** — The Subagent whose sole purpose is finding weaknesses. Never praises.

**Conversation Plan** — The model of inter-instrument dialogue: voice focus, calls and responses, reactive fills. **[NEW]**

**GrooveProfile** — A genre-specific microtiming + velocity + jitter profile applied across the ensemble. **[NEW]**

**Form Library** — The catalog of song forms (AABA, rondo, etc.). **[NEW]**

**Surprise Score** — The per-note divergence between predicted and actual pitch/duration. **[NEW]**

**Pin** — A localized user feedback attached to a specific (section, bar, beat, instrument). **[NEW]**

**Negative Space** — The intentional design of silence and frequency gaps.

**Iteration** — A versioned generation (`v001`, `v002`, ...).

**Music Lint** — Automatic detection of theory violations and constraint breaches.

**Sketch-to-Spec** — The dialogue process from a natural-language sketch to a complete YAML spec.

**Note Realizer** — A Layer 2 generator that turns MPIR into ScoreIR.

**Use Case** — A declared listening context (`youtube_bgm`, `game_bgm`, `advertisement`, `study_focus`, `cinematic`) that activates context-specific evaluation metrics. **[NEW]**

---

## 21. Closing: What YaO Aspires To Be **[REVISED]**

YaO is **not a project that "lets AI make music"**. It is infrastructure for **humans and AI to co-create music, each contributing their strengths**:

- The **human** brings intent, taste, and judgment.
- The **AI** brings theoretical knowledge, iteration speed, and exhaustive recordkeeping.
- **YaO** is the structured collaboration field that makes both possible at once.

Great music remains an expression of the human soul. YaO aspires to make that expression **faster, deeper, more reproducible, and more improvable**.

The v2.0 evolution is animated by a sharper conviction: that "reproducible engineering" alone is not enough. Music must be **interesting**, **acoustically verified**, **culturally diverse**, **conversationally alive**, and **truly listened to** before it deserves the word *music*. The eight structural improvements in v2.0 — surprise, acoustic truth, diversity sources, ensemble groove, conversation, fine-grained feedback, multilingual breadth, and the arrangement engine — are how YaO commits to that conviction.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready not just to play, but to listen, respond, and surprise.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Last updated: 2026-05-03*
