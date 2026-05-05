# YaO -- You and Orchestra

**An agentic music production environment built on Claude Code.**

YaO turns music composition into a structured, reproducible process. Describe what you want in plain language (English or Japanese), and YaO generates a full MIDI score with per-instrument stems, quality evaluation, aesthetic analysis, and a provenance log explaining every decision.

> *Your vision. Your taste. Your soul. -- and an Orchestra ready to listen, respond, and surprise.*

## What YaO Does

- **Multi-turn sketch dialogue** -- 6-turn interactive conversation refines your idea into a complete spec
- **Natural language composition** -- English and Japanese input with 3-stage fallback (LLM -> Keyword -> Default)
- **Spec-driven composition** -- YAML specs (v1 flat, v2 11-section, v3 composable) with precise control
- **V2 Pipeline** -- 9-step plan-first generation (Form -> Harmony -> Motif -> Drums -> Arrangement -> Conversation -> Realization -> Performance -> Listening)
- **8 generation strategies** -- rule_based_v2, stochastic_v2, markov, twelve_tone, process_music, constraint_solver, plus 2 legacy adapters
- **8 melodic strategies** -- contour, motif development, linear voice, arpeggiated, scalar runs, call-response, pedal tone, hocketing
- **46 instruments** across 9 families with register-aware orchestration (including 8 non-Western: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney)
- **28+ scales** including microtonal (ragas, maqamat, gamelan, just intonation)
- **20 song forms** -- AABA, verse-chorus-bridge, rondo, blues, J-Pop, game BGM, ambient, and more
- **15 drum patterns** across time signatures (4/4, 3/4, 5/4, 6/8, 7/8)
- **20 groove profiles** for ensemble-wide microtiming (jazz swing, bossa nova, funk, afrobeat, samba, etc.)
- **Trajectory curves** -- Shape tension, density, predictability, brightness, register height
- **6-dimension evaluation** -- Structure, melody, harmony, aesthetic, arrangement, acoustics
- **Acoustic evaluation** -- LUFS, spectral features, 7 use-case evaluators, symbolic-acoustic divergence detection
- **35 adversarial critique rules** across 15 categories -- structured findings with severity and remediation
- **5 ensemble constraints** -- Register separation, downbeat consonance, parallel octave detection, frequency collision, bass-melody ordering
- **Ensemble groove** -- GrooveProfile applied across all instruments (not just drums)
- **Inter-instrument conversation** -- ConversationPlan with reactive fills and frequency clearance
- **Hook deployment** -- Memorable fragments with strategies (rare, frequent, withhold-then-release)
- **Arrangement engine** -- 5 transformation operations with preservation contracts and diff reports
- **Three-tier feedback** -- Spec-level, section-level, and pin-level with NL translation (30+ phrase mappings)
- **StyleVector** -- 6 copyright-safe abstract features for style comparison
- **Provenance tracking** -- Append-only causal graph recording every decision
- **7 subagents** -- Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Adversarial Critic, Producer
- **22 genre skills** -- Integrated knowledge bases for chord palettes, tempo ranges, instrumentation
- **6 output formats** -- MIDI (with stems), WAV, MusicXML, LilyPond/PDF, Reaper RPP, Strudel
- **LLM backend** -- AnthropicAPIBackend with structured output (tool use), or PythonOnly for CI
- **~2,157 tests** -- Unit, integration, scenario, constraint, golden, acoustic regression, genre coverage, properties
- **5 honesty tools** -- CI verification that features actually work (not just exist)

## Architecture (v2.0)

```
Spec -> PlanOrchestrator (9 steps) -> MusicalPlan -> Critic Gate -> NoteRealizer V2
    -> GrooveApplicator -> Performance -> Renderer -> Listening Simulator
```

8 layers with strict downward-only dependency. Plan-first generation separates *what to play* from *how to play it*.

## Quick Example

```bash
# Interactive (recommended)
/sketch a calm piano piece in D minor for studying

# Natural language (one-shot)
yao conduct "a calm piano piece in D minor for studying, 90 seconds"

# From spec (full control)
yao compose specs/templates/minimal.yaml

# Arrange existing piece
/arrange my-song --target-genre lofi_hiphop --preserve melody,form

# Localized feedback
/pin my-song --location "section:chorus,bar:6,beat:3,instrument:piano" --note "too busy"
```

Output:
```
outputs/projects/<name>/iterations/v001/
  full.mid           # Complete MIDI score
  stems/piano.mid    # Per-instrument stems
  analysis.json      # Quality analysis
  evaluation.json    # Quality scores (6 dimensions)
  perceptual.json    # Acoustic analysis
  provenance.json    # Decision log (causal graph)
```

## Design Philosophy

1. **Agent = environment, not composer** -- YaO accelerates human creativity
2. **Explain everything** -- Every note has a provenance record
3. **Constraints liberate** -- Specs and rules are scaffolds, not cages
4. **Time-axis first** -- Trajectory curves before notes
5. **Human ear is truth** -- Automated scores inform; humans decide
6. **Vertical alignment** -- Input, processing, evaluation advance together
7. **Acoustic truth complements symbolic truth** -- Symbolic metrics necessary, never sufficient

## Documentation

### Getting Started
- [Quick Start](getting-started/quickstart.md) -- Install and generate your first piece
- [Templates](getting-started/templates.md) -- Ready-to-use spec templates
- [Audio Setup](getting-started/audio-setup.md) -- FluidSynth installation

### User Guide
- [CLI Reference](guide/cli-reference.md) -- All commands and options
- [Composition Spec](guide/composition-spec.md) -- YAML schema (v1 + v2 + v3)
- [Trajectories](guide/trajectories.md) -- Emotion-shaping curves
- [Constraints](guide/constraints.md) -- Musical rule system

### Tutorials
- [Claude Code Workflow](tutorials/claude-code-workflow.md) -- Interactive composition with subagents

### Architecture
- [Layer Model](architecture/layers.md) -- 8-layer architecture
- [Design Decisions](architecture/decisions.md) -- ADRs

### Reference
- [Glossary](glossary.md) -- YaO terminology
- [Provenance Schema](provenance-schema.md) -- Decision log format
- [Instruments](reference/instruments.md) -- 46 instruments with MIDI ranges
- [Music Theory](reference/music-theory.md) -- Scales, chords, dynamics

### Development
- [Architecture](architecture/layers.md) -- System architecture details
- [Composition Specs](guide/composition-spec.md) -- YAML spec formats
- [CLI Reference](guide/cli-reference.md) -- Command-line interface
- [Design Decisions](architecture/decisions.md) -- Architectural decisions

### Audits & Design
- [Wave 1 Completion](audit/wave-1-completion.md) -- Honesty wave results
- [Monthly Audit](audit/2026-05-monthly.md) -- Latest status

### Migration
- [v2 Baseline Report](migration/v2-baseline-report.md) -- Gap analysis
- [Silent Fallback Inventory](migration/silent-fallback-inventory.md) -- RecoverableDecision sites
