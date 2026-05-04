# YaO Development Documentation

Technical documentation for contributors and AI agents developing YaO.

## Guides

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | Layer model, dependency rules, V2 pipeline, key types |
| [api-reference.md](api-reference.md) | Public API surface, module-by-module reference |
| [generator-guide.md](generator-guide.md) | How to build plan generators and note realizers |
| [spec-system.md](spec-system.md) | YAML specification system (v1 + v2 + v3 composability) |
| [testing-strategy.md](testing-strategy.md) | Test categories, helpers, golden tests, audio regression |
| [roadmap.md](roadmap.md) | Development roadmap with milestones |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Quick setup and contribution guide |

## See Also

- [PROJECT.md](../PROJECT.md) -- Full project design (v2.0)
- [CLAUDE.md](../CLAUDE.md) -- Development rules and conventions
- [VISION.md](../VISION.md) -- Target architecture
- [FEATURE_STATUS.md](../FEATURE_STATUS.md) -- Capability matrix (single source of truth)
- [.claude/guides/](../.claude/guides/) -- Focused guides (architecture, coding, music engineering, testing, workflow)

## Current State

- **Version:** 0.1.0
- **Phase:** v2.0 -- Phase gamma complete + Phase delta complete
- **Python:** 3.11+
- **Source files:** 222 Python modules in `src/yao/`
- **Test files:** 195 test files, ~2,157 tests passing
- **Test categories:** unit, integration, scenario, constraint, golden, acoustic regression, properties, genre coverage, subjective

### Generation

- **V2 Pipeline:** Spec -> PlanOrchestrator (9 steps) -> MusicalPlan -> Critic Gate -> NoteRealizer V2 -> Performance -> Renderer
- **Note Realizers:** 4 registered -- 2 V2 (rule_based_v2, stochastic_v2 with 100% plan consumption) + 2 legacy (deprecated)
- **Additional generators:** markov, twelve_tone, process_music, constraint_solver
- **Melodic strategies:** 8 distinct approaches (contour, motif development, linear voice, arpeggiated, scalar runs, call-response, pedal tone, hocketing)
- **Plan generators:** FormPlanner, HarmonyPlanner, Composer, DrumPatterner, Orchestrator, ConversationDirector

### Evaluation and Critique

- **Evaluation:** 11+ metrics across 6 dimensions (structure, melody, harmony, aesthetic, arrangement, acoustics)
- **Critique rules:** 35 structured rules across 12+ categories
- **Aesthetic metrics:** 4 (surprise, memorability, contrast, pacing)
- **Acoustic evaluation:** LUFS, spectral features, onset density, 7 use-case evaluators, symbolic-acoustic divergence detection
- **Ensemble constraints:** 5 inter-part rules (register separation, downbeat consonance, no parallel octaves, no frequency collision, bass below melody)

### Music Theory

- **Instruments:** 46 across 9 families (including 8 non-Western: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney)
- **Scales:** 28+ including microtonal (ragas, maqamat, gamelan, just intonation)
- **Song forms:** 20 (AABA, verse-chorus-bridge, rondo, blues, J-Pop, game BGM, ambient, etc.)
- **Drum patterns:** 15 across time signatures (4/4, 3/4, 5/4, 6/8, 7/8)
- **Groove profiles:** 20 (jazz swing, bossa nova, funk, afrobeat, samba, etc.)
- **Chord types:** 14 with functional harmony

### Infrastructure

- **Spec formats:** v1 (flat YAML) + v2 (11-section) + v3 (composability with extends/overrides/fragments)
- **Backends:** PythonOnlyBackend (CI default) + AnthropicAPIBackend (real LLM, structured output via tool use)
- **Genre Skills:** 22 genres integrated into HarmonyPlanner + SpecCompiler + genre_fitness critique
- **Subagents:** 7 roles (Composer, Harmony Theorist, Rhythm Architect, Orchestrator, Mix Engineer, Adversarial Critic, Producer)
- **Slash commands:** 10 (compose, conduct, sketch, critique, regenerate-section, render, explain, arrange, pin, feedback)
- **StyleVector:** 6 copyright-safe features (histograms + statistics, never sequences)
- **Sketch:** 6-turn interactive dialogue with state persistence (English + Japanese)
- **Arrangement:** Source plan extraction, style vector transfer, preservation contracts, diff reports
- **Feedback:** Three-tier (spec/section/pin) + NL translator (30 phrase-to-intent mappings)
- **Perception:** Audio features (librosa + pyloudnorm), surprise scorer, listening simulator
- **Groove:** GrooveProfile IR + GrooveApplicator (ensemble-wide microtiming)
- **Conversation:** ConversationPlan + reactive fills + frequency clearance
- **Rendering:** MIDI, WAV, MusicXML, LilyPond/PDF, Reaper RPP, Strudel
- **CI:** GitHub Actions + pre-commit hooks + 5 honesty check tools + weekly audio regression
- **Provenance:** Append-only causal graph with record_id + caused_by edges
