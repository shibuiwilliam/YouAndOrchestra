# YaO v2.0 Architecture Summary

> For new contributors: read this document alongside PROJECT.md and CLAUDE.md
> to understand the v2.0 architecture without reading source code.

## What Changed in v2.0

YaO v1.0 was implicitly biased toward Western tonal chamber and pop music.
v2.0 removes these assumptions while preserving engineering discipline.

### New Layers

| Layer | Module | Purpose |
|-------|--------|---------|
| 3.5 | `src/yao/sound_design/` | Synthesis patches, effect chains, sample packs |
| 4 | `src/yao/perception/` | Feature extraction, reference matching, distance metrics |

### New Schema Models

| Model | File | Purpose |
|-------|------|---------|
| `TonalSystem` | `schema/tonal_system.py` | Polymorphic tonal framework (10 kinds) |
| `SoundDesignSpec` | `schema/sound_design.py` | Per-stem patch and effect chain config |
| `ReferencesSpec` | `schema/references.py` | Positive/negative aesthetic anchors |

### New Generators

| Generator | File | Strategy |
|-----------|------|----------|
| `loop_evolution` | `generators/loop_evolution.py` | Core loop + layer evolution, arrangement parsing |

### New Evaluators

| Evaluator | File | Metrics |
|-----------|------|---------|
| Seamlessness | `verify/seamlessness.py` | Boundary cutoff, energy/pitch continuity |
| Singability | `verify/singability.py` | Awkward leaps, breath violations, tessitura strain |
| Harmony (v2) | `verify/evaluator.py` | Tonal-system-aware consonance and variety |

### New Infrastructure

| Component | File | Purpose |
|-----------|------|---------|
| Phase Protocol | `conductor/protocol.py` | Six-phase enforcement with PhaseIncompleteError |
| Subagent Message | `conductor/subagent_message.py` | Standardized message format |
| Feature Extractors | `perception/feature_extractors/` | 7 symbolic extractors |
| Genre Skill Loader | `skills/genre_skill.py` | v2.0 template validation |

## Design Decisions

### 1. TonalSystem Dispatch (PR-2)

Instead of `if mode == "major"`, all harmony/evaluation code dispatches on
`TonalSystem.kind`. This allows blues b3 to be a feature (not a defect),
drone to skip pitch_class_variety, and atonal to skip consonance metrics.

Legacy specs with `key: "D minor"` are auto-promoted via `promote_legacy_key()`.

### 2. Lazy Sound Design (PR-3)

`pedalboard` is optional. The import is wrapped in try/except at the module
level. When absent, `SOUND_DESIGN_AVAILABLE = False` and the system degrades
to MIDI-only output without crashing.

### 3. Ensemble Templates (PR-1)

Genre Skills declare which subagents are active/inactive. Deep house doesn't
use the Composer subagent. Ambient doesn't use Rhythm Architect. The Producer
validates coherence.

### 4. Six-Phase Enforcement (PR-6)

Phases must execute in order. Skipping raises `PhaseIncompleteError`.
`--force-phase` exists for debugging only and emits a warning.

### 5. Reference-Driven Evaluation (PR-4)

7 symbolic feature extractors produce a 20-dimensional vector. Weighted
Euclidean distance to positive references drives adaptation decisions.

## File Map for New Contributors

```
src/yao/
├── schema/tonal_system.py      ← Start here: understand the 10 tonal kinds
├── schema/sound_design.py      ← Then: how timbre is specified
├── skills/genre_skill.py       ← Then: how genres are loaded and validated
├── conductor/protocol.py       ← Then: the 6-phase workflow
├── perception/feature_extractors/  ← Then: how quality is measured
├── generators/loop_evolution.py    ← Then: how loops are generated
├── verify/singability.py       ← Then: vocal constraints
└── verify/seamlessness.py      ← Then: loop boundary evaluation
```

## Test Categories

| Directory | Tests | Purpose |
|-----------|-------|---------|
| `tests/tonal_systems/` | 15 | TonalSystem schema, promotion, evaluation |
| `tests/unit/skills/` | 15 | Genre skill loading and validation |
| `tests/unit/test_sound_design.py` | 26 | Sound design patches and effects |
| `tests/unit/perception/` | 32 | Feature extraction and reference matching |
| `tests/unit/test_phase_protocol.py` | 28 | Phase enforcement |
| `tests/unit/test_subagent_protocol.py` | 12 | Subagent message format |
| `tests/unit/test_loop_evolution.py` | 20 | Loop generator |
| `tests/unit/test_vocal_track.py` | 12 | Singability evaluation |
| `tests/integration/test_v2_definition_of_done.py` | 11 | End-to-end v2.0 criteria |
