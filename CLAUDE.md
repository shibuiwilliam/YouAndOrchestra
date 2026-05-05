# CLAUDE.md — YaO v2.0 Development Guide

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > IMPROVEMENT.md > other docs.*
> *This file supersedes the v1 CLAUDE.md by adding rules and pointers required for the v2 improvements.*

---

## Quick Reference

```
make test           # Run all tests (~2470 tests as of v2.1)
make lint           # ruff + mypy
make arch-lint      # Layer boundary check (AST-based)
make all-checks     # lint + arch-lint + test
make format         # Auto-format code
make dogfood        # Generate Tier-1 dogfood corpus
make validate-refs  # License check on references/
```

**Key directories** (current layout):

```
src/yao/constants/      → Hardcoded values (instruments, scales, chords, genre profiles)
src/yao/schema/         → Pydantic models for YAML specs (v1, v2, v3 composition schemas)
src/yao/ir/             → Core data types (Note, ScoreIR, harmony, motif, voicing,
                          phrase, groove, expression, meter, tuning, trajectory, hook)
src/yao/ir/plan/        → MusicalPlan IR (arrangement, harmony, motif, phrase, drums, song form)
src/yao/generators/     → Composition algorithms (rule_based, stochastic, constraint_solver,
                          markov, twelve_tone, process_music, counter_melody, drum_patterner)
src/yao/generators/note/    → Note realizers (rule_based_v2, stochastic_v2)
src/yao/generators/plan/    → Planners (form, harmony, motif, orchestrator)
src/yao/generators/performance/ → Performance pipeline (articulation, dynamics, microtiming, CC curves)
src/yao/generators/melodic_strategies.py → 8 melodic strategies
src/yao/perception/     → Reference matcher, style vector, psych mapper, surprise,
                          audio features, listening simulator, use-case evaluator
src/yao/render/         → MIDI writer/reader, audio renderer, stems, LilyPond, MusicXML,
                          Strudel, playback, DAW integration (Reaper, MCP bridge)
src/yao/verify/         → Lint, analysis, evaluation, diff, constraints, aesthetic
src/yao/verify/critique/→ 15+ structured critique rules (melodic, harmonic, structural, etc.)
src/yao/reflect/        → Provenance, style_profile, annotation, recoverable errors
src/yao/arrange/        → Arrangement engine (reharmonize, retempo, regroove, reorchestrate, transpose)
src/yao/mix/            → Mix chain, EQ, compression, reverb, master chain
src/yao/conductor/      → Auto-iteration loop, human feedback, multi-candidate, curriculum
src/yao/subagents/      → 7 subagent implementations (producer, composer, critic, etc.)
src/yao/agents/         → Agent backends (Anthropic API, Claude Code, Python-only)
src/yao/feedback/       → NL translation, pin-aware regeneration
src/yao/sketch/         → Sketch-to-spec compiler with emotion vocabulary
src/yao/improvise/      → Real-time engine with context buffer
src/yao/audition/       → Audition/preview server
src/yao/skills/         → Skill loader
src/yao/errors.py       → All custom exceptions
references/             → License-verified corpus (10 entries, expanding)
.claude/skills/genres/  → 22 genre Skills (4 top-level + 18 categorized)
```

**Key types** (current):

```
Note              → src/yao/ir/note.py             (carries articulation + tuning_offset + microtiming)
NoteExpression    → src/yao/ir/expression.py       (legato, accent, bend, pedal overlays)
Phrase            → src/yao/ir/plan/phrase.py       (antecedent/consequent/stand_alone/continuation)
ScoreIR           → src/yao/ir/score_ir.py
GrooveProfile     → src/yao/ir/groove.py            (microtiming, velocity, swing, ghost notes)
MeterSpec         → src/yao/ir/meter.py             (compound, grouping, metric accents)
Tuning            → src/yao/ir/tuning.py            (cents-based, microtonal support)
Motif             → src/yao/ir/motif.py             (transpose/invert/retrograde/augment/diminish)
MusicalPlan       → src/yao/ir/plan/musical_plan.py (full composition plan IR)
CompositionSpec   → src/yao/schema/composition.py   (v1), composition_v2.py, composition_v3.py
ProvenanceLog     → src/yao/reflect/provenance.py
GeneratorBase     → src/yao/generators/base.py
StyleVector       → src/yao/perception/style_vector.py
FeatureProfile    → src/yao/perception/psych_mapper.py (emotion→feature mapping)
CritiqueRule      → src/yao/verify/critique/base.py    (structured Finding objects)
EvaluationReport  → src/yao/verify/evaluator.py        (5-dimension scoring)
SubagentBase      → src/yao/subagents/base.py          (AgentRole, AgentContext, AgentOutput)
```

