# YaO Development Documentation

Technical documentation for contributors and AI agents developing YaO.

## Guides

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | Layer model, dependency rules, data flow |
| [api-reference.md](api-reference.md) | Public API surface, module-by-module reference |
| [generator-guide.md](generator-guide.md) | How to build plan generators and note realizers |
| [spec-system.md](spec-system.md) | YAML specification system (v1 + v2, templates, validation) |
| [testing-strategy.md](testing-strategy.md) | Test categories, helpers, golden tests |
| [roadmap.md](roadmap.md) | Development roadmap with milestones |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Quick setup and contribution guide |

## See Also

- [PROJECT.md](../PROJECT.md) — Full project design (v2.0)
- [CLAUDE.md](../CLAUDE.md) — Development rules and 7 principles
- [VISION.md](../VISION.md) — Target architecture
- [FEATURE_STATUS.md](../FEATURE_STATUS.md) — Capability matrix (single source of truth)
- [.claude/guides/](../.claude/guides/) — Focused guides (architecture, coding, music engineering, testing, workflow)

## Current State

- **Phase:** v2.0 — Phase γ complete + Phase δ complete
- **Tests:** 1,748 passing (unit, integration, scenario, constraint, golden, subjective, acoustic regression)
- **Source files:** 198 Python modules in `src/yao/`
- **Test files:** 207 test files
- **Note Realizers:** 4 registered — 2 V2 (rule_based_v2, stochastic_v2 with 100% plan consumption) + 2 legacy deprecated
- **Critique rules:** 35 structured rules across 8+ categories (structural, melodic, harmonic, rhythmic, arrangement, emotional, genre fitness, memorability, surprise, hook, groove, acoustic, conversation)
- **Aesthetic metrics:** 4 (surprise, memorability, contrast, pacing) in a dedicated dimension
- **Acoustic evaluation:** LUFS, spectral features, onset density, 7 use-case evaluators, symbolic-acoustic divergence detection
- **Ensemble constraints:** 5 inter-part rules (register separation, downbeat consonance, etc.)
- **Spec formats:** v1 (flat YAML) + v2 (11-section with emotion, melody, harmony, drums, hooks, groove, conversation)
- **Pipeline:** Spec → PlanOrchestrator (9 steps) → MusicalPlan → NoteRealizer V2 → Performance → MIDI/WAV/Score
- **Evaluation:** 10+ metrics across 6 dimensions (structure, melody, harmony, aesthetic, arrangement, acoustics)
- **Backends:** PythonOnlyBackend (CI default) + AnthropicAPIBackend (real LLM, is_stub=False)
- **Genre Skills:** 22 files across 5 categories, integrated into HarmonyPlanner + SpecCompiler + genre_fitness critique
- **StyleVector:** 6 copyright-safe features (histograms + statistics, never sequences)
- **Sketch:** 6-turn interactive dialogue with state persistence and resume (English + Japanese)
- **Arrangement:** Source plan extraction, style vector transfer, preservation contracts, diff reports
- **Feedback:** Three-tier (spec/section/pin) + NL translator (30 phrase→intent mappings)
- **Forms:** 20 song forms (AABA, verse-chorus-bridge, rondo, blues, J-Pop, game BGM, ambient, etc.)
- **Melodic strategies:** 8 distinct approaches (contour, motif development, linear voice, arpeggiated, scalar runs, call-response, pedal tone, hocketing)
- **Perception:** Audio features (librosa + pyloudnorm), surprise scorer, listening simulator
- **Groove:** GrooveProfile IR + GrooveApplicator (ensemble-wide microtiming)
- **Conversation:** ConversationPlan + reactive fills + frequency clearance
- **CI:** GitHub Actions + pre-commit hooks + 5 honesty check tools + weekly audio regression
