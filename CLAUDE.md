# CLAUDE.md — YaO Core Rules (v2.0)

> *Read this file at session start. Detailed guides are in `.claude/guides/`.*
> *In case of conflict: CLAUDE.md > PROJECT.md > guides > other docs.*
> *This is the v2.0 development guide, incorporating Phase 1.5 multi-genre foundation.*

---

## 0. What Changed in v2.0

This file extends the v1.0 CLAUDE.md to support development of the multi-genre, multi-layer YaO described in PROJECT.md v2.0. The v1.0 invariants — strict layer boundaries, append-only provenance, no silent fallbacks, range violations as errors — all remain. The additions are:

- **Layer 3.5 (Sound Design)** is added between IR and Render. New layer-import rules apply.
- **Layer 4 (Perception)** is now real, not "planned". Its module exists and is imported by Conductor.
- **Five new subagents** (Sound Designer, Sample Curator, Texture Composer, Beatmaker, Loop Architect) join the seven existing ones.
- **`tonal_system` replaces flat `key`** in the schema; harmony realization dispatches on tonal kind.
- **Six-phase cognitive protocol is enforced in code**, not merely documented.
- **Genre Skills follow a standard template** with frontmatter, evaluator weights, and default sound design.
- **Inter-subagent message protocol** is specified in `.claude/agents/_protocol.md`.

When in doubt about a v2.0-specific detail, consult PROJECT.md §3 (architecture), §5 (subagents), §6 (six phases), §7 (specs), and §10 (genre skill template).

---

## 1. Quick Reference

```
make test           # Run all tests
make lint           # ruff + mypy
make arch-lint      # Layer boundary check (now includes layer 3.5)
make all-checks     # lint + arch-lint + test
make format         # Auto-format code
make test-genre     # NEW v2.0 — genre-specific scenario tests
make test-tonal     # NEW v2.0 — tonal system tests across kinds
make test-perception # NEW v2.0 — perception layer tests
```

**Key directories (v2.0):**

```
src/yao/constants/      → Layer 0: hardcoded values (ranges, scales, MIDI mappings)
src/yao/schema/         → Layer 1: Pydantic models for YAML specs
                          (composition, tonal_system, duration, sound_design, references, ensemble)
src/yao/ir/             → Layer 3: core data types (Note, ScoreIR, harmony, motif, voicing)
src/yao/generators/     → Layer 2: composition algorithms (rule_based, stochastic, loop_evolution)
src/yao/sound_design/   → Layer 3.5 (NEW): patches, effects, samples
src/yao/perception/     → Layer 4 (NEW): reference matcher, psych mapper, surprise model
src/yao/render/         → Layer 5: output (MIDI, audio, stems)
src/yao/verify/         → Layer 6: analysis, linting, evaluation, idiomaticity, singability, seamlessness
src/yao/reflect/        → Provenance tracking (cross-cutting)
src/yao/conductor/      → Orchestration; protocol.py enforces 6 phases; adaptations/ library
src/yao/errors.py       → All custom exceptions
```

**Key types (v2.0 additions in bold):**

```
Note                  → src/yao/ir/note.py
ScoreIR               → src/yao/ir/score_ir.py
CompositionSpec       → src/yao/schema/composition.py
TonalSystem           → src/yao/schema/tonal_system.py        ← NEW
Duration              → src/yao/schema/duration.py            ← NEW (Bars | Beats | Seconds | Loops | Free)
SoundDesignSpec       → src/yao/schema/sound_design.py        ← NEW
ReferencesSpec        → src/yao/schema/references.py          ← NEW
EnsembleTemplate      → src/yao/schema/ensemble.py            ← NEW
ProvenanceLog         → src/yao/reflect/provenance.py
GeneratorBase         → src/yao/generators/base.py
SubagentMessage       → src/yao/conductor/subagent_message.py ← NEW
Phase                 → src/yao/conductor/protocol.py         ← NEW
AdaptationStrategy    → src/yao/conductor/adaptations/base.py ← NEW
```

---

## 2. Your Role

You are a **co-developer of YaO**, not YaO itself. You build the infrastructure that the Orchestra of subagents will use. Your code enables reproducible, auditable, iterable music creation across many genres.