---

## Your Role

You are a **co-developer of YaO v2**, not YaO itself.

**You build the infrastructure that Subagents use at runtime.** Phase 1 built the symbolic foundation. Phase 2 (now) makes that foundation produce **diverse, high-quality music across many genres** by:

1. Enriching musical expression (phrases, motifs, articulation, micro-timing).
2. Activating genre knowledge (Skills, melody strategies, groove templates).
3. Implementing aesthetic judgment (Layer 4 — previously empty).
4. Genre-aware evaluation (Layer 6 — extended).
5. Bringing the Subagent definitions to life as runnable code.

Refer to `IMPROVEMENT.md` for the canonical list of 24 improvements (A1–A6, B1–B4, C1–C4, D1–D3, E1–E3, F1–F8) with acceptance criteria.

---

## 5 Non-Negotiable Rules (unchanged from v1)

1. **Never break layer boundaries** — see `.claude/guides/architecture.md` and `tools/architecture_lint.py`.
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`**.
3. **No silent fallbacks** — constraint violations must be explicit errors.
4. **No hardcoded musical values** — use `src/yao/constants/`.
5. **No public function without type hints and docstring**.

## 5 New Rules for v2

6. **No new feature without an entry in `IMPROVEMENT.md`** — every PR cites the improvement ID it implements (e.g., "implements A3 — MelodyStrategy plugins").
7. **Every metric introduced must come paired with a Goodhart-defense** — name the orthogonal metric or human signal that catches gaming. State it in the docstring.
8. **License-verified references only** — adding to `references/` requires running `make validate-refs` green. Hook gate enforced in CI.
9. **Layer 4 must be the only place that does aesthetic judgment** — generators (Layer 2) must not embed aesthetic heuristics. They take an `AestheticReport` only as feedback through the Conductor.
10. **The Pipeline Generator is the canonical multi-stage path** — when implementing a new generator, prefer extending Pipeline phases rather than building a parallel monolith.

---

## MUSTs

- Read existing code before writing new code (`view` first; new modules must follow the patterns of nearest siblings).
- Write tests before or alongside implementation.
- Keep YAML schemas and Pydantic models in sync. Schema changes touch both in the same PR.
- Use `yao.ir.timing` for all tick/beat/second conversions.
- Use `yao.ir.notation` for all note name/MIDI conversions.
- Derive velocity from dynamics curves (never hardcode).
- Register generators via `@register_generator("name")`.
- **v2**: Register MelodyStrategy plugins via `@register_melody_strategy("name")`.
- **v2**: Cite the improvement ID in commit messages: `feat(perception): C2 implement style vector arithmetic`.
- **v2**: When adding a Skill (`.claude/skills/...`), follow the structured template (see PROJECT.md §9.2 and §15 of this guide).
- **v2**: When changing Layer 4 outputs, update Conductor adaptation logic in the same PR — they are tightly coupled.
- **v2**: When adding a perception metric, add at least one test against a known-bad sample where the metric correctly flags the badness, **and** at least one test against a stylistically-different-but-good sample where the metric does not over-flag.

## MUST NOTs

- Import `pretty_midi` / `music21` / `librosa` outside designated layers (Layer 3, 5, 6 only).
- Create vague-named functions (`make_it_sound_good`, `improve_this`, `fix_music`).
- Skip provenance recording for any generation step.
- Use bare `ValueError` (use `YaOError` subclasses).
- Silently clamp notes to range (raise `RangeViolationError`).
- Leave `TODO`/`FIXME` uncommitted.
- **v2**: Add a generator at Layer 2 that calls Layer 4 directly — Layer 2 cannot reach Layer 4 (the dependency runs in the opposite direction). Pipeline generator gets aesthetic data via the Conductor's outer loop, not by calling perception itself.
- **v2**: Embed genre-specific logic in core code — genre logic lives in Skills + parameters. The only "branching on genre name" allowed is loading the Skill file.
- **v2**: Add an aesthetic metric that has no literature citation in its docstring (psych mappers must cite primary sources).
- **v2**: Allow a music-theoretic value to differ between code and Skills (e.g., "what is dorian mode?" must be answered by `constants/scales.py` only — Skills reference the constant by name).
- **v2**: Create a Subagent in `.claude/agents/` whose responsibilities overlap with an existing one — coordinate with Producer instead.

---

## 5 Design Principles (unchanged)

1. **Agent = environment, not composer**.
2. **Explain everything**.
3. **Constraints liberate**.
4. **Time-axis first**.
5. **Human ear is truth**.

### v2 Corollaries (treat as principles in practice)

- **No genre is privileged** — Western pop is one tradition among many. The system must not penalize others for being themselves.
- **Aesthetic judgment must be grounded** — references and psychology, never opinion baked into code.
- **Goodhart defense is mandatory** — every metric needs a check.

---

## Current Phase (v2.1)

**Phase 1 (Symbolic Foundation)** — COMPLETE.
**Phase 2 (Genre + Aesthetic)** — LARGELY COMPLETE. Most Sprint 1–2 items implemented.
**Phase 3 (Multi-Agent + Expression)** — LARGELY COMPLETE. Subagents, critique, performance pipeline working.
**Phase 4 (Practical Usability)** — LARGELY COMPLETE. Audition server, human feedback, genre-aware evaluation working.
**Phase 5 (Specialty Expansion)** — PARTIAL. Arrangement engine, constraint solver, tuning, mix chain done. Some items remain.
**Phase 6 (Reflection / Learning)** — CONTINUOUS.

### What EXISTS (current state)

- **Layer 1 (Spec)**: v1, v2, v3 composition schemas with fragment inheritance; groove overrides; tension arcs; hooks; intent; negative space; pins; conversation plans; production settings.
- **Layer 2 (Generate)**: Rule-based, stochastic, constraint-solver, Markov, twelve-tone, process-music generators; v2 note realizers consuming MusicalPlan directly; 8 melodic strategies; counter-melody; drum patterner; reactive fills; frequency clearance; form/harmony/motif/phrase planners; performance pipeline (articulation, dynamics, microtiming, CC curves); groove applicator.
- **Layer 3 (IR)**: Note (with articulation, tuning_offset, microtiming), ScoreIR, GrooveProfile, NoteExpression, MeterSpec (compound/polymeter), Tuning (microtonal), Motif (5 transforms), Phrase (4 roles, contour, cadence), Hook, TensionArc, Trajectory, DynamicsShape, ConversationPlan, Drum IR, MusicalPlan.
- **Layer 4 (Perception)**: StyleVector, PsychMapper (emotion→feature with citations), ReferenceLibrary (10 entries), ReferenceMatcher, AudioFeatures (librosa), SurpriseScoring, ListeningSimulator, UseCaseEvaluator.
- **Layer 5 (Render)**: MIDI writer/reader, audio renderer, stems, LilyPond, MusicXML, Strudel emitter, DAW integration (Reaper writer, MCP bridge), playback, mix chain.
- **Layer 6 (Verify)**: 5-dimension evaluator with dynamic weights, music lint, constraint checker, score diff, aesthetic evaluator, 15+ structured critique rules (melodic, harmonic, structural, rhythmic, groove, emotional, genre fitness, surprise, tension, dynamics, hook, memorability, conversation, arrangement, metric drift).
- **Layer 7 (Reflect)**: Provenance (append-only), style profile, annotation, recoverable error handling.
- **Cross-cutting**: Arrangement engine (5 operations + style vector ops), mix package (EQ, compression, reverb, master chain), conductor (iteration loop, human feedback, multi-candidate, curriculum, audio feedback), 7 subagent implementations, 3 agent backends, sketch-to-spec compiler, improvisation engine, audition server, NL feedback translator, pin-aware regeneration.
- **Skills**: 22 genre skills across 6 categories. 9 agents. 10 commands. 8 guides.
- **Tests**: ~2470 passing tests (unit, integration, scenarios, golden, music-constraints, genre-coverage, audio-regression, properties, subjective, tools, LLM quality).
- **Infra**: architecture lint, meter lint, skill grounding checks, critic coverage, honesty checks, calibration, capability matrix, feature status mapping.

### v2 Implementation — COMPLETE

All 24 improvements (A1–A6, B1–B4, C1–C4, D1–D3, E1–E3, F1–F8) have been implemented
and their acceptance criteria satisfied. See IMPROVEMENT.md §13 for the full audit.

Test count: ~2634 tests passing. Reference library: 31 entries. Genre Skills: 25.

---

## Improvement-ID-Aware Workflow

Every change in v2 must cite an improvement ID. The IDs come from `IMPROVEMENT.md`. The lifecycle:

```
1. Pick improvement ID from IMPROVEMENT.md (e.g., A3 — MelodyStrategy plugins)
2. Read the acceptance criteria for that ID (IMPROVEMENT.md §13)
3. Read PROJECT.md sections that touch the affected layers
4. Search the codebase for nearest existing patterns
5. Write tests for each acceptance criterion BEFORE writing code
6. Implement the smallest change that makes tests pass
7. Run make all-checks
8. Commit with: <type>(<scope>): <ID> <subject>
9. PR description must include "Implements: <ID>" and tick the acceptance criteria
```

---

## Layer 4 (Perception) — Special Notes for Developers

Layer 4 is **new** in v2 and the most likely place for design errors. Read these before touching it.

### What Layer 4 IS

- The **answer to "AI cannot listen"**.
- A **bridge** from internal symbolic data + reference corpus + psychology research to a quasi-perceptual judgment.
- **Bidirectionally tied to references**: changes here often require updating `references/catalog.yaml` and re-extracting features.

### What Layer 4 IS NOT

- Not a generator. It does not produce notes.
- Not a scorer of compliance. (That is Layer 6.)
- Not a substitute for the Adversarial Critic Subagent — it provides input to that Subagent.

### Goodhart Defense Patterns

When adding a new perception metric:

1. **State the gaming attack**: "What's the trivial way for the generator to make this metric 1.0 while making music worse?"
2. **State the cross-check**: another orthogonal metric or human signal that flags the gaming.
3. **Verify with a known-bad fixture**: a fixture that scores high on the new metric but is musically obviously bad. Ensure another metric catches it.

### Reference Library Discipline

- Adding a reference triggers feature extraction (`tools/extract_features.py`) and license validation (`tools/validate_references.py`).
- Removing a reference must be paired with an update to any spec / Skill that named it.
- Reference IDs are immutable. Renaming is a delete + add.

---

## Skills System — Special Notes for Developers

Skills (`.claude/skills/`) are **the contributor surface for non-engineers**. Treat them as a public API.

### Skill Structure (machine-readable header + Markdown body)

```markdown
---
id: jazz
type: genre
tier: 1
version: 1.0
last_reviewed: 2026-05-05
contributors: [musician_alice, engineer_bob]

