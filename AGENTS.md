# AGENTS.md — YaO Core Rules (v2.0)

> *Read this file at session start. Detailed guides are in `.Codex/guides/`.*
> *In case of conflict: AGENTS.md > PROJECT.md > other docs.*

---

## Quick Reference

```bash
make test               # Run all tests
make test-unit          # Unit tests only
make test-integration   # Full pipeline tests
make test-music         # Music constraint tests
make test-genre         # v2.0: per-genre scenario tests
make test-drums         # v2.0: drum kit tests
make test-groove        # v2.0: groove engine tests
make lint               # ruff + mypy
make arch-lint          # Layer boundary check
make all-checks         # lint + arch-lint + test
make format             # Auto-format code
make seed-references    # v2.0: ingest reference library
make build-profiles     # v2.0: rebuild genre profile registry
```

**Key directories:**

```
src/yao/constants/       -> Hardcoded values (ranges, scales, MIDI mappings)
  drums.py               -> v2.0: GM drum map (DrumPiece enum)
  drum_patterns.py       -> v2.0: DRUM_PATTERNS library
  groove_templates.py    -> v2.0: named groove templates
  micro_timing.py        -> v2.0: MICRO_TIMING_LIBRARY
  genres.py              -> v2.0: GENRE_HIERARCHY, GenreName enum
  genre_profiles.py      -> v2.0: GENRE_PROFILES registry
  phrase_library.py      -> v2.0: PHRASE_LIBRARY (idiomatic phrases)
  scales.py              -> v2.0: extended with bebop, altered, ragas, etc.
src/yao/schema/          -> Pydantic models for YAML specs
  composition.py         -> v2.0: + genre, + drum_kit, + groove fields
  genre.py               -> v2.0 NEW: GenreSpec, GenreInfluence
  groove.py              -> v2.0 NEW: GrooveSpec
src/yao/ir/              -> Core data types (Note, ScoreIR, harmony, voicing)
  drum_part.py           -> v2.0 NEW: DrumNote, DrumPart
  synth_part.py          -> v2.0 NEW: SynthPart, ModulationCurve
  phrase.py              -> v2.0 NEW: PhraseTemplate, PhraseInstance
  harmony.py             -> v2.0: extended ChordSpec (extensions, alterations)
  voicing.py             -> v2.0: + power, quartal, shell, rootless, ...
  timing.py              -> v2.0: groove application functions
src/yao/generators/      -> Composition algorithms
  rule_based.py          -> v2.0: genre-aware
  stochastic.py          -> v2.0: genre-aware
  drum_generator.py      -> v2.0 NEW
  markov.py              -> v2.0 NEW
  ai_bridge.py           -> v2.0 NEW (optional, behind feature flag)
src/yao/perception/      -> v2.0 NEW: Layer 4 finally implemented
  reference_matcher.py
  psych_mapper.py
  style_vector.py
src/yao/arrange/         -> v2.0 NEW: arrangement engine
  operations.py, reharmonize.py, regroove.py, reorchestrate.py,
  genre_transfer.py
src/yao/render/          -> Output (MIDI, audio, stems)
  midi_writer.py         -> v2.0: writes drum parts on Channel 10
src/yao/verify/          -> Analysis, linting, evaluation, diff
  evaluator.py           -> v2.0: abstract base
  evaluators/            -> v2.0 NEW: JazzEvaluator, EDMEvaluator, ...
src/yao/conductor/       -> Orchestration engine
  conductor.py           -> v2.0: genre-aware
  feedback.py            -> v2.0: genre-specific adaptations
  mood_parser.py         -> v2.0 NEW: NL -> (MoodVector, GenreSpec)
src/yao/reflect/         -> Provenance tracking
src/yao/errors.py        -> All custom exceptions
references/              -> v2.0: rights-cleared reference library
  catalog.yaml, midi/, extracted_features/, learned_models/
```

**Key types:**

