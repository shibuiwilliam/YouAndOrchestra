# You and Orchestra (YaO)

[![CI](https://github.com/yao-project/yao/actions/workflows/ci.yml/badge.svg)](https://github.com/yao-project/yao/actions/workflows/ci.yml)
[![Docs](https://github.com/yao-project/yao/actions/workflows/docs.yml/badge.svg)](https://yao-project.github.io/yao/)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

Describe what you want in plain English or YAML, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to serve.

**What's implemented?** See [FEATURE_STATUS.md](FEATURE_STATUS.md) — the single source of truth for capabilities.

---

## Three Ways to Use YaO

### 1. Natural language (fastest)

```bash
yao conduct "a calm piano piece in D minor for studying, 90 seconds"
```

YaO parses your description, picks the key, tempo, instruments, and sections, generates a composition, evaluates it, and automatically adapts and regenerates until quality metrics pass.

```
=== Conductor Result ===
Quality Score: 7.2/10
Pass rate: 100% (10/10)
Duration: 90.0s | Bars: 30 | Notes: 112
Instruments: piano
Output: outputs/projects/a-calm-piano-piece/iterations/v001/
```

### 2. YAML specification (full control)

```bash
yao compose specs/projects/my-song/composition.yaml
```

```yaml
title: Rainy Cafe
key: D minor
tempo_bpm: 90
time_signature: "4/4"

instruments:
  - name: piano
    role: melody
  - name: cello
    role: bass

sections:
  - name: intro
    bars: 4
    dynamics: pp
  - name: verse
    bars: 8
    dynamics: mp
  - name: chorus
    bars: 8
    dynamics: f
  - name: outro
    bars: 4
    dynamics: pp

generation:
  strategy: stochastic
  seed: 42
  temperature: 0.5
```

YaO also supports a **v2 spec format** with 11 dedicated sections for finer control over emotion, melody, harmony, rhythm, drums, arrangement, and production. See [Composition Spec Guide](docs/guide/composition-spec.md).

### 3. Claude Code (interactive, recommended)

```
> /sketch a mysterious puzzle game BGM, minimal and looping
```

Claude Code guides you through spec creation, generates the music, critiques it, and iterates based on your feedback.

---

## Instant Audition

```bash
yao preview specs/templates/minimal.yaml     # Generate and play — no file written
yao watch specs/templates/minimal.yaml       # Edit spec, hear changes on save
```

Requires FluidSynth and a SoundFont (see [Audio Rendering](#audio-rendering)).

---

## Install

```bash
git clone <repo-url>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-hooks  # Install pre-commit hooks
```

Requires **Python 3.11+**. Audio rendering requires [FluidSynth](#audio-rendering).

---

## What YaO Generates

Each iteration produces:

```
outputs/projects/<name>/iterations/v001/
  full.mid           # Complete MIDI score (all instruments)
  stems/             # Per-instrument MIDI files
    piano.mid
    cello.mid
  analysis.json      # Note counts, pitch ranges, duration, lint results
  evaluation.json    # Quality scores (1.0-10.0) across structure/melody/harmony
  provenance.json    # Decision log with rationale for every choice
```

Pre-generated examples in [`gallery/`](gallery/).

---

## CLI Reference

| Command | What it does |
|---|---|
| `yao conduct "<description>"` | Natural language to MIDI with automatic evaluate-adapt-regenerate |
| `yao conduct --spec <yaml>` | Run the Conductor loop on an existing spec |
| `yao compose <spec.yaml>` | Generate from spec (single pass, no iteration) |
| `yao regenerate-section <project> <section>` | Regenerate one section, preserve the rest |
| `yao render <file.mid>` | Render MIDI to WAV audio |
| `yao preview <spec.yaml>` | Generate and play in-memory (no file output) |
| `yao watch <spec.yaml>` | File-watch + auto-regenerate + auto-play on save |
| `yao new-project <name>` | Create a project skeleton |
| `yao validate <spec.yaml>` | Check a spec and display its details |
| `yao evaluate <project>` | Re-evaluate the latest iteration |
| `yao diff <spec.yaml>` | Compare two stochastic generations side by side |
| `yao explain <spec.yaml>` | Show provenance — why each decision was made |

---

## The Conductor

The Conductor automates the generate-evaluate-adapt loop:

```
Spec  ->  Plan  ->  Generate  ->  Evaluate + Critique  ->  Pass?  ->  Done
                                       | No
                                  Adapt spec  ->  Regenerate
```

It builds a Composition Plan (form + harmony), realizes it into notes, scores the result across 10 metrics, runs 20 adversarial critique rules, and adapts the spec if issues are found. Each iteration is saved as a new version with full provenance.

| Problem Detected | Adaptation |
|---|---|
| Low pitch variety | Increase temperature or switch to stochastic |
| Too many melodic leaps | Decrease temperature for smoother lines |
| Sections sound too similar | Differentiate dynamics across sections |
| Climax absence (critique) | Adjust section dynamics to create climax |
| Cliche progression (critique) | Flag for harmonic revision |
| Intent divergence (critique) | Realign generation parameters with intent |

---

## Generation

### Strategies

| Strategy | Description |
|---|---|
| **rule_based** | Deterministic. Same spec = same output. Good for golden tests. |
| **stochastic** | Seed + temperature. 4 contour algorithms, 5 chord voicings, 12 rhythm templates, walking bass, motif transformation. |
| **markov** | Probabilistic transitions from learned patterns. |
| **twelve_tone** | Serialist composition using tone rows. |
| **process_music** | Minimalist / generative process-based composition. |
| **constraint_solver** | Backtracking search with hard constraints. |

### Additional Generators

| Generator | What it does |
|---|---|
| **drum_patterner** | 8 genre-specific patterns (pop, rock, jazz, lo-fi, trap, ballad, game, four-on-the-floor) with swing, ghost notes, trajectory density |
| **counter_melody** | Species counterpoint with contrary motion, consonance preference, density control |
| **performance** | Performance expression (articulation, dynamics, timing micro-offsets) |
| **neural** | Neural/AI model bridge for texture generation |

All generators respond to multi-dimensional trajectory: tension affects pitch+leaps, density affects rhythm, register_height affects octave.

---

## Trajectory System

Shape the emotional arc independently from the notes:

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.85], [32, 0.3]]
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, chorus: 0.9, outro: 0.3 }
  predictability:
    type: linear
    target: 0.65
    variance: 0.15
```

Five dimensions: tension, density, predictability, brightness, register height. Three curve types: bezier, stepped, linear.

---

## Quality Evaluation

Every composition is scored across 10 metrics in 3 dimensions, producing a **quality score from 1.0 to 10.0**:

| Dimension (weight) | Metrics |
|---|---|
| **Structure** (25%) | Section contrast, bar count accuracy, section count match, rhythm variety, syncopation ratio |
| **Melody** (30%) | Pitch range utilization, stepwise motion ratio, contour variety |
| **Harmony** (25%) | Pitch class variety, consonance ratio |

Each metric uses a typed `MetricGoal` (7 types: AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN, MATCH_CURVE, RELATIVE_ORDER, DIVERSITY).

---

## Adversarial Critique

A **rule-based critique engine** with 20 structured rules across 8 categories:

| Category | Rules |
|---|---|
| **Structural** (3) | Climax absence, section monotony, form imbalance |
| **Melodic** (3) | Cliche motif, contour monotony, phrase closure weakness |
| **Harmonic** (3) | Cliche progression, voice crossing, cadence weakness |
| **Rhythmic** (2) | Rhythmic monotony, groove inconsistency |
| **Arrangement** (2) | Frequency collision, texture collapse |
| **Emotional** (2) | Intent divergence, trajectory violation |
| **Genre Fitness** (2) | Genre convention mismatch, idiom deviation |
| **Memorability** (2) | Hook weakness, motif recall failure |

Each rule emits structured `Finding` objects with severity, evidence, location, and recommendations — machine-actionable, not free text.

---

## Arrangement Engine

Transform existing compositions:

```bash
yao arrange my-project --target-genre lofi_hiphop --preserve melody
```

Pipeline: Source MIDI → Extract plan → Style vector operations → Target plan → Realize → Diff report.

Components: `extractor.py` (MIDI analysis), `style_vector_ops.py` (genre transformation), `diff_writer.py` (change report), `critique_rules.py` (arrangement-specific validation).

---

## Perception Layer

Audio-level analysis that substitutes for human listening:

- **Audio features** — LUFS, spectral centroid, onset density, tempo stability (via librosa)
- **Use-case evaluation** — youtube_bgm, game_bgm, advertisement, study_focus
- **Reference matching** — Abstract feature vector comparison (never melody/hook copying)
- **Style vectors** — Multi-dimensional genre representation for interpolation

---

## Using YaO with Claude Code

| Command | What it does |
|---|---|
| `/sketch` | Interactive spec creation through guided dialogue |
| `/compose <project>` | Generate with the Conductor |
| `/critique <project>` | Adversarial feedback — finds every weakness |
| `/explain <question>` | Trace any decision through the provenance log |
| `/regenerate-section <project> <section>` | Fix one section |
| `/render <project>` | Render to WAV audio |
| `/arrange <project>` | Transform an existing composition |

### 7 Subagents

| Subagent | Role |
|---|---|
| **Producer** | Coordinates all subagents, resolves conflicts, makes final decisions |
| **Composer** | Melodies, motifs, themes, structural outlines |
| **Harmony Theorist** | Chord progressions, modulations, cadences |
| **Rhythm Architect** | Drum patterns, grooves, syncopation, fills |
| **Orchestrator** | Instruments, voicings, frequency spacing, countermelodies |
| **Mix Engineer** | Stereo placement, dynamics, frequency balance, loudness |
| **Adversarial Critic** | Finds weaknesses — never praises |

### 32 Domain Skills

| Category | Count | Examples |
|---|---|---|
| **Genres** | 22 | cinematic, lofi_hiphop, j_pop, jazz_swing, bossa_nova, synthwave, celtic, arab_maqam, blues, funk, baroque, romantic... |
| **Theory** | 4 | voice-leading, twelve-tone, microtonal, process-music |
| **Articulation** | 4 | piano-pedaling, jazz-microtiming, strings-articulation, winds-articulation |
| **Instruments** | 1 | piano |
| **Psychology** | 1 | tension-resolution |

---

## Music Theory Built In

- **38 instruments** across 9 families (keyboard, strings, guitar, bass, brass, woodwind, saxophone, synth, percussion)
- **14 scales** (major, minor, harmonic minor, melodic minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic major/minor, blues, whole tone, chromatic)
- **14 chord types** (major through major 9th, including sus2, sus4, add9)
- **Functional harmony** via Roman numeral notation (I, ii, V7/V) with `realize()` for concrete pitches
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations** (transpose, invert, retrograde, augment, diminish) tracked in provenance
- **DrumPattern IR** with 15 kit pieces mapped to General MIDI, 8 genre patterns
- **12 section types** (intro, verse, pre-chorus, chorus, bridge, solo, interlude, breakdown, build, drop, outro, coda)

---

## Architecture

```
Conductor           — Orchestrates generate-evaluate-critique-adapt loop
Layer 6: Verify     — Evaluation (10 metrics), critique (20 rules), linting, diffing, constraints
Layer 5: Render     — MIDI writer, stems, audio renderer, iteration management
Layer 4: Perception — Audio features, use-case evaluation, reference matching, style vectors
Layer 3a: Plan IR   — Composition Plan IR (CPIR): SongFormPlan, HarmonyPlan
Layer 3b: Score IR  — ScoreIR, Note, DrumPattern, harmony, motif, voicing, timing
Layer 2: Generate   — Plan generators, note realizers, drum patterner, counter-melody, markov, twelve-tone, process, neural, performance
Layer 1: Schema     — Pydantic models for YAML specs (v1 + v2)
Layer 0: Constants  — 38 instruments, 14 scales, 14 chords, MIDI mappings
```

The v2.0 pipeline: `Spec → PlanOrchestrator → MusicalPlan (CPIR) → NoteRealizer → ScoreIR → MIDI`

All IR objects are immutable frozen dataclasses. Layer boundaries enforced by `make arch-lint`.

---

## Constraint System

```yaml
constraints:
  - type: must_not
    rule: parallel_fifths
    scope: global
    severity: error
  - type: prefer
    rule: "max_density:4"
    scope: "section:intro"
    severity: hint
```

Four types (`must`, `must_not`, `prefer`, `avoid`) with scopes: `global`, `section:<name>`, `instrument:<name>`, `bars:<start>-<end>`.

---

## Audio Rendering

Requires FluidSynth and a General MIDI SoundFont:

```bash
# macOS
brew install fluid-synth
# Linux
sudo apt-get install fluidsynth
# Place a SoundFont in soundfonts/, then render
yao render outputs/projects/my-song/iterations/v001/full.mid
```

---

## Spec Templates

| Template | Description |
|---|---|
| `minimal.yaml` | 8-bar solo piano in C major |
| `bgm-90sec.yaml` | 90-second BGM with piano and bass |
| `cinematic-3min.yaml` | 3-minute orchestral piece in D minor |
| `lofi-cafe.yaml` | Lo-fi cafe BGM with relaxed tempo |
| `trajectory-example.yaml` | Example tension/density/predictability curves |
| `v2/bgm-90sec-pop.yaml` | Pop BGM with emotion, melody, harmony, production |
| `v2/cinematic-3min.yaml` | Full cinematic in 11-section v2 format |
| `v2/loopable-game-bgm.yaml` | Looping game music with loop-aware constraints |

---

## Project Structure

```
yao/
+-- CLAUDE.md                     # Development rules
+-- PROJECT.md                    # Design documentation
+-- FEATURE_STATUS.md             # Single source of truth for capabilities
+-- VISION.md                     # Target architecture
+-- README.md                     # This file
+-- pyproject.toml                # Dependencies and config
+-- Makefile                      # Development commands
+-- .pre-commit-config.yaml       # Pre-commit hooks
+-- .github/workflows/            # CI + docs deployment
|
+-- src/yao/                      # Main library (155 Python files)
|   +-- conductor/                # Orchestration + critique integration
|   +-- constants/                # 38 instruments, 14 scales, 14 chords
|   +-- schema/                   # Pydantic specs (v1 + v2)
|   +-- ir/                       # ScoreIR, DrumPattern, plan/ (CPIR)
|   +-- generators/               # 10+ generators: stochastic, markov, twelve_tone,
|   |                             #   process_music, drum_patterner, counter_melody,
|   |                             #   neural/, performance/, plan/, note/
|   +-- render/                   # MIDI writer, stems, audio, iterations
|   +-- verify/                   # Lint, eval, diff, constraints, critique/ (20 rules)
|   +-- reflect/                  # Provenance, RecoverableDecision
|   +-- perception/               # Audio features, style vectors, use-case eval
|   +-- arrange/                  # Arrangement engine (extractor, style ops, diff)
|   +-- sketch/                   # NL → spec compiler
+-- src/cli/                      # Click CLI (11 commands)
|
+-- .claude/
|   +-- commands/                 # 7 slash commands
|   +-- agents/                   # 7 subagent definitions
|   +-- skills/                   # 32 domain skills
|   +-- guides/                   # 8 development guides
|
+-- drum_patterns/                # 8 genre-specific drum pattern YAMLs
+-- specs/templates/              # 5 v1 + 3 v2 YAML templates
+-- gallery/                      # Pre-generated MIDI examples
+-- tests/                        # 1,094 tests
+-- tools/                        # Architecture lint, feature status, skill sync
+-- docs/                         # mkdocs documentation
+-- development/                  # Developer reference docs
```

---

## Development

```bash
make install           # Install with dev dependencies
make setup-hooks       # Install pre-commit + pre-push hooks
make test              # Run all 1,094 tests
make test-unit         # Unit tests only
make test-golden       # Golden MIDI regression
make test-subjective   # Subjective quality evaluation
make lint              # ruff + mypy strict
make format            # Auto-format
make arch-lint         # Layer boundary enforcement
make feature-status    # Verify FEATURE_STATUS.md matches code
make sync-skills       # Sync genre skill YAML from markdown
make sync-docs         # Sync documentation consistency
make all-checks        # Everything
```

### Code Standards

- Python 3.11+, `from __future__ import annotations`
- mypy strict, ruff (line length: 120)
- Pydantic for YAML specs, frozen dataclasses for IR
- Custom exceptions only (`YaOError` subclasses)
- Pre-commit: ruff, mypy, arch-lint on commit; unit tests on push

### CI/CD

- **ci.yml** — Lint, type check, arch-lint, tests (Python 3.11-3.13), golden MIDI regression
- **docs.yml** — Build and deploy mkdocs to GitHub Pages on push to main

---

## Design Philosophy

1. **The agent is an environment, not a composer** — YaO accelerates human creativity
2. **Every decision is explainable** — provenance records why each note exists
3. **Constraints liberate** — specs and rules are scaffolding, not cages
4. **Time-axis first** — trajectory curves define the arc; notes fill the details
5. **The human ear is the final truth** — automated scores inform; humans decide
6. **Incrementality** — do not break what works; extend each layer progressively

Full design: [PROJECT.md](PROJECT.md) | Rules: [CLAUDE.md](CLAUDE.md) | Vision: [VISION.md](VISION.md) | Features: [FEATURE_STATUS.md](FEATURE_STATUS.md) | [Docs](https://yao-project.github.io/yao/) | [Gallery](gallery/)

---

## License

MIT
