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

## Phase 2: Claude Agent SDK -- COMPLETE (2026-05-14)

The Agent SDK surface makes YaO driveable from any Python program. Seven sub-phases delivered:

| Phase | Feature | Key Deliverable |
|---|---|---|
| 2A | SDK Foundation | In-process MCP server (15 tools), `default_yao_options()`, Lane B raw access |
| 2B | Lane A Facade | `YaoAgent` class (10 async-generator methods), 9 streaming events, 9 typed results |
| 2C | Hooks & Permissions | 4 standard hooks, `default_yao_permission()` callback, protected-path enforcement |
| 2D | Programmatic Subagents | `yao_agent_definitions()` Markdown parser, parity guarantee G2 |
| 2E | Sessions & Streaming | Project-scoped sessions, JSON-Schema outputs, `fork_session`, `tag_session` |
| 2F | Reference Applications | 5 examples: minimal, web (FastAPI+SSE), Discord bot, CI pipeline, Jupyter notebook |
| 2G | Documentation | 6 SDK doc pages, design summary ADR, CLAUDE.md SDK section |

**Post-2G gap fixes (commit 03438ff):** Wired hooks/agents/permissions into `default_yao_options`, added `YaoAgent.interrupt()` and `set_permission_mode()`, structured error payloads, per-subagent tool restrictions and effort tuning, CLI commands `yao agent` and `yao serve`.

**Parity guarantees (G1--G5):** Same files, same subagent reasoning, same Conductor loop, same provenance/outputs, same constraint/lint results across all three surfaces. 164 SDK tests + 196 existing tests = 360 total, zero Phase 1 regressions.

---

## Diversity Foundation -- COMPLETE (2026-05-14)

Introduced the Combination & Coupling layer with 11 modules:

| Module | Status | Key Deliverable |
|---|---|---|
| §4.1 Chord-Aware Melody | Complete | `HarmonicMelodyConstraints` IR, `derive_constraints()`, M2 wire-up, 5 `CouplingStyle` profiles |
| §5.4 Voice-Leading Optimizer | Complete | `optimal_voicing_transition()` with Hungarian assignment, `VoicingConstraints` schema |
| §5.1 Reharmonization Engine | Complete | 12 reharmonization operations, `ReharmonizationConstraints`, `/reharmonize` command |

Coupling infrastructure is in place: `src/yao/coupling/` contains 11 modules, `src/yao/ir/harmonic_melody_constraints.py` defines core IR types, `src/yao/schema/features.py` provides feature flags, and `src/yao/verify/melody_harmony_alignment.py` + `voice_leading_smoothness.py` provide evaluation metrics.

---

## Phase 3: Engine Expansion -- COMPLETE (2026-05-16)

| Component | Key Deliverable |
|---|---|
| C1: Synth/Electronic | Expanded from 4 to 24 GM synth instruments (leads, pads, FX) |
| C2: Perception Layer | 8 modules: StyleVector, MoodProfile, ReferenceMatcher, SurpriseAnalyzer, AudioPerceptionAnalyzer, ListeningSimulator, UseCaseEvaluator |
| D1: Arrangement Engine | 7 modules: ArrangementOperation ABC, reorchestrate, reharmonize, retempo, transpose, regroove |
| D2: AI Bridge | ai_seed.py (Claude API motif expansion), stable_audio_bridge.py (texture generation). Feature-flagged |
| D3: Vocal/Lead | VocalNote/LyricsLine IR, VocalSpec schema, vocal_lead role |
| Layer 7: Reflection | UserStyleProfile with update_from() and update_from_outcome() |

## Phase 4: Production Integration -- COMPLETE (2026-05-16)

