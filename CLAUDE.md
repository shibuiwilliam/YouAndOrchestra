# CLAUDE.md — YaO Core Rules (v1.1)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > other docs.*
> *Feature reality: see [FEATURE_STATUS.md](./FEATURE_STATUS.md) — never trust descriptions over the matrix.*

---

## What changed in v1.1

YaO is evolving through **9 progressive improvements** rather than a large redesign. This is a deliberate choice — v1.0 is working, and our job is to magnify it without breaking it.

**Key concepts new in v1.1**:
- **Principle 6: Incrementality** — "do not break what works"
- **Feature Status Matrix** — single source of truth for what's implemented
- **9 progressive improvements (★1–★9)** — each is one PR, 1–2 weeks
- **DrumPattern IR** (★1), **counter-melody** (★2), **multi-dim trajectory** (★3)
- **Mechanized Adversarial Critic** with 15+ rules (★4)
- **`yao preview` / `yao watch`** for instant audition (★6)
- **RecoverableDecision** to replace silent fallbacks (★8)
- **Golden MIDI tests** for regression detection (★9)

**Core architecture is unchanged**: still 7 layers, still 7 subagents, still 5 (now 6) principles. We extend each layer; we do not add layers.

---

## Quick Reference

```bash
make test                # All tests
make test-unit           # Unit only
make test-golden         # Golden MIDI tests (NEW in v1.1, after ★9)
make lint                # ruff + mypy strict
make arch-lint           # Layer boundary check
make all-checks          # lint + arch-lint + matrix-check + feature-status + test + golden
make format              # Auto-format
make feature-status      # Verify FEATURE_STATUS.md matches code (NEW in v1.1, after ★5)
```

### Key directories (largely unchanged from v1.0)

```
src/yao/constants/      # Layer 0 — hardcoded values (ranges, scales, MIDI mappings)
src/yao/schema/         # Layer 1 — Pydantic models for YAML
src/yao/ir/             # Layer 3 — core data types
  ├── score_ir.py
  ├── trajectory.py     # ★3 will extend this with multi-dim coupling
  ├── motif.py
  ├── harmony.py
  ├── voicing.py
  ├── drum.py           # ★1 NEW — DrumPattern IR
  ├── timing.py
  └── notation.py
src/yao/generators/     # Layer 2
  ├── rule_based.py
  ├── stochastic.py
  ├── drum_patterner.py # ★1 NEW
  └── counter_melody.py # ★2 NEW
src/yao/render/         # Layer 5 — MIDI / audio / stems
src/yao/verify/         # Layer 6
  ├── music_lint.py
  ├── analyzer.py
  ├── evaluator.py
  ├── diff.py
  ├── recoverable.py    # ★8 NEW
  └── critique/         # ★4 NEW — 15+ rules
      ├── base.py
      ├── registry.py
      └── (per role)
src/yao/reflect/        # Provenance
src/yao/conductor/      # Generate-evaluate-adapt loop
src/yao/errors.py       # All custom exceptions
src/cli/                # CLI commands
  ├── compose.py
  ├── conduct.py
  ├── render.py
  ├── preview.py        # ★6 NEW
  └── watch.py          # ★6 NEW

drum_patterns/          # ★1 NEW — 8+ genre drum YAMLs
```

### Key types

