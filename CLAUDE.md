# CLAUDE.md — YaO Core Rules (v2.0)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: **CLAUDE.md > PROJECT.md > VISION.md > FEATURE_STATUS.md > other docs**.*
> *PROJECT.md describes **what** YaO is. This file describes **how** to build it.*

---

## 0. Document Status

This is **CLAUDE.md v2.0**, evolved from v1.1 to align with **PROJECT.md v2.0**. v2.0 introduces:

- An 8-layer architecture (Layer 3.5: MPIR added)
- A 9-step pipeline (Conversation Director and Listening Simulation added)
- 12 specification files (was 8)
- 8 Subagents (Conversation Director added)
- Acoustic evaluation parallel to symbolic evaluation
- 30+ critique rules (was 15)
- Eight structural improvements: Surprise, Acoustic Truth, Diversity, Ensemble Groove, Conversation, Fine-Grained Feedback, Multilingual/Multicultural, Arrangement

Sections marked **[v2.0]** are new or substantially revised compared to v1.1.

---

## 1. Quick Reference

```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-acoustic     # [v2.0] Audio regression tests
make test-subagent     # [v2.0] Subagent behavioral tests
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary check (8 layers in v2.0)
make feature-status    # Verify FEATURE_STATUS.md matches code
make sync-skills       # Sync genre Skill YAML from Markdown front-matter
make skill-quality     # [v2.0] Check Skill quality
make all-checks        # lint + arch-lint + feature-status + test + golden
make format            # Auto-format
```

### Key Directories **[v2.0 expanded]**

```
src/yao/constants/        → Hardcoded values (ranges, scales, MIDI mappings, forms)
src/yao/schema/           → Pydantic models for all 12 YAML specs
src/yao/ir/score/         → Score IR (Note, Part, Section, Voicing)
src/yao/ir/plan/          → MPIR (SongFormPlan, HarmonyPlan, MotifPlan, etc.)
src/yao/ir/tension_arc.py → [v2.0] TensionArc IR
src/yao/ir/hook.py        → [v2.0] Hook IR (Motif specialization)
src/yao/ir/conversation.py → [v2.0] ConversationPlan IR
src/yao/ir/groove.py      → [v2.0] GrooveProfile IR
src/yao/generators/plan/  → Plan-level generators
src/yao/generators/note/  → Note Realizers
src/yao/generators/groove_applicator.py    → [v2.0]
src/yao/generators/reactive_fills.py       → [v2.0]
src/yao/generators/frequency_clearance.py  → [v2.0]
src/yao/render/           → MIDI, audio, MusicXML, LilyPond
src/yao/perception/       → [v2.0 newly populated] Layer 4
src/yao/arrange/          → [v2.0] Arrangement engine
src/yao/verify/           → Lint, evaluation, critique, diff, constraints
src/yao/verify/critique/  → 30+ critique rules across 7 roles
src/yao/verify/acoustic/  → [v2.0] Acoustic-side verification
src/yao/reflect/          → Provenance, RecoverableDecision
src/yao/sketch/           → NL → spec compiler (multilingual)
src/yao/feedback/         → [v2.0] Pin processing, NL feedback
src/yao/runtime/          → [v2.0] ProjectRuntime
src/yao/errors.py         → All custom exceptions
```

### Key Types **[v2.0 expanded]**

```
Note                 → src/yao/ir/score/note.py
ScoreIR              → src/yao/ir/score/score_ir.py
MusicalPlan          → src/yao/ir/plan/musical_plan.py    (the MPIR root)
SongFormPlan         → src/yao/ir/plan/form.py
HarmonyPlan          → src/yao/ir/plan/harmony.py
MotifPlan            → src/yao/ir/plan/motif.py
TensionArc           → src/yao/ir/tension_arc.py          [v2.0]
Hook                 → src/yao/ir/hook.py                 [v2.0]
ConversationPlan     → src/yao/ir/conversation.py         [v2.0]
GrooveProfile        → src/yao/ir/groove.py               [v2.0]
PerceptualReport     → src/yao/perception/audio_features.py [v2.0]
StyleVector          → src/yao/perception/reference_matcher.py [v2.0]
SurpriseAnalysis     → src/yao/perception/surprise.py     [v2.0]
Pin                  → src/yao/feedback/pin.py            [v2.0]
CompositionSpec      → src/yao/schema/composition.py
ProvenanceLog        → src/yao/reflect/provenance.py
GeneratorBase        → src/yao/generators/base.py
PlanGeneratorBase    → src/yao/generators/plan/base.py
NoteRealizerBase     → src/yao/generators/note/base.py
CritiqueRule         → src/yao/verify/critique/base.py
Finding              → src/yao/verify/critique/finding.py
```

---

## 2. Your Role

You are a **co-developer of YaO**, not YaO itself.

The distinction matters:

- **YaO** is "the agentic music production environment".
- **The Subagents** (Composer, Critic, Conversation Director, Producer, etc.) are how YaO behaves at runtime.
- **You** build the infrastructure those Subagents use.

When you write code, you are implementing functions that **a future Composer Subagent will call**, not composing music yourself. Your code enables reproducible, auditable, iterable music creation.

### What v2.0 means for your role **[v2.0]**

The eight structural improvements are not "8 separate features"; they are **cross-cutting concerns** that should be considered in every change. When you touch any module, ask:

1. Does this change preserve **surprise** (controlled unpredictability)?
2. Does this change keep **symbolic and acoustic evaluation in alignment**?
3. Does this change preserve **diversity sources** (does it accidentally narrow the output space)?
4. Does this change respect **ensemble groove** (cross-instrument microtiming)?
5. Does this change respect **ensemble conversation** (inter-instrument dialogue)?
6. Does this change preserve **fine-grained feedback** (can users still pin/section/spec)?
7. Does this change preserve **multilingual/multicultural support**?
8. Does this change cleanly compose with the **arrangement engine**?

