# CLAUDE.md — YaO Core Rules

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > IMPROVEMENT.md > other docs.*

> **Version 3.0**: this file extends the v2.1 rules with the **Combination Stack** (Layer 2.5) introduced in `IMPROVEMENT.md`. The current development phase is **Phase 3.5: Diversity Foundation** — chord-aware melody, voice-leading optimizer, and reharmonization engine. Two new non-negotiable rules (8 and 9) and an additional design principle (8) make harmonic coupling and combination-driven diversity architecturally enforced rather than optional.

---

## Quick Reference

```
make test           # Run all tests
make lint           # ruff + mypy strict
make arch-lint      # Layer boundary check (AST-based, now covers Layer 2.5)
make all-checks     # lint + arch-lint + test
make format         # Auto-format code
make test-melody    # Unit tests for the phrase-first melody pipeline
make test-coupling  # NEW: unit tests for the Combination Stack (Layer 2.5)
make test-genres    # Genre-specific scenario tests
make test-golden    # Snapshot tests of canonical outputs
make test-diversity # NEW: same-spec/different-seed diversity scenarios
make profile-perf   # Verify generation stays within performance budget
make markov-validate     # NEW: validate all Markov YAML models
make device-validate     # NEW: validate harmonic-device YAMLs
make gesture-validate    # NEW: validate idiomatic-gesture YAMLs
```

**Key directories:**

```
src/yao/constants/                   → Hardcoded values (ranges, scales, MIDI)
src/yao/constants/melodic_profiles/  → 30+ genre profile YAMLs
src/yao/constants/rhythms/           → 30+ rhythm template YAMLs
src/yao/constants/grooves.py         → GrooveProfile presets
src/yao/constants/harmonic_devices/  → NEW (15+ YAMLs)
src/yao/constants/idiomatic_gestures/ → NEW (15+ YAMLs)
src/yao/schema/                      → Pydantic models for YAML specs
src/yao/schema/melodic_profile.py    → MelodicProfile schema (v3.0 fields added)
src/yao/schema/genre_blend.py        → NEW (genre blend YAML schema)
src/yao/schema/features.py           → NEW (feature flags schema)
src/yao/ir/                          → Core data types
src/yao/ir/phrase.py                 → Phrase, PhrasePlan, Cadence
src/yao/ir/skeleton.py               → Skeleton, SkeletonNote
src/yao/ir/melody_line.py            → MelodyLine, MelodyNote, OrnamentedNote
src/yao/ir/harmonic_context.py       → HarmonicContext
src/yao/ir/harmonic_melody_constraints.py → NEW
src/yao/ir/phrase_shape.py           → NEW
src/yao/ir/theme_recurrence.py       → NEW
src/yao/ir/genre_vector.py           → NEW
src/yao/ir/polyrhythm.py             → NEW
src/yao/ir/rhythm_event.py           → NEW (functional rhythm labels)
src/yao/coupling/                    → NEW Layer 2.5 modules
src/yao/coupling/harmonic_melody.py  → §4.1 derive_constraints
src/yao/coupling/voice_leading.py    → §5.4 optimal_voicing_transition
src/yao/coupling/reharmonization.py  → §5.1 reharmonize
src/yao/coupling/modulation.py       → §5.2 ModulationPlanner
src/yao/coupling/genre_vector.py     → §6.1 blend_n_way
src/yao/coupling/rhythm_markov.py    → §3.1 RhythmMarkovGenerator
src/yao/coupling/polyrhythm.py       → §3.2 PolyrhythmComposer
src/yao/coupling/theme_recurrence.py → §6.4 plan_theme_recurrences
src/yao/coupling/phrase_shape.py     → §4.3 PhraseShapeGenerator
src/yao/coupling/listening_dialog.py → §6.3 turn-based generation
src/yao/coupling/idiomatic_gestures.py → §4.4 apply_gestures
src/yao/generators/                  → Composition algorithms
src/yao/generators/melody/           → 4-layer phrase-first pipeline (M1–M4)
src/yao/generators/markov_models/    → 2 → 30+ models
src/yao/generators/markov_models/pitch/   → 15+ pitch models (v3.0)
src/yao/generators/markov_models/rhythm/  → 12+ rhythm models (NEW)
src/yao/generators/markov_models/contour/ → 3+ contour models (NEW)
src/yao/conductor/                   → Orchestration + intent parsing
src/yao/render/                      → Output (MIDI, audio, stems, score)
src/yao/verify/                      → Analysis, lint, evaluation, diff
src/yao/verify/genre_critic.py       → Genre-specific anti-pattern checker
src/yao/verify/conformity.py         → KL divergence, motif coherence
src/yao/verify/melody_harmony_alignment.py → NEW (v3.0 metric)
src/yao/verify/voice_leading_smoothness.py → NEW (v3.0 metric)
src/yao/verify/polyrhythm_coherence.py → NEW (v3.0 metric)
src/yao/reflect/                     → Provenance tracking
src/yao/errors.py                    → Custom exception hierarchy
.claude/skills/genres/               → 30+ paired md/yaml genre Skills
.claude/skills/theory/reharmonization.md  → NEW
.claude/skills/theory/modulation.md  → NEW
.claude/skills/instruments/idiomatic-gestures.md → NEW
.claude/guides/                      → Developer guides
.claude/guides/combination-stack.md  → NEW
.claude/guides/chord-aware-melody.md → NEW
.claude/guides/voice-leading-optimizer.md → NEW
.claude/guides/reharmonization-engine.md → NEW
.claude/guides/genre-vector-space.md → NEW
.claude/guides/rhythm-markov.md      → NEW
.claude/guides/listening-agents.md   → NEW
references/motifs/                   → Reusable motif library
tools/extract_groove.py              → NEW
tools/learn_markov_from_corpus.py    → NEW
```

**Key types:**