```
Note                 → src/yao/ir/score_ir.py
ScoreIR              → src/yao/ir/score_ir.py
DrumPattern, DrumHit → src/yao/ir/drum.py             ★1 NEW
CompositionSpec      → src/yao/schema/composition.py
ProvenanceLog        → src/yao/reflect/provenance.py
GeneratorBase        → src/yao/generators/base.py
Finding              → src/yao/verify/critique/base.py ★4 NEW
RecoverableDecision  → src/yao/verify/recoverable.py   ★8 NEW
MultiDimensionalTrajectory → src/yao/ir/trajectory.py
GenerationParams     → src/yao/ir/trajectory.py        ★3 NEW
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build infrastructure that Subagents will use. Your code enables reproducible, auditable, iterable music creation.

In v1.1, your concrete mission is:

> **Implement one of the 9 progressive improvements (★1–★9) per PR, without breaking anything else.**

You are not redesigning the architecture. You are extending it carefully, one well-tested layer at a time.

---

## 6 Non-Negotiable Rules (v1.1)

Five rules carried from v1.0, plus one new rule that captures the spirit of v1.1.

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`** — including new generators (drum_patterner, counter_melody)
3. **No silent fallbacks** — constraint violations must be explicit errors *or* logged as `RecoverableDecision` (★8)
4. **No hardcoded musical values** — use `src/yao/constants/`
5. **No public function without type hints and docstring**
6. **★ NEW — Do not break what works** — every change must preserve existing behavior unless explicitly approved. Existing specs must still produce reasonable output. Existing tests must still pass. Existing golden MIDI must still match (or have a documented reason for change).

---

## MUSTs

### Always-on
- Read existing code before writing new code
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Derive velocity from dynamics curves and trajectory tension (never hardcode)
- Register generators via `@register_generator("name")`

### v1.1-specific
- ★ **Update [FEATURE_STATUS.md](./FEATURE_STATUS.md)** in the same PR as any feature change
- ★ **Run `make feature-status`** before opening a PR — it warns if FEATURE_STATUS.md and code disagree
- ★ **One PR = one improvement (★N)** — do not bundle ★1 and ★3 in the same PR
- ★ **Backward compatibility check** — the existing `specs/templates/*.yaml` must still load and produce MIDI without modification
- ★ **Golden MIDI verification** — after ★9 lands, run `make test-golden` before any PR touching generators or rendering
- ★ **When adding a new module, follow the directory layout in PROJECT.md §5**, not your own structure
- ★ When generating any compromise (e.g., out-of-range note), log a `RecoverableDecision` (★8 onward)

---

## MUST NOTs