If a change harms any of these without explicit justification, escalate.

---

## 3. Five Non-Negotiable Rules **[v2.0 unchanged]**

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`. The architecture lint enforces this; do not bypass it.
2. **Every generation function returns `(IR, ProvenanceLog)`** — for plan generators it returns `(MusicalPlan, ProvenanceLog)`; for note realizers it returns `(ScoreIR, ProvenanceLog)`. There is no third option.
3. **No silent fallbacks** — constraint violations must be explicit errors. Use `RecoverableDecision` if a documented graceful degradation is required.
4. **No hardcoded musical values** — use `src/yao/constants/` for instrument ranges, MIDI numbers, scales, chord types, dynamics tables, and form definitions.
5. **No public function without type hints and docstring** — `mypy --strict` must pass; the docstring includes purpose, args, returns, raises, and an example where useful.

---

## 4. Six Additional v2.0 Non-Negotiable Rules **[v2.0]**

These six rules are specific to the v2.0 architecture. Violating them will cause the system's eight improvements to silently degrade.

### Rule 6: Plan-First, Then Notes

For any new generator, the entry point must produce or consume a `MusicalPlan`, not raw `ScoreIR`. The "old" pattern of `Spec → ScoreIR` directly is **forbidden** in new code. The valid patterns are:

- Plan generator: `Spec → MusicalPlan` (subclasses of `PlanGeneratorBase`)
- Note realizer: `MusicalPlan → ScoreIR` (subclasses of `NoteRealizerBase`)

Existing rule-based and stochastic generators are being **repositioned** as Note Realizers. When extending them, ensure they accept `MusicalPlan`, not `CompositionSpec`.

### Rule 7: Symbolic Evaluation Has An Acoustic Counterpart

Whenever you add a symbolic metric to the Evaluator, you must also add (or document an issue for) a corresponding acoustic verification when audio is rendered. The two must not drift apart. If you genuinely cannot define an acoustic counterpart, leave a TODO with rationale and an Issue link.

### Rule 8: Groove Is Ensemble-Wide By Default

When you add a generator that produces notes, those notes must pass through the `GrooveApplicator` before reaching the MIDI writer. The `apply_groove(score_ir, groove_profile)` step is **mandatory** unless the spec explicitly sets `groove.apply_to_all_instruments: false`. Hardcoding "drums get groove, others don't" is a violation.

### Rule 9: Conversation Plan Is Not Optional

When you add a generator that places notes in time, you must respect the `ConversationPlan` if one exists in the `MusicalPlan`. Specifically: if `voice_focus.<section>.primary` is set, the primary instrument's part must dominate the frequency space in that section, and accompaniment parts must yield via the Frequency Clearance generator. Ignoring `ConversationPlan` is silently breaking the ensemble.

### Rule 10: Pins Override Spec In Their Scope

When you implement code that consumes specs, pins (`specs/projects/<name>/pins.yaml`) must be loaded and applied as **localized constraints** within the regions they target. Pins do not modify the spec; they overlay constraints on regeneration. Any code that loads `composition.yaml` without checking for `pins.yaml` is incomplete.

### Rule 11: The Eight Improvements Are Tested Together

Whenever you introduce or extend a feature touching one of the eight improvements (Surprise, Acoustic, Diversity, Groove, Conversation, Feedback, Multilingual, Arrangement), the change must include **at least one test** in the corresponding directory:

| Improvement | Test directory |
|---|---|
| Surprise | `tests/unit/perception/test_surprise.py` + scenario test |
| Acoustic Truth | `tests/unit/perception/test_audio_features.py` + audio regression |
| Diversity | `tests/scenarios/test_diversity_sources.py` |
| Ensemble Groove | `tests/unit/generators/test_groove_applicator.py` |
| Conversation | `tests/unit/ir/test_conversation.py` + scenario test |
| Fine-Grained Feedback | `tests/unit/feedback/test_pin.py` |
| Multilingual/Multicultural | `tests/unit/sketch/test_multilingual.py` |
| Arrangement | `tests/unit/arrange/test_*.py` |

A change that lands without a corresponding test in the relevant directory is rejected at PR review.

---

## 5. MUSTs **[v2.0 expanded]**

- Read existing code before writing new code (use `view` on the relevant directory)
- Write tests before or alongside implementation (TDD where feasible)
- Keep YAML schemas and Pydantic models in sync; update both in the same PR
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Derive velocity from dynamics curves and `phrase_dynamics` shapes (never hardcode)
- Register generators via `@register_generator("name")`
- **[v2.0]** Register critique rules via `@register_critique_rule("name")`
- **[v2.0]** Register groove profiles via `@register_groove_profile("name")` (or load from `grooves/*.yaml`)
- **[v2.0]** Register form definitions via `@register_form("name")` (or load from `forms/*.yaml`)
- **[v2.0]** When extending the Critique Registry, the new rule must emit a typed `Finding` with severity, evidence, location, and recommendation
- **[v2.0]** Acoustic features must be extracted via `pyloudnorm` for loudness and `librosa.feature.*` for spectral; do not roll your own
- **[v2.0]** When implementing arrangement operations, they must subclass `ArrangementOperation` and produce a `MusicalPlan` (not directly notes)
- **[v2.0]** When introducing a new Pin schema field, update `pins.yaml` Pydantic model, the CLI, and the regeneration logic in the same PR
- **[v2.0]** Update `FEATURE_STATUS.md` whenever a feature crosses a status boundary (⚪ → 🟡 → 🟢 → ✅), and run `make feature-status`

## 6. MUST NOTs **[v2.0 expanded]**

- Import `pretty_midi`/`music21`/`librosa`/`pyloudnorm` outside designated layers (see architecture.md)
- Create functions with vague names (`make_it_sound_good`, `improve_quality`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError`)
- Leave `TODO`/`FIXME` uncommitted (file an Issue and reference it instead)
- **[v2.0]** Generate notes that bypass `GrooveApplicator`
- **[v2.0]** Generate parts that ignore `ConversationPlan` when one exists
- **[v2.0]** Add a symbolic metric without an acoustic counterpart (or a documented exception)
- **[v2.0]** Compare references on raw audio similarity, melody, hook rhythm, or chord progression — only `do_not_copy`-allowlisted abstract features
- **[v2.0]** Hardcode "drums use groove, others don't" — `apply_to_all_instruments` is determined by the spec
- **[v2.0]** Hardcode artist names (living or recent) in any Skill, prompt, parameter, or test
- **[v2.0]** Mutate `provenance.json` retroactively — it is append-only
- **[v2.0]** Mutate a `MusicalPlan` after it has been frozen and passed through the Critic Gate
- **[v2.0]** Modify pins after they have been written; pins are immutable user input
- **[v2.0]** Skip `Listening Simulation` (Step 7.5) for use-case-targeted pieces
- **[v2.0]** Add Subagents without updating `.claude/agents/`, `PROJECT.md` Section 5, and the Subagent behavioral test directory

---

## 7. Five + Two Design Principles **[v2.0]**

The original five principles remain. v2.0 adds two more (numbered 6 and 7 in PROJECT.md).

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform; humans decide
6. **[v2.0] Vertical alignment** — input expressiveness, processing depth, evaluation resolution advance together
7. **[v2.0] Acoustic truth complements symbolic truth** — symbolic metrics necessary, never sufficient

When in doubt about an architectural decision, walk through these seven principles in order. The first principle that gives a clear answer wins.

---

## 8. Current Phase and Status **[v2.0]**

**Active phase: γ — Differentiation: Quality and Acoustic Truth**

The structural improvements are sequenced as follows:

### What EXISTS (Phase α + β complete):

- ✅ 7-layer architecture + AST architecture lint
- ✅ Spec loading + validation (Pydantic v1 + v2)
- ✅ ScoreIR (Note, Part, Section, Motif, Voicing, Harmony)
- ✅ MPIR partial (SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan, DrumPattern, ArrangementPlan)
- ✅ Rule-based generator (deterministic) + stochastic generator (seeded)
- ✅ Generator registry
- ✅ Constraint system (must / must_not / prefer / avoid with scoping)
- ✅ MIDI rendering + per-instrument stems
- ✅ MIDI reader (round-trip)
- ✅ Music linting, analysis, evaluation
- ✅ Evaluation report persistence (`evaluation.json`)
- ✅ Score diff with modified note tracking
- ✅ Provenance logging (append-only, queryable, persisted)
- ✅ Conductor feedback loop (generate → evaluate → adapt → regenerate)
- ✅ Section-level regeneration
- ✅ Multi-candidate generation (5 plans → critic-rank → producer-pick)
- ✅ CLI: compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section, preview, watch
- ✅ 7 Claude Code commands + 7 Subagent definitions
- ✅ 8 genre Skills (paired Markdown + YAML)
- ✅ 4 domain Skills (voice-leading, piano, tension-resolution, …)
- ✅ MetricGoal type system (7 goal types)
- ✅ RecoverableDecision logging
- ✅ 15 critique rules across 6 roles
- ✅ Pre-commit hooks + GitHub Actions CI
- ✅ Golden MIDI regression
- ✅ ~643 tests

### What is being built in Phase γ **[in progress]**:

- 🟡 **Perception Layer Stage 1** (audio features extraction, librosa + pyloudnorm)
- 🟡 **Perception Layer Stage 2** (use-case targeted evaluation: BGM/Game/Ad/Study/Cinematic)
- 🟡 **Surprise Score** computation + critique rules
- 🟡 **TensionArc IR** + `tension_arcs.yaml` schema + Plan Generator integration
- 🟡 **Hook IR** + `hooks.yaml` schema + deployment-aware Composer
- 🟡 **Phrase-Level Dynamics** schema + Note Realizer support
- 🟡 **GrooveProfile IR** + 12 genre groove YAMLs + `GrooveApplicator`
- 🟡 **Conversation Director Subagent** + `ConversationPlan` IR + `conversation.yaml`
- 🟡 **Reactive Fills + Frequency Clearance** generators
- 🟡 **Multilingual SpecCompiler** (Japanese first; framework for additional languages)
- 🟡 **Extended Scales** (Japanese in/yo/ritsu/min'yō, Hijaz, Kurd, Bhairav)
- 🟡 **Form Library** (20+ song forms) + `forms/*.yaml`
- 🟡 **Critique Rules** expanded to 30+ across 7 roles (acoustic role added)

### What does NOT exist yet:

- ⚪ **Arrangement Engine** (Phase δ): SourcePlan extractor, operations, preservation contract, diff report
- ⚪ **Three-tier feedback**: `pin` and `feedback` commands (Phase δ)
- ⚪ **MusicXML / LilyPond** writers (Phase δ)
- ⚪ **Reaper MCP** integration (Phase δ)
- ⚪ **Mix chain** (pedalboard EQ/comp/reverb) (Phase ε)
- ⚪ **Strudel emitter** (Phase ε)
- ⚪ **Reflection Layer (Layer 7)** (Phase ζ)
- ⚪ **Live improvisation mode** (Phase ζ)

The single source of truth for status is `FEATURE_STATUS.md`. **Always read it before claiming a feature is done.**

---

## 9. Architecture **[v2.0]**

YaO follows a strict 8-layer architecture (was 7 in v1.1). Each layer can only depend on layers below. Enforced by `make arch-lint` (AST-based).

```
Conductor          — Orchestrates the full generate-evaluate-adapt pipeline
  ↑
Layer 7: Reflect   — Provenance, learning (Phase ζ)
Layer 6: Verify    — Symbolic + acoustic evaluation, critique (30+ rules), constraints
Layer 5: Render    — MIDI, audio, MusicXML, LilyPond, Strudel, iteration mgmt
Layer 4: Percept   — Audio features, use-case targets, surprise, listening simulation
Layer 3.5: MPIR    — Plan IR (form, harmony, motif, drum, arrangement, conversation, etc.)
Layer 3: ScoreIR   — Concrete notes
Layer 2: Generate  — Plan generators + Note realizers + groove applicator
Layer 1: Schema    — Pydantic models for all 12 YAML specs
Layer 0: Constants — Instruments, scales, chords, dynamics, forms, MIDI maps
```

### Pipeline (9 steps in v2.0)

```
Step 1: Form Planner          → SongFormPlan + TensionArcs
Step 2: Harmony Planner       → HarmonyPlan
Step 3: Motif Developer       → MotifPlan + PhrasePlan + HookPlan
Step 4: Drum Patterner        → DrumPattern + GrooveProfile
Step 5: Arranger              → ArrangementPlan
Step 5.5: Conversation Dir.   → ConversationPlan         [v2.0]
═══ MUSICAL PLAN COMPLETE — Critic Gate ═══
Step 6: Note Realizer         → ScoreIR (groove applied)
Step 7: Renderer              → MIDI / Audio / Score
Step 7.5: Listening Sim.      → PerceptualReport         [v2.0]
[Optional] Loopback to earlier steps
```

### Layer Discrimination Questions

When adding a new module, decide its layer using these questions, in order:

- Does it merely **define** values? → **Layer 0**
- Is it a **Pydantic model** for a YAML spec? → **Layer 1**
- Does it **emit notes**? → **Layer 2**
- Is it the **Score IR** structure (notes, parts, sections)? → **Layer 3**
- Is it the **Plan IR** structure (the why)? → **Layer 3.5**
- Does it **extract acoustic features** or **simulate listening**? → **Layer 4**
- Does it **render output** (MIDI, audio, score)? → **Layer 5**
- Does it **evaluate or critique** existing output? → **Layer 6**
- Does it **learn from history** across runs? → **Layer 7**

If two layers seem possible, write a 1-page design doc in `docs/design/` and escalate. Do not guess.

---

## 10. Code Conventions **[v2.0 expanded]**

### Python and Types

- Python 3.11+, `from __future__ import annotations`
- All public functions: type hints + Google-style docstring
- `mypy --strict` must pass
- ruff for linting, line length 99 (extended to 120 for docstrings only)

### Naming

- Modules: `snake_case`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Music acronyms (MIDI, BPM, IR, MPIR) may be uppercase: `load_midi_file`, `MpirSnapshot`

### Domain Vocabulary **[v2.0 expanded]**

- "Piece" or "composition" — never "track" (which is ambiguous)
- "Section" (intro, verse, chorus, etc.) — capitalized when referring to the IR class
- "Motif" — short, characteristic, generative; "Phrase" — bar-scale unit; "Hook" — memorable centerpiece
- "Tick" (MIDI) ≠ "beat" (musical) ≠ "second" (real time) — keep them distinct, convert via `yao.ir.timing`
- "Voicing" (chord arrangement) ≠ "orchestration" (instrument assignment) — do not conflate
- **[v2.0]** "Plan" = MPIR-level (the why); "Score" = ScoreIR-level (the what)
- **[v2.0]** "Groove" = ensemble-wide microtiming/velocity profile; not just drums
- **[v2.0]** "Conversation" = inter-instrument dialogue; not human-AI dialogue (which is "feedback")

### Pydantic vs frozen dataclass

- **Pydantic** for external input (YAML specs, JSON imports)
- **`frozen=True` dataclass** for internal IR (Note, ScoreIR, MusicalPlan, all Plan IRs)
- IR objects must be **hashable** to allow caching and diffing

### Errors

- Custom exceptions only — no bare `ValueError` (`YaOError` is the base)
- `RangeViolationError` for instrument range issues
- `ConstraintViolation` for spec constraint failures
- **[v2.0]** `PlanIncoherenceError` for MPIR consistency violations (e.g., HarmonyPlan claims a chord at bar 5 but SongFormPlan ends at bar 4)
- **[v2.0]** `GrooveConflictError` when two ensemble-wide groove profiles conflict
- **[v2.0]** `ReferenceCopyError` when a `references.yaml` entry tries to compare on a forbidden axis

Use `RecoverableDecision` for **documented** graceful degradations. Every recoverable decision must be registered in the central registry (currently 9+ entries).

---

## 11. Music Engineering Conventions **[v2.0 expanded]**

### Pitch and Notes

- MIDI ↔ note name conversion: `yao.ir.notation` only
- Scientific pitch notation (C4 = MIDI 60)
- Avoid ambiguous wording ("middle C", "central do")
- **[v2.0]** Microtonal pitch (when `MicrotonalNote` is used) is in cents; `pitch_cents = base_pitch * 100 + cents_offset`

### Time

- Tick resolution: `pretty_midi` default (220 PPQ) unless overridden
- Tick/beat/second conversions: `yao.ir.timing` only
- Time signature changes occur at section boundaries; mid-bar changes are forbidden
- **[v2.0]** Microtiming offsets are in milliseconds and are recorded **after** beat-aligned positions are computed; never bake them in at the beat-position level

### Range and Voicing

- Per-instrument ranges: `src/yao/constants/instruments.py`
- Range violations raise `RangeViolationError` with a recovery suggestion (no silent clamping)
- Voicing decisions: `yao.ir.score.voicing`; parallel-fifths/octaves checks: `yao.verify.voice_leading`

### Harmony

- Chord function notation: Roman numerals (I, ii, V7/V, bVII)
- Concrete chords (C, Dm7) are derived via `yao.ir.harmony.realize()`; do not mix function and concrete in the same expression
- **[v2.0]** Tension levels are normalized to [0, 1] across genres; `tension_level=0.7` means the same urgency in jazz and cinematic contexts

### Rhythm

- Swing ratio: 0.5 = straight, 0.667 = triplet swing
- Humanize: timing (ms) and velocity (0–127) specified independently
- Velocity hardcoding is forbidden; derive from `dynamics` × `phrase_dynamics_shape` × `humanize`
- **[v2.0]** GrooveProfile microtiming is in ms per 16th-note position (0–15); positions outside this resolution must be derived, not hardcoded

### Acoustic Measurement **[v2.0]**

- LUFS measurement: `pyloudnorm` (do not approximate via `librosa.feature.rms`)
- BPM detection: result must include a confidence score
- Spectral features: `librosa.feature.*` only; document the exact function used in the docstring
- Onset density: `librosa.onset.onset_detect` per section, not globally

### Conversation **[v2.0]**

- `voice_focus.<section>.primary` instrument's range and dynamics dominate that section
- Accompaniment instruments must yield via Frequency Clearance
- Reactive fills only fire when silence after a phrase end is ≥ `minimum_silence_beats` (default 1.0)

---

## 12. Test Conventions **[v2.0 expanded]**

### Layout

- Unit tests: `tests/unit/` (mirrored to `src/yao/` structure)
- Integration: `tests/integration/`
- Music constraints: `tests/music_constraints/`
- Scenarios: `tests/scenarios/`
- Golden MIDI: `tests/golden/` (bit-exact regression)
- **[v2.0] Audio regression**: `tests/audio_regression/`
- **[v2.0] Subagent behavioral**: `tests/subagents/`

### Required Tests by Change Type

| Change | Required tests |
|---|---|
| Generator added | "Spec-conformance" + "Determinism (rule_based) or seed-stability (stochastic)" |
| IR changed | Round-trip (IR → MIDI → IR equivalence) |
| Evaluator/Critique rule added | Known-good and known-bad samples; severity correctness |
| Bug fix | Failing test reproducing the bug, then the fix |
| **[v2.0] Plan generator added** | Plan completeness (all required MPIR fields filled) + plan validity (cross-references resolve) |
| **[v2.0] Acoustic feature added** | Synthetic-input verification (known LUFS test signal, etc.) |
| **[v2.0] Subagent behavior change** | Behavioral test in `tests/subagents/` checking role boundaries |
| **[v2.0] Arrangement operation added** | Source preservation test + transformation magnitude test |
| **[v2.0] Pin handling added** | Localization test (pin scope is respected, surrounding region preserved) |

### Music-Specific Test Helpers

```python
from tests.helpers import (
    assert_in_range,
    assert_no_parallel_fifths,
    assert_trajectory_match,
    assert_groove_applied,           # [v2.0]
    assert_voice_focus_dominant,     # [v2.0]
    assert_pin_scope_preserved,      # [v2.0]
    assert_acoustic_close,           # [v2.0]
)
```

### Audio Regression **[v2.0]**

Audio regression tests render representative pieces, extract acoustic features, and compare to a stored baseline:

```python
@pytest.mark.audio_regression
@pytest.mark.parametrize("spec_path", REPRESENTATIVE_SPECS)
def test_audio_regression(spec_path: Path):
    score_ir = compose(spec_path)
    audio = render_to_wav(score_ir)
    features = extract_perceptual_features(audio)
    baseline = load_baseline(spec_path)
    drift = compute_drift(features, baseline)
    assert drift < ACCEPTABLE_DRIFT
```

These run weekly in CI, not on every PR (too slow). PRs that intentionally change acoustic features must regenerate baselines via `tools/regenerate_audio_baselines.py` and explain the change.

### Golden MIDI Discipline

- Golden tests are bit-exact MIDI regression
- Updating goldens is **not automatic**; the PR must include the updated baselines and a written justification
- "Cleaning up" tests by deleting goldens is forbidden

### Subagent Behavioral Tests **[v2.0]**

Subagent behavioral tests verify that each Subagent stays within its role:

```python
@pytest.mark.subagent
def test_composer_does_not_change_orchestration():
    """Composer Subagent may change melody/motif/phrase, but never instrumentation."""
    initial_plan = create_initial_plan()
    composer_output = invoke_composer_subagent(initial_plan)
    assert plans_differ_in(initial_plan, composer_output, allowed=["motif", "phrase", "hook"])
    assert plans_equal_in(initial_plan, composer_output, fields=["arrangement.layers"])
```

---

## 13. Schema and Spec Conventions **[v2.0]**

YaO has 12 spec files. Their conventions:

| File | Pydantic class | Mutable by user? | Generated? |
|---|---|---|---|
| `intent.md` | `IntentSpec` | Yes | No |
| `composition.yaml` | `CompositionSpec` (v1) or `CompositionSpecV2` | Yes | No |
| `trajectory.yaml` | `TrajectorySpec` | Yes | No |
| `tension_arcs.yaml` **[v2.0]** | `TensionArcsSpec` | Yes | No |
| `hooks.yaml` **[v2.0]** | `HooksSpec` | Yes | No |
| `conversation.yaml` **[v2.0]** | `ConversationSpec` | Yes | No |
| `groove.yaml` **[v2.0]** | `GrooveSpec` | Yes | No |
| `references.yaml` | `ReferencesSpec` | Yes | No |
| `negative-space.yaml` | `NegativeSpaceSpec` | Yes | No |
| `arrangement.yaml` | `ArrangementSpec` | Yes (arrangement mode) | No |
| `production.yaml` | `ProductionSpec` | Yes | No |
| `pins.yaml` **[v2.0]** | `PinsSpec` | **No (CLI only)** | Yes (via `yao pin`) |
| `provenance.json` | `ProvenanceLog` | **No** | Yes (system) |

### Schema Evolution Rules **[v2.0]**

- Adding a new optional field: minor version bump
- Adding a new required field: major version bump (with migration tool)
- Renaming a field: forbidden in minor versions; must be a breaking change with a deprecation cycle of at least 1 minor version
- All Pydantic models must include a `schema_version: str` field

### Cross-Spec Validation **[v2.0]**

Specs reference each other:

- `composition.yaml` defines sections; `tension_arcs.yaml` references those section names; `hooks.yaml` references motif IDs from generated `MotifPlan`; `conversation.yaml` references instruments.

Cross-spec consistency is checked by `yao validate <project-dir>`. This must run cleanly before generation. The validator is in `src/yao/schema/validator.py`.

---

## 14. Subagent Conventions **[v2.0]**

Each Subagent has:

1. A definition file `.claude/agents/<name>.md` with role, inputs, outputs, forbidden actions, evaluation criteria
2. A behavioral test in `tests/subagents/test_<name>.py`
3. A clear hand-off contract to the Producer

### Producer Is Special

Only the Producer may override another Subagent's output. This rule prevents agent-agent infinite loops and is enforced architecturally.

### Adversarial Critic Is Adversarial **[v2.0]**

The Adversarial Critic **must not praise**. Its sole purpose is finding weaknesses. If you ever find yourself adding a "good aspects" section to its output, you have misunderstood its role.

### Conversation Director Is New **[v2.0]**

The Conversation Director Subagent is a v2.0 addition. When extending Subagent infrastructure, ensure:

- It receives the full ArrangementPlan and a draft ScoreIR
- It produces a ConversationPlan
- Its output is consumed by the Note Realizer in Step 6
- Its findings are visible in `provenance.json`

### Subagent → Pipeline Mapping **[v2.0]**

| Pipeline Step | Owning Subagent |
|---|---|
| Step 1 Form Planner | Producer (form is meta) |
| Step 2 Harmony Planner | Harmony Theorist |
| Step 3 Motif Developer | Composer |
| Step 4 Drum Patterner | Rhythm Architect |
| Step 5 Arranger | Orchestrator |
| **Step 5.5 Conversation Director** | **Conversation Director** |
| Critic Gate | Adversarial Critic |
| Step 6 Note Realizer | Composer (low-level) |
| Step 7 Renderer | Mix Engineer |

---

## 15. Skill Conventions **[v2.0 expanded]**

### Skill Categories

```
.claude/skills/
├── genres/      → Per-genre knowledge (12+ targets in v2.0)
├── theory/      → Music theory (voice leading, reharmonization, etc.)
├── instruments/ → Per-instrument idioms
├── psychology/  → Empirical perception mappings
├── grooves/     → [v2.0] Genre-specific groove profiles
├── forms/       → [v2.0] Song form library
└── cultures/    → [v2.0] Non-Western music traditions
```

### Skill Quality Requirements

Every skill file (Markdown) must include:

1. YAML front-matter with structured fields (`name`, `category`, `examples_count`, etc.)
2. At least 3 concrete examples
3. At least 1 counter-example (where the rule does NOT apply or is intentionally violated)
4. Genre dependencies marked
5. Related skills cross-referenced
6. Source citations (textbook, paper, or trusted web reference)

`make skill-quality` checks these and fails if a skill is below standard.

### Markdown ↔ YAML Sync

Genre Skills exist as paired Markdown (for prompts) and YAML (for programmatic use). They must never desync. The YAML is generated from the Markdown front-matter via `make sync-skills`.

### Forbidden in Skills **[v2.0]**

- Names of living or recently active artists
- Specific copyrighted song titles as "examples to mimic"
- Direct quotes from copyrighted works longer than fair use permits
- Cultural appropriation framing — non-Western traditions must be presented with respect and source citations

---

## 16. Hooks Discipline **[v2.0 expanded]**

Hooks are scripts whose execution is **guaranteed**, not instructions to Claude Code. The current hooks:

| Hook | Trigger | Action | Status |
|---|---|---|---|
| `pre-commit-lint` | git commit | ruff + mypy + YAML schema | ✅ |
| `pre-commit-arch` | git commit | Layer boundary check | ✅ |
| `post-generate-render` | After `compose`/`arrange` | Auto-render audio + score | 🟡 |
| `post-generate-critique` | After generate | Run rule-based critique → `critique.json` | ✅ |
| `post-generate-perceptual` **[v2.0]** | After audio render | Extract acoustic features → `perceptual.json` | ⚪ |
| `update-provenance` | Any plan/score change | Append to provenance log | ✅ |
| `spec-changed-show-diff` | Edit spec | Show MPIR-level diff | ⚪ |
| `pin-changed-mark-stale` **[v2.0]** | New pin added | Mark current iteration stale | ⚪ |

When implementing a new hook, use bash if it's a system-level guarantee, or Python if it requires YaO domain logic. Place in `.claude/hooks/` (system) or `tools/` (domain).

---

## 17. Common Failure Patterns and Their Catchers **[v2.0 expanded]**

These failure patterns are common; tooling catches them automatically. **Never rely on memorization.**

| Pattern | Catcher | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | Code review pattern + ruff custom rule | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| **[v2.0] Symbolic-acoustic divergence** | Acoustic regression + critique rule | `make test-acoustic` (weekly) |
| **[v2.0] Mode collapse** | Diversity scenario test | `make test` |
| **[v2.0] Groove not applied** | Generator output check (`assert_groove_applied`) | `make test` |
| **[v2.0] Conversation ignored** | Voice focus dominance test | `make test` |
| **[v2.0] Pin scope not respected** | Pin localization test | `make test` |
| **[v2.0] Artist name leaked into Skill** | grep + skill-quality check | `make skill-quality` |
| **[v2.0] Reference comparison on forbidden axis** | Pydantic `do_not_copy` allowlist | runtime |
| **[v2.0] Subagent role overreach** | Subagent behavioral test | `make test-subagent` |
| **[v2.0] FEATURE_STATUS.md drift** | feature-status check | `make feature-status` |

---

## 18. Performance Expectations **[v2.0 revised]**

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Generate 8-bar piece | <1s | Both generators |
| Generate 64-bar piece | <5s | Stochastic may vary |
| Generate 5 candidates **[v2.0]** | <15s | Parallel pipelines |
| Write MIDI file | <200ms | pretty_midi |
| Render audio (90s) **[v2.0]** | <10s | FluidSynth |
| Extract acoustic features **[v2.0]** | <3s | librosa |
| Run full lint | <500ms | All lint rules |
| Run all unit tests | <30s | ~1500 tests projected at v2.0 maturity |
| Architecture lint | <1s | AST parsing |
| Audio regression (10 pieces) **[v2.0]** | <5min | Weekly CI |

Performance is enforced. Do not introduce changes that exceed these budgets without discussion. The `performance_regression` test in CI is now mandatory.

---

## 19. Workflow for New Changes **[v2.0]**

For any change, follow this sequence:

### Step 1: Classify the change

- Bug fix? → Failing test first.
- New feature? → Locate the layer, locate the Subagent owner, design the IR change first.
- Refactor? → No behavior change must be possible (regression tests catch this).
- Architecture? → Design doc in `docs/design/` first; escalate.

### Step 2: Read existing code

- `view` the directory you'll be touching
- Read related tests
- Read the corresponding Subagent definition in `.claude/agents/`

### Step 3: Read relevant guides

| When you're working on... | Read first |
|---|---|
| Note generation logic | `.claude/guides/music-engineering.md` |
| Layer boundary changes | `.claude/guides/architecture.md` |
| New schema/IR fields | `coding-conventions.md` + `architecture.md` |
| Critique rules | `music-engineering.md` + `coding-conventions.md` |
| CLI commands | `workflow.md` |
| Performance changes | `testing.md` + `workflow.md` |
| **[v2.0] Plan IR changes** | `architecture.md` + design docs in `docs/design/plan-ir/` |
| **[v2.0] Acoustic / Perception** | `music-engineering.md` + `docs/design/perception/` |
| **[v2.0] Arrangement** | `docs/design/arrangement/` (when present) |

### Step 4: Write a failing test

For non-trivial changes, write the test that would pass **after** the change. Verify it fails today.

### Step 5: Implement minimally

Make the test pass with the smallest possible change. Do not refactor in the same commit.

### Step 6: Verify

```bash
make lint              # ruff + mypy
make arch-lint         # Layer boundaries
make test              # All tests
make feature-status    # FEATURE_STATUS.md alignment
```

### Step 7: Update documentation

- `FEATURE_STATUS.md` if status changes
- `PROJECT.md` if a public-facing concept changes
- `VISION.md` if a forward-looking design changes
- `docs/design/<topic>.md` for non-trivial design decisions
- `docs/glossary.md` for new vocabulary
- `.claude/skills/...` for new domain knowledge

### Step 8: Commit

Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Type: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`
Scope: `composer`, `harmony`, `ir`, `verify`, `cli`, `perception`, `groove`, `conversation`, `arrange`, etc.

Example:

```
feat(perception): add LUFS extraction via pyloudnorm

Adds Stage 1 of the Perception Layer per PROJECT.md v2.0 §11.2.
Integrates with the post-generate-perceptual hook.
Surfaces results in evaluation.json under acoustic.loudness.

Closes #142
```

---

## 20. Recent Changes **[v2.0]**

* **2026-05-03**: PROJECT.md and CLAUDE.md upgraded to v2.0. 8-layer architecture (Layer 3.5 MPIR added). 9-step pipeline (Conversation Director + Listening Simulation). 12 specs (was 8). 8 Subagents (Conversation Director added). 30+ critique rules planned. Eight structural improvements explicitly named.
* **2026-04-30**: FEATURE_STATUS.md introduced as single source of truth; feature-status check added.
* **2026-04-29**: MIDI reader, section regeneration (Conductor + CLI), evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades, 4 skills populated, mypy fixes.
* **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff.
* **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance.
* **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI.
* **2026-04-27**: Project initialized.

---

## 21. Escalation **[v2.0 expanded]**

Stop and ask the human when:

- **Architectural changes**: layer rules, Subagent responsibilities, Plan IR shape
- **New external dependencies**: any library not already listed
- **Music theory judgment calls** you are not confident about (e.g., "is this voicing acceptable in jazz?")
- **Deleting files** or rewriting git history
- **Any change touching 5+ files**
- **[v2.0] Adding a new failure mode** (Section 18 of PROJECT.md)
- **[v2.0] Modifying the Critique Registry's role taxonomy** (currently 7: structural, melodic, harmonic, rhythmic, arrangement, emotional, acoustic)
- **[v2.0] Touching pins.yaml schema** — pins are user input, mutating their format risks data loss
- **[v2.0] Changing what "groove applies to all instruments" means** — this affects every output
- **[v2.0] Adding a new use case** to `USE_CASE_EVALUATORS`
- **[v2.0] Changing the `do_not_copy` allowlist** for StyleVectors — this has IP implications

When uncertain, **err toward asking**. The system is large enough that "I'll just figure it out" is rarely the right move.

---

## 22. Failure Modes Reference **[v2.0]**

The 12 failure modes documented in PROJECT.md §18 are recapitulated here in tabular form for quick reference. When you suspect one, follow the link.

| # | Mode | Symptom | Defense |
|---|---|---|---|
| 1 | Mode collapse | All generations feel similar | Multi-candidate, Form Library, vocabulary profiles, strategy diversity |
| 2 | Symbolic optimization drift | Symbolic up, listening down | Acoustic eval, divergence rule, weekly regression |
| 3 | Cliché convergence | Always I-V-vi-IV | `cliche_progression` rule, vocabulary weights |
| 4 | Surprise deficit | Boring | Surprise Score, Tension Arcs, Hook deployment |
| 5 | Frequency masking | Muddy mix | Frequency Clearance, `frequency_collision` rule |
| 6 | Ensemble silence | No dialogue | ConversationPlan, Reactive Fills, `conversation_silence` rule |
| 7 | Cultural monoculture | Only Western pop | Extended scales, multilingual SpecCompiler, Culture Skills |
| 8 | Rights drift | Unclear-status reference | Schema-required `rights_status`, allowlisted comparisons |
| 9 | Provenance erosion | "Why?" unanswerable | Generator return type structurally enforces logging |
| 10 | Layer boundary erosion | Architecture rots | AST architecture lint, pre-commit, CI |
| 11 | Test rot | Skipped/removed tests | No-skip rule, ratchet on test count |
| 12 | Performance creep | Slowly slower | Performance budgets, regression test |

---

## 23. The Eight Improvements at a Glance **[v2.0]**

| # | Improvement | Primary modules | Test directory | Critique rules |
|---|---|---|---|---|
| 1 | **Surprise** | `perception/surprise.py`, `ir/tension_arc.py`, `ir/hook.py` | `tests/unit/perception/`, `tests/scenarios/` | `surprise_deficit`, `surprise_overload`, `tension_arc_unresolved`, `hook_overuse`, `hook_underuse` |
| 2 | **Acoustic Truth** | `perception/audio_features.py`, `verify/acoustic/` | `tests/audio_regression/` | `symbolic_acoustic_divergence`, `lufs_target_violation`, `spectral_imbalance` |
| 3 | **Diversity** | `constants/forms.py`, Skills `harmonic_vocabulary`, generator strategies | `tests/scenarios/test_diversity_sources.py` | (preventive, no specific rule) |
| 4 | **Ensemble Groove** | `ir/groove.py`, `generators/groove_applicator.py`, `grooves/*.yaml` | `tests/unit/generators/test_groove_applicator.py` | `groove_inconsistency`, `microtiming_flatness`, `ensemble_groove_conflict` |
| 5 | **Conversation** | `ir/conversation.py`, agents/conversation-director.md, `generators/reactive_fills.py`, `generators/frequency_clearance.py` | `tests/unit/ir/test_conversation.py`, `tests/scenarios/` | `conversation_silence`, `primary_voice_ambiguity`, `fill_absence_at_phrase_ends` |
| 6 | **Fine-Grained Feedback** | `feedback/pin.py`, CLI `pin`/`feedback` | `tests/unit/feedback/test_pin.py` | (operational, no critique rule) |
| 7 | **Multilingual / Multicultural** | `sketch/`, `constants/scales.py`, Culture Skills | `tests/unit/sketch/test_multilingual.py` | (preventive, no specific rule) |
| 8 | **Arrangement** | `arrange/extractor.py`, `arrange/operations.py`, `arrange/preservation.py`, `arrange/style_vector.py` | `tests/unit/arrange/` | (handled by preservation contract) |

---

## 24. Guides (read when relevant)

| Guide | When to read |
|---|---|
| Architecture | Working across layers; adding modules; touching MPIR |
| Coding Conventions | Writing any code |
| Music Engineering | Generating/modifying notes; acoustic features |
| Testing | Writing or running tests; golden discipline |
| Workflow | Planning a change |
| **[v2.0] Plan IR** | Touching `src/yao/ir/plan/` |
| **[v2.0] Perception** | Touching `src/yao/perception/` |
| **[v2.0] Arrangement** | Touching `src/yao/arrange/` |
| **[v2.0] Subagents** | Editing `.claude/agents/`; behavioral tests |

Guides live under `.claude/guides/`.

Full design: **PROJECT.md** • Forward sketches: **VISION.md** • Status truth: **FEATURE_STATUS.md**

---

## 25. Closing Note **[v2.0]**

YaO v2.0 commits to a sharper conviction than v1.1 did: that "reproducible engineering" alone is not enough. Music must be **interesting** (Surprise), **truly heard** (Acoustic Truth), **diverse** (Diversity Sources), **alive in groove** (Ensemble Groove), **conversational** (Conversation Plan), **finely shaped** (Fine-Grained Feedback), **culturally broad** (Multilingual/Multicultural), and **transformable** (Arrangement Engine).

These eight improvements are not features bolted on. They are how the system commits to its purpose. **Every change you make should serve at least one of them — or, if not, it should be obviously enabling something that does.**

Build the orchestra well, so the conductor can lead it freely.

> *Build the orchestra well. Build it so the human can listen, respond, and surprise.*

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 2.0*
*Last updated: 2026-05-03*