```
# Stable from v1.0
Note                    -> src/yao/ir/note.py
ScoreIR                 -> src/yao/ir/score_ir.py
CompositionSpec         -> src/yao/schema/composition.py
ProvenanceLog           -> src/yao/reflect/provenance.py
GeneratorBase           -> src/yao/generators/base.py
EvaluationReport        -> src/yao/verify/evaluator.py

# New in v2.0
GenreSpec               -> src/yao/schema/genre.py
GenreProfile            -> src/yao/constants/genre_profiles.py
GenreName               -> src/yao/constants/genres.py (enum)
DrumNote                -> src/yao/ir/drum_part.py
DrumPart                -> src/yao/ir/drum_part.py
DrumPiece               -> src/yao/constants/drums.py (enum)
DrumPatternSpec         -> src/yao/constants/drum_patterns.py
MicroTimingProfile      -> src/yao/constants/micro_timing.py
GrooveSpec              -> src/yao/schema/groove.py
PhraseTemplate          -> src/yao/constants/phrase_library.py
ChordSpec (extended)    -> src/yao/ir/harmony.py
VoicingStyle            -> src/yao/ir/voicing.py (enum)
Extension, Alteration   -> src/yao/ir/harmony.py (enum)
SynthPart               -> src/yao/ir/synth_part.py
ModulationCurve         -> src/yao/ir/synth_part.py
MoodVector              -> src/yao/conductor/mood_parser.py
ReferenceFeatures       -> src/yao/perception/style_vector.py
StyleVector             -> src/yao/perception/style_vector.py
ArrangementOp           -> src/yao/arrange/operations.py
```

---

## Your Role

You are a **co-developer of YaO v2.0**, not YaO itself. You build the infrastructure that Subagents will use. Your code enables reproducible, auditable, iterable music creation **across at least 30 genres**.

v2.0 is **additive**. Every v1.0 capability must continue to work. No silent behavior changes. No backward-incompatible schema changes. New features default to `None` or are disabled by absence.

---

## 5 Non-Negotiable Rules

