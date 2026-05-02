# You and Orchestra (YaO)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

Describe what you want in plain English, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to serve.

**What's implemented?** See [FEATURE_STATUS.md](FEATURE_STATUS.md) — the single source of truth for capabilities.

---

## Getting Started

### Install

```bash
git clone <repo-url>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-hooks  # Install pre-commit hooks
```

Requires **Python 3.11+**. Audio rendering requires [FluidSynth](#audio-rendering).

### Open in Claude Code

Launch Claude Code in the project directory to start composing:

```bash
claude
```

---

## Usage

All interaction happens through Claude Code slash commands. Describe your music, iterate on it, and render — all through conversation.

### `/sketch` — Create a composition from a description

Start here. Describe what you want and YaO guides you through spec creation.

```
> /sketch a calm piano piece in D minor for studying, 90 seconds
```

YaO will:
1. Propose key, tempo, instruments, sections, and dynamics
2. Suggest an emotional trajectory (tension/density arc)
3. Ask for adjustments
4. Write the spec files and validate them

Example prompts:

```
> /sketch a calm piano piece in D minor for studying, 90 seconds
> /sketch a mysterious puzzle game BGM, minimal and looping
> /sketch an epic orchestral piece in D minor, 3 minutes, cinematic
> /sketch a jazz trio improvisation in Bb major, relaxed swing feel
> /sketch upbeat 8-bit chiptune for a platformer game, 60 seconds, loopable
> /sketch a Mozart-style piano trio waltz in F major, 3/4 time, happy and elegant
> /sketch dark ambient drone for a horror game menu screen, slow and unsettling
> /sketch a bossa nova piece with acoustic guitar and flute, sunny afternoon vibe
> /sketch aggressive piano solo in C major, fast tempo like heavy metal energy
> /sketch lo-fi hip hop beat for a rainy cafe, piano and cello, 85 BPM
> /sketch a Celtic folk tune with violin and harp in G mixolydian, 120 BPM
> /sketch romantic string quartet in Ab major, slow waltz, Chopin-inspired
> /sketch anime opening theme, energetic J-pop style, 150 BPM, full orchestra
```

### `/compose <project>` — Generate music

Run the Conductor loop: generate, evaluate, critique, adapt, regenerate (up to 3 iterations).

```
> /compose my-song
```

Output:
```
=== Conductor Result ===
Quality Score: 7.2/10
Pass rate: 100% (10/10)
Duration: 90.0s | Bars: 30 | Notes: 112
Instruments: piano
Output: outputs/projects/my-song/iterations/v001/
```

### `/critique <project>` — Find weaknesses

Run adversarial critique rules against a composition. Finds every weakness — never praises.

```
> /critique my-song
```

Returns structured findings with severity (critical/major/minor), evidence, location, and recommendations.

### `/regenerate-section <project> <section>` — Fix a specific section

Re-generate one section while keeping the rest intact. Provide feedback on what to change.

```
> /regenerate-section my-song chorus
```

YaO will ask what should change (more energy, different melody, new seed, etc.) and create a new iteration with the merged result.

### `/render <project>` — Render to audio

Convert MIDI to WAV using SoundFont rendering.

```
> /render my-song
```

### `/explain <question>` — Trace decisions

Query the provenance log to understand why any musical decision was made.

```
> /explain why did the chorus use a V-vi deceptive cadence?
```

### `/arrange <project>` — Transform a composition

Apply style transfer to an existing composition while preserving selected elements.

```
> /arrange my-song --target-genre lofi_hiphop --preserve melody
```

---

## Typical Workflow

```
/sketch  -->  /compose  -->  /critique  -->  /regenerate-section  -->  /critique  -->  /render
```

1. **Sketch** — describe your idea, refine the spec interactively
2. **Compose** — generate with automatic quality evaluation
3. **Critique** — identify weaknesses
4. **Regenerate** — fix specific sections based on feedback
5. **Iterate** — repeat critique/regenerate until satisfied
6. **Render** — output to WAV audio

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

## 7 Subagents

Behind each slash command, specialized subagents collaborate:

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

## 32 Domain Skills

YaO draws on specialized musical knowledge:

| Category | Count | Examples |
|---|---|---|
| **Genres** | 22 | cinematic, lofi_hiphop, j_pop, jazz_swing, bossa_nova, synthwave, celtic, arab_maqam, blues, funk, baroque, romantic... |
| **Theory** | 4 | voice-leading, twelve-tone, microtonal, process-music |
| **Articulation** | 4 | piano-pedaling, jazz-microtiming, strings-articulation, winds-articulation |
| **Instruments** | 1 | piano |
| **Psychology** | 1 | tension-resolution |

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

## Generation Strategies

| Strategy | Description |
|---|---|
| **rule_based** | Deterministic. Same spec = same output. |
| **stochastic** | Seed + temperature. 4 contour algorithms, 5 chord voicings, 12 rhythm templates, walking bass, motif transformation. |
| **markov** | Probabilistic transitions from learned patterns. |
| **twelve_tone** | Serialist composition using tone rows. |
| **process_music** | Minimalist / generative process-based composition. |
| **constraint_solver** | Backtracking search with hard constraints. |

Additional generators: drum patterner (8 genres), counter-melody (species counterpoint), performance expression, neural bridge (texture generation).

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

Each rule emits structured `Finding` objects with severity, evidence, location, and recommendations.

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

## Constraint System

Define musical rules in your spec:

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
```

Place a `.sf2` SoundFont file in the `soundfonts/` directory, then use `/render` to generate WAV audio.

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
