# PROJECT.md — You and Orchestra (YaO)

> *An agentic music production environment built on Claude Code.*
> *You are the conductor; the AI is your orchestra.*
> *Music as Code. Reproducible. Auditable. Iterable. Multi-genre.*

---

## 0. The Essence of YaO

**You and Orchestra (YaO)** is an agentic music production environment that runs on top of Claude Code. Unlike conventional "AI music tools" that emit music from a single black box, YaO is structured as **a coordinated team of specialized AI subagents (the Orchestra Members), directed by a human (You = the Conductor)**.

Every architectural choice in YaO descends from one proposition:

> **Music production is not a one-off, intuitive act. It is a reproducible, improvable creative-engineering process.**

For this reason, YaO treats music — before it is sound — as **code, specifications, tests, diffs, and provenance**. We call this the **Music-as-Code** philosophy.

This document, version 2.0, extends the original YaO architecture with **first-class support for diverse music genres**. The single most important architectural addition since 1.0 is the introduction of the **Genre System**: a coordinated set of data structures, generators, and evaluators that allow YaO to produce credible output across at least 20 distinct genres including pop, rock, jazz, hip-hop, EDM, blues, funk, R&B, Latin, classical, and electronic subgenres.

---

## 1. The Metaphor: You and Orchestra

Every concept in YaO maps to a corresponding role in a real orchestra. Internalizing this mapping is the shortest path to using YaO correctly.

| YaO Component | Orchestra Metaphor | Implementation |
|---|---|---|
| **You** | Conductor | The human project owner |
| **Score** | Sheet music | YAML specs in `specs/` |
| **Orchestra Members** | Players | Each Subagent (Composer, Critic, Theorist, etc.) |
| **Concertmaster** | Lead violinist | Producer Subagent (overall coordination) |
| **Section Leader** | Genre specialist | **Genre Specialist Subagent** (NEW in v2.0) |
| **Rehearsal** | Practice cycle | Generate-evaluate-revise iteration loop |
| **Library** | Score archive | `references/` (with genre-tagged catalog) |
| **Performance** | Live concert | Rendered final audio |
| **Recording** | Studio recording | Files in `outputs/` |
| **Critic / Reviewer** | Music critic | Adversarial Critic Subagent |

The Conductor (you) does not write every note. Your job is to **clarify intent, set direction for the orchestra members, make judgment calls during rehearsal, and ensure the quality of the final performance**. YaO brings this division of labor to AI.

---

## 2. Five Inviolable Design Principles

Every implementation decision in YaO is checked against these five principles. They are also reproduced verbatim in `CLAUDE.md` as the primary judgment criteria for the development agent.

### Principle 1: The Agent Is an Environment, Not a Composer
YaO is "an environment that makes a human composer 10x faster," not "an AI that writes music." Full automation is not the goal; accelerating and extending human creative judgment is.

### Principle 2: Every Decision Must Be Explainable
For every generated note, chord, and arrangement choice, a "why" must be recordable. This becomes a `ProvenanceLog` and is persistent, traceable, reviewable, and revisable.

### Principle 3: Constraints Liberate
Explicit specifications (YAML), reference libraries, negative space declarations, and **genre profiles** are not shackles on creativity but scaffolds for it. Unbounded freedom produces paralysis.

### Principle 4: Time-Axis First, Notes Second
A piece is first sketched as time-axis trajectories (tension, density, valence, predictability) and only then filled with notes. This produces structurally meaningful music.

### Principle 5: The Human Ear Is the Final Truth
No matter how sophisticated the automated metrics become, human auditory experience is the ultimate judge. Agents **assist** judgment; they do not replace it.

---

## 3. Architecture: The 8-Layer Model

YaO is composed of eight clearly separated layers. Each layer has independent input/output contracts and can be swapped or tested in isolation.

