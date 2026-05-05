# You and Orchestra (YaO)

**Describe music in plain language. Get a full MIDI score with stems, quality evaluation, and a log explaining every decision.**

YaO is an agentic music production environment built on Claude Code. It takes your idea -- a sentence, a conversation, or a detailed YAML spec -- and runs it through a 9-step generation pipeline with 7 AI subagents, 35 adversarial critique rules, and automatic iteration until the result meets quality thresholds. Everything is explainable: every note has a provenance record explaining why it exists.

> Your vision. Your taste. Your soul. -- and an Orchestra ready to listen, respond, and surprise.

---

## Quick Start

```bash
git clone https://github.com/shibuiwilliam/YouAndOrchestra
cd YouAndOrchestra
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires **Python 3.11+**. Audio rendering (MIDI to WAV) requires [FluidSynth](#audio-rendering).

### Your first piece

The fastest way to hear something:

```bash
yao conduct "a calm piano piece in D minor, 90 seconds"
```

This generates MIDI, evaluates quality across 6 dimensions, and iterates automatically if metrics fall short. Output lands in `outputs/projects/`.

Or launch Claude Code for an interactive experience:

```bash
claude
> /sketch a melancholic piano piece for studying on a rainy evening
```

The `/sketch` command walks you through a 6-turn dialogue to refine your idea, then you can `/compose`, `/critique`, and `/render`.

---

## Three Ways to Compose

### 1. Interactive sketch (recommended for exploration)

```
/sketch tense horror game BGM with dissonant strings and sparse percussion
/compose my-horror-bgm
/critique my-horror-bgm
/pin my-horror-bgm --location "section:chorus,bar:3" --note "too busy"
/render my-horror-bgm
```

The sketch dialogue supports both English and Japanese input.

### 2. Natural language (one-shot)

```bash
yao conduct "epic orchestral trailer music building to a massive brass climax"
```

The Conductor generates, evaluates, adapts, and regenerates -- up to 3 iterations -- until quality thresholds pass.

### 3. YAML spec (full control)

```bash
yao new-project my-piece
# Edit specs/projects/my-piece/composition.yaml
yao compose specs/projects/my-piece/composition.yaml
```

YaO supports three spec formats:
- **v1** -- Simple flat YAML for quick experiments
- **v2** -- 11-section detailed spec with full control over melody, harmony, rhythm, arrangement, and production
- **v3** -- Composable specs with `extends`, `overrides`, and reusable `fragments`

See [Spec System](development/spec-system.md) for details.

---

## What You Get

Each generation creates a versioned iteration (`v001`, `v002`, ...) so you never lose previous versions:

```
outputs/projects/my-piece/iterations/v001/
  full.mid           # Complete MIDI score
  stems/piano.mid    # Per-instrument MIDI stems
  analysis.json      # Structural analysis
  evaluation.json    # Quality scores (6 dimensions)
  perceptual.json    # Acoustic analysis (LUFS, spectral, temporal)
  provenance.json    # Causal graph of every decision
