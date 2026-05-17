# YaO Development Documentation

Technical documentation for contributors and AI agents developing YaO.

## Guides

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | Layer model, dependency rules, pipeline, key types |
| [api-reference.md](api-reference.md) | Public API surface, module-by-module reference |
| [generator-guide.md](generator-guide.md) | How to build plan generators and note realizers |
| [spec-system.md](spec-system.md) | YAML specification system (simple, detailed, composable formats) |
| [testing-strategy.md](testing-strategy.md) | Test categories, helpers, golden tests, audio regression |
| [roadmap.md](roadmap.md) | Development roadmap with milestones |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Quick setup and contribution guide |

## See Also

- [PROJECT.md](../PROJECT.md) -- Full project design
- [CLAUDE.md](../CLAUDE.md) -- Development rules and conventions
- [IMPROVEMENT.md](../IMPROVEMENT.md) -- Gap analysis and roadmap
- [VISION.md](../VISION.md) -- Target architecture
- [FEATURE_STATUS.md](../FEATURE_STATUS.md) -- Capability matrix (single source of truth)
- [.claude/guides/](../.claude/guides/) -- Focused guides (architecture, coding, music engineering, testing, workflow)

## Current State

- **Version:** 0.1.0
- **Phase:** Phase 5 (tests, guides, documentation) complete. All planned phases delivered. Post-phase additions: cover art generation (Gemini), multi-act composition support.
- **Python:** 3.11+
- **Source modules:** 302 Python modules in `src/yao/` (including 14 SDK modules in `src/yao/sdk/`)
- **Test files:** 332 test files (including SDK test files in `tests/sdk/`)
- **Test categories:** unit (including `unit/coupling/`), integration, scenario, constraint, golden, acoustic regression, properties, genre coverage, subjective, tools, sdk (unit + integration + scenarios)
- **Surfaces:** Claude Code (interactive), CLI (scriptable), Agent SDK (programmatic)
- **Project specs:** 151 example projects in `specs/projects/`

### Generation

- **Pipeline:** Spec -> PlanOrchestrator (9 steps) -> MusicalPlan -> Critic Gate -> NoteRealizer -> Performance -> Renderer
- **Combination & Coupling:** 11 coupling modules (`src/yao/coupling/`) -- voice leading, reharmonization, harmonic-melody coupling, harmonic devices, rhythm Markov, modulation, phrase shape, theme recurrence, polyrhythm, genre vector, listening dialog
- **Registered generators:** 9 (rule_based, stochastic, markov, constraint_satisfaction, twelve_tone, phrase_aware, process_music, loop_evolution, ai_seed)
- **Melodic strategies:** 8 distinct approaches (contour, motif development, linear voice, arpeggiated, scalar runs, call-response, pedal tone, hocketing)
- **Plan generators:** FormPlanner, HarmonyPlanner, Composer, DrumPatterner, Orchestrator, ConversationDirector

### Evaluation and Critique

- **Evaluation:** 11+ metrics across 6 dimensions (structure, melody, harmony, aesthetic, arrangement, acoustics)
- **Critique rules:** 34 structured rules across 15 categories
- **Aesthetic metrics:** 4 (surprise, memorability, contrast, pacing)
- **Acoustic evaluation:** LUFS, spectral features, onset density, 7 use-case evaluators, symbolic-acoustic divergence detection
- **Ensemble constraints:** 5 inter-part rules (register separation, downbeat consonance, no parallel octaves, no frequency collision, bass below melody)

### Music Theory

- **Instruments:** 46 across 9 families (including 8 non-Western: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney)
- **Scales:** 33 including microtonal (14 standard + 19 extended: ragas, maqamat, gamelan, Japanese, just intonation)
- **Song forms:** 20 (AABA, verse-chorus-bridge, rondo, blues, J-Pop, game BGM, ambient, etc.)
- **Drum patterns:** 15 across time signatures (4/4, 3/4, 5/4, 6/8, 7/8)
- **Groove profiles:** 20 (jazz swing, bossa nova, funk, afrobeat, samba, etc.)
- **Chord types:** 30 with functional harmony
- **Harmonic devices:** 15 YAML-defined devices (jazz turnarounds, blues 12-bar, Coltrane changes, etc.)
- **Markov models:** 29 total (14 pitch, 10+ rhythm, contour) with genre-specific models

### Infrastructure

