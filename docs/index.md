# YaO — You and Orchestra

**YaO** is an agentic music production environment built on Claude Code. It transforms natural language descriptions into complete, multi-instrument compositions through a pipeline of AI subagents, music theory engines, and adversarial critique.

---

## What YaO Does

- **Multi-turn sketches** — describe a piece in plain language (English or Japanese), refine through dialogue
- **Full composition pipeline** — 9-step plan-based generation from intent to rendered audio
- **Genre-aware** — 29 genre skills shape every decision from chord palette to groove feel
- **Adversarial critique** — 35 rules catch structural, harmonic, melodic, and rhythmic issues
- **Pin-based feedback** — point at a specific bar and say what's wrong in natural language
- **Multiple output formats** — MIDI, WAV, MusicXML, LilyPond/PDF, Reaper RPP, Strudel

---

## Architecture Overview

```
CompositionSpec
    → PlanOrchestrator (9 steps)
        → MusicalPlan (form + harmony + motif + phrase + drums + arrangement + hooks + conversation)
    → Critic Gate (35 rules)
    → NoteRealizer (rule-based or stochastic)
    → GrooveApplicator (20 profiles)
    → Performance (articulation + dynamics + microtiming + CC curves)
    → Renderer (MIDI / WAV / MusicXML / LilyPond / Reaper / Strudel)
```

**7 Subagents**: Producer, Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Adversarial Critic

**8 Generation Strategies**: rule_based, stochastic, markov, twelve_tone, process_music, constraint_solver, loop_evolution, ai_seed

**8 Melodic Strategies**: contour_based, motif_development, linear_voice, arpeggiated, scalar_runs, call_response, pedal_tone, hocketing

---

## Key Capabilities

| Area | What's Available |
|------|-----------------|
| Instruments | 54 (46 standard + 8 non-Western cultural) |
| Scales | 28 including microtonal (EDO, maqam, raga, gamelan) |
| Song Forms | 20 (AABA, verse-chorus, rondo, blues, J-pop, game BGM, ambient...) |
| Drum Patterns | 15 (including non-4/4: waltz, 6/8, 5/4, 7/8) |
| Groove Profiles | 20 (jazz swing, bossa nova, afrobeat, samba, drum & bass...) |
| Critique Rules | 35 across 8 categories |
| Genre Skills | 29 covering classical, electronic, world, functional music |
| Tonal Systems | 10 kinds (major/minor, modal, blues, pentatonic, atonal, drone, raga, maqam, microtonal, custom) |
| Trajectory Dims | 5 (tension, density, register_height, variation, instrumentation) |
| Evaluation | 6-dimension scoring + 7 use-case evaluators + aesthetic metrics |
| Perception | Audio features, surprise scoring, mood classification, reference matching |

---

## Quick Examples

### Interactive Sketch
```
/sketch
> A melancholic piano piece with cello, 90 seconds, like a rainy afternoon
```

### Natural Language Composition
```bash
yao conduct "upbeat J-pop opening, 90 seconds, energetic with catchy hook"
```

### From YAML Spec
```bash
yao compose specs/templates/cinematic-3min.yaml --render-audio
```

### Targeted Feedback
```bash
yao pin "verse:bar4:piano — too busy, simplify the left hand"
```

### Arrange Existing MIDI
```
/arrange input.mid --style jazz_ballad --preserve melody,harmony
```

---

## Design Philosophy

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide

---

## Getting Started

- [Quick Start](getting-started/quickstart.md) — generate your first piece in 2 minutes
- [Spec Templates](getting-started/templates.md) — pre-built starting points
- [Audio Setup](getting-started/audio-setup.md) — optional FluidSynth for WAV output
- [CLI Reference](guide/cli-reference.md) — all commands and options
- [Claude Code Workflow](tutorials/claude-code-workflow.md) — using YaO interactively