This v2.0 work is fundamentally about **removing assumptions** that biased YaO toward Western tonal pop music. Every change you make should be evaluated against the question: *"Does this work for blues, modal jazz, ambient drone, deep house, lo-fi hip-hop, J-pop, prog rock, microtonal contemporary, and Indian classical music — or just for major/minor pop?"* If the answer is "just for pop", the change is incomplete.

---

## 3. 7 Non-Negotiable Rules (v2.0 — extends v1.0)

The original five rules remain. Two are added in v2.0.

1. **Never break layer boundaries** — including the new Layer 3.5 and Layer 4. See `.claude/guides/architecture.md`.
2. **Every generation function returns `(ScoreIR, ProvenanceLog)`** — and every Provenance entry must include `agent`, `phase`, `confidence`.
3. **No silent fallbacks** — constraint violations must be explicit errors.
4. **No hardcoded musical values** — use `src/yao/constants/`.
5. **No public function without type hints and docstring**.
6. **NEW v2.0** — **No Western tonality assumption**. Code that handles harmony, scales, or pitch must dispatch on `TonalSystem.kind`. A function that "just assumes major/minor" is broken.
7. **NEW v2.0** — **Subagent decisions must be recorded in Provenance with the subagent identifier**. A decision attributed to "the system" or "the generator" with no subagent name is incomplete.

---

## 4. MUSTs (v2.0 additions in bold)

- Read existing code before writing new code.
- Write tests before or alongside implementation.
- Keep YAML schemas and Pydantic models in sync.
- Use `yao.ir.timing` for all tick/beat/second conversions.
- Use `yao.ir.notation` for all note name/MIDI conversions; note that v2.0 `Pitch` is `(midi_int, cents_offset)`.
- Derive velocity from dynamics curves (never hardcode).
- Register generators via `@register_generator("name")`.
- **NEW v2.0** — When adding a Genre Skill, follow the template in PROJECT.md §10. A Skill missing the YAML frontmatter is unloadable.
- **NEW v2.0** — When adding a subagent, comply with the message format in `.claude/agents/_protocol.md`. A subagent that does not emit `SubagentMessage` is a v1.0-style stub.
- **NEW v2.0** — When changing the evaluator, ensure each metric declares whether it is `tonal_system_aware`. Untagged metrics are run for all systems by default; tagged metrics are conditionally enabled.
- **NEW v2.0** — When adding an adaptation strategy, register it in `conductor/adaptations/` with `applies()`, `apply()`, `cost`, and `expected_metric_delta`. Strategies must be discoverable by the Conductor.
- **NEW v2.0** — When touching Layer 3.5 (Sound Design), ensure the `pedalboard` import is **lazy**. Sound Design is an optional dependency; missing it must degrade gracefully, not crash.
- **NEW v2.0** — When phase logic changes, update `PHASE_REQUIRED_ARTIFACTS` in `conductor/protocol.py` so phase completion is verifiable.

---

## 5. MUST NOTs (v2.0 additions in bold)

- Import `pretty_midi`/`music21`/`librosa` outside designated layers.
- **NEW v2.0** — Import `pedalboard` outside `src/yao/sound_design/` or `src/yao/render/audio_renderer.py`.
- **NEW v2.0** — Import `numpy` heavily inside Layer 1 (schema). Schemas are validation-only; computation belongs in IR or above.
- Create functions with vague names (`make_it_sound_good`).
- Skip provenance recording for any generation step.
- Use bare `ValueError` (use `YaOError` subclasses).
- Silently clamp notes to range (raise `RangeViolationError`).
- Leave `TODO`/`FIXME` uncommitted.
- **NEW v2.0** — Hardcode major/minor as the only tonal system. If you write `if mode == 'major'`, ask whether `if tonal_system.kind == 'tonal_major_minor'` is what you mean.
- **NEW v2.0** — Generate music in a phase before the previous phase's required artifact exists. Phase ordering is enforced; bypassing it requires `--force-phase` and is for debug only.
- **NEW v2.0** — Mark a Skill or subagent as "Genre X compatible" without an integration test that proves it. A Skill without a test is documentation, not a feature.
- **NEW v2.0** — Add a reference piece to `references/midi/` without a corresponding entry in `references/catalog.yaml` declaring rights status. Files without rights metadata fail loading and break tests.

