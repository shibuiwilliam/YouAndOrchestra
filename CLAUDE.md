# CLAUDE.md — YaO Core Development Rules (v2.0)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > VISION.md > other docs.*
>
> **Document version**: 2.0
> **Updated**: 2026-05-04
> **Status**: Operational rules for implementing v2.0 improvements

---

## Quick Reference

```
make test           # Run all tests
make lint           # ruff + mypy
make arch-lint      # Layer boundary check
make feature-status # Verify FEATURE_STATUS.md matches code
make all-checks     # lint + arch-lint + feature-status + test + golden
make format         # Auto-format code
make calibrate-genres  # NEW: genre profile parameter sweep
make sync-skills    # Sync genre skill YAML from markdown front-matter
```

**Key directories:**

```
src/yao/constants/   → Hardcoded values (ranges, scales, MIDI mappings)
src/yao/schema/      → Pydantic models (composition, genre_profile, meter, groove,
                        tuning, articulation, composability)
src/yao/ir/          → Domain IR (Note, ScoreIR, MeterSpec, GrooveProfile,
                        TuningSystem, Articulation, ExpressionCurve, plan/)
src/yao/generators/  → Composition algorithms (rule_based, stochastic, markov,
                        constraint_solver, drum_patterner, counter_melody, ensemble)
src/yao/perception/  → Layer 4 (audio_features, use_case_eval, reference_matcher,
                        psych_mapper, style_vector)
src/yao/render/      → Output (MIDI, audio, stems, articulation_router, musicxml)
src/yao/verify/      → Analysis, linting, evaluation, diff, critique/
src/yao/arrange/     → Arrangement engine (source_extractor, style_vector_ops,
                        preservation, arrangement_diff)
src/yao/reflect/     → Provenance (causal graph), feedback, style_profile
src/yao/conductor/   → Generate-evaluate-adapt loop with multi-candidate
src/yao/errors.py    → All custom exceptions
```

**Key types (NEW in v2.0 marked):**

```
Note                    → src/yao/ir/note.py        [extended in v2.0]
ScoreIR                 → src/yao/ir/score_ir.py
MeterSpec               → src/yao/ir/meter.py        [NEW v2.0]
GrooveProfile           → src/yao/ir/groove.py       [NEW v2.0]
TuningSystem            → src/yao/ir/tuning.py       [NEW v2.0]
Articulation            → src/yao/ir/articulation.py [NEW v2.0]
ExpressionCurve         → src/yao/ir/articulation.py [NEW v2.0]
GenreProfile            → src/yao/schema/genre_profile.py [NEW v2.0]
MusicalPlan (MPIR)      → src/yao/ir/plan/musical_plan.py
CompositionSpec         → src/yao/schema/composition.py
ProvenanceLog           → src/yao/reflect/provenance.py
GeneratorBase           → src/yao/generators/base.py
StyleVector             → src/yao/perception/style_vector.py [NEW v2.0]
PerceptualReport        → src/yao/perception/audio_features.py [NEW v2.0]
ArrangementDiff         → src/yao/arrange/arrangement_diff.py [NEW v2.0]
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that Subagents will use. Your code enables reproducible, auditable, iterable music creation across **diverse genres, meters, grooves, tunings, and articulations**.

YaO v2.0 expands the system from "Western melody-and-harmony-and-4/4-and-12TET" to honor the world's musical traditions. Every code change should ask: **does this assume a particular tradition, or does it accommodate plurality?**

---

## 6 Non-Negotiable Rules

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`**
3. **No silent fallbacks** — constraint violations must be explicit errors
4. **No hardcoded musical values** — use `src/yao/constants/` or genre-aware lookups
5. **No public function without type hints and docstring**
6. **No implicit Western-tradition defaults** [NEW v2.0] — meter, tuning, groove, articulation must be explicit; defaults come from GenreProfile, never from code constants

---

## MUSTs

### Core (Inherited from v1.0)
- Read existing code before writing new code
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Derive velocity from dynamics curves (never hardcode)
- Register generators via `@register_generator("name")`
- Update `FEATURE_STATUS.md` row in the same PR as the feature

