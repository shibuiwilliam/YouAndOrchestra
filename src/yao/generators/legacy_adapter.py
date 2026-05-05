"""Legacy adapter — bridges v1 CompositionSpec to the v2 pipeline.

DEPRECATED: This adapter exists for backward compatibility during Phase α.
It will be removed at the end of Phase β when all consumers have migrated
to the v2 pipeline (CompositionProject → MusicalPlan → ScoreIR).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import yao.generators.note  # noqa: F401 — trigger realizer registration
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

_DYNAMICS_TO_DENSITY: dict[str, float] = {
    "pp": 0.2,
    "p": 0.3,
    "mp": 0.4,
    "mf": 0.5,
    "f": 0.7,
    "ff": 0.85,
    "fff": 0.95,
}


def _v1_to_v2(spec: CompositionSpec) -> CompositionSpecV2:
    """Convert a v1 CompositionSpec to v2 for pipeline processing."""
    sections = [
        {
            "id": s.name,
            "bars": s.bars,
            "density": _DYNAMICS_TO_DENSITY.get(s.dynamics, 0.5),
            "dynamics": s.dynamics,
            "climax": False,
        }
        for s in spec.sections
    ]
    # Map v1 roles to v2-allowed roles (v2 doesn't have counter_melody)
    _role_map = {"counter_melody": "melody"}
    instruments = {inst.name: {"role": _role_map.get(inst.role, inst.role)} for inst in spec.instruments}

    # Estimate duration
    total_bars = sum(s.bars for s in spec.sections)
    ts_parts = spec.time_signature.split("/")
    beats_per_bar = int(ts_parts[0]) if len(ts_parts) == 2 else 4  # noqa: PLR2004
    duration = (total_bars * beats_per_bar * 60.0) / spec.tempo_bpm

    return CompositionSpecV2.model_validate(
        {
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
        }
    )


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
    traj = MultiDimensionalTrajectory.from_spec(trajectory) if trajectory else MultiDimensionalTrajectory.default()
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
) -> tuple[ScoreIR, MusicalPlan, ProvenanceLog]:
    """Full v1 → v2 pipeline: CompositionSpec → MusicalPlan → ScoreIR.

    This is the v2 equivalent of GeneratorBase.generate(). It goes through
    the full plan-first path.

    Args:
        spec: v1 CompositionSpec.
        trajectory: Optional v1 TrajectorySpec.

    Returns:
        Tuple of (ScoreIR, MusicalPlan, ProvenanceLog). The plan is returned
        so the Conductor can pass it to the Adversarial Critic gate.
    """
    plan, provenance = build_plan_from_v1(spec, trajectory)

    strategy = spec.generation.strategy
    if strategy not in NOTE_REALIZERS:
        # Fall back to rule_based if strategy not registered as realizer
        strategy = "rule_based"

    realizer = NOTE_REALIZERS[strategy]()
    seed = spec.generation.seed if spec.generation.seed is not None else 42
    temperature = spec.generation.temperature

    # Pass the original v1 spec so realizers can preserve key/tempo/instruments
    # during Phase α (the MusicalPlan doesn't carry global metadata yet).
    score = realizer.realize(plan, seed, temperature, provenance, original_spec=spec)
    return score, plan, provenance
