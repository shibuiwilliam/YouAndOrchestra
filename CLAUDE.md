# CLAUDE.md — YaO Development Rules

> Read this file at session start. Detailed guides in `.claude/guides/`.
> In case of conflict: CLAUDE.md > PROJECT.md > other docs.

---

## Quick Reference

```bash
make test              # All tests (~492)
make test-unit         # Unit only
make test-golden       # Golden MIDI regression
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary check
make all-checks        # lint + arch-lint + matrix-check + test + test-golden
make format            # Auto-format
```

### Key Directories

```
src/yao/constants/          Layer 0 — scales, chords, instruments          [STABLE]
src/yao/schema/             Layer 1 — Pydantic specs (v1 + v2)            [STABLE]
src/yao/ir/                 Layer 3 — ScoreIR, Note, harmony, motif       [STABLE]
src/yao/ir/plan/            Layer 3.5 — MPIR (form + harmony only)        [ALPHA]
src/yao/reflect/            Provenance, RecoverableDecision               [STABLE]
src/yao/generators/         Layer 2 — rule_based + stochastic             [STABLE]
src/yao/generators/plan/    Plan generators (form, harmony planners)      [ALPHA]
src/yao/generators/note/    Note realizers (wrappers)                     [ALPHA]
src/yao/render/             Layer 5 — MIDI writer, stems, audio, iters    [STABLE]
src/yao/verify/             Layer 6 — lint, eval, diff, constraints       [STABLE]
src/yao/verify/critique/    Rule-based critique engine                    [NOT STARTED]
src/yao/conductor/          Orchestration engine                          [STABLE]
src/yao/perception/         Layer 4 — aesthetic judgment                  [NOT STARTED]
src/yao/arrange/            Arrangement engine                            [NOT STARTED]
src/yao/sketch/             NL → spec dialogue                            [NOT STARTED]
```

### Key Types

```
Note, ScoreIR           → src/yao/ir/score_ir.py, note.py
CompositionSpec         → src/yao/schema/composition.py
CompositionSpecV2       → src/yao/schema/composition_v2.py
MusicalPlan             → src/yao/ir/plan/musical_plan.py      [ALPHA]
SongFormPlan            → src/yao/ir/plan/song_form.py         [ALPHA]
HarmonyPlan             → src/yao/ir/plan/harmony.py           [ALPHA]
ProvenanceLog           → src/yao/reflect/provenance.py
RecoverableDecision     → src/yao/reflect/recoverable.py
GeneratorBase           → src/yao/generators/base.py
EvaluationReport        → src/yao/verify/evaluator.py
MetricGoal              → src/yao/verify/metric_goal.py
```

---

## Your Role

You maintain and extend a music generation CLI tool. The working pipeline is:

```
YAML spec → PlanOrchestrator → MusicalPlan → NoteRealizer → ScoreIR → MIDI
                   ↕ (Conductor feedback loop)
           Evaluation → Adaptation → Regeneration
```

Your priorities:
1. **Don't break what works** — run `make all-checks`
2. **Keep provenance** — every generation step must log its decisions
3. **Improve output quality** — the music should sound better after your changes
4. **Keep it simple** — if a 20-line change solves the problem, don't build a new layer

---

## When You Start a Task

