# YaO — You and Orchestra

**An agentic music production environment built on Claude Code.**

YaO turns music composition into a structured, reproducible process. Describe what you want in plain language (English or Japanese), and YaO generates a full MIDI score with per-instrument stems, quality evaluation, aesthetic analysis, and a provenance log explaining every decision.

> *Your vision. Your taste. Your soul. — and an Orchestra ready to serve.*

## What YaO Does

- **Multi-turn sketch dialogue** — 6-turn interactive conversation refines your idea into a complete spec
- **Natural language composition** — English and Japanese input with 3-stage fallback (LLM → Keyword → Default)
- **Spec-driven composition** — YAML specs (v1 flat or v2 11-section) with precise control
- **V2 Pipeline** — 7-step plan-first generation (Form → Harmony → Motif → Drums → Arrangement → Realization)
- **4 Note Realizers** — rule_based_v2 and stochastic_v2 consume 100% of the MusicalPlan directly
- **38 instruments** across 9 families with register-aware orchestration
- **Trajectory curves** — Shape tension, density, predictability, brightness, register height
- **6-dimension evaluation** — Structure, melody, harmony, aesthetic, arrangement, acoustics
- **4 aesthetic metrics** — Surprise (bigram NLL), memorability, contrast, pacing
- **20 adversarial critique rules** — Structured findings with severity and remediation
- **5 ensemble constraints** — Register separation, downbeat consonance, parallel octave detection
- **StyleVector** — 10 copyright-safe abstract features for style comparison
- **Provenance tracking** — Every note has a recorded rationale
- **7 subagents** — Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Critic, Producer
- **LLM backend** — AnthropicAPIBackend with structured output (tool use), or PythonOnly for CI
- **~1,150 tests** — Unit, integration, scenario, constraint, golden, aesthetic, subjective
- **5 honesty tools** — CI verification that features actually work (not just exist)

## Architecture (v3.0)

```
Spec → PlanOrchestrator → MusicalPlan → Critic Gate → NoteRealizer V2 → Performance → Renderer
```

8 layers with strict downward-only dependency. Plan-first generation separates *what to play* from *how to play it*.

## Quick Example

```bash
# Interactive (recommended)
/sketch a calm piano piece in D minor for studying

# Natural language (one-shot)
yao conduct "a calm piano piece in D minor for studying, 90 seconds"

# From spec (full control)
yao compose specs/templates/bgm-90sec.yaml
```

Output:
```
outputs/projects/<name>/iterations/v001/
  full.mid           # Complete MIDI score
  stems/piano.mid    # Per-instrument stems
  analysis.json      # Quality analysis
  evaluation.json    # Quality scores (6 dimensions)
  provenance.json    # Decision log
```

## Design Philosophy

1. **Agent = environment, not composer** — YaO accelerates human creativity
2. **Explain everything** — Every note has a provenance record
3. **Constraints liberate** — Specs and rules are scaffolds, not cages
4. **Time-axis first** — Trajectory curves before notes
5. **Human ear is truth** — Automated scores inform; humans decide
6. **Vertical alignment** — Input, processing, evaluation advance together
7. **Status honesty** — A ✅ means it actually works

## Documentation

### Getting Started
- [Quick Start](getting-started/quickstart.md) — Install and generate your first piece
- [Templates](getting-started/templates.md) — Ready-to-use spec templates
- [Audio Setup](getting-started/audio-setup.md) — FluidSynth installation

### User Guide
- [CLI Reference](guide/cli-reference.md) — All commands and options
- [Composition Spec](guide/composition-spec.md) — YAML schema (v1 + v2)
- [Trajectories](guide/trajectories.md) — Emotion-shaping curves
- [Constraints](guide/constraints.md) — Musical rule system

### Tutorials
- [Claude Code Workflow](tutorials/claude-code-workflow.md) — Interactive composition with subagents

### Architecture
- [Layer Model](architecture/layers.md) — 8-layer architecture
- [Design Decisions](architecture/decisions.md) — ADRs

### Reference
- [Glossary](glossary.md) — YaO terminology
- [Provenance Schema](provenance-schema.md) — Decision log format
- [Instruments](reference/instruments.md) — 38 instruments with MIDI ranges
- [Music Theory](reference/music-theory.md) — Scales, chords, dynamics

### Audits & Design
- [Wave 1 Completion](audit/wave-1-completion.md) — Honesty wave results
- [Wave 2 Completion](audit/wave-2-completion.md) — Alignment wave results
- [Aesthetic Benchmark](wave-2-2-aesthetic-benchmark.md) — Metric validation

### Migration
- [v2 Baseline Report](migration/v2-baseline-report.md) — Gap analysis
- [Silent Fallback Inventory](migration/silent-fallback-inventory.md) — RecoverableDecision sites