```

---

## Example Prompts

### Simple

```
/sketch a melancholic piano piece for studying on a rainy evening
/sketch anime opening theme, energetic J-pop style, 90 BPM, full orchestra
/sketch tense horror game BGM with dissonant strings and sparse percussion
/sketch upbeat 8-bit chiptune for a retro platformer boss fight
/sketch gentle jazz trio for a late-night cafe scene, brushed drums and walking bass
/sketch epic orchestral trailer music building to a massive brass climax
/sketch minimalist ambient piece with slow-evolving pad textures, 60 BPM
/sketch funky slap bass groove with wah guitar and tight drums, 110 BPM
/sketch classical string quartet in the style of late Romantic era, D minor
/sketch Japanese festival matsuri music with taiko drums and shinobue flute
/sketch smooth bossa nova for a sunset beach bar, nylon guitar and soft percussion
```

### Advanced

```
/sketch cinematic sci-fi soundtrack, 130 BPM, layered synth pads with orchestral strings, brass stabs on downbeats, sparse piano motif, 180 seconds, build from silence to wall of sound
/sketch lo-fi hip-hop study beat, 75 BPM, detuned electric piano chords, vinyl crackle texture, side-chained kick with muted bass, jazzy 7th voicings, loopable 90 seconds
/sketch Baroque fugue for harpsichord and string trio, 3 voices, subject-answer-countersubject structure, D minor, 100 BPM, strict voice leading, 120 seconds
/sketch Indian classical fusion, sitar melody over tabla and tanpura drone, Raga Yaman ascending phrases, 90 BPM, gradually introduce cello and flute harmonizing, 180 seconds
/sketch Studio Ghibli-inspired waltz, 3/4 time, 108 BPM, piano lead with accordion counter-melody, pizzicato strings, glockenspiel accents, warm and nostalgic, 150 seconds
/sketch high-energy drum and bass track, 174 BPM, breakbeat drums with heavy sub-bass reese, staccato string stabs, atmospheric pads, tension ramp in the last 16 bars, 150 seconds
/sketch Flamenco bulerias for nylon guitar, cajon, and handclaps, 12-beat compas cycle, rasgueado strumming, falsetas over Am-G-F-E progression, 100 seconds
/sketch ambient generative soundscape for planetarium, 50 BPM, granular-style evolving textures with oboe and cello drones, no percussion, very slow harmonic motion, 240 seconds
/sketch aggressive industrial metal, 140 BPM, drop-tuned palm-muted guitar riff in 7/8, double kick drums, distorted bass following guitar, dissonant brass hits on accents, 90 seconds
/sketch big band swing, 160 BPM, walking bass, ride cymbal, trumpet section melody in unison then harmony soli, trombone counter-melody, piano comping, saxophone shout chorus at climax, 120 seconds
```

---

## How It Works

### The V2 Pipeline (9 Steps)

YaO separates *what to play* from *how to play it*. Six plan generators decide structure, harmony, motifs, rhythm, orchestration, and inter-instrument dialogue. Then a note realizer places concrete notes that faithfully execute the plan.

```
User Input (natural language or YAML)
  -> SpecCompiler              (3-stage: LLM -> Keyword -> Default; EN + JP)
  -> [Step 1]  Form Planner   -> SongFormPlan + TensionArcs
  -> [Step 2]  Harmony Planner -> HarmonyPlan (genre-aware chord palettes)
  -> [Step 3]  Composer        -> MotifPlan + PhrasePlan + HookPlan
  -> [Step 4]  Drum Patterner  -> DrumPattern + GrooveProfile
  -> [Step 5]  Orchestrator    -> ArrangementPlan
  -> [Step 5.5] Conversation   -> ConversationPlan (inter-instrument dialogue)
  === Critic Gate (35 adversarial rules before any notes are placed) ===
  -> [Step 6]  Note Realizer V2 -> ScoreIR (100% plan consumption)
  -> [Step 6.5] Performance    -> Articulation, dynamics, microtiming
  -> [Step 7]  Renderer        -> MIDI / WAV / MusicXML / LilyPond / Score
  -> [Step 7.5] Listening Sim  -> PerceptualReport (LUFS, spectral, temporal)
  -> Evaluator (6 dimensions)  -> Conductor feedback loop (up to 3 iterations)
