# Quick Start

## Install

```bash
git clone <repo-url>
cd yao
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires **Python 3.11+**.

## Create a Project

```bash
yao new-project my-first-song
```

This creates:
```
specs/projects/my-first-song/
  +-- composition.yaml   # Your music specification
  +-- intent.md          # Describe what the piece should feel like
```

## Edit the Spec

Open `specs/projects/my-first-song/composition.yaml`:

```yaml
title: My First Song
genre: ambient
key: C major
tempo_bpm: 120
time_signature: "4/4"

instruments:
  - name: piano
    role: melody

sections:
  - name: intro
    bars: 4
    dynamics: mp
  - name: verse
    bars: 8
    dynamics: mf
  - name: outro
    bars: 4
    dynamics: pp
```

## Generate

### Option A: Single pass

```bash
yao compose specs/projects/my-first-song/composition.yaml
```

### Option B: With automatic iteration (recommended)

```bash
yao conduct --spec specs/projects/my-first-song/composition.yaml --project my-first-song
```

The Conductor evaluates quality after generation and automatically adapts the spec if metrics fail, then regenerates until everything passes.

### Option C: From natural language (fastest)

```bash
yao conduct "a calm piano piece in C major, 16 bars, ambient"
```

Each run auto-creates a new iteration (`v001`, `v002`, ...) so you never lose previous versions.

## Listen

```bash
# Open MIDI in your default player
open outputs/projects/my-first-song/iterations/v001/full.mid

# Or render to WAV (requires FluidSynth)
yao render outputs/projects/my-first-song/iterations/v001/full.mid
```

## Try the Stochastic Generator

Add a `generation` section to get varied output:

```yaml
generation:
  strategy: stochastic
  seed: 42
  temperature: 0.7
```

Change the seed to get a different composition from the same spec.

## Fix One Section

If only one section needs improvement:

```bash
yao regenerate-section my-first-song verse --seed 99
```

This creates a new iteration with only the verse regenerated, keeping intro and outro intact.

## Next Steps

- [Templates](templates.md) — Start from a ready-made spec
- [Audio Setup](audio-setup.md) — Render MIDI to WAV with FluidSynth
- [CLI Reference](../guide/cli-reference.md) — All commands and options
- [Claude Code Workflow](../tutorials/claude-code-workflow.md) — Interactive music creation
