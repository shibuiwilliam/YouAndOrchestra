# CLAUDE.md — YaO Core Rules

> *Read this file at session start. Detailed guides live in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > other docs.*
> *`FEATURE_STATUS.md` overrides all on "what currently exists."*

---

## Quick Reference

```bash
make test           # Run all tests (~643)
make test-unit      # Unit tests only
make test-golden    # Golden MIDI regression
make lint           # ruff + mypy strict
make arch-lint      # Layer boundary check (AST-based)
make feature-status # Verify FEATURE_STATUS.md matches code
make all-checks     # lint + arch-lint + feature-status + test + golden
make format         # Auto-format code
```

**Key directories:**

```
src/yao/constants/   → Hardcoded values (ranges, scales, MIDI mappings)
src/yao/schema/      → Pydantic models for YAML specs (v1 + v2)
src/yao/ir/          → Core data types (Note, ScoreIR, plan/, motif, voicing,
                       harmony, timing, notation, drum)
src/yao/generators/  → Composition algorithms (rule_based, stochastic,
                       drum_patterner, counter_melody, plan/, note/)
src/yao/perception/  → Perception Substitute Layer (planned per IMPROVEMENT.md)
src/yao/render/      → Output (MIDI writer, stems, audio, iterations,
                       mix chain — planned)
src/yao/verify/      → Analyzer, evaluator, diff, lint, constraints,
                       critique/ (15 rules)
src/yao/reflect/     → Provenance, RecoverableDecision, style_profile
src/yao/conductor/   → Generate-evaluate-adapt loop, feedback adaptation
src/yao/sketch/      → Natural language → spec compiler
src/yao/arrange/     → Arrangement engine (stub, IMPROVEMENT.md proposal 5)
src/yao/errors.py    → All custom exceptions
src/yao/types.py     → Domain type aliases
src/cli/             → Click CLI entry points (11 commands)
```

**Key types:**

