# CLI Reference

## Commands

### `yao compose <spec.yaml>`

Generate a composition from a YAML specification.

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output-dir` | auto-versioned | Output directory |
| `-p, --project` | — | Project name |
| `-t, --trajectory` | — | Path to trajectory YAML |
| `--render-audio` | off | Render MIDI to WAV |
| `--soundfont` | auto-detect | Path to SoundFont |
| `--stems / --no-stems` | on | Per-instrument MIDI stems |

### `yao render <file.mid>`

Render a MIDI file to WAV audio.

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | same dir as MIDI | Output WAV path |
| `--soundfont` | auto-detect | Path to SoundFont |

### `yao validate <spec.yaml>`

Validate a composition spec without generating.

### `yao evaluate <project>`

Run quality evaluation on a project's latest iteration.

### `yao diff <spec.yaml>`

Compare two stochastic generations of the same spec.

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

Create a new project skeleton under `specs/projects/`.