```

### 7 Subagents

YaO models the roles of a real music production team:

| Subagent | Role | Key Output |
|---|---|---|
| **Producer** | Coordinates all agents, resolves conflicts | SongFormPlan |
| **Composer** | Melodies, motifs, thematic development | MotifPlan + PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences, modulations | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves, syncopation | DrumPattern + GrooveProfile |
| **Orchestrator** | Instruments, voicings, register separation | ArrangementPlan |
| **Mix Engineer** | EQ, compression, reverb, loudness | ProductionManifest |
| **Adversarial Critic** | Finds weaknesses -- never praises | Structured Findings |

Subagents run via **PythonOnlyBackend** (default, CI-safe) or **AnthropicAPIBackend** (real LLM calls with structured output via tool use).

---

## Slash Commands

| Command | Purpose |
|---|---|
| `/sketch` | 6-turn interactive dialogue to build a complete spec |
| `/compose <project>` | Run Conductor loop (generate, evaluate, adapt) |
| `/conduct <description>` | Natural-language composition with feedback loop |
| `/critique <project>` | Adversarial critique with structured findings |
| `/regenerate-section <project> <section>` | Re-generate one section, keep the rest |
| `/render <project>` | MIDI to WAV audio, MusicXML, LilyPond, or Strudel |
| `/explain <question>` | Query the provenance log |
| `/arrange <project>` | Style transfer with preservation contracts |
| `/pin <project> <location> <note>` | Attach localized feedback to specific bars/beats/instruments |
| `/feedback <project> <text>` | Natural-language feedback translated to structured suggestions |

---

## Generation Strategies

YaO supports 8 generation strategies:

| Strategy | Description |
|---|---|
| **rule_based_v2** | Deterministic, chord-aware, motif placement, phrase contour |
| **stochastic_v2** | Seed + temperature controlled, non-chord tones, rhythmic variety |
| **markov** | Probabilistic transitions from learned patterns |
| **twelve_tone** | Serialist composition using tone rows (P/I/R/RI) |
| **process_music** | Minimalist generative processes (phasing, additive, subtractive) |
| **constraint_solver** | Backtracking search with hard constraints |
| **rule_based** | Legacy deterministic (via v1 adapter) |
| **stochastic** | Legacy seed-based (via v1 adapter) |

### 8 Melodic Strategies

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

Every composition is automatically evaluated across 6 dimensions:

| Dimension | Weight | What It Measures |
|---|---|---|
| Structure | 20% | Section contrast, bar count, rhythm variety |
| Melody | 25% | Pitch range, stepwise motion, contour variety |
| Harmony | 20% | Pitch class variety, consonance ratio |
| Aesthetic | 20% | Surprise, memorability, contrast, pacing |
| Arrangement | 10% | Texture variety, register separation |
| Acoustics | 5% | Spectral balance, LUFS compliance |

### Acoustic Evaluation

| Category | Metrics |
|---|---|
| Loudness | Integrated LUFS, short-term curve, peak dBFS, dynamic range |
| Spectral | Centroid, rolloff, flatness, 7-band energy, masking risk |
| Temporal | Onset density per section, tempo stability |
| Use-case | YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic |

### Adversarial Critique (35 Rules)

The critique system works like a panel of experts, each looking for specific weaknesses:

| Category | Rules |
|---|---|
| Structural (3) | Section monotony, climax absence, form imbalance |
| Melodic (3) | Contour monotony, motif recurrence, phrase closure |
| Harmonic (3) | Cliche progression, cadence weakness, harmonic monotony |
| Rhythmic (2) | Rhythmic monotony, syncopation lack |
| Arrangement (2) | Frequency collision, texture collapse |
| Emotional (2) | Intent divergence, trajectory violation |
| Genre Fitness (2) | Tempo out of range, instrument mismatch |
| Memorability (2) | Hook weakness, motif absence |
| Surprise (2) | Surprise deficit, surprise overload |
| Tension (1) | Tension arc unresolved |
| Hook (3) | Hook overuse, hook underuse, hook misplacement |
| Dynamics (1) | Flat phrase dynamics |
| Groove (3) | Groove inconsistency, microtiming flatness, ensemble conflict |
| Conversation (4) | Conversation silence, voice ambiguity, fill absence, frequency collision |
| Acoustic (5) | Symbolic-acoustic divergence, LUFS violation, spectral imbalance, brightness-intent mismatch, energy-trajectory violation |
| Metric (1) | Metric drift |

---

## Music Theory Support

- **46 instruments** across 9 families (including 8 non-Western: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney)
- **28+ scales** including microtonal tuning systems (ragas, maqamat, gamelan pelog/slendro, just intonation)
- **14 chord types** with functional harmony (Roman numeral analysis)
- **20 song forms** (AABA, verse-chorus-bridge, rondo, blues 12-bar, J-Pop, game BGM, ambient, and more)
- **Voice leading** with parallel fifths/octaves detection
- **Motif transformations**: transpose, invert, retrograde, augment, diminish, sequence
- **15 drum patterns** across time signatures (4/4, 3/4, 5/4, 6/8, 7/8)
- **20 groove profiles** for ensemble-wide microtiming (jazz swing, bossa nova, funk, afrobeat, samba, and more)
- **Extended time signatures**: compound meters, polymeter support, beat groupings
- **Hook deployment**: rare, frequent, withhold-then-release, ascending repetition
- **ConversationPlan**: inter-instrument dialogue, reactive fills, frequency clearance
- **22 genre skills** with integrated knowledge bases (chord palettes, tempo ranges, instrumentation)

---

## Feedback and Iteration

YaO supports feedback at three levels of granularity:

| Level | Scope | How |
|---|---|---|
| **Spec-level** | Change YAML, regenerate everything | Edit `composition.yaml` |
| **Section-level** | Regenerate one section, preserve others | `/regenerate-section` |
| **Pin-level** | Localized feedback at (section, bar, beat, instrument) | `/pin` |

Natural-language feedback (e.g., "the chorus feels weak") is translated to structured suggestions via `/feedback`, which maps 30+ phrases to specific adaptations.

### Trajectory System

Shape the emotional arc independently from notes, across 5 dimensions:

```yaml
trajectories:
  tension:
    type: bezier
    waypoints: [[0, 0.2], [16, 0.85], [32, 0.3]]
  density:
    type: stepped
    sections: { intro: 0.3, verse: 0.5, chorus: 0.9, outro: 0.3 }
