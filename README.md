# You and Orchestra (YaO)

**Describe music in plain language. Get a full MIDI score with stems, quality evaluation, and a log explaining every decision.**

YaO is an agentic music production environment built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code). You give it an idea — a sentence, a conversation, or a detailed YAML spec — and it runs a multi-stage generation pipeline with AI subagents, 35 adversarial critique rules, and automatic iteration until quality thresholds pass. Everything is explainable: every note carries a provenance record explaining why it exists.

> Your vision. Your taste. Your soul. — and an Orchestra ready to listen, respond, and surprise.

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

Launch Claude Code in the project directory:

```bash
claude
> /sketch a melancholic piano piece for studying on a rainy evening
```

The `/sketch` command walks you through a 6-turn dialogue to refine your idea into a complete specification. Then `/compose`, `/critique`, and `/render` to generate, evaluate, and render audio.

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

```
/conduct epic orchestral trailer music building to a massive brass climax
```

The Conductor generates, evaluates, adapts, and regenerates — up to 3 iterations — until quality thresholds pass.

### 3. YAML spec (full control)

Create a project and edit the spec directly:

```
/sketch my-piece
# Edit specs/projects/my-piece/composition.yaml to taste
/compose my-piece
```

Three spec formats are available:

- **Simple** — Flat YAML for quick experiments
- **Detailed** — Multi-section spec with full control over melody, harmony, rhythm, arrangement, and production
- **Composable** — Specs with `extends`, `overrides`, and reusable fragments

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
/sketch big band swing, 160 BPM, walking bass, ride cymbal, trumpet section melody in unison then harmony soli, trombone counter-melody, saxophone shout chorus at climax, 120 seconds
```

---

## What You Get

Each generation creates a versioned iteration (`v001`, `v002`, ...) so nothing is ever lost:

```
outputs/projects/my-piece/iterations/v001/
  full.mid           # Complete MIDI score
  stems/             # Per-instrument MIDI stems
    piano.mid
    violin.mid
    ...
  analysis.json      # Structural analysis
  evaluation.json    # Quality scores (6 dimensions)
  provenance.json    # Causal graph of every decision
```

---

## How It Works

### The Generation Pipeline

YaO separates *what to play* from *how to play it*. Plan generators decide structure, harmony, motifs, rhythm, and orchestration. Then a note realizer places concrete notes that execute the plan.

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
  -> [Step 6]  Note Realizer   -> ScoreIR (with harmonic coupling)
  -> [Step 6.5] Performance    -> Articulation, dynamics, microtiming
  -> [Step 7]  Renderer        -> MIDI / WAV / MusicXML / LilyPond / Score
  -> [Step 7.5] Listening Sim  -> PerceptualReport (LUFS, spectral, temporal)
  -> Evaluator (6 dimensions)  -> Conductor feedback loop (up to 3 iterations)
```

### Subagents

YaO models the roles of a real music production team:

| Subagent | Role | Key Output |
|---|---|---|
| **Producer** | Coordinates all agents, resolves conflicts | SongFormPlan |
| **Composer** | Melodies, motifs, thematic development | MotifPlan + PhrasePlan |
| **Harmony Theorist** | Chord progressions, cadences, modulations | HarmonyPlan |
| **Rhythm Architect** | Drum patterns, grooves, syncopation | DrumPattern + GrooveProfile |
| **Orchestrator** | Instruments, voicings, register separation | ArrangementPlan |
| **Mix Engineer** | EQ, compression, reverb, loudness | ProductionManifest |
| **Adversarial Critic** | Finds weaknesses — never praises | Structured Findings |

Subagents run via **PythonOnlyBackend** (default, no API key needed) or **AnthropicAPIBackend** (real LLM calls with structured output).

### The Combination Stack

The **Combination & Coupling** layer provides 11 modules that turn YaO's material library into genuinely diverse output. These modules sit between raw generation and the IR layer, coupling melody to harmony, optimizing voice leading, and enabling genre blending.

| Module | What It Does |
|---|---|
| **Chord-Aware Melody** | Scores every melody pitch against the active chord |
| **Voice-Leading Optimizer** | Minimizes total voice motion between chords |
| **Reharmonization Engine** | 12 operations (tritone sub, secondary dominant, ii-V insertion, ...) |
| **Rhythm Markov Generator** | Genre-conditioned rhythm onset patterns |
| **Modulation Planner** | 7 key-modulation strategies (pivot chord, direct, chromatic, ...) |
| **Harmonic Devices Library** | 15 genre-typical chord patterns (turnarounds, cadences, blues forms) |
| **Phrase-Shape Generator** | Antecedent/consequent phrase structures |
| **Theme Recurrence Graph** | Long-form thematic coherence across sections |
| **Genre Vector Space** | 12-dimension genre embedding with n-way blending |
| **Polyrhythm Engine** | Multi-layer rhythmic textures at arbitrary ratios |
| **Listening-Agent Dialog** | Turn-based ensemble generation (instruments respond to each other) |