```
Note                  → src/yao/ir/note.py
ScoreIR               → src/yao/ir/score_ir.py
Section / Part        → src/yao/ir/score_ir.py
Motif                 → src/yao/ir/motif.py
Voicing               → src/yao/ir/voicing.py
DrumPattern           → src/yao/ir/drum.py
SongFormPlan          → src/yao/ir/plan/form.py
HarmonyPlan           → src/yao/ir/plan/harmony.py
MultiDimensionalTrajectory → src/yao/ir/trajectory.py
CompositionSpec       → src/yao/schema/composition.py
ProductionSpec        → src/yao/schema/production.py
ProvenanceLog         → src/yao/reflect/provenance.py
RecoverableDecision   → src/yao/reflect/recoverable.py
GeneratorBase         → src/yao/generators/base.py
Finding (critique)    → src/yao/verify/critique/types.py
MetricGoal            → src/yao/verify/metric_goal.py
ConductorResult       → src/yao/conductor/result.py
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself.

This distinction is essential.

- **YaO** is "an agentic music production environment."
- **The Subagents** (Composer, Critic, Producer, …) are roles at runtime.
- **You** build the infrastructure that the Subagents use.

In other words, you write code that *future Composer Subagents will call*. You do not compose. You build the substrate that makes composition reproducible, auditable, and iterable.

That said, your code must function musically. You need a working understanding of music theory, instrument characteristics, and audio processing. When unsure, consult `.claude/guides/music-engineering.md`, `.claude/skills/`, or escalate to the human.

---

## 6 Non-Negotiable Rules

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`. Enforced by `make arch-lint`.
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`** — and provenance is appended, never modified after the fact.
3. **No silent fallbacks** — constraint violations must raise explicit errors. When a fallback is intentional, log it via `RecoverableDecision`.
4. **No hardcoded musical values** — use `src/yao/constants/`. No literal `velocity=100`, no literal MIDI numbers, no literal instrument ranges in business logic.
5. **No public function without type hints and a docstring** — enforced by mypy strict.
6. **Sync FEATURE_STATUS.md with reality** — if you add or change a capability, update `FEATURE_STATUS.md` in the same PR. `make feature-status` enforces consistency.

---

## MUSTs

- Read existing code before writing new code (`view` first, write second).
- Write tests before or alongside implementation. Bug fixes require a regression test reproducing the bug.
- Keep YAML schemas and Pydantic models in sync within the same PR.
- Use `yao.ir.timing` for all tick / beat / second conversions.
- Use `yao.ir.notation` for all note name ↔ MIDI conversions.
- Derive velocity from dynamics curves — never hardcode (failure pattern F3).
- Register generators via `@register_generator("name")`.
- Register critique rules via the critique registry; emit structured `Finding` objects.
- Use `MetricGoal` types when adding evaluation metrics — do not invent ad-hoc goal logic.
- For any silent-fallback path that already exists, wrap it with `RecoverableDecision.log(...)` so it appears in audit trails. Use `tools/check_silent_fallback.py` to detect new ones.
- When adding a new spec field, also update the spec applicability registry (per IMPROVEMENT.md proposal 4) so users see honestly whether the field is honored.
- Run `make all-checks` before committing.

## MUST NOTs

- Import `pretty_midi` / `music21` / `librosa` outside their designated layers (see `.claude/guides/architecture.md`).
- Create functions with vague names (`make_it_sound_good`, `improve_quality`, `fix_it`).
- Skip provenance recording for any generation step.
- Use bare `ValueError` — always use `YaOError` subclasses (`RangeViolationError`, `ConstraintViolation`, `SpecValidationError`, …).
- Silently clamp notes to instrument range (raise `RangeViolationError` with a fix suggestion in the message — failure pattern F2).
- Leave `TODO` / `FIXME` uncommitted. File a tracking issue first, reference its number in the comment.
- Mock specific living artists in Skills, parameter names, or examples. Use abstract feature descriptions only.
- Add reference works to `references/` without rights-status entries in `references/catalog.yaml`.
- Bypass `make arch-lint` failures. Restructure the code; do not weaken the linter.
- Disable a test with `@pytest.mark.skip` without a reason comment and a tracking issue.
- Modify provenance entries after the fact. Provenance is append-only.

---

## 6 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity; we don't replace it.
2. **Explain everything** — every note has a provenance record.
3. **Constraints liberate** — specs and rules are scaffolds, not cages.
4. **Time-axis first** — design trajectory curves before notes.
5. **Human ear is truth** — automated scores inform; humans decide.
6. **Incrementality** — do not break what works; extend each layer progressively.

These map onto implementation as follows:

- Principle 1 → APIs are designed to be called *by* a subagent; do not embed aesthetic preferences in the API itself.
- Principle 2 → All generation APIs return `ProvenanceLog`. There are no exceptions.
- Principle 3 → Validators fail loudly. Constraint scopes are explicit.
- Principle 4 → `trajectory/` does not depend on `generators/`. The reverse is allowed.
- Principle 5 → Automation loops are interruptible at human-approval gates.
- Principle 6 → Backwards compatibility on CLI and YAML. New fields default to neutral behavior.

---

## Current Phase

**Phase 1** — Parameter-driven symbolic composition (deployed and stable).

**What EXISTS** (✅ unless noted):

- Spec loading + validation: Pydantic v1 (`CompositionSpec`, `SectionSpec`, `InstrumentSpec`) and v2 (22 models, 11 sections)
- ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) — frozen dataclasses
- CPIR planning IR (SongFormPlan, HarmonyPlan)
- Trajectory IR (5-dimensional: tension, density, predictability, brightness, register_height)
- DrumPattern IR (15 GM kit pieces, 8 genre-specific patterns in `drum_patterns/`)
- Rule-based generator (deterministic)
- Stochastic generator (seed + temperature; 4 contour algorithms; 5 voicing types; 12 rhythm templates; walking bass; counter-melody via species counterpoint; motif transformations; 3-axis trajectory coupling)
- Drum patterner (swing, ghost notes, trajectory density)
- Counter-melody generator (consonance + contrary motion + parallel-fifths avoidance)
- Generator registry (`@register_generator`)
- Constraint system (must / must_not / prefer / avoid; scopes: global / section / instrument / bars)
- MIDI rendering + per-instrument stems
- MIDI reader (round-trip MIDI → ScoreIR for analysis)
- Audio renderer (FluidSynth; optional)
- Music linting, score analyzer, evaluator (10+ metrics in 6 dimensions)
- MetricGoal type system (7 types)
- Score diff with modified-note tracking
- 35 critique rules across 12 categories with structured Findings
- RecoverableDecision logging (9 registered codes; silent-fallback detector)
- Provenance logging (append-only, queryable, JSON-persisted)
- Conductor feedback loop (generate → evaluate → critique → adapt → regenerate)
- Section-level regeneration (`regenerate_section`)
- SpecCompiler (NL → spec; English keyword dictionary; explicit-key regex)
- 13 CLI commands (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section, preview, watch, rate, reflect-ingest)
- 10 Claude Code slash commands
- 7 Subagent definitions
- 22 genre Skills + 3 culture Skills + 3 other Skills (theory: voice-leading; instruments: piano; psychology: tension-resolution)
- Architecture lint tool (AST-based)
- Feature status check tool
- Pre-commit hooks; CI on Python 3.11/3.12/3.13
- Golden MIDI regression tests

**What does NOT exist yet** (⚪ — see IMPROVEMENT.md for proposals):

- Perception Substitute Layer (acoustic fingerprinting, reference matcher, psych mapper) — IMPROVEMENT.md proposal 1
- Genre profiles as structured data consumed by generators (currently genre is implemented mainly in drum patterns and Skill markdown only) — IMPROVEMENT.md proposal 2
- Motivic Development Plan in CPIR — IMPROVEMENT.md proposal 3
- Spec applicability registry and `mix_chain` — IMPROVEMENT.md proposal 4
- Arrangement engine (operations: reharmonize, regroove, reorchestrate, transpose, retempo) — IMPROVEMENT.md proposal 5
- Structured human feedback loop (`yao annotate`, FeedbackToAdaptation, UserStyleProfile) — IMPROVEMENT.md proposal 6
- Markov / constraint-solver generators
- MusicXML / LilyPond / PDF output
- DAW MCP integration
- Live improvisation mode

**Always defer to `FEATURE_STATUS.md` for the up-to-date status.**

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization:

| Pattern | What catches it | Command |
|---|---|---|
| F1: tick calculation error | Unit tests in `test_ir.py`, mandatory `yao.ir.timing` use | `make test-unit` |
| F2: silent range clamp | `RangeViolationError` in `yao.ir.notation` and constants | `make test` |
| F3: velocity hardcode | Code review pattern (no literal in `velocity=`) + lint | `make lint` |
| F4: missing provenance | `GeneratorBase` enforces return type | `mypy` |
| F5: layer boundary breach | AST-based import checker | `make arch-lint` |
| F6: schema/model mismatch | Integration test loads all templates | `make test` |
| F7: parallel fifths | Constraint checker + voicing module | `make test` |
| F8: silent fallback | RecoverableDecision wrapping + AST detector | `tools/check_silent_fallback.py` |
| F9: feature-status drift | Static check that code matches FEATURE_STATUS.md | `make feature-status` |
| F10: spec field silently ignored | Spec applicability registry (planned, IMPROVEMENT.md) | `yao validate` |

---

## Performance Expectations

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100 ms | Pydantic validation |
| Generate 8-bar piece | <1 s | Both generators |
| Generate 64-bar piece | <5 s | Stochastic may vary |
| Write MIDI file | <200 ms | pretty_midi |
| Run full lint | <500 ms | All lint rules |
| Run all tests | <30 s | ~2,157 tests |
| Architecture lint | <1 s | AST parsing |
| `yao preview` end-to-end | <2 s | Spec → MIDI → audio → playback |
| `yao watch` debounce | 500 ms | Auto-regenerate trigger |

Do not introduce changes that exceed these budgets without discussion.

---

## Coding Conventions

### Python
- Python 3.11+, `from __future__ import annotations`
- mypy strict — all public functions have type hints and docstrings
- ruff for lint and format (line length: 120)
- Pydantic for external data (YAML specs); frozen dataclasses for internal IR

### Naming
- modules: `snake_case`
- classes: `PascalCase`
- functions / variables: `snake_case`
- constants: `UPPER_SNAKE_CASE`
- music acronyms (MIDI, BPM, IR, LUFS) may stay uppercase in identifiers

### Domain vocabulary (do not mix)
- "piece" or "composition" — never "track" (track is a MIDI concept)
- "section" — Section IR (intro / verse / chorus / bridge / …)
- "motif" / "phrase" — distinct levels of musical structure
- "tick" (MIDI), "beat" (musical), "second" (real time) — never conflate
- "voicing" (chord layout) vs "orchestration" (instrument assignment) — distinct concerns

### Errors
- Define new exceptions in `src/yao/errors.py` as `YaOError` subclasses
- Never `raise ValueError(...)` — use the typed exception
- Constraint violations → `ConstraintViolation`
- Range violations → `RangeViolationError` (with fix suggestion in message)
- Spec validation → `SpecValidationError`
- Logging → `structlog` (structured), never `print()`

### Pydantic / dataclass split
- External-facing data (parsed from YAML, JSON, CLI) → Pydantic models in `schema/`
- Internal domain objects → frozen dataclasses in `ir/`

---

## Music Engineering Conventions

For full details see `.claude/guides/music-engineering.md`.

### Pitch
- MIDI 0–127. C4 (middle C) = 60.
- All conversions via `yao.ir.notation`. No manual arithmetic.
- Scientific pitch notation only ("C4", "F#3", "Bb5").

### Timing
- Default PPQ: 220 (`yao.constants.midi.DEFAULT_PPQ`).
- Tick / beat / second conversions only via `yao.ir.timing`.
- Time-signature changes only at section boundaries.

### Instrument ranges
- Centralized in `yao.constants.instruments.INSTRUMENT_RANGES` (46 instruments).
- Range violations → `RangeViolationError`. Never silently clamp.
- The error message must include the offending note and a fix suggestion.

### Velocity & dynamics
- Never hardcode (`velocity=100` is forbidden).
- Derive from `DYNAMICS_TO_VELOCITY[section.dynamics]` plus a trajectory tension modifier.
- Stochastic generators may add ±5 humanization on top.

### Chord progressions
- Functional notation in IR: Roman numerals (I, ii, V7/V).
- Concrete pitches only via `yao.ir.harmony.realize()`.
- Never mix functional and concrete representations in the same context.

### Voice leading
- `yao.ir.voicing.check_parallel_fifths()` for parallel-fifth/octave detection.
- Minimize `voice_distance()` between consecutive voicings.

### Generators
- All extend `GeneratorBase` and return `(ScoreIR, ProvenanceLog)`.
- Register via `@register_generator("name")`.
- Selected via `composition.yaml` `generation.strategy`.
- Stochastic generators use `seed` for reproducibility plus `temperature` for variation.

### Musical correctness checklist (every PR touching notes)
- [ ] All notes within instrument range
- [ ] Velocity derived from dynamics, not hardcoded
- [ ] Timing uses `yao.ir.timing`, not manual arithmetic
- [ ] Provenance records created for all generated elements
- [ ] Integration test produces valid MIDI (round-trip via `pretty_midi`)
- [ ] Constraint checker passes
- [ ] No silent fallback (or wrapped via `RecoverableDecision`)

---

## Testing Conventions

For full details see `.claude/guides/testing.md`.

### Test layout
- `tests/unit/` — per-module unit tests
- `tests/integration/` — full pipeline (spec → MIDI → analysis → evaluation)
- `tests/scenarios/` — musical scenarios (trajectory compliance, motif recall)
- `tests/music_constraints/` — instrument range / voice leading constraints (parameterized)
- `tests/golden/` — bit-exact MIDI regression against committed fixtures

### Required tests for common changes
- New generator → "params produce expected output" + "round-trip via MIDI reader is consistent"
- New IR type → ScoreIR round-trip identity test
- New evaluator metric → "good" and "bad" canonical samples score correctly apart
- New constraint → violation sample raises; conformant sample passes
- Bug fix → regression test reproducing the original bug

### Music-specific test helpers (`tests/helpers/`)
- `assert_in_range(notes, instrument)` — verify all notes within playable range
- `assert_no_parallel_fifths(voicings)` — detect parallel perfect fifths
- `assert_trajectory_match(score, trajectory, dimension, tolerance)` — validate dynamics match the curve

### Golden tests
- Use for outputs that must be bit-exact stable (canonical specs in standard generation modes).
- When a golden file is intentionally updated, the PR description must say *why*. Never auto-accept golden updates.

### Markers
- `@pytest.mark.integration` — full pipeline
- `@pytest.mark.golden` — golden output
- `@pytest.mark.music_constraints` — music theory constraints
- `@pytest.mark.subagent` — subagent evaluation

---

## Documentation Conventions

### Docstrings
- Google style. Cover `Args`, `Returns`, `Raises`, `Example` (when helpful).
- Public APIs (no leading underscore) require docstrings (mypy strict will not enforce content, but reviewers will).

### Design records
- Significant design decisions → `docs/design/NNNN-<topic>.md` (sequential numbering).
- ADR format: Context, Decision, Consequences, Alternatives considered.

### Glossary
- New domain terminology → `docs/glossary.md`.

### Diagrams and examples
- Architecture diagrams as ASCII art or mermaid.
- Music examples → `docs/examples/` with MIDI plus a screenshot of the piano roll.

---

## Adding New Components

### New Subagent
1. Add row to PROJECT.md Subagent table.
2. Create `.claude/agents/<name>.md` with: responsibility, inputs, outputs, forbidden actions, evaluation criteria.
3. Verify role does not duplicate an existing subagent.
4. Define handoff protocol with Producer.
5. Add integration test in `tests/integration/test_<name>_subagent.py`.

### New Skill
1. Create `.claude/skills/<category>/<name>.md`.
2. Cite sources (textbooks, papers, reputable sites).
3. Include at least one positive example and one counter-example.
4. List `Related:` skills.
5. If a paired data file exists (e.g. `genre_profiles/<name>.yaml`), update it within the same PR.

### New Custom Command
1. Create `.claude/commands/<name>.md`.
2. Document purpose, arguments, execution steps.
3. List `Uses:` (subagents / skills / hooks).
4. Add `Makefile` alias if appropriate.

### New spec field
1. Add Pydantic model field in `src/yao/schema/`.
2. Add applicability entry: status (Applied / Partial / Ignored), tracking issue if not yet applied.
3. Update `specs/templates/` minimal example (only if Applied).
4. Update PROJECT.md spec section.
5. Add validation test.

### New evaluation metric
1. Use a `MetricGoal` type — do not invent ad-hoc goal logic.
2. Add to `src/yao/verify/evaluator.py` registered metrics.
3. Add to PROJECT.md Section 11 metric list.
4. Add unit test that "good" and "bad" canonical samples score correctly.

### New critique rule
1. Inherit `CritiqueRule` base class.
2. Emit `Finding` with severity, evidence, location, recommendation (no free text only).
3. Register via `CritiqueRegistry`.
4. Add to PROJECT.md Section 11 (categorize: structural / harmonic / melodic / rhythmic / arrangement / emotional).
5. Add unit test with sample expected to trigger the rule and sample expected to pass.
6. Map the rule to a feedback adaptation in `conductor/feedback.py` if Conductor should react.

---

## Tooling and Library Policy

### Core dependencies (do not remove)
- `pretty_midi` — MIDI generation/editing (Layer 3, 5 only)
- `music21` — theory analysis, MusicXML (Layer 3, 6 only)
- `librosa` — audio analysis (Layer 6 only)
- `pydantic` — spec validation (Layer 1)
- `pyloudnorm` — LUFS measurement (Layer 6 only)
- `click` — CLI (CLI layer only)
- `structlog` — structured logging (any layer)

### Recommended optional dependencies
- `mido` — low-level MIDI when `pretty_midi` is insufficient
- `pedalboard` — VST chain for the future mix engine (IMPROVEMENT.md proposal 4)
- `numpy` / `scipy` — numerical
- `watchdog` — file watching (used by `yao watch`)
- `sounddevice` — direct WAV playback (used by `yao preview`)

### Adding a new dependency — checklist
1. Try first to do it with existing dependencies.
2. Check the license (avoid GPL by default).
3. Add to `pyproject.toml` with a sensible upper bound.
4. Document the rationale in `docs/dependencies.md`.
5. Optional GPU-required deps must remain optional.

### Forbidden
- Hardcoded API keys for external SaaS music generators.
- Trained model weights in `references/`. Use `models/` if you must.

---

## File and Path Conventions

### Working directories
- Temp files: `/tmp/yao-<session-id>/`
- Scratch / experiments: `scratch/` (gitignored).
- Final artifacts: `outputs/projects/<project>/iterations/v<NNN>/`

### Naming
- Iteration: `v001`, `v002`, … (3-digit zero-padded)
- Per-instrument MIDI: `<instrument>.mid` under `stems/`
- Master MIDI: `full.mid`
- Score: `score.musicxml`, `score.pdf` (when written)
- Audio: `audio.wav` (master), `stems/<instrument>.wav` (per-instrument)
- Analysis: `analysis.json`
- Evaluation: `evaluation.json`
- Critique: `critique.md`
- Provenance: `provenance.json`
- Feedback (planned): `feedback.yaml`

### Git
- `outputs/`, large `references/midi/`, and `soundfonts/` are out of git or LFS-only.
- `.gitignore` is maintained alongside any directory addition.

---

## Commit and PR Conventions

### Commit messages — Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

- `type`: `feat` | `fix` | `refactor` | `test` | `docs` | `chore` | `perf`
- `scope`: module name (`composer`, `harmony`, `ir`, `verify`, `cli`, …)
- `subject`: ≤ 50 chars, present tense

Example:

```
feat(harmony): add secondary dominant insertion to reharmonization

