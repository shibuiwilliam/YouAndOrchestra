# You and Orchestra (YaO)

**An agentic music production environment built on Claude Code** — where you are the conductor, and the AI is your orchestra.

Describe what you want in plain language, and YaO generates a full MIDI score with per-instrument stems, quality evaluation, aesthetic analysis, and a provenance log explaining every decision.

> Your vision. Your taste. Your soul. — and an Orchestra ready to listen, respond, and surprise.

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
3. **Critique** — 35 adversarial rules find every weakness
4. **Regenerate** — fix specific sections based on feedback
5. **Pin** — attach localized feedback to specific bars/beats/instruments
6. **Arrange** — transform an existing piece into a new style with preservation contracts
7. **Render** — output to WAV audio via FluidSynth, MusicXML, LilyPond/PDF, or Strudel

---

## Slash Commands

| Command | Purpose |
|---|---|
| `/sketch` | 6-turn interactive dialogue → complete spec |
| `/compose <project>` | Run Conductor loop (generate → evaluate → adapt) |
| `/conduct <description>` | Natural-language composition with feedback loop |
| `/critique <project>` | Adversarial critique with structured findings |
| `/regenerate-section <project> <section>` | Re-generate one section |
| `/render <project>` | MIDI → WAV audio |
| `/explain <question>` | Query the provenance log |
| `/arrange <project>` | Style transfer with preservation contracts |
| `/pin <project> <location> <note>` | Attach localized feedback |
| `/feedback <project> <text>` | Natural-language feedback → structured suggestions |

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
Layer 6: Verification & Critique     (verify/ — 35 rules, aesthetic metrics, acoustic evaluation)
Layer 5: Rendering                   (render/ — MIDI, WAV, MusicXML, LilyPond, Reaper, Strudel)
Layer 4.5: Performance Expression    (generators/performance/ — articulation, dynamics, microtiming)
Layer 4: Perception Substitute       (perception/ — audio features, style vectors, surprise, use-case eval)
Layer 3.5: Musical Plan IR           (ir/plan/ — form, harmony, motif, phrase, arrangement, drums, conversation)
Layer 3: Score IR                    (ir/ — note, part, section, voicing, timing, hook, dynamics_shape, groove, conversation)
Layer 2: Generation Strategy         (generators/ — plan generators, note realizers, reactive fills, frequency clearance)
Layer 1: Specification               (schema/, sketch/ — YAML specs, NL compiler, conversation, hooks, groove)
Layer 0: Constants                   (constants/ — 46 instruments, 28 scales, 20 forms, 14 chords)
```

### The V2 Pipeline (9 Steps)

```
Spec + Trajectory
  → [Step 1]   Form Planner         → SongFormPlan + TensionArcs
  → [Step 2]   Harmony Planner      → HarmonyPlan
  → [Step 3]   Motif Developer      → MotifPlan + PhrasePlan + HookPlan
  → [Step 4]   Drum Patterner       → DrumPattern + GrooveProfile
  → [Step 5]   Arranger             → ArrangementPlan
  → [Step 5.5] Conversation Dir.    → ConversationPlan
  ═══ Critic Gate (MPIR-level evaluation) ═══
  → [Step 6]   Note Realizer V2     → ScoreIR (100% plan consumption)
  → [Step 6.5] Performance          → Articulation, dynamics, microtiming
  → [Step 7]   Renderer             → MIDI / WAV / Score
  → [Step 7.5] Listening Simulation → PerceptualReport
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

### Melodic Strategies (8)

| Strategy | Character |
|---|---|
| contour_based | Arch/ascending/descending contour shaping |
| motif_development | Short motif repeated with transformations |
| linear_voice | Stepwise motion, classical voice-leading |
| arpeggiated | Broken chord patterns |
| scalar_runs | Scale runs in sequences |
| call_response | Alternating question-answer phrases |
| pedal_tone | Revolves around repeated note |
| hocketing | Register jumps (high-low alternation) |

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
| Acoustics | 5% | Spectral balance, LUFS compliance |

### Acoustic Evaluation (Perception Layer)

| Category | Metrics |
|---|---|
| Loudness | Integrated LUFS, short-term curve, peak dBFS, dynamic range |
| Spectral | Centroid, rolloff, flatness, 7-band energy, masking risk |
| Temporal | Onset density per section, tempo stability |
| Use-case | YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic |

### Adversarial Critique (35 rules across 12 categories)

| Category | Rules |
|---|---|
| Structural (3) | Section monotony, climax absence, form imbalance |
| Melodic (3) | Contour monotony, motif recurrence, phrase closure |
| Harmonic (3) | Cliche progression, cadence weakness, harmonic monotony |
| Rhythmic (2) | Rhythmic monotony, syncopation lack |
| Arrangement (5) | Frequency collision, texture collapse, register violation, conversation silence, voice ambiguity |
| Emotional (2) | Intent divergence, trajectory violation |
| Genre Fitness (2) | Tempo out of range, instrument mismatch |
| Memorability (2) | Hook weakness, motif absence |
| Surprise (3) | Surprise deficit, surprise overload, tension arc unresolved |
| Hook (4) | Hook overuse, hook underuse, hook misplacement, flat dynamics |
| Groove (3) | Groove inconsistency, microtiming flatness, ensemble conflict |
| Acoustic (3) | Symbolic-acoustic divergence, LUFS violation, spectral imbalance |

---

## 7 Subagents

| Subagent | Role | Key Output |
|---|---|---|
| **Producer** | Coordinates all agents, resolves conflicts | SongFormPlan |
| **Composer** | Melodies, motifs, thematic development | MotifPlan + PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences, modulations | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves, syncopation | DrumPattern + GrooveProfile |
| **Orchestrator** | Instruments, voicings, register separation | ArrangementPlan |
| **Mix Engineer** | EQ, compression, reverb, loudness | ProductionManifest |
| **Adversarial Critic** | Finds weaknesses — never praises | Findings |