---

## 6. 5 Design Principles

1. **Agent = environment, not composer** — we accelerate human creativity.
2. **Explain everything** — every note has a provenance record.
3. **Constraints liberate** — specs and rules are scaffolds, not cages.
4. **Time-axis first** — design trajectory curves before notes.
5. **Human ear is truth** — automated scores inform, humans decide.

These are repeated from PROJECT.md to ensure they are present at the start of every session.

---

## 7. Current Phase

**Phase 1.5** — Multi-Genre Foundation (in progress)

**What EXISTS (carried over from Phase 1):**

- Spec loading + validation (YAML → Pydantic) ✅
- ScoreIR (Note, Part, Section, Motif, Voicing, Harmony) ✅
- Rule-based generator (deterministic) ✅
- Stochastic generator (seed + temperature) ✅
- Generator registry (strategy selection via spec) ✅
- Constraint system (must / must_not / prefer / avoid with scoped rules) ✅
- MIDI rendering + stems ✅
- MIDI reader (load existing MIDI back to ScoreIR for analysis) ✅
- Music linting, analysis, evaluation ✅
- Score diff with modified note tracking ✅
- Provenance logging (append-only, queryable) ✅
- Conductor feedback loop (generate → evaluate → adapt → regenerate) ✅
- Section-level regeneration ✅
- CLI (compose, conduct, render, validate, evaluate, diff, explain, new-project, regenerate-section) ✅
- Architecture lint tool ✅
- 7 Claude Code commands and 7 v1.0 subagent definitions ✅
- 4 Skills populated (cinematic, voice-leading, piano, tension-resolution) ✅

**What is being added in Phase 1.5:**

- `tonal_system` schema and harmony dispatch (PR-2)
- Genre Skill template + 6 Tier-1 Skills (PR-1)
- Subagent message protocol (`.claude/agents/_protocol.md`) (PR-5)
- Six-phase enforcement (`conductor/protocol.py`) (PR-6)

**What is queued for Phase 2:**

- Sound Design Layer (Layer 3.5)
- Perception Layer (Layer 4): reference matcher, psych mapper, surprise model
- Five new subagents (Sound Designer, Sample Curator, Texture Composer, Beatmaker, Loop Architect)

**What is queued for Phase 3:**

- Loop-First generator + modular arrangement
- Vocal Track support
- Arrangement Engine (reharmonization, regrooving, reorchestration)

**What does NOT exist yet (later phases):**

- Markov / constraint-solver / AI-bridge generators
- DAW integration (MCP)
- Live improvisation mode
- Continuous Conductor TUI

---

## 8. Layer Architecture (v2.0 — 8 layers)

The architecture lint enforces these import rules. Read `.claude/guides/architecture.md` for the full table.

```
Layer 0  constants/         → (nothing)
Layer 1  schema/            → constants
Layer 1  ir/                → constants
Layer 1  reflect/           → constants (cross-cutting)
Layer 2  generators/        → constants, schema, ir, reflect
Layer 3.5 sound_design/     → constants, schema, ir                 ← NEW
Layer 4  perception/        → constants, schema, ir, generators     ← NEW (real)
Layer 5  render/            → constants, schema, ir, generators, sound_design, perception
Layer 6  verify/            → constants, schema, ir, generators, sound_design, perception, render
         conductor/         → all of the above
```

**Library restrictions (v2.0 additions):**

| Library | Allowed In | Purpose |
|---|---|---|
| `pretty_midi` | ir/, render/ | MIDI creation and editing |
| `music21` | ir/, verify/ | Music theory analysis, MusicXML |
| `librosa` | verify/ only | Audio feature analysis |
| `pyloudnorm` | verify/ only | LUFS loudness measurement |
| `pedalboard` | sound_design/, render/audio_renderer.py only | VST chain hosting (NEW v2.0) |
| `pydantic` | schema/ | YAML spec validation |
| `structlog` | anywhere | Structured logging |
| `click` | cli/ only | CLI framework |
| `numpy/scipy` | ir/, generators/, sound_design/, perception/, render/, verify/ | Numerical computation |

---

## 9. Genre-Aware Development

This is the most important new section in v2.0. Every change to generation, IR, or evaluation must be evaluated for **genre universality**.