| Component | Key Deliverable |
|---|---|
| DAW Integration (MCP) | DAWMCPBridge with Reaper TCP backend, MIDI import/export, DAWBackend ABC |
| Live Improvisation | `yao improvise` CLI wired to RealtimeImprovisationEngine |
| Vocal Synthesis Bridge | VocalSynthBridge ABC, NeutrinoBridge stub, MidiVocalFallback |
| A/B Testing Framework | Hypothesis, Variant, ABTestResult, Cohen's d effect size, `yao ab-test` CLI |
| Cross-Project Style | ProjectFingerprint, compute_fingerprint(), fingerprint_distance() |

## Phase 5: Tests, Guides & Documentation -- COMPLETE (2026-05-16)

| Component | Key Deliverable |
|---|---|
| Developer Guides | 11 guides in `.claude/guides/` (architecture, coding, music engineering, testing, workflow, drum/genre development, neural, cookbook, matrix discipline) |
| Documentation Site | 39 documentation pages across 7 sections (guides, design, getting-started, sdk, tutorials, reference) |
| Test Expansion | 332 test files with comprehensive coverage across all phases |
| Genre Coverage | 30 genre profiles, 46 genre skill files, 34 genre templates |

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
| Phase 2 SDK (complete) | ~2,823 |
| Diversity Foundation | ~2,900+ |
| Phases 3--5 (complete) | **~4,000+** |

---

## Current Capabilities

Everything below is implemented, tested, and verified by CI honesty tools:

- 302 Python source modules (including 11 coupling modules + 14 SDK modules)
- 332 test files with ~4,000+ tests (including `tests/unit/coupling/` + `tests/sdk/`)
- 9 generation strategies + 8 melodic strategies
- 34 critique rules across 15 categories
- 46 instruments (9 families), 33 scales, 20 forms, 30 chords
- 15 drum patterns, 20 groove profiles
- 25 melodic profile YAMLs, 31 rhythm template YAMLs
- 15 harmonic device YAMLs (jazz turnarounds, blues patterns, Coltrane changes, etc.)
- 29 Markov model YAMLs organized by type: 14 pitch, 12 rhythm, 3 contour
- 30 genre profiles, 46 genre skill files, 34 genre templates, 3 culture skills
- 11 agent definitions, 11 slash commands (including cover-art)
- 7 output formats (MIDI, WAV, MusicXML, LilyPond, Reaper RPP, Strudel, cover art PNG)
- 7 use-case evaluators (YouTube BGM, Game BGM, Ad, Study, Meditation, Workout, Cinematic)
- 5 honesty check tools enforced in CI
- Mix chain with per-track EQ, compression, reverb + master (pedalboard-based)
- Multilingual spec compilation (English + Japanese)
- 151 example project specs across diverse genres
- Feature flags schema (`src/yao/schema/features.py`) for gating Combination Stack modules
- New evaluation metrics: melody-harmony alignment, voice-leading smoothness
- Agent SDK surface: `YaoAgent` facade (Lane A) + raw SDK access (Lane B), 15 in-process MCP tools, 9 streaming events, 9 typed results
- 5 SDK reference applications (minimal, web, Discord, CI, notebook)
- 6 SDK documentation pages in `docs/sdk/`
- G1--G5 surface parity guarantees enforced in CI

---

## Post-Phase Additions (2026-05-17)

| Feature | Key Deliverable |
|---|---|
| Cover Art Generation | `src/yao/render/cover_art.py`, Gemini-powered album art, `yao cover-art` CLI, `/cover-art` slash command, style/mood configuration |
| Multi-Act Compositions | Three-act structure demonstrated: ambient soundscape → piano cadenza (terror) → return and fade. 13 sections, 50 bars, 9 instruments (ambient-v4) |
| Percussion-Only Pieces | Drums-only composition pipeline: bass drum + snare + tenor drum, 96 bars at 174 BPM, polyrhythmic interlocking patterns (primal-trio) |

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
- **Cloud API server** -- expose YaO as a web service (SDK reference apps provide a starting point)
- **Full microtonal MIDI rendering** -- MPE-based per-note pitch bend for non-12TET tunings
- **Genre-driven dynamic evaluation weights** -- evaluation criteria that adapt to the genre being composed
