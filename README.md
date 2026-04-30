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
Pass rate: 100% (9/9)
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

YaO also supports a **v2 spec format** with 11 dedicated sections for finer control over emotion, melody, harmony, rhythm, drums, arrangement, and production. See [Composition Spec Guide](docs/guide/composition-spec.md) for details.

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
Spec  ->  Plan  ->  Generate  ->  Evaluate  ->  Pass?  ->  Done
                                     | No
                                Adapt spec  ->  Regenerate
```

It builds a Musical Plan (form + harmony), realizes it into notes, scores the result across 10 metrics in 3 dimensions (structure, melody, harmony), and adapts the spec if any metric fails. Each iteration is saved as a new version with full provenance.

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

Features: melodic contour shaping (arch, ascending, descending, wave), section-aware chord progressions, diatonic 7th chords, 12 rhythm templates, walking bass, velocity humanization, and motif transformation (transpose, invert, retrograde, augment, diminish).

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

Every composition is scored across 10 metrics in 3 dimensions, producing a quality score from 1.0 to 10.0:

| Dimension (weight) | Metrics |
|---|---|
| **Structure** (25%) | Section contrast, bar count accuracy, section count match, rhythm variety, syncopation ratio |
| **Melody** (30%) | Pitch range utilization, stepwise motion ratio, contour variety |
| **Harmony** (25%) | Pitch class variety, consonance ratio |

Each metric uses a typed `MetricGoal` (AT_LEAST, BETWEEN, TARGET_BAND, etc.) instead of a one-size-fits-all tolerance check.

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

- **38 instruments** across 9 families (keyboard, strings, guitar, bass, brass, woodwind, saxophone, synth, percussion)
- **14 scales** (major, minor, harmonic minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic, blues, whole tone, chromatic)
- **14 chord types** (major through major 9th, including sus2, sus4, add9)
- **Functional harmony** via Roman numeral notation (I, ii, V7/V) with `realize()` for concrete pitches
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations** (transpose, invert, retrograde, augment, diminish) tracked in provenance
- **12 section types** (intro, verse, pre-chorus, chorus, bridge, solo, interlude, breakdown, build, drop, outro, coda)

---

## Architecture

```
Conductor           — Orchestrates the generate-evaluate-adapt loop
Layer 6: Verify     — Evaluation, linting, diffing, constraints, MetricGoal
Layer 5: Render     — MIDI writer, stems, audio renderer, iteration management
Layer 3a: Plan IR   — Composition Plan IR (CPIR): SongFormPlan, HarmonyPlan
Layer 3b: Score IR  — ScoreIR, Note, harmony, motif, voicing, timing, notation
Layer 2: Generate   — Plan generators + Note realizers (rule-based, stochastic)
Layer 1: Schema     — Pydantic models for YAML specs (v1 + v2)
Layer 0: Constants  — Instrument ranges, MIDI maps, scales, chords, dynamics
```

The v2.0 pipeline: `Spec → PlanOrchestrator → MusicalPlan (CPIR) → NoteRealizer → ScoreIR → MIDI`

All IR objects are immutable frozen dataclasses. Layer boundaries are enforced by `make arch-lint`.

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

```bash
cp specs/templates/minimal.yaml specs/projects/my-song/composition.yaml
yao compose specs/projects/my-song/composition.yaml
```

---

## Development

```bash
make test              # All tests (~560)
make test-unit         # Unit tests only (~500)
make test-golden       # Golden MIDI regression tests (6)
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary enforcement
make matrix-check      # Capability Matrix vs. code consistency
make all-checks        # All of the above
make format            # Auto-format
```

### Test Organization

| Directory | Count | What it tests |
|---|---|---|
| `tests/unit/` | ~500 | Individual modules: IR, schema, generators, render, verify, conductor, CPIR, metric goals, critique rules |
| `tests/integration/` | ~15 | Full pipeline, v2 pipeline, silent-fallback checks |
| `tests/scenarios/` | ~16 | Musical scenarios: tension arcs, trajectory compliance |
| `tests/music_constraints/` | 7 | Instrument range constraints (parameterized) |
| `tests/golden/` | 6 | Bit-exact MIDI regression against committed fixtures |

### Code Standards

- Python 3.11+, `from __future__ import annotations`
- mypy strict, ruff for linting (line length: 99)
- Pydantic for YAML specs, frozen dataclasses for IR
- Custom exceptions only (`YaOError` subclasses, never bare `ValueError`)
- Conventional commits: `feat(harmony): add secondary dominant insertion`

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
