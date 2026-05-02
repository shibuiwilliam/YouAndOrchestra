# CLAUDE.md — YaO Core Rules

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > VISION.md > other docs.*
> *This is v2.0, aligned with PROJECT.md v2.0 and the v2.0 improvement roadmap.*

---

## Quick Reference

```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-golden       # Golden MIDI regression tests
make test-subjective   # Subjective quality tests (★NEW)
make lint              # ruff + mypy strict
make arch-lint         # Layer boundary check (8 layers)
make feature-status    # Verify FEATURE_STATUS.md matches code
make sync-skills       # Sync genre skill YAML from markdown front-matter
make sync-docs         # Verify PROJECT.md / VISION.md / FEATURE_STATUS.md consistency (★NEW)
make all-checks        # lint + arch-lint + feature-status + sync-docs + test + golden
make format            # Auto-format
```

**Key directories:**

```
src/yao/constants/    → Hardcoded values (ranges, scales, MIDI mappings, dynamics)
src/yao/schema/       → Pydantic models for YAML specs (v1 + v2)
src/yao/ir/           → Score IR (Layer 3)
src/yao/ir/plan/      → Musical Plan IR / MPIR (Layer 3.5)
src/yao/ir/expression.py → Performance Expression IR (Layer 4.5) ★NEW
src/yao/generators/   → Plan generators + Note Realizers + Performance Realizers
src/yao/perception/   → Audio features, use-case eval, reference matcher (Layer 4)
src/yao/render/       → MIDI / audio / MusicXML / LilyPond / DAW projects (Layer 5)
src/yao/mix/          → EQ / compression / reverb / mastering (★NEW)
src/yao/arrange/      → Arrangement Engine (extractor, style ops, diff) (★NEW)
src/yao/verify/       → Lint, evaluation, critique (50+ rules), diff, constraints (Layer 6)
src/yao/reflect/      → Provenance, style profile, annotation (Layer 7)
src/yao/subagents/    → Python subagent implementations (★NEW)
src/yao/agents/       → Backend-agnostic agent protocol (Tier 4)
src/yao/runtime/      → ProjectRuntime (stateful sessions) (Tier 3)
src/yao/improvise/    → Live improvisation engine (Tier 3)
src/yao/sketch/       → NL → spec compiler
src/yao/conductor/    → Multi-candidate orchestration + critic-gate
src/yao/errors.py     → All custom exceptions
```

**Key types:**

