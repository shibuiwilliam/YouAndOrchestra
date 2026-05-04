# You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## 0. The Essence of the Project

**You and Orchestra (YaO)** is an **agentic music production environment** that runs on top of Claude Code. Unlike typical "AI music tools" that emit music from a single black box, YaO is structured around a different premise: **multiple AI agents (Orchestra Members) with specialized roles, conducted by a human (You = Conductor).**

Every design decision in YaO is subordinate to a single proposition:

> **Music production is not a one-shot intuitive act. It is a reproducible, improvable engineering process.**

Therefore, YaO treats music as **code, specification, tests, diffs, and provenance** *before* it treats it as audio files. This is the **Music-as-Code** philosophy.

---

## 1. The Metaphor: You and Orchestra

Every concept in YaO maps onto an orchestra metaphor. Internalizing this mapping is the shortest path to using YaO correctly.

| YaO Component | Orchestra Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human owner of the project |
| **Score** | Sheet music | YAML specs in `specs/*.yaml` |
| **Orchestra Members** | Musicians | Subagents (Composer, Critic, Theorist, …) |
| **Concertmaster** | Lead violinist | Producer subagent (overall coordinator) |
| **Rehearsal** | Rehearsal | The generate–evaluate–revise loop |
| **Library** | The orchestra's music library | Reference works in `references/` |
| **Performance** | Live performance | The rendered final audio |
| **Recording** | Recording session | Artifacts in `outputs/` |
| **Critic / Reviewer** | Music critic | Adversarial Critic subagent |

The conductor (You) does not write every note. The conductor's job is to **clarify intent, give direction to the players, make judgments during rehearsal, and ensure the quality of the performance.** YaO brings this division of labor into the AI domain.

---

## 2. Design Principles

Every implementation decision in YaO is checked against the following **6 inviolable principles.** They are also transcribed into `CLAUDE.md` so that they function as the agent's decision criteria.

### Principle 1 — The agent is an environment, not a composer
YaO does not aim to be "an AI that writes songs." It aims to be **an environment that makes a human composer 10× faster.** The goal is augmentation of creative judgment, not its replacement.

### Principle 2 — Every decision must be explainable
Every generated note, chord, and arrangement choice records *why* it exists. This is persisted as a Provenance log: traceable, reviewable, modifiable.

### Principle 3 — Constraints liberate
Explicit specs (YAML), reference libraries, and negative-space designs are not cages. They are scaffolding. Unbounded freedom produces paralysis.

### Principle 4 — Time-axis design precedes note design
A piece is first designed as a set of **time-axis trajectories** (tension, density, valence, predictability, register-height). Notes are filled in afterwards. This is what makes long-form pieces structurally meaningful.

### Principle 5 — The human ear is the final truth
However sophisticated automated metrics become, the human listening experience remains the final judge. The agent **assists**, it does not **replace**, human judgment.

### Principle 6 — Incrementality
Do not break what works. Each layer extends progressively. Backwards compatibility is preserved unless deliberately and visibly broken.

---

## 3. Architecture: 7-Layer Model

YaO is constructed in 7 cleanly separated layers. Each layer has an independent input/output contract and is interchangeable and testable in isolation.

```
┌──────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                           │
│   Provenance, RecoverableDecision, user style profile    │
├──────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                         │
│   Lint, analysis, evaluation (6 dims), 35 critique rules │
│   rules, score diff, constraint checking                 │
├──────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                       │
│   MIDI writer, per-instrument stems, audio (FluidSynth), │
│   iteration management                                   │
├──────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                           │
│   Acoustic fingerprinting, reference matcher,            │
│   psychology mapping (planned, see IMPROVEMENT.md)       │
├──────────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation                     │
│   3a: Plan IR (CPIR) — SongFormPlan, HarmonyPlan         │
│   3b: Score IR — Note, Part, Section, Motif, Voicing,    │
│        Trajectory (5-dim), DrumPattern                   │
├──────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                             │
│   Plan generators, note realizer, drum patterner,        │
│   counter-melody, generator registry                     │
├──────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                   │
│   YAML parsing (Pydantic v1 + v2), constraints,          │
│   trajectory, references, intent.md                      │
├──────────────────────────────────────────────────────────┤
│ Layer 0: Constants                                       │
│   46 instruments, 28 scales, 14 chords, MIDI mappings    │
└──────────────────────────────────────────────────────────┘
```

