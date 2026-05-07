# CLAUDE.md — YaO Core Rules

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > other docs.*

---

## Quick Reference

```
make test           # Run all tests
make lint           # ruff + mypy strict
make arch-lint      # Layer boundary check (AST-based)
make all-checks     # lint + arch-lint + test
make format         # Auto-format code
make test-melody    # Unit tests for the phrase-first melody pipeline
make test-genres    # Genre-specific scenario tests
make test-golden    # Snapshot tests of canonical outputs
make profile-perf   # Verify generation stays within performance budget
```

**Key directories:**

```
src/yao/constants/       → Hardcoded values (ranges, scales, MIDI mappings)
src/yao/constants/melodic_profiles/  → 30+ genre profile YAMLs
src/yao/constants/rhythms/           → 30+ rhythm template YAMLs
src/yao/constants/grooves.py         → GrooveProfile presets
src/yao/schema/          → Pydantic models for YAML specs
src/yao/schema/melodic_profile.py    → MelodicProfile schema
src/yao/ir/              → Core data types
src/yao/ir/phrase.py     → Phrase, PhrasePlan, Cadence
src/yao/ir/skeleton.py   → Skeleton, SkeletonNote
src/yao/ir/melody_line.py → MelodyLine, MelodyNote, OrnamentedNote
src/yao/ir/harmonic_context.py → HarmonicContext
src/yao/generators/      → Composition algorithms
src/yao/generators/melody/ → 4-layer phrase-first pipeline (M1–M4)
src/yao/conductor/       → Orchestration + intent parsing
src/yao/render/          → Output (MIDI, audio, stems, score)
src/yao/verify/          → Analysis, lint, evaluation, diff
src/yao/verify/genre_critic.py → Genre-specific anti-pattern checker
src/yao/verify/conformity.py   → KL divergence, motif coherence
src/yao/reflect/         → Provenance tracking
src/yao/errors.py        → Custom exception hierarchy
.claude/skills/genres/   → 30+ paired md/yaml genre Skills
.claude/guides/          → Developer guides (architecture, melody-pipeline, etc.)
references/motifs/       → Reusable motif library
```

**Key types:**

```
Note                 → src/yao/ir/note.py
ScoreIR              → src/yao/ir/score_ir.py
CompositionSpec      → src/yao/schema/composition.py
ProvenanceLog        → src/yao/reflect/provenance.py
GeneratorBase        → src/yao/generators/base.py
Phrase, PhrasePlan   → src/yao/ir/phrase.py
Skeleton             → src/yao/ir/skeleton.py
MelodyLine           → src/yao/ir/melody_line.py
HarmonicContext      → src/yao/ir/harmonic_context.py
MelodicProfile       → src/yao/schema/melodic_profile.py
GrooveProfile        → src/yao/constants/grooves.py
StructuredIntent     → src/yao/conductor/intent_parser.py
GenreCritic          → src/yao/verify/genre_critic.py
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that subagents will use. Your code enables reproducible, auditable, iterable music creation.

The current development effort centers on the **phrase-first melody pipeline** and the **30+ genre profile system**. These are not future additions—they are the present reality YaO is being built into. Treat them as core, not optional.

---

## 7 Non-Negotiable Rules

The first five are foundational. The last two were added when the phrase-first pipeline became core.

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`**
3. **No silent fallbacks** — constraint violations must be explicit errors
4. **No hardcoded musical values** — use `src/yao/constants/`
5. **No public function without type hints and docstring**
6. **The melody pipeline is monolithically four-layer** — never bypass M1–M4 ordering, never let M3 run without M2's skeleton, never call M2 without M1's phrase plan
7. **Genre is a `MelodicProfile`, not a string** — never hard-code genre-specific logic in generators; always parameterize via the loaded profile

---

## MUSTs

### Foundational
- Read existing code before writing new code
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Derive velocity from dynamics curves (never hardcode)
- Register generators via `@register_generator("name")`

### Phrase-First Pipeline
- The `phrase_aware` generator must invoke layers in order: M1 → M2 → M3 → M4
- Each layer records provenance with its specific layer tag (`M1_phrase_plan`, `M2_skeleton`, `M3_surface`, `M4_ornament`)
- Layer M2 must consult `HarmonicContext` for every skeleton note placement
- Layer M3 may only place pitches that connect existing skeleton notes
- Layer M4 microtiming offsets must come from a registered `GrooveProfile`, never hardcoded
- All four layers must be unit-tested independently before testing the full pipeline