All coupling modules are **feature-flagged** — they return input unchanged when disabled. The existing pipeline is never broken.

---

## Generation Strategies

Nine registered generators cover a spectrum from deterministic to probabilistic to experimental:

| Strategy | Description |
|---|---|
| **rule_based** | Deterministic, chord-aware, motif placement |
| **stochastic** | Seed + temperature controlled, contour-shaped |
| **markov** | Probabilistic transitions from 15 genre-specific pitch models |
| **phrase_aware** | Four-layer pipeline (phrase plan -> skeleton -> surface -> ornament) |
| **twelve_tone** | Serialist composition using P/I/R/RI tone rows |
| **process_music** | Minimalist generative processes (phasing, additive, subtractive) |
| **constraint_solver** | Backtracking search with hard constraints |
| **loop_evolution** | Loop-first iterative design with layer evolution |
| **ai_seed** | LLM-generated motif seeds (optional Anthropic API) |

### Melodic Strategies

Eight strategies shape how pitches are chosen within any generator:

| Strategy | Character |
|---|---|
| contour_based | Arch/ascending/descending contour shaping |
| motif_development | Short motif with transformations (transpose, invert, retrograde, augment, diminish, sequence) |
| linear_voice | Stepwise motion, classical voice-leading |
| arpeggiated | Broken chord patterns |
| scalar_runs | Scale runs in sequences |
| call_response | Alternating question-answer phrases |
| pedal_tone | Revolves around a repeated note |
| hocketing | Register jumps (high-low alternation) |

---

## Music Theory Support

### Instruments (54)

46 Western instruments across keyboard, strings, guitar, bass, brass, woodwind, saxophone, synth, and percussion families. Plus 8 non-Western instruments with culturally appropriate ranges and idiomatic techniques:

**shakuhachi** (Japanese bamboo flute) | **koto** (13-string zither) | **shamisen** (3-string lute) | **taiko** (drum) | **sitar** (Indian plucked string) | **tabla** (pair of drums) | **oud** (fretless lute) | **ney** (end-blown flute)

### Scales (28)

14 Western scales (major, minor, harmonic minor, melodic minor, dorian, mixolydian, lydian, phrygian, locrian, pentatonic major/minor, blues, whole tone, chromatic) plus 14 extended tuning systems:

- **Japanese**: hirajoshi, iwato, in, minyo, ritsu, yo
- **Indian**: raga Yaman, Bhairav, Todi, Marwa, Darbari
- **Arab/Turkish**: maqam Rast, Bayati, Hijaz, Kurd, Nahawand
- **Southeast Asian**: gamelan pelog, slendro
- **Western extended**: just intonation major

All defined in cents-based `ScaleDefinition` objects supporting microtonal precision.

### Tonal Systems (10 kinds)

`tonal_major_minor` | `modal` | `pentatonic` | `blues` | `microtonal` | `atonal` | `drone` | `raga` | `maqam` | `custom`

### Harmony

- 14 chord types (major, minor, diminished, augmented, dom7, maj7, min7, dim7, half-dim7, sus2, sus4, add9, min9, maj9)
- Functional harmony with Roman numeral analysis (I, ii, V7/V, vii, etc.)
- Voice-leading detection (parallel fifths/octaves)
- 15 harmonic devices (jazz turnaround, gospel walkdown, 12-bar blues, Coltrane changes, ii-V-I, Neapolitan approach, circle of fifths, tritone substitution, etc.)

### Rhythm

- 31 rhythm templates spanning jazz, rock, pop, Latin, electronic, classical, world
- 20 groove profiles for ensemble-wide microtiming (jazz swing, bossa nova, funk, afrobeat, samba, lo-fi hip hop, drum & bass, etc.)
- 15 drum patterns across time signatures (4/4, 3/4, 5/4, 6/8, 7/8)
- 12 rhythm Markov models for genre-conditioned onset patterns
- 15 pitch Markov models per genre (bebop, blues, modal dorian, celtic, bossa nova, flamenco, raga, maqam, impressionist, J-pop, classical, ambient, etc.)

