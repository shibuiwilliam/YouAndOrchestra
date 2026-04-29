# You and Orchestra (YaO)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

YaO turns music composition into a structured, reproducible engineering process. Describe what you want in plain English or YAML, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to serve.

---

## What Makes YaO Different

| Traditional AI Music Tools | YaO |
|---|---|
| Black-box input/output | Transparent, layered pipeline with full provenance |
| One generation, take it or leave it | Automatic evaluate-adapt-regenerate loop |
| No explanation of choices | Every note has a record explaining *why* |
| Fixed output | Same spec + different seed = different composition |
| No quality control | Automated evaluation across structure, melody, and harmony |
| CLI only | Deep Claude Code integration with slash commands and 7 subagents |

---

## Three Ways to Use YaO

### 1. Natural language (fastest)

```bash
yao conduct "a calm piano piece in D minor for studying, 90 seconds"
```

YaO parses your description, picks the key, tempo, instruments, and sections, generates a composition, evaluates it, and automatically adapts and regenerates until quality metrics pass.

```
=== Conductor Result ===
Iterations: 2
Pass rate: 100%
Duration: 90.0s | Bars: 30 | Notes: 112
Instruments: piano
Output: outputs/projects/a-calm-piano-piece-in-d-minor/iterations/v002/
```

### 2. YAML specification (full control)

```bash
yao compose specs/projects/my-song/composition.yaml
```

Write a spec with precise control over every parameter:

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

### 3. Claude Code (interactive, recommended)

Launch Claude Code inside the YaO directory and use slash commands:

```
> /sketch a mysterious puzzle game BGM, minimal and looping
```

