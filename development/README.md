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

- [PROJECT.md](../PROJECT.md) — Current architecture and Capability Matrix
- [CLAUDE.md](../CLAUDE.md) — Development rules
- [VISION.md](../VISION.md) — Target architecture and future plans
- [.claude/guides/](../.claude/guides/) — Focused guides (architecture, coding conventions, music engineering, testing, workflow, matrix discipline)

## Current State

- **Phase:** Alpha (CPIR foundation)
- **Tests:** ~492 (unit 448, integration 15, scenario 16, constraint 7, golden 6)
- **Source files:** 79 Python modules in src/yao/
- **Generators:** 2 legacy (rule_based, stochastic) wrapped as NoteRealizers + 2 plan generators (form, harmony)
- **Spec formats:** v1 (flat YAML) + v2 (11-section with emotion, melody, harmony, drums, etc.)
- **Pipeline:** Spec → PlanOrchestrator → MusicalPlan → NoteRealizer → ScoreIR → MIDI
- **Evaluation:** 10 metrics across 3 dimensions, MetricGoal type system, quality score 1.0-10.0
