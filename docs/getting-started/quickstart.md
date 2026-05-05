# Quick Start

Generate your first piece in under 2 minutes.

---

## Install

```bash
pip install -e ".[dev]"
```

Optional extras:
```bash
pip install -e ".[neural]"     # Stable Audio bridge
pip install -e ".[live]"       # Realtime improvisation
pip install -e ".[annotate]"   # A/B audition + annotation UI
```

---

## Option A: Interactive Sketch (Recommended)

Use the `/sketch` command in Claude Code for a guided 6-turn dialogue:

```
/sketch
> A melancholic piano piece with strings, about 90 seconds
```

The sketch dialogue asks about mood, instruments, structure, and constraints, then generates a complete YAML spec and composition.

---

## Option B: Natural Language

```bash
yao conduct "upbeat jazz trio, 2 minutes, swinging and playful"
```

The Conductor translates your description to a spec, generates a composition, evaluates it, and iterates up to 3 times.

Japanese is also supported:
```bash
yao conduct "雨の午後のような、メランコリックなピアノ曲、90秒"
```

---

## Option C: From YAML Spec

```bash
# Create a project skeleton
yao new-project my-piece

# Edit the generated spec, then compose
yao compose my-piece/composition.yaml
```

### Minimal spec structure:

```yaml
title: "My First Piece"
genre: "cinematic"
key: "C minor"
tempo_bpm: 100
time_signature: "4/4"
total_bars: 32
instruments:
  - name: piano
    role: melody
  - name: cello
    role: accompaniment
sections:
  - name: intro
    bars: 8
    dynamics: mp
  - name: main
    bars: 16
    dynamics: mf
  - name: outro
    bars: 8
    dynamics: p
generation:
  strategy: stochastic
  seed: 42
  temperature: 0.7
```

---

## Output Structure

After generation, your project contains:

```
outputs/projects/<name>/iterations/v001/
  full.mid              # Complete MIDI file
  stems/                # Per-instrument MIDI files
  analysis.json         # Structural analysis
  evaluation.json       # 6-dimension quality scores
  perceptual.json       # Audio perception report (if rendered)
  provenance.json       # Decision log (every note explained)
  critique.md           # Adversarial critique findings
  audio.wav             # Rendered audio (if --render-audio)
```

---

## Generation Strategies

| Strategy | Character |
|----------|-----------|
| `rule_based` | Deterministic, predictable |
| `stochastic` | Probabilistic, temperature-controlled |
| `markov` | N-gram patterns, style-aware |
| `twelve_tone` | Serial composition (P/I/R/RI) |
| `process_music` | Phasing, additive, subtractive |
| `constraint_solver` | CSP backtracking |
| `loop_evolution` | Loop-first, layer evolution |
| `ai_seed` | Motif generation from intent |

---

## Iterate and Refine

```bash
# Regenerate just the chorus
yao regenerate-section my-piece chorus --seed 99

# Pin feedback to a specific location
yao pin "verse:bar4:piano — too busy, simplify"

# Arrange an existing piece in a new style
/arrange my-piece/full.mid --style jazz_ballad

# Preview without saving to disk
yao preview my-spec.yaml

# Watch for spec changes and auto-regenerate
yao watch my-spec.yaml
```

---

## Next Steps

- [Spec Templates](templates.md) — pre-built starting points for common genres
- [Audio Setup](audio-setup.md) — render MIDI to WAV
- [CLI Reference](../guide/cli-reference.md) — all commands and options
- [Composition Specs](../guide/composition-spec.md) — full spec format reference
- [Claude Code Workflow](../tutorials/claude-code-workflow.md) — interactive session guide