### Genre Profiles
- Adding a new genre Skill requires four artifacts:
  1. Markdown file (`.claude/skills/genres/<name>.md`) with required sections
  2. YAML companion (`.claude/skills/genres/<name>.yaml`) producing a valid `MelodicProfile`
  3. Reference catalog entry (`references/catalog.yaml`) with verified license status
  4. Scenario test (`tests/scenarios/test_<genre>.py`)
- Genre Skill Markdown must cite music-theoretical sources for the characterization
- Genre profiles use the `MelodicProfile` Pydantic schema — never define ad-hoc genre dicts in code
- Anti-patterns in a genre Skill must specify severity (`critical` / `major` / `minor` / `hint`) and a fix recipe

### Provenance
- Every generation step records provenance — no exceptions
- Provenance entries are append-only — never delete or modify
- Each provenance entry includes: timestamp, layer, decision, input, output, rationale, agent
- The `update-provenance` hook must run on every change
- Use `provenance.record(layer, decision, input, output, rationale, agent)` consistently

### Intent Parsing
- The intent parser produces a `StructuredIntent` with all 5 emotional dimensions populated
- `IntentToSpec` builds a complete `CompositionSpec` from a `StructuredIntent` — never a partial spec
- Mode selection (Dorian, Phrygian, Lydian, etc.) must come from the genre's `scale_preferences` weighted by emotional vector
- Genre candidates from the parser are ranked with confidence scores

---

## MUST NOTs