```

Dimensions: **tension**, **density**, **predictability**, **brightness**, **register height**.

---

## Arrangement Engine

Transform an existing piece into a new style while preserving what matters:

```bash
/arrange my-song --target-genre lofi_hiphop --preserve melody,form
```

Operations: **regroove**, **reharmonize**, **reorchestrate**, **retempo**, **transpose**. Each transformation generates a diff report and respects preservation contracts.

---

## Output Formats

| Format | Notes |
|---|---|
| MIDI | Default output with per-instrument stems |
| WAV | Requires FluidSynth + SoundFont |
| MusicXML | Import into Finale, MuseScore, Sibelius |
| LilyPond / PDF | Publication-quality engraving |
| Reaper RPP | DAW project with per-track MIDI |
| Strudel | Live-coding notation for browser playback |

---

## Ensemble Constraints

Inter-part validation for multi-instrument arrangements:

| Rule | What It Checks |
|---|---|
| `register_separation` | Instruments maintain minimum distance |
| `downbeat_consonance` | Bass-melody consonance on strong beats |
| `no_parallel_octaves` | No parallel octave motion between parts |
| `no_frequency_collision` | Parts don't overlap excessively in pitch |
| `bass_below_melody` | Bass stays in lower register |

---

## StyleVector (Copyright-Safe)

Abstract features for style comparison -- never includes melody, chords, or hooks:

| Feature | Dims | Safe Because |
|---|---|---|
| interval_class_histogram | 12 | No sequence order |
| chord_quality_histogram | 8 | No progression order |
| cadence_type_distribution | 4 | Aggregate only |
| rhythm_complexity | 1 | Single statistic |
| harmonic_rhythm | 1 | Rate only |
| register_distribution | 12 | Octave histogram |

**Forbidden features**: melody_contour, chord_sequence, chord_progression, lyrics, hook

---

## CLI Reference

| Command | Description |
|---|---|
| `yao conduct "<description>"` | Natural language to MIDI with auto-iteration |
| `yao compose <spec>` | Generate from YAML spec (single pass) |
| `yao regenerate-section <project> <section>` | Regenerate one section |
| `yao render <midi>` | Render MIDI to WAV |
| `yao validate <spec>` | Validate spec YAML |
| `yao evaluate <project>` | Evaluate latest iteration |
| `yao critique <project>` | Adversarial critique |
| `yao diff <spec> --seed-a N --seed-b M` | Compare two stochastic generations |
| `yao explain <spec>` | Query provenance decisions |
| `yao new-project <name>` | Create project skeleton |
| `yao preview <spec>` | In-memory generate + play (no file output) |
| `yao watch <spec>` | Auto-regenerate on file change |
| `yao arrange <project>` | Transform into another style |
| `yao rate <project>` | Interactive 5-dimension rating |
| `yao reflect ingest` | Aggregate ratings into UserStyleProfile |

---

## Architecture

YaO uses an 8-layer architecture with strict downward-only dependency flow, enforced by CI:

```
Layer 7: Reflection & Learning       (reflect/, agents/)
Layer 6: Verification & Critique     (verify/ -- 35 rules, aesthetic metrics, acoustic evaluation)
Layer 5: Rendering                   (render/ -- MIDI, WAV, MusicXML, LilyPond, Reaper, Strudel)
Layer 4.5: Performance Expression    (generators/performance/ -- articulation, dynamics, microtiming)
Layer 4: Perception                  (perception/ -- audio features, style vectors, surprise, use-case eval)
Layer 3.5: Musical Plan IR           (ir/plan/ -- form, harmony, motif, phrase, arrangement, drums, conversation)
Layer 3: Score IR                    (ir/ -- note, part, section, voicing, timing, hook, dynamics_shape, groove)
Layer 2: Generation Strategy         (generators/ -- plan generators, note realizers, reactive fills)
Layer 1: Specification               (schema/, sketch/ -- YAML specs, NL compiler, hooks, groove)
Layer 0: Constants                   (constants/ -- 46 instruments, 28 scales, 20 forms, 14 chords)
```

Layer boundaries are enforced by `tools/architecture_lint.py` -- lower layers never import upper layers.

---

## Multi-Genre Capabilities

YaO supports 22 genre skills with genre-specific evaluation weights, chord palettes, and instrumentation defaults:

| Genre | Key Feature | Example |
|---|---|---|
| **Cinematic** | Wide trajectory arcs, orchestral texture evolution | `yao conduct "epic orchestral trailer building to brass climax"` |
| **Lo-fi Hip Hop** | Loop evolution, tape saturation sound design | `yao conduct "lofi study beat, 82 BPM, dusty Rhodes chords"` |
| **J-Pop** | Complex form (verse/pre-chorus/chorus/D-melody), vocal singability | `yao conduct "J-pop chorus with wide melodic range and key change"` |
| **Ambient** | Drone-safe evaluation, texture-first composition | `yao conduct "ambient drone, single evolving pad, 5 minutes"` |
| **Deep House** | Four-on-the-floor, loop architecture, filter evolution | `yao conduct "deep house 122 BPM, Rhodes chords, sub bass"` |
| **Jazz** | Jazz swing grooves, extended chord voicings | `yao conduct "jazz ballad, brushed drums, walking bass"` |
| **Classical** | Baroque, romantic, and orchestral styles | `yao conduct "string quartet in late Romantic style, D minor"` |
| **World** | Bossa nova, Celtic, Indian classical, Arab maqam | `yao conduct "bossa nova for nylon guitar and soft percussion"` |

---

## Audio Rendering

Requires FluidSynth and a General MIDI SoundFont:

```bash
# macOS
brew install fluid-synth