### v2.0 Additions
- **Consult GenreProfile when generating notes**: defaults for tempo, contour, harmonic extensions come from the active genre profile
- **Use `yao.ir.meter.MeterSpec` for all meter operations**: never write `bars * 4` assuming 4 beats per bar
- **Use `yao.ir.groove.apply_groove()` for microtiming**: never set `microtiming_offset_ms` directly
- **Use `yao.ir.tuning.apply_tuning()` for pitch realization**: never write naked `pretty_midi.Note(pitch=60)` if the spec has a non-12TET tuning
- **Use `yao.ir.articulation.realize()` to convert articulation IR into MIDI events**: keyswitches and CCs go through this function
- **Validate GenreProfile completeness before generation**: missing fields raise `IncompleteGenreProfileError`
- **Honor `requires_mpe` flag on TuningSystem**: emit a warning if MPE-required tuning is rendered to single-channel MIDI
- **Track all new IR fields in Provenance**: articulation choice, tuning offset, groove application — each gets a provenance entry
- **Run `make calibrate-genres` before claiming a GenreProfile is "ready"**: parameter sweeps must validate the profile

## MUST NOTs

### Core (Inherited from v1.0)
- Import `pretty_midi` / `music21` / `librosa` outside designated layers
- Create functions with vague names (`make_it_sound_good`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError`)
- Leave `TODO` / `FIXME` uncommitted

### v2.0 Additions
- **Hardcode `time_signature == "4/4"` anywhere in code**: even in tests, use a meter fixture
- **Hardcode `swing` as scalar in code**: it must come from GrooveProfile if present
- **Hardcode `velocity = 100` even in tests**: derive from dynamics
- **Hardcode pitch values without consulting TuningSystem**: a "C4 = 60" assumption is a 12TET assumption
- **Substitute a "reasonable" articulation when none is specified**: leave `articulation: None` and let the renderer use the instrument default
- **Reference real artists by name in code, tests, or fixture data**: GenreProfile uses abstract feature descriptions
- **Add a new genre Skill without a paired GenreProfile YAML**: Markdown and YAML are paired; `make sync-skills` enforces this
- **Bypass GenreProfile validation in tests with `# noqa` style suppression**: if a test needs incomplete GenreProfile, build it explicitly via `IncompleteGenreProfile.from_partial(...)` to make the partiality explicit
- **Use 12TET intervals (semitones) directly in non-12TET contexts**: convert to cents via `yao.ir.tuning.intervals_to_cents()`

---

## 6 Design Principles (Updated for v2.0)

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record (now causal-graph-structured)
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first (generalized)** — design trajectory, meter, groove, tuning, articulation curves before notes
5. **Human ear is truth** — automated scores inform, humans decide
6. **Vertical Alignment** [NEW] — input expressiveness, processing depth, and evaluation resolution must advance together; do not deepen one alone

---

## Current Phase

**Phase 1.5** — Foundation for Genre Plurality

**v2.0 Foundations Being Built:**

| Component | Status |
|---|---|
| GenreProfile YAML schema | 🟡 In design |
| GenreProfile numeric backfill (8 genres) | 🟡 Per-genre work |
| Dynamic evaluation weights from GenreProfile | 🟡 In design |
| MeterSpec IR | 🟡 In design |
| DrumPattern meter-aware refactor | 🟡 In design |
| GrooveProfile IR | ⚪ After Phase 1.5 |
| Articulation IR | ⚪ After Phase 1.5 |
| TuningSystem IR | ⚪ Phase 3 |
| Spec composability (extends/overrides) | ⚪ Phase 2 |
| Genre Coverage Tests | ⚪ Phase 2 |
| Perception Layer (Stages 1, 2, 3) | ⚪ Phase 3 |
| Arrangement Engine | ⚪ Phase 3 |

**What EXISTS (carried from v1.0):**

* Spec loading + validation (YAML → Pydantic, v1 + v2) ✅
* ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
* Rule-based generator (deterministic) ✅
* Stochastic generator (seed + temperature) ✅
* Drum patterner + counter-melody ✅
* MPIR (SongFormPlan, HarmonyPlan) ✅
* Generator registry (strategy selection via spec) ✅
* Constraint system ✅
* MIDI rendering + stems ✅
* MIDI reader (MIDI → ScoreIR) ✅
* Music linting, analysis, evaluation (10 metrics, 3 dims) ✅
* Critique rules (15 rules, 6 categories, structured Findings) ✅
* Conductor feedback loop with critique integration ✅
* Section-level regeneration ✅
* CLI (11 commands including preview/watch) ✅
* Architecture lint, feature-status check ✅
* 7 Subagent definitions, 7 slash commands, 8 Genre Skills ✅

**What does NOT exist yet (v2.0 priorities):**

* Numeric GenreProfile schema and validation
* Genre-aware evaluation weights
* MeterSpec / GrooveProfile / TuningSystem / Articulation IRs
* Spec composability
* Perception Layer (Stages 1-3)
* Arrangement Engine
* Markov / constraint_solver generators
* Genre Coverage Tests
* DAW (MCP) integration
* Live improvisation mode

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization:

| Pattern | What Catches It | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | Code review pattern (no literal in `velocity=`) | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| FEATURE_STATUS drift | `tools/feature_status_check.py` | `make feature-status` |
| Skill ↔ GenreProfile desync [v2.0] | `tools/skill_sync.py` | `make sync-skills` |
| 4/4 hardcoded assumption [v2.0] | `tools/meter_assumption_lint.py` | `make meter-lint` |
| Western default leak [v2.0] | `tools/check_genre_profile_defaults.py` | `make genre-defaults-check` |
| GenreProfile incomplete [v2.0] | `IncompleteGenreProfileError` raise | `make test` |
| Microtonal MPE missing [v2.0] | `tuning-mpe-check` hook | `make hook-check` |

---

## Performance Expectations (Updated for v2.0)

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec (v1, v2) | <100ms | Pydantic validation |
| Load YAML spec with composability (v3) | <200ms | + fragment merging |
| Load GenreProfile | <50ms | Cached after first load |
| Generate 8-bar piece | <1s | Both base generators |
| Generate 64-bar piece | <5s | Stochastic may vary |
| Generate with multi-candidate (5 plans) | <15s | Parallelizable |
| Apply groove profile | <100ms | Per piece |
| Apply tuning system (12TET) | negligible | No-op |
| Apply tuning system (microtonal) | <500ms | + pitch_bend computation |
| Write MIDI file | <200ms | pretty_midi |
| Write microtonal MIDI (MPE) | <500ms | + per-channel routing |
| Run full lint | <500ms | All lint rules |
| Run all tests | <8s | ~700 tests (v2.0 target) |
| Architecture lint | <1s | AST parsing |
| Audio feature extraction (Layer 4 Stage 1) | <2s | librosa per minute of audio |
| Reference matching (Layer 4 Stage 3) | <1s | Pre-computed feature vectors |
| Arrangement diff generation | <3s | Per arrangement run |
| Genre calibration sweep | <10min | 100 generations × 1 genre |

Do not introduce changes that exceed these budgets without discussion.

---

## v2.0 Specific Implementation Guidelines

### G1. Adding a New IR

When adding new IR types (MeterSpec, GrooveProfile, TuningSystem, Articulation):

1. Place in `src/yao/ir/<name>.py` as frozen dataclass
2. Add corresponding Pydantic schema in `src/yao/schema/<name>.py`
3. Document in `src/yao/ir/__init__.py` public API
4. Add unit tests in `tests/unit/ir/test_<name>.py`
5. Update `.claude/guides/music-engineering.md`
6. Update glossary in PROJECT.md
7. Add row to FEATURE_STATUS.md
8. Add architecture lint rule if new layer dependency emerges

### G2. Extending Note IR

The `Note` dataclass gains optional fields in v2.0. Backward compatibility is **mandatory**:

```python
@dataclass(frozen=True)
class Note:
    # v1.0 fields (required)
    pitch: MidiNote
    start: Beat
    duration: Beat
    velocity: Velocity

    # v2.0 fields (optional with defaults)
    articulation: Articulation | None = None
    expression: tuple[ExpressionCurve, ...] = ()
    tuning_offset_cents: float = 0.0
    microtiming_offset_ms: float = 0.0
```

When working with notes, always use `Note(...)` constructor or `dataclasses.replace(note, ...)`. Never mutate (frozen guarantees this).

### G3. Working with GenreProfile

```python
from yao.schema.genre_profile import load_genre_profile

# Load a profile
profile = load_genre_profile("lofi_hiphop")

# Use defaults from profile
tempo = spec.tempo_bpm or profile.tempo.central
swing = spec.groove.swing if spec.groove else profile.groove.swing.value

# Validate before relying on it
profile.validate_complete()  # raises IncompleteGenreProfileError if missing fields

# Genre inheritance
parent = profile.parent  # may be None
combined_signature_progressions = profile.harmony.signature_progressions + (
    parent.harmony.signature_progressions if parent else []
)
```

Never modify a loaded GenreProfile — they are frozen. To customize, use spec composability.

### G4. Working with MeterSpec

```python
from yao.ir.meter import MeterSpec, parse_meter_string

# Construct
meter = MeterSpec(
    numerator=7, denominator=8,
    grouping=(2, 2, 3),
    is_compound=False,
    pulse_unit="eighth",
    metric_accents=(1.0, 0.5, 0.5, 0.7, 0.5, 0.7, 0.5),  # accents on pulses 1, 4, 6
)

# Or parse from string with grouping notation
meter = parse_meter_string("7/8 (2,2,3)")

# Convert beats considering meter
from yao.ir.timing import bars_to_beats
beats = bars_to_beats(2, meter)  # 2 bars in 7/8 = 14 eighth-note pulses
```

### G5. Working with GrooveProfile

```python
from yao.ir.groove import GrooveProfile, apply_groove

# Apply groove to a sequence of notes
grooved_notes = apply_groove(notes, groove_profile, jitter_seed=42)

# Each note now has microtiming_offset_ms set; original timing preserved in start
```

`apply_groove` is the only sanctioned way to set `microtiming_offset_ms`. Direct manipulation is forbidden.

### G6. Working with TuningSystem

```python
from yao.ir.tuning import TuningSystem, apply_tuning, requires_mpe

tuning = TuningSystem.load("maqam_rast")

# Apply tuning to notes (sets tuning_offset_cents)
tuned_notes = apply_tuning(notes, tuning)

# Renderer uses tuning_offset_cents to emit pitch_bend
# But check MPE requirement first
if requires_mpe(tuning, polyphony=score.max_polyphony):
    renderer.use_mpe = True
```

### G7. Working with Articulation

```python
from yao.ir.articulation import Articulation, get_default_articulation

violin_legato = get_default_articulation("violin", style="cantabile")
# Returns Articulation(name="legato", duration_factor=1.0, ...)

# Apply to notes
notes_with_art = [
    dataclasses.replace(n, articulation=violin_legato) for n in notes
]
```

The renderer `articulation_router.py` consumes these and emits the right MIDI events (keyswitches, CCs).

### G8. Adding a New Genre

When adding a genre:

1. Create `.claude/skills/genres/<name>.md` with rich front-matter (the YAML profile is generated from front-matter)
2. Run `make sync-skills` to generate `.claude/skills/genres/<name>.yaml`
3. Validate via `yao validate-genre <name>`
4. Provide at least 3 reference compositions in `references/<name>/`
5. Add entry to FEATURE_STATUS.md genre table
6. Add tests in `tests/genre_coverage/test_<name>.py`
7. Run `make calibrate-genres NAME=<name>` to verify profile produces in-genre output

### G9. Adding a New Generator

```python
from yao.generators.base import GeneratorBase, register_generator
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog

@register_generator("markov")
class MarkovGenerator(GeneratorBase):
    """Generates notes via Markov chain trained on genre corpus."""

    def generate(
        self,
        spec: CompositionSpec,
        plan: MusicalPlan,
        genre_profile: GenreProfile,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        # MUST consult genre_profile, not hardcoded values
        # MUST honor MeterSpec, GrooveProfile, TuningSystem from plan
        # MUST emit ProvenanceLog entries for every decision
        ...
```

### G10. Multi-Candidate Generation

When implementing multi-candidate logic:

```python
candidates = []
for seed in candidate_seeds:
    plan = generate_plan(spec, seed=seed)
    candidates.append(plan)

ranked = critic.rank_candidates(candidates)
selected = producer.select(ranked)  # may merge top candidates

score = note_realizer.realize(selected)
```

Multi-candidate logic lives in `conductor/multi_candidate.py`. Do not duplicate it elsewhere.

### G11. Arrangement Engine Work

Arrangement-mode code is isolated to `src/yao/arrange/`. Touch only this directory unless the change is cross-cutting.

```python
from yao.arrange import (
    extract_source_plan,        # MIDI → MPIR
    compute_style_vector,
    style_vector_arithmetic,
    apply_preservation,
    generate_arrangement_diff,
)
```

The Arrangement Diff is a Markdown file. Its format is rigorously defined in `docs/design/arrangement-diff-format.md`; do not deviate.

### G12. Perception Layer Work

Perception is **post-rendering**. It consumes audio (WAV) and produces `PerceptualReport`.

```python
from yao.perception import (
    extract_audio_features,     # Stage 1
    evaluate_for_use_case,      # Stage 2
    match_references,            # Stage 3
)
```

Stage 3 has hard schema constraints: forbidden comparison axes raise `ForbiddenComparisonAxisError`. **Do not bypass this** — it enforces ethical reference use.

---

## v2.0 Common Failure Modes (Updated F-Codes)

| Code | Pattern | Detection |
|---|---|---|
| F1 | Tick calculation error | Unit tests, `yao.ir.timing` enforcement |
| F2 | Silent range clamp | `RangeViolationError`, no `min(127, ...)` patterns |
| F3 | Velocity hardcode | Lint rule for `velocity=` literals |
| F4 | Missing provenance | mypy on return type |
| F5 | Layer boundary breach | `make arch-lint` |
| F6 | Schema/model mismatch | Integration tests on all templates |
| F7 | Parallel fifths | Constraint checker |
| F8 | FEATURE_STATUS drift | `make feature-status` |
| **F9** | **Skill ↔ GenreProfile desync** [NEW] | `make sync-skills` |
| **F10** | **4/4 hardcoded** [NEW] | `make meter-lint` |
| **F11** | **Western tradition default leak** [NEW] | `make genre-defaults-check` |
| **F12** | **Incomplete GenreProfile bypass** [NEW] | `IncompleteGenreProfileError`, no `try: profile.validate_complete() except: pass` |
| **F13** | **Direct microtiming write** [NEW] | Lint: `note.microtiming_offset_ms =` outside `apply_groove` is an error |
| **F14** | **Non-MPE microtonal MIDI** [NEW] | `tuning-mpe-check` hook warns |
| **F15** | **Real-artist reference in code/tests** [NEW] | Lint: known artist name list checked |

---

## v2.0 Code Conventions

### Style

- Python 3.11+, `from __future__ import annotations`
- mypy strict on all `src/yao/`
- ruff lint and format (line length: 120)
- Pydantic v2 for YAML specs, frozen dataclasses for IR
- Custom exceptions only (`YaOError` subclasses)
- Pre-commit hooks enforce all of the above

### Naming Conventions [v2.0 additions]

- Frozen dataclass for IR: `MeterSpec`, `GrooveProfile`, `TuningSystem`, `Articulation`, `ExpressionCurve`
- Pydantic schema: `MeterSpecSchema`, `GrooveProfileSchema`, etc. (with `Schema` suffix for validation models)
- Loader functions: `load_genre_profile`, `load_groove_profile`, `load_tuning`
- Apply functions (no mutation): `apply_groove`, `apply_tuning`, `apply_articulation`
- Realize functions (consume IR, produce MIDI events): `realize_articulation`, `realize_meter`
- Validation functions: `validate_complete`, `validate_in_range`, `validate_compatible`

### Provenance Conventions [v2.0]

Every new generation decision adds a provenance entry:

```python
provenance.append(
    ProvenanceEntry(
        action="apply_groove",
        target=note_id,
        decision={
            "groove_profile": "j_dilla_drunken",
            "offset_ms": -18,
            "jitter_seed": 42,
        },
        rationale="Genre-specified default groove for lo-fi hip-hop",
        parent_decisions=[note.provenance_id],  # causal graph edge
    )
)
```

### Testing Conventions [v2.0]

- Add to `tests/unit/<layer>/test_<module>.py` for unit tests
- Add to `tests/integration/` only for end-to-end pipelines
- Add to `tests/scenarios/` for musical scenario tests
- Add to `tests/genre_coverage/test_<genre>.py` for per-genre validation [NEW]
- Add to `tests/golden/` for bit-exact MIDI regression
- Use fixtures from `tests/fixtures/`:
  - `fixtures/meters/` for MeterSpec instances
  - `fixtures/grooves/` for GrooveProfile instances
  - `fixtures/tunings/` for TuningSystem instances
  - `fixtures/genre_profiles/` for GenreProfile instances

```python
def test_balkan_dance_meter():
    spec = load_test_spec("fixtures/specs/balkan_dance.yaml")
    plan = conductor.generate(spec)

    # Verify meter is honored
    assert plan.form.meter == MeterSpec(
        numerator=7, denominator=8,
        grouping=(2, 2, 3), is_compound=False,
        pulse_unit="eighth",
        metric_accents=(1.0, 0.5, 0.5, 0.7, 0.5, 0.7, 0.5),
    )

    # Verify drums respect grouping
    drum_hits = plan.drums.hits
    long_pulse_hits = [h for h in drum_hits if h.time_in_pulses == 5]
    assert len(long_pulse_hits) > 0, "Long pulse should have accent"
```

---

## Escalation

Stop and ask the human when:

- Changing architectural boundaries or layer rules
- Adding new external dependencies
- Making music theory judgment calls you're unsure about
- Deleting files or rewriting git history
- Any change touching 5+ files
- **Adding a new musical tradition without GenreProfile guidance** [v2.0]
- **Setting numeric values in GenreProfile without empirical grounding** [v2.0]
- **Implementing a tuning system you cannot find in the recommended reading** [v2.0]
- **Reverse-engineering microtiming from a copyrighted recording** [v2.0]

The last four are critical because YaO v2.0 deals with **cultural traditions** and **scientific empirical content**. Wrong numbers in a GenreProfile do not just produce bad output; they propagate stereotypes about a tradition.

---

## v2.0 Cultural Sensitivity Guidelines

When working on:

### Non-Western Traditions
- Read the corresponding cultural-context document in `docs/genres/cultural-context/<tradition>.md`
- When uncertain, escalate rather than guess
- Avoid technical jargon unless it appears in canonical sources for that tradition
- Do not equate non-Western concepts with Western analogs in code (e.g., `maqam` is not a "scale" in the Western sense)

### Tunings and Microtonality
- Cite the temperament source (treatise, paper) in profile YAML
- Do not invent tuning ratios — derive from cited sources
- Document the historical/cultural origin of each tuning system

### Grooves and Rhythms
- Distinguish "groove" (microtiming) from "rhythm" (notated)
- Reference academic sources (Iyer 2002, Naveda 2011) for groove parameters
- Acknowledge that some grooves resist quantification — document the limits

### Genre Imitation
- "Inspired by" is fine; "in the style of <named living artist>" is not
- Use abstract feature descriptions, not artist names
- See `docs/ethics/artist-imitation.md` for examples

---

## Recent Changes (v2.0 Phase 1.5)

* **2026-05-04 (planned)**: GenreProfile schema strict definition; numeric backfill of 8 genres
* **2026-05-04 (planned)**: Dynamic evaluation weights from GenreProfile
* **2026-05-04 (planned)**: MeterSpec IR + DrumPattern meter-aware refactor
* **2026-04-29 (v1.x)**: MIDI reader, section regeneration, evaluation.json persistence, richer feedback adaptations
* **2026-04-28 (v1.x)**: Stochastic generator, generator registry, queryable provenance
* **2026-04-27 (v1.x)**: Project initialized with PROJECT.md and CLAUDE.md

---

## Guides (Read When Relevant)

| Guide | When to Read |
|---|---|
| [Architecture](./.claude/guides/architecture.md) | Working across layers, adding modules |
| [Coding Conventions](./.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](./.claude/guides/music-engineering.md) | Generating/modifying notes |
| [Testing](./.claude/guides/testing.md) | Writing or running tests |
| [Workflow](./.claude/guides/workflow.md) | Planning a change |
| [GenreProfile](./.claude/guides/genre-profile.md) [NEW] | Adding or modifying a genre |
| [Meter](./.claude/guides/meter.md) [NEW] | Working with non-4/4 |
| [Groove](./.claude/guides/groove.md) [NEW] | Working with microtiming |
| [Tuning](./.claude/guides/tuning.md) [NEW] | Working with non-12TET |
| [Articulation](./.claude/guides/articulation.md) [NEW] | Working with performance technique |
| [Arrangement](./.claude/guides/arrangement.md) [NEW] | Working in arrange/ |
| [Perception](./.claude/guides/perception.md) [NEW] | Working in perception/ |

Full design documentation: [PROJECT.md](./PROJECT.md)
Target architecture: [VISION.md](./VISION.md)
Capability matrix: [FEATURE_STATUS.md](./FEATURE_STATUS.md)
Improvement plan: [IMPROVEMENT.md](./IMPROVEMENT.md)

---

## Implementation Priority Heuristics

When picking up an issue, prioritize by:

### Tier 1: Foundation (P1.5 — Days 1–14)
1. **GenreProfile schema** before anything that uses it
2. **MeterSpec IR** before DrumPattern meter-aware refactor
3. **Eval weights from GenreProfile** can be in parallel with the above

### Tier 2: Vertical Alignment (P2 — Days 15–60)
After Tier 1 completes, the next pieces work as a vertical:

- New IR (input expressiveness): GrooveProfile, Articulation, TuningSystem (reduced scope)
- Generator updates (processing depth): consult new IR
- Critic rules (evaluation resolution): catch failure modes for new IR

Always advance these three together for a given dimension. Do not implement GrooveProfile IR without simultaneously updating Stochastic Generator and adding Groove Critic rules.

### Tier 3: Differentiation (P3 — Days 61–105)
- Perception Layer (Stage 1 → 2 → 3 in order)
- Arrangement Engine (full vertical: extractor → style ops → diff)
- TuningSystem (full microtonal MIDI rendering)

### Tier 4: Production (P4 — Days 106+)
- DAW integration
- A/B audition UI
- Reflection Layer activation

---

## Decision Cards (When Stuck)

These are short flowcharts for common decisions.

### "Should I add a new genre?"
1. Is there a documented cultural source for the genre? → If no, escalate.
2. Are there at least 3 rights-cleared reference compositions? → If no, defer.
3. Does the genre fit an existing family? → If yes, inherit; if no, create new family.
4. Have I run `make calibrate-genres` and verified output? → If no, do not merge.

### "Should I extend an existing IR or create a new one?"
1. Is the new concept orthogonal to existing IR? → Create new IR.
2. Does it modify the existing IR's core meaning? → Create new IR (composition over inheritance).
3. Is it just a new field on existing IR? → Extend, with optional + default for backward compat.

### "Should I add a Critic rule?"
1. Does the rule generalize across genres? → Add to global critique catalog.
2. Is it genre-specific? → Add to GenreProfile's `aesthetic_critique` section.
3. Does it require audio analysis? → Add to Perception Layer Stage 1, not Critic.

### "Should I touch the Conductor's adapt logic?"
1. Is this a new failure pattern + fix mapping? → Add to feedback rules table.
2. Is this a major flow change? → Escalate.
3. Is this a one-off case? → Probably wrong — generalize first.

### "Microtonal output: MPE or not?"
1. Polyphony ≤ 1? → Single channel pitch_bend works.
2. Polyphony > 1 in a single instrument? → MPE required.
3. Multiple monophonic instruments? → One channel each, no MPE.
4. Document the choice in renderer output metadata.

---

## Working with Subagents (When in Claude Code)

When developing as a co-developer, you may invoke subagents for specialized tasks:

- `composer` subagent: melody, motif validation
- `harmony-theorist` subagent: chord progression validation
- `rhythm-architect` subagent: drum pattern, groove validation
- `orchestrator` subagent: instrument balance review
- `adversarial-critic` subagent: code review with no-praise stance
- `mix-engineer` subagent: production parameter advice
- `producer` subagent: cross-cutting decision review

For a v2.0 task involving GenreProfile or new IR, consider invoking:

```
> review my GenreProfile YAML using harmony-theorist subagent
> critique my MeterSpec implementation using adversarial-critic subagent
```

---

## The Bottom Line

YaO v2.0 is about making the system honor **musical pluralism** while preserving **engineering rigor**. The two are not in tension if we:

1. Make every implicit default explicit (especially Western defaults)
2. Drive every default from GenreProfile, not from code
3. Validate every new IR with cross-genre tests
4. Document every cultural choice transparently
5. Ground every numeric value in empirical sources
6. Respect the Vertical Alignment Principle in every release

The reward is a system that doesn't just generate music; it generates **the right music for the tradition the user is working in**.

> *Build the orchestra well — and make sure the orchestra knows the music of the world.*

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 2.0*
*Last updated: 2026-05-04*
*Compatible with: Claude Code, Claude Sonnet 4.6+ / Opus 4.7+*