1. Read this file (you're doing that now)
2. Identify which files you'll touch — read them before writing
3. Check status tags above: [STABLE] = safe to modify, [ALPHA] = read impl first, [NOT STARTED] = ask before implementing
4. Write or update tests alongside your changes
5. Run `make all-checks` before considering yourself done

---

## Rules (Phase Alpha — Active)

1. **Never break layer boundaries** — lower layers cannot import upper layers. `make arch-lint` enforces this.
2. **Every generator returns `(ScoreIR, ProvenanceLog)`** — no exceptions.
3. **No public function without type hints and docstring.**
4. **No hardcoded musical values** — use `src/yao/constants/`.
5. **Use `yao.ir.timing`** for all tick/beat/second conversions.
6. **Use `yao.ir.notation`** for all note name/MIDI conversions.
7. **Derive velocity from dynamics + trajectory** — never hardcode velocity values.

---

## MUSTs

- Read existing code before writing new code
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync
- Use `YaOError` subclasses — never bare `ValueError`
- Update golden tests if output changes: `python tests/golden/tools/regenerate_goldens.py --reason "..." --confirm`

## MUST NOTs

- Import `pretty_midi` / `music21` / `librosa` outside designated layers (see Library Restrictions)
- Create functions with vague names (`make_it_sound_good`)
- Skip provenance recording for any generation step
- Silently clamp notes to range — raise `RangeViolationError` or emit `RecoverableDecision`
- Leave `TODO`/`FIXME` uncommitted

---

## Quick Decisions

| Situation | Do This |
|-----------|---------|
| Need a new constant (scale, chord, instrument) | Add to `src/yao/constants/` |
| Need beat/tick/second conversion | Use `yao.ir.timing` |
| Need note name ↔ MIDI number | Use `yao.ir.notation` |
| Need to raise an error | Use a `YaOError` subclass |
| Need to add a test | Put in `tests/unit/` unless full pipeline needed |
| Changing rendered output | Regenerate goldens: `make test-golden` |
| Not sure if a feature exists | Check Capability Matrix in PROJECT.md §4 |
| Touching 5+ files | Ask the human first |
| Adding a dependency | Ask the human first |

---

## Essential Anti-Patterns

**Don't hardcode velocity:**
```python
# BAD:  Note(pitch=60, velocity=100, ...)
# GOOD: velocity = compute_velocity(dynamics, trajectory_tension)
```

**Don't silently clamp ranges:**
```python
# BAD:  note = note.replace(pitch=instrument.range_min)
# GOOD: raise RangeViolationError(instrument, note, valid_low, valid_high)
#   or: emit RecoverableDecision and log the compromise
```

Full anti-pattern catalog: `.claude/guides/coding-conventions.md`

---

## Library Restrictions

| Library | Allowed In | Purpose |
|---------|-----------|---------|
| `pretty_midi` | ir/, render/ | MIDI creation/editing |
| `music21` | ir/, verify/ | Theory analysis |
| `librosa` | verify/, perception/ | Audio features |
| `pyloudnorm` | verify/, perception/ | LUFS measurement |
| `pydantic` | schema/ | YAML validation |
| `numpy/scipy` | anywhere | Numerical computation |

---

## Current Phase (Alpha)

### What works
- Full pipeline: YAML → generator → ScoreIR → MIDI with stems, analysis, evaluation, provenance
- Two generators: rule_based (deterministic) and stochastic (seed + temperature, 4 contours, voicings)
- Conductor feedback loop: generate → evaluate → adapt → regenerate
- Section regeneration, MIDI reader, score diffing, constraint system
- 9 CLI commands, 7 Claude Code slash commands, 7 subagent definitions, 4 skills
- v1 + v2 spec formats with auto-detection
- MetricGoal type system, RecoverableDecision mechanism
- ~492 tests (unit, integration, scenario, constraint, golden)

### What's being built (Phase Alpha)
- MPIR foundation: SongFormPlan + HarmonyPlan as intermediaries
- Plan generators (form planner, harmony planner)
- Golden MIDI test infrastructure

### What does NOT exist yet
- MotifPlan, PhrasePlan, DrumPattern, ArrangementPlan
- Adversarial Critic with structured rules
- Multi-candidate Conductor
- Perception layer, Arrangement engine, Sketch dialogue
- MusicXML / LilyPond output, DAW integration

**If a task asks you to use a feature that doesn't exist, ask the human.**

---

## Don't Do This

- Don't implement features described only in VISION.md unless explicitly asked
- Don't create new abstraction layers "for future use"
- Don't reference Phase beta types (MotifPlan, DrumPattern, ArrangementPlan) in new code
- Don't refactor working code to match the v2.0 target architecture unless that's the task
- Don't add RecoverableDecision to code that should simply raise an error
- Don't describe features that don't exist as if they do in documentation

---

## Escalation

Stop and ask the human when:
- Changing architectural boundaries or layer rules
- Adding new external dependencies
- Making music theory judgment calls you're unsure about
- Deleting files or rewriting git history
- Any change touching 5+ files
- Downgrading a feature in the Capability Matrix

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| [Architecture](.claude/guides/architecture.md) | Working across layers |
| [Coding Conventions](.claude/guides/coding-conventions.md) | Writing any code (full anti-pattern catalog) |
| [Music Engineering](.claude/guides/music-engineering.md) | Generating/modifying notes |
| [Testing](.claude/guides/testing.md) | Writing or running tests |
| [Workflow](.claude/guides/workflow.md) | Planning a change, PR process |
| [Cookbook](.claude/guides/cookbook.md) | Common tasks with step-by-step instructions |

Full design documentation: [PROJECT.md](./PROJECT.md) · Target architecture: [VISION.md](./VISION.md)

---

## Future Rules (Phase Beta)

These rules take effect when MPIR becomes the required path (after Phase Alpha):

8. **Plans before notes** — structural decisions belong in Layer 3.5 (MPIR), not in Note Realizers.
9. **Every plan generator returns `(PlanNode, ProvenanceLog)`.** Every note realizer returns `(ScoreIR, ProvenanceLog)`.
10. **No silent fallbacks** — use `RecoverableDecision` for every compromise.
11. **Trajectory is a control signal** — when trajectory values change, every generator's output must change measurably.
12. **Critique rules emit `Finding` objects** — never free text.
13. **Do not bypass MPIR** — a spec → ScoreIR path that skips MPIR is forbidden.

---

*Project: You and Orchestra (YaO) · CLAUDE.md v3.1 · Last revised: 2026-04-30*