### 9.1 The Genre Universality Test

Before merging a PR, ask:

1. Does this change work for tonal major/minor? (the v1.0 baseline)
2. Does it work for modal music (Dorian, Mixolydian, Phrygian)?
3. Does it work for blues (where ♭3 is a feature)?
4. Does it work for atonal music (where consonance ratio is meaningless)?
5. Does it work for drone music (where pitch class variety is meaningless)?
6. Does it work for music with mid-section meter changes (prog rock)?
7. Does it work for music with no meter at all (free jazz, ambient)?
8. Does it work for music where melody is absent (deep house, dark ambient)?
9. Does it work for music where timbre defines the genre (lo-fi, dnb)?
10. Does it work for music with microtonal pitches (Indian classical, contemporary)?

If the answer to any of (2)–(10) is "no", document why in the PR description. If multiple are "no", reconsider the design.

### 9.2 Genre-Conditional Code Patterns

```python
# WRONG (v1.0 pattern that fails for non-tonal genres)
def evaluate_consonance(score: ScoreIR) -> float:
    return count_consonant_intervals(score) / total_intervals(score)

# RIGHT (v2.0 pattern)
def evaluate_consonance(score: ScoreIR, tonal_system: TonalSystem) -> float | None:
    if tonal_system.kind in {"atonal", "drone", "microtonal"}:
        return None  # not applicable
    if tonal_system.kind == "blues":
        return count_consonant_intervals_blues_aware(score) / total_intervals(score)
    return count_consonant_intervals(score) / total_intervals(score)
```

```python
# WRONG (assumes melody exists)
def generate_section(spec: SectionSpec) -> Section:
    melody = compose_melody(spec)
    chords = harmonize(melody)
    bass = bass_from_chords(chords)
    return Section(parts=[melody, chords, bass])

# RIGHT (delegates to ensemble template)
def generate_section(spec: SectionSpec, ensemble: EnsembleTemplate) -> Section:
    parts: list[Part] = []
    for subagent in ensemble.active_subagents:
        parts.extend(subagent.generate_for_section(spec))
    return Section(parts=parts)
```

### 9.3 Genre Skill Authoring

When adding or editing a Skill, follow PROJECT.md §10. A skeleton:

```markdown
---
genre_id: <id>
display_name: "<name>"
parent_genres: [...]
related_genres: [...]
typical_use_cases: [...]
ensemble_template: <template>
default_subagents:
  active: [...]
  inactive: [...]
---

## Defining Characteristics
## Required Spec Patterns
## Idiomatic Chord Progressions
## Idiomatic Rhythms
## Anti-Patterns
## Reference Tracks
## Default Sound Design
## Evaluation Weight Adjustments
## Default Trajectories
```

A Skill that lacks the YAML frontmatter is rejected at load time. A Skill that lacks `Anti-Patterns` cannot be used by the Adversarial Critic. A Skill that lacks `Reference Tracks` cannot drive Reference-Driven Evaluation.

---

## 10. Subagent Development

### 10.1 Subagent File Structure

`.claude/agents/<name>.md` for every subagent. Required sections:

```markdown
---
agent_id: sound_designer
role: subagent
active_for_genres: [electronic, ambient, lo_fi_hiphop, ...]
inactive_for_genres: [classical_chamber, baroque, ...]
forbidden_actions: [pitch_choice, chord_choice]
---

## Responsibility
## Inputs
## Outputs (must conform to .claude/agents/_protocol.md)
## Decision Domains
## Forbidden Actions
## Evaluation Criterion
## Skill References
```

### 10.2 Subagent Message Protocol

Every subagent invocation produces a `SubagentMessage`:

```python
# src/yao/conductor/subagent_message.py
@dataclass(frozen=True)
class SubagentMessage:
    agent: str
    phase: Phase
    input_hash: str
    decisions: list[Decision]
    questions_to_other_agents: list[Question]
    flags: list[str]
    artifacts: list[Path]
```

These are recorded in Provenance verbatim.

### 10.3 Producer Arbitration

When subagent outputs conflict, Producer arbitrates by this priority:

1. `intent.md` alignment (highest)
2. Hard constraints (`must` / `must_not`)
3. Active genre Skill recommendations
4. Expected evaluator score improvement
5. Subagent default preference (Composer or replacement is the default tiebreaker)

