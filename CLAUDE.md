# CLAUDE.md — YaO Core Rules (v2.0)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > other docs.*
> *Implementation reality: see [Capability Matrix in PROJECT.md §5](./PROJECT.md#5-capability-matrix透明性の核-v20) — never trust descriptions over the Matrix.*

---

## What's New in v2.0

YaO has evolved past Phase 1. The architecture and rules have changed accordingly.

**Key architectural change**: a new layer **3a (Composition Plan IR, "CPIR")** sits above ScoreIR. The pipeline is now `Spec → CPIR → ScoreIR`, not `Spec → ScoreIR`. **Most non-trivial work touches CPIR or its consumers.** If you don't know what CPIR is, stop and read [PROJECT.md §7](./PROJECT.md#7-composition-plan-ircpir-v20-の心臓部) first.

**Other v2.0 additions**:
- **Capability Matrix** is the single source of truth for what works
- **Vertical Alignment** — input / processing / evaluation must advance together (Principle 6)
- **MetricGoal** type system replaces single tolerance check
- **RecoverableDecision** replaces silent fallbacks
- **Adversarial Critic Rule Registry** (30+ rules) replaces free-text critique
- **Music-as-Plan** philosophy supersedes Music-as-Code

The 5 design principles from v1.0 are intact. We added a 6th meta-principle.

---

## Quick Reference

```bash
make test                # All tests
make test-unit           # Unit only
make test-golden         # ★v2.0: Golden MIDI tests
make test-subagent       # ★v2.0: Subagent eval tests
make lint                # ruff + mypy strict
make arch-lint           # Layer boundary check (now Layer 3a/3b aware)
make matrix-check        # ★v2.0: Capability Matrix vs reality
make all-checks          # lint + arch-lint + matrix-check + test
make format              # Auto-format
```

### Key directories (v2.0)

```
src/yao/constants/        Layer 0 — hardcoded values
src/yao/schema/           Layer 1 — Pydantic models for YAML
src/yao/ir/
  ├── score_ir.py         Layer 3b — concrete notes (existing)
  ├── plan/               ★v2.0 Layer 3a — CPIR
  │   ├── form.py
  │   ├── harmony.py
  │   ├── motif.py
  │   ├── phrase.py
  │   ├── drums.py
  │   ├── arrangement.py
  │   └── composition_plan.py
  ├── trajectory.py       5-dimensional curves
  ├── timing.py           Tick/beat/second
  ├── notation.py         Note ↔ MIDI
  └── voicing.py
src/yao/reflect/          Provenance (cross-cutting)
src/yao/generators/
  ├── plan/               ★v2.0: produce CPIR
  │   ├── form_planner.py
  │   ├── harmony_planner.py
  │   ├── motif_planner.py
  │   ├── drum_patterner.py
  │   └── arranger.py
  └── note/               ★v2.0: CPIR → ScoreIR
      ├── rule_based.py   (existing, repositioned)
      ├── stochastic.py   (existing, repositioned)
      ├── markov.py
      └── constraint_solver.py
src/yao/perception/       Layer 4 — substitute hearing (3 stages)
src/yao/render/
  ├── midi_writer.py
  ├── audio_renderer.py
  ├── musicxml_writer.py  ★v2.0
  ├── lilypond_writer.py  ★v2.0
  ├── strudel_emitter.py  ★v2.0
  └── production/         ★v2.0: manifest, mix chain
src/yao/verify/
  ├── critique/           ★v2.0: Rule Registry (30+)
  ├── metric_goal.py      ★v2.0: typed evaluation goals
  ├── recoverable.py      ★v2.0: explicit fallback tracking
  ├── lint.py
  ├── analyzer.py
  ├── evaluator.py
  └── diff.py
src/yao/arrange/          ★v2.0: Layer 5.5 — arrangement engine
src/yao/conductor/
  ├── conductor.py
  ├── multi_candidate.py  ★v2.0
  └── feedback.py
src/yao/sketch/           ★v2.0: NL → spec dialogue
src/yao/errors.py
src/yao/types.py
drum_patterns/            ★v2.0: 12+ genre YAMLs
```

### Key types (v2.0)

```
Note                   → src/yao/ir/score_ir.py
ScoreIR                → src/yao/ir/score_ir.py
CompositionPlan        → src/yao/ir/plan/composition_plan.py     ★v2.0
FormPlan               → src/yao/ir/plan/form.py                 ★v2.0
HarmonyPlan            → src/yao/ir/plan/harmony.py              ★v2.0
MotifPlan, PhrasePlan  → src/yao/ir/plan/motif.py, phrase.py     ★v2.0
DrumPattern            → src/yao/ir/plan/drums.py                ★v2.0
ArrangementPlan        → src/yao/ir/plan/arrangement.py          ★v2.0
MultiDimensionalTrajectory → src/yao/ir/trajectory.py
CompositionSpec (v2)   → src/yao/schema/composition.py
ProvenanceLog          → src/yao/reflect/provenance.py
PlanGeneratorBase      → src/yao/generators/plan/base.py         ★v2.0
NoteRealizerBase       → src/yao/generators/note/base.py         ★v2.0
Finding                → src/yao/verify/critique/types.py        ★v2.0
MetricGoal             → src/yao/verify/metric_goal.py           ★v2.0
RecoverableDecision    → src/yao/verify/recoverable.py           ★v2.0
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that Subagents will use. Your code enables reproducible, auditable, iterable music creation through *plans*, not just notes.

Three sentences that should govern your work:

1. **You write the planner that the Composer Subagent will run** — not the music itself.
2. **You write the critic rules that the Adversarial Critic will evaluate** — not the critique prose.
3. **You write the realizer that turns plans into notes** — not by inventing notes from prose, but by faithfully realizing a structured plan.

If you find yourself writing notes directly from a YAML spec without a plan in between, stop. That path is no longer valid in v2.0.

---

## 7 Non-Negotiable Rules (v2.0)

The 5 rules from v1.0 are intact. Two new rules (#6, #7) reflect the CPIR architecture.

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`. Layer 3a (CPIR) is enforced like any other layer.
2. **Every plan generator returns `(<PlanComponent>, ProvenanceLog)`. Every note realizer returns `(ScoreIR, ProvenanceLog)`.** No exceptions.
3. **No silent fallbacks** — use `RecoverableDecision` to log every compromise. Tests assert no clamp/coerce happens without a `RecoverableDecision` record.
4. **No hardcoded musical values** — use `src/yao/constants/`.
5. **No public function without type hints and docstring.**
6. **★ NEW: Plans before notes.** When a feature involves "more than placing a note," it belongs in Layer 3a (CPIR). Do not put structural decisions in Note Realizers.
7. **★ NEW: Trajectory is a control signal, not a decoration.** When trajectory values change, *every* relevant generator must respond. Velocity-only changes are a regression.

---

## MUSTs

### Always-on (carried from v1.0)

- Read existing code before writing new code
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Derive velocity from dynamics curves (and trajectory tension — see Rule #7)

### v2.0-specific (NEW)

- ★ **Update the [Capability Matrix](./PROJECT.md#5-capability-matrix透明性の核-v20)** in the same PR as any feature change
- ★ Run `make matrix-check` before opening a PR — it fails if Matrix and code disagree
- ★ Register plan generators via `@register_plan_generator("name")` (NOT the legacy `@register_generator`)
- ★ Register note realizers via `@register_note_realizer("name")`
- ★ When generating any plan or note, **call `provenance.record(...)`** with a structured rationale. The codebase asserts coverage: untraced generation fails CI.
- ★ When a generator must compromise, **emit a `RecoverableDecision`** before continuing
- ★ Critique rules must inherit `CritiqueRule` and emit structured `Finding` objects — never free text
- ★ When you change something that affects rendered audio, **attach an audio sample to the PR** (Sound-First culture)

---

## MUST NOTs

### Carried from v1.0

- Import `pretty_midi`/`music21`/`librosa` outside designated layers
- Create functions with vague names (`make_it_sound_good`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError` *or* emit a `RecoverableDecision`)
- Leave `TODO`/`FIXME` uncommitted

### New in v2.0

- ★ **Do not write structural decisions in Note Realizers.** "Which chord should the chorus end on?" is a HarmonyPlanner question, not a stochastic generator question.
- ★ **Do not put musical knowledge in Conductor.** Conductor orchestrates; it does not compose. Mood-keyword tables, instrument selection rules, etc., belong in `src/yao/sketch/` and Plan Generators.
- ★ **Do not bypass CPIR.** A "spec → notes" path that skips CPIR is forbidden, even if "it would be simpler for this case."
- ★ **Do not hardcode artist names.** The schema enforces this; do not work around it.
- ★ **Do not advance the Capability Matrix optimistically.** Implementation drives status, not aspiration.
- ★ **Do not add free-text critique.** All critique flows through `Finding` objects.
- ★ **Do not silence trajectory.** Ignoring a trajectory dimension that should affect your generator violates Rule #7.

---

## 5 Design Principles (carried from v1.0)

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide

### + 1 Meta-Principle (new in v2.0)

6. **Vertical Alignment** — input expressiveness, processing depth, and evaluation resolution must advance together. **Never deepen one layer alone.**

When proposing a change, ask: *Does this widen one layer without matching the others?* If yes, either expand scope or reduce scope.

---

## Capability Matrix (Single Source of Truth)

The full matrix lives in **[PROJECT.md §5](./PROJECT.md#5-capability-matrix透明性の核-v20)**. Before any non-trivial work, read it.

When the Matrix says:

| Status | What you can assume |
|---|---|
| ✅ Implemented | Working with tests; safe to depend on |
| 🟢 Working | Core works; check edge cases |
| 🟡 Partial | Some paths work; **read the impl before depending** |
| ⚪ Designed, not started | Don't import; don't pretend it exists |
| 🔴 Identified gap | Treat as a target, not a tool |

**Hard rule**: If you write code that depends on a `⚪` or `🔴` feature, the PR is rejected.

---

## Library Restrictions (carried, with additions)

| Library | Allowed in | Purpose |
|---|---|---|
| `pretty_midi` | `ir/`, `render/` | MIDI creation/editing |
| `music21` | `ir/`, `verify/`, `arrange/` | Theory analysis, MusicXML |
| `librosa` | `verify/`, `perception/` | Audio feature analysis (Layer 4) |
| `pyloudnorm` | `verify/`, `perception/` | LUFS measurement |
| `pedalboard` ★v2.0 | `render/production/` | Audio plugin processing |
| `pydantic` | `schema/` | YAML validation |
| `structlog` | anywhere | Structured logging |
| `click` | `cli/` | CLI framework |
| `numpy/scipy` | anywhere | Numerical computation |

**Never**:
- music21 for MIDI generation (use pretty_midi)
- librosa for MIDI ops
- pretty_midi for theory analysis
- ★ pedalboard outside `render/production/`

---

## Current Phase

YaO has completed **Phase 1** (parameter-driven symbolic composition). v2.0 work is organized into **Phases α through ε**.

### Phase α (Days 1–30): Foundation of Alignment

Objective: build scaffolding so the three vertical-alignment layers can advance in lockstep.

**What is BEING BUILT in Phase α**:
- ⏳ Capability Matrix in PROJECT.md §5
- ⏳ `composition.yaml v2` schema (Pydantic, 11 sections)
- ⏳ `intent.md` and `trajectory.yaml` as first-class artifacts
- ⏳ CPIR minimal: `FormPlan` + `HarmonyPlan`
- ⏳ `MetricGoal` type system
- ⏳ `RecoverableDecision` mechanism
- ⏳ Golden MIDI test infrastructure
- ⏳ `make matrix-check`

### What EXISTS now (Phase 1 carryover, unchanged)

- Spec loading + validation (YAML → Pydantic, v1 schema) ✅
- ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
- Rule-based note generator (deterministic) ✅
- Stochastic note generator (seed + temperature) ✅
- Generator registry (legacy `@register_generator`) ✅
- Constraint system (must/must_not/prefer/avoid with scoped rules) ✅
- MIDI rendering + stems ✅
- MIDI reader (load existing MIDI back to ScoreIR) ✅
- Music linting, analysis, evaluation ✅
- Evaluation report persistence (evaluation.json) ✅
- Score diff with modified note tracking ✅
- Provenance logging (append-only, queryable) ✅
- Conductor feedback loop (basic) ✅
- Section-level regeneration ✅
- CLI (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section) ✅
- Architecture lint tool ✅
- 7 Claude Code commands, 7 Subagent definitions ✅
- 4 Skills populated (cinematic, voice-leading, piano, tension-resolution) ✅
- 226 tests ✅

### What does NOT exist yet (Phase β onward)

- MotifPlanner, DrumPattern, ArrangementPlan
- Plan-level generators (form/harmony/motif/drum/arranger)
- Adversarial Critic with 30+ rules
- Multi-candidate Conductor
- Markov / constraint_solver realizers
- Counter-melody generator
- 12 genre Skills
- Perception layer (any stage)
- Arrangement engine
- Production manifest + mix chain
- MusicXML / LilyPond / Strudel writers
- Sketch dialogue state machine
- Subagent eval harness
- DAW MCP integration
- Live mode

**If a task asks you to use a Phase β/γ/δ feature, escalate.**

---

## Two Critical Architecture Rules (v2.0)

### Rule A: The Plan-First Boundary

```
✅ Correct flow:
  CompositionSpec  →  PlanGenerator  →  CompositionPlan  →  NoteRealizer  →  ScoreIR

❌ Forbidden:
  CompositionSpec  →  NoteRealizer  →  ScoreIR
```

The forbidden path is how Phase 1 worked. v2.0 disallows it. Any PR that adds a path from spec to ScoreIR without going through CPIR is rejected.

The legacy generators (`rule_based`, `stochastic`) are being **repositioned** as Note Realizers. During the migration window (Phase α–β), they may still accept specs directly *if* they internally construct a minimal CPIR and pass through it. After Phase β, the spec→ScoreIR shortcut is removed.

### Rule B: The Critic Gate

Between CPIR completion (Step 5) and Note Realization (Step 6), the **Adversarial Critic Gate** runs. Even if you are testing locally, do not bypass it without flagging this in the PR description. The Critic Gate is what makes "fundamentally weak plan, beautifully realized" impossible — short-circuiting it defeats the v2.0 architecture.

---

## Generator Registration (v2.0)

The legacy `@register_generator("name")` decorator is **split into two**:

```python
# src/yao/generators/plan/form_planner.py
from yao.generators.plan.base import PlanGeneratorBase, register_plan_generator

@register_plan_generator("rule_based_form")
class RuleBasedFormPlanner(PlanGeneratorBase):
    def plan(
        self,
        spec: CompositionSpec,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> FormPlan:
        ...

# src/yao/generators/note/stochastic.py
from yao.generators.note.base import NoteRealizerBase, register_note_realizer

@register_note_realizer("stochastic")
class StochasticNoteRealizer(NoteRealizerBase):
    def realize(
        self,
        plan: CompositionPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        ...
```

Generator selection in spec:

```yaml
generation:
  plan_strategy: "rule_based"          # picks plan generators
  realize_strategy: "stochastic"       # picks note realizer
  seed: 42
  temperature: 0.5
```

---

## Trajectory Compliance (Rule #7 deep-dive)

When trajectory's `tension`, `density`, or `predictability` changes between bars, your generator's output **must change in a measurable way**:

| Generator | Must respond to ↑ tension by … |
|---|---|
| HarmonyPlanner | Adding secondary dominants, borrowed chords, suspensions |
| MotifPlanner | Higher register, more leaps, fewer rests |
| DrumPatterner | More subdivision, more syncopation, ghost notes |
| Arranger | More active layers, wider register spread |
| NoteRealizer | Higher velocity, sharper articulation |

**Test harness**: `tests/scenarios/test_trajectory_compliance.py` parameterizes over each generator with high-tension and low-tension trajectories and asserts measurable difference. Adding a new generator without a trajectory compliance test fails CI.

---

## Critique Rule Authoring (NEW in v2.0)

If your task is "make the critic detect X", here is the pattern:

```python
# src/yao/verify/critique/harmonic.py
from yao.verify.critique.base import CritiqueRule, Finding, Role, Severity

class ClicheChordProgressionDetector(CritiqueRule):
    rule_id = "harmonic.cliche_progression"
    role = Role.HARMONY

    def detect(
        self,
        plan: CompositionPlan,
        spec: CompositionSpec,
    ) -> list[Finding]:
        # n-gram based detection of common cliches
        # I-V-vi-IV, vi-IV-I-V, etc.
        ...
        return [
            Finding(
                rule_id=self.rule_id,
                severity=Severity.MAJOR,
                role=self.role,
                issue="chorus uses I-V-vi-IV without variation",
                evidence={"progression_entropy": 0.31, "target": 0.55},
                location=SongLocation(section="chorus", bars=(33, 40)),
                recommendation={
                    "harmony": "introduce V/V before final IV",
                    "structure": "consider modal interchange (bVII)",
                },
            )
        ]

# Register
CRITIQUE_RULES.register(ClicheChordProgressionDetector())
```

Required: every new rule has at least 2 unit tests (one positive, one negative) and is added to the registry.

---

## RecoverableDecision (NEW in v2.0)

The way to write a "fallback" without breaking Rule #3:

```python
from yao.verify.recoverable import RecoverableDecision

# A walking bass note falls below the instrument range
if proposed_note < instrument.range_min:
    decision = RecoverableDecision(
        code="BASS_NOTE_OUT_OF_RANGE",
        severity="warning",
        original_value=proposed_note,
        recovered_value=instrument.range_min,
        reason="Walking bass passing tone below upright bass range",
        musical_impact="Bass line jumps up an octave at this point",
        suggested_fix=[
            "narrow the walking-bass interval pool",
            "use synth_bass with wider range",
            "raise the chord root by an octave",
        ],
    )
    provenance.record_recoverable(decision)
    proposed_note = decision.recovered_value
```

This is not a fallback — it is a logged, traceable, fixable decision. Future iterations can see and act on it.

---

## Automated Failure Prevention (v2.0 expanded)

These common failure patterns are caught by tooling — not memorization:

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` / RecoverableDecision check | `make test` |
| Velocity hardcode | Linter pattern check | `make lint` |
| Missing provenance | `GeneratorBase` type contract + coverage assertion | `mypy` + `make test` |
| Layer boundary breach | AST-based import checker (now incl. Layer 3a) | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| ★ Spec → ScoreIR shortcut | Architecture lint | `make arch-lint` |
| ★ Capability Matrix drift | matrix-check tool diffs registered features | `make matrix-check` |
| ★ Trajectory ignored | Compliance scenario tests | `make test-scenario` |
| ★ Free-text critique | Type contract on `Finding` | `mypy` |
| ★ Plan vs note confusion | Layer-specific lint rules | `make arch-lint` |
| ★ Missing audio sample on render PRs | PR template check | CI |
| ★ Missing golden update on render-affecting changes | Golden test | `make test-golden` |

If you bypass any of these without explicit approval, the PR will be reverted.

---

## Performance Expectations (v2.0)

The pipeline grew. Budget grows accordingly, but with limits:

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec (v2) | <150ms | Pydantic validation |
| Build CPIR (8-bar piece) | <500ms | All 5 plan steps |
| Realize 8-bar piece from CPIR | <500ms | Note realizer |
| End-to-end 64-bar generation | <8s | Spec → CPIR → ScoreIR → MIDI |
| Multi-candidate (5×) 64-bar | <30s | Run 5 in parallel where possible |
| Critic Gate evaluation | <2s | All 30+ rules over CPIR |
| Audio render (64 bars) | <10s | FluidSynth |
| Mix chain processing | <5s | pedalboard |
| Run all tests | <12s | ~400 tests projected post-Phase β |
| Architecture lint | <2s | AST parsing + matrix check |
| Capability matrix check | <1s | Registry diff |

Do not introduce changes that exceed these budgets without discussion.

---

## Workflow

### When you start a session

1. Read this file
2. Skim PROJECT.md §5 (Capability Matrix) for current reality
3. Identify the layer you are touching (use the questions in `.claude/guides/architecture.md`)
4. Read the existing tests for that layer

### Before opening a PR

```bash
# 1. Local validation
make all-checks                # lint + arch-lint + matrix-check + test

# 2. If you touched generators or rendering
make test-golden               # compare against committed MIDI

# 3. If you added a Subagent or Skill
make test-subagent             # LLM-as-judge eval

# 4. If your change is audible
# Render a sample, attach to PR description
yao compose specs/templates/minimal.yaml
yao render outputs/projects/.../full.mid
```

### PR description template (enforced by CI)

```markdown
## What
<one line>

## Why
<reason / linked issue>

## How
<key implementation choices>

## Vertical Alignment
- Input: <changed/unchanged>
- Processing: <changed/unchanged>
- Evaluation: <changed/unchanged>
(If only one is changed, justify why the others don't need changes.)

## Capability Matrix
- Updated entries: <list>

## Audio impact
<sample link, or "no audio impact">

## Tests
- Added: <list>
- Golden updated: yes/no (if yes, why)
```

---

## Common Tasks Cookbook

### "Add a new genre Skill"

1. Create `.claude/skills/genres/<name>.md` with the genre template (front-matter for YAML extraction)
2. Run the front-matter extractor: `python tools/skill_yaml_sync.py`
3. Add at least one drum pattern in `drum_patterns/<name>.yaml` if it requires a distinct groove
4. Add a unit test: spec specifying this genre produces a CPIR with the genre's required features
5. Update Capability Matrix: Skills row

### "Add a new critique rule"

1. Inherit `CritiqueRule` in `src/yao/verify/critique/<role>.py`
2. Implement `detect(plan, spec) -> list[Finding]`
3. Register in `src/yao/verify/critique/registry.py`
4. Write 2+ tests (positive case detects, negative case is silent)
5. If the rule is severity=critical, add a Conductor adapter so it triggers regeneration
6. Update Capability Matrix: Critique row

### "Add a new note realizer"

1. Inherit `NoteRealizerBase` in `src/yao/generators/note/<name>.py`
2. Decorate with `@register_note_realizer("<name>")`
3. Realize from `CompositionPlan`, not from `CompositionSpec` (Rule #6)
4. Emit `RecoverableDecision` for any compromise (Rule #3)
5. Add trajectory compliance test (Rule #7)
6. Add golden MIDI fixture
7. Update Capability Matrix: Generation row

### "Add a new Plan generator step"

This is rare and architectural. Escalate first.

### "Edit composition.yaml schema"

1. Make additive changes only when possible
2. Update Pydantic model in `src/yao/schema/composition.py`
3. Update at least one template in `specs/templates/`
4. Update PROJECT.md §10.1 example
5. Add migration logic if non-additive (rare, escalate first)
6. Update Capability Matrix: Spec row

---

## Anti-Patterns (concrete examples)

### ❌ Anti-pattern 1: Spec → ScoreIR shortcut

```python
# DON'T
def generate(spec: CompositionSpec) -> ScoreIR:
    notes = []
    for section in spec.form.sections:
        notes.extend(stochastic_notes(section, spec))
    return ScoreIR(notes=notes)
```

```python
# DO
def generate(spec: CompositionSpec) -> tuple[ScoreIR, ProvenanceLog]:
    plan, prov = build_composition_plan(spec, trajectory)  # CPIR first
    score, prov = realize_notes(plan, prov)                # Then notes
    return score, prov
```

### ❌ Anti-pattern 2: Velocity hardcode

```python
# DON'T
note = Note(pitch=60, velocity=100, ...)
```

```python
# DO
velocity = velocity_from(
    dynamics=section.dynamics,
    tension=trajectory.tension_at(beat),
    humanization=stochastic_jitter(seed, ±5),
)
note = Note(pitch=60, velocity=velocity, ...)
```

### ❌ Anti-pattern 3: Silent fallback

```python
# DON'T
if note.pitch < instrument.range_min:
    note = note.replace(pitch=instrument.range_min)  # silent clamp
```

```python
# DO
if note.pitch < instrument.range_min:
    decision = RecoverableDecision(
        code="NOTE_OUT_OF_RANGE",
        severity="warning",
        original_value=note.pitch,
        recovered_value=instrument.range_min,
        reason="...",
        musical_impact="...",
        suggested_fix=[...],
    )
    provenance.record_recoverable(decision)
    note = note.replace(pitch=decision.recovered_value)
```

### ❌ Anti-pattern 4: Free-text critique

```python
# DON'T
def critique(score: ScoreIR) -> str:
    return llm.complete(f"What's wrong with this music?\n{score}")
```

```python
# DO
def critique(plan: CompositionPlan, spec: CompositionSpec) -> list[Finding]:
    findings = []
    for rule in CRITIQUE_RULES.all():
        findings.extend(rule.detect(plan, spec))
    return findings
```

### ❌ Anti-pattern 5: Trajectory ignored

```python
# DON'T
def realize_chorus(plan: CompositionPlan) -> list[Note]:
    return [Note(...) for ... ]  # nothing changes between bars
```

```python
# DO
def realize_chorus(plan: CompositionPlan) -> list[Note]:
    notes = []
    for beat in chorus_beats:
        tension = plan.trajectory.tension_at(beat)
        density = plan.trajectory.density_at(beat)
        velocity = scale_by_tension(tension)
        rhythmic_subdivision = density_to_subdivision(density)
        notes.extend(make_notes(velocity, rhythmic_subdivision, ...))
    return notes
```

### ❌ Anti-pattern 6: Capability Matrix drift

```markdown
# DON'T (in PROJECT.md §5)
| Feature X | ✅ Implemented |  <-- but no code, just a stub
```

```markdown
# DO
| Feature X | 🟡 Partial — only handles Y case, see issue #42 |
```

### ❌ Anti-pattern 7: Conductor doing music theory

```python
# DON'T (in src/yao/conductor/conductor.py)
MOOD_TO_KEY = {"happy": "C major", "sad": "C minor", "dark": "Em"}

class Conductor:
    def parse_mood(self, text):
        for mood, key in MOOD_TO_KEY.items():
            if mood in text.lower():
                return key
```

```python
# DO (in src/yao/sketch/compiler.py)
class SpecCompiler:
    def __init__(self):
        self.mood_lexicon = MoodLexicon.load()  # data, not code

    def compile(self, description: str) -> SpecDraft:
        moods = self.mood_lexicon.match(description)
        emotion = self._aggregate_moods(moods)
        ...
```

The Conductor orchestrates a pipeline. Music decisions live in the SpecCompiler, Plan Generators, and Skills.

---

## Escalation

Stop and ask the human when:

- Changing architectural boundaries or layer rules (especially Layer 3a)
- Adding new external dependencies
- Making music theory judgment calls you're unsure about
- Deleting files or rewriting git history
- Any change touching 5+ files
- ★ Any change to the Capability Matrix that downgrades a feature (`✅` → anything else)
- ★ Touching multiple subagent definitions in one PR
- ★ Modifying golden MIDI files
- ★ Changing the spec schema in a non-additive way (breaking change)

Escalation is responsibility, not weakness. **When uncertain, ask.**

---

## Recent Changes

- **2026-04-30 (v2.0)**: Major architecture revision. Introduced Layer 3a (CPIR), Capability Matrix, Vertical Alignment Principle, MetricGoal type system, RecoverableDecision, Music-as-Plan philosophy. Generator registry split into PlanGeneratorBase and NoteRealizerBase. Roadmap restructured into Phase α/β/γ/δ/ε. PROJECT.md updated to v2.0.
- **2026-04-29**: MIDI reader, section regeneration (Conductor + CLI), evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades (compose/critique/sketch/regenerate-section), 4 skills populated (cinematic, voice-leading, piano, tension-resolution), mypy fixes (140→0 errors).
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff, documentation completions.
- **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance, CLAUDE.md restructured into tiered guides.
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Claude Code commands/agents.
- **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md.

---

## Closing thought

You are building the environment in which a Conductor (the human) leads an Orchestra (the Subagents) to make music together. **Build the environment well, and the music will follow.** Take shortcuts in the environment, and every piece composed in YaO will inherit those shortcuts.

When a rule in this file feels inconvenient, remember: it exists because a previous shortcut produced unexplainable music. The rules are scar tissue. They protect the project's integrity.

> *Plan before notes. Explain every decision. Advance the layers together.*

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| [Architecture](./.claude/guides/architecture.md) | Working across layers, adding modules — note Layer 3a additions |
| [Coding Conventions](./.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](./.claude/guides/music-engineering.md) | Generating/modifying notes |
| [Plan Engineering](./.claude/guides/plan-engineering.md) ★v2.0 | Writing plan generators or critique rules |
| [Testing](./.claude/guides/testing.md) | Writing or running tests (incl. golden, scenario, subagent) |
| [Workflow](./.claude/guides/workflow.md) | Planning a change |
| [Matrix Discipline](./.claude/guides/matrix-discipline.md) ★v2.0 | Updating PROJECT.md §5 |
| [Critique Rule Authoring](./.claude/guides/critique-rules.md) ★v2.0 | Adding to the 30+ rule registry |

Full design documentation: [PROJECT.md](./PROJECT.md)

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 2.0*
*Supersedes: CLAUDE.md v1.0 (2026-04-28)*
*Last revised: 2026-04-30*