Subagents run via **PythonOnlyBackend** (default, CI-safe) or **AnthropicAPIBackend** (real LLM calls with structured output via tool use).

---

## Eight Structural Improvements (v2.0)

| # | Improvement | Status | Key Module |
|---|---|---|---|
| 1 | **Surprise Score** | ✅ | `perception/surprise.py`, `ir/tension_arc.py` |
| 2 | **Acoustic Truth** | ✅ | `perception/audio_features.py`, `verify/acoustic/` |
| 3 | **Hook IR + Phrase Dynamics** | ✅ | `ir/hook.py`, `ir/dynamics_shape.py` |
| 4 | **Ensemble Groove** | ✅ | `ir/groove.py`, `generators/groove_applicator.py` |
| 5 | **Conversation Plan** | ✅ | `ir/conversation.py`, `generators/reactive_fills.py` |
| 6 | **Diversity Sources** | ✅ | `constants/forms.py`, `generators/melodic_strategies.py` |
| 7 | **Multilingual** | ✅ | `sketch/compiler.py` (Japanese + English) |
| 8 | **Arrangement Engine** | ✅ | `arrange/` (extractor, style vector, diff) |

---

## Ensemble Constraints

Inter-part validation for multi-instrument arrangements:

| Rule | What it checks |
|---|---|
| `register_separation` | Instruments maintain minimum distance |
| `downbeat_consonance` | Bass-melody consonance on strong beats |
| `no_parallel_octaves` | No parallel octave motion between parts |
| `no_frequency_collision` | Parts don't overlap excessively in pitch |
| `bass_below_melody` | Bass stays in lower register |

---

## Three-Tier Feedback

| Level | Scope | Command |
|---|---|---|
| **Spec-level** | Change YAML, regenerate everything | Edit `composition.yaml` |
| **Section-level** | Regenerate one section, preserve others | `/regenerate-section` |
| **Pin-level** | Localized feedback at (section, bar, beat, instrument) | `/pin` |

Natural-language feedback (e.g., "the chorus feels weak") is translated to structured suggestions via `/feedback`.

---

## StyleVector (Copyright-Safe)

Abstract features for style comparison — never includes melody, chords, or hooks:

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

- **46 instruments** across 9 families (including 8 non-Western: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney)
- **28 scales** including 17 microtonal tuning systems (EDO, raga, maqam, gamelan, JI)
- **14 chord types** with functional harmony (Roman numerals)
- **20 song forms** (AABA, verse-chorus-bridge, rondo, blues 12-bar, J-Pop, game BGM, ambient, etc.)
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations**: transpose, invert, retrograde, augment, diminish, sequence
- **DrumPattern IR**: 15 kit pieces, 8 genre patterns, swing + ghost notes
- **Extended time signatures**: compound meters, polymeter support
- **Hook deployment**: rare, frequent, withhold-then-release, ascending repetition
- **GrooveProfile**: ensemble-wide microtiming, velocity patterns, swing ratio
- **ConversationPlan**: inter-instrument dialogue, reactive fills, frequency clearance

---

## CI & Quality

```bash
make all-checks    # Full quality pipeline (2157 tests + 6 golden)
make test          # All tests
make lint          # ruff + mypy strict
make arch-lint     # Layer boundary enforcement
make test-acoustic # Audio regression (weekly CI)
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
src/yao/           213 Python modules
  constants/       46 instruments, 28 scales, 20 forms, MIDI, theory
  schema/          Pydantic specs (v1 + v2), constraints, hooks, groove, conversation
  sketch/          NL → spec compiler (EN + JP), dialogue state
  ir/              Score IR + Plan IR (MPIR) + Hook, Groove, Conversation, TensionArc
  generators/      Note realizers, plan generators, performance, melodic strategies,
                   reactive fills, frequency clearance, groove applicator
  perception/      Audio features, StyleVector, surprise scorer, use-case eval,
                   listening simulator
  verify/          Evaluator, 35 critique rules, aesthetic metrics, acoustic divergence,
                   constraint checker
  reflect/         Provenance, style profile, ratings
  conductor/       Orchestration loop, feedback, multi-candidate, audio loop
  subagents/       7 Python subagent implementations
  agents/          Backend protocol (PythonOnly, Anthropic API)
  render/          MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel
  mix/             EQ, compression, reverb, mastering (pedalboard-based)
  arrange/         Style transfer, source extraction, preservation contracts
  feedback/        Pin IR, NL translator, pin-aware regenerator
  improvise/       Real-time improvisation engine
  skills/          Genre skill loader + registry
  runtime/         Project runtime (undo/redo, caching, lockfile)
  annotate/        Browser-based time-range annotation UI
tests/             181 test files, 2157 test functions
tools/             CI tooling (honesty checks, architecture lint, sync)
.claude/           Agent prompts, slash commands, genre skills (22 genres)
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
7. **Acoustic truth complements symbolic truth** — symbolic metrics necessary, never sufficient

---

## Documentation

| Document | Purpose |
|---|---|
| [FEATURE_STATUS.md](FEATURE_STATUS.md) | Single source of truth for capabilities |
| [PROJECT.md](PROJECT.md) | Full design (v2.0) |
| [CLAUDE.md](CLAUDE.md) | Development rules and conventions |
| [VISION.md](VISION.md) | Target architecture |
| [development/](development/) | Contributor guide |
| [docs/](docs/) | Architecture and design docs |

---

## License

MIT
