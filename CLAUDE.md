# CLAUDE.md — YaO Core Rules (v2.0 — Genre Diversity)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > IMPROVEMENT.md > other docs.*

---

## Quick Reference

```
make test                # Run all tests
make test-genre          # Genre-specific scenario tests (NEW)
make test-conformance    # Genre Conformance evaluator tests (NEW)
make lint                # ruff + mypy
make arch-lint           # Layer boundary check (incl. new layers)
make all-checks          # lint + arch-lint + test
make format              # Auto-format code
make new-genre NAME=foo  # Scaffold a new GenreProfile (NEW)
make audit-genres        # Validate every GenreProfile (NEW)
```

**Key directories:**

```
src/yao/constants/   → Hardcoded values (ranges, scales, MIDI maps, drum kits)
src/yao/genre/       → GenreProfile system (Layer 0/1)        (NEW v2.0)
src/yao/schema/      → Pydantic models for YAML specs
src/yao/ir/          → Core data types (Note, ScoreIR, harmony, motif,
                       voicing, groove, drum_pattern, phrasing)
src/yao/generators/  → Generators (rule_based, stochastic, drums,
                       walking_bass, markov, constraint_solver, ai_bridge)
src/yao/perception/  → Style vector, reference matcher          (NEW v2.0)
src/yao/render/      → Output (MIDI, audio, stems)
src/yao/production/  → Per-genre mix/master profiles            (NEW v2.0)
src/yao/verify/      → Lint, evaluation, diff, genre conformance
src/yao/reflect/     → Provenance, style profile
src/yao/conductor/   → Orchestration loop, NL parser
src/yao/errors.py    → All custom exceptions
```

**Key types:**

