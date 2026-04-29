# Generator Development Guide

## How Generators Work

A generator takes a `CompositionSpec` (and optional `TrajectorySpec`) and produces a `ScoreIR` with full provenance. Every note, every chord, every rhythm decision is recorded.

## Creating a New Generator

### Step 1: Create the module

```python
# src/yao/generators/my_generator.py
from __future__ import annotations

from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.trajectory import TrajectorySpec


@register_generator("my_strategy")
class MyGenerator(GeneratorBase):
    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        prov = ProvenanceLog()
        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={"title": spec.title, "strategy": "my_strategy"},
            source="MyGenerator.generate",
            rationale="Starting generation with my custom strategy.",
        )

        # ... generate notes ...

        return score, prov
```

### Step 2: Register via import

Add to `src/cli/main.py`:
```python
import yao.generators.my_generator as _mg  # noqa: F401
```

### Step 3: Use via spec

```yaml
# composition.yaml
generation:
  strategy: my_strategy
  seed: 42
  temperature: 0.5
```

### Step 4: Write tests

```python
# tests/unit/test_my_generator.py
def test_generates_notes():
    gen = get_generator("my_strategy")
    score, prov = gen.generate(spec)
    assert len(score.all_notes()) > 0
    assert len(prov) > 0
```

## Rules for Generators

1. **Always return `(ScoreIR, ProvenanceLog)`** — no exceptions
2. **Record every decision** in provenance with a meaningful rationale
3. **Never hardcode velocity** — derive from `DYNAMICS_TO_VELOCITY` + trajectory
4. **Never silently clamp ranges** — raise `RangeViolationError` or skip the note
5. **Use `yao.ir.timing`** for all beat/tick/second conversions
6. **Use `yao.ir.notation`** for all note name/MIDI conversions
7. **Respect `GenerationConfig`** — use `spec.generation.seed` and `spec.generation.temperature`

## Existing Generators

### `rule_based` (deterministic)
- Scale-based melody with stepwise motion
- Root-note bass following I-IV-V-I
- Block chord harmonization with triads
- 4 rhythm patterns cycling per bar
- No randomness — same spec always produces same output

### `stochastic` (seeded randomness)
- Melodic contour shaping (arch, ascending, descending)
- Interval variety (steps, leaps of 3rds/4ths/5ths)
- Section-aware chord progressions (verse/chorus/bridge patterns)
- Diatonic 7th chords (temperature-dependent)
- 12 rhythm patterns with syncopation, dotted rhythms
- Walking bass with passing tones
- Velocity humanization (±5)
- Rest insertion for negative space
- Temperature: 0.0 = conservative, 1.0 = adventurous
