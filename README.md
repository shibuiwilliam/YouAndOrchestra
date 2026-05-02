# You and Orchestra (YaO)

[![CI](https://github.com/yao-project/yao/actions/workflows/ci.yml/badge.svg)](https://github.com/yao-project/yao/actions/workflows/ci.yml)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

Describe what you want in plain English or YAML, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to serve.

**What's implemented?** See [FEATURE_STATUS.md](FEATURE_STATUS.md) — the single source of truth for YaO's capabilities.

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

Claude Code guides you through spec creation interactively, generates the music, critiques it, and iterates based on your feedback.

---

## Instant Audition

```bash
yao preview specs/templates/minimal.yaml     # Generate and play — no file written
yao watch specs/templates/minimal.yaml       # Edit and save to hear changes instantly
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

Pre-generated examples are available in [`gallery/`](gallery/).

---

## CLI Reference

| Command | What it does |
|---|---|
| `yao conduct "<description>"` | Natural language to MIDI with automatic evaluate-adapt-regenerate |
| `yao conduct --spec <yaml>` | Run the Conductor loop on an existing spec |
| `yao compose <spec.yaml>` | Generate from spec (single pass, no iteration) |
| `yao regenerate-section <project> <section>` | Regenerate one section, preserve the rest |
| `yao render <file.mid>` | Render MIDI to WAV audio |
| `yao preview <spec.yaml>` | Generate and play in-memory — no file written |
| `yao watch <spec.yaml>` | File-watch + auto-regenerate + auto-play on save |
| `yao new-project <name>` | Create a project skeleton with template files |
| `yao validate <spec.yaml>` | Check a spec and display its details |
| `yao evaluate <project>` | Re-evaluate the latest iteration |
| `yao diff <spec.yaml>` | Compare two stochastic generations side by side |
| `yao explain <spec.yaml>` | Show provenance — why each decision was made |

---

## The Conductor

The Conductor automates the generate-evaluate-adapt loop:

```
Spec  ->  Plan  ->  Generate  ->  Evaluate  ->  Pass?  ->  Done
                                     | No
                                Adapt spec  ->  Regenerate
```

It builds a Composition Plan (form + harmony), realizes it into notes, scores the result across 10 metrics in 3 dimensions, runs 15 adversarial critique rules, and adapts the spec if issues are found. Each iteration is saved as a new version with full provenance.

| Problem Detected | Adaptation |
|---|---|
| Low pitch variety | Increase temperature or switch to stochastic |
| Too many melodic leaps | Decrease temperature for smoother lines |
| Sections sound too similar | Differentiate dynamics across sections |
| Too dissonant | Reduce temperature for more consonant intervals |
| Climax absence (critique) | Adjust section dynamics to create climax |
| Cliche progression (critique) | Flag for manual harmonic revision |

---

## Generation Strategies

### Rule-Based (deterministic)

```yaml
generation:
  strategy: rule_based
```

Same spec always produces the same output. Scale-based melodies, I-IV-V-I progressions, root-note bass. Good for baselines and golden tests.

### Stochastic (controlled randomness)

```yaml
generation:
  strategy: stochastic
  seed: 42
  temperature: 0.5  # 0.0 = conservative, 1.0 = adventurous
```

Features:
- **4 melodic contour algorithms** — arch, ascending, descending, wave (section-aware selection)
- **5 chord voicing types** — root, first inversion, second inversion, open, drop2 (temperature-dependent)
- **Section-aware chord progressions** — different patterns for verse, chorus, bridge, intro, outro
- **Diatonic 7th chords** — maj7, min7, dom7 with temperature-dependent probability
- **12 rhythm templates** — syncopation, dotted rhythms, mixed patterns
- **Walking bass** — quarter-note patterns with passing tones and approach notes
- **Drum patterns** — 8 genre-specific patterns with swing, ghost notes, trajectory density
- **Counter-melody** — species counterpoint with contrary motion and density control
- **Velocity humanization** — dynamics-derived with trajectory tension modifier
- **Motif transformation** — transpose, invert, retrograde, augment, diminish
- **Multi-dimensional trajectory coupling** — tension affects pitch+leaps, density affects rhythm, register_height affects octave
- **Configurable via `StochasticConfig`** — 15+ tuning parameters extracted into a frozen dataclass

Change the seed to get a completely different composition from the same spec.

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

Five dimensions: tension, density, predictability, brightness, and register height. Three curve types: bezier, stepped, and linear. All generators respond to trajectory changes — this is enforced by trajectory compliance tests.

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

YaO includes a **rule-based critique engine** with 15 structured rules across 6 categories:

| Category | Rules |
|---|---|
| **Structural** (3) | Climax absence, section monotony, form imbalance |
| **Melodic** (3) | Cliche motif, contour monotony, phrase closure weakness |
| **Harmonic** (3) | Cliche progression, voice crossing, cadence weakness |
| **Rhythmic** (2) | Rhythmic monotony, groove inconsistency |
| **Arrangement** (2) | Frequency collision, texture collapse |
| **Emotional** (2) | Intent divergence, trajectory violation |

Each rule emits structured `Finding` objects with severity (critical/major/minor/suggestion), evidence, location, and recommendations — machine-actionable, not free text. The Conductor integrates critique findings into its feedback loop.

---

## Using YaO with Claude Code

Launch Claude Code in the YaO directory and use slash commands:

| Command | What it does |
|---|---|
| `/sketch` | Interactive spec creation through guided dialogue |
| `/compose <project>` | Generate with the Conductor |
| `/critique <project>` | Adversarial feedback — finds every weakness |
| `/explain <question>` | Trace any decision through the provenance log |
| `/regenerate-section <project> <section>` | Fix one section |
| `/render <project>` | Render to WAV audio |
| `/arrange <project>` | Transform an existing composition *(planned)* |

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

### 11 Domain Skills

| Category | Skills |
|---|---|
| **Genres** (8) | cinematic, lofi_hiphop, j_pop, neoclassical, ambient, jazz_ballad, game_8bit_chiptune, acoustic_folk |
| **Theory** (1) | voice-leading |
| **Instruments** (1) | piano |
| **Psychology** (1) | tension-resolution |

---

## Music Theory Built In

- **38 instruments** across 9 families (keyboard, strings, guitar, bass, brass, woodwind, saxophone, synth, percussion)
- **14 scales** (major, minor, harmonic minor, melodic minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic major/minor, blues, whole tone, chromatic)
- **14 chord types** (major through major 9th, including sus2, sus4, add9)
- **Functional harmony** via Roman numeral notation (I, ii, V7/V) with `realize()` for concrete pitches
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations** (transpose, invert, retrograde, augment, diminish) tracked in provenance
- **DrumPattern IR** with 15 kit pieces mapped to General MIDI, 8 genre-specific patterns
- **12 section types** (intro, verse, pre-chorus, chorus, bridge, solo, interlude, breakdown, build, drop, outro, coda)

---

## Architecture

```
Conductor           — Orchestrates the generate-evaluate-adapt loop + critique integration
Layer 6: Verify     — Evaluation (10 metrics), critique (15 rules), linting, diffing, constraints
Layer 5: Render     — MIDI writer, stems, audio renderer, iteration management
Layer 3a: Plan IR   — Composition Plan IR (CPIR): SongFormPlan, HarmonyPlan
Layer 3b: Score IR  — ScoreIR, Note, DrumPattern, harmony, motif, voicing, timing
Layer 2: Generate   — Plan generators + note realizers + drum patterner + counter-melody
Layer 1: Schema     — Pydantic models for YAML specs (v1 + v2)
Layer 0: Constants  — 38 instruments, 14 scales, 14 chords, MIDI mappings
```

The v2.0 pipeline: `Spec → PlanOrchestrator → MusicalPlan (CPIR) → NoteRealizer → ScoreIR → MIDI`

All IR objects are immutable frozen dataclasses. Layer boundaries are enforced by `make arch-lint`.

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

### v1 (simple)

| Template | Description |
|---|---|
| `minimal.yaml` | 8-bar solo piano in C major — the simplest possible spec |
| `bgm-90sec.yaml` | 90-second BGM with piano and bass, 4 sections |
| `cinematic-3min.yaml` | 3-minute orchestral piece in D minor |
| `lofi-cafe.yaml` | Lo-fi cafe BGM with relaxed tempo and warm tones |
| `trajectory-example.yaml` | Example tension/density/predictability curves |

### v2 (rich)

| Template | Description |
|---|---|
| `v2/bgm-90sec-pop.yaml` | Pop BGM with emotion, melody, harmony, and production |
| `v2/cinematic-3min.yaml` | Full cinematic with 11-section v2 format |
| `v2/loopable-game-bgm.yaml` | Looping game music with loop-aware constraints |

---

## Project Structure

```
yao/
+-- CLAUDE.md                     # Development rules (v1.1)
+-- PROJECT.md                    # Full design documentation
+-- FEATURE_STATUS.md             # Single source of truth for capabilities
+-- VISION.md                     # Target architecture
+-- README.md                     # This file
+-- pyproject.toml                # Dependencies and config
+-- Makefile                      # Development commands
+-- .pre-commit-config.yaml       # Pre-commit hook configuration
+-- .github/workflows/ci.yml      # GitHub Actions CI
|
+-- src/
|   +-- yao/                      # Main library (89 Python files)
|   |   +-- conductor/            # Orchestration engine + critique integration
|   |   +-- constants/            # 38 instruments, 14 scales, 14 chords
|   |   +-- schema/               # Pydantic specs (v1 + v2)
|   |   +-- ir/                   # ScoreIR + DrumPattern + plan/ (CPIR)
|   |   +-- generators/           # rule_based, stochastic, drum_patterner, counter_melody, plan/, note/
|   |   +-- render/               # MIDI writer, stems, audio, iterations
|   |   +-- verify/               # Lint, eval, diff, constraints, critique/ (15 rules)
|   |   +-- reflect/              # Provenance, RecoverableDecision
|   |   +-- sketch/               # NL → spec compiler
|   |   +-- arrange/              # Arrangement engine (stub)
|   |   +-- perception/           # Aesthetic judgment (stub)
|   +-- cli/                      # Click CLI (11 commands)
|
+-- .claude/
|   +-- commands/                 # 7 slash commands
|   +-- agents/                   # 7 subagent definitions
|   +-- skills/                   # 11 domain skills (8 genres + 3 other)
|   +-- guides/                   # 7 development guides
|
+-- drum_patterns/                # 8 genre-specific drum pattern YAMLs
+-- specs/templates/              # 5 v1 + 3 v2 YAML templates
+-- gallery/                      # Pre-generated MIDI examples
+-- tests/                        # 643 tests
+-- tools/                        # Architecture lint, feature status check, skill sync
+-- docs/                         # mkdocs documentation
+-- development/                  # Developer reference docs
```

---

## Development

```bash
make install           # Install with dev dependencies
make setup-hooks       # Install pre-commit + pre-push hooks
make test              # Run all 643 tests
make test-unit         # Unit tests only
make test-golden       # Golden MIDI regression tests
make lint              # ruff + mypy strict
make format            # Auto-format
make arch-lint         # Layer boundary enforcement
make feature-status    # Verify FEATURE_STATUS.md matches code
make sync-skills       # Sync genre skill YAML from markdown front-matter
make all-checks        # lint + arch-lint + feature-status + test + golden
```

### Test Organization

| Directory | What it tests |
|---|---|
| `tests/unit/` | Individual modules: IR, schema, generators, render, verify, conductor, CPIR, critique rules, metric goals, drum patterner, counter-melody, preview/watch |
| `tests/integration/` | Full pipeline, v2 pipeline, silent-fallback checks |
| `tests/scenarios/` | Musical scenarios: tension arcs, trajectory compliance |
| `tests/music_constraints/` | Instrument range constraints (parameterized) |
| `tests/golden/` | Bit-exact MIDI regression against committed fixtures |

### Code Standards

- Python 3.11+, `from __future__ import annotations`
- mypy strict, ruff for linting (line length: 120)
- Pydantic for YAML specs, frozen dataclasses for IR
- Custom exceptions only (`YaOError` subclasses, never bare `ValueError`)
- Pre-commit hooks enforce formatting, lint, type checks, and architecture boundaries on every commit

### CI

GitHub Actions runs on every push and PR:
- **Lint & type check** (ruff + mypy)
- **Architecture lint** (layer boundary enforcement)
- **Tests** across Python 3.11, 3.12, 3.13
- **Golden MIDI regression** (bit-exact comparison)

---

## Design Philosophy

1. **The agent is an environment, not a composer** — YaO accelerates human creativity
2. **Every decision is explainable** — provenance records why each note exists
3. **Constraints liberate** — specs and rules are scaffolding, not cages
4. **Time-axis first** — trajectory curves define the arc; notes fill the details
5. **The human ear is the final truth** — automated scores inform; humans decide
6. **Incrementality** — do not break what works; extend each layer progressively

Full design: [PROJECT.md](PROJECT.md) | Development rules: [CLAUDE.md](CLAUDE.md) | Target architecture: [VISION.md](VISION.md) | Feature status: [FEATURE_STATUS.md](FEATURE_STATUS.md) | [Gallery](gallery/)

---

## License

MIT