If you write code that lets a non-Producer subagent override another, that is a bug.

---

## 11. Six-Phase Enforcement

`conductor/protocol.py`:

```python
class Phase(IntEnum):
    INTENT_CRYSTALLIZATION = 1
    ARCHITECTURAL_SKETCH = 2
    SKELETAL_GENERATION = 3
    CRITIC_COMPOSER_DIALOGUE = 4
    DETAILED_FILLING = 5
    LISTENING_SIMULATION = 6

PHASE_REQUIRED_ARTIFACTS: dict[Phase, list[str]] = {
    Phase.INTENT_CRYSTALLIZATION:    ["intent.md"],
    Phase.ARCHITECTURAL_SKETCH:      ["trajectory.yaml"],
    Phase.SKELETAL_GENERATION:       ["score_skeleton.json"],
    Phase.CRITIC_COMPOSER_DIALOGUE:  ["critique_round_1.md", "selected_skeleton.json"],
    Phase.DETAILED_FILLING:          ["full.mid", "stems/"],
    Phase.LISTENING_SIMULATION:      ["analysis.json", "evaluation.json", "critique.md"],
}
```

**When developing**:

- Production code must walk phases in order; check artifacts before advancing.
- The CLI flag `--force-phase <PHASE>` is for debugging only and emits a warning.
- Tests should verify that bypassing a phase raises `PhaseIncompleteError`.

**When debugging**:

- If a piece looks "structurally directionless", the most likely cause is that Phase 2 (trajectory) was skipped or generated trivially. Check `trajectory.yaml`.
- If a piece sounds "technically correct but soulless", Phase 6 (listening simulation) most likely returned no perception feedback. Check Layer 4 is initialized.

---

## 12. Sound Design Layer (3.5) — Development Notes

### 12.1 Optional Dependency
`pedalboard` is not a hard dependency. Code paths that use it must:

```python
try:
    import pedalboard
    SOUND_DESIGN_AVAILABLE = True
except ImportError:
    SOUND_DESIGN_AVAILABLE = False

def render_audio_with_sound_design(...):
    if not SOUND_DESIGN_AVAILABLE:
        log.info("pedalboard not installed; falling back to MIDI-only output")
        return None
    ...
```

### 12.2 Two-Stage Rendering

```
spec → MIDI per stem → audio per stem (with sound design) → mixdown
```

- Stage 1 (MIDI) is fast, mandatory.
- Stage 2 (audio per stem) is slow, optional, requires `pedalboard` + soundfont.
- Stage 3 (mixdown) requires Stage 2.

When tests run in CI without `pedalboard`, Stage 2/3 tests are skipped with `@pytest.mark.requires_pedalboard`. They are not failures.

### 12.3 Sound Design Specs

`SoundDesignSpec` validates the YAML fragment from PROJECT.md §7.7. Synthesis kinds: `sample_based`, `subtractive`, `fm`, `wavetable`, `physical`. Effect types: `eq`, `compressor`, `limiter`, `reverb`, `convolution_reverb`, `delay`, `tape_saturation`, `bitcrusher`, `chorus`, `phaser`, `flanger`. Add new kinds by extending the union and writing a renderer.

---

## 13. Perception Layer (4) — Development Notes

### 13.1 Three Submodules

- `reference_matcher.py` — extract feature vectors from reference and generated pieces; compute weighted Euclidean distance.
- `psych_mapper.py` — map symbolic and acoustic features to predicted arousal/valence/genre coherence.
- `surprise_model.py` — n-gram or Markov model of the piece's own opening; measure entropy of subsequent events.

### 13.2 Feature Extraction

A feature extractor takes a `ScoreIR` and returns a `FeatureVector`:

```python
class FeatureExtractor(Protocol):
    name: str
    feature_dim: int
    def extract(self, score: ScoreIR) -> np.ndarray: ...
```

Initial feature set (must be implemented in PR-4):

- `voice_leading_smoothness`
- `motivic_density`
- `surprise_index`
- `register_distribution`
- `temporal_centroid`
- `groove_pocket`
- `chord_complexity`

### 13.3 Reference Library

References are loaded from `references/midi/` and `references/musicxml/`. Each entry has metadata in `references/catalog.yaml`:

```yaml
- id: jazz_invention_001
  file: midi/jazz_invention_001.mid
  rights_status: cc0
  license_url: https://creativecommons.org/publicdomain/zero/1.0/
  attribution: "Original work by [author], dedicated to the public domain"
  features_extracted: true
  feature_cache: extracted_features/jazz_invention_001.npz
```

A reference without complete metadata is **not loaded**. Loading-time validation is strict.

### 13.4 Conductor Integration

The Conductor calls Perception during Phase 6 (Listening Simulation). The output is a set of perception scores that feed into the adaptation decision:

```python
perception_report = perception_layer.evaluate(
    score=generated_score,
    references=spec.references,
    intent=spec.intent,
    target_surprise_band=genre_skill.target_surprise_band,
)
adapted_spec = conductor.adapt(spec, perception_report, evaluation_report)
```

---

## 14. Adaptation Strategies (v2.0)

The Conductor selects adaptation strategies from `src/yao/conductor/adaptations/`. Each strategy:

```python
class AdaptationStrategy(Protocol):
    name: str
    cost: float
    expected_metric_delta: dict[str, float]
    def applies(self, report: EvaluationReport, spec: CompositionSpec) -> bool: ...
    def apply(self, spec: CompositionSpec) -> CompositionSpec: ...
    def explain(self) -> str: ...
```

Initial strategies (must be implemented):

| Strategy | Triggers When | Effect |
|---|---|---|
| `transpose_section` | Section contrast < 0.4 | Add `transpose_semitones` to bridge |
| `swap_instrument` | Frequency clash detected | Substitute one instrument in section |
| `change_texture` | Density curve flat | Switch homophonic ↔ polyphonic |
| `change_meter_in_section` | Predictability too high | Add 6/8 or 5/4 in a section |
| `redistribute_density` | Climax not at golden ratio | Move climax to bar 0.61 of total |
| `add_counter_melody` | Texture density < target | Add countermelody to chosen voice |
| `drop_layers_for_impact` | Build-up needed | Drop drums/bass for 4 bars before climax |
| `reharmonize_with_secondary_dominant` | Harmonic predictability high | Insert V/V, V/vi |
| `insert_modal_interchange` | Genre allows, palette too small | Borrow from parallel mode |
| `humanize_micro_timing` | Groove too rigid | Add ±10ms timing offsets |
| `simplify_overcrowded_section` | Texture density > 0.95 | Reduce instrument count |
| `add_negative_space` | Continuous activity > target | Insert deliberate silence at phrase boundaries |

Strategies are selected by `(expected_improvement / cost)` with a stochastic exploration component. The selection is logged in Provenance.

---

## 15. Automated Failure Prevention (v2.0 additions in bold)

| Pattern | What catches it | Command |
|---|---|---|
| Tick calculation error | Unit tests in `test_ir.py` | `make test-unit` |
| Range violation silence | `RangeViolationError` | `make test` |
| Velocity hardcode | Code review pattern | `make lint` |
| Missing provenance | `GeneratorBase` enforces return | `mypy` |
| Layer boundary breach | AST-based import checker | `make arch-lint` |
| Schema/model mismatch | Integration test loads all templates | `make test` |
| Parallel fifths | Constraint checker + voicing module | `make test` |
| **Tonal system assumption (v2.0)** | **`test_tonal_system_dispatch.py`** | **`make test-tonal`** |
| **Phase ordering bypass (v2.0)** | **`test_phase_protocol.py`** | **`make test`** |
| **Subagent without provenance ID (v2.0)** | **Provenance schema validation** | **`make test`** |
| **Skill without frontmatter (v2.0)** | **Skill loader rejects** | **`make test-skills`** |
| **Reference without rights metadata (v2.0)** | **Reference loader rejects** | **`make test`** |

---

## 16. Performance Expectations (v2.0 — updated)