### Foundational
- Import `pretty_midi` / `music21` / `librosa` outside designated layers
- Create functions with vague names (e.g., `make_it_sound_good`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError`)
- Leave `TODO` / `FIXME` uncommitted

### Phrase-First Pipeline
- Bypass any of M1–M4 — even when "the simple case" would seem to allow it
- Call M3 without an M2 skeleton, or M2 without an M1 phrase plan
- Mix concrete pitches and Roman numerals in the same context
- Hardcode swing ratios, microtiming offsets, or ornament probabilities
- Replace the existing `rule_based` or `stochastic` generators when adding `phrase_aware`

### Genre Profiles
- Define a genre by fiat without citing sources
- Add a genre Skill without all four required artifacts
- Specify "in the style of [active artist]" — use abstract feature descriptions
- Add reference works of unknown licensing to `references/`

### Adversarial Critic
- Make the Critic praise — its job is to find weaknesses
- Hide critical issues from the Conductor
- Skip genre-specific critique when a genre is set
- Allow Critic outputs to depend on randomness

### Conductor
- Run a Conductor adaptation that violates `CLAUDE.md` rules
- Loop forever — cap iterations, escalate to human after 5 attempts
- Adapt the spec by hardcoding values; always go through the spec schema

---

## 7 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform; humans decide
6. **Phrase before notes** — phrases have function, target pitch, and cadence; notes are derived
7. **Genre is a constellation** — `MelodicProfile`, not a label

---

## Current Phase

**Phase 3** — Motif development + harmonic coupling

**What EXISTS (from Phase 0–2):**

- Spec loading + validation (YAML → Pydantic) ✅
- ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
- Rule-based generator (deterministic) ✅
- Stochastic generator (seed + temperature) ✅
- Generator registry ✅
- Constraint system (must / must_not / prefer / avoid with scoped rules) ✅
- MIDI rendering + stems ✅
- MIDI reader ✅
- Music linting, analysis, evaluation ✅
- Evaluation report persistence (`evaluation.json`) ✅
- Score diff with modified-note tracking ✅
- Provenance logging (append-only, queryable) ✅
- Conductor feedback loop ✅
- Section-level regeneration ✅
- CLI (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section) ✅
- Architecture lint tool ✅
- 7 Claude Code commands ✅
- 7 Subagent definitions ✅
- 4 Skills populated (cinematic genre, voice-leading, piano, tension-resolution) ✅
- **`MelodicProfile` Pydantic schema** (`src/yao/schema/melodic_profile.py`) ✅ — Phase 2
- **5 Tier-1 genre profiles** (`src/yao/constants/melodic_profiles/`) ✅ — Phase 2
  - `bebop_jazz`, `j_pop_ballad`, `classical_romantic`, `lofi_hiphop`, `rock_classic`
- **Phrase IR types** (`Phrase`, `PhrasePlan`, `PhraseFunction`, `CadenceType`) ✅ — Phase 2
- **Skeleton IR types** (`Skeleton`, `SkeletonNote`) ✅ — Phase 2
- **MelodyLine IR types** (`MelodyNote`, `MelodyLine`, `OrnamentedNote`, `OrnamentedMelodyLine`) ✅ — Phase 2
- **HarmonicContext** (`src/yao/ir/harmonic_context.py`) ✅ — Phase 2
- **Layer M1** — `MotifDevelopmentPlanner` (phrase planning + motif generation) ✅ — Phase 2
- **Layer M2** — `SkeletonGenerator` (chord-tone skeleton with harmonic context) ✅ — Phase 2
- **Layer M3** — `SurfaceRealizer` (passing/neighbor tones, rhythm application) ✅ — Phase 2
- **Layer M4** — `OrnamentEngine` (ornaments, articulation, groove microtiming) ✅ — Phase 2
- **`phrase_aware` generator** registered via `@register_generator("phrase_aware")` ✅ — Phase 2
- **176 new tests** for phrase-first pipeline (2978 total) ✅ — Phase 2
- **Profile blending** (`blend_profiles()`) ✅ — Phase 2
- **Profile loading** (`load_melodic_profile()`) ✅ — Phase 2

**What is being BUILT NOW (Phase 3):**

- `HarmonicMelodicSelector` — pitch selection deeply coupled with harmonic context
- `OutlineGenerator` — chord-progression-outlining skeleton strategy
- Enhanced motif development — all 13 motif transformations wired into generation
- Motif library persistence at `references/motifs/`
- Motif coherence scoring integration
- Integration test: `motif_coherence_score >= 0.5` on 32-bar pieces

**What does NOT exist yet (Phase 4 onward):**

- 30+ rhythm templates and `GrooveProfile` engine (Phase 4)
- Tier 2 + Tier 3 genre profiles (Phase 5)
- `GenreCritic` (Phase 5)
- Genre conformity, motif coherence, memorability proxy (Phase 5)
- `IntentParser` and `IntentToSpec` (Phase 6)
- Perception layer (Phase 7)
- Arrangement engine (Phase 8)
- DAW integration via MCP (Phase 8)
- Live improvisation mode (Phase 8)

---

## Phase 2 Implementation Plan — COMPLETE ✅

Phase 2 was completed on 2026-05-07. All deliverables landed:

| Deliverable | Status | Files |
|---|---|---|
| MelodicProfile schema | ✅ | `src/yao/schema/melodic_profile.py` |
| Phrase IR types | ✅ | `src/yao/ir/phrase.py`, `skeleton.py`, `melody_line.py`, `harmonic_context.py` |
| 5 Tier-1 profiles | ✅ | `src/yao/constants/melodic_profiles/*.yaml` |
| Layer M1 (MotifDevelopmentPlanner) | ✅ | `src/yao/generators/melody/motif_developer.py` |
| Layer M2 (SkeletonGenerator) | ✅ | `src/yao/generators/melody/skeleton.py` |
| Layer M3 (SurfaceRealizer) | ✅ | `src/yao/generators/melody/surface.py` |
| Layer M4 (OrnamentEngine) | ✅ | `src/yao/generators/melody/ornament.py` |
| PhraseAwareGenerator | ✅ | `src/yao/generators/melody/phrase_aware.py` |
| 176 new tests | ✅ | `tests/unit/generators/melody/`, `tests/unit/schema/`, `tests/unit/ir/` |
| All 2978 tests green | ✅ | `make all-checks` passes |

---

## Phase 3 Implementation Plan

When working on Phase 3, follow this order. Each step builds on Phase 2.

### Step 1: HarmonicMelodicSelector
1. `src/yao/generators/melody/selector.py`
2. Pitch selection deeply coupled with `HarmonicContext` — chord-tone scoring, avoid-note penalty, voice-leading bonus, metric-strength weighting
3. Integrate into `SkeletonGenerator` to replace simple pitch selection
4. Unit tests verifying pitch choices respect harmonic context

### Step 2: OutlineGenerator
1. `src/yao/generators/melody/outline.py`
2. Generates skeleton by "outlining" the chord progression — chord tones on downbeats, voice-leading at boundaries
3. Alternative skeleton strategy for genres with strong harmonic outlining (bebop, classical)
4. Unit tests verifying chord-tone ratio ≥ profile.chord_tone_targeting

### Step 3: Enhanced Motif Development
1. Wire all 13 motif transformations (identity, transposed, inverted, retrograde, augmented, diminished, sequential, fragmented, extension, truncation, chromatic_decoration, rhythmic_displacement, interpolation) into `MotifDevelopmentPlanner`
2. Motif assignment strategy driven by `MelodicProfile.motif_transformations` weights
3. Track motif derivation using `MotifNetwork`
4. Unit tests verifying transformation diversity

### Step 4: Motif Library Persistence
1. `references/motifs/catalog.yaml` — motif index with metadata
2. JSON format for individual motifs
3. Loader/saver for motif library
4. Spec support: `motifs.primary.source: library` / `motifs.primary.source: generate`

### Step 5: Motif Coherence Scoring
1. `src/yao/verify/conformity.py` — `motif_coherence_score()` implementation
2. Measures motif recurrence and variation balance across sections
3. Genre-specific target ranges (from `MelodicProfile`)
4. Integration test: `motif_coherence_score >= 0.5` on 32-bar pieces

### Step 6: Integration + Acceptance
- All existing tests still green
- `phrase_aware` generator uses `HarmonicMelodicSelector` for pitch decisions
- Cadences clearly resolve at phrase boundaries
- Motivic connection between sections measurable
- `make all-checks` passes

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization:

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | Code-review pattern | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| Phrase pipeline order violation | Pipeline runtime asserts M1 before M2 before M3 before M4 | `make test-melody` |
| MelodicProfile schema drift | Pydantic validates every profile YAML at startup | `make test` |
| Missing genre artifacts | `genre-skill-validate` hook + CI check | git hook |
| Microtiming hardcode in M4 | Code-review pattern (no literal in `timing_offset_ms=`) | `make lint` |
| Genre-specific logic in generators | Code-review pattern (no `if genre == ...` in `src/yao/generators/`) | `make lint` |

---

## Performance Expectations

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Load MelodicProfile | <50ms | Cached after first load |
| Generate 8-bar piece (rule_based) | <1s | |
| Generate 8-bar piece (stochastic) | <1s | |
| Generate 8-bar piece (phrase_aware) | <2s | Multi-layer overhead acceptable |
| Generate 64-bar piece (any) | <5s | |
| Phrase plan only (M1) | <300ms | Lightweight |
| Skeleton generation (M2) | <1s | Most expensive layer |
| Surface realization (M3) | <500ms | |
| Ornament + groove (M4) | <300ms | |
| Write MIDI file | <200ms | pretty_midi |
| Run full lint | <500ms | |
| Run all tests | <8s | ~400 tests after Phase 5 |
| Architecture lint | <1s | AST parsing |
| Genre conformity score | <500ms | KL divergence over 32 bars |
| Motif coherence score | <300ms | |

Do not introduce changes that exceed these budgets without discussion. The phrase-first pipeline budget is intentionally generous; do not exceed it through carelessness.

---

## Provenance Discipline

Every generation step records provenance. This is not optional and not "do at the end."

```python
# Correct
provenance.record(
    layer="M2_skeleton",
    decision="select_target_pitch",
    input={"phrase_id": phrase.id, "current_chord": str(chord), "metric_position": 0.0},
    output={"target_pitch": 67, "chord_relation": "5th"},
    rationale=f"phrase function {phrase.function.value} + chord_tone_targeting={profile.chord_tone_targeting} + voice_leading_target",
    agent="composer-subagent",
)

# Wrong: missing rationale
provenance.record(layer="M2_skeleton", output={"target_pitch": 67})

# Wrong: defer to end
notes = []
for ...:
    notes.append(...)
# no provenance written until end — DO NOT DO THIS
```

`provenance.json` is **append-only**. Never delete or modify existing entries.

---

## Music Engineering Discipline

When writing code that touches music:

- Use `yao.ir.timing` for **all** tick/beat/second conversions
- Use `yao.ir.notation` for **all** MIDI note ↔ note name conversions
- Use scientific pitch notation (`C4`, `F#3`, `Bb5`)
- Functional harmony in Roman numerals (`I`, `ii`, `V7/V`); concrete pitches only via `yao.ir.harmony.realize()`
- Velocity is **derived** from dynamics curves and trajectory, never hardcoded
- Range violations raise `RangeViolationError` with a helpful suggestion. Never silently clamp.
- New rhythm templates and genre profiles are static data files (YAML), not Python literals
- Microtiming offsets come from `GrooveProfile`, not from inline numbers
- Ornament rates come from `OrnamentProfile.<event>_probability`, not from inline literals

---

## Testing Discipline

For every new module or feature:

- **Unit tests** in `tests/unit/` covering normal cases, edge cases, error cases
- **Integration tests** in `tests/integration/` for any new generation strategy or pipeline
- **Scenario tests** in `tests/scenarios/` for genre-specific behaviors
- **Music constraint tests** in `tests/music_constraints/` for new constraints
- **Golden tests** in `tests/golden/` for stable canonical outputs

Use existing test helpers:
```python
from tests.helpers import (
    assert_in_range,
    assert_no_parallel_fifths,
    assert_trajectory_match,
    assert_phrase_plan_valid,           # NEW
    assert_skeleton_outlines_harmony,    # NEW
    assert_genre_conformity,             # NEW
    assert_motif_coherence_above,        # NEW
)
```

For genre-specific tests, use **golden tests**: generate output with a fixed seed, snapshot relevant musical features (interval distribution, phrase length distribution, chord-tone ratio), assert future outputs match within tolerance.

---

## Phrase-First Pipeline Patterns

When implementing the melody pipeline, follow these patterns.

### Pattern: Layer dispatch

```python
class PhraseAwareGenerator(GeneratorBase):
    def generate(self, spec: CompositionSpec) -> tuple[ScoreIR, ProvenanceLog]:
        profile = load_melodic_profile(spec.genre.primary)
        if spec.genre.secondary:
            secondary = load_melodic_profile(spec.genre.secondary)
            profile = blend_profiles(profile, secondary, spec.genre.blend_ratio)

        prov = ProvenanceLog()

        plan = MotifDevelopmentPlanner().plan(spec, profile, prov)
        skel = SkeletonGenerator().generate(plan, spec.harmony, profile, prov)
        surf = SurfaceRealizer().realize(skel, profile, prov)
        orn  = OrnamentEngine().apply(surf, profile.ornament_profile,
                                       load_groove(profile.groove_profile_name), prov)

        return self._to_score_ir(orn, spec), prov
```

### Pattern: Profile-parameterized choice

```python
# Wrong
def select_pitch(prev_pitch: int, scale: list[int]) -> int:
    return random.choice(scale)  # not parameterized by genre

# Right
def select_pitch(prev_pitch: int, scale: list[int], profile: MelodicProfile) -> int:
    candidates_with_weights = [
        (p, profile.interval_distribution.get(abs(p - prev_pitch), 0.01))
        for p in scale
    ]
    return weighted_sample(candidates_with_weights)
```

### Pattern: Profile-parameterized error

```python
# Wrong: silent clamp
if pitch > range_max:
    pitch = range_max

# Right: explicit error with suggestion
if pitch > range_max:
    raise RangeViolationError(
        instrument=instrument,
        attempted_pitch=pitch,
        max=range_max,
        suggestion=f"reduce melody contour amplitude or transpose section down an octave",
    )
```

---

## Genre Skill Addition Protocol

When adding a genre Skill (Phase 5 and beyond):

1. **Cite sources** for the characterization. If you cannot cite, escalate.
2. **Create paired files**:
   - `.claude/skills/genres/<name>.md` (human-readable)
   - `.claude/skills/genres/<name>.yaml` (machine-readable `MelodicProfile`)
3. **Add reference works** to `references/catalog.yaml` with verified license. Do not add works of unknown licensing.
4. **Add scenario test** at `tests/scenarios/test_<genre>.py` verifying conformity metrics.
5. **Add anti-pattern checklist** to the Skill with severity levels and fix recipes.
6. **For world music traditions**, flag in the PR description that human review by someone familiar with the tradition is requested.

---

## Recent Changes

- **2026-05-07**: Phase 2 COMPLETE — phrase-first pipeline fully implemented: MelodicProfile schema, 5 Tier-1 genre profiles (bebop_jazz, j_pop_ballad, classical_romantic, lofi_hiphop, rock_classic), all 4 melody pipeline layers (M1–M4), PhraseAwareGenerator registered, 176 new tests (2978 total), all checks green. Phase 3 (motif development + harmonic coupling) begins.
- **2026-05-07**: Phase 2 launched — phrase-first pipeline foundation, MelodicProfile schema, 5 Tier-1 genre profiles in progress; CLAUDE.md updated to v2.0 with phrase-pipeline rules and genre Skill protocol
- **2026-04-29**: MIDI reader, section regeneration, evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades, 4 skills populated, mypy fixes (140 → 0 errors)
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff
- **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance, CLAUDE.md restructured into tiered guides
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Claude Code commands/agents
- **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md

---

## Escalation

Stop and ask the human when:

- Changing architectural boundaries or layer rules
- Adding new external dependencies
- Making music theory judgment calls you're unsure about (especially for cultural traditions outside your knowledge)
- Deleting files or rewriting git history
- Any change touching 5+ files
- Defining a new genre by fiat without sources
- A test fails after 3 fix attempts
- The acceptance criteria for a phase are ambiguous
- IMPROVEMENT.md, PROJECT.md, or CLAUDE.md disagree about something
- Performance budgets are exceeded by more than 20%
- A change would require modifying existing `rule_based` or `stochastic` generators (they must remain stable)

Asking is not weakness. It is correct behavior under uncertainty.

---

## Sound-First Culture

For changes that affect generated music (new generators, new profiles, modified rhythm logic):

- Generate sample outputs with the existing templates before and after the change
- If FluidSynth is available, render to WAV and note any audible differences
- Include in commit message: musical impact note (e.g., "swing ratio measured at 0.67, was 0.50; phrase length distribution shifted toward 8-bar")
- For changes that subjectively improve quality, save sample MIDI/WAV files for the human

You cannot truly "hear" the music yourself, but you can measure features that are proxies for what humans will hear. Use those measurements liberally.

---

## Backward Compatibility

The phrase-first pipeline is added alongside the existing generators, never replacing them.

- The existing `rule_based` and `stochastic` generators continue to work without modification
- All existing tests (226+) must remain green throughout Phase 2 and beyond
- Existing CLI commands behave identically by default
- Users opt into the new pipeline via `generation.strategy: phrase_aware` in their YAML spec
- The default strategy in templates does not change until `phrase_aware` reaches feature parity and the human approves the cutover

If a refactor would touch the existing generators, stop and propose a specific plan to the human before proceeding.

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| Architecture | Working across layers, adding modules |
| Coding Conventions | Writing any code |
| Music Engineering | Generating/modifying notes |
| Melody Pipeline (NEW) | Anything in `src/yao/generators/melody/` |
| Genre Profiles (NEW) | Adding or modifying a genre Skill |
| Testing | Writing or running tests |
| Workflow | Planning a change |

Full design documentation: [PROJECT.md](./PROJECT.md)

---

## Operating Constants — Pinned Reminders

- **Layer rule**: lower layers never depend on higher layers
- **Generators return**: `(ScoreIR, ProvenanceLog)` — always
- **Errors**: typed `YaOError` subclasses; never bare `ValueError`; never silent fallback
- **Constants**: lookups via `src/yao/constants/`; never literals in logic
- **Pipeline order**: M1 → M2 → M3 → M4 — strict, monolithic
- **Genre = MelodicProfile**: never strings in logic, never `if genre == "..."`
- **Provenance**: append-only, recorded for every generation step
- **Tests**: written before or alongside; never skipped without justification
- **Commits**: Conventional Commits, one logical change each
- **Performance**: budgets in this file are not aspirational
- **Migration**: additive, never replacing existing generators
- **Escalation**: when in doubt, stop and ask

---

*CLAUDE.md version: 2.1*
*Last updated: 2026-05-07*
*v2.1: Phase 2 complete — updated Current Phase to Phase 3, added Phase 3 implementation plan, marked Phase 2 deliverables as complete with file locations.*
*v2.0: Added phrase-first pipeline rules (Rules 6, 7), genre Skill protocol, layer M1–M4 patterns, performance budgets for new layers, Phase 2 implementation plan, and 4 new failure-prevention patterns.*
