# YaO — You and Orchestra

**YaO** is an agentic music production environment reachable through **three peer surfaces** — Claude Code (interactive), a Click-based CLI (scriptable), and the Claude Agent SDK for Python (programmatic). It transforms natural language descriptions into complete, multi-instrument compositions through a pipeline of AI subagents, music theory engines, and adversarial critique. The same orchestra plays in every venue.

---

## What YaO Does

- **Multi-turn sketches** — describe a piece in plain language (English or Japanese), refine through dialogue
- **Full composition pipeline** — 9-step plan-based generation from intent to rendered audio
- **Combination Stack** — Coupling layer modules: chord-aware melody, voice-leading optimization, reharmonization, genre blending, and more
- **Genre-aware** — 38 genre profiles shape every decision from chord palette to groove feel
- **Adversarial critique** — 34 rules catch structural, harmonic, melodic, and rhythmic issues
- **Pin-based feedback** — point at a specific bar and say what's wrong in natural language
- **Multiple output formats** — MIDI, WAV, MusicXML, LilyPond/PDF, Reaper RPP, Strudel

---

## Architecture Overview

### Three Surfaces, One Engine

```
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Claude Code     │ │  CLI (Click)     │ │  Agent SDK       │
│  (interactive)   │ │  (yao …)         │ │  (yao.sdk)       │
└─────────┬────────┘ └─────────┬────────┘ └─────────┬────────┘
          └────────────────────┴────────────────────┘
                               │
                          Conductor
                               │
                     7-Layer Music Engine
```

All surfaces share the same `.claude/` directory, the same Conductor, and the same seven-layer engine. Changing a subagent definition affects all three surfaces simultaneously.

### Generation Pipeline

```
CompositionSpec
    → PlanOrchestrator (9 steps)
        → MusicalPlan (form + harmony + motif + phrase + drums + arrangement + hooks + conversation)
    → Combination Stack (chord-aware melody, voice leading, reharmonization...)
    → Critic Gate (34 rules)
    → NoteRealizer (rule-based or stochastic)
    → GrooveApplicator (20 profiles)
    → Performance (articulation + dynamics + microtiming + CC curves)
    → Renderer (MIDI / WAV / MusicXML / LilyPond / Reaper / Strudel)
```

**7 Subagents**: Producer, Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Adversarial Critic

**9 Generation Strategies**: rule_based, stochastic, markov, twelve_tone, process_music, constraint_solver, loop_evolution, ai_seed, phrase_aware

**8 Melodic Strategies**: contour_based, motif_development, linear_voice, arpeggiated, scalar_runs, call_response, pedal_tone, hocketing

---

## Key Capabilities

| Area | What's Available |
|------|-----------------|
| Instruments | 46 (38 standard + 8 non-Western cultural) |
| Scales | 33 including microtonal (14 standard + 19 extended: maqam, raga, gamelan, Japanese) |
| Song Forms | 20 (AABA, verse-chorus, rondo, blues, J-pop, game BGM, ambient...) |
| Drum Patterns | 15 (including non-4/4: waltz, 6/8, 5/4, 7/8) |
| Groove Profiles | 20 (jazz swing, bossa nova, afrobeat, samba, drum & bass...) |
| Critique Rules | 34 across 15 categories |
| Genre Skills | 38 covering classical, electronic, world, functional music |
| Harmonic Devices | 15 YAML-defined (jazz turnarounds, blues patterns, Coltrane changes...) |
| Tonal Systems | 10 kinds (major/minor, modal, blues, pentatonic, atonal, drone, raga, maqam, microtonal, custom) |
| Trajectory Dims | 5 (tension, density, predictability, brightness, register_height) |
| Evaluation | 6-dimension scoring + melody-harmony alignment + voice-leading smoothness + 7 use-case evaluators |
| Coupling | 11 modules: chord-aware melody, voice leading, reharmonization, genre blending, and more |
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

### Agent SDK (Programmatic)
```python
import asyncio
from yao.sdk import YaoAgent
from yao.sdk.events import IterationCompletedEvent, AudioReadyEvent

async def main():
    async with YaoAgent(project="rainy-cafe") as agent:
        async for event in agent.conduct(
            "a rainy-cafe BGM with piano and cello, melancholy",
            max_iterations=3,
        ):
            if isinstance(event, IterationCompletedEvent):
                print(f"iter {event.iteration} -> {event.iteration_path}")
            elif isinstance(event, AudioReadyEvent):
                print(f"audio: {event.wav_path}")

asyncio.run(main())
```

---

## Design Philosophy

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide
6. **Phrase before notes** — phrases have function, target pitch, cadence
7. **Genre is a constellation** — `MelodicProfile`, not a label
8. **Diversity through combination** — the Combination Stack turns rich material into genuinely diverse output

---

## Getting Started

- [Quick Start](getting-started/quickstart.md) — generate your first piece in 2 minutes
- [Spec Templates](getting-started/templates.md) — pre-built starting points
- [Audio Setup](getting-started/audio-setup.md) — optional FluidSynth for WAV output
- [CLI Reference](guide/cli-reference.md) — all commands and options
- [Claude Code Workflow](tutorials/claude-code-workflow.md) — using YaO interactively
- [SDK Overview](sdk/overview.md) — programmatic access via Agent SDK
- [SDK Quickstart](sdk/quickstart.md) — five lines to your first composition
- [SDK API Reference](sdk/api-reference.md) — YaoAgent, events, results, MCP tools