1. **Never break layer boundaries** — see `.Codex/guides/architecture.md`. All v2.0 additions slot into existing layers.
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`** — drum and synth generators included.
3. **No silent fallbacks** — constraint violations, unknown genres, missing profiles, and channel conflicts must be explicit errors.
4. **No hardcoded musical values** — use `src/yao/constants/`. v2.0 adds drum maps, genre profiles, drum patterns, groove templates, phrase library. None of these belong inline in generators.
5. **No public function without type hints and docstring** — applies to every new v2.0 module.

---

## MUSTs

### Carried from v1.0

* Read existing code before writing new code
* Write tests before or alongside implementation
* Keep YAML schemas and Pydantic models in sync
* Use `yao.ir.timing` for all tick/beat/second conversions
* Use `yao.ir.notation` for all note name/MIDI conversions
* Derive velocity from dynamics curves (never hardcode)
* Register generators via `@register_generator("name")`

### New in v2.0

* **Validate `GenreSpec` hierarchy at schema load time** — subgenre must belong to primary. Reject otherwise with `InvalidGenreError`.
* **Use `DrumPart` (not `Part`) for drum kit data** — drum kit always rides MIDI channel 9 (0-indexed = Channel 10).
* **Record `genre_profile_id` and `genre_profile_version` in provenance** for every decision driven by genre profile.
* **Apply the Groove Engine *after* generation, not during** — generators produce grid-aligned notes; `groove.apply()` is called in render preparation. Pre-groove and post-groove tick must both be in provenance.
* **Register every new drum pattern in `DRUM_PATTERNS`** via the pattern registry — never instantiate a pattern inline.
* **Register every new phrase template in `PHRASE_LIBRARY`** with explicit `genre_tags` and `instrument_class`.
* **Genre-specific evaluators must subclass `GenericEvaluator`** and add metrics — never delete or override v1.0 metrics. Use `report.add()`.
* **Every new genre profile must have at least one template** under `specs/templates/genres/<primary>/`.
* **Every new genre profile must have a Skill file** under `.Codex/skills/genres/<primary>/<subgenre>.md`.
* **Fall back to `GenericEvaluator`** when no evaluator subclass exists for the genre. Never error.
* **Fall back to `DEFAULT_PROFILE`** when no `GenreSpec` is set on the composition. Never error.
* **Stop and ask the human** when adding a new primary genre (not just subgenre) — primary genres are normative decisions.

## MUST NOTs

### Carried from v1.0

* Import `pretty_midi` / `music21` / `librosa` outside designated layers
* Create functions with vague names (`make_it_sound_good`)
* Skip provenance recording for any generation step
* Use bare `ValueError` (use `YaOError` subclasses)
* Silently clamp notes to range (raise `RangeViolationError`)
* Leave `TODO` / `FIXME` uncommitted

### New in v2.0

* **Never use `Note` for drum kit data** — `DrumNote` is required. Drum kit pitches are GM percussion sound IDs, not pitches.
* **Never write drum kit data on channels other than 9** — `MidiWriter` enforces this; if drums need to be on multiple channels (unusual), open an architectural discussion first.
* **Never silently apply an alien time signature to a genre profile** — if user requests 7/8 in `pop.mainstream`, the Conductor must record this as an intentional override in provenance and surface a hint in critique.
* **Never blend `GenericEvaluator` results with genre-evaluator results inconsistently** — when a genre evaluator is active, it determines the report. v1.0 metrics are preserved; new metrics are added.
* **Never name a living artist in any profile, prompt, reference description, or test fixture** — use abstract feature descriptions only. CI greps for known artist surnames.
* **Never reference copyrighted material in the reference library** without a license entry in `references/catalog.yaml`. CI rejects PRs adding works without a license entry.
* **Never train a Markov model on works without verified license**. The training corpus must be a subset of `references/catalog.yaml` filtered by license terms allowing derivative works.
* **Never call an external AI model (`ai_bridge`) without explicit user opt-in** — the AI Bridge is behind a feature flag.
* **Never mutate `GenreProfile` at runtime** — profiles are frozen dataclasses. Fusion blending creates a new profile.
* **Never let a drum pattern bypass `humanize`** — even patterns intended to be "tight" pass through humanize with `humanize_ms=0`. This keeps the pipeline uniform.
* **Never put a `Genre` name in a string literal in generator code** — always go through `GENRE_PROFILES[spec.genre.full_id()]` or `resolve_genre_profile(spec)`.

---

## 5 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide

v2.0 deepens each principle (see PROJECT.md §2.1). When you face a tradeoff that touches one of these, re-read the principle before deciding.

---

## Current Phase

**Phase 2 — Diversity Foundation** (months 1–3 of v2.0)

### What EXISTS (carried from Phase 1)

* Spec loading + validation (YAML → Pydantic) ✅
* ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
* Rule-based generator (deterministic) ✅
* Stochastic generator (seed + temperature) ✅
* Generator registry (strategy selection via spec) ✅
* Constraint system (must/must_not/prefer/avoid with scoped rules) ✅
* MIDI rendering + stems ✅
* MIDI reader (load existing MIDI back to ScoreIR) ✅
* Music linting, analysis, evaluation ✅
* Evaluation report persistence (evaluation.json) ✅
* Score diff with modified note tracking ✅
* Provenance logging (append-only, queryable) ✅
* Conductor feedback loop (generate → evaluate → adapt → regenerate) ✅
* Section-level regeneration ✅
* CLI (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section) ✅
* Architecture lint tool ✅
* 7 Codex commands + 7 Subagent definitions ✅
* Skills: cinematic, voice-leading, piano, tension-resolution ✅

### What is IN PROGRESS (Phase 2)

* **Drum Kit System** (A1) — `drums.py`, `drum_patterns.py`, `DrumNote`, `DrumPart`, drum_generator, MIDI Ch10 output
* **Genre Schema** (A2) — `GenreSpec`, `GenreName` enum, `GenreInfluence`, hierarchy validator
* **Genre Profile Library** (A3) — `genre_profiles.py` + Skill files for 30+ genres
* **Conductor Genre-Awareness** (B5) — `mood_parser.py`, genre-conditioned defaults
* **Groove Engine** (B1) — `groove_templates.py`, `micro_timing.py`, render-time application
* **Extended Chord Vocabulary** (B2) — ChordSpec extensions/alterations, VoicingStyle enum
* **Idiomatic Phrase Library** (B3) — `phrase_library.py`, Orchestrator integration
* **Time Signature Flexibility** (B4) — section-level meter, compound meter helpers
* **Genre-Specific Evaluators** (C3) — `evaluators/` subclasses
* **Markov Generator** (C4) — `markov.py` + per-genre learned models
* **Per-Genre Templates** (D4) — `specs/templates/genres/`
* **Genre + Drum + Groove Tests** — `tests/genres/`, `tests/drums/`, `tests/groove/`

### What does NOT exist yet (Phase 3+)

* Synth / Electronic full expansion (C1, partial)
* Perception Substitute Layer full implementation (C2)
* Arrangement Engine (D1)
* AI Bridge (D2)
* Vocal / Lead support (D3)
* DAW integration (MCP)
* Live improvisation mode
* Reflection & Learning Layer (Layer 7) operational

---

## Developing v2.0 Features

### Adding a New Genre

Strict order. Each step's completion is verified by tests before the next begins.

1. **Write the Skill file** at `.Codex/skills/genres/<primary>/<subgenre>.md` following the template in `.Codex/guides/genre-development.md`. Include: overview, instrumentation, tempo/meter, harmonic vocab, melodic vocab, rhythmic vocab, structure templates, evaluation criteria, antipatterns, abstract references, constraints.
2. **Add the profile entry** in `src/yao/constants/genre_profiles.py` as a frozen `GenreProfile`. Cross-reference the Skill file.
3. **Reference existing drum patterns** in the profile's `drum_patterns` field. If a new pattern is needed, add it to `DRUM_PATTERNS` first (separate PR if it's a non-trivial pattern).
4. **Reference existing phrase templates** in the profile's per-instrument fields. Add new phrases to `PHRASE_LIBRARY` as needed.
5. **(Optional) Add a genre-specific evaluator** under `src/yao/verify/evaluators/<primary>.py` if the genre needs metrics beyond `GenericEvaluator`.
6. **Add at least one template** under `specs/templates/genres/<primary>/<id>.yaml`.
7. **Add scenario test** under `tests/scenarios/test_genre_<primary>_<subgenre>.py`. Test produces a valid composition that survives lint, eval, and constraint checks.
8. **Run `make all-checks`**. The new genre must not break any existing tests.

### Adding a New Drum Pattern

1. Define `DrumPatternSpec` in `src/yao/constants/drum_patterns.py`. Required: `name`, `time_signature`, `grid`, `kick_pattern`, `snare_pattern`, `hat_pattern`, `velocity_profile`, `genre_tags`.
2. Patterns are validated at registry-build time. Grid length must match time signature × grid resolution.
3. Add a unit test under `tests/drums/test_pattern_<name>.py` that:
   - Instantiates the pattern at a target bar count
   - Verifies all drum notes are on channel 9
   - Verifies grid alignment matches the pattern definition
   - Verifies humanization stays within `humanize_ms` budget
4. Reference the pattern from at least one `GenreProfile`.

### Adding a New Phrase Template

1. Define `PhraseTemplate` in `src/yao/constants/phrase_library.py`. Required: `name`, `instrument_class`, `genre_tags`, `rhythm_pattern`, `pitch_pattern`, `velocity_pattern`, `articulation`, `typical_length_bars`.
2. Phrase pitch patterns are not literal MIDI numbers — they are `PitchPattern` strategies (e.g., `ChordTones`, `WalkingBass`, `RootOctave`) realized against the current chord.
3. Add a unit test under `tests/unit/test_phrase_<name>.py` that:
   - Instantiates the phrase against a known chord context
   - Verifies all notes are within the instrument's range
   - Verifies rhythm pattern matches the spec
4. Reference the template from `GenreProfile` or `Orchestrator` selection logic.

### Adding a New Genre Evaluator

1. Subclass `GenericEvaluator` under `src/yao/verify/evaluators/<primary>.py`.
2. Override `evaluate()` to call `super().evaluate()` first, then `report.add()` new metrics.
3. Document each metric in the docstring with: definition, range (typically 0.0–1.0), pass threshold, and the source of the threshold (music research, community consensus, or empirical tuning).
4. Register the evaluator in `EVALUATOR_BY_GENRE` in `src/yao/verify/evaluator.py`.
5. Add `tests/unit/test_evaluator_<primary>.py` verifying metrics on synthetic inputs.
6. Add at least one adaptation rule in `GENRE_ADAPTATIONS` (in `feedback.py`) so the Conductor knows what to do when the metric fails.

### Adding a New Groove Template

1. Define `MicroTimingProfile` in `src/yao/constants/micro_timing.py`.
2. Document the source: musicological reference, community consensus, or empirical (record source explicitly).
3. Add unit test verifying that applying the groove preserves note count and ordering, and that offsets stay within ±50ms.

---

## Working with Drum Parts

* **Always use `DrumPart`**, never `Part`, for drum kit data.
* **DrumPart's `midi_channel` is always 9 (0-indexed Channel 10)**. Do not override.
* **DrumNote has no pitch concept** — it has `piece: DrumPiece`. Pitch is implied by the GM percussion map.
* **DrumNote duration is conventionally short (60 ticks)**. Most drum samples ignore note-off anyway; keep the convention for consistency.
* **Use `DrumPiece` enum** for all drum pieces. Never use raw MIDI numbers.
* **Latin and world percussion go on the same `DrumPart`** by default. If you have a clear musical reason for separation (e.g., shaker on its own track for mix), create a second `DrumPart` — both still on channel 9, but a single MIDI file can contain multiple tracks on the same channel.
* **Fills, breakdowns, and drops are computed at section boundaries** by the drum generator. Do not inline them in the pattern itself.
* **Humanization is applied during generation**, not at render. Groove Engine micro-timing is applied at render.

```python
# CORRECT
drum_part = DrumPart(
    instrument_name="drum_kit",
    midi_channel=9,
    notes=tuple(
        DrumNote(piece=DrumPiece.KICK, onset_tick=t, velocity=110)
        for t in kick_tick_positions
    ),
)

