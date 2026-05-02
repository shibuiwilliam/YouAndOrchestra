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

- [PROJECT.md](../PROJECT.md) — Full project design (v3.0)
- [CLAUDE.md](../CLAUDE.md) — Development rules and 7 principles
- [VISION.md](../VISION.md) — Target architecture
- [FEATURE_STATUS.md](../FEATURE_STATUS.md) — Capability matrix (single source of truth)
- [.claude/guides/](../.claude/guides/) — Focused guides (architecture, coding, music engineering, testing, workflow)

## Current State

- **Phase:** v3.0 — Wave 3 (Depth)
- **Tests:** ~1,150 passing (unit, integration, scenario, constraint, golden, subjective, aesthetic)
- **Source files:** 167 Python modules in `src/yao/`
- **Note Realizers:** 4 registered — 2 V2 (rule_based_v2, stochastic_v2 with 100% plan consumption) + 2 legacy deprecated
- **Critique rules:** 20 structured rules across 8 categories + ensemble constraint rules
- **Aesthetic metrics:** 4 (surprise, memorability, contrast, pacing) in a dedicated dimension
- **Ensemble constraints:** 5 inter-part rules (register separation, downbeat consonance, etc.)
- **Spec formats:** v1 (flat YAML) + v2 (11-section with emotion, melody, harmony, drums)
- **Pipeline:** Spec → PlanOrchestrator → MusicalPlan → NoteRealizer V2 → ScoreIR → Performance → MIDI
- **Evaluation:** 10+ metrics across 6 dimensions (structure, melody, harmony, aesthetic, arrangement, acoustics)
- **Backends:** PythonOnlyBackend (CI default) + AnthropicAPIBackend (real LLM, is_stub=False)
- **Genre Skills:** 22 files across 5 categories, 8 grounded in pipeline
- **StyleVector:** 10 copyright-safe features (histograms + statistics, never sequences)
- **Sketch:** 6-turn interactive dialogue with state persistence and resume
- **CI:** GitHub Actions + pre-commit hooks + 5 honesty check tools