| Operation | Target | Notes |
|---|---|---|
| Load YAML spec (incl. tonal_system) | <100ms | Pydantic validation |
| Generate 8-bar piece | <1s | Both generators |
| Generate 64-bar piece | <5s | Stochastic may vary |
| **Loop_evolution 64-bar piece (v2.0)** | <8s | New strategy; layer-by-layer construction |
| Write MIDI file | <200ms | pretty_midi |
| **Render audio with Sound Design (v2.0)** | <30s for 90s piece | pedalboard + VST chain |
| **Reference distance computation (v2.0)** | <500ms per reference | Feature extraction + Euclidean |
| **Perception layer full pass (v2.0)** | <2s | All three submodules |
| Run full lint | <500ms | All lint rules |
| Run all unit tests | <10s | Phase 1.5 grew the test count |
| Architecture lint | <1s | AST parsing |

Do not introduce changes that exceed these budgets without discussion. If Sound Design rendering drives audio time over 30s for 90s pieces, profile and optimize.

---

## 17. Testing (v2.0 additions)

### 17.1 New Test Categories

- `tests/genres/` — one test file per Tier-1 genre, verifying the Skill's evaluation weights and default trajectories produce a recognizable output.
- `tests/tonal_systems/` — for each tonal system kind, a fixture spec and an evaluation that confirms genre-appropriate scoring.
- `tests/perception/` — feature extractor unit tests + reference distance integration tests.
- `tests/sound_design/` — synthesis patch and effect chain rendering tests, gated on `pedalboard` availability.
- `tests/phase_protocol/` — phase ordering enforcement tests.
- `tests/subagent_protocol/` — subagent message format and Producer arbitration tests.

### 17.2 Test Helpers (v2.0 additions)

```python
from tests.helpers import (
    assert_in_range,
    assert_no_parallel_fifths,
    assert_trajectory_match,
    assert_phase_complete,           # NEW v2.0
    assert_subagent_in_provenance,   # NEW v2.0
    assert_tonal_system_appropriate, # NEW v2.0
    assert_seamless_loop,            # NEW v2.0
    assert_singable,                 # NEW v2.0
)
```

### 17.3 Genre Scenario Test Skeleton

```python
# tests/genres/test_lo_fi_hiphop.py
def test_lo_fi_hiphop_basic_generation(tmp_output_dir):
    spec = load_template("lofi-loop-2min.yaml")
    spec.tonal_system = TonalSystem(kind="tonal_major_minor", key="C", mode="major")
    result = compose(spec, output_dir=tmp_output_dir)

    assert result.evaluation.acoustics.tempo_bpm in range(80, 96)
    assert "tape_saturation" in result.sound_design.effect_chains["piano"]
    assert result.score.has_idiomatic_pattern("boom_bap_drums")
    assert result.evaluation.harmony.has_jazz_chord_extensions
    assert_seamless_loop(result.score, tolerance=0.05)
```

---

## 18. Code Standards (v2.0 — extends v1.0)

- Python 3.11+ with `from __future__ import annotations`.
- `mypy --strict` for all public API.
- `ruff` for linting and formatting (line length 99).
- Pydantic for external data (YAML specs); frozen dataclasses for internal domain objects.
- Custom exceptions only — no bare `ValueError`; use `YaOError` subclasses.
- Conventional Commits — `feat(harmony): add secondary dominant insertion`.
- **NEW v2.0** — Subagent files use `<role>-<noun>.md` format: `sound-designer.md`, `loop-architect.md`, etc.
- **NEW v2.0** — When adding a tonal system, add (a) Pydantic enum entry, (b) `harmony.realize_<kind>()` function, (c) evaluator dispatch case, (d) test fixture, (e) example template — in the same PR.
- **NEW v2.0** — When adding a feature extractor, add (a) class implementing `FeatureExtractor`, (b) registration in `feature_extractors/__init__.py`, (c) at least one reference using it, (d) round-trip test (extract from MIDI → MIDI → extract again should give equivalent vector).

---

## 19. Recent Changes

- **2026-05-05**: PROJECT.md and CLAUDE.md updated to v2.0. IMPROVEMENT.md findings C1–C6, Q1–Q5, A1–A3 incorporated. Phase 1.5 introduced.
- **2026-04-29**: MIDI reader, section regeneration, evaluation.json persistence, richer feedback adaptations, Claude Code command upgrades, 4 skills populated, mypy fixes (140→0 errors).
- **2026-04-29**: Constraint system, CLI diff/explain commands, stochastic unit tests, modified_notes in ScoreDiff, documentation completions.
- **2026-04-28**: Stochastic generator, generator registry, musical error messages, queryable provenance, CLAUDE.md restructured into tiered guides.
- **2026-04-28**: Phase 0+1 complete: 7-layer architecture, rule-based generator, MIDI/stems, evaluation, provenance, CLI, Claude Code commands/agents.
- **2026-04-27**: Project initialized with PROJECT.md and CLAUDE.md.

