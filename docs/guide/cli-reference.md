# CLI Reference

## Commands

### `yao conduct "<description>"`

Natural language to MIDI with automatic evaluate-adapt-regenerate loop.

| Option | Default | Description |
|--------|---------|-------------|
| `--spec` | — | Path to existing composition.yaml (alternative to description) |
| `-p, --project` | — | Project name for output directory |
| `-n, --iterations` | 3 | Maximum feedback-loop iterations |

When given a description, the Conductor parses mood keywords (e.g., "happy" -> C major, "dark" -> C minor), selects instruments from keywords (e.g., "orchestra", "piano", "jazz"), and builds a full spec automatically.

When given `--spec`, it runs the feedback loop on an existing spec, evaluating and adapting until all metrics pass or max iterations is reached.

### `yao compose <spec.yaml>`

Generate a composition from a YAML specification (single pass, no iteration).

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output-dir` | auto-versioned | Output directory |
| `-p, --project` | — | Project name |
| `-t, --trajectory` | — | Path to trajectory YAML |
| `--render-audio` | off | Render MIDI to WAV |
| `--soundfont` | auto-detect | Path to SoundFont |
| `--stems / --no-stems` | on | Per-instrument MIDI stems |

### `yao regenerate-section <project> <section>`

Regenerate a specific section while preserving the rest of the composition.

| Option | Default | Description |
|--------|---------|-------------|
| `--seed` | — | Seed override for regeneration |
| `-n, --iterations` | 3 | Maximum feedback-loop iterations |

Creates a new iteration with only the specified section regenerated and merged with existing content.

### `yao render <file.mid>`

Render a MIDI file to WAV audio. Requires FluidSynth.

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | same dir as MIDI | Output WAV path |
| `--soundfont` | auto-detect | Path to SoundFont |

### `yao validate <spec.yaml>`

Validate a composition spec without generating. Shows key, tempo, time signature, bars, instruments, and sections.

### `yao evaluate <project>`

Run quality evaluation on a project's latest iteration. Scores across structure, melody, and harmony.

### `yao diff <spec.yaml>`

Compare two stochastic generations of the same spec. Shows added, removed, and modified notes.

| Option | Default | Description |
|--------|---------|-------------|
| `--seed-a` | 1 | Seed for first generation |
| `--seed-b` | 2 | Seed for second generation |

### `yao explain <spec.yaml>`

Show provenance decisions for a composition.

| Option | Default | Description |
|--------|---------|-------------|
| `-q, --query` | — | Filter by operation name |

### `yao new-project <name>`

Create a new project skeleton under `specs/projects/` with a `composition.yaml` template and `intent.md` placeholder.

### `yao preview <spec.yaml>`

In-memory generation + FluidSynth synthesis + sounddevice playback. No file output -- instant audition.

| Option | Default | Description |
|--------|---------|-------------|
| `--soundfont` | auto-detect | Path to SoundFont |

### `yao watch <spec.yaml>`

File-watch mode: auto-regenerate and auto-play when spec files change. 500ms debounce.

| Option | Default | Description |
|--------|---------|-------------|
| `--soundfont` | auto-detect | Path to SoundFont |

### `yao rate <iteration_path>`

Interactive 5-dimension rating (memorability, emotional fit, technical quality, genre fitness, overall) plus free text. Saves a JSON rating file.

| Option | Default | Description |
|--------|---------|-------------|
| `--rater` | prompted | Rater identifier |

### `yao reflect ingest [ratings_dir]`

Aggregates rating JSON files into a `UserStyleProfile` with preferred ranges and confidence per dimension.

| Option | Default | Description |
|--------|---------|-------------|
| `--profile-path` | `user_style_profile.json` | Path to save/load profile |

### `yao critique <project>`

Run adversarial critique on the latest iteration of a project. Generates structured findings across all registered critique rules and writes `critique.md` to the iteration directory.

### `yao arrange <spec.yaml>`

Transform an existing piece using arrangement operations defined in an `arrangement.yaml` spec.

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output-dir` | auto-versioned | Output directory |

### `yao feedback apply <project>`

Apply human feedback from a `feedback.yaml` file to regenerate a composition.

| Option | Default | Description |
|--------|---------|-------------|
| `-f, --feedback` | — | Path to feedback.yaml file (required) |
| `-n, --max-iterations` | 3 | Max conductor iterations |

---

## Combination Stack Commands

### `yao reharmonize <midi_path>`

Apply reharmonization to an existing piece using the Reharmonization Engine.

| Option | Default | Description |
|--------|---------|-------------|
| `--intensity` | `0.3` | Probability of applying operations per chord (0.0-1.0) |
| `--style` | `common_practice` | Coupling style (common_practice, jazz, blues, modal) |
| `--preserve-melody` | `true` | Keep melody bit-identical |
| `--operations` | all | Comma-separated list of operations to use |

### `yao blend-genres <genres...>`

Generate using a blended genre profile.

```bash
yao blend-genres bossa_nova:0.6,drum_n_bass:0.4 --project my-blend
```

### `yao modulate <project> <bar> <to_key>`

Add a modulation at a specific bar.

```bash
yao modulate my-song 32 "F major" --strategy pivot_chord
```