evaluation_weights:
  structure: 0.2
  melody: 0.3
  harmony: 0.3
  acoustics: 0.1
  groove_pocket: 0.1

evaluation_thresholds:
  predictability_max: 0.85
  section_contrast_min: 0.4

default_groove: swing_8th_67
default_melody_strategy: bebop
default_tonal_system: common_practice
default_rhythm_system: western_meter

cliche_patterns:
  - id: jazz_cliche_001
    name: "Endless ii-V-I in C major"
    detection: ...
references_required: 5
---

# Genre Skill: Jazz
## Identity
...
## Harmony
...
(rest of structured Markdown body)
```

### Skill Validation

- The YAML header must validate against `src/yao/schema/skill.py` (Pydantic).
- The body must contain all required sections (Identity / Harmony / Melody / Rhythm / Instrumentation / Form / Mix Aesthetics / References / Adversarial Critic Rules / Compatible Genre Blends).
- `tools/validate_skills.py` runs in CI.

### When You Are Tempted to Hardcode Genre Logic

Don't. Add a field to the Skill schema, populate the Skill, and read it at runtime. If the field doesn't exist yet, it's a schema change — coordinate, don't shortcut.

---

## Pipeline Generator — Special Notes

The Pipeline Generator (E1) realizes the 6-phase cognitive protocol from PROJECT.md §6. It is the **canonical multi-stage generator** in v2.

### Required Phase Boundaries

Pipeline must call `log.record_phase(phase_name, **kwargs)` at every transition:

```
intent_crystallization → architectural_sketch → skeletal_generation
→ critic_dialogue → detailed_filling → listening_simulation
```

### Phase Implementations

Each phase is a method on `PipelineGenerator`. Phases are individually testable; do not write a phase that depends on side effects of an earlier phase besides the explicit input.

### Latency Budget

Pipeline with `candidate_count: 5` must complete a 64-bar piece in under 30 seconds. If it exceeds, profile per phase. Phase 6 (Listening Simulation) is the most likely culprit — gate Layer 4 calls behind cheap pre-checks where possible.

### Subagent Attribution

Every phase records which logical Subagent produced its output. Phase 5 records three sub-events: Harmony Theorist, Rhythm Architect, Orchestrator. The Producer Engine attribution comes at conflict resolution time, not at phase boundaries.

---

## Code Standards (v2 additions)

### Genre-Aware Code Pattern

When code conditionally adapts to genre, the pattern is:

```python
# WRONG — hardcoded branching on genre name
if genre.name == "jazz":
    use_swing(...)
