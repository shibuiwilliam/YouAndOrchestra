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
  ├── composition.yaml   # Your music specification
  └── intent.md          # Describe what the piece should feel like
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

```bash
yao compose specs/projects/my-first-song/composition.yaml
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