---

## 20. Escalation

Stop and ask the human when:

- Changing architectural boundaries or layer rules (especially the new layers 3.5 and 4).
- Adding new external dependencies.
- Making music theory judgment calls you're unsure about — **especially in non-Western or non-tonal contexts**.
- Deleting files or rewriting git history.
- Any change touching 5+ files.
- **NEW v2.0** — Adding a Genre Skill where you do not have personal listening experience in the genre. The maintainer should commission a musician's review before merging.
- **NEW v2.0** — Modifying the subagent arbitration priority. This affects every Producer decision.
- **NEW v2.0** — Adding a Tonal System kind. This affects evaluator dispatch, harmony realization, MIDI rendering, and tests across all phases.
- **NEW v2.0** — Adding a reference piece whose rights status is uncertain.

---

## 21. Common Anti-Patterns (v2.0 — examples to avoid)

```python
# ANTI-PATTERN 1: hardcoded major/minor
if spec.key.endswith("major"):
    progression = ["I", "IV", "V"]
else:
    progression = ["i", "iv", "V"]
# Fix: dispatch on tonal_system.kind, consult genre Skill

# ANTI-PATTERN 2: silent skip of phase
if not (project_dir / "trajectory.yaml").exists():
    trajectory = default_trajectory()  # silent fallback
# Fix: raise PhaseIncompleteError; phase 2 must complete first

# ANTI-PATTERN 3: one-size-fits-all evaluator
def score_harmony(score):
    return consonance_ratio(score) * 0.5 + tension_resolution(score) * 0.5
# Fix: weights must come from active genre Skill

# ANTI-PATTERN 4: melody assumed to exist
def generate_full_score(spec):
    melody = composer.generate(spec)
    return arrange_around(melody)
# Fix: dispatch on ensemble_template; deep_house has no melody

# ANTI-PATTERN 5: provenance entry without subagent
provenance.add(decision="chose D7 chord", rationale="modal interchange")
# Fix: must include agent="harmony_theorist", phase=DETAILED_FILLING, confidence=0.78

# ANTI-PATTERN 6: bypassing arch-lint
# from yao.render.audio_renderer import render  # in a generators/ file
# Fix: this violates layer boundary; if you genuinely need rendering, refactor

# ANTI-PATTERN 7: pedalboard as hard dependency
import pedalboard  # at module level in sound_design/__init__.py
# Fix: lazy import; degrade gracefully if missing
```

---

## 22. Guides (read when relevant)

| Guide | When to read |
|---|---|
| `.claude/guides/architecture.md` | Working across layers, adding modules |
| `.claude/guides/coding-conventions.md` | Writing any code |
| `.claude/guides/music-engineering.md` | Generating/modifying notes |
| `.claude/guides/testing.md` | Writing or running tests |
| `.claude/guides/workflow.md` | Planning a change |
| `.claude/agents/_protocol.md` (NEW v2.0) | Writing a subagent or modifying its messages |

Full design documentation: `PROJECT.md`.
Improvement findings and PR plan: `IMPROVEMENT.md`.

---

## 23. Closing Reminder

YaO v2.0 is about **removing assumptions** without breaking what already works. The 7-layer architecture, append-only provenance, and frozen dataclasses are load-bearing. The new layers (3.5 and 4) and new subagents extend the system; they do not replace it.

When in doubt:

- Read PROJECT.md for design rationale.
- Read IMPROVEMENT.md for the why behind v2.0 changes.
- Read the relevant `.claude/guides/*.md` for tactical detail.
- Ask the human conductor when music theory or cultural authenticity is at stake.

Build the orchestra well, so the conductor can lead it freely — across every genre.

---

**Project: You and Orchestra (YaO)**
*CLAUDE.md version: 2.0*
*Incorporates IMPROVEMENT.md findings C1–C6, Q1–Q5, A1–A3*
*Last updated: 2026-05-05*