```
┌──────────────────────────────────────────────────────┐
│ Layer 7: Reflection & Learning                       │
│   Learn from production history; user-style profiles │
├──────────────────────────────────────────────────────┤
│ Layer 6: Verification & Critique                     │
│   Music lint, evaluation, diff, Genre Conformance    │
├──────────────────────────────────────────────────────┤
│ Layer 5: Rendering                                   │
│   MIDI, audio (FluidSynth + pedalboard), score PDF   │
├──────────────────────────────────────────────────────┤
│ Layer 4: Perception Substitute                       │
│   Reference matching, style vector, psych mapping    │
├──────────────────────────────────────────────────────┤
│ Layer 3: Intermediate Representation (IR)            │
│   ScoreIR, harmony, motif, voicing, timing, groove,  │
│   phrasing, drum pattern                             │
├──────────────────────────────────────────────────────┤
│ Layer 2: Generation Strategy                         │
│   Pluggable generators: rule-based, stochastic,      │
│   drums, markov, constraint solver, AI bridge        │
├──────────────────────────────────────────────────────┤
│ Layer 1: Specification                               │
│   YAML, Pydantic, dialogue, sketch input             │
├──────────────────────────────────────────────────────┤
│ Layer 0: Constants & Genre Definitions               │
│   Instruments, scales, chords, dynamics,             │
│   GenreProfiles, drum kits, grooves                  │
└──────────────────────────────────────────────────────┘
```

Inter-layer dependencies flow strictly upward. Lower-layer changes propagate up; upper layers can change without affecting lower ones. This means, for example, that swapping Layer 2 generators (rule-based → Markov) requires no changes to Layer 1 specifications.

The new addition in v2.0 is making **Layer 0 contain genre definitions**, which then flow up through every layer. This is the foundation of multi-genre support.

---

## 4. The Genre System (v2.0 Centerpiece)

The Genre System is the single most important architectural addition in YaO v2.0. It elevates "genre" from a string label to a first-class data structure that coordinates every layer of the pipeline.

### 4.1 Why a Genre System Was Needed

In v1.0, a user could write `genre: jazz` in `composition.yaml`, but no module interpreted that string into actionable musical decisions. As a result, the system could produce reasonable classical or chamber piano works, but rock had no drums, jazz had no swing, hip-hop had no boom-bap, EDM had no buildup-and-drop. **Every genre limitation traced to a single missing abstraction**: a coordinator that mapped genre semantics into instruments, rhythm, harmony, form, and production.

### 4.2 The GenreProfile Data Structure

The Genre System is centered on the `GenreProfile` frozen dataclass, defined in `src/yao/genre/profile.py`. Each profile captures, in machine-readable form, what a genre *is*: typical tempo range, modes, time signatures, core and forbidden instruments, chord palette extensions, harmonic rhythm, voicing style, swing ratios, drum kit preferences, melodic devices, production targets, and anti-cliché rules. Profiles also support **inheritance** (e.g., `bebop` inherits from `jazz` and overrides specific fields), enabling a hierarchy of related genres.

Profiles are authored as YAML files in `src/yao/genre/profiles/<name>.yaml`, validated through Pydantic, and consumed by every layer that needs to make genre-aware decisions. Non-developers can contribute new genres without writing Python.

### 4.3 Initial Genre Catalog

The launch catalog covers 20 genres organized by family:

| Family | Genres |
|---|---|
| Popular | Pop, Rock, Hard Rock, Funk, R&B, Hip-Hop, Lo-fi Hip-Hop |
| Jazz | Swing Jazz, Bebop, Bossa Nova, Modal Jazz, Fusion |
| Electronic | House, Techno, Drum & Bass, Ambient, Synthwave |
| Roots & World | Blues, Latin, Reggae, Celtic |
| Classical/Cinematic | Baroque, Romantic, Impressionist, Cinematic, Minimalist |

Subgenres (e.g., trap inheriting from hip-hop, bossa nova inheriting from latin) are added incrementally by community contribution.

### 4.4 How Genre Flows Through the System

A user request flows through the Genre System as follows:

1. **Spec Layer:** The natural-language parser or YAML spec produces a primary genre (and optional fusion genres with weights).
2. **Genre Specialist Subagent:** Reads the resolved `GenreProfile` and produces a "genre briefing" — a structured summary distributed to all other subagents.
3. **Generation Layer:** Each generator consults the genre briefing to constrain its output. Drum Generator picks a kit and pattern set; Harmony Theorist selects a chord palette and voicing style; Rhythm Architect applies a groove template.
4. **Verification Layer:** The Genre Conformance evaluator scores how well the output matches the genre, and feeds adaptation hints back to the Conductor.
5. **Provenance Layer:** Every genre-driven decision is recorded ("9th chord chosen because GenreProfile.chord_palette_extended includes it for `lo-fi hip-hop`").

The Genre System is **additive**: a user who omits the genre field gets the same v1.0 behavior. There are no breaking changes.

---

## 5. Directory Structure

