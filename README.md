# You and Orchestra (YaO)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

Describe what you want in plain language, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, aesthetic analysis, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to serve.

**Current state:** See [FEATURE_STATUS.md](FEATURE_STATUS.md) for the complete capability matrix.

---

## Quick Start

```bash
git clone https://github.com/shibuiwilliam/YouAndOrchestra
cd YouAndOrchestra
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make setup-hooks
```

Requires **Python 3.11+**. Audio rendering requires [FluidSynth](#audio-rendering).

Then launch Claude Code:

```bash
claude
```

---

## What YaO Does

```
/sketch  →  /compose  →  /critique  →  /regenerate-section  →  /render
```

1. **Sketch** — describe your idea in natural language (English or Japanese), refine through 6-turn dialogue
2. **Compose** — generate with automatic quality evaluation + aesthetic scoring
3. **Critique** — 20 adversarial rules find every weakness
4. **Regenerate** — fix specific sections based on feedback
5. **Render** — output to WAV audio via FluidSynth

---

## Slash Commands

| Command | Purpose |
|---|---|
| `/sketch` | 6-turn interactive dialogue → complete spec |
| `/compose <project>` | Run Conductor loop (generate → evaluate → adapt) |
| `/critique <project>` | Adversarial critique with structured findings |
| `/regenerate-section <project> <section>` | Re-generate one section |
| `/render <project>` | MIDI → WAV audio |
| `/explain <question>` | Query the provenance log |
| `/arrange <project>` | Style transfer with preservation contracts |

### Example `/sketch` Prompts

```
/sketch a melancholic piano piece for studying on a rainy evening
/sketch anime opening theme, energetic J-pop style, 90 BPM, full orchestra with electric sounds
/sketch tense horror game BGM with dissonant strings and sparse percussion
/sketch upbeat 8-bit chiptune for a retro platformer boss fight
/sketch gentle jazz trio for a late-night cafe scene, brushed drums and walking bass
/sketch epic orchestral trailer music building to a massive brass climax
/sketch minimalist ambient piece with slow-evolving pad textures, 60 BPM
/sketch funky slap bass groove with wah guitar and tight drums, 110 BPM
/sketch classical string quartet in the style of late Romantic era, D minor
/sketch Japanese festival matsuri music with taiko drums and shinobue flute
```

---

## Architecture (8 Layers)

```
Layer 7: Reflection & Learning       (reflect/, agents/)
Layer 6: Verification & Critique     (verify/, 20 rules, aesthetic metrics)
Layer 5: Rendering                   (render/ — MIDI, WAV, MusicXML, LilyPond, Reaper, Strudel)
Layer 4.5: Performance Expression    (generators/performance/ — articulation, dynamics, microtiming)
Layer 4: Perception Substitute       (perception/ — audio features, style vectors, use-case eval)
Layer 3.5: Musical Plan IR           (ir/plan/ — form, harmony, motif, phrase, arrangement, drums)
Layer 3: Score IR                    (ir/ — note, part, section, voicing, timing)
Layer 2: Generation Strategy         (generators/note/ — V2 realizers consume MPIR directly)
Layer 1: Specification               (schema/, sketch/ — YAML specs, NL compiler)
Layer 0: Constants                   (constants/ — 38 instruments, 14 scales, 17 tuning systems)
```

### The V2 Pipeline (7 Steps)

```
Spec + Trajectory
  → [Step 1] Form Planner      → SongFormPlan
  → [Step 2] Harmony Planner   → HarmonyPlan
  → [Step 3] Motif Developer   → MotifPlan + PhrasePlan
  → [Step 4] Drum Patterner    → DrumPattern
  → [Step 5] Arranger          → ArrangementPlan
  ═══ Critic Gate (MPIR-level evaluation) ═══
  → [Step 6] Note Realizer V2  → ScoreIR (100% plan consumption)
  → [Step 6.5] Performance     → Articulation, dynamics, microtiming
  → [Step 7] Renderer          → MIDI / WAV / Score
```

---

## Generation Strategies

| Strategy | Description |
|---|---|
| **rule_based_v2** | Deterministic, chord-aware, motif placement, phrase contour |
| **stochastic_v2** | Seed + temperature controlled, non-chord tones, rhythmic variety |
| **rule_based** | Legacy (deprecated) — deterministic via v1 adapter |
| **stochastic** | Legacy (deprecated) — seed-based via v1 adapter |
| **markov** | Probabilistic transitions from learned patterns |
| **twelve_tone** | Serialist composition using tone rows |
| **process_music** | Minimalist generative processes |
| **constraint_solver** | Backtracking search with hard constraints |

---

## Quality Evaluation

### Formal Metrics (6 dimensions)

| Dimension | Weight | Metrics |
|---|---|---|
| Structure | 20% | Section contrast, bar count, section count, rhythm variety |
| Melody | 25% | Pitch range, stepwise motion, contour variety |
| Harmony | 20% | Pitch class variety, consonance ratio |
| **Aesthetic** | **20%** | Surprise, memorability, contrast, pacing |
| Arrangement | 10% | Texture variety, register separation |
| Acoustics | 5% | Spectral balance |

### Aesthetic Metrics (Wave 2.2)

| Metric | What it measures | Source |
|---|---|---|
| **Surprise** | Melodic unpredictability (bigram NLL) | diatonic_bigram.yaml |
| **Memorability** | Motif recurrence x identity strength | MusicalPlan motifs |
| **Contrast** | Section-to-section style distance | StyleVector comparison |
| **Pacing** | Tension arc match to plan | Velocity vs target_tension |

### Adversarial Critique (20 rules)

| Category | Rules |
|---|---|
| Structural (3) | Section monotony, climax absence, form imbalance |
| Melodic (3) | Contour monotony, motif recurrence, phrase closure |
| Harmonic (3) | Cliche progression, cadence weakness, harmonic monotony |
| Rhythmic (2) | Rhythmic monotony, syncopation lack |
| Arrangement (3) | Frequency collision, texture collapse, **ensemble register violation** |
| Emotional (2) | Intent divergence, trajectory violation |
| Genre Fitness (2) | Tempo out of range, instrument mismatch |
| Memorability (2) | Hook weakness, motif absence |

---

## 7 Subagents

| Subagent | Role | Key Output |
|---|---|---|
| **Producer** | Coordinates all agents, resolves conflicts | SongFormPlan |
| **Composer** | Melodies, motifs, thematic development | MotifPlan + PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences, modulations | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves, syncopation | DrumPattern |
| **Orchestrator** | Instruments, voicings, register separation | ArrangementPlan |
| **Mix Engineer** | EQ, compression, reverb, loudness | ProductionManifest |
| **Adversarial Critic** | Finds weaknesses — never praises | Findings |

Subagents run via **PythonOnlyBackend** (default, CI-safe) or **AnthropicAPIBackend** (real LLM calls with structured output via tool use).

---

## Ensemble Constraints (Wave 3.2)

Inter-part validation for multi-instrument arrangements:

| Rule | What it checks |
|---|---|
| `register_separation` | Instruments maintain minimum distance |
| `downbeat_consonance` | Bass-melody consonance on strong beats |
| `no_parallel_octaves` | No parallel octave motion between parts |
| `no_frequency_collision` | Parts don't overlap excessively in pitch |
| `bass_below_melody` | Bass stays in lower register |

---

## StyleVector (Wave 3.4)

Copyright-safe abstract features for style comparison:

| Feature | Dims | Safe because |
|---|---|---|
| interval_class_histogram | 12 | No sequence order |
| chord_quality_histogram | 8 | No progression order |
| cadence_type_distribution | 4 | Aggregate only |
| rhythm_complexity | 1 | Single statistic |
| harmonic_rhythm | 1 | Rate only |
| register_distribution | 12 | Octave histogram |

**FORBIDDEN**: melody_contour, chord_sequence, chord_progression, lyrics, hook

---

## Trajectory System

Shape the emotional arc independently from notes:

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.85], [32, 0.3]]
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, chorus: 0.9, outro: 0.3 }
```

Five dimensions: tension, density, predictability, brightness, register height.

---

## Music Theory

- **38 instruments** across 9 families
- **14 scales** + 17 microtonal tuning systems (EDO, raga, maqam, gamelan, JI)
- **14 chord types** with functional harmony (Roman numerals)
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations**: transpose, invert, retrograde, augment, diminish, sequence
- **DrumPattern IR**: 15 kit pieces, 8 genre patterns, swing + ghost notes
- **Extended time signatures**: compound meters, polymeter support

---

## CI & Quality

```bash
make all-checks    # Full quality pipeline
make test          # All tests (~1150 pass)
make lint          # ruff + mypy strict
make arch-lint     # Layer boundary enforcement
make honesty-check # Verify no stub ✅ features
make backend-honesty
make plan-consumption
make skill-grounding
make critic-coverage
```

---

## Audio Rendering

Requires FluidSynth and a General MIDI SoundFont:

```bash
# macOS
brew install fluid-synth
# Linux
sudo apt-get install fluidsynth
```

Place a `.sf2` file in `soundfonts/`, then use `/render`.

---

## Project Structure

```
src/yao/           167 Python modules
  constants/       Instruments, scales, MIDI, theory
  schema/          Pydantic specs (v1 + v2), constraints
  sketch/          NL → spec compiler (EN + JP), dialogue state
  ir/              Score IR + Plan IR (MPIR)
  generators/      Note realizers (V2), plan generators, performance
  perception/      Audio features, StyleVector, use-case eval
  verify/          Evaluator, critique, aesthetic metrics, constraint checker
  reflect/         Provenance, style profile, ratings
  conductor/       Orchestration loop, feedback, multi-candidate
  subagents/       7 Python subagent implementations
  agents/          Backend protocol (PythonOnly, Anthropic API)
  render/          MIDI, WAV, MusicXML, LilyPond, Reaper, Strudel
  mix/             EQ, compression, reverb, mastering
  arrange/         Style transfer, source extraction
  improvise/       Real-time improvisation engine
  skills/          Genre skill loader
tests/             126 test files, ~1235 test functions
tools/             CI tooling (honesty checks, architecture lint)
.claude/           Agent prompts, slash commands, genre skills
docs/              Design docs, audits, guides
```

---

## Design Philosophy

1. **The agent is an environment, not a composer** — accelerates human creativity
2. **Every decision is explainable** — provenance records why each note exists
3. **Constraints liberate** — specs and rules are scaffolding, not cages
4. **Time-axis first** — trajectory curves define the arc; notes fill details
5. **The human ear is the final truth** — automated scores inform; humans decide
6. **Vertical alignment** — input, processing, evaluation advance together
7. **Status honesty** — a ✅ means it works, not just that tests exist

---

## Documentation

| Document | Purpose |
|---|---|
| [FEATURE_STATUS.md](FEATURE_STATUS.md) | Single source of truth for capabilities |
| [PROJECT.md](PROJECT.md) | Full design (v3.0) |
| [CLAUDE.md](CLAUDE.md) | Development rules and conventions |
| [VISION.md](VISION.md) | Target architecture |
| [development/](development/) | Contributor guide |
| [docs/](docs/) | User and architecture docs |

---

## License

MIT
