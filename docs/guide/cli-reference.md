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

### `yao rate <project>`

Interactive 5-dimension rating (memorability, emotional fit, technical quality, genre fitness, overall) plus free text. Saves a JSON rating file.

### `yao reflect ingest [ratings_dir]`

Aggregates rating JSON files into a `UserStyleProfile` with preferred ranges and confidence per dimension.

| Option | Default | Description |
|--------|---------|-------------|
| `--profile-path` | `user_style_profile.json` | Path to save/load profile |