```
yao/
├── CLAUDE.md                      # Invariant rules for the development agent
├── PROJECT.md                     # This document
├── README.md                      # User-facing quickstart
├── pyproject.toml                 # Python dependencies
├── Makefile                       # Top-level commands
│
├── .claude/
│   ├── commands/                  # Slash commands (/compose, /arrange, ...)
│   ├── agents/                    # Subagent definitions (8 total in v2.0)
│   │   ├── composer.md
│   │   ├── harmony-theorist.md
│   │   ├── rhythm-architect.md
│   │   ├── orchestrator.md
│   │   ├── adversarial-critic.md
│   │   ├── mix-engineer.md
│   │   ├── producer.md
│   │   ├── genre-specialist.md          # NEW in v2.0
│   │   └── reharmonization.md           # NEW in v2.0
│   ├── skills/
│   │   ├── genres/                # ≥20 genre skills
│   │   ├── theory/                # voice-leading, reharmonization, etc.
│   │   ├── instruments/           # per-instrument idiomatic playing
│   │   ├── psychology/            # emotion-mapping, memorability
│   │   ├── grooves/               # NEW: groove-engineering knowledge
│   │   ├── drums/                 # NEW: per-genre drum vocabulary
│   │   └── production/            # NEW: per-genre mix/master practice
│   ├── guides/                    # Internal developer docs
│   │   ├── architecture.md
│   │   ├── coding-conventions.md
│   │   ├── music-engineering.md
│   │   ├── testing.md
│   │   ├── workflow.md
│   │   ├── genre-development.md         # NEW: how to add a genre
│   │   └── drum-pattern-authoring.md    # NEW: how to author drum MIDI
│   └── hooks/                     # Pre-commit, post-generate, etc.
│
├── specs/
│   ├── projects/                  # User compositions
│   │   └── <name>/
│   │       ├── intent.md
│   │       ├── composition.yaml
│   │       ├── trajectory.yaml
│   │       ├── references.yaml
│   │       ├── negative-space.yaml
│   │       ├── arrangement.yaml
│   │       └── production.yaml
│   ├── templates/                 # Compose-from-scratch starters
│   │   ├── bgm-90sec.yaml
│   │   ├── cinematic-3min.yaml
│   │   ├── lofi-hiphop-loop.yaml        # NEW
│   │   ├── rock-anthem-3min.yaml        # NEW
│   │   ├── jazz-trio-4min.yaml          # NEW
│   │   └── edm-drop-90sec.yaml          # NEW
│   ├── templates/forms/           # NEW: form-template library
│   │   ├── 12_bar_blues.yaml
│   │   ├── aaba_32.yaml
│   │   ├── verse_chorus_bridge.yaml
│   │   ├── edm_buildup_drop.yaml
│   │   └── ...
│   └── fragments/                 # Reusable spec fragments (planned)
│
├── src/
│   └── yao/
│       ├── constants/             # Layer 0
│       │   ├── instruments.py     # Extended to ~70 instruments
│       │   ├── scales.py
│       │   ├── chords.py          # Extended to 30+ chord types
│       │   ├── dynamics.py
│       │   └── drum_kits.py             # NEW: drum-kit definitions
│       ├── genre/                       # NEW: Genre subsystem (Layer 0/1)
│       │   ├── profile.py
│       │   ├── registry.py
│       │   ├── inheritance.py
│       │   ├── briefing.py
│       │   └── profiles/<name>.yaml
│       ├── schema/                # Layer 1: Pydantic models
│       │   ├── composition.py    # Extended with genre block
│       │   ├── trajectory.py
│       │   ├── constraints.py
│       │   ├── negative_space.py
│       │   ├── references.py
│       │   ├── production.py
│       │   └── form_template.py         # NEW
│       ├── ir/                    # Layer 3
│       │   ├── note.py
│       │   ├── score_ir.py
│       │   ├── harmony.py        # Extended chord types + devices
│       │   ├── progressions.py          # NEW: progression library
│       │   ├── motif.py
│       │   ├── voicing.py        # Extended voicing styles
│       │   ├── timing.py
│       │   ├── notation.py
│       │   ├── groove.py                # NEW: groove templates
│       │   ├── drum_pattern.py          # NEW: drum pattern type
│       │   └── phrasing.py              # NEW: vocal-like phrasing
│       ├── generators/            # Layer 2
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── rule_based.py
│       │   ├── stochastic.py
│       │   ├── drums.py                 # NEW: drum generator
│       │   ├── walking_bass.py          # NEW: walking-bass generator
│       │   ├── markov.py                # NEW: per-genre markov
│       │   ├── constraint_solver.py     # NEW: counterpoint, voice leading
│       │   └── ai_bridge.py             # NEW: external-model adapter
│       ├── perception/            # Layer 4
│       │   ├── style_vector.py          # NEW
│       │   ├── reference_matcher.py     # NEW
│       │   └── reference_library.py     # NEW
│       ├── render/                # Layer 5
│       │   ├── midi_writer.py
│       │   ├── stems.py
│       │   ├── audio_renderer.py
│       │   ├── lilypond_writer.py
│       │   └── strudel_emitter.py
│       ├── production/                  # NEW (Layer 5 adjunct)
│       │   ├── profile.py
│       │   ├── effect_chain.py
│       │   ├── pedalboard_runner.py
│       │   └── profiles/<name>.yaml
│       ├── verify/                # Layer 6
│       │   ├── music_lint.py
│       │   ├── analyzer.py
│       │   ├── evaluator.py
│       │   ├── diff.py
│       │   ├── constraint_checker.py
│       │   └── genre_conformance.py     # NEW
│       ├── reflect/               # Layer 7
│       │   ├── provenance.py
│       │   ├── feedback_loop.py
│       │   └── style_profile.py         # NEW: user preference learning
│       └── conductor/             # Cross-layer orchestrator
│           ├── conductor.py
│           ├── feedback.py
│           ├── nl_parser.py             # Upgraded to LLM-powered
│           └── result.py
│
├── references/                    # Aesthetic reference library
│   ├── catalog.yaml               # Rights, era, genre tags, feature vectors
│   ├── midi/<genre>/<id>.mid      # Rights-cleared MIDIs
│   ├── musicxml/<genre>/<id>.xml
│   ├── drum_patterns/<genre>/<id>.mid   # NEW: pattern library
│   ├── grooves/<id>.yaml                # NEW: groove templates
│   └── extracted_features/        # Pre-computed style vectors
│
├── outputs/                       # Generated artifacts (git-ignored)
├── soundfonts/                    # SoundFont files
└── tests/                         # 226+ tests, growing
    ├── unit/
    ├── integration/
    ├── scenarios/
    ├── music_constraints/
    ├── genre/                           # NEW: genre-specific tests
    └── helpers/
```

