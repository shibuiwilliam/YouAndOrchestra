# CLAUDE.md — YaO Core Rules

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > other docs.*

---

## Quick Reference

```
make test           # Run all tests
make lint           # ruff + mypy
make arch-lint      # Layer boundary check
make all-checks     # lint + arch-lint + test
make format         # Auto-format code
```

**Key directories:**
```
src/yao/constants/   → Hardcoded values (ranges, scales, MIDI mappings)
src/yao/schema/      → Pydantic models for YAML specs
src/yao/ir/          → Core data types (Note, ScoreIR, harmony, motif, voicing)
src/yao/generators/  → Composition algorithms (rule_based, stochastic)
src/yao/render/      → Output (MIDI, audio, stems)
src/yao/verify/      → Analysis, linting, evaluation, diff
src/yao/reflect/     → Provenance tracking
src/yao/errors.py    → All custom exceptions
```

**Key types:**
```
Note              → src/yao/ir/note.py
ScoreIR           → src/yao/ir/score_ir.py
CompositionSpec   → src/yao/schema/composition.py
ProvenanceLog     → src/yao/reflect/provenance.py
GeneratorBase     → src/yao/generators/base.py
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that Subagents will use. Your code enables reproducible, auditable, iterable music creation.

---

## 5 Non-Negotiable Rules

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`**
3. **No silent fallbacks** — constraint violations must be explicit errors
4. **No hardcoded musical values** — use `src/yao/constants/`
5. **No public function without type hints and docstring**

---

## MUSTs

- Read existing code before writing new code
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Derive velocity from dynamics curves (never hardcode)
- Register generators via `@register_generator("name")`

## MUST NOTs

- Import `pretty_midi`/`music21`/`librosa` outside designated layers
- Create functions with vague names (`make_it_sound_good`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError`)
- Leave `TODO`/`FIXME` uncommitted

---

## 5 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide

---

## Current Phase

**Phase 1** — Parameter-driven symbolic composition

**What EXISTS:**
- Spec loading + validation (YAML → Pydantic) ✅
- ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
- Rule-based generator (deterministic) ✅
- Stochastic generator (seed + temperature) ✅
- Generator registry (strategy selection via spec) ✅
- Constraint system (must/must_not/prefer/avoid with scoped rules) ✅
- MIDI rendering + stems ✅
- MIDI reader (load existing MIDI back to ScoreIR for analysis) ✅
- Music linting, analysis, evaluation ✅
- Evaluation report persistence (evaluation.json) ✅
- Score diff with modified note tracking ✅
- Provenance logging (append-only, queryable) ✅
- Conductor feedback loop (generate → evaluate → adapt → regenerate) ✅
- Section-level regeneration (regenerate one section, preserve others) ✅
- CLI (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section) ✅
- Architecture lint tool ✅
- 7 Claude Code commands (.claude/commands/) with full workflow integration ✅
- 7 Subagent definitions (.claude/agents/) ✅
- 4 Skills populated (cinematic genre, voice-leading, piano, tension-resolution) ✅

**What does NOT exist yet:**
- Advanced generators (Markov, constraint solver)
- Perception layer (reference matching, psychology)
- Arrangement engine
- DAW integration (MCP)
- Live improvisation mode

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization:

| Pattern | What catches it | Command |
|---------|----------------|---------|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | Code review pattern (no literal in velocity=) | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |

---

## Performance Expectations

| Operation | Target | Notes |
|-----------|--------|-------|
| Load YAML spec | <100ms | Pydantic validation |
| Generate 8-bar piece | <1s | Both generators |
| Generate 64-bar piece | <5s | Stochastic may vary |
| Write MIDI file | <200ms | pretty_midi |
| Run full lint | <500ms | All lint rules |
| Run all tests | <5s | ~190 tests |
| Architecture lint | <1s | AST parsing |

Do not introduce changes that exceed these budgets without discussion.

---

## Recent Changes

- **2026-04-29**: MIDI reader, section regeneration (Conductor + CLI), evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades (compose/critique/sketch/regenerate-section), 4 skills populated (cinematic, voice-leading, piano, tension-resolution), mypy fixes (140→0 errors)
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff, documentation completions
- **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance, CLAUDE.md restructured into tiered guides
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Claude Code commands/agents
- **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md

---

## Escalation

Stop and ask the human when:
- Changing architectural boundaries or layer rules
- Adding new external dependencies
- Making music theory judgment calls you're unsure about
- Deleting files or rewriting git history
- Any change touching 5+ files

---

## Guides (read when relevant)

| Guide | When to read |
|-------|-------------|
| [Architecture](.claude/guides/architecture.md) | Working across layers, adding modules |
| [Coding Conventions](.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](.claude/guides/music-engineering.md) | Generating/modifying notes |
| [Testing](.claude/guides/testing.md) | Writing or running tests |
| [Workflow](.claude/guides/workflow.md) | Planning a change |

Full design documentation: [PROJECT.md](./PROJECT.md)
