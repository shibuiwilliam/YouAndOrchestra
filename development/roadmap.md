# Development Roadmap

## Value-Driven Milestones

### Milestone 1: "Describe and Hear" -- COMPLETE
**User value:** Describe what you want in YAML, generate it, hear it.

**Delivered:** CLI pipeline, 2 generators, 4 templates, trajectory dynamics, versioning, provenance.

### Milestone 2: "Iterate and Improve" -- COMPLETE
**User value:** Tell YaO what you don't like, and it improves.

**Delivered:** Conductor loop, NL composition, section regeneration, 10-metric evaluation, 7 slash commands, 7 subagents.

### Milestone 3: "Richer Music" -- COMPLETE
**User value:** Music sounds professional with proper harmony, rhythm, dynamics.

**Delivered:** Harmony IR, motif transforms, voice leading, constraints, detailed spec format, CPIR foundation, MetricGoal, RecoverableDecision.

---

## Phase gamma: Eight Structural Improvements -- COMPLETE (2026-05-04)

Delivered the eight structural improvements from PROJECT.md:

| Phase | Feature | Key Deliverable |
|---|---|---|
| gamma.1 | Surprise Score + Tension Arcs | SurpriseScorer, TensionArc IR, 3 critique rules |
| gamma.2 | Acoustic Truth | PerceptualReport, ListeningSimulator, 7 use-case evaluators, 5 acoustic divergence rules |
| gamma.3 | Hook IR + Phrase Dynamics | Hook with DeploymentStrategy, DynamicsShape, HooksSpec, 4 critique rules |
| gamma.4 | Ensemble Groove | GrooveProfile IR, 20 groove profiles, GrooveApplicator, GrooveSpec, 3 critique rules |
| gamma.5 | Conversation Plan | ConversationPlan, reactive fills, frequency clearance, 4 critique rules |
| gamma.6 | Diversity Sources | 20-form library, 8 melodic generation strategies |
| gamma.7 | Multilingual | Japanese SpecCompiler (50+ emotion words, valence x arousal), 3 culture skills, 8 non-Western instruments |

## Phase delta: Production Features -- COMPLETE (2026-05-04)

| Phase | Feature | Key Deliverable |
|---|---|---|
| delta.1 | Arrangement Engine | SourcePlanExtractor (MIDI to MusicalPlan), StyleVectorOps, PreservationContract, DiffWriter, 5 transformation operations |
| delta.2 | Three-Tier Feedback | Pin IR (localized), NL translator (30 phrases), pin-aware regenerator |

---

## Honesty, Alignment, and Depth -- COMPLETE

| Focus | Key Deliverable |
|---|---|
| Honesty | Composer subagent, AnthropicAPIBackend, SpecCompiler 3-stage, NoteRealizer (100% plan consumption), golden tests |
| Alignment | Genre skill integration (22 genres), aesthetic metrics (surprise, memorability, contrast, pacing), audio feedback loop |
| Depth | Performance expression pipeline (articulation, dynamics, microtiming, CC curves), ensemble constraints, causal provenance graph |

---

## Diversity Foundation -- ACTIVE (started 2026-05-08)

The highest-leverage current effort. Introduces the Combination & Coupling layer with the three highest-impact modules:

| Module | Status | Key Deliverable |
|---|---|---|
| §4.1 Chord-Aware Melody | In progress | `HarmonicMelodyConstraints` IR, `derive_constraints()`, M2 wire-up, 5 `CouplingStyle` profiles |
| §5.4 Voice-Leading Optimizer | In progress | `optimal_voicing_transition()` with Hungarian assignment, `VoicingConstraints` schema |
| §5.1 Reharmonization Engine | In progress | 12 reharmonization operations, `ReharmonizationConstraints`, `/reharmonize` command |

Coupling infrastructure is in place: `src/yao/coupling/` contains 13 modules, `src/yao/ir/harmonic_melody_constraints.py` defines core IR types, `src/yao/schema/features.py` provides feature flags, and `src/yao/verify/melody_harmony_alignment.py` + `voice_leading_smoothness.py` provide evaluation metrics.

### Upcoming Work

| Focus | Key Deliverables |
|---|---|
| Genre Diversification | 15+ pitch Markov models, rhythm Markov generator, harmonic devices library, modulation planner |
| Structural Diversity | Phrase-shape generator, theme recurrence graph, variable harmonic rhythm |
| Cross-Cutting Diversity | Genre vector n-way blending, idiomatic gestures, polyrhythm engine |
| Advanced Ensemble | Listening agents, corpus learning, metric modulation, microtonal melody |
| Production Integration | DAW integration, live improvisation, user preference learning |

---

## Test Coverage Growth

| Milestone | Tests |
|---|---|
| Describe and Hear | ~200 |
| Iterate and Improve | ~500 |
| Richer Music | ~1,094 |
| Honesty/Alignment/Depth | ~1,150 |
| Structural Improvements | ~1,680 |
| Production Features | ~1,748 |
| Combination Stack Foundation | ~2,157 |
| Current (Diversity Foundation in progress) | **~2,701** |

---

## Current Capabilities

Everything below is implemented, tested, and verified by CI honesty tools:

- 277 Python source modules (including 13 new coupling modules)
- 299 test files with ~2,701 tests (including `tests/unit/coupling/` with 12 test files)
- 8 generation strategies + 8 melodic strategies
- 35 critique rules across 15 categories
- 46 instruments (9 families), 28+ scales, 20 forms, 14 chords
- 15 drum patterns, 20 groove profiles
- 15 harmonic device YAMLs (jazz turnarounds, blues patterns, Coltrane changes, etc.)
- Markov models organized by type: pitch/, rhythm/, contour/
- 29+ genre skills, 3 culture skills
- 8 subagents (including Modulation Planner), 13 slash commands
- 6 output formats (MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel)
- 7 use-case evaluators (YouTube BGM, Game BGM, Ad, Study, Meditation, Workout, Cinematic)
- 5 honesty check tools enforced in CI
- Mix chain with per-track EQ, compression, reverb + master (pedalboard-based)
- Multilingual spec compilation (English + Japanese)
- 110+ example project specs across diverse genres
- Feature flags schema (`src/yao/schema/features.py`) for gating Combination Stack modules
- New evaluation metrics: melody-harmony alignment, voice-leading smoothness

---

## Future Directions

These are research directions, not committed roadmap items:

- **Live performance mode** -- real-time MIDI controller input (prototype exists in `src/yao/improvise/`)
- **Neural generator bridge** -- Stable Audio textures under YaO structural control (prototype exists in `src/yao/generators/neural/`)
- **DAW MCP integration** -- real bidirectional MCP connection to Reaper (interface defined, stub implementation)
- **Multi-model orchestration** -- different LLMs for different subagents
- **Community reference library** -- shared StyleVector format for collaboration
- **Backend-agnostic agents** -- Claude Code as one adapter among many
- **Video sync** -- align music to visual cues
- **Cloud API server** -- expose YaO as a web service
- **Full microtonal MIDI rendering** -- MPE-based per-note pitch bend for non-12TET tunings
- **Genre-driven dynamic evaluation weights** -- evaluation criteria that adapt to the genre being composed