```
Note              → src/yao/ir/note.py
ScoreIR           → src/yao/ir/score_ir.py             (Layer 3)
MusicalPlan       → src/yao/ir/plan/musical_plan.py    (Layer 3.5, MPIR)
NoteExpression    → src/yao/ir/expression.py           (Layer 4.5) ★NEW
PerformanceLayer  → src/yao/ir/expression.py           (Layer 4.5) ★NEW
CompositionSpec   → src/yao/schema/composition.py
ProvenanceLog     → src/yao/reflect/provenance.py
Finding           → src/yao/verify/critique/finding.py
SubagentBase      → src/yao/subagents/base.py          ★NEW
GeneratorBase     → src/yao/generators/base.py
StyleVector       → src/yao/perception/style_vector.py ★NEW
PerceptualReport  → src/yao/perception/audio_features.py ★NEW
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself.

You build the infrastructure that **Subagents will use**. Your code enables reproducible, auditable, iterable music creation. You do **not** compose music; you build the environment in which composition becomes engineering.

This distinction matters more in v2.0:

- **Python Subagents** (`src/yao/subagents/`) — structured judgment, deterministic logic
- **Claude Code prompts** (`.claude/agents/*.md`) — creative dialogue, sketch-to-spec
- **Both share the same `AgentContext` / `AgentOutput` contract**

When you implement a Subagent, ensure both representations stay aligned.

---

## 6 Non-Negotiable Rules

These are absolute. Violations are auto-rejected by tooling or review.

1. **Never break layer boundaries** — 8 layers (0, 1, 2, 3, 3.5, 4, 4.5, 5, 6, 7). Enforced by `make arch-lint`. See [.claude/guides/architecture.md](./.claude/guides/architecture.md)
2. **Every generation function returns `(<output>, ProvenanceLog)`** — Plan generators, Note Realizers, Performance Realizers, Mix Designers all comply
3. **No silent fallbacks** — constraint violations must be explicit errors. Use `RecoverableDecision` if recovery is intentional and recorded
4. **No hardcoded musical values** — use `src/yao/constants/`. Includes scales, ranges, dynamics, MIDI mappings, and **scale intervals in cents** (★NEW for microtonal)
5. **No public function without type hints and docstring** — `mypy --strict` enforced
6. **Vertical alignment must be respected** — every change must declare which of {input, processing, evaluation} it advances. Pure-input or pure-processing PRs require justification. (★NEW v2.0)

---

## MUSTs

**Code structure:**
- Read existing code before writing new code (`view` first, then write)
- Write tests before or alongside implementation
- Keep YAML schemas and Pydantic models in sync (CI enforces)
- Use `yao.ir.timing` for all tick/beat/second conversions
- Use `yao.ir.notation` for all note name/MIDI conversions
- Use `yao.ir.tuning` for all cents/microtonal conversions (★NEW)
- Derive velocity from dynamics curves (never hardcode)
- Register generators via `@register_generator("name")`
- Register critique rules via `@register_critique("rule_id")` (★NEW)
- Register subagents via `@register_subagent(AgentRole.X)` (★NEW)

**Provenance:**
- Every generation step records to `ProvenanceLog` — including Plan-level, Note-level, Performance-level, Mix-level, and Neural-call steps
- Neural generator calls record `model_version`, `prompt`, `seed`, `output_hash`, `rights_status`
- AI-disclosure metadata is stamped by `ai-disclosure-stamp` Hook on every render

**Testing:**
- Add to `tests/golden/` if output should be bit-exact stable
- Add to `tests/scenarios/` if a musical scenario should be verified
- Add to `tests/properties/` for genre invariants (★NEW)
- Add to `tests/subjective/ratings/` if you generated and listened to verify quality (★NEW)

**Documentation:**
- Update `FEATURE_STATUS.md` when adding/completing a feature (CI enforces via `make feature-status`)
- Update `PROJECT.md` only for design-level changes
- Update `VISION.md` only for roadmap or target-architecture changes
- Add ADRs (Architecture Decision Records) to `docs/design/NNNN-topic.md` for non-trivial design choices

## MUST NOTs

**Imports:**
- Import `pretty_midi` / `music21` / `librosa` / `pyloudnorm` / `pedalboard` outside their designated layers
- Import `torch` / `transformers` / `magenta` / `audiocraft` outside `src/yao/generators/neural/` (★NEW)
- Import `sounddevice` / `mido.ports` outside `src/yao/improvise/` and CLI preview/watch (★NEW)

**Code patterns:**
- Create functions with vague names (`make_it_sound_good`, `do_music_stuff`)
- Skip provenance recording for any generation step
- Use bare `ValueError` (use `YaOError` subclasses)
- Silently clamp notes to range (raise `RangeViolationError`)
- Mix `Beat` and `Tick` and `seconds` in the same function without explicit conversion
- Mix functional Roman numerals (`I`, `V7/V`) and concrete chords (`C`, `G7`) in the same field

**Music data:**
- Hardcode artist names or copyrighted melodies anywhere (skills, references, prompts)
- Add reference MIDI without `references/catalog.yaml` rights status (★STRICT)
- Bypass the `references.yaml` `forbidden_to_extract` allowlist (raw melody/chord copying is schema-blocked)
- Generate output without `ai-disclosure-stamp` Hook completing (★NEW)

**Workflow:**
- Leave `TODO` / `FIXME` uncommitted (file an Issue or resolve it)
- Skip `make all-checks` before pushing
- Force-push to main (use feature branches)

---

## 6 Design Principles (v2.0)

These are the absolute compass. When in doubt, return to these.

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform, humans decide
6. **Vertical alignment** — input expressivity, processing depth, evaluation resolution must advance together (★NEW v2.0)

For each PR, confirm at least one principle is advanced and **none is violated**.

---

## Architecture Reference (8 Layers)

```
Layer 7: Reflection & Learning      (reflect/, runtime/)
Layer 6: Verification & Critique    (verify/)
Layer 5: Rendering                  (render/, mix/)
Layer 4.5: Performance Expression   (ir/expression.py, generators/performance/) ★NEW
Layer 4: Perception Substitute      (perception/)
Layer 3.5: Musical Plan IR (MPIR)   (ir/plan/)
Layer 3: Score IR                   (ir/)
Layer 2: Generation Strategy        (generators/)
Layer 1: Specification              (schema/)
Layer 0: Constants                  (constants/)
```

**Dependency rule**: each layer can only depend on layers **below** it. Conductor is allowed to import any layer but must not be imported by anything below itself.

**MPIR is the heart**: Plan generators (Steps 1-5) produce MPIR. Critic Gate operates on MPIR. Note Realizer (Step 6) consumes MPIR and produces ScoreIR. Performance Realizer (Step 6.5) augments ScoreIR with PerformanceLayer. Mix Designer (Step 7) produces ProductionManifest.

When adding a module, **first decide its layer**, then place in the correct directory. Use `architecture-lint` to verify.

---

## Current Phase

**Phase β** (in progress) → **Phase γ** (next)

**What EXISTS** (Phase α + early β complete):
- 7-layer architecture (v1.0) with strict AST lint ✅
- Spec loading + validation (Pydantic v1+v2) ✅
- Score IR (Note, Part, Section, Motif, Voicing, Harmony) ✅
- MPIR (SongFormPlan, HarmonyPlan, MotifPlan, PhrasePlan, DrumPattern, ArrangementPlan) ✅
- Rule-based + stochastic generators ✅
- Drum patterner (8 genres) + counter-melody ✅
- Generator registry ✅
- Constraint system with scopes ✅
- MIDI rendering + stems + audio (FluidSynth) ✅
- MIDI reader (round-trip) ✅
- 5-dimensional trajectory + multi-dim coupling ✅
- Music linting, analysis, evaluator (10 metrics, 3 dims) ✅
- Critique rules (15 across 6 categories) ✅
- Score diff with modified note tracking ✅
- Provenance logging (append-only, queryable) ✅
- Conductor feedback loop with critic integration ✅
- Section-level regeneration ✅
- CLI (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section, preview, watch) ✅
- 7 Claude Code commands + 7 subagent definitions (.md only) ✅
- 11 Skills (8 genres + 3 other) ✅
- Architecture lint, feature-status check, golden tests ✅
- Pre-commit hooks + GitHub Actions CI ✅

**What is BEING BUILT in v2.0** (Phase β/γ):

### Tier 1 — Quick Wins (current sprint)
- [ ] **Layer 4.5: Performance Expression IR** (`src/yao/ir/expression.py`)
- [ ] **Markov generator** (registered alongside stochastic)
- [ ] **Constraint solver generator** (using `python-constraint` or OR-tools)
- [ ] **Audio Perception Stage 1** (`librosa` + `pyloudnorm` features → `PerceptualReport`)
- [ ] **Production Manifest + mix chain** (`src/yao/mix/` with `pedalboard`)
- [ ] **MusicXML writer** (`music21` based)
- [ ] **LilyPond writer** (CLI via subprocess)
- [ ] **Genre Skills expansion** (8 → 16: rock_classic, jazz_swing, edm_house, baroque, blues, funk, ambient_drone, anime_bgm)

### Tier 2 — Differentiation (next 1-3 months)
- [ ] **Arrangement Engine MVP** (`src/yao/arrange/`)
- [ ] **Performance Realizers** (4 subtypes)
- [ ] **Use-Case Targeted Evaluators** (YouTubeBGM, GameBGM, Advertisement, StudyFocus)
- [ ] **Reference Matcher** (StyleVector with copyright-safe feature extraction)
- [ ] **Subagent Python implementations** (7 classes implementing `SubagentBase`)
- [ ] **Multi-candidate Orchestrator** (5-10 parallel MPIR generation + critic ranking)
- [ ] **Critique rule expansion** (15 → 50+, including memorability/genre_fitness/performance/mix)

### Tier 3 — Diversity & Identity (3-6 months)
- [ ] **Microtonal scale support** (cents-based ScaleDefinition + MPE MIDI output)
- [ ] **Extended TimeSignatures** (compound meters, polymeter, beat groupings)
- [ ] **Algorithmic paradigm generators** (twelve_tone, spectral, process_music, l_system, cellular_automata)
- [ ] **Neural generator bridges** (Stable Audio for textures, MusicGen, Magenta — all optional dependencies)
- [ ] **Project Runtime** (stateful session with cache/undo/redo)
- [ ] **Live Improvisation engine** (real-time MIDI in/out + accompanist roles)
- [ ] **DAW project writers** (Reaper RPP, Ableton ALS)

### Tier 4 — Platform Maturity (continuous)
- [ ] **Genre Skills 30+** with cultural categories (world/, functional/)
- [ ] **Annotation UI** (`yao annotate` browser-based time-tagged feedback)
- [ ] **Reflection Layer** (UserStyleProfile, cross-project pattern mining)
- [ ] **Backend-Agnostic Agent Protocol** (Claude Code adapter + Anthropic API + Local LLM + PythonOnly)
- [ ] **DAW MCP Integration** (Reaper-first)
- [ ] **Subjective Quality Test Suite** (`tests/subjective/`)
- [ ] **Property-based tests** (genre invariants, trajectory compliance)
- [ ] **Strudel emitter** (browser-side instant audition)

When picking up work, choose the highest-tier item that aligns with the current sprint focus.

---

## Tier-Specific Implementation Rules

### Tier 1 Rules

**Performance Expression IR (Layer 4.5)**:
- `NoteExpression` is a frozen dataclass; never mutate
- `PerformanceLayer` overlays on ScoreIR; never modifies ScoreIR
- All CC/pitch-bend curves must respect MIDI 1.0 spec (CC range 0-127, pitch bend range -8192 to +8191)
- For MPE output, use `MidiWriter(mode="mpe")`; never duplicate channel assignment logic

**Markov / Constraint Solver Generators**:
- Register via `@register_generator("markov")` / `@register_generator("constraint_satisfaction")`
- Same `(ScoreIR, ProvenanceLog)` return contract as existing generators
- Markov n-gram tables in `src/yao/generators/markov_models/` are configuration data, not code; load lazily
- Constraint solver must time-bound (default 5 seconds); on timeout raise `GenerationTimeoutError`

**Audio Perception (Stage 1)**:
- All `librosa` calls live in `src/yao/perception/audio_features.py`
- Sample rate handling: always pass through `librosa.load(..., sr=None)` to preserve original; downsample only inside extraction functions
- LUFS measurements must use `pyloudnorm.Meter`, never approximate via RMS
- `PerceptualReport` is frozen; one analysis = one report

**Production / Mix Chain**:
- All `pedalboard` calls live in `src/yao/mix/`
- Master chain caps at -1.0 dBFS true-peak (configurable but warn if exceeded)
- Use `pyloudnorm.normalize.loudness` for LUFS targeting; never custom RMS-based normalization
- ProductionManifest is fully derivable from spec + ScoreIR; the user can override but defaults must be sensible

**MusicXML / LilyPond Writers**:
- MusicXML uses `music21.converter`; respect MusicXML 4.0 spec
- LilyPond writer shells out to `lilypond` binary via subprocess; warn-and-skip if not installed (do not hard-fail)
- Output goes under `outputs/.../score.musicxml` / `score.pdf` / `score.ly`

### Tier 2 Rules

**Arrangement Engine**:
- `SourcePlan` extracted from MIDI is **best-effort**; document confidence per layer (form/harmony/motif/role)
- `arrangement.yaml` MUST have `rights_status` field; missing → `MissingRightsStatusError`
- `Preservation contract` violations (e.g., melody similarity < threshold) trigger findings, not silent acceptance
- `Arrangement Diff` markdown is required output; if generation succeeds but diff fails to write, treat as failure
- Style vector ops: `target = source - source_genre + target_genre ⊕ preservation` is the only formula; document any deviation

**Performance Realizers**:
- Run order: Articulation → Dynamics Curve → Microtiming → CC Curves
- Each realizer is independent and idempotent; running twice produces same output
- Articulation defaults from `.claude/skills/articulation/<instrument>.md`
- Microtiming profiles from `.claude/skills/articulation/<genre>-microtiming.md`

**Use-Case Targeted Evaluators**:
- Each `UseCase` enum value has exactly one evaluator class
- Evaluators take `PerceptualReport` and `IntentSpec` as input
- Output dict[str, float] with documented score keys; do not invent ad-hoc keys
- Score in [0.0, 1.0]; values outside this range raise `EvaluatorError`

**Reference Matcher**:
- `StyleVector` extraction uses ONLY abstract features; concrete melody/chord extraction is forbidden by schema and must also raise at runtime if attempted
- `references.yaml` `forbidden_to_extract` is enforced even if user removes it from spec (defense in depth)
- Reference cache files in `references/extracted_features/` are content-addressed (`sha256` of source MIDI)

**Subagent Python Implementations**:
- All inherit `SubagentBase`
- All declare `role: AgentRole`
- All return `AgentOutput` containing the appropriate plan/score/findings + `ProvenanceLog`
- Tests live in `tests/unit/subagents/test_<role>.py`
- Producer is the only one who can call `override_other_subagent()`; this is a method on `ProducerSubagent` only

**Multi-Candidate Orchestrator**:
- Default candidates = 5; configurable up to 10
- Each candidate uses a different seed; provenance records all candidate seeds
- Critic ranks by **weighted severity sum** (critical=10, major=3, minor=1, suggestion=0)
- Producer either picks top1 or merges if `_candidates_complementary()` returns True
- Merging is deterministic given (candidates, producer_strategy_seed)

### Tier 3 Rules

**Microtonal Scale Support**:
- All scales declare `intervals_cents: tuple[int, ...]` in addition to existing semitone-based form
- 12-EDO scales have `intervals_cents = tuple(s * 100 for s in semitones)` for backwards compatibility
- MIDI 1.0 output: pitch bend approximation only; warn user that ±50 cent precision is the limit per channel
- MPE MIDI output: each note gets independent channel + pitch bend (channels 2-16)
- `MidiWriter(mode="mpe")` is opt-in; default remains `per_instrument` for backwards compatibility

**Extended Time Signatures**:
- `TimeSignatureSpec` Pydantic model; `time_signature` field accepts string OR object
- `beat_groupings` must sum to numerator (e.g., `[3, 2, 2]` requires `7/8`)
- Polymeter: layouts with different sigs require `sync_at` to be specified; otherwise schema error
- Generators must check `time_signature.is_compound()` and adapt; no hardcoded "4/4" assumptions

**Neural Generator Bridges**:
- All neural generators live in `src/yao/generators/neural/`
- ALL imports of `torch` / `transformers` / `magenta` / `audiocraft` happen inside these modules
- Each bridge MUST handle `ImportError` gracefully and raise `NeuralBackendUnavailableError` with install instructions
- All neural generation MUST record:
  - `model_version` (from package metadata)
  - `prompt` (as sent to model)
  - `seed`
  - `output_hash` (sha256 of generated content)
  - `rights_status` (`user_owned` / `model_license_<name>` / `unknown`)
- `unknown` rights_status → emit warning; do not silently proceed
- Neural calls have a default timeout (60s for texture, 30s for melody); raise `NeuralGenerationTimeoutError`

**Project Runtime**:
- `ProjectRuntime` is a context manager; `with ProjectRuntime("my-song") as rt: ...`
- Generation cache keys are `(spec_hash, seed, generator_name)` tuples
- Undo stack capped at 50; redo cleared on new edit
- Concurrent access to a single project is not supported; runtime takes a lockfile

**Live Improvisation**:
- All real-time code must specify max latency budget (default 50ms input → output)
- MIDI port handling via `mido` only (no platform-specific libs)
- Context buffer is fixed-size ring buffer; do not grow unbounded
- Improvisation does not write to disk during session; export is explicit

### Tier 4 Rules

**Genre Skills (30+)**:
- Markdown body + YAML front-matter; `make sync-skills` enforces consistency
- World genre Skills (Hindustani, Maqam, Gamelan, etc.) require `cultural_context` field
- Cultural context Skills must include `forbidden_in_pure_form` and `allowed_relaxations` keys
- New world genre PRs require Issue with subject matter expert review note (cannot self-merge)

**Annotation UI**:
- `yao annotate` launches local FastAPI/HTML; no external services
- Annotations stored as `outputs/.../iterations/<v>/annotations.json`
- Annotation schema validated via Pydantic; malformed file → recoverable error with skip option

**Reflection Layer**:
- `UserStyleProfile` is per-user (default: single local user)
- Profile updates are explicit (`yao reflect ingest <annotations>`); never automatic mid-session
- Profile influence on generation is opt-in via spec field `style_profile.use: true`

**Backend-Agnostic Agent Protocol**:
- `AgentBackend` protocol is read-only contract; backends implement it
- Default backend = `ClaudeCodeBackend` (when running in Claude Code)
- `PythonOnlyBackend` is REQUIRED for CI; tests must work without LLM access
- Backend selection via env var `YAO_AGENT_BACKEND` or programmatic config

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization:

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py`, `test_timing.py` | `make test-unit` |
| Cents/microtonal arithmetic error | `test_tuning.py` (★NEW) | `make test-unit` |
| Range violation silence | `RangeViolationError` (no silent clamp) | `make test` |
| Velocity hardcode | `ruff` custom rule + code review pattern | `make lint` |
| Missing provenance | `GeneratorBase.generate()` enforces return type | `mypy` |
| Layer boundary breach (8 layers) | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test-integration` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| MPIR contract violation | `test_plan_contracts.py` (★NEW) | `make test-unit` |
| Subagent contract violation | `test_subagent_contracts.py` (★NEW) | `make test-unit` |
| FEATURE_STATUS drift | `tools/feature_status_check.py` | `make feature-status` |
| Doc drift (PROJECT/VISION/STATUS) | `tools/sync_docs.py` (★NEW) | `make sync-docs` |
| Skill markdown/yaml drift | `tools/sync_skills.py` | `make sync-skills` |
| Neural call without provenance | Unit test asserting provenance fields ★NEW | `make test-unit` |
| AI-disclosure missing | `ai-disclosure-stamp` Hook + render-time check | `make test-integration` |
| Copyright extraction breach | `references.yaml` schema validator + runtime guard ★NEW | `make test` |

---

## Performance Expectations

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Generate 8-bar piece (rule_based) | <1s | Deterministic |
| Generate 8-bar piece (stochastic) | <1s | Deterministic given seed |
| Generate 8-bar piece (markov) | <2s | ★NEW |
| Generate 8-bar piece (constraint_satisfaction) | <5s | ★NEW; timeout at 5s |
| Generate 64-bar piece (any non-neural) | <5s | Stochastic may vary |
| Generate via neural texture (Stable Audio) | <60s | ★NEW; CPU mode allowed but slow |
| Plan critic gate (15 rules) | <500ms | Existing |
| Plan critic gate (50+ rules) | <2s | ★NEW target |
| Multi-candidate generation (5 parallel) | <15s | ★NEW; uses `concurrent.futures` |
| Audio feature extraction (90s WAV) | <3s | ★NEW; librosa + pyloudnorm |
| Use-case evaluator | <500ms | ★NEW |
| Reference style vector extraction | <2s | ★NEW; cached after first run |
| Mix chain (90s, 5 stems) | <10s | ★NEW; pedalboard offline render |
| MusicXML write | <1s | ★NEW |
| LilyPond render to PDF | <30s | ★NEW; via subprocess |
| Write MIDI file | <200ms | pretty_midi |
| Run full lint | <500ms | All lint rules |
| Run all unit tests | <10s | ~700+ tests target (★NEW from 643) |
| Run all tests including subjective | <30s | ★NEW |
| Architecture lint | <2s | AST parsing for 8 layers |

Do not introduce changes that exceed these budgets without discussion. Add a `pytest.mark.slow` marker if a test legitimately takes longer.

---

## Common Failure Patterns to Watch For

These are pitfalls observed during v1.0 development. v2.0 development should avoid them deliberately.

### F1: "Just one more conditional" in generators
When a generator gets new behavior, the temptation is to add `if temperature > 0.7 elif ...` branches. Resist. Extract to a strategy pattern or a new generator class.

### F2: MPIR-Score divergence
After implementing Performance Layer, the MPIR-ScoreIR-Performance chain has 3 representations of the same musical idea. Always update Provenance to track which representation owns which decision.

### F3: Layer 4.5 leaking into Layer 3
Performance expression (CC curves, microtiming) should NOT modify ScoreIR. They overlay. If you find yourself mutating Note objects to add expression, stop and add to PerformanceLayer instead.

### F4: Neural calls hidden in synchronous code
Neural generation can take 60+ seconds. Never block the user thread. Either:
- Run in CLI as a separate command with progress
- Use `asyncio` if part of an async pipeline
- Cache aggressively (hash spec → cached result)

### F5: Microtonal scale assumed semitone
After adding cents-based scales, code that assumes `pitch_class = midi_note % 12` will break. Use `Tuning.cents_from_a4(pitch)` consistently.

### F6: Cultural insensitivity by omission
Adding "Indian Classical Skill" with only Western terminology is a cultural failure. Always:
- Use original culture's term (raga, tala, maqam, makam, dastgah)
- Reference scholarly sources, not pop summaries
- Note which traditions are being mixed (pure vs. fusion)

### F7: Silent capability drift
You add a feature but forget to update FEATURE_STATUS.md. Two months later, README claims a capability that isn't real. **Always run `make feature-status` before merge.**

### F8: Subagent definition drift
You update `.claude/agents/composer.md` but forget the Python `ComposerSubagent`. Or vice versa. Both must change in lockstep. CI runs `tests/subagents/test_dual_consistency.py`.

### F9: References used as input training data
A user adds `references/midi/popular_song.mid` for "style transfer." Without explicit license, this is copyright theft. **Schema validation must require `rights_status` and reject `unknown`.**

### F10: Provenance entry without rationale
A provenance entry that says "added note" without WHY is useless. Every entry has a `rationale` field; if you cannot fill it, the operation should not happen.

---

## Recent Changes (most recent first)

- **2026-05-02 (PROJECT.md v2.0 alignment)**: 8-layer architecture, Layer 4.5 introduced, 6th principle (Vertical Alignment), Tier 1-4 roadmap formalized, microtonal/MPIR/Arrangement Engine/Neural integration scoped, this CLAUDE.md restructured to v2.0
- **2026-04-30**: FEATURE_STATUS.md as single source of truth; capability matrix discipline
- **2026-04-29**: MIDI reader, section regeneration (Conductor + CLI), evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff
- **2026-04-28**: Stochastic generator, generator registry, queryable provenance
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI
- **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md

---

## Escalation

Stop and ask the human when:

- **Music theory judgment** — you're unsure if a progression is "voice-leading clean" or stylistically appropriate
- **Cultural sensitivity** — adding world genre Skills, reviewing translations, naming conventions
- **Copyright / rights** — adding any reference material; integrating any neural model
- **Architectural boundaries** — proposing a layer change, adding a new layer, or breaking an existing boundary
- **Adding new external dependencies** — especially heavyweight (torch, magenta, vst3 hosts)
- **Deleting files or rewriting git history**
- **Any change touching 5+ files in different layers**
- **Changes that would require updating PROJECT.md or VISION.md**
- **Performance regressions** that exceed the budgets in this file
- **Subjective quality evaluation** — when you've generated music and want a human ear to verify before merging
- **Neural model selection** — choosing which Stable Audio version, MusicGen size, etc.

The human is the conductor; you are a subagent yourself when developing YaO. Defer when uncertain.

---

## Workflow for Adding a v2.0 Feature

A typical feature implementation cycle:

1. **Read context**: PROJECT.md section relevant to the feature, VISION.md if it's a target architecture piece, FEATURE_STATUS.md for current state
2. **Find the layer**: which of Layer 0-7 does this belong to? (often layer 3.5 or 4.5 for v2.0 features)
3. **Find the existing pattern**: similar feature already implemented? (e.g., new generator → check `rule_based.py` and `stochastic.py`)
4. **Design the contract**: type signatures, ProvenanceLog fields, error types
5. **Write tests first** (unit + integration if appropriate)
6. **Implement** (minimum to pass tests)
7. **Update FEATURE_STATUS.md** (move from ⚪ to 🟡, then 🟢, then ✅ with tests)
8. **Update Skills if applicable** (`.claude/skills/...`)
9. **Update Subagent definitions if applicable** (`.claude/agents/...` AND `src/yao/subagents/...`)
10. **Run `make all-checks`**
11. **Generate sample music to verify** (Sound-First culture)
12. **Open PR** with: What/Why/How/Music impact/Tests/Vertical alignment statement

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| [Architecture](./.claude/guides/architecture.md) | Working across layers, adding modules, Layer 4.5 design |
| [Coding Conventions](./.claude/guides/coding-conventions.md) | Writing any code |
| [Music Engineering](./.claude/guides/music-engineering.md) | Generating/modifying notes, MPIR, microtonal |
| [Testing](./.claude/guides/testing.md) | Writing or running tests, subjective testing setup |
| [Workflow](./.claude/guides/workflow.md) | Planning a change |
| [Cultural Sensitivity](./.claude/guides/cultural-sensitivity.md) | Adding world genres, translations, ethics |
| [Subagent Implementation](./.claude/guides/subagents.md) | ★NEW — Implementing Python Subagents that mirror .md prompts |
| [Performance Layer](./.claude/guides/performance-layer.md) | ★NEW — Layer 4.5 design and CC curve generation |
| [Arrangement Engine](./.claude/guides/arrangement.md) | ★NEW — MIDI extraction, style vector ops |
| [Neural Integration](./.claude/guides/neural.md) | ★NEW — Bridging to Magenta/MusicGen/Stable Audio |

Full design documentation: [PROJECT.md](./PROJECT.md)
Target architecture: [VISION.md](./VISION.md)
Capability matrix: [FEATURE_STATUS.md](./FEATURE_STATUS.md)

---

## When in Doubt

Ask these questions, in order:

1. **Which of the 6 principles does this advance?** If none, reconsider.
2. **Which of input/processing/evaluation does this advance?** If only one, why isn't it paired?
3. **Which layer does this belong to?** Place it correctly.
4. **What is the contract?** Inputs, outputs, errors, provenance fields.
5. **What is the test?** Unit, integration, scenario, subjective?
6. **What does FEATURE_STATUS.md say after this lands?**
7. **Has the human asked for this, or am I scope-creeping?**

If you cannot answer any of these clearly, **stop and escalate**.

---

> *Build the orchestra well, so the conductor can lead it freely.*
> *— and remember: you are building infrastructure for an orchestra that will make music in 30+ genres, in any tuning system, in any culture, for any use case. Build accordingly.*

**CLAUDE.md version: 2.0**
**Last updated: 2026-05-02**
**Aligned with: PROJECT.md v2.0**