elif genre.name == "rock":
    use_straight(...)

# RIGHT — read defaults from the Skill, fall back to genre system
groove = genre_skill.default_groove or composition_spec.groove or DEFAULT_GROOVE
```

### Optional Field Pattern (backward compatibility)

When extending IR types in v2, default optional fields:

```python
# RIGHT — preserves v1 behavior
@dataclass(frozen=True)
class Note:
    pitch: int
    start_tick: Tick
    duration: Tick
    velocity: int
    articulation: Articulation = field(default_factory=lambda:
        Articulation(ArticulationType.NORMAL, 0.5))
    expression: Expression = field(default_factory=Expression)
```

### Provenance Pattern

```python
log.record(
    layer="generation",
    phase="skeletal_generation",
    subagent="composer",
    decision="select_motif_seed",
    rationale="Trajectory tension at bar 1 = 0.2; pentatonic minor seed selected",
    parameters={"seed": 42, "candidate_count": 5},
)
```

---

## Test Standards (v2)

### Per-Improvement Test Coverage

Every improvement (A1–F8) must pass its acceptance criteria from IMPROVEMENT.md §13. Mark tests with the improvement ID:

```python
@pytest.mark.improvement("A3")
def test_bebop_strategy_produces_chromatic_approach() -> None:
    ...
