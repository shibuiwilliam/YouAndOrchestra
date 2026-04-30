# You and Orchestra (YaO) — PROJECT.md v3.0

> *An agentic music production environment built on Claude Code*
> *— where you are the conductor, and the AI is your orchestra.*

---

## Document Status

This is **PROJECT.md v3.0**. It describes **what YaO is today** — current architecture, working features, and implementation status. For the target architecture and future vision, see [VISION.md](./VISION.md). For development rules, see [CLAUDE.md](./CLAUDE.md).

The **Capability Matrix** (Section 4) is the single source of truth for what works.

---

## Table of Contents

0. [Project Essence](#0-project-essence)
1. [Metaphor: You and Orchestra](#1-metaphor-you-and-orchestra)
2. [Five Inviolable Principles](#2-five-inviolable-principles)
3. [Capability Matrix (Single Source of Truth)](#3-capability-matrix-single-source-of-truth)
4. [Architecture](#4-architecture)
5. [Specification Layer](#5-specification-layer)
6. [Generation Pipeline](#6-generation-pipeline)
7. [Verification & Evaluation](#7-verification--evaluation)
8. [Rendering](#8-rendering)
9. [The Conductor](#9-the-conductor)
10. [Claude Code Integration](#10-claude-code-integration)
11. [Directory Structure](#11-directory-structure)
12. [Quick Start](#12-quick-start)
13. [Ethics & Licensing](#13-ethics--licensing)
14. [Document Roles](#14-document-roles)

---

## 0. Project Essence

**You and Orchestra (YaO)** is an **agentic music production environment built on Claude Code**. Unlike a generic "AI music tool" that emits music from a black box, YaO is a structured environment in which **a human (You = Conductor) directs AI through a transparent, layered, auditable production pipeline**.

YaO treats music as **specification, code, test, diff, and provenance** before treating it as audio.

---

## 1. Metaphor: You and Orchestra

| YaO Component | Orchestral Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human owning the project |
| **Score** | Sheet music | YAML specs in `specs/` |
| **Orchestra Members** | Players | Subagents (Composer, Critic, Theorist, ...) |
| **Rehearsal** | Iterative refinement | Generate-evaluate-adapt-regenerate loop |
| **Performance** | Concert | Final rendered audio |
| **Recording** | Recording session | `outputs/iterations/` |
| **Critic** | External reviewer | Adversarial Critic Subagent |

---

## 2. Five Inviolable Principles

### Principle 1: The agent is an environment, not a composer
YaO augments human creativity. Full automation is not the goal.

### Principle 2: Every decision is explainable
Every generated note carries a *why* in the Provenance Log — persistent, queryable, traceable.

### Principle 3: Constraints liberate
Specs and rules are scaffolds, not cages. Unlimited freedom produces paralysis.

### Principle 4: Time-axis first
Trajectory curves and structural plans are designed *first*. Notes fill the structure *second*.

### Principle 5: The human ear is the final truth
Agents *inform*, never *replace*, human judgment.

---

## 3. Capability Matrix (Single Source of Truth)

This matrix is the **single authoritative description of what YaO can and cannot do**. It is updated with every PR, never aspirationally.

Status legend: ✅ Implemented · 🟢 Working but limited · 🟡 Partial · ⚪ Designed, not started · 🔴 Identified gap

| Area | Feature | Status | CLI | Claude Cmd | Tests | Notes |
|---|---|---|---|---|---|---|
| **Spec / Input** | composition.yaml v1 | ✅ | compose | /compose | yes | Pydantic v1 schema with sections, instruments, generation config |
| | composition.yaml v2 (rich DSL) | 🟢 | validate-spec | — | yes | limitation: schema implemented; no plan generators consume it yet |
| | intent.md as first-class artifact | 🟢 | new-project | — | yes | limitation: parsed with keyword extraction; no NL→emotion inference yet |
| | trajectory.yaml multi-dimensional | 🟢 | --trajectory | — | yes | limitation: 5 dims defined; generators respond to tension-velocity only |
| | constraints with scoping | ✅ | (in spec) | — | yes | must/must_not/prefer/avoid × global/section/instrument/bars |
| | NL → Spec compiler (sketch state machine) | 🟡 | conduct | /sketch | yes | limitation: keyword matching in Conductor only; no state machine |
| **Plan IR** | SongFormPlan | ✅ | — | — | yes | SectionPlan + SongFormPlan with section_at_bar, serialization |
| | HarmonyPlan with functions/cadences | ✅ | — | — | yes | ChordEvent + HarmonicFunction + CadenceRole + ModulationEvent |
| | MotifPlan / PhrasePlan | ⚪ | — | — | no | Skeleton files only; Phase beta |
| | DrumPattern IR | 🔴 | — | — | no | Skeleton file only; Phase beta |
| | ArrangementPlan | ⚪ | — | — | no | Skeleton file only; Phase beta |
| | MusicalPlan (integrated) | 🟢 | — | — | yes | limitation: form + harmony populated; motifs/arrangement/drums still None |
| **Generation** | rule_based generator (v1, spec→notes) | ✅ | compose | — | yes | Deterministic; also wrapped as NoteRealizer |
| | stochastic generator (v1, spec→notes) | ✅ | compose | — | yes | Seed + temperature, 4 contours, chord voicings; also wrapped as NoteRealizer |
| | generator registry (legacy) | ✅ | — | — | yes | @register_generator for v1 compat |
| | plan generator registry | ✅ | — | — | yes | @register_plan_generator; form + harmony planners |
| | note realizer registry | ✅ | — | — | yes | @register_note_realizer; rule_based + stochastic |
| | form planner (rule_based) | ✅ | — | — | yes | Spec sections → SongFormPlan with roles/climax |
| | harmony planner (rule_based) | ✅ | — | — | yes | Spec harmony → HarmonyPlan with chord events/cadences |
| | plan orchestrator | ✅ | — | — | yes | Runs form → harmony planners, builds MusicalPlan |
| | legacy adapter (v1→v2 bridge) | ✅ | — | — | yes | v1 CompositionSpec → v2 pipeline |
| | markov generator | ⚪ | — | — | no | Phase beta |
| | constraint_satisfaction generator | ⚪ | — | — | no | Phase beta |
| **Critique** | critique base types (Finding, CritiqueRule) | ✅ | — | — | yes | Base types + registry |
| | MetricGoal type system | ✅ | — | — | yes | 7 goal types: AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN, MATCH_CURVE, RELATIVE_ORDER, DIVERSITY |
| | RecoverableDecision logging | ✅ | — | — | yes | 9 known codes; integrated with ProvenanceLog and both generators |
| | rule-based critique engine (30+ rules) | 🔴 | — | /critique | no | Phase beta |
| **Rendering** | MIDI writer + stems | ✅ | render | /render | yes | midi_writer.py + stem_writer.py |
| | audio renderer (FluidSynth) | ✅ | render | /render | yes | audio_renderer.py; requires FluidSynth install |
| | MIDI reader | ✅ | — | — | yes | midi_reader.py; loads MIDI back to ScoreIR |
| | iteration management | ✅ | — | — | yes | iteration.py; v001/v002/... versioning |
| **Conductor** | basic generate-evaluate-adapt | ✅ | conduct | — | yes | conductor.py + feedback.py + result.py |
| | section regeneration | ✅ | regenerate-section | /regenerate-section | yes | — |
| | multi-candidate conductor | 🔴 | — | — | no | Phase beta |
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
| | Evaluator (5-dimension + quality score) | ✅ | evaluate | — | yes | evaluator.py; MetricGoal-based + weighted quality_score |
| | Rhythm evaluation (variety + syncopation) | ✅ | — | — | yes | evaluate_rhythm() in evaluator.py |
| | Score diff | ✅ | diff | — | yes | diff.py with modified note tracking |
| | Constraint checker | ✅ | — | — | yes | Part of verify pipeline |
| **Subagents** | 7 definitions (.claude/agents/) | ✅ | — | (all) | n/a | Prompt definitions only; no runtime impl |
| **Skills** | genre skills | 🟡 | — | — | n/a | 1 of 12 target (cinematic) |
| | theory skills | 🟡 | — | — | n/a | 1 of target set (voice-leading) |
| | instrument skills | 🟡 | — | — | n/a | 1 of 38 target (piano) |
| | psychology skills | 🟡 | — | — | n/a | 1 of target set (tension-resolution) |
| **QA** | unit tests | ✅ | make test-unit | — | yes | ~400 unit tests |
| | integration tests | ✅ | make test-integration | — | yes | Full pipeline tests |
| | scenario tests | ✅ | make test | — | yes | Musical scenario validation |
| | music constraint tests | ✅ | make test-music | — | yes | Parameterized across instruments |
| | golden MIDI tests | ✅ | make test-golden | — | yes | 6 goldens: 3 specs × 2 realizers, bit-exact comparison |
| | architecture lint | ✅ | make arch-lint | — | yes | tools/architecture_lint.py |

---

## 4. Architecture

YaO uses a layered architecture with downward-only dependencies, enforced by `make arch-lint`.

```
+--------------------------------------------------------------+
| Conductor                                                    |
|   Feedback loop: generate → evaluate → adapt → regenerate    |
+--------------------------------------------------------------+
| Layer 6: Verification (verify/)                              |
|   Linting, evaluation, constraint checking, score diffing    |
+--------------------------------------------------------------+
| Layer 5: Rendering (render/)                                 |
|   MIDI writing/reading, audio rendering, stems, iterations   |
+--------------------------------------------------------------+
| Layer 3.5: Musical Plan IR (ir/plan/)  [ALPHA]               |
|   SongFormPlan, HarmonyPlan — structural decisions            |
+--------------------------------------------------------------+
| Layer 3: Score IR (ir/)                                      |
|   Note, Part, Section, ScoreIR, harmony, motif, voicing      |
+--------------------------------------------------------------+
| Layer 2: Generation (generators/)                            |
|   Rule-based + stochastic, plan generators, note realizers   |
+--------------------------------------------------------------+
| Layer 1: Foundation (schema/ + reflect/)                     |
|   Pydantic specs (v1 + v2), provenance, recoverable decisions|
+--------------------------------------------------------------+
| Layer 0: Constants (constants/)                              |
|   38 instruments, 14 scales, 14 chord types, MIDI mappings   |
+--------------------------------------------------------------+
```

**Library restrictions:**

| Library | Allowed In |
|---------|-----------|
| `pretty_midi` | ir/, render/ |
| `music21` | ir/, verify/ |
| `librosa` | verify/, perception/ |
| `pyloudnorm` | verify/, perception/ |

Key data types:
- **`CompositionSpec`** (Pydantic) — validated YAML input
- **`ScoreIR`** (frozen dataclass) — concrete notes: Section → Part → Note
- **`ProvenanceLog`** (append-only) — decision log with rationale
- **`EvaluationReport`** — quality scores + user-facing quality_score (1-10)

---

## 5. Specification Layer

YaO supports two spec formats (auto-detected at load time):

**v1** — Simple flat YAML with title, key, tempo, instruments, sections, generation config.

**v2** — 11-section format with identity, globals, emotion, form, melody, harmony, rhythm, drums, arrangement, production, constraints.

Additional artifacts: `trajectory.yaml` (time-axis curves), `intent.md` (natural language purpose), `constraints.yaml`, `references.yaml`, `negative-space.yaml`, `production.yaml`.

7 templates available in `specs/templates/` (4 v1, 3 v2).

---

## 6. Generation Pipeline

The current working pipeline:

```
CompositionSpec → Generator → ScoreIR → MIDI/Audio
```

Two generators are available:

### Rule-based (deterministic)
- Scale-based stepwise melody, root-note bass, diatonic triads
- Same spec always produces same output — good for golden tests

### Stochastic (controlled randomness)
- **4 melodic contour algorithms**: arch, ascending, descending, wave (section-aware selection)
- **Chord voicing variety**: root position, first/second inversion, open, drop2 (temperature-dependent)
- **Section-aware chord progressions**: different patterns for verse, chorus, bridge, intro, outro
- **Diatonic 7th chords**: maj7, min7, dom7 with temperature-dependent probability
- **12 rhythm templates**: syncopation, dotted rhythms, mixed patterns
- **Walking bass**: quarter-note patterns with passing tones and approach notes
- **Velocity humanization**: dynamics-derived with trajectory tension modifier
- **Motif transformation**: transpose, invert, retrograde for secondary melody instruments
- **Configurable via StochasticConfig**: all magic numbers extracted into a frozen dataclass

Generation selection: `spec.generation.strategy` → `"rule_based"` or `"stochastic"`.

---

## 7. Verification & Evaluation

### Evaluation (5 dimensions, 10 metrics)

| Dimension | Metrics |
|---|---|
| **Structure** | Section count, section contrast, bar count accuracy, rhythm variety, syncopation ratio |
| **Melody** | Pitch range utilization, stepwise motion ratio, contour variety |
| **Harmony** | Pitch class variety, consonance ratio |

Each metric is evaluated against a **MetricGoal** (7 types: AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN, MATCH_CURVE, RELATIVE_ORDER, DIVERSITY).

**Quality Score**: Aggregate 1.0-10.0 score weighted by dimension (melody 30%, harmony 25%, structure 25%, arrangement 10%, acoustics 10%).

### RecoverableDecision
When the system must compromise (e.g., note out of range), it logs a `RecoverableDecision` instead of silently clamping. These are traceable and actionable in future iterations.

### Other verification
- **Music linting**: range violations, parallel fifths, velocity bounds, duration checks
- **Score diffing**: added/removed/modified notes between two generations
- **Constraint checking**: must/must_not/prefer/avoid with scoped rules

---

## 8. Rendering

| Output | Engine |
|---|---|
| MIDI (.mid) | pretty_midi |
| Per-instrument stems | stem_writer.py |
| WAV audio | FluidSynth (optional) |

Each iteration produces: `full.mid`, `stems/`, `analysis.json`, `evaluation.json`, `provenance.json`.

Iterations are auto-versioned: `v001`, `v002`, etc. — previous versions are never overwritten.

---

## 9. The Conductor

The Conductor automates the generate-evaluate-adapt loop:

```
Description/Spec → Generate → Evaluate → Pass? → Done
                                 | No
                             Adapt spec → Regenerate
```

- **Natural language**: parses mood keywords (67 moods), pace, instrument keywords, duration
- **Feedback loop**: 8 adaptation rules map failing metrics to spec changes (temperature adjustments, strategy switches, dynamics differentiation)
- **Section regeneration**: regenerate one section while preserving the rest

---

## 10. Claude Code Integration

### 7 Slash Commands
`/sketch`, `/compose`, `/critique`, `/regenerate-section`, `/explain`, `/render`, `/arrange`

### 7 Subagents
Producer, Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Adversarial Critic. Currently prompt definitions in `.claude/agents/`.

### 4 Domain Skills
cinematic genre, voice-leading theory, piano instrument, tension-resolution psychology.

---

## 11. Directory Structure

```
yao/
├── CLAUDE.md                     # Development rules
├── PROJECT.md                    # This document (current state)
├── VISION.md                     # Target architecture
├── README.md                     # User guide
├── src/yao/                      # Main library
│   ├── constants/                # Layer 0
│   ├── schema/                   # Layer 1 (v1 + v2 specs)
│   ├── ir/                       # Layer 3 (ScoreIR + plan/)
│   ├── reflect/                  # Provenance + RecoverableDecision
│   ├── generators/               # Layer 2 (+ plan/ + note/)
│   ├── render/                   # Layer 5
│   ├── verify/                   # Layer 6
│   └── conductor/                # Orchestration
├── src/cli/                      # Click CLI
├── .claude/                      # Commands, agents, guides, skills
├── specs/                        # Templates + projects
├── tests/                        # ~486 tests
├── tools/                        # Architecture lint, matrix check
└── docs/ + development/          # Documentation
```

---

## 12. Quick Start

```bash
git clone <yao-repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Create and generate
yao new-project my-first-song
yao conduct "a calm piano piece in D minor, 90 seconds"

# Or from a spec
yao compose specs/templates/minimal.yaml
```

---

## 13. Ethics & Licensing

- References must be rights-cleared (`references/catalog.yaml` enforces `rights_status`)
- No artist-name imitation (schema rejects identifying references)
- Output rights belong to the user
- Every output includes `provenance.json` for transparency
- License: MIT

---

## 14. Document Roles

| Document | Role | Forbidden content |
|---|---|---|
| `README.md` | User guide and quick start | Deep internals |
| `PROJECT.md` (this) | Current state + Capability Matrix | Aspirational claims not in matrix |
| `VISION.md` | Target architecture | Claims about current state |
| `CLAUDE.md` | Development rules | Re-explanation of principles |
| Capability Matrix | Authoritative feature status | Aspirational entries |

---

## 15. Strategic Direction

### Dual Value Proposition

YaO serves two audiences:

- **For musicians**: "Turn your musical ideas into MIDI scores in minutes. Describe what you want, iterate until it sounds right, and understand every decision the system made."
- **For developers**: "A reference architecture for building domain-specific AI agent environments — with music as the proving ground. Provenance, structured critique, evaluate-adapt-regenerate loops, and capability matrix discipline, all demonstrated in a working system."

### Implementation Priorities

**Completed:**
- PROJECT.md split into current-state + VISION.md
- CLAUDE.md rewritten with phase-gated rules and status tags
- Gallery with pre-generated examples
- 5-minute contribution guide
- Stochastic generator improvements (contours, voicings)
- User-facing quality score (1-10)
- Magic number extraction (StochasticConfig)
- Rhythm evaluation metrics

**Next (medium-term):**

| Priority | Action | Impact |
|----------|--------|--------|
| 1 | Implement Perception Stage 1 (audio feature extraction with librosa) | Improves every piece generated |
| 2 | Real multi-agent orchestration in Python (not just prompt templates) | Makes the Orchestra metaphor real |
| 3 | Extract domain-agnostic patterns into documented architecture guide | 10x impact multiplier for the AI agent community |
| 4 | YAML-based plugin system for musical content (scales, chords, rhythms) | Lets musicians contribute without writing Python |
| 5 | Generation progress callbacks for real-time feedback | Better CLI/Claude Code UX |

**Long-term:**

| Priority | Action | Impact |
|----------|--------|--------|
| 6 | Complete Phase beta MPIR (motif/phrase/drums/arrangement plans) | Enables rich critique and multi-candidate generation |
| 7 | Implement Arrangement Engine | Unique capability — transform existing MIDI under preservation contracts |
| 8 | Build a second domain proof-of-concept using YaO patterns | Proves framework transferability |

### Transferable Patterns

YaO contains patterns valuable far beyond music:

| Pattern | Module | Applicability |
|---------|--------|---------------|
| Spec → IR → Output pipeline | schema/ → ir/ → render/ | Any structured generation |
| Append-only provenance | reflect/provenance.py | Any explainable AI system |
| MetricGoal typed evaluation | verify/metric_goal.py | Any quality gate |
| RecoverableDecision | reflect/recoverable.py | Any system with graceful degradation |
| Evaluate-adapt-regenerate loop | conductor/ | Any iterative generation |
| Capability Matrix discipline | PROJECT.md §3 | Any project with aspirational scope |
| Adversarial critique with Findings | verify/critique/ (planned) | Any system needing structured feedback |

### Success Metrics

| Metric | Current | Target (3 months) |
|--------|---------|-------------------|
| Time from install to first MIDI | ~10 min | < 3 min |
| Tests | 492 | 550+ |
| Generator strategies | 2 | 4 |
| Melodic contour algorithms | 4 | 8 |
| Chord voicing strategies | 5 | 5+ |
| Documents for new contributors | ~10 | 3 (README, CLAUDE.md, CONTRIBUTING.md) |

---

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*

---

*Project: You and Orchestra (YaO)*
*PROJECT.md version: 3.1*
*Last revised: 2026-04-30*