Dependencies flow strictly downward. Lower layers do not import upper layers. This is enforced by an AST-based linter (`make arch-lint`) that fails CI if violated. Restructure your code — never bypass.

The pipeline:

```
Spec → PlanOrchestrator → MusicalPlan (CPIR) → NoteRealizer → ScoreIR → MIDI
                                                    ↓
                                          Verify / Critique / Conductor loop
```

---

## 4. Repository Structure

```
yao/
├── PROJECT.md                       # This file (project-wide design)
├── CLAUDE.md                        # Operational rules for Claude Code
├── README.md                        # User quick-start
├── FEATURE_STATUS.md                # Single source of truth for capabilities
├── IMPROVEMENT.md                   # Analysis & forward-looking proposals
├── VISION.md                        # Target architecture
├── pyproject.toml                   # Python deps + tool config
├── Makefile                         # Development commands
├── .pre-commit-config.yaml          # Pre-commit hook config
├── .github/workflows/ci.yml         # CI: lint, type, arch-lint, tests, golden
│
├── .claude/                         # Claude Code integration
│   ├── commands/                    # Slash commands (compose, critique, sketch,
│   │                                #   arrange, regenerate-section, explain, render)
│   ├── agents/                      # 7 subagent definitions
│   ├── skills/                      # Domain knowledge modules
│   │   ├── genres/                  #   8 genre skills
│   │   ├── theory/                  #   voice-leading, etc.
│   │   ├── instruments/             #   piano, strings, etc.
│   │   └── psychology/              #   tension-resolution, etc.
│   └── guides/                      # Developer guides referenced by CLAUDE.md
│
├── specs/
│   ├── projects/                    # User compositions (versioned)
│   └── templates/                   # Spec templates (v1 + v2)
│
├── src/
│   ├── yao/                         # Main library
│   │   ├── conductor/               # Generate-evaluate-adapt orchestration
│   │   ├── constants/               # Instrument ranges, scales, chord types
│   │   ├── schema/                  # Pydantic models (v1 + v2)
│   │   ├── ir/                      # ScoreIR, plan/ (CPIR), motif, voicing,
│   │   │                            #   harmony, timing, notation, drum
│   │   ├── generators/              # rule_based, stochastic, drum_patterner,
│   │   │                            #   counter_melody, plan/, note/
│   │   ├── perception/              # PSL (planned, IMPROVEMENT.md proposal 1)
│   │   ├── render/                  # MIDI writer, stems, audio, iteration mgmt
│   │   ├── verify/                  # Lint, analyzer, evaluator, diff,
│   │   │                            #   constraints, critique/ (15 rules)
│   │   ├── reflect/                 # Provenance, RecoverableDecision,
│   │   │                            #   style_profile (planned)
│   │   ├── sketch/                  # NL → spec compiler
│   │   ├── arrange/                 # Arrangement engine (stub, IMPROVEMENT.md)
│   │   ├── errors.py                # YaOError hierarchy
│   │   └── types.py                 # Domain types (MidiNote, Beat, Velocity, …)
│   └── cli/                         # Click CLI: 11 commands
│
├── drum_patterns/                   # 8 genre-specific drum pattern YAMLs
├── genre_profiles/                  # Genre profiles (IMPROVEMENT.md proposal 2)
├── references/                      # Aesthetic reference library (rights-cleared)
├── soundfonts/                      # SoundFont files for audio rendering
├── outputs/                         # Generated artifacts (gitignored)
├── gallery/                         # Pre-generated example MIDIs
├── tests/                           # 643+ tests
│   ├── unit/                        #   Per-module unit tests
│   ├── integration/                 #   Full pipeline tests
│   ├── scenarios/                   #   Musical scenarios (trajectory, motif)
│   ├── music_constraints/           #   Range / voice-leading constraints
│   └── golden/                      #   Bit-exact MIDI regression
├── tools/                           # arch lint, feature status check,
│                                    #   silent fallback detector, skill sync
└── docs/                            # mkdocs documentation
    ├── design/                      # ADRs (Architecture Decision Records)
    ├── tutorials/
    └── glossary.md
```

---

## 5. The Orchestra: Subagent Roster

Each Orchestra Member has a clearly defined role and constraints. Each subagent has its own context, allowed tools, and evaluation criteria. They operate independently and are integrated by the Producer subagent.