Implement V/V, V/vi, V/IV substitution in HarmonyTheorist subagent's
reharmonization step. Adds tension while preserving chord function.

Closes #42
```

### PR rules
- One PR = one logical change.
- PR description must include:
  - **What** — the change
  - **Why** — the reason
  - **How** — design choices made
  - **Music impact** — how it affects generated music (when applicable)
  - **Tests** — what was added or changed

### Merge gates
- All CI green.
- ≥ 1 review approval.
- Golden test changes require an explicit reason.
- `FEATURE_STATUS.md` updated when capabilities change.

---

## Escalation

Stop and ask the human when:

- Changing layer boundaries or architectural rules.
- Adding a new external dependency.
- Making a music-theory judgment call you are unsure about (e.g. "is this voicing acceptable in jazz contexts?").
- Deleting files or rewriting git history.
- Any change touching ≥ 5 files outside test directories.
- Changing the public CLI surface.
- Touching `references/catalog.yaml` rights metadata.
- Encountering a finding that suggests a generated piece is too similar to a known existing work.

Escalation is responsibility, not weakness. **When in doubt, ask.**

---

## Common Failure Patterns to Avoid

### F1 — Tick calculation drift
Mixing time signature, tempo, and resolution leads to off-by-one timing errors. **All tick operations go through `yao.ir.timing`.**

### F2 — Implicit range clamp
When a note exceeds the instrument range, do not silently move it. **Raise `RangeViolationError`** so the caller decides.

### F3 — Velocity hardcode
`velocity=100` defeats the dynamics design. **Always derive from the dynamics curve.**

### F4 — Symbolic/acoustic confusion
"BPM = 140" does not mean "feels fast." Note density, groove, and frequency content also matter. PSL (IMPROVEMENT.md proposal 1) addresses this systematically.

### F5 — TODO accumulation
TODO-laden code rots the project. **Resolve or file an issue and link the comment.**

### F6 — Provenance afterthought
"I'll write provenance later" breaks Principle 2. **Generation and provenance recording happen in the same transaction.**

### F7 — Genre by independent decree
Don't redefine "what rock is" on your own. **Update the Skill file and `genre_profiles/<name>.yaml`, get review.**

### F8 — Over-trusting automated scores
A high evaluator score does not mean good music (Principle 5). **Listen to outputs in person before declaring victory.**

### F9 — Spec field that silently does nothing
Adding a Pydantic field that no generator reads creates a silent broken promise. **Wire it through, or list it as `Ignored` in the applicability registry.**

### F10 — Provenance mutation
Once written, provenance is read-only. Modifying past entries hides what happened. **Append new entries instead.**

---

## Reference Links

Frequently consulted during development:

- Project overview: [`PROJECT.md`](./PROJECT.md)
- User-facing: [`README.md`](./README.md)
- Capability status (truth source): [`FEATURE_STATUS.md`](./FEATURE_STATUS.md)
- Forward-looking proposals: [`IMPROVEMENT.md`](./IMPROVEMENT.md)
- Target architecture: [`VISION.md`](./VISION.md)
- Design decision records: [`docs/design/`](./docs/design/)
- Glossary: [`docs/glossary.md`](./docs/glossary.md)
- Skill files: [`.claude/skills/`](./.claude/skills/)
- Slash commands: [`.claude/commands/`](./.claude/commands/)
- Subagent definitions: [`.claude/agents/`](./.claude/agents/)
- Developer guides: [`.claude/guides/`](./.claude/guides/)

External references:

- [pretty_midi docs](https://craffel.github.io/pretty-midi/)
- [music21 docs](https://music21.org/)
- [librosa docs](https://librosa.org/doc/)
- [LilyPond manual](https://lilypond.org/manuals.html)
- [Pydantic v2 docs](https://docs.pydantic.dev/)

---

## Session Start Checklist

When you start a new Claude Code session:

- [ ] Read this file (`CLAUDE.md`).
- [ ] Skim `FEATURE_STATUS.md` for current capability state.
- [ ] Read `PROJECT.md` (or recall from a recent session).
- [ ] If task touches a specific layer, read the relevant `.claude/guides/` doc.
- [ ] `view` the area of the code you will modify.
- [ ] Check existing tests for the area.
- [ ] Look for related ADRs in `docs/design/`.
- [ ] List unclear points and decide which need human input before coding.

---

## Recent Changes (selected)

- Spec applicability registry, mix chain MVP, acoustic critique rules — under design (IMPROVEMENT.md).
- Genre profile data extension — under design (IMPROVEMENT.md proposal 2).
- Phase 1 deployed and stable: 2,157 tests, CPIR pipeline, 35 critique rules, RecoverableDecision, `yao preview` / `yao watch`.

For the canonical change log, see `git log` and `FEATURE_STATUS.md` history.

---

## Closing

YaO development is not "just software." It is **the translation of music — one of humanity's most beautiful expressions — into a reproducible, improvable engineering process.** Every change you commit ultimately affects the quality of music that moves someone.

For that reason: **prefer correctness over speed, explainability over convenience, human collaboration over full automation.**

> *Build the orchestra well, so the conductor can lead it freely.*

---

## Guides (read when relevant)

| Guide | Read when |
|---|---|
| [Architecture](./.claude/guides/architecture.md) | Working across layers, adding modules |
| [Coding Conventions](./.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](./.claude/guides/music-engineering.md) | Generating or modifying notes |
| [Testing](./.claude/guides/testing.md) | Writing or running tests |
| [Workflow](./.claude/guides/workflow.md) | Planning a change |

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 2.0*
*Last updated: 2026-05-04*