# WRONG — using Part with regular Notes
drum_part = Part(
    instrument_name="drum_kit",
    notes=(Note(pitch=36, onset_tick=0, velocity=110, duration_tick=60),),
)
```

---

## Working with Genre

* **Always resolve genre via `resolve_genre_profile(spec)`** — never index `GENRE_PROFILES` directly with a string built inline.
* **Fall back gracefully** — if `spec.genre is None`, use `DEFAULT_PROFILE`. If the requested genre is unknown, raise `UnknownGenreError` (never silently default).
* **Fusion blending creates a new profile** — never mutate the base profile.
* **Record genre choice in provenance** at the top of every generator's output:

```python
def generate(self, spec: CompositionSpec) -> tuple[ScoreIR, ProvenanceLog]:
    profile = resolve_genre_profile(spec)
    log = ProvenanceLog()
    log.record(
        kind="genre_profile_selected",
        profile_id=profile.full_id,
        profile_version=profile.version,
        is_fusion=spec.genre.fusion if spec.genre else False,
    )
    # ... rest of generation
```

* **Genre-typical does not mean genre-mandatory** — profiles are defaults. If user spec overrides (e.g., requests 7/8 in `pop.mainstream`), respect the override but log the divergence.

```python
# CORRECT
if spec.time_signature not in profile.typical_time_signatures:
    log.record(
        kind="genre_meter_divergence",
        requested=spec.time_signature,
        typical=profile.typical_time_signatures,
        severity="hint",
    )
    # ... proceed with user's choice