### Form

20 song forms: AABA, verse-chorus-bridge, rondo, blues 12-bar/16-bar, sonata, fugue, theme & variations, binary, ternary, arch form, through-composed, J-pop, game BGM (intro-loop), ambient throughflow, minimalist phasing.

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

### Combination Stack Metrics

- **Melody-Harmony Alignment** — scores each melody note against the chord active at that position (target: >= 0.7 overall, >= 0.85 on downbeats)
- **Voice-Leading Smoothness** — total voice motion relative to the theoretical minimum (target: <= 1.5x for common practice, <= 2.0x for jazz)

### Acoustic Evaluation

| Category | Metrics |
|---|---|
| Loudness | Integrated LUFS, short-term curve, peak dBFS, dynamic range |
| Spectral | Centroid, rolloff, flatness, 7-band energy, masking risk |
| Temporal | Onset density per section, tempo stability |
| Use-case | YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic |

### Adversarial Critique (35 Rules)

A panel of automated critics, each specialized to find specific weaknesses:

| Category | Rules |
|---|---|
| Structural | Section monotony, climax absence, form imbalance |
| Melodic | Contour monotony, motif recurrence, phrase closure |
| Harmonic | Cliche progression, cadence weakness, harmonic monotony |
| Rhythmic | Rhythmic monotony, syncopation lack |
| Arrangement | Frequency collision, texture collapse |
| Emotional | Intent divergence, trajectory violation |
| Genre Fitness | Tempo out of range, instrument mismatch |
| Memorability | Hook weakness, motif absence |
| Surprise | Surprise deficit, surprise overload |
| Hook | Hook overuse, underuse, misplacement |
| Groove | Groove inconsistency, microtiming flatness, ensemble conflict |
| Conversation | Conversation silence, voice ambiguity, fill absence |
| Acoustic | Symbolic-acoustic divergence, LUFS violation, spectral imbalance, brightness-intent mismatch |

---

## Slash Commands

All interaction happens through Claude Code slash commands:

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
| `/pin <project> <location> <note>` | Attach localized feedback to bars/beats/instruments |
| `/feedback <project> <text>` | Natural-language feedback translated to structured suggestions |

---

## Feedback and Iteration

Three levels of granularity:

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

```
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

## Architecture

YaO uses an 8-layer architecture with strict downward-only dependency flow, enforced by an AST-based import checker in CI:

```
Layer 7: Reflection & Learning       (reflect/, agents/, runtime/)
Layer 6: Verification & Critique     (verify/ - 35 rules, aesthetic metrics, acoustic eval)
Layer 5: Rendering                   (render/ - MIDI, WAV, MusicXML, LilyPond, Reaper, Strudel)
Layer 4: Perception                  (perception/ - audio features, style vectors, surprise, use-case eval)
Layer 3: Score IR                    (ir/ - note, part, section, voicing, timing, phrase, skeleton, melody)
Coupling: Combination & Coupling     (coupling/ - 11 modules, Combination Stack)
Layer 2: Generation Strategy         (generators/ - plan generators, note realizers, melody pipeline)
Layer 1: Specification               (schema/, sketch/ - YAML specs, NL compiler, feature flags)
Layer 0: Constants                   (constants/ - instruments, scales, forms, chords, profiles)
```

Layer boundaries are enforced by `tools/architecture_lint.py` — lower layers never import upper layers.

### The Phrase-First Melody Pipeline (Layer 2)

Inside Layer 2, melodies are generated through a four-stage sub-pipeline:

```
M1: Phrase & Motif Plan    -> phrase boundaries, cadence types, motif selection
M2: Skeleton Generation    -> chord-tone targets at metrically strong positions
M3: Surface Realization    -> passing tones, neighbor tones, rhythm templates
M4: Ornament & Articulation -> grace notes, trills, slides, microtiming
```

When `features.chord_aware_melody` is enabled (the default), M2 scores every candidate pitch against `HarmonicMelodyConstraints` derived from the active chord — transforming melodies from "scale-walking" to "harmonically functional."

---

## Feature Flags

The Combination Stack is controlled by feature flags in the composition spec:

```yaml
features:
  chord_aware_melody: true        # M2 scores pitches against chord constraints
  voice_leading_optimization: true # Orchestrator uses voice-leading optimizer
  reharmonization: false           # Opt-in: apply reharmonization operations