Claude Code will guide you through spec creation interactively, generate the music, critique it, and iterate based on your feedback. This is the most powerful way to use YaO — see [Using YaO with Claude Code](#using-yao-with-claude-code) for full details.

---

## Install

```bash
git clone <repo-url>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires **Python 3.11+**. Audio rendering (optional) requires [FluidSynth](#audio-rendering).

### Core dependencies

| Package | Purpose |
|---|---|
| `pretty-midi` | MIDI representation and I/O |
| `music21` | Music notation and analysis |
| `librosa` | Audio feature extraction |
| `pydantic` | YAML spec validation (v2) |
| `pyloudnorm` | Loudness normalization (LUFS) |
| `click` | CLI framework |
| `numpy` / `scipy` | Numerical and scientific computing |
| `structlog` | Structured logging |

---

## Quick Start

```bash
# Create a project
yao new-project my-first-song

# Edit the spec
# -> specs/projects/my-first-song/composition.yaml

# Generate (single pass)
yao compose specs/projects/my-first-song/composition.yaml

# Or generate with automatic iteration (recommended)
yao conduct --spec specs/projects/my-first-song/composition.yaml --project my-first-song

# Listen
open outputs/projects/my-first-song/iterations/v001/full.mid

# Render to WAV (requires FluidSynth)
yao render outputs/projects/my-first-song/iterations/v001/full.mid
```

Each run creates a new iteration (`v001`, `v002`, ...), so you never lose previous versions.

---

## CLI Reference

| Command | What it does |
|---|---|
| `yao conduct "<description>"` | Natural language to MIDI with automatic evaluate-adapt-regenerate loop |
| `yao conduct --spec <yaml>` | Run the Conductor loop on an existing YAML spec |
| `yao compose <spec.yaml>` | Generate from YAML spec (single pass, no iteration) |
| `yao regenerate-section <project> <section>` | Regenerate one section, preserve the rest |
| `yao render <file.mid>` | Render MIDI to WAV audio |
| `yao new-project <name>` | Create a new project skeleton with `composition.yaml` and `intent.md` |
| `yao validate <spec.yaml>` | Check a spec and display its details without generating |
| `yao evaluate <project>` | Re-evaluate the latest iteration of a project |
| `yao diff <spec.yaml>` | Compare two stochastic generations side by side |
| `yao explain <spec.yaml>` | Show provenance — why each decision was made |

### Key Options

```bash
# Conduct with more iterations
yao conduct "a jazz ballad" --iterations 5

# Conduct from an existing spec
yao conduct --spec my-spec.yaml --project my-song

# Compose with trajectory shaping
yao compose my-spec.yaml --trajectory trajectory.yaml

# Compose with audio rendering
yao compose my-spec.yaml --render-audio --soundfont soundfonts/FluidR3_GM.sf2

# Compose with per-instrument stems (on by default)
yao compose my-spec.yaml --stems

# Regenerate just the bridge, with a new seed
yao regenerate-section my-song bridge --seed 99

# Compare two seeds
yao diff my-spec.yaml --seed-a 42 --seed-b 99

# Explain a specific aspect
yao explain my-spec.yaml --query melody
```

---

## The Conductor

The Conductor is YaO's agentic orchestration engine. It automates the generate-evaluate-adapt loop:

```
Description/Spec -> Generate -> Evaluate -> Pass? -> Done
                                   | No
                               Adapt spec -> Regenerate
                                   ^              |
                                   +--------------+
```

When you use `yao conduct` with a natural language description, the Conductor:

1. **Parses** mood keywords to choose key, tempo, and instruments (e.g., "happy" -> C major, "dark" -> C minor, "orchestra" -> strings + french horn + cello + piano)
2. **Generates** a composition via the selected generator strategy
3. **Evaluates** quality across structure, melody, and harmony metrics
4. **Adapts** the spec if metrics fail, then regenerates

| Problem Detected | Adaptation |
|---|---|
| Low pitch variety | Increase temperature or switch to stochastic |
| Too many melodic leaps | Decrease temperature for smoother lines |
| Sections sound too similar | Differentiate dynamics across sections |
| Too dissonant | Reduce temperature for more consonant intervals |
| Melody too monotone | Increase temperature for more contour variety |

Each iteration is saved separately (`v001`, `v002`, ...) with full provenance, so you can trace exactly what changed and why.

---

## Using YaO with Claude Code

YaO is designed for deep integration with Claude Code. Launch Claude Code in the YaO directory and use these slash commands:

### `/sketch` — Interactive spec creation

```
> /sketch a mysterious puzzle game BGM, minimal and looping
```

Claude Code will guide you through:
1. Clarifying the mood, emotion, and context
2. Proposing key, tempo, instruments, and section structure
3. Designing a trajectory (tension/density curves over time)
4. Validating the final spec before saving
5. Generating the first iteration with the Conductor

### `/compose` — Generate with the Conductor

```
> /compose my-puzzle-bgm
> /compose "an epic orchestral piece, dramatic, 2 minutes"
```

Generates the composition using the Conductor's automatic iteration loop. Shows a full summary including evaluation scores, iteration count, and output paths.

### `/critique` — Adversarial feedback

```
> /critique my-puzzle-bgm
```

The Adversarial Critic subagent examines the latest iteration and **finds every weakness** — it never praises. It rates issues by severity (critical / major / minor / suggestion) and writes a `critique.md` to the iteration directory. Categories examined:

- Structural weaknesses (predictability, lack of contrast)
- Melodic issues (range, contour, memorability)
- Harmonic problems (voice leading, function, cliches)
- Rhythmic concerns (groove, monotony, humanization)
- Emotional alignment with intent

### `/explain` — Trace any decision

```
> /explain why is there an F# in bar 12 of my-puzzle-bgm?
```

Queries the provenance log to show the chain of decisions that led to a specific note, chord, or structural choice.

### `/regenerate-section` — Fix one section

```
> /regenerate-section my-puzzle-bgm bridge
```

Regenerates only the specified section while keeping everything else intact. Creates a new iteration and shows a diff of changes.

### `/arrange` — Transform an existing composition

```
> /arrange my-puzzle-bgm --style jazz
```

Applies transformations like reharmonization, regrooving, reorchestration, or style transfer to an existing piece. *(Arrangement engine is planned for Phase 2.)*

### `/render` — MIDI to audio

```
> /render my-puzzle-bgm
```

Renders the latest iteration to WAV audio using FluidSynth.

### Free-form conversation

You don't have to use slash commands. Just describe what you want:

```
> I want to create background music for a rainy cafe scene.
  Something with piano and cello, a bit melancholy but not depressing.
  About 90 seconds.
```

Claude Code will create the project, write the spec, generate the music, and present the results — using the subagents as needed.

### The Orchestra: 7 Subagents

Behind the scenes, Claude Code can invoke specialized subagents, each with defined expertise:

| Subagent | Role |
|---|---|
| **Producer** | Coordinates all subagents, resolves conflicts, makes final decisions. The only one who can override others. |
| **Composer** | Generates melodies, motifs, themes, and structural outlines |
| **Harmony Theorist** | Designs chord progressions, modulations, cadences, reharmonization |
| **Rhythm Architect** | Creates drum patterns, grooves, syncopation, fills |
| **Orchestrator** | Assigns instruments, voicings, frequency spacing, countermelodies |
| **Mix Engineer** | Manages stereo placement, dynamics, frequency balance, loudness (LUFS) |
| **Adversarial Critic** | Finds weaknesses — never praises. Rates severity, proposes improvements. |

The Producer subagent acts as the concertmaster, coordinating the others and ensuring the final output aligns with the composer's (your) intent.

---

## Generation Strategies

Specify the strategy in your YAML spec or let the Conductor choose:

### Rule-Based (deterministic)

```yaml
generation:
  strategy: rule_based
```

Same spec always produces the same output. Scale-based melodies, I-IV-V-I chord progressions, root-note bass. Good for predictable baselines and golden tests.

### Stochastic (controlled randomness)

```yaml
generation:
  strategy: stochastic
  seed: 42          # same seed = same output (reproducible)
  temperature: 0.5  # 0.0 = conservative, 1.0 = adventurous
```

- **Melodic contour shaping** — arch, ascending, descending, wave patterns
- **Section-aware chord progressions** — different patterns for verse, chorus, bridge, intro, outro
- **Diatonic 7th chords** — maj7, min7, dom7 for richer harmony
- **12 rhythm templates** — syncopation, dotted rhythms, mixed patterns
- **Walking bass** — quarter-note patterns with passing tones and approach notes
- **Velocity humanization** — dynamics derived from section markings and trajectory curves

Change the seed to get a completely different composition from the same spec. New generators (Markov chains, constraint solvers) are planned.

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

Values range from 0.0 to 1.0. Higher tension drives louder dynamics. Higher density means more notes. Three curve types:

- **bezier** — Smooth curves through waypoints `[bar, value]`
- **stepped** — Flat values per named section
- **linear** — Interpolation toward a target with allowed variance

```bash
yao compose my-spec.yaml --trajectory specs/templates/trajectory-example.yaml
```

---

## Constraint System

Define musical rules scoped to sections, instruments, or bar ranges:

```yaml
constraints:
  - type: must_not
    rule: parallel_fifths
    scope: global
    severity: error
  - type: must_not
    rule: "note_above:C6"
    scope: "instrument:piano"
    severity: warning
  - type: prefer
    rule: "max_density:4"
    scope: "section:intro"
    severity: hint
  - type: must
    rule: "min_rest_ratio:0.2"
    scope: "section:bridge"
    severity: warning
```

| Constraint Type | Behavior |
|---|---|
| `must` | Required — violation is an error |
| `must_not` | Forbidden — presence is an error |
| `prefer` | Soft preference — violation is a hint |
| `avoid` | Soft avoidance — presence is a hint |

Scopes: `global`, `section:<name>`, `instrument:<name>`, `bars:<start>-<end>`

---

## Score Diffing

Compare two generations to see exactly what changed musically:

```bash
yao diff my-spec.yaml --seed-a 42 --seed-b 99
```

Shows added, removed, and **modified** notes with details like "pitch E6 -> A5 (down 7 semitones)" and "velocity 96 -> 64". Also detects section structure, tempo, and key changes.

---

## Quality Evaluation

Every composition is automatically scored across five dimensions:

| Dimension | Metrics |
|---|---|
| **Structure** | Bar count accuracy, section count match, section contrast |
| **Melody** | Pitch range utilization, stepwise motion ratio, contour variety |
| **Harmony** | Pitch class variety, consonance ratio |
| **Arrangement** | Instrument balance, texture density |
| **Acoustics** | Loudness, frequency balance |

Scores are 0.0-1.0 with pass/fail thresholds. The Conductor uses these scores to decide whether to iterate.

```bash
yao evaluate my-project
```

---

## What YaO Generates

Each iteration produces:

```
outputs/projects/<name>/iterations/v001/
  +-- full.mid           # Complete MIDI score (all instruments)
  +-- stems/             # Per-instrument MIDI files
  |   +-- piano.mid
  |   +-- cello.mid
  |   +-- ...
  +-- analysis.json      # Note counts, pitch ranges, duration, lint results
  +-- evaluation.json    # Quality scores across structure/melody/harmony
  +-- provenance.json    # Decision log with rationale for every choice
  +-- critique.md        # Adversarial critique (if /critique was run)
  +-- audio.wav          # Rendered audio (if --render-audio or /render was used)
```

---

## Spec Templates

YaO ships with ready-to-use templates in `specs/templates/`:

| Template | Description |
|---|---|
| `minimal.yaml` | 8-bar solo piano in C major at 120 BPM — the simplest possible spec |
| `bgm-90sec.yaml` | 90-second BGM with piano and acoustic bass, 4 sections (intro/verse/chorus/outro), dynamic arc |
| `cinematic-3min.yaml` | 3-minute orchestral piece in D minor with strings, piano, cello, and french horn across 6 sections |
| `trajectory-example.yaml` | Example tension/density/predictability curves with bezier, stepped, and linear types |

```bash
# Start from a template
cp specs/templates/cinematic-3min.yaml specs/projects/my-movie-score/composition.yaml
```

YaO also ships with 7 example projects in `specs/projects/` covering styles from classical piano trio to hard rock game BGM.

---

## Music Theory Built In

### 38 Instruments Across 9 Families

| Family | Instruments |
|---|---|
| **Keyboard** | piano, electric_piano, harpsichord, celesta, organ |
| **Strings** | violin, viola, cello, contrabass, harp, strings_ensemble |
| **Guitar** | acoustic_guitar_nylon, acoustic_guitar_steel, electric_guitar_clean |
| **Bass** | acoustic_bass, electric_bass_finger, electric_bass_pick, synth_bass |
| **Brass** | trumpet, trombone, tuba, french_horn |
| **Woodwind** | flute, piccolo, oboe, clarinet, bassoon |
| **Saxophone** | alto_sax, tenor_sax, baritone_sax |
| **Synth** | synth_lead_square, synth_lead_saw, synth_pad_warm |
| **Percussion** | timpani, vibraphone, marimba, xylophone, glockenspiel |

Each instrument has a defined MIDI note range and General MIDI program number. YaO raises a `RangeViolationError` (never silently clamps) if a note falls outside the playable range, with a helpful message suggesting how to fix it.

### 14 Scales

Major, natural minor, harmonic minor, melodic minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic major, pentatonic minor, blues, whole tone, chromatic

### 14 Chord Types

Major, minor, diminished, augmented, major 7th, minor 7th, dominant 7th, diminished 7th, half-diminished 7th, sus2, sus4, add9, minor 9th, major 9th

### Functional Harmony

Chords are described using Roman numeral notation (I, ii, V7/V) and realized to concrete pitches via `realize()`. This separates harmonic *function* from specific *voicing*, enabling reharmonization and transposition.

### Voice Leading

Parallel fifths and octaves detection, voice distance measurement for smooth progressions. All checked via the `voicing` module.

### Motif Transformations

Transpose, invert, retrograde, augment, diminish — all tracked in provenance so you can trace how a theme evolved across the piece.

### Dynamics

`ppp` (16) -> `pp` (33) -> `p` (49) -> `mp` (64) -> `mf` (80) -> `f` (96) -> `ff` (112) -> `fff` (127)

### 12 Section Types

intro, verse, pre-chorus, chorus, bridge, solo, interlude, breakdown, build, drop, outro, coda

---

## Audio Rendering

Optional. Requires FluidSynth and a General MIDI SoundFont:

```bash
# macOS
brew install fluid-synth

# Linux
sudo apt-get install fluidsynth

# Download FluidR3_GM (~140 MB) and place it in soundfonts/
# See soundfonts/README.md for detailed instructions

# Render
yao render outputs/projects/my-song/iterations/v001/full.mid
```

YaO auto-detects SoundFont files in the `soundfonts/` directory.

---

## Architecture

YaO follows a strict 7-layer architecture. Each layer can only depend on layers below it, enforced by an AST-based linter (`make arch-lint`):

```
Conductor         -- Orchestrates the full generate-evaluate-adapt pipeline
  |
Layer 6: Verify   -- Linting, analysis, evaluation, diffing, constraints
Layer 5: Render   -- MIDI writing, stems, audio rendering, iteration management
Layer 4: Percept  -- Aesthetic judgment substitutes (planned)
Layer 2: Generate -- Pluggable generators (rule-based, stochastic)
Layer 1: Spec/IR  -- YAML parsing, Pydantic models, ScoreIR, harmony, motif, voicing, timing, provenance
Layer 0: Consts   -- Instrument ranges, MIDI mappings, scales, chords, dynamics
```

Key data types flow through the system:

- **`CompositionSpec`** (Pydantic) — validated YAML input
- **`ScoreIR`** (frozen dataclass) — the central intermediate representation containing `Section` -> `Part` -> `Note`
- **`ProvenanceLog`** (append-only) — every generation decision with timestamp, parameters, and rationale
- **`EvaluationReport`** — quality scores that drive the Conductor's feedback loop

All IR objects are immutable (frozen dataclasses). All timing conversions go through `ir.timing`. All pitch conversions go through `ir.notation`.

---

## Project Structure

```
yao/
+-- CLAUDE.md                     # Development rules for Claude Code
+-- PROJECT.md                    # Full design documentation
+-- pyproject.toml                # Dependencies and tool config
+-- Makefile                      # Development commands
|
+-- src/
|   +-- yao/
|   |   +-- conductor/            # Agentic orchestration engine
|   |   |   +-- conductor.py      #   Compose from description or spec with auto-iteration
|   |   |   +-- feedback.py       #   Evaluation-driven spec adaptation
|   |   |   +-- result.py         #   Structured output with iteration history
|   |   +-- constants/            # Instrument ranges, MIDI maps, scales, chords
|   |   +-- schema/               # Pydantic models (composition, trajectory, constraints,
|   |   |                         #   negative space, references, production)
|   |   +-- ir/                   # ScoreIR, Note, harmony, motif, voicing, timing, notation
|   |   +-- generators/           # Rule-based + stochastic, pluggable registry
|   |   +-- perception/           # Aesthetic judgment substitutes (planned)
|   |   +-- render/               # MIDI writer, stem export, audio renderer, iteration mgmt
|   |   +-- verify/               # Lint, analysis, evaluation, diff, constraint checker
|   |   +-- reflect/              # Provenance logging with query and explain
|   |   +-- errors.py             # Custom exception hierarchy (YaOError base)
|   |   +-- types.py              # Domain type aliases (MidiNote, Beat, Velocity, Tick, etc.)
|   +-- cli/                      # Click CLI (conduct, compose, render, diff, evaluate, explain)
|
+-- .claude/
|   +-- commands/                 # Claude Code slash commands (7)
|   +-- agents/                   # Subagent definitions (7)
|   +-- guides/                   # Developer guides (architecture, coding, music, testing, workflow)
|
+-- specs/
|   +-- templates/                # Ready-to-use YAML templates (4)
|   +-- projects/                 # Your compositions (7 examples included)
|
+-- outputs/                      # Generated MIDI, audio, analysis (git-ignored)
+-- soundfonts/                   # SoundFont files for audio rendering
+-- tests/                        # 226 tests across unit, integration, scenario, constraint
+-- tools/                        # Architecture lint (layer boundary enforcement)
+-- docs/                         # Design docs, reference, tutorials
```

---

## Development

```bash
make install        # Install with dev dependencies
make test           # Run all 226 tests
make test-unit      # Unit tests only (207 tests)
make test-integration  # Full pipeline tests
make test-music     # Music constraint tests (instrument ranges, voice leading)
make lint           # ruff + mypy (strict)
make format         # Auto-format code
make arch-lint      # Layer boundary enforcement (AST-based)
make all-checks     # lint + arch-lint + test
```

### Test Organization

| Directory | Tests | Purpose |
|---|---|---|
| `tests/unit/` | 207 | Individual modules — IR, schema, generators, render, verify, conductor, harmony, motif, voicing, evaluator, constraints, diff, feedback, errors |
| `tests/integration/` | 2 | Full spec -> MIDI -> analysis -> evaluation pipeline |
| `tests/music_constraints/` | 7 | Instrument range constraints (parameterized across instruments) |
| `tests/scenarios/` | 10 | Musical scenarios — tension arcs create climax, different specs produce different music, genre-specific tests |

### Test Helpers

```python
from tests.helpers import assert_in_range, assert_no_parallel_fifths, assert_trajectory_match
```

- `assert_in_range(notes, instrument)` — verifies all notes within the instrument's playable range
- `assert_no_parallel_fifths(voicings)` — detects parallel perfect fifths in voice leading
- `assert_trajectory_match(score, trajectory, dimension, tolerance)` — validates dynamics match trajectory curves

### Code Standards

- **Python 3.11+** with `from __future__ import annotations`
- **mypy strict** — all public functions have type hints and docstrings
- **ruff** for linting and formatting (line length: 99)
- **Pydantic** for external data (YAML specs), **frozen dataclasses** for internal domain objects
- **Custom exceptions only** — no bare `ValueError`; use `YaOError` subclasses
- **Conventional Commits** — `feat(harmony): add secondary dominant insertion`

---

## Design Philosophy

1. **The agent is an environment, not a composer** — YaO accelerates human creativity; it doesn't replace it
2. **Every decision is explainable** — provenance records why each note exists
3. **Constraints liberate** — specs and theory rules are scaffolding, not cages
4. **Time-axis first** — trajectory curves define the arc; notes fill the details
5. **The human ear is the final truth** — automated scores inform; humans decide

Full design: [PROJECT.md](PROJECT.md) | Development rules: [CLAUDE.md](CLAUDE.md) | Documentation: [docs/](docs/)

---

## License

MIT