### Carried from v1.0
- Import `pretty_midi` / `music21` / `librosa` outside designated layers
- Create functions with vague names (`make_it_sound_good`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError`)
- Leave `TODO`/`FIXME` uncommitted

### v1.1-specific
- ★ **Do not redesign architecture** — if a task requires "let's change the layer structure", escalate. The 7-layer model is unchanged in v1.1.
- ★ **Do not bundle multiple improvements in one PR** — each ★N is independent
- ★ **Do not advance FEATURE_STATUS.md optimistically** — implementation drives status, not aspiration
- ★ **Do not skip the audio sample for sound-affecting changes** — ★1, ★2, ★3 PRs require before/after audio
- ★ **Do not introduce a new layer** — extend existing layers (Layer 3 gets DrumPattern, Layer 6 gets critique/, etc.)
- ★ **Do not reference v2.0 design** — YaO v2.0 (8-layer, MPIR) was not adopted. Forget about MPIR; we extend Layer 3 instead.

---

## 6 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes (★3 makes this real across 5 dimensions)
5. **Human ear is truth** — automated scores inform, humans decide
6. **★ Incrementality — do not break what works** — small, verifiable improvements over grand redesigns

When in doubt, ask: *Does this preserve existing behavior while adding new capability?* If yes, proceed. If no, escalate.

---

## FEATURE_STATUS.md Anchor

The full matrix lives in **[FEATURE_STATUS.md](./FEATURE_STATUS.md)** (also summarized in [PROJECT.md §4](./PROJECT.md)). Before any non-trivial work, read it.

When the matrix says:

| Status | What you can assume |
|---|---|
| ✅ Stable | Working with tests; safe to depend on |
| 🟢 Working but limited | Core works; check edge cases noted in the matrix |
| 🟡 Partial | Some paths work; **read the impl before depending** |
| ⚪ Designed, not started | Don't import; don't pretend it exists |
| 🔴 Identified gap | Treat as a target, not a tool |

**Hard rule**: If you write code that depends on a `⚪` or `🔴` feature, the PR is rejected. Wait for that improvement's PR to land first.

---

## The 9 Improvements: Your Worklist

This section is the heart of v1.1. Each improvement is a single PR. Pick one and complete it before moving on.

### ★1 DrumPattern IR + drum_patterner generator
**Goal**: Enable pop, EDM, rock, hip-hop, lo-fi, game BGM by introducing dedicated drum representation.
**New files**: `src/yao/ir/drum.py`, `src/yao/generators/drum_patterner.py`, `drum_patterns/*.yaml` (8+).
**Modified**: `src/yao/schema/composition.py` (add `DrumsSpec`).
**Cost**: Medium (~2 weeks).
**Validation**: existing specs still produce MIDI without drums; new specs with `drums:` section produce a `drums.mid` stem.

### ★2 Counter-melody / Inner-voice generator
**Goal**: Move from 3-voice (melody + bass + chord) to 6-voice with counter-melody and inner voices.
**New files**: `src/yao/generators/counter_melody.py`.
**Modified**: `src/yao/schema/composition.py` (add `counter_melody` role to `InstrumentSpec.role`).
**Cost**: Medium (~1.5 weeks).
**Validation**: Species counterpoint principles enforced (consonance on strong beats, no parallel fifths/octaves with main melody, contrary motion preferred). Range stays within target instrument.

### ★3 Trajectory multi-dimensional coupling
**Goal**: Make tension/density/predictability/brightness/register_height **all** affect generation, not just velocity.
**New files**: none (extend `src/yao/ir/trajectory.py`).
**Modified**: `src/yao/ir/trajectory.py` (add `derive_generation_params()`), `src/yao/generators/rule_based.py` and `stochastic.py` (call it per bar).
**Cost**: Medium (~1.5 weeks).
**Validation**: `tests/scenarios/test_trajectory_compliance.py` confirms high-tension produces wider pitch range, more leaps, and more chord extensions — not just louder velocity.

### ★4 Adversarial Critic mechanized rules (15+)
**Goal**: Move `/critique` from free-text LLM interpretation to deterministic, structured Findings.
**New files**: `src/yao/verify/critique/` package with `base.py`, `registry.py`, and rule files per role (structural / melodic / harmonic / rhythmic / arrangement / emotional).
**Modified**: `.claude/commands/critique.md` (use the structured output instead of free interpretation).
**Cost**: Large (~3–4 weeks; ~half a day per rule × 15). Parallelizable across rules.
**Validation**: every rule has 1+ positive test (rule fires) and 1+ negative test (rule silent). Re-running `/critique` on the same iteration produces identical findings.

### ★5 FEATURE_STATUS.md + feature_status_check
**Goal**: Eliminate documentation drift by having a single authoritative status table.
**New files**: `FEATURE_STATUS.md`, `tools/feature_status_check.py`.
**Modified**: `README.md` and `CLAUDE.md` lose their numeric capability claims (e.g., "226 tests"), replaced by links to FEATURE_STATUS.md.
**Cost**: Small (~2–3 days).
**Validation**: `make feature-status` runs in CI and reports any drift.

### ★6 yao preview / yao watch (instant audition)
**Goal**: Reduce iteration time from tens of seconds to real-time. Enable "edit YAML → hear change" workflow.
**New files**: `src/cli/preview.py`, `src/cli/watch.py`.
**New deps**: `sounddevice`, `watchdog`.
**Cost**: Small–medium (~1 week).
**Validation**: `yao preview specs/templates/minimal.yaml` plays audio without writing any file. `yao watch <spec>` re-plays automatically when the spec is saved.

### ★7 Genre Skills mass production (8+)
**Goal**: Move from 1 genre Skill (cinematic) to 8+, enabling broad style coverage.
**New files**: `.claude/skills/genres/{lofi_hiphop,j_pop,neoclassical,ambient,jazz_ballad,game_8bit_chiptune,acoustic_folk,...}.md` plus auto-generated YAML companions in `src/yao/skills/genres/`.
**Cost**: Medium (half a day each × 7 = 3–4 days). **Python-free contribution path** for musicians.
**Validation**: Each Skill follows the standard schema. Front-matter YAML is auto-extracted to `src/yao/skills/genres/<name>.yaml`. Generators can reference these for default tempo/keys/progressions.

### ★8 RecoverableDecision logging
**Goal**: Eliminate silent fallbacks by logging every compromise as a structured `RecoverableDecision`.
**New files**: `src/yao/verify/recoverable.py`, `src/yao/verify/recoverable_codes.py`, `tools/check_silent_fallback.py`, `docs/migration/silent-fallback-inventory.md`.
**Modified**: `src/yao/reflect/provenance.py` (add `record_recoverable()`), existing fallback sites in `stochastic.py` etc.
**Cost**: Medium (~1.5 weeks).
**Validation**: `tools/check_silent_fallback.py` detects untracked silent compromises in CI. Existing `provenance.json` files gain a `recoverable_decisions` array.

### ★9 Golden MIDI tests
**Goal**: Detect unintended musical regression in any future generator change.
**New files**: `tests/golden/{inputs,expected}/`, `tests/golden/test_golden.py`, `tests/golden/tools/regenerate_goldens.py`.
**Modified**: `Makefile` (add `test-golden`), CI workflow (run `test-golden`).
**Cost**: Small (~1 week).
**Validation**: 6+ golden MIDI files committed. Bit-exact comparison. `regenerate_goldens.py --reason "..." --confirm` is the only way to update them.

### Recommended order

```
Week 1:    ★5 FEATURE_STATUS.md (2-3 days) + ★9 Golden MIDI infrastructure
Week 2:    ★6 yao preview / watch
Week 3-4:  ★3 Trajectory multi-dim
Week 5-6:  ★1 DrumPattern IR
Week 7-8:  ★2 Counter-melody
Week 9-12: ★4 Critic rules (parallel)
Week 9-12: ★7 Genre Skills (parallel, contributors welcome)
Week 13-14: ★8 RecoverableDecision
```

★5 first because it scaffolds discipline. ★9 second because it's the safety net for everything else. ★6 third because it improves your own development feedback loop. Then the music-quality improvements stack up.

---

## Two Critical Discipline Rules for v1.1

### Rule A: One PR = One Improvement

A PR titled "feat: implement ★1 DrumPattern IR" must touch only files relevant to ★1. If you find yourself wanting to "also fix this little thing in stochastic.py while I'm here", **stop**. Open a separate PR.

This keeps:
- Reviews focused
- Rollbacks possible (revert one PR = lose one improvement, not eight)
- Golden MIDI diffs interpretable (a change in drum output is from ★1; a change in melodic contour is from ★3)

### Rule B: Backward Compatibility Is Sacred

Every PR must satisfy:

```bash
# Existing test suite passes unchanged
make test

# All shipped templates still produce MIDI without modification
yao compose specs/templates/minimal.yaml
yao compose specs/templates/bgm-90sec.yaml
yao compose specs/templates/cinematic-3min.yaml

# Existing example projects still produce MIDI
for proj in specs/projects/*/; do
    yao compose "$proj/composition.yaml"
done

# After ★9 lands: golden MIDI bit-exact
make test-golden
```

If a PR cannot satisfy this, it requires explicit approval and a documented migration path for users.

---

## Anti-Patterns (carried + new for v1.1)

### ❌ Anti-pattern 1: Velocity hardcode (carried)
```python
# DON'T
note = Note(pitch=60, velocity=100, ...)

# DO
velocity = velocity_from(
    dynamics=section.dynamics,
    tension=trajectory.tension_at(beat),
    humanization=stochastic_jitter(seed, ±5),
)
note = Note(pitch=60, velocity=velocity, ...)
```

### ❌ Anti-pattern 2: Silent fallback (carried, formalized in ★8)
```python
# DON'T
if note.pitch < instrument.range_min:
    note = note.replace(pitch=instrument.range_min)  # silent clamp

# DO (after ★8)
if note.pitch < instrument.range_min:
    decision = RecoverableDecision(
        code="NOTE_OUT_OF_RANGE",
        severity="warning",
        original_value=note.pitch,
        recovered_value=instrument.range_min,
        reason="Walking bass passing tone below upright bass range",
        musical_impact="Bass line jumps up at this point",
        suggested_fix=["narrow walking bass intervals", "use synth_bass"],
    )
    provenance.record_recoverable(decision)
    note = note.replace(pitch=decision.recovered_value)
```

### ❌ Anti-pattern 3: Bundling improvements (NEW)
```
PR title: "feat: implement drum patterns and counter-melody"
```
This is **two improvements in one PR**. Reject. Split into two PRs.

### ❌ Anti-pattern 4: Skipping FEATURE_STATUS.md update (NEW)
You added a fully-tested DrumPattern IR with 8 genres of patterns, but FEATURE_STATUS.md still says `🔴 Not implemented`. The PR is incomplete. Update the matrix in the same PR.

### ❌ Anti-pattern 5: Trajectory ignored (NEW, formalized in ★3)
```python
# DON'T (v1.0 stochastic generator behavior)
def realize_chorus(spec, trajectory):
    notes = []
    for beat in chorus_beats:
        velocity = base_velocity + trajectory.tension_at(beat) * 20  # only velocity changes
        notes.append(make_note(velocity, ...))
    return notes

# DO (after ★3)
def realize_chorus(spec, trajectory):
    notes = []
    for bar in chorus_bars:
        params = derive_generation_params(trajectory, bar)
        # Now ALL of these change: velocity, density, leap_prob, register_spread, chord_extension_prob
        notes.extend(make_notes(params))
    return notes
```

### ❌ Anti-pattern 6: Architecture redesign in disguise (NEW)
```python
# DON'T — this is sneaking in a new layer
class MusicalPlan:  # this is the rejected v2.0 MPIR
    form: SongFormPlan
    harmony: HarmonyPlan
    ...
```
v1.1 does not introduce new layers. If you find yourself designing a new IR that sits between Layer 1 (spec) and Layer 3 (ScoreIR), stop and escalate.

### ❌ Anti-pattern 7: Free-text critique after ★4 lands (NEW)
```python
# DON'T (after ★4)
def critique(score: ScoreIR) -> str:
    return llm.complete(f"What's wrong with this music?\n{score}")

# DO
def critique(score: ScoreIR, spec: CompositionSpec) -> list[Finding]:
    findings = []
    for rule in CRITIQUE_REGISTRY.all_rules():
        findings.extend(rule.detect(score, spec))
    return findings
```

---

## Automated Failure Prevention (v1.1 expanded)

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests | `make test-unit` |
| Range violation silence | `RangeViolationError` + `RecoverableDecision` checker (★8) | `make test` |
| Velocity hardcode | Linter pattern check | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` + `make test` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| ★ NEW: FEATURE_STATUS.md drift | `feature_status_check.py` (★5) | `make feature-status` |
| ★ NEW: Trajectory ignored | `test_trajectory_compliance.py` (★3) | `make test` |
| ★ NEW: Silent fallback | `check_silent_fallback.py` (★8) | `make lint` |
| ★ NEW: Free-text critique | Type contract on `Finding` (★4) | `mypy` |
| ★ NEW: Generation regression | Golden MIDI bit-exact (★9) | `make test-golden` |
| ★ NEW: Backward incompatibility | All shipped templates still compose | (manual + CI) |

---

## Performance Expectations

The 9 improvements add capabilities but should not significantly slow generation:

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Generate 8-bar piece (no drums) | <1s | Both generators |
| Generate 8-bar piece with drums (★1) | <1.5s | DrumPatterner adds ~30% |
| Generate 8-bar piece with counter-melody (★2) | <1.3s | Counter-melody adds ~20% |
| Generate 64-bar piece | <5s | Stochastic may vary |
| Run all critique rules (★4) | <2s | All 15+ rules over a 64-bar score |
| Audio render (FluidSynth) | <10s | 64 bars |
| `yao preview` time-to-first-sound (★6) | <2s | Memory-only, no FluidSynth file write |
| Run all tests | <12s | ~280 tests projected (+50 from v1.0) |
| Golden MIDI test (★9) | <3s | Bit-exact MIDI comparison |
| Architecture lint | <1s | AST parsing |

Do not introduce changes that exceed these budgets without discussion.

---

## Current Phase

**Phase 1.1** — Progressive enhancement of v1.0's working baseline.

### What EXISTS (carried from v1.0)
- Spec loading + validation (YAML → Pydantic)
- ScoreIR (Note, Part, Section, Motif, Voicing, Harmony)
- Rule-based generator (deterministic)
- Stochastic generator (seed + temperature)
- Generator registry
- Constraint system (must/must_not/prefer/avoid with scoped rules)
- MIDI rendering + per-instrument stems
- Audio rendering via FluidSynth
- MIDI reader (load existing MIDI back to ScoreIR)
- Music linting, analysis, evaluation, score diff
- Provenance logging (append-only, queryable)
- Conductor feedback loop (generate → evaluate → adapt → regenerate)
- Section-level regeneration
- CLI: compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section
- Architecture lint
- 7 Claude Code commands, 7 Subagent definitions
- 4 Skills populated (cinematic, voice-leading, piano, tension-resolution)
- ~226 tests

### What is BEING BUILT in v1.1 (the 9 improvements)
- ⏳ ★5 FEATURE_STATUS.md
- ⏳ ★9 Golden MIDI tests
- ⏳ ★6 `yao preview` / `yao watch`
- ⏳ ★3 Trajectory multi-dim coupling
- ⏳ ★1 DrumPattern IR + drum_patterner
- ⏳ ★2 Counter-melody generator
- ⏳ ★4 Adversarial Critic rules (15+)
- ⏳ ★7 Genre Skills (8+)
- ⏳ ★8 RecoverableDecision

### What does NOT EXIST yet (Phase 2 onward)
- Arrangement engine (Phase 2 marquee feature)
- Perception layer (reference matching, psychology) — Phase 3
- Production manifest + mix chain — Phase 4
- DAW integration (MCP) — Phase 4
- MusicXML / LilyPond / Strudel writers — Phase 4
- Live improvisation mode — Phase 5
- Reflection layer (style profiles) — Phase 5

**If a task asks you to implement a Phase 2+ feature, escalate.**

---

## Workflow

### When you start a session

1. Read this file (CLAUDE.md)
2. Read [FEATURE_STATUS.md](./FEATURE_STATUS.md) for current reality
3. Identify which improvement (★N) you're working on
4. Read the existing tests for the layer you'll touch
5. Read the corresponding section of PROJECT.md §14 for that improvement's full design

### Before opening a PR

```bash
# 1. Standard checks
make all-checks

# 2. After ★9 lands: regression check
make test-golden

# 3. After ★5 lands: documentation discipline
make feature-status

# 4. Backward compatibility manual check
yao compose specs/templates/minimal.yaml
yao compose specs/templates/bgm-90sec.yaml

# 5. If your change affects audio output (★1, ★2, ★3, ★8 onward)
yao compose specs/templates/minimal.yaml --render-audio
# Listen and capture before/after audio for the PR
```

### PR description template (v1.1)

```markdown
## Improvement
★N — <name>

## What
<one line>

## Why
<reason / linked issue>

## How
<key implementation choices>

## FEATURE_STATUS.md
- Updated entries: <list>

## Backward compatibility
- [ ] All shipped templates still compose without modification
- [ ] make test passes unchanged
- [ ] make test-golden passes (or goldens regenerated with documented reason)

## Audio impact
<sample link or "no audio impact">

## Tests
- Added: <list>
- Modified: <list>
```

---

## Escalation

Stop and ask the human when:

- Changing architectural boundaries or layer rules (the 7 layers are fixed in v1.1)
- Adding new external dependencies beyond `sounddevice`/`watchdog` (★6) and `pedalboard` (Phase 4)
- Making music theory judgment calls you're unsure about
- Deleting files or rewriting git history
- ★ A task seems to require touching 2+ improvements at once — split it
- ★ A task seems to require a new layer or major IR restructuring — this is v2.0 territory and was explicitly rejected
- ★ Backward compatibility cannot be preserved (e.g., a spec field must be renamed)
- ★ Modifying golden MIDI files (after ★9 lands)
- ★ FEATURE_STATUS.md needs to downgrade a feature (`✅` → anything else)

Escalation is responsibility, not weakness. **When uncertain, ask.**

---

## Common Tasks Cookbook

### "Add a new genre Skill" (this is ★7)

1. Choose a genre from the priority list (lofi_hiphop, j_pop, etc.)
2. Create `.claude/skills/genres/<name>.md` following the standard schema
3. Verify front-matter YAML is correct (used by auto-generation)
4. Run the front-matter extractor: `python tools/skill_yaml_sync.py`
5. Add at least one drum pattern in `drum_patterns/<related>.yaml` if needed (depends on ★1)
6. Update FEATURE_STATUS.md: Skills row
7. PR title: `feat(skills): add <genre> genre skill (★7)`

### "Add a new critique rule" (this is part of ★4)

1. Identify the role (structural / melodic / harmonic / rhythmic / arrangement / emotional)
2. Create or extend `src/yao/verify/critique/<role>.py`
3. Inherit `CritiqueRule` and implement `detect(score, spec) -> list[Finding]`
4. Register in `src/yao/verify/critique/registry.py`
5. Write 2+ tests:
   - Positive: feed a fixture that should trigger the rule, assert finding present
   - Negative: feed a clean fixture, assert no finding from this rule
6. Update FEATURE_STATUS.md: Critique row (increment rule count)
7. PR title: `feat(critique): add <RuleName> detector (★4)`

### "Add a new instrument range or scale"

1. Edit `src/yao/constants/<file>.py` (instruments.py / scales.py / chords.py)
2. Add unit test verifying the constant is accessible and reasonable
3. If it changes generator behavior, run `make test-golden` and document any drift

### "Edit composition.yaml schema (additive change)"

1. Make additive changes only — never rename existing fields
2. Update Pydantic model in `src/yao/schema/composition.py`
3. Update at least one template in `specs/templates/`
4. Update PROJECT.md §8 example if relevant
5. Verify all existing project specs still load
6. PR title: `feat(schema): add <field> to <section> (★N)`

### "Edit composition.yaml schema (renaming/breaking change)"

**Stop. Escalate.** Breaking schema changes violate Rule #6 (Incrementality).

If absolutely required: provide a migration script in `tools/migrate_spec.py`, support both old and new for at least one release, and document deprecation in CHANGELOG.

### "Add `yao watch` watcher" (this is ★6)

1. Create `src/cli/watch.py` using `watchdog.observers.Observer`
2. Listen for file modifications on the spec path
3. On change: re-run compose in memory, play via `sounddevice`
4. Show a clean status line (not a flood of logs)
5. Handle Ctrl+C gracefully
6. Add `yao watch` to the click command group in `src/cli/__init__.py`
7. PR title: `feat(cli): add yao watch for hot-reload audition (★6)`

---

## Library Restrictions (carried, with v1.1 additions)

| Library | Allowed in | Purpose |
|---|---|---|
| `pretty_midi` | `ir/`, `render/` | MIDI creation/editing |
| `music21` | `ir/`, `verify/` | Theory analysis, MusicXML |
| `librosa` | `verify/`, `perception/` (future) | Audio feature analysis |
| `pyloudnorm` | `verify/`, `perception/` (future) | LUFS measurement |
| `pydantic` | `schema/` | YAML validation |
| `structlog` | anywhere | Structured logging |
| `click` | `cli/` | CLI framework |
| `numpy/scipy` | anywhere | Numerical computation |
| **★ NEW: `sounddevice`** | `cli/` only | Audio playback (★6) |
| **★ NEW: `watchdog`** | `cli/` only | File watching (★6) |
| `pedalboard` | (future) `render/production/` | Audio plugin processing (Phase 4 — do not use yet) |

**Never**:
- music21 for MIDI generation (use pretty_midi)
- librosa for MIDI ops
- pretty_midi for theory analysis
- ★ sounddevice or watchdog outside `cli/` (these are user-facing only)
- ★ pedalboard before Phase 4 lands

---

## Recent Changes

- **2026-04-29 (v1.1)**: Introduced 9 progressive improvements, Principle 6 (Incrementality), FEATURE_STATUS.md as single source of truth. Rejected v2.0 MPIR redesign in favor of incremental Layer-3/Layer-2 extensions. New types: DrumPattern, Finding, RecoverableDecision, GenerationParams. New CLI: yao preview, yao watch. New deps: sounddevice, watchdog. Architecture (7 layers) unchanged.
- **2026-04-29 (v1.0.x)**: MIDI reader, section regeneration (Conductor + CLI), evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades (compose/critique/sketch/regenerate-section), 4 skills populated, mypy fixes (140→0 errors)
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff
- **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Claude Code commands/agents
- **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md

---

## Why this approach for v1.1

Earlier proposals suggested large architectural revisions (an 8-layer model with a Musical Plan IR, a 180-day migration plan). Those proposals were ambitious but did not get implemented.

v1.1 takes the opposite stance:

> **A working v1.0 is more valuable than a designed v2.0. Improve v1.0 in small, verifiable steps.**

This means:
- No new layers, no new IR types between Spec and ScoreIR (only DrumPattern as a parallel IR)
- No global pipeline restructuring
- No "migration phase" that puts everything on hold
- Each improvement ships independently and provides immediate value
- Backward compatibility is a hard constraint, not a "nice to have"

You will be tempted, while implementing ★1, to think "this would be cleaner if we also did ★3 here". Resist. Each improvement on its own is small and reversible. Together they transform YaO from a "phase 1 demo" into a real music production tool.

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| [Architecture](.claude/guides/architecture.md) | Working across layers, adding modules — note: 7 layers are fixed in v1.1 |
| [Coding Conventions](.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](.claude/guides/music-engineering.md) | Generating/modifying notes |
| [Testing](.claude/guides/testing.md) | Writing or running tests (incl. golden MIDI after ★9) |
| [Workflow](.claude/guides/workflow.md) | Planning a change |

Full design documentation: [PROJECT.md](./PROJECT.md)
Feature reality: [FEATURE_STATUS.md](./FEATURE_STATUS.md)

---

## Closing thought

You are extending a working environment, not rebuilding it. Each PR you ship adds one capability and preserves all existing ones. Over 3–4 months, these accumulate into a tool that is genuinely useful for diverse, high-quality music production.

When you're tempted to redesign, remember: **v1.0 works. v1.1 makes it sing.**

> *Your vision. Your taste. Your soul.*
> *— and an Orchestra ready to grow with you, one careful step at a time.*

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 1.1*
*Supersedes: CLAUDE.md v1.0 (2026-04-28)*
*Last revised: 2026-04-29*