```
Note                          → src/yao/ir/note.py
ScoreIR                       → src/yao/ir/score_ir.py
CompositionSpec               → src/yao/schema/composition.py
ProvenanceLog                 → src/yao/reflect/provenance.py
GeneratorBase                 → src/yao/generators/base.py
Phrase, PhrasePlan            → src/yao/ir/phrase.py
Skeleton                      → src/yao/ir/skeleton.py
MelodyLine                    → src/yao/ir/melody_line.py
HarmonicContext               → src/yao/ir/harmonic_context.py
MelodicProfile                → src/yao/schema/melodic_profile.py
GrooveProfile                 → src/yao/constants/grooves.py
StructuredIntent              → src/yao/conductor/intent_parser.py
GenreCritic                   → src/yao/verify/genre_critic.py
HarmonicMelodyConstraints     → src/yao/ir/harmonic_melody_constraints.py    (NEW)
CouplingStyle                 → src/yao/ir/harmonic_melody_constraints.py    (NEW)
VoicingConstraints            → src/yao/ir/voicing.py                         (extended)
ReharmonizationOperation      → src/yao/coupling/reharmonization.py           (NEW)
ModulationStrategy            → src/yao/coupling/modulation.py                (NEW)
GenreVector                   → src/yao/ir/genre_vector.py                    (NEW)
PhraseShape                   → src/yao/ir/phrase_shape.py                    (NEW)
ThemeRecurrence               → src/yao/ir/theme_recurrence.py                (NEW)
ThemeRecurrenceGraph          → src/yao/ir/theme_recurrence.py                (NEW)
RhythmEvent (with function)   → src/yao/ir/rhythm_event.py                    (NEW)
PolyrhythmLayer               → src/yao/ir/polyrhythm.py                      (NEW)
PolyrhythmTexture             → src/yao/ir/polyrhythm.py                      (NEW)
HarmonicDevice                → src/yao/ir/harmonic_devices.py                (NEW)
IdiomaticGesture              → src/yao/ir/idiomatic_gestures.py              (NEW)
ListeningGenerator            → src/yao/coupling/listening_dialog.py          (NEW)
RhythmicDialogGraph           → src/yao/coupling/listening_dialog.py          (NEW)
FeatureFlags                  → src/yao/schema/features.py                    (NEW)
```

---

## Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that subagents will use. Your code enables reproducible, auditable, iterable music creation.

The current development effort is **Phase 3.5: Diversity Foundation**. The v2.x melody pipeline is complete and stable. Your job is to add the **Combination Stack** (Layer 2.5) on top of it, starting with the three highest-impact modules: chord-aware melody, voice-leading optimization, and reharmonization. The existing `phrase_aware`, `rule_based`, `stochastic`, and `markov` generators continue to work without modification.

**The single most important rule of v3.0**: never break existing generators while adding the Combination Stack. The new modules must be feature-flag-gated and additive. If a refactor would touch the existing generators, stop and propose a specific plan to the human first.

---

## 9 Non-Negotiable Rules

The first five are foundational. Rules 6 and 7 were added when the phrase-first pipeline became core. Rules 8 and 9 are added in v3.0 for the Combination Stack.