```
Note               → src/yao/ir/note.py
ScoreIR            → src/yao/ir/score_ir.py
CompositionSpec    → src/yao/schema/composition.py
ProvenanceLog      → src/yao/reflect/provenance.py
GeneratorBase      → src/yao/generators/base.py
GenreProfile       → src/yao/genre/profile.py        (NEW v2.0)
GenreBriefing      → src/yao/genre/briefing.py       (NEW v2.0)
DrumPattern        → src/yao/ir/drum_pattern.py      (NEW v2.0)
GrooveTemplate     → src/yao/ir/groove.py            (NEW v2.0)
ChordProgression   → src/yao/ir/progressions.py      (NEW v2.0)
StyleVector        → src/yao/perception/style_vector.py  (NEW v2.0)
ProductionProfile  → src/yao/production/profile.py   (NEW v2.0)
GenreConformance   → src/yao/verify/genre_conformance.py (NEW v2.0)
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that the Orchestra subagents will use at runtime. Your code enables reproducible, auditable, iterable, **multi-genre** music creation.

In v2.0, your most important responsibility is to make **genre a first-class concept** that flows through every layer. When a user writes `genre: jazz`, that string must produce traceable, idiomatic jazz output — not generic music with a jazz label attached.

---

## 5 Non-Negotiable Rules (preserved from v1.0)

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`. Note Layer 0 and Layer 4 are now populated with substantial code.
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`** — and in v2.0, the provenance must include `genre_briefing_id` if a genre was active.
3. **No silent fallbacks** — constraint violations and genre-conformance failures must be explicit.
4. **No hardcoded musical values** — use `src/yao/constants/` and `src/yao/genre/`.
5. **No public function without type hints and docstring**.

---

## 5 Additional Genre-System Rules (NEW in v2.0)

6. **Genre is data, not a string.** Anywhere code looks at `spec.genre`, it must resolve through `GenreRegistry.get(name)` and consume a typed `GenreProfile`. Direct string comparison (`if genre == "jazz":`) is forbidden in generation logic.

7. **Genre profiles are inheritable.** A new subgenre (e.g., `bebop`) must declare a `parent` and use additive overrides where possible. Duplicating fields wholesale is a code-review reject.

8. **Drum patterns live as MIDI in `references/drum_patterns/`.** Never inline drum patterns as Python literals. Authoring patterns in a DAW and exporting MIDI is the canonical workflow.

9. **Grooves are whole-piece, not per-track.** Once a `GrooveTemplate` is selected for a composition, every track's note positions must pass through it. Per-track ad-hoc humanization is an anti-pattern.

10. **Genre Conformance failures are first-class adaptation signals.** When `GenreConformance.overall_score < threshold`, the Conductor must adapt before regenerating. Treating the score as advisory is forbidden.

---

## MUSTs

* Read existing code before writing new code
* Write tests before or alongside implementation
* Keep YAML schemas and Pydantic models in sync
* Use `yao.ir.timing` for all tick/beat/second conversions
* Use `yao.ir.notation` for all note name/MIDI conversions
* Derive velocity from dynamics curves AND `GrooveTemplate.accent_pattern`
* Register generators via `@register_generator("name")`
* Register genres via `GenreRegistry.register(profile)` in module init
* Reference drum patterns by ID; never embed pattern literals
* Apply `GrooveTemplate.apply()` before final MIDI write when a groove is active
* Record `GenreBriefing.id` in provenance for every genre-aware generation
* Validate new `GenreProfile` YAMLs against the Pydantic schema in CI

## MUST NOTs

* Import `pretty_midi` / `music21` / `librosa` outside designated layers
* Import `pedalboard` outside `src/yao/production/`
* Create functions with vague names (`make_it_sound_good`)
* Skip provenance recording for any generation step
* Use bare `ValueError` (use `YaOError` subclasses)
* Silently clamp notes to range (raise `RangeViolationError`)
* Leave `TODO`/`FIXME` uncommitted
* Compare genres by string (use the registry)
* Inline drum patterns as Python lists of `(tick, velocity)` tuples
* Hardcode swing ratios in generators (use `GenreProfile.swing_8th`)
* Add a new genre without populating the corresponding `.claude/skills/genres/<name>.md`
* Add a generator that ignores `GenreBriefing` when one is provided
* Reproduce copyrighted MIDI in `references/midi/` without `catalog.yaml` rights status
* Name a Skill or profile after a currently active artist

---

## 5 Design Principles (preserved verbatim)

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide

These principles are unchanged in v2.0. The Genre System extends them; it does not replace them.

---

## Current Phase

**Phase A — Genre System Foundation** (then B, C, ... G in order)

**What EXISTS (carried from v1.0):**

* Spec loading + validation (YAML → Pydantic) ✅
* ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
* Rule-based generator (deterministic) ✅
* Stochastic generator (seed + temperature) ✅
* Generator registry (strategy selection via spec) ✅
* Constraint system (must / must_not / prefer / avoid with scoped rules) ✅
* MIDI rendering + stems ✅
* MIDI reader (load existing MIDI back to ScoreIR) ✅
* Music linting, analysis, evaluation ✅
* Evaluation report persistence (evaluation.json) ✅
* Score diff with modified-note tracking ✅
* Provenance logging (append-only, queryable) ✅
* Conductor feedback loop (generate → evaluate → adapt → regenerate) ✅
* Section-level regeneration ✅
* CLI (compose, conduct, render, validate, evaluate, diff, explain, ...) ✅
* Architecture lint tool ✅
* 7 Claude Code commands and 7 subagent definitions ✅

**What is being BUILT now (Phase A targets):**

* `src/yao/genre/profile.py` — `GenreProfile` Pydantic model
* `src/yao/genre/registry.py` — registry with inheritance support
* `src/yao/genre/profiles/*.yaml` — initial 15–20 profiles
* `src/yao/genre/briefing.py` — `GenreBriefing` resolution
* `src/yao/conductor/nl_parser.py` upgrades — extract genre from natural language
* `src/yao/verify/genre_conformance.py` — Genre Conformance evaluator (4–5 sub-metrics)
* `.claude/agents/genre-specialist.md` — new subagent definition
* `tests/genre/` — genre-specific scenario tests

**Phase A acceptance gate:**

`yao conduct "modal jazz piano trio in dorian"` produces output where:
- The active `GenreProfile` is `modal_jazz`
- Generated mode is Dorian
- Tempo is in `typical_tempo_range`
- Generated output uses `chord_palette_extended` (extensions appear)
- Genre Conformance score ≥ 0.7

**Coming after Phase A (do not start until A is gate-passed):**

* Phase B: Drums and Grooves (Drum Generator, GrooveTemplate, 35–40 patterns)
* Phase C: Extended Harmony (15+ chord types, Progression Library, Reharmonization Subagent)
* Phase D: Instrument Palette Expansion (20–30 modern instruments, 808/909, Rhodes)
* Phase E: Form Templates (12-bar blues, AABA, EDM buildup-drop)
* Phase F: Layer 4 — Style Reference (Reference Library, Style Vector, Reference Matcher)
* Phase G: Production and Phrasing (pedalboard, Production Profiles, Phrasing Engine, Markov, Constraint Solver, AI Bridge)

---

## Component Addition Procedures

### Adding a new GenreProfile

1. Author `src/yao/genre/profiles/<name>.yaml`. Set `parent` if extending an existing genre.
2. Run `make audit-genres` — schema must validate.
3. Add `.claude/skills/genres/<name>.md` with chord progressions, rhythm patterns, instrumentation, references, and clichés to avoid.
4. Add at least one example project under `specs/projects/<name>-example/`.
5. Add a scenario test under `tests/genre/test_<name>_conformance.py`.
6. Update `PROJECT.md` Section 4.3 if the genre extends the catalog beyond the documented 20.

### Adding a new DrumPattern

1. Author the pattern in a DAW. Export as MIDI Type 1.
2. Save as `references/drum_patterns/<genre>/<pattern_id>.mid`.
3. Add metadata entry in `references/drum_patterns/catalog.yaml` (genre tags, time signature, swing, fill compatibility).
4. Add a unit test that loads the pattern and asserts shape (bars, voice presence).
5. Reference the new pattern from at least one `GenreProfile.drum_pattern_ids`.

### Adding a new GrooveTemplate

1. Author `references/grooves/<id>.yaml` with `micro_timing`, `swing_8th`, `swing_16th`, `pocket`, `accent_pattern`.
2. Add a Pydantic test that loads and validates the YAML.
3. Reference the new groove from at least one `GenreProfile.typical_grooves`.
4. Add an integration test verifying that applying the groove changes note positions as expected.

### Adding a new ChordProgression

1. Add an entry to `src/yao/ir/progressions.py` (or load from YAML if author wants).
2. Specify Roman-numeral chords, bars-per-chord, genre tags, cadence type.
3. Add a unit test verifying realization to concrete pitches in multiple keys.
4. Reference the progression ID from at least one `GenreProfile.progression_library_ids`.

### Adding a new Subagent

1. Create `.claude/agents/<name>.md`. Specify role, inputs, outputs, prohibitions, acceptance criteria.
2. Confirm role does not duplicate existing subagents.
3. Define interaction protocol with the Producer subagent.
4. Add an integration test under `tests/integration/test_<name>_subagent.py` that exercises the new subagent's contract.

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not by memorization. Run the listed command before requesting review.

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | Lint rule (no literal in `velocity=`) | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| Genre string comparison | Lint rule against `==` on `genre` field (NEW) | `make lint` |
| Drum pattern as Python literal | Lint rule against inline NoteEvent lists in drums.py (NEW) | `make lint` |
| Hardcoded swing in generators | Lint rule against numeric literals near "swing" (NEW) | `make lint` |
| Missing GenreBriefing in provenance | Provenance test asserts presence (NEW) | `make test` |
| Genre Conformance below threshold | Scenario test asserts pass (NEW) | `make test-conformance` |
| GenreProfile schema drift | `make audit-genres` (NEW) | `make audit-genres` |
| Pedalboard imported in wrong layer | architecture-lint extension (NEW) | `make arch-lint` |

---

## Performance Expectations

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Resolve GenreProfile | <50ms | Includes inheritance chain (NEW) |
| Build GenreBriefing | <100ms | Synchronous, deterministic (NEW) |
| Generate 8-bar piece | <1s | Symbolic generators |
| Generate 64-bar piece | <5s | Stochastic may vary |
| Generate drums for 64 bars | <500ms | Pattern-based (NEW) |
| Apply groove to full piece | <200ms | Tick-level offset (NEW) |
| Compute Genre Conformance | <300ms | All sub-metrics (NEW) |
| Compute style-vector | <500ms | Per ScoreIR (Phase F) |
| Reference matcher (cached) | <50ms | Vector cosine (Phase F) |
| Pedalboard render 60s audio | <3s | Best-effort (Phase G) |
| Write MIDI file | <200ms | pretty_midi |
| Run full lint | <500ms | All lint rules |
| Run all tests | <8s | Test count grows in v2.0 |
| Architecture lint | <1s | AST parsing |

Do not introduce changes that exceed these budgets without discussion.

---

## When You Must Be Especially Careful

These areas have caused subtle bugs in similar systems. Move slowly and add extra tests when working in them.

* **Genre inheritance resolution.** Subtle bugs occur when child profile fields shadow parent fields incorrectly. Always test with a 3-level chain (e.g., `bebop` ← `jazz` ← `<root>`).
* **Groove application order.** Apply groove **after** all generators emit, **before** humanization. Reversing this corrupts the felt rhythm.
* **Drum kit selection.** GM Drum Map only goes so far; non-GM drum kits (808/909/lo-fi) require explicit MIDI program/channel handling in `render/midi_writer.py`.
* **Style vector dimensionality.** Adding a dimension breaks reference cache compatibility. Bump the cache version when this happens.
* **NL parser fall-through.** When the LLM-powered parser fails or times out, fall back to keyword extraction explicitly — do not silently produce a default genre.
* **Per-instrument generator selection.** When the spec uses `generation.per_instrument`, all listed generators must produce compatible IRs in the same key/tempo. Mismatches must be detected at spec-load time, not at render time.
* **Reference Library license tracking.** Every reference MIDI must have a `catalog.yaml` entry. CI must fail if a MIDI exists without an entry.

---

## Recent Changes

* **v2.0 / 2026-05-08**: Genre System foundation work begins. PROJECT.md and CLAUDE.md updated to integrate IMPROVEMENT.md proposals. Phases A–G defined.
* **2026-04-29**: MIDI reader, section regeneration (Conductor + CLI), evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades, 4 skills populated, mypy fixes (140→0 errors).
* **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff.
* **2026-04-28**: Stochastic generator, generator registry, queryable provenance, CLAUDE.md restructured.
* **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI.
* **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md.

---

## Escalation

Stop and ask the human when:

* Changing architectural boundaries or layer rules (especially Layer 0/4 expansion in v2.0)
* Adding new external dependencies (e.g., `pedalboard`, `or-tools`, `z3-solver`)
* Adding a new genre that does not fit the existing catalog families
* Adding a Reference MIDI when license status is uncertain
* Naming any artifact (skill, profile, pattern) in a way that could imply a specific living artist
* Making music-theory judgment calls you're unsure about (e.g., "is this voicing acceptable for jazz?")
* Deleting files or rewriting git history
* Any change touching 5+ files
* Considering changes to the Conductor feedback-loop logic itself
* Considering changes to provenance schema (it must remain append-compatible)

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| `architecture.md` | Working across layers, adding modules |
| `coding-conventions.md` | Writing any code |
| `music-engineering.md` | Generating/modifying notes |
| `testing.md` | Writing or running tests |
| `workflow.md` | Planning a change |
| `genre-development.md` (NEW) | Adding a new genre or modifying a profile |
| `drum-pattern-authoring.md` (NEW) | Authoring or extending the drum pattern library |
| `groove-engineering.md` (NEW) | Designing a new groove template |
| `production-profile.md` (NEW) | Defining or extending production effects |
| `reference-library.md` (NEW) | Adding rights-cleared MIDIs to the reference set |

Full design documentation: `PROJECT.md`
Detailed v2.0 analysis: `IMPROVEMENT.md`

---

**Document version:** 2.0
**Last updated:** 2026-05-08
