# YaO Development Documentation

Technical documentation for contributors and AI agents developing YaO.

## Guides

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | System architecture, layer model (including Layer 3.5 MPIR), dependency rules, data flow |
| [api-reference.md](api-reference.md) | Public API surface with module-by-module reference (v1 + v2.0 types) |
| [generator-guide.md](generator-guide.md) | How to build plan generators and note realizers (v2.0 two-stage architecture) |
| [roadmap.md](roadmap.md) | Value-driven development roadmap with milestones and phase plan |
| [testing-strategy.md](testing-strategy.md) | Test categories (447 tests), helpers, golden tests, v2.0 testing |
| [spec-system.md](spec-system.md) | YAML specification system design (v1 + v2 formats, templates, validation) |

## See Also

- [PROJECT.md](../PROJECT.md) — Project vision, design philosophy, and Capability Matrix
- [CLAUDE.md](../CLAUDE.md) — Core development rules (v2.0)
- [.claude/guides/](../.claude/guides/) — Focused development guides (architecture, coding conventions, music engineering, plan engineering, testing, workflow, matrix discipline, critique rules)
- [docs/](../docs/) — User-facing documentation

## Current State

- **Phase:** Alpha (MPIR foundation)
- **Tests:** 447 (unit, integration, scenario, constraint, golden)
- **Generators:** 2 legacy (rule_based, stochastic) + 2 plan generators (form, harmony)
- **Spec formats:** v1 (flat) + v2 (11-section)
- **Architecture:** 8-layer model with Layer 3.5 (Musical Plan IR)