```

When a flag is off, the module returns its input unchanged — existing behavior is preserved bit-identically.

---

## Multi-Genre Capabilities

25 melodic profiles with genre-specific interval distributions, phrase conventions, ornament profiles, and anti-patterns:

| Genre Category | Profiles |
|---|---|
| **Jazz** | Bebop, modal jazz, jazz ballad |
| **Rock** | Classic rock, progressive rock |
| **Pop** | J-Pop ballad, K-Pop |
| **Electronic** | House, ambient, progressive electronic |
| **Latin** | Bossa nova, salsa |
| **Classical** | Baroque, romantic |
| **World** | Celtic, reggae, bluegrass, folk |
| **Urban** | Lo-fi hip hop, funk, soul/R&B, gospel |
| **Other** | Blues, country, metal, cinematic |

Each profile drives every decision in the pipeline — interval weights, chord-tone targeting, syncopation density, ornament probabilities, motif transformation preferences, and anti-pattern rules.

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

Abstract features for style comparison — never includes melody, chords, or hooks:

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

## Audio Rendering

Requires FluidSynth and a General MIDI SoundFont:

```bash
# macOS
brew install fluid-synth

# Linux
sudo apt-get install fluidsynth
```

Place a `.sf2` file in `soundfonts/`, then use `/render` in Claude Code.

---

## Gallery

Four pre-generated demonstration pieces with audio and full specs:

| Audio | Description |
|---|---|
| [short-anime-v1.mp3](https://drive.google.com/file/d/1GRhr3dlH41BJ4krFNCKvYfLiWLQif0fR/view?usp=drive_link) | 28-second anime J-rock opening in Bb major, 165 BPM. Electric guitar lead with driving energy. |
| [short-string-v1.mp3](https://drive.google.com/file/d/1Kex9F1l6jbAROb7GIS4NM9a4ILApJuwm/view?usp=drive_link) | 29-second Romantic-era string ensemble miniature in A major, 90 BPM. Elegant and tender. |
| [short-jazz-v1.mp3](https://drive.google.com/file/d/1KXKeYuJo9H2OpNybEmV8OSM7nCiFh6nN/view?usp=drive_link) | 30-second cool jazz for a midnight bar in Bb minor, 80 BPM. Tenor sax, piano, contrabass, drums. |
| [puzzle-light.mp3](https://drive.google.com/file/d/1Pq8btcpo1iOjKxffWGm1IhSksUxxOynu/view?usp=drive_link) | 29-second light puzzle game BGM in C major, 90 BPM. Loopable and cheerful. |

Each gallery directory contains the full `composition.yaml`, `trajectory.yaml`, and `intent.md` used for generation.

---

## CI and Quality

```bash
make all-checks     # Full quality pipeline
make test           # All tests (~2,500+ test functions across 256 files)
make lint           # ruff + mypy strict
make arch-lint      # Layer boundary enforcement (AST-based)
make test-coupling  # Combination Stack tests
make test-diversity # Diversity scenario tests
make test-golden    # Golden MIDI regression tests
make test-melody    # Melody pipeline tests
make markov-validate # Validate all Markov model YAMLs
make device-validate # Validate harmonic device YAMLs
make honesty-check  # Verify no stub features marked as complete
make calibrate-genres # Genre profile parameter sweep
```

Five honesty tools run in CI to verify that features actually work, not just exist.

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

1. **The agent is an environment, not a composer** — accelerates human creativity, never replaces it
2. **Every decision is explainable** — provenance records why each note exists
3. **Constraints liberate** — specs and rules are scaffolding, not cages
4. **Time-axis first** — trajectory curves define the arc before notes fill details
5. **The human ear is the final truth** — automated scores inform; humans decide
6. **Phrase before notes** — phrases have function, target pitch, and cadence; notes are derived
7. **Genre is a constellation** — a `MelodicProfile` with dozens of parameters, not a string label
8. **Diversity through combination** — the Combination Stack turns existing materials into genuinely varied output

---

## Documentation

| Document | Purpose |
|---|---|
| [FEATURE_STATUS.md](FEATURE_STATUS.md) | Single source of truth for all capabilities |
| [PROJECT.md](PROJECT.md) | Full architecture and design |
| [CLAUDE.md](CLAUDE.md) | Development rules, current phase, escalation guide |
| [IMPROVEMENT.md](IMPROVEMENT.md) | Gap analysis and diversity improvement roadmap |
| [development/](development/) | API reference, generator guide, spec system, testing strategy, contributing |
| [docs/](docs/) | MkDocs site with tutorials, glossary, and architecture deep-dives |

---

## License

MIT
