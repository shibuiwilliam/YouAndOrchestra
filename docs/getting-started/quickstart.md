# Quick Start

## Install

```bash
git clone https://github.com/shibuiwilliam/YouAndOrchestra
cd YouAndOrchestra
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires **Python 3.11+**.

## Three Ways to Get Started

### Option A: Interactive Sketch (recommended)

Launch Claude Code and start a conversation:

```bash
claude
> /sketch a calm piano piece in D minor for studying
```

The sketch dialogue walks you through 6 turns to refine your idea into a complete spec. Then:

```
> /compose my-piece
> /critique my-piece
> /render my-piece
```

### Option B: Natural Language (fastest)

```bash
yao conduct "a calm piano piece in C major, 16 bars, ambient"
```

The Conductor evaluates quality after generation and automatically adapts the spec if metrics fail, then regenerates until everything passes.

### Option C: From YAML Spec (full control)

Create a project:

```bash
yao new-project my-first-song
```

This creates:
```
specs/projects/my-first-song/
  +-- composition.yaml   # Your music specification
  +-- intent.md          # Describe what the piece should feel like
```

Edit `specs/projects/my-first-song/composition.yaml`:

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

Then generate:

```bash
# Single pass
yao compose specs/projects/my-first-song/composition.yaml

# With automatic iteration (recommended)
yao conduct --spec specs/projects/my-first-song/composition.yaml --project my-first-song
```

Each run auto-creates a new iteration (`v001`, `v002`, ...) so you never lose previous versions.

## Listen

```bash
# Open MIDI in your default player
open outputs/projects/my-first-song/iterations/v001/full.mid

# Or render to WAV (requires FluidSynth -- see Audio Setup)
yao render outputs/projects/my-first-song/iterations/v001/full.mid

# Or preview directly (in-memory, no file output)
yao preview specs/projects/my-first-song/composition.yaml
```

## What You Get

Each generation creates:

```
outputs/projects/my-first-song/iterations/v001/
  full.mid           # Complete MIDI score
  stems/             # Per-instrument MIDI stems
  analysis.json      # Quality analysis
  evaluation.json    # Quality scores (6 dimensions)
  perceptual.json    # Acoustic analysis
  provenance.json    # Decision log explaining every choice
```

## Try Different Generators

Add a `generation` section to get varied output:

```yaml
generation:
  strategy: stochastic    # rule_based, stochastic, markov, twelve_tone, process_music
  seed: 42                # change for different results
  temperature: 0.7        # 0.0=conservative, 1.0=adventurous
```

## Fix One Section

If only one section needs improvement:

```bash
yao regenerate-section my-first-song verse --seed 99
```

This creates a new iteration with only the verse regenerated, keeping intro and outro intact.

## Give Localized Feedback

Attach feedback to a specific location:

```
/pin my-first-song --location "section:verse,bar:5,instrument:piano" --note "melody is too busy here"
```

Or use natural language:

```
/feedback my-first-song "the chorus needs more energy"
```

## Arrange Into a New Style

Transform your piece into a different genre:

```
/arrange my-first-song --target-genre lofi_hiphop --preserve melody,form
```

## Next Steps

- [Templates](templates.md) -- Start from a ready-made spec
- [Audio Setup](audio-setup.md) -- Render MIDI to WAV with FluidSynth
- [CLI Reference](../guide/cli-reference.md) -- All commands and options
- [Composition Spec](../guide/composition-spec.md) -- YAML schema details (v1 + v2 + v3)
- [Claude Code Workflow](../tutorials/claude-code-workflow.md) -- Interactive music creation with subagents
