# PROJECT.md — You and Orchestra (YaO) v2.0

> *An agentic music production environment built on Claude Code.*
> *Where you are the conductor, and the AI is your orchestra.*
>
> **This is the v2.0 design.** It supersedes v1.0 by integrating the genre-diversity
> and musical-quality improvements specified in `IMPROVEMENT.md`.

---

## Table of Contents

0. [The Essence of YaO](#0-the-essence-of-yao)
1. [The Conductor Metaphor](#1-the-conductor-metaphor)
2. [Design Principles](#2-design-principles)
3. [Architecture: The 7-Layer Model (v2)](#3-architecture-the-7-layer-model-v2)
4. [Directory Structure](#4-directory-structure)
5. [Orchestra: Subagent Design (v2)](#5-orchestra-subagent-design-v2)
6. [The 6-Phase Cognitive Protocol (Now Executable)](#6-the-6-phase-cognitive-protocol-now-executable)
7. [Specification Language (v2)](#7-specification-language-v2)
8. [Custom Commands](#8-custom-commands)
9. [Skills as Genre Knowledge](#9-skills-as-genre-knowledge)
10. [Hooks](#10-hooks)
11. [MCP Integration](#11-mcp-integration)
12. [Quality Assurance: Multi-Layered Evaluation](#12-quality-assurance-multi-layered-evaluation)
13. [Roadmap (v2)](#13-roadmap-v2)
14. [Quick Start](#14-quick-start)
15. [File Formats and Interoperability](#15-file-formats-and-interoperability)
16. [Ethics and Licensing](#16-ethics-and-licensing)
17. [Document Relationships](#17-document-relationships)
18. [Future Architectural Extensions](#18-future-architectural-extensions)
19. [Glossary](#19-glossary)
20. [Closing](#20-closing)

---

## 0. The Essence of YaO

**You and Orchestra (YaO)** is an agentic music production environment built on Claude Code. Unlike "AI music tools" that emit music from a black box, YaO is structured as a **division of labor among AI subagents (Orchestra Members), conducted by you (the human Conductor).**

All design in YaO derives from one proposition:

> **Music creation is not a one-shot, sensory act. It is a reproducible, improvable engineering process.**

YaO therefore treats music as **code, specifications, tests, diffs, and provenance** *before* it ever becomes audio. This is the **Music-as-Code** philosophy.

### What v2 Adds Over v1

v1.0 established the symbolic foundation: 7-layer architecture, IR, generators, MIDI rendering, evaluation, provenance, and a Conductor feedback loop. v2.0 builds on that foundation with five new commitments:

1. **Rich musical expression** (Layer 1/3): Phrase IR, Motif Networks, articulation, expression, micro-timing.
2. **Genre diversity as a first-class concept** (Layer 2/3): pluggable melody strategies, groove templates, tonal/rhythm system abstractions, structured genre Skills.
3. **Aesthetic judgment is real** (Layer 4 *implemented*): reference library, style vectors, psych-mapping, mood profiles.
4. **Genre-aware evaluation** (Layer 6): different genres, different success criteria.
5. **Multi-agent coordination is live** (across the stack): the 6-phase cognitive protocol becomes executable code; Producer arbitration becomes runtime, not documentation.

The 5 design principles, the 7-layer boundary discipline, and the Music-as-Code ethos are unchanged.

---

## 1. The Conductor Metaphor

YaO concepts map to an orchestra. Internalizing this mapping is the shortest path to using YaO correctly.

| YaO concept | Orchestra metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human project owner |
| **Score** | Sheet music | YAML specifications under `specs/` |
| **Orchestra Members** | Players | Subagents (Composer, Critic, Theorist, etc.) |
| **Concertmaster** | Lead violinist | Producer Subagent (final arbiter) |
| **Rehearsal** | Practice run | The generate → evaluate → adapt → regenerate loop |
| **Library** | Sheet-music archive | `references/` — license-cleared corpus |
| **Style Cards** | Genre-specific tradition guides | `.claude/skills/genres/` |
| **Performance** | Live concert | Rendered final audio |
| **Recording** | Master tape | `outputs/` artifacts |
| **Critic** | Reviewer | Adversarial Critic Subagent + Programmatic Critic |
| **Tempo Sketch** | Pacing diagram | Trajectory curves (tension/density/etc.) |

The Conductor does not write every note. The Conductor's job is to **clarify intent, set direction, judge during rehearsal, and own the quality of the performance**. YaO ports this division to AI.

---

## 2. Design Principles

These five principles are immutable. Every implementation decision must be justifiable against them.

### Principle 1: Agent = Environment, not Composer
YaO accelerates human creativity by 10x; it does not replace it. Generation is one of YaO's affordances, not its purpose.

### Principle 2: Every Decision Is Explainable
Every note, every chord choice, every instrument selection has a Provenance entry. There are no decisions YaO cannot account for.

### Principle 3: Constraints Liberate
Specs, references, negative space, and theory rules are scaffolds, not cages. Unconstrained freedom produces paralysis.

### Principle 4: Time-Axis First
Trajectory curves (tension, density, valence, predictability) are designed *before* notes. Notes fill in the curves' implications.

### Principle 5: The Human Ear Is the Final Truth
Automated metrics inform; humans decide. v2 makes this principle operational with the Human Feedback Logger.

### v2 Corollaries

These follow logically from the principles but are made explicit for v2:

- **Corollary 4a (Aesthetic Anchoring)**: Aesthetic judgment must be grounded in references and empirical psychology, not in metrics alone.
- **Corollary 5a (No Goodhart)**: For every metric that drives generation, an orthogonal metric or human signal must check it.
- **Corollary 1a (Genre Pluralism)**: No genre is privileged. Western pop is one tradition among many; the system must not penalize others for being themselves.

---

## 3. Architecture: The 7-Layer Model (v2)

YaO is partitioned into 7 layers with strict downward-only dependencies. The architecture v1 introduced is preserved; v2 fills in Layer 4 (previously empty) and enriches Layers 2, 3, and 6.

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                                  │
│   Provenance graph, style-profile learning, feedback ingestion  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                                │
│   Music lint • Genre-aware evaluator • Programmatic critic      │
│   Loopability validator • Score diff • Constraint checker       │
├─────────────────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                              │
│   MIDI writer • SoundFont renderer • Optional VST host          │
│   Mix engine • Master engine • Stems • Live preview server      │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute    ← NEW (v2)                    │
│   Reference matcher • Style vector • Psych mapper               │
│   Mood profile • Aesthetic report                               │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)                       │
│   ScoreIR • Note (with Articulation/Expression) • Phrase        │
│   Motif Network • Voicing • Harmony                             │
│   Tonal System • Rhythm System • Groove Template • Vocal IR     │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                                    │
│   Rule-based • Stochastic • Pipeline (6-phase)                  │
│   AI-Seed • Constraint-Solver • Markov                          │
│   MelodyStrategy plugins (chord_tone, bebop, pentatonic, modal,│
│   riff_based, ambient_drone, melismatic)                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: Specification                                          │
│   YAML schemas • Pydantic models • Sketch-to-Spec dialogue      │
└─────────────────────────────────────────────────────────────────┘
       Layer 0 (Constants): instrument ranges, scales, chords,
       MIDI maps, dynamics, groove constants, mood lexicons
```

### Strict Dependency Rules

- A layer may depend on layers strictly below it. Sideways and upward dependencies are forbidden.
- The AST-based linter (`tools/architecture_lint.py`) enforces these boundaries at CI time.
- New modules are placed by answering "What does this code do?" against the discriminator questions in CLAUDE.md.

### What Each Layer Owns in v2

- **Layer 4 (Perception Substitute, new)** owns the question: *"Would a human find this aesthetically convincing?"* Reference matching, psych mapping, and mood profiling all live here. Layer 4 is the answer to "AI cannot listen."
- **Layer 6 (Verify, expanded)** now owns *both* programmatic critique (no LLM, fast, CI-suitable) and orchestration of the LLM-based Adversarial Critic Subagent (deeper, slower, pre-finalization).
- **Layer 2 (Generation, expanded)** holds **plug-and-play strategies**, not a single algorithm. The Pipeline generator orchestrates the 6-phase protocol; AI-Seed delegates motif generation to an LLM; Constraint-Solver uses CP-SAT.

---

## 4. Directory Structure

```
yao/
├── CLAUDE.md                        # Agent rules
├── PROJECT.md                       # This file
├── README.md                        # User quickstart
├── IMPROVEMENT.md                   # Live tracking of v2 improvements
├── pyproject.toml
├── Makefile
│
├── .claude/
│   ├── commands/                    # Custom slash commands
│   │   ├── compose.md
│   │   ├── arrange.md
│   │   ├── critique.md
│   │   ├── morph.md
│   │   ├── improvise.md
│   │   ├── explain.md
│   │   ├── regenerate-section.md
│   │   ├── sketch.md
│   │   └── render.md
│   ├── agents/                      # Subagent definitions
│   │   ├── producer.md
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   └── mix-engineer.md
│   ├── skills/                      # Domain knowledge modules
│   │   ├── genres/                  # Tier-1/2/3 genre Skills
│   │   ├── theory/
│   │   ├── instruments/
│   │   └── psychology/
│   ├── guides/                      # Developer guides (cross-cuts)
│   │   ├── architecture.md
│   │   ├── coding-conventions.md
│   │   ├── music-engineering.md
│   │   ├── testing.md
│   │   └── workflow.md
│   └── hooks/                       # Forced-execution scripts
│       ├── pre-commit-lint.sh
│       ├── post-generate-render.sh
│       ├── post-generate-critique.sh
│       └── update-provenance.sh
│
├── specs/
│   ├── projects/                    # User compositions
│   ├── templates/                   # Reusable spec scaffolds
│   └── fragments/                   # Reusable spec fragments (v2 §18.4)
│
├── src/
│   ├── yao/
│   │   ├── constants/               # Layer 0
│   │   │   ├── instruments.py
│   │   │   ├── scales.py
│   │   │   ├── chords.py
│   │   │   ├── dynamics.py
│   │   │   └── grooves.py           # NEW — built-in GrooveTemplates
│   │   ├── schema/                  # Layer 1: Pydantic
│   │   ├── ir/                      # Layer 3
│   │   │   ├── note.py
│   │   │   ├── score_ir.py
│   │   │   ├── harmony.py
│   │   │   ├── voicing.py
│   │   │   ├── motif.py
│   │   │   ├── timing.py
│   │   │   ├── notation.py
│   │   │   ├── phrase.py            # NEW (A1)
│   │   │   ├── groove.py            # NEW (A4)
│   │   │   ├── tonal_system.py      # NEW (B3)
│   │   │   ├── rhythm_system.py     # NEW (B4)
│   │   │   └── vocal.py             # NEW (F6)
│   │   ├── generators/              # Layer 2
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── rule_based.py
│   │   │   ├── stochastic.py
│   │   │   ├── pipeline.py          # NEW (E1) — 6-phase orchestrator
│   │   │   ├── ai_seed.py           # NEW (F2)
│   │   │   ├── constraint_solver.py # NEW (F3)
│   │   │   ├── producer.py          # NEW (E3)
│   │   │   └── melody/              # NEW (A3) — pluggable strategies
│   │   │       ├── base.py
│   │   │       ├── chord_tone.py
│   │   │       ├── bebop.py
│   │   │       ├── pentatonic.py
│   │   │       ├── modal.py
│   │   │       ├── riff_based.py
│   │   │       ├── ambient_drone.py
│   │   │       └── melismatic.py
│   │   ├── perception/              # Layer 4 — NEW
│   │   │   ├── reference_matcher.py # (C1)
│   │   │   ├── style_vector.py      # (C2)
│   │   │   ├── psych_mapper.py      # (C3)
│   │   │   ├── mood.py              # (D2)
│   │   │   └── aesthetic.py         # (C4)
│   │   ├── render/                  # Layer 5
│   │   │   ├── midi_writer.py
│   │   │   ├── audio_renderer.py
│   │   │   ├── stem_export.py
│   │   │   ├── iteration_mgr.py
│   │   │   ├── vst_host.py          # NEW (F8)
│   │   │   ├── mix_engine.py        # NEW (F8)
│   │   │   ├── master_engine.py     # NEW (F8)
│   │   │   └── live_preview.py      # NEW (F4)
│   │   ├── verify/                  # Layer 6
│   │   │   ├── lint.py
│   │   │   ├── analyzer.py
│   │   │   ├── evaluator.py         # → genre-aware (D1)
│   │   │   ├── diff.py
│   │   │   ├── constraints.py
│   │   │   ├── critic.py            # NEW (E2) — programmatic critic
│   │   │   └── loopability.py       # NEW (F5)
│   │   ├── reflect/                 # Layer 7
│   │   │   ├── provenance.py
│   │   │   ├── feedback_logger.py   # NEW (D3)
│   │   │   └── style_profile.py     # NEW (Phase 6)
│   │   ├── arrangement/             # NEW (F1) — top-level package
│   │   │   ├── engine.py
│   │   │   ├── reharmonize.py
│   │   │   ├── regroove.py
│   │   │   ├── reorchestrate.py
│   │   │   └── restyle.py
│   │   ├── conductor/               # Auto-iteration
│   │   │   ├── conductor.py
│   │   │   ├── feedback.py
│   │   │   └── result.py
│   │   ├── errors.py
│   │   └── types.py
│   └── cli/
│       └── main.py
│
├── references/
│   ├── catalog.yaml                 # license-verified
│   ├── midi/
│   ├── musicxml/
│   └── extracted_features/
│
├── outputs/
│   └── projects/<name>/iterations/v<NNN>/
│       ├── full.mid
│       ├── stems/
│       ├── audio.wav
│       ├── analysis.json
│       ├── evaluation.json
│       ├── aesthetic_report.json    # NEW
│       ├── critique.md
│       ├── provenance.json
│       └── human_feedback.jsonl     # NEW
│
├── soundfonts/
├── plugins/                         # NEW — VST3 collection (gitignored, local only)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── music_constraints/
│   ├── scenarios/
│   ├── perception/                  # NEW (v2)
│   └── golden/
├── tools/
│   ├── architecture_lint.py
│   └── validate_references.py       # NEW (C1)
└── docs/
    ├── design/
    ├── tutorials/
    └── glossary.md
```

---

## 5. Orchestra: Subagent Design (v2)

In v2, Subagent definitions in `.claude/agents/` are **executable**, not just descriptive. The Pipeline generator (Layer 2) instantiates each as a programmatic role with specific tool permissions and concrete outputs.

### 5.1 Composer
- **Owns**: melodies, motifs, themes, structural skeletons.
- **Reads**: `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`, the chosen MelodyStrategy plugin.
- **Emits**: `tuple[Phrase, ...]` per part, with `MotifNetwork` annotations.
- **Forbidden**: instrument selection, final voicing.
- **Evaluation**: motif memorability, repetition/variation balance, trajectory-fit, phrase coherence.

### 5.2 Harmony Theorist
- **Owns**: chord progressions, modulations, cadences, reharmonization.
- **Reads**: Composer's melodic skeleton, `composition.yaml` `harmony` block, the active TonalSystem.
- **Emits**: `ChordProgression` (Roman numerals + voicing candidates).
- **Evaluation**: functional integrity, tension/resolution balance, genre-typical vocabulary.

### 5.3 Rhythm Architect
- **Owns**: drums, grooves, syncopation, fills, micro-timing.
- **Reads**: `composition.yaml` `rhythm` block, the active RhythmSystem and GrooveTemplate.
- **Emits**: rhythmic placement for all parts; drum patterns; per-section accent maps.
- **Evaluation**: groove feel, humanization quality, section contrast.

### 5.4 Orchestrator
- **Owns**: instrument assignments, voicings, register placement, countermelodies.
- **Reads**: outputs of Composer / Harmony Theorist / Rhythm Architect; genre Skill `instrumentation`.
- **Emits**: complete `ScoreIR` with idiomatic per-instrument writing.
- **Evaluation**: frequency-space conflict avoidance, idiomatic instrument writing, texture density.

### 5.5 Adversarial Critic
- **Owns**: weakness detection. **Never praises.**
- **Reads**: any intermediate or final ScoreIR.
- **Emits**: `critique.md` with severity-rated issue list.
- **Evaluation**: comprehensiveness and specificity of weaknesses found.
- **v2 addition**: works alongside the **Programmatic Critic** (`src/yao/verify/critic.py`). Programmatic Critic runs in milliseconds and gates candidates; LLM-based Adversarial Critic runs at finalization for depth.

### 5.6 Mix Engineer
- **Owns**: stereo placement, dynamics, frequency masking, loudness (LUFS).
- **Reads**: Orchestrator output + `production.yaml` + genre Skill `mix_aesthetics`.
- **Emits**: mix-engine instructions (per-track EQ/compression/reverb/pan) → consumed by `render/mix_engine.py`.
- **Evaluation**: LUFS target met, frequency balance, stereo width.

### 5.7 Producer
- **Owns**: integration, prioritization, dialogue with the human Conductor, final calls.
- **Reads**: outputs from all subagents, all critic reports, human feedback.
- **Emits**: final production decisions, regeneration directives, provenance entries explaining each.
- **Privilege**: the **only** subagent allowed to override another subagent's output.
- **Evaluation**: fidelity of final score to `intent.md`.

---

## 6. The 6-Phase Cognitive Protocol (Now Executable)

The 6-phase cognitive protocol described in v1 is now **runnable code** in v2. The `pipeline` generator strategy (`src/yao/generators/pipeline.py`) executes the phases in order, recording each phase boundary in Provenance.

```
Phase 1: Intent Crystallization
  ↓ Read intent.md; verify it is unambiguous; record into Provenance
Phase 2: Architectural Sketch
  ↓ Compute trajectory curves first; no notes yet
Phase 3: Skeletal Generation (multi-candidate)
  ↓ Composer produces 5–10 60%-complete skeletons
Phase 4: Critic-Composer Dialogue
  ↓ Programmatic Critic scores all candidates; Producer picks/merges
Phase 5: Detailed Filling
  ↓ Harmony Theorist → Rhythm Architect → Orchestrator fill the winner
Phase 6: Listening Simulation
  ↓ Perception Substitute Layer evaluates aesthetics
  ↓ If aesthetic_score < threshold: regenerate weakest section
```

### Phase boundaries in code

```python
class PipelineGenerator(GeneratorBase):
    def generate(self) -> tuple[ScoreIR, ProvenanceLog]:
        log = ProvenanceLog()

        log.record_phase("intent_crystallization", intent=self.spec.intent)
        trajectory = self._sketch_trajectory()
        log.record_phase("architectural_sketch", trajectory=trajectory)

        candidates = [self._skeleton(trajectory, seed_offset=k)
                      for k in range(self.candidate_count)]
        log.record_phase("skeletal_generation", count=len(candidates))

        winner = self._critic_dialogue(candidates, log)
        with_harmony  = self.harmony_theorist.fill(winner)
        with_rhythm   = self.rhythm_architect.fill(with_harmony)
        orchestrated  = self.orchestrator.fill(with_rhythm)
        log.record_phase("detailed_filling", instruments=orchestrated.instruments)

        aesthetic = self.perception.evaluate(orchestrated)
        if aesthetic.overall_score < self.spec.thresholds.aesthetic_min:
            orchestrated = self._regen_weakest(orchestrated, aesthetic)
        log.record_phase("listening_simulation",
                         aesthetic_score=aesthetic.overall_score)
        return orchestrated, log
```

The Conductor's outer loop (already in v1: generate → evaluate → adapt) wraps Pipeline. Each invocation of Pipeline is one inner pass; the Conductor's adaptation drives outer iterations.

---

## 7. Specification Language (v2)

YaO describes a piece using a small set of YAML files plus auto-generated artifacts. v2 adds new schemas and extends existing ones.

### 7.1 `intent.md` (natural language)
1–3 sentences fixing the piece's essence. Final ground for every decision.

### 7.2 `composition.yaml` (extended)

```yaml
title: ...
identity:
  purpose: ...
  duration_sec: 90
  loopable: true

key: D minor
tempo_bpm: 92
time_signature:
  primary: "6/8"
  groupings: [3, 3]
  polymeter: []
  polyrhythm: []

tonal_system: common_practice    # NEW (B3)
rhythm_system: western_meter     # NEW (B4)
melody_strategy: chord_tone      # NEW (A3) — selects melody plugin

genre:                           # NEW (B2) — blended genres allowed
  primary: { name: cinematic, weight: 0.7 }
  blends:
    - { name: neoclassical, weight: 0.3, blend_aspects: [harmony, instrumentation] }

groove: orchestral_rubato        # NEW (A4)

instruments:
  - { name: violin, role: melody, articulations_allowed: [legato, staccato, marcato] }
  - { name: cello,  role: bass,   articulations_allowed: [legato, pizzicato] }

sections:
  - { name: intro,  bars: 4,  dynamics: pp }
  - { name: verse,  bars: 8,  dynamics: mp }
  - { name: chorus, bars: 8,  dynamics: f  }
  - { name: outro,  bars: 4,  dynamics: pp }

generation:
  strategy: pipeline             # NEW — selects v2 multi-stage generator
  candidate_count: 5
  seed: 42

target_mood:                     # NEW (D2)
  arousal: 0.55
  valence: -0.20
  tension: 0.45
  intimacy: 0.65
  grandeur: 0.40
  nostalgia: 0.55

thresholds:
  aesthetic_min: 0.70
  predictability_max: 0.85
```

### 7.3 `trajectory.yaml`
Time-axis curves for `tension`, `density`, `valence`, `predictability`. Three curve types: `bezier`, `stepped`, `linear`. Unchanged from v1 except all four dimensions are now mandatory.

### 7.4 `references.yaml` (newly active)

```yaml
positive:
  - { id: ref_007, weight: 0.6, extract: [harmony, motif] }
  - { id: ref_012, weight: 0.3, extract: [groove, mix] }
negative:
  - { id: ref_092, anti_weight: 0.5, avoid: [predictable_progression] }
```

References point to entries in `references/catalog.yaml` (license-cleared).

### 7.5 `negative-space.yaml`
Silence design: required rests, frequency reservations, drop sections.

### 7.6 `arrangement.yaml` (used by `/arrange`)

```yaml
input:
  source_file: inputs/source.mid
  rights_status: owned
preserve: [melody, song_form]
transform:
  target_style: lo-fi-hiphop
  preserve_aspects: [melody]
  intensity: 0.7
avoid: [overcrowded_arrangement, melody_range_change]
```

### 7.7 `production.yaml`

```yaml
target_lufs: -16
stereo_width: 0.7
master_chain: lo-fi-hiphop_default      # references genre Skill preset
stems_export: true
```

### 7.8 `provenance.json` (auto-generated, append-only)
Every generation decision recorded with timestamp, parameters, and rationale. v2 expands to record phase boundaries (§6) and Subagent attributions.

### 7.9 `human_feedback.jsonl` (newly active, append-only)
Per-iteration tagged feedback from the human Conductor. Read by the Conductor's adaptation logic.

---

## 8. Custom Commands

| Command | Purpose | Phase 6 wired? | Subagents involved |
|---|---|---|---|
| `/sketch` | Sketch → Spec dialogue | n/a | Producer |
| `/compose <project>` | Compose from spec via Pipeline | yes | All |
| `/arrange <project>` | Transform via Arrangement Engine | yes | Orchestrator + Adversarial Critic |
| `/critique <iteration>` | Run LLM-based Adversarial Critic | n/a | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section | yes | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate two style profiles | yes | Composer + Orchestrator |
| `/improvise <input>` | Real-time accompaniment (Phase 5+) | n/a | Composer + Rhythm Architect |
| `/explain <element>` | Trace a decision via Provenance | n/a | Producer |
| `/diff <iter_a> <iter_b>` | Musical diff between iterations | n/a | Verify |
| `/render <iteration>` | MIDI → audio + score | n/a | Mix Engineer |
| `/feedback <project> <iter>` | Record human listening feedback | n/a | Reflection layer |

---

## 9. Skills as Genre Knowledge

`.claude/skills/` is the contributor surface for non-engineers. Genre Skills are Markdown files with a structured front-matter block (machine-readable) and a free-form body (human-readable).

### 9.1 Genre Skill Tiering

- **Tier 1 (10 must-have)**: cinematic ✅, orchestral classical, jazz, pop, rock, hiphop, electronic dance, ambient, folk, bossa nova / latin.
- **Tier 2 (10 extended)**: lo-fi hiphop, neoclassical, metal, R&B, blues, country, game BGM, anime / J-pop, reggae, funk.
- **Tier 3 (8+ global / specialist)**: Indian classical, Arabic maqam, West African, East Asian traditional, Klezmer, Flamenco, Tango, Bluegrass.

### 9.2 Required Sections in Each Genre Skill

Identity, Harmony (typical / reharmonization / cliches), Melody (scale, phrase structure, embellishments, range, MelodyStrategy), Rhythm (default GrooveTemplate, subdivisions, syncopation, drum patterns), Instrumentation (core / optional / roles), Form, Mix Aesthetics (stereo, LUFS, EQ curve, FX), References, Adversarial Critic Rules, Compatible Genre Blends.

### 9.3 Theory, Instrument, and Psychology Skills

- **Theory**: voice-leading ✅, reharmonization, counterpoint, modal interchange, secondary dominants, blue-note theory.
- **Instruments**: piano ✅, strings, brass, woodwinds, drums, synths, guitar, vocals — each documenting range, idiomatic playing, articulation defaults, common pitfalls.
- **Psychology**: tension-resolution ✅, emotion-mapping, memorability, expectation (Huron), arousal-valence (Russell, Schubert).

---

## 10. Hooks

Hooks are **forced-execution** scripts. They run regardless of agent intent. v2 keeps the v1 set and adds two.

| Hook | When | Purpose |
|---|---|---|
| `pre-commit-lint` | git commit | music21 lint, schema validation |
| `post-generate-render` | after every `/compose` | auto MIDI→audio + score |
| `post-generate-critique` | after every `/compose` | run Programmatic Critic + (if configured) Adversarial Critic |
| `update-provenance` | after every change | reconcile Provenance graph |
| `validate-references` | weekly + pre-commit | NEW — license-clearance enforcement on `references/` |
| `dogfood-snapshot` | end of each Sprint | NEW — generate Tier-1 dogfood corpus, archive under `outputs/dogfood/sprint-N/` |

---

## 11. MCP Integration

YaO is designed to integrate with MCP servers. Connections are not required to use YaO, but greatly extend capability.

| MCP target | Purpose |
|---|---|
| **DAW (Reaper preferred)** | Project files, track layout, mix automation |
| **Sample libraries** | Drum samples, one-shots, loops |
| **Reference DB** | Searchable catalog of license-cleared MIDI/audio |
| **MIDI controller** | Live improvisation input |
| **SoundFont/VST server** | Audio rendering |
| **Cloud storage** | Output backup, team sharing |
| **LLM APIs** | AI-Seed generator backend |

---

## 12. Quality Assurance: Multi-Layered Evaluation

v2 evaluates output across **three orthogonal axes**, each guarding against the others' failure modes.

### 12.1 Symbolic / Theoretical (Layer 6)
Music lint, voice-leading checks, range conformance, constraint satisfaction. Catches: rule violations.

### 12.2 Genre-Aware Numerical (Layer 6 — D1)
Structure / melody / harmony / acoustics + genre-specific dimensions (`groove_pocket`, `drone_immersion`, `loop_seamlessness`, etc.) weighted by the active genre Skill. Catches: genre mismatch.

### 12.3 Aesthetic / Perceptual (Layer 4 — C1–C4)
Reference matching, style-vector similarity, psych-mapped arousal/valence/tension/memorability/predictability, mood-profile distance. Catches: technically correct but emotionally dead.

### 12.4 Human Feedback (Layer 7 — D3)
Per-iteration tagged listening notes. Catches: everything the metrics missed.

### Failure Mode Matrix

| Failure mode | Symptom | Caught by |
|---|---|---|
| Formal boredom | Rule-compliant, predictable | C3 (predictability), Programmatic Critic, D3 |
| Formal breakdown | Rule violations | Music lint, Programmatic Critic |
| Emotional death | Technically right, unmoving | C2 (reference distance), C3 (memorability), D3 |
| Cliché contamination | Overly familiar | Programmatic Critic (cliché patterns), C2 (anti-references) |
| Excessive ornamentation | Cluttered | Genre-aware evaluator (texture cap) |
| Section dis-coherence | Poor transitions | Trajectory match, Loopability |
| Frequency conflict | Mud | Mix Engineer, frequency masking analyzer |

The Conductor's adaptation logic reads from all four axes; no single axis dominates.

---

## 13. Roadmap (v2.1 — updated to reflect implementation progress)

v2 reframes the v1 phase plan. v1 Phase 1 (symbolic foundation) is complete. v2 implementation is ~75% done.

### Phase 2: Genre + Aesthetic — ~80% DONE
- ✅ B1: 22 genre Skills populated (3 Tier-1 still needed: pop, hiphop, orchestral classical; field enrichment needed).
- ⚠️ A3: 8 melody strategies implemented (schema integration pending).
- ✅ A4: 20 GrooveTemplates + GrooveProfile + GrooveApplicator.
- ⚠️ C1: Reference library at 10 entries (target: 20+; tools needed).
- ⚠️ C2: StyleVector implemented (missing arithmetic ops + cosine_similarity).
- ⚠️ C3: PsychMapper emotion→feature done (score→perception direction pending).
- ⚠️ D2: Mood profile partially covered by EmotionSpec; standalone MoodProfile type pending.

### Phase 3: Multi-Agent + Expression — ✅ DONE
- ✅ E1: Performance pipeline + Producer subagent orchestration (5-step).
- ✅ E2: 15+ programmatic critique rules.
- ✅ E3: Producer with conflict arbitration + provenance.
- ✅ A5: Compound meter, polymeter, polyrhythm.
- ✅ A6: Articulation + Expression IR + performance realizers.
- ✅ A1: Phrase IR.
- ⚠️ A2: Motif transforms done, MotifNetwork class pending.

### Phase 4: Practical Usability — ~90% DONE
- ✅ F4: Audition/preview server.
- ✅ D1: Genre-aware evaluator with dynamic weights.
- ❌ F5: Loopability Validator (not started).
- ✅ D3: Human Feedback Logger + Conductor integration.

### Phase 5: Specialty Expansion — ~60% DONE
- ✅ F1: Arrangement engine (5 operations).
- ✅ F3: Constraint solver.
- ❌ F2: AI-Seed Generator (not started).
- ✅ F8: Mix/production chain.
- ❌ B3/B4: TonalSystem/RhythmSystem Protocols (infrastructure exists, formalization pending).
- ❌ F6: Vocal IR (not started).
- ✅ F7: Tuning system.
- ⚠️ B2: Genre blending (partial).
- ✅ C4: Aesthetic report (listening simulator).

### Phase 6: Reflection & Learning (continuous)
- ✅ Style profile learning.
- ✅ Provenance graph.
- Remaining: community reference sharing, IDyOM-class predictive models.

### User-Value Milestones (parallel measurement)

| Milestone | User value | Unblocked by | Status |
|---|---|---|---|
| Describe & Hear | "YAML in, music out" | v1 | ✅ |
| Iterate & Improve | "Tell it what's wrong, it improves" | v1 | ✅ |
| Richer Music | "Pro-quality harmony, rhythm, dynamics" | A1–A6, B1 | ✅ |
| My Style | "Learns my preferences" | C1–C3, D3 | ⚠️ 80% |
| Multi-Genre | "Convincing across diverse genres" | B1–B4, C1–C4, D1 | ⚠️ 70% |
| Production Ready | "Usable in real projects" | F1, F4, F8 | ✅ |
| Stage Ready | "Live performance, real-time" | Phase 5 / `/improvise` | ⚠️ 60% |

---

## 14. Quick Start

```bash
git clone <repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
make all-checks
```

```bash
# 1. Sketch a piece
yao new-project rainy-cafe
claude
> /sketch
> "A 90-second melancholy piano-cello piece for a rainy cafe scene"
> (Producer crystallizes intent and proposes references)

# 2. Compose
> /compose rainy-cafe

# 3. Listen and feed back
afplay outputs/projects/rainy-cafe/iterations/v001/audio.wav
yao feedback rainy-cafe v001 --section chorus --bars 17-24 --tag "boring" --severity 0.6

# 4. Conductor adapts
> /compose rainy-cafe        # creates v002 incorporating feedback

# 5. Critique
> /critique rainy-cafe v002

# 6. Regenerate weak parts
> /regenerate-section rainy-cafe bridge

# 7. Arrange to a different genre
> /arrange rainy-cafe --target lo-fi-hiphop --preserve melody
```

---

## 15. File Formats and Interoperability

| Use | Format | Why |
|---|---|---|
| Symbolic music | MIDI (.mid), MusicXML (.xml) | Industry standard |
| Score | LilyPond (.ly), PDF | High quality |
| Specs | YAML | Human + git friendly |
| IR | JSON | Programmatic, schema-validated |
| Provenance | JSON | Graph-friendly |
| Feedback | JSONL | Append-only |
| Audio (production) | WAV (24-bit) | Lossless |
| Audio (delivery) | FLAC, MP3 | Standard |
| Live patterns | Strudel pattern strings | Browser playback |
| Microtonal | MTS sysex / MPE | Standard for non-12-TET |

YaO does not invent new formats unless none of the above can express what is needed.

---

## 16. Ethics and Licensing

### 16.1 Reference Library
Only `public_domain`, `owned`, or permissive Creative Commons (`cc_by`, `cc_by_sa`) entries allowed in `references/catalog.yaml`. The `validate-references` hook enforces this in CI.

### 16.2 Artist Imitation
Naming a living artist as a reference is **discouraged**. Prefer abstract feature descriptions:
- ✗ "Joe Hisaishi style"
- ✓ "Wide open string voicings, ascending stepwise motifs, modal mixture, contemplative tempo"

### 16.3 Output Rights
Generated works belong to the user by default. If reference influence on a piece exceeds an internal threshold (cosine similarity > 0.9 in style space), the system warns and records the warning in Provenance.

### 16.4 Transparency
Every generated work has a Provenance entry listing the references that influenced it. We recommend disclosing "made with YaO" alongside output.

---

## 17. Document Relationships

| File | Audience | Content |
|---|---|---|
| `PROJECT.md` (this) | Humans + agents | Full design, philosophy, architecture |
| `CLAUDE.md` | Agents primarily | Inviolable rules, prohibitions, Skill pointers |
| `README.md` | Humans primarily | Quickstart, minimal usage |
| `IMPROVEMENT.md` | Both | v2 improvement tracking, acceptance criteria |
| `.claude/guides/*.md` | Both | Cross-cutting developer guidance |
| `docs/design/*.md` | Both | Per-decision design records (ADR-style) |

---

## 18. Future Architectural Extensions

### 18.1 Project Runtime (Stateful Sessions)
The current CLI is stateless. A `ProjectRuntime` will provide section-level generation cache, feedback queue, undo/redo at the musical level.

### 18.2 Abstract Agent Protocol
Subagent definitions in `.claude/agents/` are coupled to Claude Code. We will define a backend-agnostic Python protocol (`AgentRole`, `AgentContext`, `AgentOutput`) so other LLM providers can plug in.

### 18.3 Immediate Feedback Path
The YAML → MIDI → WAV → external player path is too slow. F4 (Live Preview Server) is the first step. Future steps: in-browser preview via Strudel, direct WAV playback via `sounddevice`.

### 18.4 Spec Composability
`specs/fragments/` will hold reusable spec snippets, with `extends:` / `overrides:` keywords to compose them.

### 18.5 Adaptive / Interactive Music
For game audio, an `adaptive:` spec block defines named states (e.g., `explore`, `combat`) and inter-state transitions (`stinger_then_crossfade`, etc.). Output becomes a Wwise/FMOD-compatible state machine.

### 18.6 Style Profile Per User
Phase 6 introduces persistent user preferences derived from feedback history. Style profiles are versioned per project owner under `~/.yao/profiles/`.

---

## 19. Glossary

- **Aesthetic Score** — Overall score from Layer 4, blending reference and psych metrics.
- **Aesthetic Reference Library** — License-cleared corpus serving as taste anchors.
- **Articulation** — Note-level performance attribute (legato, staccato, ghost, etc.).
- **Conductor (capital C)** — The human project owner; final decision-maker.
- **Conductor (lowercase, the engine)** — The generate/evaluate/adapt loop, separate from the human Conductor.
- **GrooveTemplate** — Reusable micro-timing + velocity pattern.
- **Iteration** — Versioned generation under one project (`v001`, `v002`, …).
- **Motif Network** — Tree of motif derivatives, tracking all transformations.
- **Music Lint** — Theory-based automated rule check.
- **Negative Space** — The intentional absence of sound; required rests and gaps.
- **Orchestra** — Collective name for Subagents.
- **Perception Substitute Layer** — Layer 4; replaces the missing AI ear with reference + psych machinery.
- **Phrase** — A musical sentence with role (antecedent/consequent/free), motif lineage, and cadence target.
- **Pipeline (the generator)** — Layer-2 generator that runs the 6-phase protocol.
- **Programmatic Critic** — Rule-based, fast critic in Layer 6.
- **Provenance** — Append-only record of every generation decision and rationale.
- **Score (capital S)** — The full set of YAML specs for a piece.
- **Score IR** — Internal representation Layer 3 emits.
- **Sketch-to-Spec** — Conversational mode converting natural language into YAML specs.
- **Style Vector** — High-dimensional feature vector representing a style; supports arithmetic.
- **Subagent** — A specialized AI role (Composer, Critic, etc.); see §5.
- **Tonal System** — Pluggable abstraction of pitch organization (common-practice, modal, raga, maqam, …).
- **Trajectory** — Time-axis curve for tension, density, valence, predictability.

---

## 20. Closing

YaO v2 is not "AI that makes music." It is the structured environment in which a human Conductor and a disciplined AI Orchestra co-create music — faster, deeper, and far more reproducibly than either could alone.

- The **human** brings intent, taste, and final judgment.
- The **AI Orchestra** brings theory mastery, iteration speed, exhaustive memory, and patient critique.
- **YaO** is the place where these two strengths combine without either dominating.

Great music remains the expression of a human soul. YaO's job is to make that expression **faster, deeper, and more reproducible**. Nothing more, nothing less.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Last updated: 2026-05-05*
*Supersedes: v1.0 (2026-04-27)*