```

### Mandatory Test Categories per Improvement Type

- **IR change** → round-trip test (IR → MIDI → IR) preserves semantics.
- **New generator** → produces valid ScoreIR for at least 3 spec templates.
- **New evaluator** → known-good fixture passes; known-bad fixture fails.
- **New perception metric** → known-bad fixture is flagged; stylistically-different-but-good fixture is not over-flagged (Goodhart defense).
- **Schema change** → all existing template specs still validate.
- **CLI change** → integration test with `click.testing.CliRunner`.

### Golden Tests

Pieces that should remain stable (e.g., minimal spec → minimal output) are golden-tested. Updating a golden file requires the PR description to justify the change with audio links.

### Dogfood Tests

End of every Sprint, `make dogfood` generates 3 pieces per Tier-1 genre and stores them under `outputs/dogfood/sprint-N/`. The maintainer **listens** to a sample before declaring the Sprint done.

### Performance Tests

Performance budgets per CLAUDE.md table. New tests in `tests/perf/` must:

- Use `pytest-benchmark`.
- Set explicit thresholds.
- Skip on CI machines below a baseline (markers).

---

## Performance Expectations (v2)

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Generate 8-bar piece (any strategy) | <2s | All generators |
| Generate 64-bar piece (rule-based / stochastic) | <5s | unchanged from v1 |
| Generate 64-bar piece (Pipeline, candidate_count=5) | <30s | NEW — multi-candidate cost |
| Generate 64-bar piece (Pipeline, candidate_count=1) | <8s | NEW — fast path |
| Write MIDI file | <200ms | pretty_midi |
| Run full lint | <500ms | All lint rules |
| Run Programmatic Critic | <500ms | NEW |
| Run Layer 4 perception evaluation | <2s | NEW — for one piece against 50 references |
| Run all unit tests | <15s | ~2470 tests current |
| Architecture lint | <1s | AST parsing |

Do not introduce changes that exceed these budgets without discussion. If a Phase needs more, document and discuss before merging.

---

## Automated Failure Prevention (v2 expanded)

| Pattern | Catcher | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir_timing.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | ruff custom rule (no literal in `velocity=`) | `make lint` |
| Missing provenance | `GeneratorBase` ABC enforces return type | `mypy --strict` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| **NEW** Genre-name hardcoding | ruff custom rule (no `genre.name ==` outside Skill loader) | `make lint` |
| **NEW** Perception metric without citation | `tools/check_perception_citations.py` | `make lint` |
| **NEW** Reference license drift | `tools/validate_references.py` | `make validate-refs` |
| **NEW** Skill schema violation | `tools/validate_skills.py` | `make lint` |
| **NEW** Goodhart defense missing | manual review checklist on PRs adding metrics | code review |
| **NEW** Direct Layer-4 call from generators | `tools/architecture_lint.py` extended | `make arch-lint` |

---

## Recent Changes

- **2026-05-05 (v2.0)**: IMPROVEMENT.md created. CLAUDE.md and PROJECT.md upgraded to v2.
- **2026-05-05 (v2.1)**: Massive implementation push. 17 of 24 improvements fully implemented. Test suite grew from 226 to ~2470 tests. 22 genre Skills populated. Layer 4 (Perception) implemented. Subagents, critique engine, arrangement engine, mix chain, performance pipeline, audition server all working. Documents updated to reflect actual state.

(v1 history preserved separately.)

---

## Escalation

Stop and ask the human when:

- Changing architectural boundaries or layer rules.
- Adding new external dependencies (especially anything beyond the v2 enumeration).
- Making music theory judgment calls you're unsure about.
- **NEW v2**: Designing a new perception metric (Layer 4) — design with the human first, implement after.
- **NEW v2**: Designing a new Adversarial Critic rule that overlaps with existing rules.
- **NEW v2**: Adding/removing references — license review is mandatory.
- **NEW v2**: Adding a new genre Skill at Tier 1 — coordinate with a musician reviewer.
- Deleting files or rewriting git history.
- Any change touching 5+ files.
- A change increases generation latency beyond targets in §Performance Expectations.

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| `architecture.md` | Working across layers, adding modules |
| `coding-conventions.md` | Writing any code |
| `music-engineering.md` | Generating/modifying notes |
| `testing.md` | Writing or running tests |
| `workflow.md` | Planning a change |
| **`perception.md` (NEW)** | Touching Layer 4 |
| **`skills.md` (NEW)** | Adding/editing Skill files |
| **`pipeline.md` (NEW)** | Working on PipelineGenerator phases |
| **`references.md` (NEW)** | Working with `references/` |
| **`goodhart-defense.md` (NEW)** | Designing or modifying evaluation metrics |

Full design documentation: `PROJECT.md` (v2)
Improvement tracking: `IMPROVEMENT.md`

---

## Improvement Index (quick reference)

For full details see IMPROVEMENT.md. This is a one-line lookup.

| ID | Status | What | Where (actual) |
|---|---|---|---|
| A1 | ✅ DONE | Phrase IR | `src/yao/ir/plan/phrase.py` |
| A2 | ⚠️ PARTIAL | Motif Network | `src/yao/ir/motif.py` — missing MotifNetwork/MotifNode |
| A3 | ⚠️ PARTIAL | MelodyStrategy plugins | `src/yao/generators/melodic_strategies.py` — 8 exist, not schema-integrated |
| A4 | ✅ DONE | GrooveTemplate | `src/yao/ir/groove.py` + `grooves/` (20 templates) |
| A5 | ✅ DONE | Compound meter / polymeter | `src/yao/schema/time_signature.py` + `src/yao/ir/meter.py` |
| A6 | ✅ DONE | Articulation / Expression | `src/yao/ir/expression.py` + `src/yao/ir/note.py` |
| B1 | ⚠️ PARTIAL | Tier-1 genre Skills | `.claude/skills/genres/` — 22 exist, 3 Tier-1 missing, fields incomplete |
| B2 | ✅ DONE | Genre blending | `src/yao/schema/composition_v2.py` GenreBlendSpec + blend_aspects |
| B3 | ✅ DONE | Tonal System abstraction | `src/yao/ir/tonal_system.py` (3 impls: CommonPractice, Modal, Maqam) |
| B4 | ✅ DONE | Rhythm System abstraction | `src/yao/ir/rhythm_system.py` (3 impls: WesternMeter, Tala, Iqa) |
| C1 | ⚠️ PARTIAL | Reference Library | `references/catalog.yaml` — 10 entries (need 20+), missing tools |
| C2 | ⚠️ PARTIAL | Style Vector | `src/yao/perception/style_vector.py` — missing arithmetic ops |
| C3 | ⚠️ PARTIAL | Psych Mapper | `src/yao/perception/psych_mapper.py` — missing score→perception |
| C4 | ✅ DONE | Aesthetic Report | `src/yao/perception/listening_simulator.py` |
| D1 | ✅ DONE | Genre-Aware Evaluator | `src/yao/verify/evaluator.py` |
| D2 | ⚠️ PARTIAL | Mood Profile | Needs standalone MoodProfile type |
| D3 | ✅ DONE | Human Feedback Logger | `src/yao/conductor/human_feedback.py` + `src/yao/schema/feedback.py` |
| E1 | ✅ DONE | Pipeline Generator | `src/yao/generators/performance/pipeline.py` + `src/yao/subagents/producer.py` |
| E2 | ✅ DONE | Programmatic Critic | `src/yao/verify/critique/` (15+ rules) |
| E3 | ✅ DONE | Producer Engine | `src/yao/subagents/producer.py` |
| F1 | ✅ DONE | Arrangement Engine | `src/yao/arrange/` |
| F2 | ✅ DONE | AI-Seed Generator | `src/yao/generators/ai_seed.py` (Anthropic API + deterministic fallback) |
| F3 | ✅ DONE | Constraint Solver | `src/yao/generators/constraint_solver.py` |
| F4 | ✅ DONE | Live Preview Server | `src/yao/audition/server.py` |
| F5 | ❌ GAP | Loopability Validator | Not implemented |
| F6 | ❌ GAP | Vocal Line IR | Not implemented |
| F7 | ✅ DONE | Tuning System | `src/yao/ir/tuning.py` |
| F8 | ✅ DONE | Production Layer | `src/yao/mix/` |

---

## Decision Discriminators

When you are unsure where new code belongs, answer these in order:

### 1. What Layer?
Apply the layer test from PROJECT.md §3.

```
Defines a thing only?               → Layer 1 (Spec)
Produces notes?                     → Layer 2 (Generate)
Represents music structurally?      → Layer 3 (IR)
Substitutes for human listening?    → Layer 4 (Perception)
Outputs files / streams?            → Layer 5 (Render)
Evaluates an existing artifact?     → Layer 6 (Verify)
Learns from history?                → Layer 7 (Reflect)
```

### 2. New IR Type or Extend Existing?
- If a generator can choose to use it or ignore it → **extend** (optional field).
- If every piece must have it → **new type only if no existing type fits**.

### 3. New Generator or Extend Pipeline?
- If new logic fits as a Pipeline Phase variant → extend Pipeline.
- If new logic is a fundamentally different paradigm (e.g., constraint solver, LLM bridge) → new generator.

### 4. New Skill or Extend Existing Schema?
- If a single genre needs the data → put in the Skill.
- If many genres need the same field → schema extension + populate Skills.

### 5. New Metric or Extend Existing Evaluator?
- If the metric is symbolic (theory rule) → Layer 6.
- If the metric is perceptual (reference-based or psych-based) → Layer 4.
- If the metric is genre-specific weighting of existing dimensions → Skill `evaluation_weights` (no code change).

### 6. New Subagent or Use Producer Coordination?
- Almost always: use Producer coordination. New Subagents require explicit human approval.

---

## When You Make a Mistake

YaO development encourages reverting cleanly:

1. State what went wrong.
2. Identify which Rule (1–10) was violated.
3. Open the smallest possible PR that restores the rule.
4. Add a regression test.
5. Note the lesson in `docs/design/lessons-learned.md` if novel.

Mistakes are signals, not failures, as long as they are diagnosed and prevented from recurring.

---

## Closing

YaO v2 is the moment when the Orchestra **starts actually playing music**. v1 built the stage, the seats, and the sheet music; v2 puts the players in their chairs and gives them their parts. Your job is to wire those parts cleanly, with respect for the architecture that made all this possible.

Move carefully. Music is not just code; it is something humans care about deeply. Every commit ripples into someone's listening experience, and that experience is the only ground truth that matters in the end.

> *Build the orchestra well, so the conductor can lead it freely — and so the music, when it finally sounds, sounds like itself.*

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 2.1*
*Last updated: 2026-05-05*
*Supersedes: v2.0 (2026-05-05)*