1. **Never break layer boundaries** — see `.claude/guides/architecture.md`. Layer 2.5 (`src/yao/coupling/`) may import from Layers 0–2 only.
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`** — including new Coupling Stack functions, which return `(<TransformedIR>, ProvenanceLog)`.
3. **No silent fallbacks** — constraint violations must be explicit errors. This applies to coupling-style mismatches, modulation infeasibility, and Markov-model load failures.
4. **No hardcoded musical values** — use `src/yao/constants/`. New rule: no hardcoded chord-tone weights, voice-leading penalties, or Markov temperatures in coupling code; they come from the active `MelodicProfile` or constants.
5. **No public function without type hints and docstring**.
6. **The melody pipeline is monolithically four-layer** — never bypass M1–M4 ordering, never let M3 run without M2's skeleton, never call M2 without M1's phrase plan. **v3.0 amendment**: M2 must consult `HarmonicMelodyConstraints` from the Coupling Layer when `features.chord_aware_melody=true`.
7. **Genre is a `MelodicProfile`, not a string** — never hard-code genre-specific logic in generators; always parameterize via the loaded profile. **v3.0 amendment**: when `genre_blend` is specified, the resulting `GenreVector` is projected to a synthesized profile; downstream code consumes the profile, not the blend specification.
8. **Melody must be coupled to harmony** *(NEW)* — once `features.chord_aware_melody=true` (which is the default), no melody-pitch decision in M2 may proceed without scoring against `HarmonicMelodyConstraints` for the active chord. The `score_pitch()` result must be combined with the genre profile's `chord_tone_targeting` weight. Bypassing this is a build-failing arch-lint violation.
9. **The Combination Stack is feature-flagged and additive** *(NEW)* — every new module in `src/yao/coupling/` checks the relevant flag in `composition.features` and returns the input unchanged when disabled. No coupling module mutates its inputs; all return new IR objects with full provenance.

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

### Phrase-First Pipeline (unchanged from v2.x)
- The `phrase_aware` generator must invoke layers in order: M1 → M2 → M3 → M4
- Each layer records provenance with its specific layer tag
- Layer M2 must consult `HarmonicContext` for every skeleton note
- Layer M3 may only place pitches that connect existing skeleton notes
- Layer M4 microtiming offsets must come from a registered `GrooveProfile`
- All four layers must be unit-tested independently

### Combination Stack *(NEW v3.0)*

#### Chord-Aware Melody (§4.1)
- `derive_constraints(chord, key, profile, style)` runs once per `ChordEvent`; results are cached for the duration of the generation pass
- `HarmonicMelodyConstraints.score_pitch()` returns `0.0` (clash) to `1.0` (excellent fit). Never return values outside this range.
- The `CouplingStyle` is selected from `MelodicProfile.coupling_style`, never hard-coded in M2
- M2 combines `score_pitch()` with `profile.chord_tone_targeting` per the formula in `.claude/guides/chord-aware-melody.md`
- Provenance entry: `layer="M2_skeleton"`, `decision="select_target_pitch_with_constraints"`, including the constraints' `chord_tones`, `available_extensions`, and `avoid_notes`

#### Voice-Leading Optimization (§5.4)
- `optimal_voicing_transition(prev, next_chord, voice_count, constraints)` is the single entry point — never write ad-hoc voicing code
- Voice count comes from `MelodicProfile.voicing_density_target`, not from inline literals
- The Hungarian assignment must be deterministic for a given input (consistent tie-breaking)
- Provenance entry: per-chord `layer="orchestrator"`, `decision="optimize_voicing"`, including total motion in semitones

#### Reharmonization Engine (§5.1)
- All 12 operations live in `src/yao/coupling/reharmonization.py` as pure functions `(progression, position) → progression`
- Each operation has explicit applicability rules — operations that violate `ReharmonizationConstraints` (melody compatibility) are filtered before application, not after
- The `intensity` parameter is a probability scaling factor, not a count
- Provenance entry per operation: `layer="reharmonization"`, includes `original_chord`, `new_chord`, `operation`, `melody_compatibility_passed`

#### Modulation Generator (§5.2)
- `ModulationPlanner` is a subagent; its output is a `ModulationPlan` consumed by `HarmonyTheorist`
- All 7 strategies live in `src/yao/coupling/modulation.py`
- Modulation distances and preferences come from `MelodicProfile.modulation_preferences`
- Voice leading at modulation points is checked by §5.4 — modulation never overrides voice-leading optimization

#### Genre Vector Space (§6.1)
- `GenreVector.blend(*weighted)` is the single n-way blend entry point
- `blend_profiles(primary, secondary, ratio)` from v2.x continues to work — it is implemented internally as `GenreVector.blend((primary, ratio), (secondary, 1 - ratio)).to_melodic_profile()`
- Discrete fields (`chord_palette`, `preferred_instruments`) use weighted random sampling with a seed; numeric fields interpolate linearly
- Provenance entry: `layer="genre_blend"`, includes `component_genres` dict and computed `coordinates`

#### Rhythm Markov Pipeline (§3.1)
- New rhythm models live in `src/yao/generators/markov_models/rhythm/*.yaml`
- All models declare `n_gram_order`, `resolution`, `source`, `license` in metadata
- The `RhythmMarkovGenerator` is invoked by Layer M3 when `MelodicProfile.rhythm_markov_model` is set; otherwise the static template path runs
- Smoothing (Katz back-off) is enabled when `n_gram_order ≥ 3`
- Provenance entry: `layer="M3_surface"`, includes `model_name`, `state_history`, sampled state

#### Polyrhythm Engine (§3.2)
- `PolyrhythmTexture` is generated only when `MelodicProfile.polyrhythm_default` is enabled or the section spec sets `polyrhythm: true`
- Layers' cycle lengths must be co-prime for the ratio to actually create polyrhythm; the engine warns when given non-co-prime lengths
- Phase shifts and interlocking patterns are documented in `.claude/skills/theory/polyrhythm.md`

#### Theme Recurrence Graph (§6.4)
- `plan_theme_recurrences(form, motifs)` is auto-generated from the song form when `features.theme_recurrence=true`
- The graph is consumed by Layer M1 to bias motif assignment toward planned recurrences
- The existing `recall_melody_from` field becomes one edge type; the graph is the superset

#### Listening-Agent Dialog (§6.3)
- Default OFF (`features.listening_agents=false`); only enable when explicitly requested
- When enabled, the generation order is `bass → drums → harmony → melody_primary → melody_secondary → fills`
- Each follower receives `ensemble_history` (other instruments' notes so far) as input
- The `RhythmicDialogGraph` IR records causal edges; provenance entries include `caused_by` for each derived note

#### Idiomatic Gestures (§4.4)
- Gestures live in `src/yao/constants/idiomatic_gestures/<instrument>.yaml`
- Each gesture declares `pattern`, `placement`, `probability_by_genre`, optional `physical_constraint`
- Layer M4 applies gestures with intensity from `MelodicProfile.idiomatic_gesture_intensity`
- A gesture is applied at most once per phrase unless its `repeatable: true`

### Genre Profiles
- Adding a new genre Skill requires four artifacts:
  1. Markdown file with required sections
  2. YAML companion producing a valid `MelodicProfile` *(now including v3.0 fields)*
  3. Reference catalog entry with verified license
  4. Scenario test
- Genre Skill Markdown must cite music-theoretical sources
- Genre profiles use the `MelodicProfile` Pydantic schema — never define ad-hoc dicts
- Anti-patterns must specify severity and a fix recipe

### Provenance
- Every generation step records provenance — no exceptions
- Every coupling step records provenance with `caused_by` linking to the input decisions
- Append-only — never delete or modify
- Each entry includes timestamp, layer, decision, input, output, rationale, agent

### Intent Parsing
- The intent parser produces a `StructuredIntent` with all 5 emotional dimensions populated
- `IntentToSpec` builds a complete `CompositionSpec` from a `StructuredIntent`
- Mode selection comes from the genre's `scale_preferences` weighted by emotional vector
- Genre candidates are ranked with confidence scores
- **v3.0**: when the description suggests genre fusion (e.g., "bossa with electronic elements"), `IntentToSpec` produces a `genre_blend` rather than a single `genre.primary`

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
- Replace the existing `rule_based` or `stochastic` generators

### Combination Stack *(NEW v3.0)*
- **Bypass `derive_constraints()` in M2 when `chord_aware_melody=true`** — this is the build-failing rule for v3.0
- **Mutate any input IR object inside a coupling module** — always return new IR
- **Apply reharmonization without checking `ReharmonizationConstraints`** — melody compatibility is mandatory
- **Hardcode coupling-style avoid-note rules** — load from style-specific constants
- **Generate notes inside Layer 2.5** — Layer 2.5 only transforms or constrains; raw note generation lives in Layer 2
- **Mix functional and free harmony in the same `HarmonicSystem`** — pick one and document it
- **Use a Markov model without checking its license / source attribution** — every model YAML must have valid metadata before loading
- **Run reharmonization that produces audibly worse melody–harmony alignment** — the engine itself must verify and report alignment delta
- **Enable `listening_agents=true` on a piece with > 4 instruments without a 60s timeout** — the turn-based path is computationally expensive
- **Add a coupling module without a corresponding ADR in `docs/design/00NN-*.md`** — the Combination Stack is architectural change; document it

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
- **NEW**: skip the new v3.0 critique categories (melody–harmony alignment, voice-leading violations, reharmonization clashes, genre-blend incoherence) — they are part of the standard Critic suite

### Conductor
- Run a Conductor adaptation that violates `CLAUDE.md` rules
- Loop forever — cap iterations, escalate to human after 5 attempts
- Adapt the spec by hardcoding values; always go through the spec schema

---

## 8 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity
2. **Explain everything** — every note has a provenance record
3. **Constraints liberate** — specs and rules are scaffolds, not cages
4. **Time-axis first** — design trajectory curves before notes
5. **Human ear is truth** — automated scores inform; humans decide
6. **Phrase before notes** — phrases have function, target pitch, cadence
7. **Genre is a constellation** — `MelodicProfile`, not a label
8. **Diversity through combination** *(NEW)* — the Combination Stack turns rich material into genuinely diverse output; adding mechanisms beats adding materials

---

## Current Phase

**Phase 3.5** — Diversity Foundation: chord-aware melody + voice-leading optimizer + reharmonization engine.

This is the **highest-leverage phase in the v3.0 roadmap**. Per `IMPROVEMENT.md`, §4.1 (chord-aware melody) alone is "the largest single quality win available to YaO." Phase 3.5 ships §4.1, §5.4, and §5.1 together because they are mutually reinforcing: §4.1 makes melodies fit chords, §5.4 makes chord transitions smooth, §5.1 enriches the chord progressions that §4.1 and §5.4 then handle.

**What EXISTS (from Phase 0–3):**

- All Phase 0–2 deliverables (see v2.1 history below)
- **Phase 3 deliverables** ✅:
  - `HarmonicMelodicSelector` — pitch selection coupled with `HarmonicContext`
  - `OutlineGenerator` — chord-progression-outlining skeleton strategy
  - All 13 motif transformations wired into `MotifDevelopmentPlanner`
  - Motif library persistence at `references/motifs/`
  - Motif coherence scoring integrated into evaluation

**What is being BUILT NOW (Phase 3.5):**

- **§4.1 Chord-Aware Melody Layer**:
  - `src/yao/ir/harmonic_melody_constraints.py` — `HarmonicMelodyConstraints`, `CouplingStyle` enum
  - `src/yao/coupling/harmonic_melody.py` — `derive_constraints(chord, key, profile, style)`
  - Wire-up in `src/yao/generators/melody/skeleton.py` — M2 calls `derive_constraints()` and combines with `chord_tone_targeting`
  - 5 `CouplingStyle` rule sets: `COMMON_PRACTICE`, `JAZZ`, `BLUES`, `MODAL`, `RAGA`/`MAQAM`
  - `features.chord_aware_melody` defaults to `true`
  - Acceptance: melody–harmony alignment ≥ 0.7 average across 32-bar pieces; on downbeats ≥ 0.85

- **§5.4 Voice-Leading Optimizer**:
  - `src/yao/coupling/voice_leading.py` — `optimal_voicing_transition()` using Hungarian assignment
  - `VoicingConstraints` extension in `src/yao/ir/voicing.py`
  - Wire-up in Orchestrator subagent
  - `features.voice_leading_optimization` defaults to `true`
  - Acceptance: voice-leading smoothness ≤ 1.5× theoretical minimum for `COMMON_PRACTICE`, ≤ 2.0× for `JAZZ`

- **§5.1 Reharmonization Engine**:
  - `src/yao/coupling/reharmonization.py` — 12 operations + `ReharmonizationConstraints`
  - `/reharmonize` slash command
  - `harmonic-devices.yaml` schema
  - `features.reharmonization` defaults to `false` (opt-in)
  - Acceptance: reharmonized output passes melody–harmony alignment threshold; original melody preserved bit-identically when `preserve_melody=true`

**What does NOT exist yet (Phase 4+):**

- Genre-specific Markov models beyond the existing 2 (Phase 4.0)
- Rhythm Markov pipeline (Phase 4.0)
- Modulation Planner (Phase 4.0)
- Harmonic Devices Library wired into generation (Phase 4.0)
- Phrase-Shape Generator (Phase 4.5)
- Theme Recurrence Graph (Phase 4.5)
- Variable Harmonic Rhythm (Phase 4.5)
- Genre Vector Space n-way blending (Phase 5.0)
- Idiomatic Gestures library (Phase 5.0)
- Polyrhythm Engine (Phase 5.0)
- Listening Agents (Phase 5.5)
- Corpus learning pipeline (Phase 5.5)
- Metric modulation (Phase 5.5)
- Microtonal melody pipeline (Phase 5.5)

---

## Phase 3.5 Implementation Plan

When working on Phase 3.5, follow this order. Each step is independently mergeable behind its feature flag.

### Step 1: HarmonicMelodyConstraints IR

1. Create `src/yao/ir/harmonic_melody_constraints.py`
2. Define `CouplingStyle` enum: `COMMON_PRACTICE`, `JAZZ`, `BLUES`, `MODAL`, `RAGA`, `MAQAM`
3. Define `HarmonicMelodyConstraints` frozen dataclass with `chord_tones`, `available_extensions`, `avoid_notes`, `target_resolutions`, `style`
4. Implement `score_pitch(pitch, position) -> float` (0.0–1.0)
5. Position labels: `DOWNBEAT`, `UPBEAT`, `OFFBEAT`, `APPROACH`
6. Unit tests covering all 5 styles + 4 positions + edge cases (chord-tone, extension, avoid-note, leading-tone resolution)

### Step 2: derive_constraints() Function

1. Create `src/yao/coupling/harmonic_melody.py`
2. Implement `derive_constraints(chord, key, scale_type, style) -> HarmonicMelodyConstraints`
3. Style-specific rules in `_rules.py` files:
   - `_rules_common_practice.py` — avoid P4 over major triad on strong beats, prefer 3rd/5th on downbeats
   - `_rules_jazz.py` — avoid 11 on dominant, prefer extensions on offbeats
   - `_rules_blues.py` — b3, b5, b7 are blue notes (neutral)
   - `_rules_modal.py` — no avoid notes
   - `_rules_raga.py` and `_rules_maqam.py` — defer to `TonalSystem.cadence_strength` and characteristic-pitch logic
4. Cache derived constraints per `(chord, key, scale_type, style)` tuple
5. Unit tests verifying each rule set produces the expected `score_pitch()` distribution

### Step 3: Wire-Up in M2

1. Modify `src/yao/generators/melody/skeleton.py`
2. In `SkeletonGenerator.generate()`, for each skeleton-note position:
   - Look up the active chord at that beat
   - Call `derive_constraints(chord, key, profile, profile.coupling_style)`
   - For each candidate pitch, compute `combined_score = profile.chord_tone_targeting * constraints.score_pitch(p, pos) + (1 - profile.chord_tone_targeting) * profile.interval_distribution[interval]`
   - Sample weighted by `combined_score`
3. Provenance entry per skeleton note with `chord`, `score`, `chord_relation`
4. Behavior gated on `composition.features.chord_aware_melody` (default `true`); when `false`, fall through to v2.x path
5. Integration test: generate a 32-bar piece, verify melody–harmony alignment ≥ 0.7

### Step 4: Voice-Leading Optimizer

1. Create `src/yao/coupling/voice_leading.py`
2. Implement `optimal_voicing_transition(prev_voicing, next_chord, voice_count, constraints) -> list[MidiNote]`
3. Algorithm:
   - Enumerate inversions of `next_chord` (all possible voicings within range)
   - For each candidate voicing, compute `total_motion = sum(abs(prev[i] - next[i]) for i in range(voice_count))`
   - Filter out voicings violating constraints (parallel 5ths/8ves, voice crossing, range violations, leaps > octave)
   - Return the minimum-motion candidate; deterministic tie-breaking by lowest top-voice note
4. `VoicingConstraints` schema in `src/yao/ir/voicing.py`
5. Wire-up in Orchestrator subagent for all harmonic instruments
6. Unit tests verifying: minimum motion is selected; constraint violations filter correctly; deterministic for given inputs

### Step 5: Reharmonization Engine

1. Create `src/yao/coupling/reharmonization.py`
2. Implement all 12 operations as pure functions
3. Implement `ReharmonizationConstraints` and `melody_compatible(melody, chord)` check
4. Implement `reharmonize(progression, operations, intensity, style, constraints) -> progression`
5. `/reharmonize` slash command in `.claude/commands/reharmonize.md`
6. `harmonic-devices.yaml` schema in `src/yao/schema/`
7. Acceptance: reharmonization improves harmonic complexity score by ≥ 0.2 without dropping melody–harmony alignment below 0.65

### Step 6: New Evaluation Metrics

1. Create `src/yao/verify/melody_harmony_alignment.py`
2. Create `src/yao/verify/voice_leading_smoothness.py`
3. Wire into `evaluator.py` — both metrics added to `evaluation.json` output
4. Critique rules in `genre_critic.py` triggering on out-of-range values

### Step 7: Diversity Scenario Tests

1. `tests/scenarios/test_chord_aware_melody.py`:
   - Same spec, with vs without `chord_aware_melody`
   - Assert: alignment_with > alignment_without + 0.15
2. `tests/scenarios/test_voice_leading_quality.py`:
   - Same spec, with vs without `voice_leading_optimization`
   - Assert: total motion (with) < total motion (without) by ≥ 30%
3. `tests/scenarios/test_reharmonization_diversity.py`:
   - Same spec, intensity 0.0 vs 0.3 vs 0.6
   - Assert: harmonic complexity grows monotonically; alignment stays above threshold

### Step 8: Integration + Acceptance

- All existing 2978+ tests still green
- New tests under `tests/unit/coupling/` cover all new modules
- `make all-checks` passes (including new `make test-coupling`)
- `make arch-lint` enforces Layer 2.5 import direction
- Subjective listening test (`tests/subjective/`): Phase 3.5 output rated higher than Phase 3 output by ≥ 0.5/10 average

---

## Automated Failure Prevention

These common failure patterns are caught by tooling — not memorization. New v3.0 patterns are marked.

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
| Microtiming hardcode in M4 | Code-review pattern | `make lint` |
| Genre-specific logic in generators | Code-review pattern (`if genre == ...` in `src/yao/generators/`) | `make lint` |
| **M2 bypassing chord-aware constraints** *(NEW)* | `arch-lint` checks for `derive_constraints()` call in M2 when flag is on | `make arch-lint` |
| **Coupling module mutating its inputs** *(NEW)* | `arch-lint` AST check for non-frozen mutation of dataclass arg | `make arch-lint` |
| **Markov model without metadata** *(NEW)* | `markov-validate` schema check on YAML load | `make markov-validate` |
| **Hardcoded coupling-style rules** *(NEW)* | Code-review pattern (literal pitch-class lists in `coupling/`) | `make lint` |
| **Reharmonization without melody compatibility check** *(NEW)* | Unit test: every operation goes through `ReharmonizationConstraints` | `make test-coupling` |
| **Genre vector blend without provenance** *(NEW)* | Provenance schema requires `component_genres` for blended profiles | `make test` |
| **Listening agent bypass of order** *(NEW)* | Pipeline runtime asserts role order when `listening_agents=true` | `make test-coupling` |
| **Idiomatic gesture violating physical constraints** *(NEW)* | Gesture validator runs at load time | `make gesture-validate` |
| **Modulation distance unjustified by genre profile** *(NEW)* | `modulation-validate` checks against `MelodicProfile.modulation_preferences` | `make test` |

---

## Performance Expectations

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec | <100ms | Pydantic validation |
| Load MelodicProfile | <50ms | Cached after first load |
| Load Markov model | <30ms | YAML + metadata validation |
| Load idiomatic gestures (per instrument) | <20ms | Cached |
| Generate 8-bar piece (rule_based) | <1s | |
| Generate 8-bar piece (stochastic) | <1s | |
| Generate 8-bar piece (phrase_aware) | <2s | |
| Generate 8-bar piece (phrase_aware + Phase 3.5 flags ON) | <2.5s | Coupling overhead |
| Generate 64-bar piece (phrase_aware + Phase 3.5) | <6s | |
| Phrase plan only (M1) | <300ms | |
| Skeleton generation (M2) | <1s | Most expensive layer |
| Skeleton generation (M2) with `derive_constraints` *(NEW)* | <1.3s | +30% acceptable |
| Surface realization (M3) | <500ms | |
| Surface realization (M3) with rhythm Markov *(NEW)* | <700ms | |
| Ornament + groove (M4) | <300ms | |
| Ornament + idiomatic gestures (M4) *(NEW)* | <500ms | |
| `derive_constraints` per chord | <5ms | Cached |
| `optimal_voicing_transition` per chord *(NEW)* | <50ms | Hungarian on small matrices |
| Reharmonize 32-bar progression *(NEW)* | <1s | |
| Genre vector blend *(NEW)* | <100ms | |
| Theme recurrence planning *(NEW)* | <200ms | |
| Listening-agent dialog (per role per 4-bar chunk) *(NEW)* | <800ms | |
| Run all tests | <12s | Phase 3.5 expands suite |
| Architecture lint | <1.5s | More files to scan |
| Genre conformity score | <500ms | |
| Motif coherence score | <300ms | |
| Melody–harmony alignment score *(NEW)* | <300ms | |
| Voice-leading smoothness *(NEW)* | <200ms | |

Do not introduce changes that exceed these budgets without discussion. The 30% slack on M2 is intentional — that is the acceptable cost of chord-aware melody.

---

## Provenance Discipline

Every generation step records provenance. This is not optional and not "do at the end."

```python
# Correct (Phase 3.5 example)
provenance.record(
    layer="M2_skeleton",
    decision="select_target_pitch_with_constraints",
    input={
        "phrase_id": phrase.id,
        "current_chord": str(chord),
        "metric_position": 0.0,
        "chord_tones": list(constraints.chord_tones),
        "avoid_notes": list(constraints.avoid_notes),
        "coupling_style": constraints.style.value,
    },
    output={
        "target_pitch": 67,
        "chord_relation": "5th",
        "score_pitch": 0.92,
        "combined_score": 0.84,
    },
    rationale=(
        f"phrase function {phrase.function.value} + "
        f"chord_tone_targeting={profile.chord_tone_targeting} + "
        f"voice_leading_target + "
        f"coupling_style={constraints.style.value}"
    ),
    agent="composer-subagent",
    caused_by=[chord_event_provenance_id, phrase_plan_provenance_id],
)

# Wrong: missing rationale
provenance.record(layer="M2_skeleton", output={"target_pitch": 67})

# Wrong: missing caused_by for derived decisions
provenance.record(layer="M2_skeleton", decision="...", input={...}, output={...})
# A coupling-derived decision MUST link back to its causes.

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
- **NEW v3.0**: Avoid-note rules come from `_rules_<style>.py` constants, not from inline literals
- **NEW v3.0**: Chord extensions come from `MelodicProfile.coupling_style` rule sets, not from generator-local lookups
- **NEW v3.0**: Reharmonization operations check `melody_compatible()` *before* application, never after
- **NEW v3.0**: Voice-leading distance is in **semitones**, not in scale degrees — be explicit in function signatures

---

## Testing Discipline

For every new module or feature:

- **Unit tests** in `tests/unit/` covering normal cases, edge cases, error cases
- **Integration tests** in `tests/integration/` for any new generation strategy or pipeline
- **Scenario tests** in `tests/scenarios/` for genre-specific behaviors
- **Music constraint tests** in `tests/music_constraints/` for new constraints
- **Golden tests** in `tests/golden/` for stable canonical outputs
- **Diversity scenario tests** *(NEW)* in `tests/scenarios/test_*_diversity.py` for "same spec, different toggles → measurably different output"

Use existing test helpers:
```python
from tests.helpers import (
    assert_in_range,
    assert_no_parallel_fifths,
    assert_trajectory_match,
    assert_phrase_plan_valid,
    assert_skeleton_outlines_harmony,
    assert_genre_conformity,
    assert_motif_coherence_above,
    # NEW v3.0
    assert_melody_harmony_alignment_above,
    assert_voice_leading_smoothness_below,
    assert_reharmonization_preserves_melody,
    assert_genre_blend_blends,
    assert_polyrhythm_coherence_above,
    assert_listening_dialog_respects_order,
)
```

For genre-specific tests, use **golden tests**: generate output with a fixed seed, snapshot relevant musical features (interval distribution, phrase length distribution, chord-tone ratio, **NEW**: alignment score, voice-leading smoothness), assert future outputs match within tolerance.

For Phase 3.5, **diversity scenario tests are mandatory** for each new module:

```python
# tests/scenarios/test_chord_aware_melody.py
def test_chord_aware_melody_increases_alignment():
    spec = load_spec("specs/templates/jazz-ballad.yaml")

    spec_off = spec.with_features(chord_aware_melody=False)
    spec_on = spec.with_features(chord_aware_melody=True)

    score_off = generate(spec_off, seed=42)
    score_on = generate(spec_on, seed=42)

    align_off = melody_harmony_alignment(score_off)
    align_on = melody_harmony_alignment(score_on)

    assert align_on > align_off + 0.15, (
        f"chord-aware melody should increase alignment by ≥ 0.15; "
        f"got {align_off:.3f} → {align_on:.3f}"
    )
```

---

## Combination Stack Patterns

When implementing Layer 2.5 modules, follow these patterns.

### Pattern: Coupling module shape

```python
# src/yao/coupling/<module>.py

def couple(
    input_ir: SomeIR,
    profile: MelodicProfile,
    config: CouplingConfig,
    provenance: ProvenanceLog,
) -> SomeIR:
    """One-line summary.

    Belongs to Layer 2.5 (Combination & Coupling).

    Imports allowed: Layers 0, 1, 2, other coupling modules.
    Imports forbidden: Layers 3+ (IR, Perception, Render, Verify, Reflect).

    Args:
        input_ir: The structure to transform; treated as immutable.
        profile: Active genre profile (provides parameters).
        config: Module-specific configuration.
        provenance: Append-only log.

    Returns:
        A new SomeIR with provenance recorded. Never mutates input_ir.
    """
    if not _is_enabled(config):
        return input_ir  # feature flag off → identity

    transformed = _apply(input_ir, profile, config)
    provenance.record(
        layer="coupling",
        decision="<module>_apply",
        input={...},
        output={...},
        rationale="...",
        agent="<module>",
        caused_by=[input_ir.provenance_id],
    )
    return transformed
```

### Pattern: Profile-parameterized choice (carries forward from v2.x)

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

### Pattern: Chord-aware skeleton selection (NEW)

```python
# src/yao/generators/melody/skeleton.py

def _select_skeleton_note(
    candidates: list[MidiNote],
    chord: ChordEvent,
    key: str,
    scale_type: str,
    profile: MelodicProfile,
    position: PositionLabel,
    rng: random.Random,
) -> MidiNote:
    if not _features_enabled().chord_aware_melody:
        # Fall through to v2.x path
        return profile.interval_weighted_choice(candidates, rng)

    constraints = derive_constraints(chord, key, scale_type, profile.coupling_style)
    weighted = []
    for p in candidates:
        chord_score = constraints.score_pitch(p, position)
        interval_score = profile.interval_score(p)
        combined = (
            profile.chord_tone_targeting * chord_score
            + (1 - profile.chord_tone_targeting) * interval_score
        )
        weighted.append((p, combined))
    return weighted_sample(weighted, rng)
```

### Pattern: Reharmonization with constraints (NEW)

```python
# src/yao/coupling/reharmonization.py

def reharmonize(
    progression: ChordProgression,
    operations: list[ReharmonizationOperation],
    intensity: float,
    style: str,
    constraints: ReharmonizationConstraints,
    rng: random.Random,
) -> ChordProgression:
    result = progression
    for position in range(len(progression)):
        if rng.random() > intensity:
            continue
        candidate_op = rng.choice(operations)
        if not _is_applicable(candidate_op, result, position, style):
            continue
        proposed = _apply(candidate_op, result, position)
        if not constraints.melody_compatible(proposed, position):
            # Reject — never apply an operation that fails compatibility
            continue
        result = proposed
    return result
```

### Pattern: Profile-parameterized error (carries forward)

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
3. **Populate v3.0 fields** in the YAML:
   - `melody_markov_model: <model_name>` (from `markov_models/pitch/`)
   - `rhythm_markov_model: <model_name>` (from `markov_models/rhythm/`) — optional
   - `harmonic_system: functional | quartal | quintal | drone_based | ...`
   - `coupling_style: common_practice | jazz | blues | modal | raga | maqam`
   - `modulation_preferences:` (optional)
   - `polyrhythm_default:` (optional)
   - `idiomatic_gesture_intensity: 0.0–1.0`
4. **Add reference works** to `references/catalog.yaml` with verified license.
5. **Add scenario test** at `tests/scenarios/test_<genre>.py` verifying conformity metrics, including v3.0 metrics.
6. **Add anti-pattern checklist** with severity levels and fix recipes.
7. **For world music traditions**, flag in the PR description that human review is requested.

---

## Markov Model Addition Protocol *(NEW v3.0)*

When adding a Markov model:

1. **Specify metadata** in the YAML:
   ```yaml
   metadata:
     name: <unique_identifier>
     description: "human-readable description"
     source: "Hand-derived from..." OR "Trained on CC0 corpus: <name>"
     license: "CC0 — original work by YaO project" OR "<corpus_license>"
     n_gram_order: 2 | 3 | 4
     resolution: pitch_degree | 16th_grid | beat_grid
     smoothing: none | add_one | katz_backoff
     backoff_models: [<model_name>, ...]   # if applicable
   ```
2. **No copyrighted training data** — corpora must be CC0, public domain, or YaO-original.
3. **Run `make markov-validate`** before committing.
4. **Add unit test** verifying the model loads, transitions sum to 1.0 per row, and produces non-trivial output.
5. **Document the model's typical use** in `.claude/guides/rhythm-markov.md` or the relevant genre's Skill.

---

## Idiomatic Gesture Addition Protocol *(NEW v3.0)*

When adding a gesture for an instrument:

1. **Define in `src/yao/constants/idiomatic_gestures/<instrument>.yaml`**
2. **Each gesture specifies**:
   - `name`, `pattern`, `placement`
   - `probability_by_genre: {<genre>: 0.0–1.0, ...}`
   - `physical_constraint:` (optional, e.g., "open_string_only")
   - `repeatable: true | false` (default `false`)
3. **Cite the source** for the gesture in a comment (instrument tutor, treatise, recording analysis)
4. **Add unit test** in `tests/unit/coupling/test_idiomatic_gestures.py` covering placement triggering and probability behavior

---

## Recent Changes

- **2026-05-08**: **Phase 3.5 launched** — Combination Stack architecture (Layer 2.5) introduced. Three new modules in development: chord-aware melody (§4.1), voice-leading optimizer (§5.4), reharmonization engine (§5.1). Two new non-negotiable rules (8 and 9). Eighth design principle: Diversity Through Combination. Eleven evaluation dimensions. Three new slash commands. Two new subagents.
- **2026-05-07**: Phase 2 COMPLETE — phrase-first pipeline fully implemented; 5 Tier-1 genre profiles; all 4 melody pipeline layers (M1–M4); PhraseAwareGenerator registered; 176 new tests (2978 total); all checks green.
- **2026-04-29**: MIDI reader, section regeneration, evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades, mypy fixes (140 → 0 errors).
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff.
- **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance, CLAUDE.md restructured into tiered guides.
- **2026-04-28**: Phase 0+1 complete — 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Claude Code commands/agents.
- **2026-04-27**: Project initialized.

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
- A change would require modifying existing `rule_based`, `stochastic`, `markov`, or `phrase_aware` generators (they must remain stable)
- **NEW v3.0**: A proposed coupling module would mutate its inputs
- **NEW v3.0**: A coupling module's import surface is unclear (which layers it depends on)
- **NEW v3.0**: A reharmonization operation produces a chord–melody clash that cannot be resolved by the constraints checker
- **NEW v3.0**: A new Markov model's source corpus has uncertain licensing
- **NEW v3.0**: A genre blend produces a profile whose metrics fall outside any single component's range (potential pathological blend)
- **NEW v3.0**: An idiomatic gesture's `physical_constraint` is unfamiliar (e.g., new instrument)

Asking is not weakness. It is correct behavior under uncertainty.

---

## Sound-First Culture

For changes that affect generated music (new generators, new profiles, modified rhythm logic, new coupling modules):

- Generate sample outputs with the existing templates before and after the change
- If FluidSynth is available, render to WAV and note any audible differences
- Include in commit message: musical impact note (e.g., "alignment score 0.62 → 0.81; voice-leading total motion 287 → 124 semitones")
- For changes that subjectively improve quality, save sample MIDI/WAV files for the human
- **NEW v3.0**: For coupling-module changes, run the corresponding diversity scenario test and report the delta

You cannot truly "hear" the music yourself, but you can measure features that are proxies for what humans will hear. Use those measurements liberally.

---

## Backward Compatibility

The Combination Stack is added alongside the existing pipeline, never replacing it.

- The existing `rule_based`, `stochastic`, `markov`, and `phrase_aware` generators continue to work without modification
- All existing tests (2978+) must remain green throughout Phase 3.5 and beyond
- Existing CLI commands behave identically by default *except* for the implicit defaults in v3.0:
  - `features.chord_aware_melody=true` is the default starting v3.0
  - `features.voice_leading_optimization=true` is the default starting v3.0
  - All other features default to `false` (opt-in)
- Users opt out of new defaults via explicit `features:` block in their spec
- The default strategy in templates does not change until each Combination Stack module reaches feature parity for its domain

If a refactor would touch the existing generators, stop and propose a specific plan to the human before proceeding.

---

## Guides (read when relevant)

| Guide | When to read |
|---|---|
| Architecture | Working across layers, adding modules |
| Coding Conventions | Writing any code |
| Music Engineering | Generating/modifying notes |
| Melody Pipeline | Anything in `src/yao/generators/melody/` |
| Genre Profiles | Adding or modifying a genre Skill |
| **Combination Stack** *(NEW)* | Anything in `src/yao/coupling/` |
| **Chord-Aware Melody** *(NEW)* | Phase 3.5 — §4.1 implementation |
| **Voice-Leading Optimizer** *(NEW)* | Phase 3.5 — §5.4 implementation |
| **Reharmonization Engine** *(NEW)* | Phase 3.5 — §5.1 implementation |
| **Genre Vector Space** *(NEW)* | Phase 5.0 — §6.1 implementation |
| **Rhythm Markov** *(NEW)* | Phase 4.0 — §3.1 implementation |
| **Listening Agents** *(NEW)* | Phase 5.5 — §6.3 implementation |
| Testing | Writing or running tests |
| Workflow | Planning a change |

Full design documentation: [PROJECT.md](./PROJECT.md)
Gap analysis and roadmap: [IMPROVEMENT.md](./IMPROVEMENT.md)

---

## Operating Constants — Pinned Reminders

- **Layer rule**: lower layers never depend on higher layers; Layer 2.5 imports only from Layers 0–2
- **Generators return**: `(ScoreIR, ProvenanceLog)` — always
- **Coupling modules return**: `(<TransformedIR>, ProvenanceLog)` — never mutate inputs
- **Errors**: typed `YaOError` subclasses; never bare `ValueError`; never silent fallback
- **Constants**: lookups via `src/yao/constants/`; never literals in logic
- **Pipeline order**: M1 → M2 → M3 → M4 — strict, monolithic
- **Genre = MelodicProfile**: never strings in logic, never `if genre == "..."`
- **Coupling = feature-flagged**: every new module checks `composition.features.<flag>`
- **Coupling = additive**: never replaces existing generators
- **Provenance**: append-only, recorded for every generation step, with `caused_by` for derived decisions
- **Tests**: written before or alongside; never skipped without justification
- **Diversity tests**: mandatory for every coupling module (same spec / different flags / measurably different output)
- **Commits**: Conventional Commits, one logical change each
- **Performance**: budgets in this file are not aspirational
- **Migration**: additive, never replacing existing generators
- **Escalation**: when in doubt, stop and ask
- **The single rule of v3.0**: never break the existing pipeline while adding the Combination Stack

---

*CLAUDE.md version: 3.0*
*Last updated: 2026-05-08*
*v3.0: Combination Stack rules added. Two new non-negotiable rules (8: melody must be coupled to harmony; 9: combination stack is feature-flagged and additive). Eighth design principle: Diversity Through Combination. Phase 3.5 (Diversity Foundation) becomes the active phase with chord-aware melody, voice-leading optimizer, and reharmonization engine in development. Eleven failure-prevention patterns added. Combination-Stack patterns documented. Markov-model and idiomatic-gesture addition protocols introduced.*
*v2.1: Phase 2 complete — updated Current Phase to Phase 3, added Phase 3 implementation plan, marked Phase 2 deliverables as complete with file locations.*
*v2.0: Added phrase-first pipeline rules (Rules 6, 7), genre Skill protocol, layer M1–M4 patterns, performance budgets for new layers, Phase 2 implementation plan, and 4 new failure-prevention patterns.*
