# Generator Development Guide

## How Generation Works

YaO uses a two-stage generation architecture (v2.0):

1. **Plan Generators** take a `CompositionSpec` and produce a `MusicalPlan` (CPIR) — structural and harmonic decisions *before* any notes are placed.
2. **Note Realizers** take a `MusicalPlan` and produce a `ScoreIR` — concrete notes faithfully realizing the plan.

```
CompositionSpec → PlanGenerator → MusicalPlan → NoteRealizer → ScoreIR
```

Every step returns a `ProvenanceLog` recording every decision.

## Legacy Generators (v1, active during Phase alpha)

During Phase alpha, the v1 generators still work and are the primary path for composition. They take a spec directly and produce notes.

```python
class GeneratorBase(ABC):
    @abstractmethod
    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]: ...
```

Register with `@register_generator("name")`. Select at runtime with `get_generator("name")`.

Currently registered: `rule_based`, `stochastic`.

## Creating a Plan Generator (v2.0)

Plan generators decide *what* to play — form, harmony, motifs — without placing any concrete notes.

### Step 1: Create the module

```python
# src/yao/generators/plan/my_planner.py
from __future__ import annotations

from yao.generators.plan.base import PlanGeneratorBase, register_plan_generator
from yao.ir.plan.song_form import SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec


@register_plan_generator("my_form_planner")
class MyFormPlanner(PlanGeneratorBase):
    def plan(
        self,
        spec: CompositionSpec,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> SongFormPlan:
        provenance.record(
            layer="plan_generator",
            operation="plan_form",
            parameters={"title": spec.title, "strategy": "my_form_planner"},
            source="MyFormPlanner.plan",
            rationale="Planning song form with my custom approach.",
        )

        # ... build form plan ...

        return form_plan
```

### Step 2: Register via import

Add to the appropriate `__init__.py` or `cli/main.py`:
```python
import yao.generators.plan.my_planner as _mp  # noqa: F401
```

## Creating a Note Realizer (v2.0)

Note realizers turn a `MusicalPlan` into concrete notes. They must faithfully realize the plan, not make structural decisions.

### Step 1: Create the module

```python
# src/yao/generators/note/my_realizer.py
from __future__ import annotations

from yao.generators.note.base import NoteRealizerBase, register_note_realizer
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog
from yao.verify.recoverable import RecoverableDecision


@register_note_realizer("my_realizer")
class MyNoteRealizer(NoteRealizerBase):
    def realize(
        self,
        plan: MusicalPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        provenance.record(
            layer="note_realizer",
            operation="realize_notes",
            parameters={"seed": seed, "temperature": temperature},
            source="MyNoteRealizer.realize",
            rationale="Realizing notes from musical plan.",
        )

        # ... realize notes from plan ...

        # If a note must be adjusted (e.g., out of range):
        if proposed_note < instrument.range_min:
            decision = RecoverableDecision(
                code="NOTE_OUT_OF_RANGE",
                severity="warning",
                original_value=proposed_note,
                recovered_value=instrument.range_min,
                reason="Note below instrument range",
                musical_impact="Pitch shifted up to minimum",
                suggested_fix=["Use a bass instrument with wider range"],
            )
            provenance.record_recoverable(decision)
            proposed_note = decision.recovered_value

        return score
```

### Step 2: Use via spec

```yaml
# composition.yaml
generation:
  plan_strategy: "rule_based"      # picks plan generators
  realize_strategy: "my_realizer"  # picks note realizer
  seed: 42
  temperature: 0.5
```

### Step 3: Write tests

```python
# tests/unit/test_my_realizer.py
def test_realizes_notes_from_plan():
    realizer = get_note_realizer("my_realizer")
    score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
    assert len(score.all_notes()) > 0
    assert len(prov) > 0

def test_trajectory_compliance():
    # High tension must produce measurably different output than low tension
    ...
```

## Rules for All Generators

1. **Plan generators return plan objects + provenance. Note realizers return `ScoreIR` + provenance.** No exceptions.
2. **Record every decision** in provenance with a meaningful rationale.
3. **Never hardcode velocity** — derive from `DYNAMICS_TO_VELOCITY` + trajectory tension.
4. **Never silently clamp ranges** — raise `RangeViolationError` or emit a `RecoverableDecision`.
5. **Use `yao.ir.timing`** for all beat/tick/second conversions.
6. **Use `yao.ir.notation`** for all note name/MIDI conversions.
7. **Respect `GenerationConfig`** — use `spec.generation.seed` and `spec.generation.temperature`.
8. **Plans before notes** (v2.0) — structural decisions belong in plan generators, not note realizers.
9. **Trajectory is a control signal** (v2.0) — when trajectory values change, your generator output must change measurably.

## Existing Generators

### Legacy `rule_based` (deterministic)
- Scale-based melody with stepwise motion
- Root-note bass following I-IV-V-I
- Block chord harmonization with triads
- 4 rhythm patterns cycling per bar
- No randomness — same spec always produces same output
- Good for baselines and golden tests

### Legacy `stochastic` (seeded randomness)
- **Melodic contour shaping** — arch, ascending, descending, wave patterns with position-aware biases
- **Interval variety** — steps, leaps of 3rds/4ths/5ths (temperature-dependent)
- **Section-aware chord progressions** — different patterns for intro, verse, chorus, bridge, outro
- **Diatonic 7th chords** — maj7, min7, dom7 (probability increases with temperature)
- **12 melody rhythm patterns** — syncopation, dotted rhythms, pickup eighths, mixed patterns
- **6 bass rhythm patterns** — whole notes, walking quarters, root-fifth patterns
- **6 rhythm-part patterns** — straight eighths, syncopated, offbeat emphasis
- **Walking bass** with passing tones and approach notes
- **Velocity humanization** — dynamics-derived with trajectory tension modifier
- **Rest insertion** for negative space
- **Per-instrument deterministic RNG** — master_seed:instrument:section for reproducibility
- **Temperature semantics**: 0.0 = conservative (mostly steps, basic chords), 1.0 = adventurous (leaps, 7th chords, complex rhythms)

### v2.0 Plan Generators (Phase alpha)
- **`rule_based_form`** — Generates `SongFormPlan` from spec sections
- **`rule_based_harmony`** — Generates `HarmonyPlan` with chord events per section

### v2.0 Note Realizers (Phase alpha)
- Being built — will wrap the logic from legacy generators into the two-stage pipeline

## Planned Generators

- **Markov chain** — Probabilistic transitions learned from corpus
- **Constraint solver** — Backtracking search with hard constraints
- **AI bridge** — External model integration via API