### 5.1 Composer
**Responsibility:** melody, themes, structural outlines
**Inputs:** `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`
**Outputs:** Score IR (motifs, melodic lines, structural information)
**Forbidden:** instrument selection, final voicing (those belong to Orchestrator)
**Evaluated on:** motif memorability, balance of repetition and variation, fit to trajectory

### 5.2 Harmony Theorist
**Responsibility:** chord progressions, modulation, secondary dominants, cadences, reharmonization
**Inputs:** Composer's melodic proposals, harmony section of `composition.yaml`
**Outputs:** Harmony IR (functional notation + concrete voicing candidates)
**Evaluated on:** functional consistency, tension–resolution, genre fit

### 5.3 Rhythm Architect
**Responsibility:** drum patterns, groove, syncopation, fills
**Inputs:** rhythm section of `composition.yaml`, genre specification
**Outputs:** Rhythm IR (rhythm placement for all instruments)
**Evaluated on:** groove feel, humanization, section-to-section contrast

### 5.4 Orchestrator
**Responsibility:** instrument assignment, voicing, register placement, countermelodies
**Inputs:** outputs from Composer / Harmony Theorist / Rhythm Architect
**Outputs:** complete Score IR with all parts assigned
**Evaluated on:** frequency-space collision avoidance, idiomatic instrument use, textural density

### 5.5 Adversarial Critic
**Responsibility:** find every weakness; never praise
**Inputs:** any artifact at any stage
**Outputs:** `critique.md` with structured `Finding` objects (severity, evidence, location, recommendation)
**Property:** **never compliments.** Detects clichés, structural monotony, emotional misalignment, similarity to existing works.
**Evaluated on:** comprehensiveness and specificity of issue detection

### 5.6 Mix Engineer
**Responsibility:** stereo placement, dynamics, frequency-masking relief, loudness management
**Inputs:** Orchestrator output + `production` parameters
**Outputs:** mix instructions (per-track EQ / compression / reverb / panning)
**Evaluated on:** LUFS target adherence, frequency balance, stereo spread

### 5.7 Producer
**Responsibility:** integration, prioritization, dialogue with the human conductor, final judgment
**Inputs:** all subagent outputs + human feedback
**Outputs:** final production decisions, instructions for the next iteration
**Privilege:** the only subagent that can reject or send back another subagent's output
**Evaluated on:** fidelity to the piece's intent (`intent.md`)

---

## 6. The 6-Phase Compositional Cognition Protocol

The `/compose` and `/arrange` commands force Claude Code through the following 6 phases **in order.** This structures the cognitive process and prevents the failure pattern "the agent starts writing notes immediately."

### Phase 1 — Intent Crystallization
From user input (dialogue, YAML, sketch), articulate the essence of the piece in 1–3 sentences. Do not allow ambiguity. Commit it to `intent.md`.

> Example: "Early summer morning, forward-leaning anticipation toward a new challenge. A faint thread of anxiety underneath. Neither too refreshing nor too sentimental — a neutral, slightly elevated mood."

### Phase 2 — Architectural Sketch
Draw the time-axis trajectories (tension / density / valence / predictability / register-height) **first.** No notes yet. Complete `trajectory.yaml`.

### Phase 3 — Skeletal Generation
Composer generates 5–10 candidate skeletons of chord progression and main melody. **Diversity over completion** — 60% completeness is sufficient.

### Phase 4 — Critic–Composer Dialogue
Adversarial Critic attacks all candidates. Producer judges, picks the strongest, or instructs Composer to combine strengths into a new candidate.

### Phase 5 — Detailed Filling
Harmony Theorist / Rhythm Architect / Orchestrator fill the chosen skeleton with details. Each decision is recorded in Provenance.

### Phase 6 — Listening Simulation
Perception Substitute Layer "listens" to the finished piece, measures divergence from the original intent (Phase 1). If divergence exceeds threshold, the relevant section is regenerated. Final outputs: `critique.md` and `analysis.json`.

---

## 7. Specification Files

YaO describes a piece using the following YAML / Markdown / JSON files. All are version-controlled, all changes are visible in `git diff`.

### 7.1 `intent.md` (intent statement, natural language)
The essence of the piece in 1–3 sentences. The ultimate ground for every decision.

### 7.2 `composition.yaml` (composition parameters)
Key, tempo, time signature, form, genre, instrumentation, per-section structure. v1 (simple) and v2 (rich, 11 sections, 22 Pydantic models) variants.