---

## 6. Orchestra Composition: The 9 Subagents

YaO v2.0 includes nine subagents. Each has a defined role, scoped tools, and explicit acceptance criteria. The Producer subagent acts as the concertmaster, integrating all outputs and resolving conflicts.

### 6.1 Genre Specialist (NEW in v2.0)
**Role:** Translates the user's chosen genre into a concrete genre briefing for all other subagents.
**Inputs:** `composition.yaml` (genre block), `GenreProfile` from registry.
**Outputs:** `GenreBriefing` — a structured object with target tempo, instrumentation rules, harmonic vocabulary, rhythmic feel, do's and don'ts, and per-section dynamics expectations.
**Boundary:** Does not generate any notes. Only produces a constraint set.
**Acceptance criteria:** The briefing is read by every downstream subagent and visibly affects their decisions in the provenance log.

### 6.2 Composer
**Role:** Generates melody, themes, motifs, and structural outlines.
**Inputs:** `intent.md`, `composition.yaml`, `trajectory.yaml`, `references.yaml`, `GenreBriefing`.
**Outputs:** Skeletal `ScoreIR` (motifs, melodic lines, structural outline).
**Boundary:** Does not assign instruments or final voicings (Orchestrator's job).
**Acceptance criteria:** Motif memorability, balance of repetition and variation, fit to trajectory.

### 6.3 Harmony Theorist
**Role:** Designs chord progressions, modulations, cadences, and reharmonization.
**Inputs:** Composer's melody, `composition.yaml` harmony block, `GenreBriefing`.
**Outputs:** Chord-progression IR (functional + concrete voicings).
**Acceptance criteria:** Functional integrity, tension-resolution flow, genre-appropriate vocabulary.

### 6.4 Rhythm Architect
**Role:** Drum patterns, grooves, syncopation, fills.
**Inputs:** `composition.yaml` rhythm block, `GenreBriefing`, drum pattern library.
**Outputs:** Drum and percussion `ScoreIR` plus groove template selection.
**Acceptance criteria:** Idiomatic groove for the genre, section-to-section contrast, humanization that feels organic.

### 6.5 Orchestrator
**Role:** Instrument assignment, voicings, register placement, countermelody.
**Inputs:** Outputs from Composer, Harmony Theorist, Rhythm Architect.
**Outputs:** Complete `ScoreIR` with per-instrument parts.
**Acceptance criteria:** Frequency-spacing without collision, idiomatic instrument usage, texture density matches trajectory.

### 6.6 Reharmonization (NEW in v2.0)
**Role:** Applies chord substitutions and voicing transformations.
**Inputs:** Existing chord progression + transformation directive.
**Outputs:** Substituted progression with provenance.
**Used by:** `/arrange` command, fusion-genre handling.
**Acceptance criteria:** Substitutions preserve melodic compatibility; voice leading remains smooth.

### 6.7 Adversarial Critic
**Role:** Find every weakness. Does not praise.
**Inputs:** Any-stage generation artifact.
**Outputs:** `critique.md` with severity ratings.
**Properties:** **Praise is forbidden.** The critic detects clichés, structural monotony, emotional inconsistencies, similarity to existing works, and genre violations.

### 6.8 Mix Engineer
**Role:** Stereo placement, dynamics, frequency-mask resolution, loudness.
**Inputs:** Orchestrator output + `production.yaml` + `ProductionProfile`.
**Outputs:** Mix instructions per track (EQ, compression, reverb, panning) and final mastered audio.
**Acceptance criteria:** Target LUFS achieved, frequency balance, stereo image matches genre profile.

### 6.9 Producer
**Role:** Overall integration, prioritization, dialogue with the human Conductor, final decisions.
**Inputs:** All other subagents' outputs + human feedback.
**Outputs:** Final production decisions and instructions for the next iteration.
**Privilege:** The only subagent that can override or reject another subagent's output.
**Acceptance criteria:** Faithfulness to `intent.md`.

---

## 7. The 6-Phase Cognitive Protocol

The `/compose` and `/arrange` slash commands force Claude Code through these six phases in order. This structured cognition prevents the failure mode of "agent immediately writes notes."

### Phase 1: Intent Crystallization
Convert user input (dialogue, YAML, sketch) into a 1–3 sentence statement of essence. Ambiguity is rejected. The result lives in `intent.md`.

> Example: "An early summer morning, the forward-leaning anticipation of a new challenge — though faintly mixed with anxiety. Not too cheerful, not too sentimental. A neutral uplift."

### Phase 2: Genre Resolution (NEW in v2.0)
Resolve the primary genre, optional fusion weights, and load the corresponding `GenreProfile`. Genre Specialist subagent produces the `GenreBriefing`. This phase exists only when a genre is specified; otherwise the protocol proceeds with default heuristics.

### Phase 3: Architectural Sketch
Draw the time-axis trajectories (tension / density / valence / predictability) **first**. Notes are not yet written. `trajectory.yaml` is finalized.

### Phase 4: Skeletal Generation
Composer produces 5–10 candidate skeletons (chord progression + main motif at 60% completion).

### Phase 5: Critic-Composer Dialogue
Adversarial Critic attacks all candidates. Producer judges and either selects the strongest, or commissions a synthesis that combines strengths.

### Phase 6: Detailed Filling and Listening Simulation
Harmony, Rhythm, Orchestrator, and Mix Engineer fill in detail. Provenance is recorded for every decision. Perception Substitute Layer (Layer 4) "listens" to the result, computes style-vector similarity to references, and triggers regeneration if drift exceeds threshold. Final output: `critique.md`, `analysis.json`, `evaluation.json`, `provenance.json`.

---

## 8. Specification Files

YaO describes a piece through a coordinated set of YAML files and Markdown intent. All files are version-controlled.

| File | Purpose |
|---|---|
| `intent.md` | Natural-language statement of the piece's essence (1–3 sentences) |
| `composition.yaml` | Core spec (key, tempo, time signature, form, genre, instruments, sections) |
| `trajectory.yaml` | Time-axis curves (tension, density, valence, predictability) |
| `references.yaml` | Aesthetic reference tracks (positive and negative anchors) |
| `negative-space.yaml` | What *not* to play (rests, frequency gaps, textural subtractions) |
| `arrangement.yaml` | (Arrangement mode only) preserve / transform / avoid directives |
| `production.yaml` | Mix and master targets (LUFS, stereo width, effect chains, profile id) |
| `provenance.json` | (Auto-generated) traceable decision log |

The `composition.yaml` schema in v2.0 introduces a richer `genre` block:

```yaml
genre:
  primary: "lofi_hip_hop"
  fusion:
    - genre: "neo_soul"
      weight: 0.2
  override_profile:
    target_lufs: -18.0   # User overrides specific profile fields

generation:
  per_instrument:
    drums:   { strategy: pattern_based, pattern: "boom_bap_classic" }
    bass:    { strategy: rule_based, walking: false }
    rhodes:  { strategy: stochastic, temperature: 0.55 }
    melody:  { strategy: markov, model: "neo_soul_2gram" }

form_template: "lofi_loop"

production:
  profile: "lofi_hip_hop"
```

Per-instrument generator selection is a key v2.0 capability: jazz drums benefit from pattern-based generation, jazz bass from constraint-solver-derived walking lines, jazz piano from stochastic comping, jazz sax from a Markov model trained on bebop.

---

## 9. Custom Commands (Conductor's Baton)

| Command | Purpose | Primary Subagents |
|---|---|---|
| `/sketch` | Sketch-to-spec dialogue mode | Producer + Genre Specialist |
| `/compose <project>` | Generate from spec | Composer → all |
| `/arrange <project>` | Transform an existing piece | Orchestrator + Reharmonization + Adversarial Critic |
| `/critique <iteration>` | Critique an existing artifact | Adversarial Critic |
| `/regenerate-section <project> <section>` | Regenerate one section, preserve others | Composer + Producer |
| `/morph <from> <to> <bars>` | Interpolate between two musical states | Composer + Orchestrator |
| `/improvise <input>` | Live improvisation mode | Composer + Rhythm Architect |
| `/explain <element>` | Explain a generation decision | Producer (consults provenance) |
| `/diff <iter_a> <iter_b>` | Music diff between iterations | Verifier |
| `/render <iteration>` | MIDI → audio + score | Mix Engineer |
| `/genre-info <genre>` | Display the GenreProfile for a genre | Genre Specialist |

---

## 10. Skills (Players' Knowledge)

`.claude/skills/` contains structured knowledge modules. Subagents consult these as needed.

### 10.1 Genre Skills
Each genre has its own skill file matching the `GenreProfile` it documents. Includes typical chord progressions, rhythm patterns, instrumentation, representative reference tracks, and clichés to avoid. Authored as Markdown so non-coders can contribute.

### 10.2 Theory Skills
Voice leading, counterpoint, reharmonization, modal interchange, secondary dominants, tritone substitution. Includes examples, counter-examples, and genre-dependent applicability.

### 10.3 Instrument Skills
Per-instrument range, idiomatic articulations, characteristic phrases, physical and ergonomic constraints, recommended SoundFonts.

### 10.4 Psychology Skills
Empirical mappings from music psychology research (Juslin, Huron, Krumhansl): tempo-arousal, mode-valence, spectral centroid-brightness, expectancy-tension.

### 10.5 Groove Skills (NEW in v2.0)
What makes a piece "feel" like a genre at the rhythmic level: micro-timing, pocket, swing semantics, accent patterns. Includes call-and-response density patterns.

### 10.6 Drum Skills (NEW in v2.0)
Per-genre drum vocabulary: typical kick patterns, snare placements, hi-hat behaviors, fills, and which kit (rock, jazz, 808, lo-fi) each subgenre prefers.

### 10.7 Production Skills (NEW in v2.0)
Per-genre mix and master practices: lo-fi vinyl crackle, EDM sidechain pumping, vintage tape saturation, classical hall reverb. Operational, not theoretical.

---

## 11. Hooks (Automatic Performance Cues)

Hooks are scripts (not LLM instructions) that are guaranteed to run at specific lifecycle events. They cannot be forgotten.

| Hook | When | Action |
|---|---|---|
| `pre-commit-lint` | Before `git commit` | music21 theory lint + YAML schema validation + architecture lint |
| `post-generate-render` | After every generation | Auto-render MIDI to audio and score |
| `post-generate-critique` | After every generation | Auto-invoke Adversarial Critic |
| `post-generate-conformance` | After every generation | Auto-compute Genre Conformance (NEW in v2.0) |
| `update-provenance` | After any change | Refresh the provenance graph |

---

## 12. MCP Integrations

YaO is designed to connect with these MCP servers, though most remain optional.

| Connection | Purpose |
|---|---|
| **DAW (Reaper preferred)** | Project file read/write, automatic track layout |
| **Sample library** | Drum samples, one-shots, loop search and retrieval |
| **Reference track DB** | Rights-cleared reference catalog and feature search |
| **MIDI controller** | Live improvisation mode input |
| **SoundFont/VST server** | Audio rendering |
| **Cloud storage** | Backup and team collaboration |

---

## 13. Quality Evaluation

Generated outputs are scored across six dimensions (six in v2.0; was five in v1.0). Scores are persisted in `evaluation.json`.

### 13.1 Structure Evaluation
Section contrast, climax position, density-curve fit, repetition balance, loop-ability.

### 13.2 Melody Evaluation
Range fit, motif memorability, singability (leap reasonableness), phrase closure, contour variation.

### 13.3 Harmony Evaluation
Chord function integrity, tension-resolution, complexity matching the spec, cadence strength.

### 13.4 Arrangement Evaluation (Arrangement mode)
Instrument-role clarity, frequency collision risk, original-piece preservation, transformation strength.

### 13.5 Acoustic Evaluation
BPM match, beat stability, LUFS target achievement, spectral balance, onset density.

### 13.6 Genre Conformance (NEW in v2.0)
The aggregate of: instrumentation match, tempo match, time-signature match, mode match, swing match, chord-palette match, harmonic-rhythm match, form match, and reference similarity. Each genre profile contributes its own weighting (jazz weights harmony heavily, EDM weights rhythm and texture). The Conductor uses this score to drive genre-aware adaptations in the feedback loop.

---

## 14. Roadmap

The roadmap unifies prior phases (0–1, completed in v1.0) with the new diversity-driven phases (A–G) introduced for v2.0.

### v1.0 — Foundation (Completed)
- 7-layer architecture with AST-based linting
- `ScoreIR`, harmony, motif, voicing, timing modules
- Rule-based and stochastic generators
- Conductor with feedback loop
- Provenance logging
- Music lint, evaluator, diff
- 226+ tests
- 4 spec templates and 7 example projects

### v2.0 — Genre Diversity (In Progress)

#### Phase A: Genre System Foundation (2–3 weeks)
- `GenreProfile` Pydantic model
- 15–20 genre profile YAMLs
- Genre detection in NL parser (keyword → LLM-powered)
- Genre Conformance evaluator (initial 4–5 sub-metrics)
- Genre Specialist subagent

#### Phase B: Rhythm and Drums (3–4 weeks)
- 35–40 drum patterns as MIDI in `references/drum_patterns/`
- `DrumPattern` data structure and loader
- `DrumGenerator` with pattern selection logic
- `GrooveTemplate` and 20+ initial grooves
- Whole-piece groove application
- Section-boundary fill generator

#### Phase C: Extended Harmony (3–4 weeks)
- 15+ new chord types (9th, 11th, 13th, altered, quartal, slash, etc.)
- Progression library with 50–80 idiomatic progressions
- Secondary dominants, tritone substitution, modal interchange
- Voicing styles (rootless, drop2, quartal, power chord)
- Harmonic-rhythm control
- Reharmonization Subagent

#### Phase D: Instrument Palette Expansion (2–3 weeks)
- 20–30 modern instruments (808/909 kits, Rhodes, Hammond, distorted guitars, ethnic instruments)
- Updated SoundFont mappings
- Per-instrument velocity-response curves
- Non-GM percussion in render layer

#### Phase E: Form and Structure (2–3 weeks)
- 12–15 form templates (12-bar blues, AABA, verse-chorus-bridge, EDM buildup-drop, etc.)
- Form template loader and validator
- Automatic form selection based on genre
- Form-aware section trajectory presets

#### Phase F: Layer 4 — Style Reference (3–4 weeks)
- Reference Library with 5–10 rights-cleared MIDIs per genre
- `StyleVector` extraction
- `ReferenceMatcher` with weighted distance
- Conductor integration of similarity score

#### Phase G: Production and Phrasing (continuous)
- `ProductionProfile` data structure
- `pedalboard` dependency, per-genre effect chains
- Phrasing Engine (vocal-like melody generation)
- Call-and-response patterns
- Markov Generator (per-genre training)
- Constraint Solver Generator (counterpoint, jazz harmony, 12-tone)
- AI Bridge Generator (Magenta, Stable Audio, etc.)

### v3.0 and Beyond
- Live improvisation mode (real-time MIDI in)
- DAW integration (Reaper MCP)
- User-style learning (Layer 7)
- Community-shared reference libraries
- Web-based browser preview

---

## 15. Quickstart

```bash
git clone <repo>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-soundfonts
```

```bash
yao new-project my-first-song
claude   # launch Claude Code in the YaO directory
> /sketch
> "lo-fi hip hop for studying, mellow, 90 seconds"
> /compose my-first-song
afplay outputs/projects/my-first-song/iterations/v001/audio.wav
> /critique my-first-song
> /regenerate-section my-first-song chorus
```

For arrangement (transforming an existing piece into a different genre):

```bash
cp source.mid specs/projects/my-arrangement/source.mid
> /arrange my-arrangement --target-genre jazz
```

---

## 16. File Formats and Interoperability

YaO uses standard formats wherever possible to maintain interoperability.

| Use | Format | Reason |
|---|---|---|
| Music data | MIDI (.mid), MusicXML (.xml) | Universal DAW support |
| Score | LilyPond (.ly), PDF | High-quality typesetting |
| Specs | YAML | Human-readable, git-friendly |
| IR | JSON | Programmatic + schema-validated |
| Provenance | JSON | Graph-structured |
| Audio | WAV (working), FLAC/MP3 (distribution) | Standards |
| Live patterns | Strudel pattern strings | Browser-based instant audition |
| Drum patterns | MIDI Type 1 | Authorable in any DAW |
| Grooves | YAML | Per-tick offset specification |

Custom formats are introduced only when no standard suffices, and only with explicit design justification.

---

## 17. Ethics and Licensing

### 17.1 Reference Library
Only rights-cleared works are placed in `references/`. Each entry's license status is recorded in `catalog.yaml`. Unknown-status works are not used.

### 17.2 Artist Mimicry
Direct mimicry of named, currently-active artists is discouraged. Use abstract feature descriptions instead.

> ✗ "in the style of <Living Artist Name>"
> ✓ "wide open string voicings, ascending motifs, oscillation between major and minor, meditative tempo"

### 17.3 Output Rights
Pieces generated by YaO are owned by the user by default. If reference influence is unusually high, YaO emits a warning and records details in the provenance log.

### 17.4 Transparency
Generated outputs should record "produced with YaO" along with the list of aesthetic anchors consulted.

---

## 18. Document Relationships

| File | Audience | Contents |
|---|---|---|
| `PROJECT.md` (this) | Humans + agents | Overall design, philosophy, architecture |
| `CLAUDE.md` | Agent (development) | Invariant rules, prohibitions, references to skills |
| `IMPROVEMENT.md` | Humans + agents | Detailed analysis and proposals for v2.0 (genre diversity) |
| `README.md` | Humans | Quickstart, minimal usage |
| `docs/design/*.md` | Humans + agents | Individual design-decision records |
| `.claude/guides/*.md` | Agent (development) | Topic-specific deep guides (architecture, testing, etc.) |
| `docs/` (mkdocs) | Users + developers | Hosted documentation site |

---

## 19. Glossary

**Conductor** — The human project owner; final decision-maker.
**Orchestra** — The collective of subagents.
**Score** — The YAML spec set.
**ScoreIR** — The mid-level dataclass representation of a piece.
**Trajectory** — A time-axis curve of musical attributes.
**GenreProfile** — Machine-readable definition of a genre (NEW v2.0).
**GenreBriefing** — Resolved guidance distributed to all subagents (NEW v2.0).
**GrooveTemplate** — Coordinated micro-timing pattern (NEW v2.0).
**DrumPattern** — A bar-length pattern across the GM drum map (NEW v2.0).
**ProductionProfile** — Genre-specific mix/master settings (NEW v2.0).
**Aesthetic Reference Library** — Genre-tagged reference works.
**Perception Substitute Layer** — Layer 4: stand-in for the AI's inability to "hear."
**Provenance** — Traceable record of every generation decision.
**Adversarial Critic** — Subagent that exclusively criticizes.
**Negative Space** — What is intentionally not played.
**Style Vector** — Multi-dimensional feature representation of style.
**Iteration** — A version (v001, v002, ...) within a project.
**Music Lint** — Automated theory-violation detection.
**Genre Conformance** — Quality dimension introduced in v2.0.

---

## 20. Closing Words: What YaO Aims to Be

YaO is not a project where AI writes music. It is **infrastructure for humans and AI to co-create music**, each contributing what they do best.

- Humans provide **intent, judgment, and taste**.
- AI provides **theoretical knowledge, iteration speed, and exhaustive recordkeeping**.
- YaO is **the structured collaborative process** that lets these two work together.

Great music remains, in the end, an expression of the human soul. YaO aims to make that expression **faster, deeper, and more reproducible** — across every genre that humans care about.

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to serve, in any genre.*

---

**Project: You and Orchestra (YaO)**
*Document version: 2.0*
*Last updated: 2026-05-08*
