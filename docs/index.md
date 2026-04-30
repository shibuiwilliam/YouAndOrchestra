# YaO — You and Orchestra

**An agentic music production environment built on Claude Code.**

YaO turns music composition into a structured, reproducible engineering process. Describe what you want in plain English or YAML, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, and a provenance log explaining every decision.

> *Your vision. Your taste. Your soul. — and an Orchestra ready to serve.*

## What YaO Does

- **Natural language composition** — Describe music in plain English and the Conductor builds a spec, generates, evaluates, and iterates automatically
- **Spec-driven composition** — Describe your music in YAML (v1 flat format or v2 11-section format) and generate full MIDI scores with precise control
- **40 instruments** across 9 families — keyboard, strings, guitar, bass, brass, woodwind, saxophone, synth, percussion
- **Trajectory curves** — Shape tension, density, predictability, brightness, and register height over time
- **Two generator strategies** — Deterministic (rule-based) and stochastic (seed + temperature, 4 contour algorithms, 5 chord voicing types)
- **Quality evaluation** — 10 metrics across 3 dimensions with user-facing quality score (1.0-10.0) and MetricGoal-typed pass/fail
- **Adversarial critique** — 12 structured rules across 5 categories emitting machine-actionable `Finding` objects
- **Music linting** — Catches range violations, parallel fifths, velocity issues
- **Constraint system** — Musical rules scoped to sections, instruments, or bar ranges
- **Provenance tracking** — Every note has a recorded rationale; fallbacks tracked via RecoverableDecision
- **Per-instrument stems** — Individual MIDI files per instrument
- **Section regeneration** — Regenerate one section while keeping the rest intact
- **Score diffing** — Compare two generations to see exactly what changed musically
- **MIDI reader** — Load existing MIDI files back into ScoreIR for analysis and iteration
- **Claude Code integration** — 7 slash commands, 7 subagents, 4 domain skills for interactive workflow
- **~576 tests** — Unit, integration, scenario, constraint, golden regression, and subagent eval tests
- **CI/CD** — GitHub Actions + pre-commit hooks (ruff, mypy, arch-lint)

## Architecture (v2.0)

YaO v2.0 introduces the **Composition Plan IR (CPIR)** as a middle layer. The generation pipeline is now:

```
CompositionSpec → Plan Generators → MusicalPlan → Note Realizers → ScoreIR → MIDI
```

This separates *what to play* (the plan) from *how to play it* (the notes), enabling richer critique, better iteration, and more musical output.

## Quick Example

```bash
# Natural language (fastest)
yao conduct "a calm piano piece in D minor for studying, 90 seconds"

# From a spec (full control)
yao compose specs/templates/bgm-90sec.yaml
```

This generates:
```
outputs/projects/<name>/iterations/v001/
  +-- full.mid           # Complete MIDI score
  +-- stems/piano.mid    # Per-instrument stems
  +-- stems/acoustic_bass.mid
  +-- analysis.json      # Quality analysis
  +-- evaluation.json    # Quality scores with pass/fail
  +-- provenance.json    # Decision log
```

## Design Philosophy

1. **Agent = environment, not composer** — YaO accelerates human creativity, it doesn't replace it
2. **Explain everything** — Every note has a provenance record with a rationale
3. **Constraints liberate** — YAML specs and music theory rules are scaffolds, not cages
4. **Time-axis first** — Design trajectory curves before writing notes
5. **Human ear is truth** — Automated scores inform, humans decide
6. **Vertical alignment** — Input expressiveness, processing depth, and evaluation resolution advance together

## Documentation

### Getting Started
- [Quick Start](getting-started/quickstart.md) — Install and generate your first piece
- [Templates](getting-started/templates.md) — Ready-to-use spec templates
- [Audio Setup](getting-started/audio-setup.md) — FluidSynth installation for WAV rendering

### User Guide
- [CLI Reference](guide/cli-reference.md) — All commands and options
- [Composition Spec](guide/composition-spec.md) — YAML schema reference (v1 + v2)
- [Trajectories](guide/trajectories.md) — Time-axis curves for emotion shaping
- [Constraints](guide/constraints.md) — Musical rule system

### Tutorials
- [Claude Code Workflow](tutorials/claude-code-workflow.md) — Interactive music creation with subagents

### Architecture
- [Layer Model](architecture/layers.md) — Layered architecture with Layer 3a (CPIR)
- [Design Decisions](architecture/decisions.md) — Architecture decision records

### Reference
- [Glossary](glossary.md) — YaO terminology (including v2.0 terms)
- [Provenance Schema](provenance-schema.md) — Decision log format with RecoverableDecision
- [Instruments](reference/instruments.md) — 40 instruments with MIDI ranges
- [Music Theory](reference/music-theory.md) — Scales, chords, dynamics

### Migration
- [v2 Baseline Report](migration/v2-baseline-report.md) — Gap analysis for v2.0 architecture
- [Silent Fallback Inventory](migration/silent-fallback-inventory.md) — RecoverableDecision conversion sites
