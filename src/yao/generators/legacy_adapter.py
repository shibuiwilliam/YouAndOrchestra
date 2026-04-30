"""Legacy adapter — bridges v1 CompositionSpec to the v2 pipeline.

DEPRECATED: This adapter exists for backward compatibility during Phase α.
It will be removed at the end of Phase β when all consumers have migrated
to the v2 pipeline (CompositionProject → MusicalPlan → ScoreIR).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from yao.generators.note.base import NOTE_REALIZERS
from yao.generators.plan.orchestrator import PlanOrchestrator
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.score_ir import ScoreIR
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec
from yao.schema.trajectory import TrajectorySpec


def _v1_to_v2(spec: CompositionSpec) -> CompositionSpecV2:
    """Convert a v1 CompositionSpec to v2 for pipeline processing."""
    sections = [
        {
            "id": s.name,
            "bars": s.bars,
            "density": 0.5,
            "climax": False,
        }
        for s in spec.sections
    ]
    instruments = {
        inst.name: {"role": inst.role}
        for inst in spec.instruments
    }

    # Estimate duration
    total_bars = sum(s.bars for s in spec.sections)
    ts_parts = spec.time_signature.split("/")
    beats_per_bar = int(ts_parts[0]) if len(ts_parts) == 2 else 4  # noqa: PLR2004
    duration = (total_bars * beats_per_bar * 60.0) / spec.tempo_bpm

    return CompositionSpecV2.model_validate({
        "version": "2",
        "identity": {"title": spec.title, "duration_sec": duration},
        "global": {
            "key": spec.key,
            "bpm": spec.tempo_bpm,
            "time_signature": spec.time_signature,
            "genre": spec.genre,
        },
        "form": {"sections": sections},
        "arrangement": {"instruments": instruments},
        "generation": {
            "strategy": spec.generation.strategy,
            "seed": spec.generation.seed,
            "temperature": spec.generation.temperature,
        },
    })


def build_plan_from_v1(
    spec: CompositionSpec,
    trajectory: TrajectorySpec | None = None,
) -> tuple[MusicalPlan, ProvenanceLog]:
    """Build a MusicalPlan from a v1 spec via the v2 pipeline.

    Args:
        spec: v1 CompositionSpec.
        trajectory: Optional v1 TrajectorySpec.

    Returns:
        Tuple of (MusicalPlan, ProvenanceLog).
    """
    spec_v2 = _v1_to_v2(spec)
    traj = (
        MultiDimensionalTrajectory.from_spec(trajectory)
        if trajectory
        else MultiDimensionalTrajectory.default()
    )
    intent = IntentSpec(text="", keywords=[])
    provenance = ProvenanceLog()

    provenance.record(
        layer="generator",
        operation="legacy_v1_to_v2",
        parameters={"title": spec.title, "strategy": spec.generation.strategy},
        source="legacy_adapter.build_plan_from_v1",
        rationale="Converting v1 spec to v2 pipeline via legacy adapter.",
    )

    orchestrator = PlanOrchestrator(plan_strategy="rule_based")
    plan = orchestrator.build_plan(spec_v2, traj, intent, provenance)
    return plan, provenance


def generate_via_v2_pipeline(
    spec: CompositionSpec,
    trajectory: TrajectorySpec | None = None,
) -> tuple[ScoreIR, ProvenanceLog]:
    """Full v1 → v2 pipeline: CompositionSpec → MusicalPlan → ScoreIR.

    This is the v2 equivalent of GeneratorBase.generate(). It goes through
    the full plan-first path.

    Args:
        spec: v1 CompositionSpec.
        trajectory: Optional v1 TrajectorySpec.

    Returns:
        Tuple of (ScoreIR, ProvenanceLog).
    """
    plan, provenance = build_plan_from_v1(spec, trajectory)

    strategy = spec.generation.strategy
    if strategy not in NOTE_REALIZERS:
        # Fall back to rule_based if strategy not registered as realizer
        strategy = "rule_based"

    realizer = NOTE_REALIZERS[strategy]()
    seed = spec.generation.seed if spec.generation.seed is not None else 42
    temperature = spec.generation.temperature

    score = realizer.realize(plan, seed, temperature, provenance)
    return score, provenance