### 7.3 `trajectory.yaml` (time-axis trajectories)
Time functions for tension, density, valence, predictability, and register-height. Bezier curves, stepped sections, or linear interpolation.

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.4], [32, 0.85], [48, 0.6], [64, 0.3]]
  density:
    type: stepped
    sections: {intro: 0.3, verse: 0.5, chorus: 0.9, bridge: 1.0}
  predictability:
    type: linear
    target: 0.65
    variance: 0.15
```

### 7.4 `references.yaml` (aesthetic reference library)
Positive references (sound like) and negative references (do not sound like). For each, what to extract.

### 7.5 `negative-space.yaml` (what NOT to play)
Rests, frequency gaps, textural subtraction. Designs the silence as carefully as the sound.

### 7.6 `arrangement.yaml` (arrangement parameters)
Source piece, items to preserve, items to transform, items to avoid.

### 7.7 `production.yaml` (mixing & mastering)
LUFS target, stereo width, reverb amount, and other final acoustic specifications.

### 7.8 `provenance.json` (auto-generated, human cannot hand-write)
The complete decision log. Every note, chord, and instrument selection retains its rationale.

---

## 8. Custom Commands (the conductor's baton)

The user drives the Orchestra through the following commands, defined in `.claude/commands/*.md` and surfaced through both the CLI and Claude Code slash commands.

| Command | Purpose | Primary Subagents |
|---|---|---|
| `/compose <project>` | Generate a new piece from spec | Composer → all |
| `/arrange <project>` | Transform an existing piece | Orchestrator + Adversarial Critic |
| `/critique <iteration>` | Critique an existing artifact | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section, preserve the rest | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate between two moods | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment (live mode) | Composer + Rhythm |
| `/explain <element>` | Explain a generation decision | Producer (Provenance query) |
| `/diff <iter_a> <iter_b>` | Musical diff between two iterations | Verifier |
| `/render <iteration>` | MIDI → audio / score | Mix Engineer |
| `/sketch` | Sketch → spec dialogue mode | Producer |

The CLI mirrors these as `yao conduct`, `yao compose`, `yao arrange`, `yao regenerate-section`, `yao render`, `yao preview` (instant audition), `yao watch` (file-watch + auto-regenerate), `yao validate`, `yao evaluate`, `yao diff`, `yao explain`, `yao new-project`.

---

## 9. Skills (the musicians' education)

`.claude/skills/` holds structured knowledge modules. Subagents consult them as needed.

### 9.1 Genre Skills (8 + planned profile-data extension)
Each genre is one Skill: typical chord progressions, rhythm patterns, instrumentation, representative reference works, clichés to avoid. Per IMPROVEMENT.md proposal 2, each Skill is paired with a `genre_profiles/*.yaml` data file that generators consume directly, so that "8 genres supported" becomes acoustically distinguishable rather than nominal.

### 9.2 Theory Skills
Voice leading, counterpoint, reharmonization, modal interchange. Exception rules and genre dependencies are explicitly documented.

### 9.3 Instrument Skills
Per-instrument range, idiomatic playing, timbral characteristics, physical limits, representative phrase patterns.

### 9.4 Psychology Skills
Empirical mappings from music psychology (Juslin, Sloboda, Krumhansl, Huron). Tempo and arousal, major–minor and emotional valence, spectral centroid and brightness perception.

---

## 10. Hooks (automatic stage cues)

Hooks are not instructions to Claude Code. They are **scripts whose execution is guaranteed.** YaO ships with the following:

| Hook | Trigger | Action |
|---|---|---|
| `pre-commit-lint` | Before `git commit` | ruff + mypy + arch-lint + music21-based theory lint + YAML schema validation |
| `post-generate-render` | After generation completes | Auto-render MIDI to audio and notation |
| `post-generate-critique` | After generation completes | Run Adversarial Critic |
| `update-provenance` | After any modification | Update Provenance graph |

These ensure quality even when the agent forgets explicit instructions.

---

## 11. Quality Assurance: Evaluation Metrics

Every generated piece is automatically scored across 5 dimensions, persisted to `evaluation.json`. Scores are 1.0–10.0 with pass/fail thresholds.

### 11.1 Structural Evaluation (25%)
Section contrast, climax position, density-curve fit, repetition balance, loopability, rhythm variety, syncopation ratio.

### 11.2 Melodic Evaluation (30%)
Pitch range utilization, motif recall (planned, see IMPROVEMENT.md proposal 3), singability, phrase closure, contour variety, stepwise motion ratio.

### 11.3 Harmonic Evaluation (25%)
Chord-function consistency, tension–resolution, harmonic complexity vs spec, cadence strength, pitch class variety, consonance ratio.

### 11.4 Arrangement Evaluation
Instrument-role clarity, frequency-collision risk, source preservation (arrangement mode), transformation strength.

### 11.5 Acoustic Evaluation
BPM match, beat stability, LUFS target, spectral balance, onset density. Acoustic-level evaluation is being deepened per IMPROVEMENT.md proposal 1.

Each metric uses a typed `MetricGoal` (7 types: AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN, MATCH_CURVE, RELATIVE_ORDER, DIVERSITY). When a target is missed, the Adversarial Critic raises a structured `Finding`, and the Conductor's feedback adaptation responds in the next iteration.

---

## 12. The Conductor: Generate–Evaluate–Adapt Loop

```
Spec → Plan → Generate → Evaluate → Pass? → Done
                            ↓ No
                       Adapt spec → Regenerate
                            ↑              ↓
                            └──────────────┘
```

The Conductor automates the iteration loop. For each cycle:

1. **Plan** the composition (form + harmony) from the spec.
2. **Realize** the plan into notes via the chosen generator.
3. **Score** the result across 10 metrics in 3 dimensions.
4. **Critique** the result with the 35 critique rules across 12 categories (structural, melodic, harmonic, rhythmic, arrangement, emotional, genre fitness, memorability, surprise, hook, groove, acoustic, conversation).
5. **Adapt** the spec if metrics or findings fail thresholds.
6. **Regenerate** with the adapted spec.

| Problem Detected | Adaptation |
|---|---|
| Low pitch variety | Increase temperature / switch to stochastic |
| Too many melodic leaps | Decrease temperature for smoother lines |
| Sections too similar | Differentiate dynamics across sections |
| Too dissonant | Reduce temperature |
| Climax absence | Adjust section dynamics |
| Cliché progression | Flag for manual harmonic revision |
| Section monotony | Inject motivic variation |

Each iteration is saved as `v001`, `v002`, … with full provenance, so users can trace exactly what changed and why.

---

## 13. Roadmap

### 13.1 Technical Phases

#### Phase 0 — MVP scaffolding (✅ done)
Project structure, CLAUDE.md, dependency setup, minimal pretty_midi generation, SoundFont rendering, basic report.

#### Phase 1 — Parameter-driven symbolic composition (✅ done)
Spec system, 6-phase protocol, Composer / Harmony / Rhythm subagents, music21-based analysis, evaluator. **Currently the deployed phase.**

#### Phase 2 — Arrangement engine and diff (in progress)
Arrangement operations (reharmonize, regroove, reorchestrate, …), Style Vector, Arrangement Diff, full Provenance. Tracked in IMPROVEMENT.md proposal 5.

#### Phase 3 — Perception layer and deep critique (in progress)
Perception Substitute Layer, reference library matcher, expanded acoustic critique, multi-resolution trajectory. Tracked in IMPROVEMENT.md proposal 1.

#### Phase 4 — Advanced features
Sketch-to-spec dialogue, music theory knowledge graph, fully populated genre Skills, live-coding integration (Strudel / Sonic Pi), evolutionary multi-candidate generation.

#### Phase 5 — Production integration
DAW connection (Reaper-first), AI music model bridges (Stable Audio etc.), live-improvisation mode, user preference learning.

#### Phase 6 — Continuous learning
Layer 7 (Reflection) full operation, per-user style profiles, community reference-library sharing protocol.

### 13.2 User-Value Milestones

In parallel to the technical phases, progress is measured against user-visible milestones.

| Milestone | User Value | Key Features |
|---|---|---|
| **1. Describe & Hear** | "Write YAML, hear it instantly" | CLI compose, two generators, templates, automatic versioning |
| **2. Iterate & Improve** | "Tell it what's wrong and it improves" | Score diff, evaluation report, `/critique`, section regeneration |
| **3. Richer Music** | "Pro-quality harmony, rhythm, dynamics" | Harmony IR, constraint system, walking bass, syncopation |
| **4. My Style** | "It learns my taste and generates in it" | Reference matching, spec composition, style profile |
| **5. Production Ready** | "Output usable in real projects" | DAW connection, multi-format output, mix engineer |

### 13.3 Strategic Insight

YaO's design pattern is not music-specific. It is a **general framework for structured human–AI creative collaboration.**

| YaO Pattern | General Pattern | Applicable Domains |
|---|---|---|
| Score (YAML spec) | **Intent-as-Code** | UI design specs, narrative structure, game level design |
| Trajectory (curves) | **Time-axis quality curves** | Video pacing, presentation arc, UX journeys |
| Adversarial Critic | **Adversarial review** | Code review, design critique, writing feedback |
| Provenance Graph | **Decision provenance** | All AI-assisted creative work |
| 6-Phase Protocol | **Structured creative protocol** | Any domain where "don't implement immediately" matters |

These abstractions are designed to be extractable later, but the current scope is restricted to music production.

### 13.4 Development Process Guidelines

- **Sound-First culture** — changes that affect generation or rendering must include audio samples before/after.
- **Documentation budget** — at least 3 lines of working code per 1 line of design doc, sustained.
- **Dogfooding** — music generated by YaO is used in the project's own demo videos and presentations.
- **Musicians-friendly contribution** — adding a genre Skill, authoring a template, analyzing a reference work — none of these require Python.

---

## 14. Quick Start

### 14.1 Setup

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-hooks         # pre-commit + pre-push hooks
make setup-soundfonts    # SoundFont placement (first time only)
```

Requires Python 3.11+. Audio rendering requires FluidSynth.

### 14.2 Three usage modes

```bash
# 1. Natural language (fastest)
yao conduct "a calm piano piece in D minor for studying, 90 seconds"

# 2. YAML specification (full control)
yao compose specs/projects/my-song/composition.yaml

# 3. Claude Code (interactive, recommended)
> /sketch a mysterious puzzle game BGM, minimal and looping
```

### 14.3 Your first piece via Claude Code

```bash
# 1. Create a project
make new-project NAME=my-first-song

# 2. Launch Claude Code
claude

# 3. Conversation example
> /sketch
> "A slightly melancholy 90-second piano piece for a rainy night cafe"
> (dialogue resolves the spec)
> /compose my-first-song

# 4. Inspect the result
open outputs/projects/my-first-song/iterations/v001/score.pdf
afplay outputs/projects/my-first-song/iterations/v001/audio.wav

# 5. Iterate
> /critique my-first-song v001
> /regenerate-section my-first-song chorus
```

### 14.4 Arranging an existing piece

```bash
cp my_song.mid specs/projects/my-first-song/source.mid
# Author specs/projects/my-first-song/arrangement.yaml
> /arrange my-first-song
```

### 14.5 Instant audition

```bash
yao preview specs/templates/minimal.yaml   # Generate and play in memory; no file
yao watch   specs/templates/minimal.yaml   # Edit + save → hear instantly
```

---

## 15. File Formats and Interoperability

YaO commits to standard formats so that artifacts interoperate with external tools.

| Use | Format | Reason |
|---|---|---|
| Music data | MIDI (.mid), MusicXML (.xml) | Industry standard; all DAWs |
| Notation | LilyPond (.ly), PDF | Publication-quality scores; auto-render |
| Specs | YAML | Human-readable; git-friendly |
| Intermediate representation | JSON | Programmatically readable; schema-validated |
| Provenance | JSON | Graph-structured |
| Audio | WAV (working), FLAC / MP3 (distribution) | Standard support |
| Live-coding | Strudel pattern strings | Browser-instant audition |

Custom formats are avoided. New formats are introduced only if no existing standard suffices.

---

## 16. Ethics and Licensing

### 16.1 Training data and references
The reference library contains **only rights-cleared works.** Each entry in `references/catalog.yaml` records its license status. Works of unknown status are not used.

### 16.2 Artist imitation
"Sounds like a specific living artist" is not recommended. Instead, use **abstract feature descriptions:**

> ✗ "Joe Hisaishi-style"
> ✓ "Open wide-voiced strings, ascending motif, modal mixture between major and minor, contemplative tempo"

### 16.3 Rights to generated works
In principle, generated works belong to the user. When a piece's similarity to references is extreme, YaO emits a warning.

### 16.4 Transparency
All generated artifacts should record (a) "produced with YaO" and (b) a list of aesthetic anchors consulted, in `provenance.json`.

---

## 17. Document Hierarchy

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this file) | Humans + agents | Project-wide design, philosophy, architecture |
| `CLAUDE.md` | Agent-focused | Operational rules, prohibitions, skill pointers |
| `README.md` | Human-focused | Quick start, minimal usage |
| `FEATURE_STATUS.md` | Humans + agents | Single source of truth for current capabilities |
| `IMPROVEMENT.md` | Maintainers | Forward-looking analysis & proposals |
| `VISION.md` | Humans + agents | Target architecture |
| `docs/design/*.md` | Humans + agents | Individual design decision records (ADRs) |
| `development/*.md` | Developers + agents | Technical development docs |
| `docs/` (mkdocs) | Users + developers | Tutorials, reference, mkdocs site |

In case of conflict between documents, the precedence order is: **`CLAUDE.md` > `PROJECT.md` > other docs.** `FEATURE_STATUS.md` overrides all others on the question "what currently exists."

---

## 18. Future Architectural Extensions

The following are under consideration. Each lands when the corresponding milestone demands it.

### 18.1 Session / Project Runtime layer
The current CLI is stateless. A future `ProjectRuntime` will support:
- Generation cache (for fast section regeneration)
- Feedback queue (critique → revision loop)
- Undo / redo at the musical level

### 18.2 Abstract Agent Protocol
`.claude/agents/*.md` is currently bound to Claude Code. A backend-agnostic Python protocol (`AgentRole`, `AgentContext`, `AgentOutput`) will be defined, with Claude Code as one adapter.

### 18.3 Lower-latency feedback
The `YAML → MIDI → WAV → external player` pipeline has too much latency. Future:
- `yao preview` with inline MIDI playback (already shipping)
- Strudel pattern emission for browser-based instant audition
- `sounddevice` direct WAV playback (already shipping)

### 18.4 Spec composability
`specs/fragments/` for reusable spec fragments, with `extends:` / `overrides:` keywords.

### 18.5 Perception, Arrangement, Feedback
See **`IMPROVEMENT.md`** for detailed proposals on closing the perception gap, deepening genre implementation, motivic development, spec–implementation honesty, arrangement engine, and structured human feedback.

---

## 19. Glossary

**Conductor** — the human owner of a project. The final judge.

**Orchestra** — the collection of subagents.

**Score** — the YAML files in `specs/`. A piece's complete description.

**Score IR** — the in-implementation intermediate representation of a Score.

**CPIR (Composition Plan IR)** — the planning-layer IR sitting between Spec and Score IR. Includes SongFormPlan and HarmonyPlan; the future MotivicDevelopmentPlan extends this layer.

**Trajectory** — a piece's time-axis characteristic curve (tension, density, …).

**Aesthetic Reference Library** — works that serve as aesthetic anchors.

**Perception Substitute Layer** — the layer that compensates for AI's inability to "listen" acoustically. Currently planned; see IMPROVEMENT.md.

**Provenance** — the auditable log of every generation decision.

**Adversarial Critic** — the subagent that deliberately attacks the output. Never praises.

**Negative Space** — the design of what is not played.

**Style Vector** — a multi-dimensional feature representation of a genre or style.

**Iteration** — a generated version within a project. Numbered `v001`, `v002`, …

**Music Lint** — automatic detection of music-theory and constraint violations.

**Sketch-to-Spec** — the dialogue process that converts a natural-language sketch into a YAML spec.

**Genre Profile** — a structured YAML/dataclass encoding the harmonic, melodic, rhythmic, and acoustic preferences of a genre. The mechanism that makes "8 genres supported" actually mean 8 distinct sounds.

**Recoverable Decision** — a logged record of any place where YaO chose a fallback rather than failing. Replaces the older "silent fallback" anti-pattern with explicit, queryable decisions.

---

## 20. Closing: The World YaO Aims For

YaO is not "an AI that creates music." It is **infrastructure on which humans and AI co-create music**, each contributing their strengths.

- **Humans contribute** intent, judgment, and sensibility.
- **AI contributes** theoretical knowledge, iteration speed, and exhaustive record-keeping.
- **YaO contributes** the structured collaborative process that lets the two fit together.

Great music remains, finally, **the expression of a human soul.** YaO exists to make that expression **faster, deeper, and more reproducible.**

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Last updated: 2026-05-04*