- **Spec formats:** Simple (flat YAML), Detailed (11-section), and Composable (extends/overrides/fragments)
- **Backends:** PythonOnlyBackend (CI default) + AnthropicAPIBackend (real LLM, structured output via tool use)
- **Genre Skills:** 30 genre profiles (46 skill files) integrated into HarmonyPlanner + SpecCompiler + genre_fitness critique
- **Subagents:** 11 agent definitions (Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Adversarial Critic, Producer, Conversation Director, Genre Specialist, Spec Compiler, + protocol)
- **Cover Art:** Gemini-powered album art generation (`yao cover-art`), style-configurable, mood-matched
- **Slash commands:** 11 (compose, conduct, sketch, critique, regenerate-section, render, explain, arrange, pin, feedback, cover-art)
- **Genre skills:** 46 genre skill files in `.claude/skills/genres/`
- **Genre templates:** 34 genre-specific templates in `specs/templates/genres/`
- **StyleVector:** 6 copyright-safe features (histograms + statistics, never sequences)
- **Sketch:** 6-turn interactive dialogue with state persistence (English + Japanese)
- **Arrangement:** Source plan extraction, style vector transfer, preservation contracts, diff reports
- **Feedback:** Three-tier (spec/section/pin) + NL translator (30 phrase-to-intent mappings)
- **Perception:** Audio features (librosa + pyloudnorm), surprise scorer, listening simulator
- **Groove:** GrooveProfile IR + GrooveApplicator (ensemble-wide microtiming)
- **Conversation:** ConversationPlan + reactive fills + frequency clearance
- **Rendering:** MIDI, WAV, MusicXML, LilyPond/PDF, Reaper RPP, Strudel, cover art (PNG via Gemini)
- **Mix:** Per-track EQ, compression, reverb + master chain (pedalboard-based)
- **CI:** GitHub Actions + pre-commit hooks + 5 honesty check tools + weekly audio regression
- **Provenance:** Append-only causal graph with record_id + caused_by edges

### SDK Surface (Phase 2 -- Complete)

- **Modules:** 14 Python modules in `src/yao/sdk/`
- **Lane A:** `YaoAgent` facade with 10 async-generator methods (1:1 with slash commands) + `interrupt()` and `set_permission_mode()`
- **Lane B:** `default_yao_options()` + `create_yao_mcp_server()` for raw SDK access (fully wired: hooks, agents, permissions)
- **MCP tools:** 15 in-process tools (`yao_compose`, `yao_conduct`, `yao_critique`, etc.) with structured error payloads
- **Streaming events:** 9 typed events (`PhaseStartedEvent`, `IterationCompletedEvent`, `AudioReadyEvent`, etc.)
- **Results:** 9 typed result dataclasses (`ComposeResult`, `ConductResult`, `CritiqueResult`, etc.)
- **Hooks:** 4 standard hooks (pre-validate, post-provenance, post-render, post-critique)
- **Permissions:** `default_yao_permission()` callback protecting iterations, references, agent defs
- **Subagent definitions:** `yao_agent_definitions()` with per-role tool allowlists and effort tuning
- **Sessions:** Project-scoped sessions with tagging and forking
- **Parity:** G1--G5 guarantees enforce identical behavior across all three surfaces
- **Reference apps:** 5 examples (minimal, web/FastAPI, Discord bot, CI pipeline, Jupyter notebook)
- **CLI integration:** `yao agent` (SDK-driven one-shot) and `yao serve` (headless HTTP server)
- **Documentation:** 6 pages in `docs/sdk/` (overview, quickstart, API reference, Lane A vs B, deployment, parity)

### Phases 3--5 (Complete)

- **Phase 3:** Synth expansion (24 GM synth instruments), vocal schema (VocalSpec + vocal_lead role), outcome learning (UserStyleProfile)
- **Phase 4:** DAW integration (DAWMCPBridge with Reaper TCP), live improvisation (`yao improvise`), vocal synthesis bridge (VocalSynthBridge ABC), A/B testing framework, cross-project style fingerprinting
- **Phase 5:** Tests, guides, and documentation — comprehensive developer guides, test coverage expansion, documentation site
- **Post-Phase:** Cover art generation via Google Gemini (`yao cover-art`, `src/yao/render/cover_art.py`), multi-act composition structures (three-act with piano cadenza demonstrated in ambient-v4 project)
