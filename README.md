# You and Orchestra (YaO)

[![CI](https://github.com/yao-project/yao/actions/workflows/ci.yml/badge.svg)](https://github.com/yao-project/yao/actions/workflows/ci.yml)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

Describe what you want in plain English or YAML, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to serve.

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
| `yao new-project <name>` | Create a project skeleton with template files |
| `yao validate <spec.yaml>` | Check a spec and display its details |
| `yao evaluate <project>` | Re-evaluate the latest iteration |
| `yao diff <spec.yaml>` | Compare two stochastic generations side by side |
| `yao explain <spec.yaml>` | Show provenance — why each decision was made |

---

## The Conductor

The Conductor automates the generate-evaluate-adapt loop:

```
Spec  →  Plan  →  Generate  →  Evaluate  →  Pass?  →  Done
                                    | No
                               Adapt spec  →  Regenerate
```

It builds a Composition Plan (form + harmony), realizes it into notes, scores the result across 10 metrics in 3 dimensions, and adapts the spec if any metric fails. Each iteration is saved as a new version with full provenance.

| Problem Detected | Adaptation |
|---|---|
| Low pitch variety | Increase temperature or switch to stochastic |
| Too many melodic leaps | Decrease temperature for smoother lines |
| Sections sound too similar | Differentiate dynamics across sections |
| Too dissonant | Reduce temperature for more consonant intervals |
| Melody too monotone | Increase temperature for more contour variety |

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
- **Velocity humanization** — dynamics-derived with trajectory tension modifier
- **Motif transformation** — transpose, invert, retrograde, augment, diminish
- **Configurable via `StochasticConfig`** — all tuning parameters extracted into a frozen dataclass

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

Five dimensions: tension, density, predictability, brightness, and register height. Three curve types: bezier, stepped, and linear.

---

## Quality Evaluation

Every composition is scored across 10 metrics in 3 dimensions, producing a **quality score from 1.0 to 10.0**:

| Dimension (weight) | Metrics |
|---|---|
| **Structure** (25%) | Section contrast, bar count accuracy, section count match, rhythm variety, syncopation ratio |
| **Melody** (30%) | Pitch range utilization, stepwise motion ratio, contour variety |
| **Harmony** (25%) | Pitch class variety, consonance ratio |

Each metric uses a typed `MetricGoal` (AT_LEAST, BETWEEN, TARGET_BAND, etc.) instead of a one-size-fits-all tolerance check.

---

## Adversarial Critique

YaO includes a **rule-based critique engine** with 12 structured rules across 5 categories:

| Category | Rules |
|---|---|
| **Structural** | Climax absence, section monotony, form imbalance |
| **Melodic** | Cliche motif, contour monotony, phrase closure weakness |
| **Harmonic** | Cliche progression, voice crossing, cadence weakness |
| **Rhythmic** | Rhythmic monotony |
| **Emotional** | Intent divergence, trajectory violation |

Each rule emits structured `Finding` objects with severity (critical/major/minor/suggestion), evidence, location, and recommendations — machine-actionable, not free text.

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

---

## Music Theory Built In

- **40 instruments** across 9 families (keyboard, strings, guitar, bass, brass, woodwind, saxophone, synth, percussion)
- **14 scales** (major, minor, harmonic minor, melodic minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic major/minor, blues, whole tone, chromatic)
- **14 chord types** (major through major 9th, including sus2, sus4, add9)
- **Functional harmony** via Roman numeral notation (I, ii, V7/V) with `realize()` for concrete pitches
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations** (transpose, invert, retrograde, augment, diminish) tracked in provenance
- **12 section types** (intro, verse, pre-chorus, chorus, bridge, solo, interlude, breakdown, build, drop, outro, coda)

---

## Architecture

```
Conductor           — Orchestrates the generate-evaluate-adapt loop
Layer 6: Verify     — Evaluation, linting, diffing, constraints, critique (12 rules)
Layer 5: Render     — MIDI writer, stems, audio renderer, iteration management
Layer 3a: Plan IR   — Composition Plan IR (CPIR): SongFormPlan, HarmonyPlan
Layer 3b: Score IR  — ScoreIR, Note, harmony, motif, voicing, timing, notation
Layer 2: Generate   — Plan generators + note realizers (rule-based, stochastic)
Layer 1: Schema     — Pydantic models for YAML specs (v1 + v2)
Layer 0: Constants  — 40 instruments, 14 scales, 14 chords, MIDI mappings
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
+-- CLAUDE.md                     # Development rules for Claude Code
+-- PROJECT.md                    # Full design documentation
+-- VISION.md                     # Target architecture
+-- README.md                     # This file
+-- pyproject.toml                # Dependencies and config
+-- Makefile                      # Development commands
+-- .pre-commit-config.yaml       # Pre-commit hook configuration
+-- .github/workflows/ci.yml      # GitHub Actions CI
|
+-- src/
|   +-- yao/                      # Main library (85 Python files)
|   |   +-- conductor/            # Orchestration engine
|   |   +-- constants/            # 40 instruments, 14 scales, 14 chords
|   |   +-- schema/               # Pydantic specs (v1 + v2)
|   |   +-- ir/                   # ScoreIR + plan/ (CPIR)
|   |   +-- generators/           # rule_based + stochastic + plan/ + note/
|   |   +-- render/               # MIDI writer, stems, audio, iterations
|   |   +-- verify/               # Lint, eval, diff, constraints, critique/
|   |   +-- reflect/              # Provenance, RecoverableDecision
|   |   +-- sketch/               # NL → spec compiler
|   |   +-- arrange/              # Arrangement engine (stub)
|   |   +-- perception/           # Aesthetic judgment (stub)
|   +-- cli/                      # Click CLI (9 commands)
|
+-- .claude/
|   +-- commands/                 # 7 slash commands
|   +-- agents/                   # 7 subagent definitions
|   +-- skills/                   # Domain knowledge (4 categories)
|   +-- guides/                   # 7 development guides
|
+-- specs/templates/              # 4 v1 + 3 v2 YAML templates
+-- gallery/                      # Pre-generated MIDI examples
+-- tests/                        # 576 tests
+-- tools/                        # Architecture lint, matrix check
+-- docs/                         # mkdocs documentation
+-- development/                  # Developer reference docs
```

---

## Development

```bash
make install           # Install with dev dependencies
make setup-hooks       # Install pre-commit + pre-push hooks
make test              # Run all 576 tests
make test-unit         # Unit tests only
make test-golden       # Golden MIDI regression tests
make lint              # ruff + mypy strict
make format            # Auto-format
make arch-lint         # Layer boundary enforcement
make matrix-check      # Capability Matrix vs. code consistency
make all-checks        # All of the above
```

### Test Organization

| Directory | What it tests |
|---|---|
| `tests/unit/` | Individual modules: IR, schema, generators, render, verify, conductor, CPIR, critique rules, metric goals |
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

Full design: [PROJECT.md](PROJECT.md) | Development rules: [CLAUDE.md](CLAUDE.md) | Target architecture: [VISION.md](VISION.md) | [Gallery](gallery/)

---

## License

MIT