```

---

## Working with the Groove Engine

* **Generation produces grid-aligned notes.** Generators never apply micro-timing.
* **`groove.apply(score, groove_spec)` is called once,** in `render/midi_writer.py`, after all generation is complete.
* **Pre-groove `onset_tick` is preserved in provenance** so the same generation can be re-grooved with different profiles.

```python
# CORRECT pipeline
score_grid_aligned = generator.generate(spec)
score_grooved = groove.apply(score_grid_aligned, spec.groove or DEFAULT_GROOVE)
midi_writer.write(score_grooved, path)

# WRONG — groove inside generator
def generate(...):
    notes = [...]
    notes = apply_swing(notes)  # NO. Groove is render-time.
    return ScoreIR(notes=notes), log
```

* **Offsets stay within ±50ms** by validator. Anything beyond is a bug — humans do not perceive timing changes beyond ~100ms as "groove"; they perceive them as "wrong."
* **Velocity offsets stay within ±20** for the same reason.

---

## Working with Extended Harmony

* **`ChordSpec` is the source of truth** — extensions, alterations, voicing_hint go on the spec, not in the realization function.
* **`realize(chord_spec, voicing)` is deterministic** given the same inputs. Stochasticity comes from upstream choice, not voicing realization.
* **Power chords contain only root + fifth.** Voice-leading rules for parallel fifths do NOT apply to `VoicingStyle.POWER` — the checker exempts them.
* **Quartal voicings stack fourths.** Voice-leading parallel-fourths rules apply only when `VoicingStyle != QUARTAL`.
* **Slash chords** use the `bass` field, not a synthetic root. `C/E` is `ChordSpec(root=C, quality=MAJ, bass=E)`.

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization:

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | Code review pattern (no literal in `velocity=`) | `make lint` |
| Missing provenance | `GeneratorBase` enforces return type | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| **v2.0: Unknown genre reference** | Genre registry build-time check | `make build-profiles` |
| **v2.0: Drum on wrong channel** | `MidiWriter` channel assertion | `make test` |
| **v2.0: `Note` used for drum kit** | Type checker + runtime guard | `mypy`, `make test-drums` |
| **v2.0: Genre profile mutation** | `frozen=True` dataclass | runtime |
| **v2.0: Phrase template grid mismatch** | Pattern registry validator | `make build-profiles` |
| **v2.0: Drum pattern grid mismatch** | Pattern registry validator | `make build-profiles` |
| **v2.0: Invalid subgenre under primary** | `GenreSpec` Pydantic validator | `make test` |
| **v2.0: Living artist name in references** | CI grep | `make lint` (extended) |
| **v2.0: Unlicensed reference work** | Catalog license check | `make seed-references` |
| **v2.0: Groove offset exceeds 50ms** | `groove.apply()` validator | `make test-groove` |

---

## Performance Expectations

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation, including `GenreSpec` |
| Resolve genre profile | <5ms | dict lookup + cache |
| Build fusion profile | <50ms | blending math |
| Generate 8-bar piece | <1s | All generators |
| Generate 64-bar piece | <5s | Stochastic may vary |
| **v2.0: Instantiate drum pattern (32 bars)** | <50ms | grid expansion + humanization |
| **v2.0: Apply groove engine (full piece)** | <100ms | per-note offset |
| **v2.0: Compute style vector** | <100ms | feature extraction + projection |
| **v2.0: Reference matching (1 query)** | <200ms | nearest-neighbor in 64-dim |
| **v2.0: Markov sampling (8 bars)** | <500ms | order-2 N-gram |
| Write MIDI file | <300ms | pretty_midi, multi-channel including drums |
| Run full lint | <500ms | All lint rules |
| Run all tests | <15s | ~400 tests after Phase 2 |
| Architecture lint | <1s | AST parsing |
| **v2.0: `make build-profiles`** | <3s | full registry rebuild |

Do not introduce changes that exceed these budgets without discussion.

---

## Recent Changes

* **2026-05-16**: Phase 5: 31 new tests (ab_test, project_fingerprint, vocal_synth_bridge), genre-development + drum-development guides, 4 user docs (improvise, ab-testing, daw-integration, vocal).
* **2026-05-16**: Phase 4 complete: A/B testing framework, project fingerprinting, vocal synthesis bridge, DAW MCP bridge (Reaper TCP), yao improvise + yao ab-test CLI commands.
* **2026-05-16**: Phase 3 complete: synth instruments expanded (4→24 GM synths), vocal schema (VocalSpec + vocal_lead role), outcome-based learning in Layer 7 (update_from_outcome).
* **2026-05-16**: Phase 2 complete: 30 genre profiles, 34 templates, 45 skill files, genre distinguishability test expanded to 30 genres.
* **2026-05-15**: PROJECT.md v2.0 and AGENTS.md v2.0. Phase 2 (Diversity Foundation) kickoff.
* **2026-04-29**: MIDI reader, section regeneration, evaluation.json persistence, richer feedback adaptations, Codex command upgrades, 4 skills populated (cinematic, voice-leading, piano, tension-resolution), mypy 140→0.
* **2026-04-29**: Constraint system, CLI diff/explain, stochastic unit tests, modified_notes in ScoreDiff.
* **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance, AGENTS.md tiered guides.
* **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Codex commands/agents.
* **2026-04-27**: Project initialized with PROJECT.md and AGENTS.md.

---

## Escalation

Stop and ask the human when:

* Changing architectural boundaries or layer rules
* Adding new external dependencies (especially AI model SDKs)
* Making music theory judgment calls you're unsure about
* Deleting files or rewriting git history
* Any change touching 5+ files

**v2.0 additions:**

* **Adding a new primary genre** (not just subgenre) — these are normative decisions affecting all downstream code
* **Modifying a `GenreProfile`'s `default_constraints`** — these affect every composition in that genre
* **Adding a Markov model trained on new corpus** — license verification needed
* **Adding a new layer or restructuring the 7-layer model** — almost certainly requires PROJECT.md update first
* **Adding any AI Bridge model** — affects license, privacy, and quality story
* **Changing the GM Channel 10 convention** — affects MIDI compatibility globally
* **Changing the swing_ratio interpretation** (0.5–0.75 currently) — affects all groove rendering

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| [Architecture](.Codex/guides/architecture.md) | Working across layers, adding modules |
| [Coding Conventions](.Codex/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](.Codex/guides/music-engineering.md) | Generating/modifying notes |
| [Testing](.Codex/guides/testing.md) | Writing or running tests |
| [Workflow](.Codex/guides/workflow.md) | Planning a change |
| [Genre Development](.Codex/guides/genre-development.md) *(v2.0)* | Adding a new genre Skill + profile |
| [Drum Development](.Codex/guides/drum-development.md) *(v2.0)* | Adding drum patterns, working with DrumPart |

Full design documentation: [PROJECT.md](PROJECT.md)

---

## v2.0 Cheat Sheet (Start Here for Most Phase 2 Tasks)

**Adding a drum pattern?** → `src/yao/constants/drum_patterns.py` + `tests/drums/`
**Adding a genre profile?** → `.Codex/skills/genres/` + `src/yao/constants/genre_profiles.py` + `specs/templates/genres/` + `tests/scenarios/`
**Adding a phrase template?** → `src/yao/constants/phrase_library.py` + reference from `GenreProfile`
**Working on the Groove Engine?** → `src/yao/constants/micro_timing.py` + `src/yao/ir/timing.py` + `tests/groove/`
**Working on Conductor genre-awareness?** → `src/yao/conductor/conductor.py` + `mood_parser.py` + `feedback.py`
**Working on an evaluator?** → `src/yao/verify/evaluators/<primary>.py` (subclass `GenericEvaluator`)
**Working on the Markov generator?** → `src/yao/generators/markov.py` + `references/learned_models/`
**Touching MIDI output for drums?** → `src/yao/render/midi_writer.py` — `_write_drum_part()` is the critical method
**Adding chord vocabulary?** → `src/yao/ir/harmony.py` + `src/yao/ir/voicing.py`
**Adding a scale?** → `src/yao/constants/scales.py` + reference from at least one `GenreProfile`

When in doubt, search the codebase for the closest existing pattern before inventing a new one.

---

*Document version: 2.0*
*Targeting: Phase 2 — Diversity Foundation*
*Last updated: 2026-05-15*