# Linux
sudo apt-get install fluidsynth
```

Place a `.sf2` file in `soundfonts/`, then use `/render` or `yao render`.

---

## Project Structure

```
src/yao/           241 Python modules
  constants/       46 instruments, 28 scales, 20 forms, 14 chords, MIDI maps
  schema/          Pydantic specs (v1 + v2 + v3 composability), genre profiles
  sketch/          NL -> spec compiler (EN + JP), 6-turn dialogue
  ir/              Score IR + Plan IR (MPIR) + Hook, Groove, Conversation, TensionArc
  generators/      Note realizers, plan generators, performance pipeline,
                   melodic strategies, reactive fills, frequency clearance
  perception/      Audio features, StyleVector, surprise scorer, use-case eval,
                   listening simulator
  verify/          Evaluator, 35 critique rules, aesthetic metrics,
                   acoustic divergence, constraint checker
  reflect/         Provenance (causal graph), style profile, ratings
  conductor/       Generate-evaluate-adapt loop, multi-candidate, audio feedback
  subagents/       7 Python subagent implementations
  agents/          Backend protocol (PythonOnly, Anthropic API)
  render/          MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel
  mix/             EQ, compression, reverb, mastering (pedalboard-based)
  arrange/         Style transfer, source extraction, preservation contracts
  feedback/        Pin IR, NL translator, pin-aware regenerator
  improvise/       Real-time improvisation engine
  audition/        Browser-based A/B comparison UI
  annotate/        Browser-based time-range annotation UI
  skills/          Genre skill loader + registry (22 genres)
  runtime/         Project runtime (undo/redo, caching, lockfile)
tests/             259 test files, ~2,157 test functions
tools/             17 CI tools (honesty, architecture lint, genre calibration)
.claude/           Agent prompts, slash commands, genre skills, guides
docs/              Architecture docs, design docs, audit reports
development/       Contributor guide, API reference, roadmap
```

---

## CI and Quality

```bash
make all-checks    # Full quality pipeline (lint + arch-lint + tests + golden + honesty)
make test          # All tests (~2,157)
make lint          # ruff + mypy strict
make arch-lint     # Layer boundary enforcement
make test-golden   # Golden MIDI regression tests
make test-acoustic # Audio feature regression (weekly CI)
make honesty-check # Verify no stub features marked as complete
make backend-honesty
make plan-consumption
make skill-grounding
make critic-coverage
make calibrate-genres  # Genre profile parameter sweep
```

5 honesty tools run in CI to verify that features actually work, not just exist.

---

## Optional Dependencies

| Extra | Install | Features |
|---|---|---|
| `dev` | `pip install -e ".[dev]"` | pytest, mypy, ruff, pre-commit |
| `neural` | `pip install -e ".[neural]"` | Stable Audio texture generation (torch, transformers) |
| `live` | `pip install -e ".[live]"` | Real-time MIDI improvisation (mido, python-rtmidi) |
| `annotate` | `pip install -e ".[annotate]"` | Browser-based A/B audition and annotation UI (FastAPI) |

---

## Design Philosophy

1. **The agent is an environment, not a composer** -- accelerates human creativity
2. **Every decision is explainable** -- provenance records why each note exists
3. **Constraints liberate** -- specs and rules are scaffolding, not cages
4. **Time-axis first** -- trajectory curves define the arc; notes fill details
5. **The human ear is the final truth** -- automated scores inform; humans decide
6. **Vertical alignment** -- input, processing, evaluation advance together
7. **Acoustic truth complements symbolic truth** -- symbolic metrics necessary, never sufficient

---

## Documentation

| Document | Purpose |
|---|---|
| [FEATURE_STATUS.md](FEATURE_STATUS.md) | Single source of truth for capabilities |
| [PROJECT.md](PROJECT.md) | Full design (v2.0) |
| [CLAUDE.md](CLAUDE.md) | Development rules and conventions |
| [VISION.md](VISION.md) | Target architecture |
| [docs/](docs/) | Architecture, tutorials, reference, audit reports |
| [development/](development/) | Contributor guide, API reference, roadmap |

---

## License

MIT
