"""Plan orchestrator — runs plan generators in sequence to build a MusicalPlan.

This is the entry point for the plan generation pipeline. It runs
form → harmony (Phase α) and will add motif → drum → arrangement in Phase β.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

# Ensure plan generators are registered
import yao.generators.plan.form_planner as _fp  # noqa: F401
import yao.generators.plan.harmony_planner as _hp  # noqa: F401
from yao.errors import SpecValidationError
from yao.generators.plan.base import PLAN_GENERATORS
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec


class PlanOrchestrator:
    """Runs plan generators in sequence and builds a MusicalPlan.

    Phase α: form + harmony.
    Phase β: adds motif, drum, arrangement planners.
    """

    def __init__(self, plan_strategy: str = "rule_based") -> None:
        """Initialize with a plan strategy name.

        Args:
            plan_strategy: Strategy prefix (e.g., "rule_based").
                Looks up "{strategy}_form", "{strategy}_harmony" in registry.
        """
        form_key = f"{plan_strategy}_form"
        harmony_key = f"{plan_strategy}_harmony"

        if form_key not in PLAN_GENERATORS:
            available = ", ".join(sorted(PLAN_GENERATORS.keys()))
            msg = f"Plan generator '{form_key}' not found. Available: {available}"
            raise SpecValidationError(msg, field="generation.plan_strategy")

        self._form_planner = PLAN_GENERATORS[form_key]()
        self._harmony_planner = PLAN_GENERATORS[harmony_key]()

    def build_plan(
        self,
        spec: CompositionSpecV2,
        trajectory: MultiDimensionalTrajectory,
        intent: IntentSpec,
        provenance: ProvenanceLog,
    ) -> MusicalPlan:
        """Build a MusicalPlan by running all plan generators.

        Args:
            spec: The v2 composition specification.
            trajectory: Multi-dimensional trajectory.
            intent: The piece's intent.
            provenance: Provenance log.

        Returns:
            A MusicalPlan (Phase α: form + harmony populated).
        """
        form_result = self._form_planner.generate(spec, trajectory, provenance)
        harmony_result = self._harmony_planner.generate(spec, trajectory, provenance)

        return MusicalPlan(
            form=form_result["form"],
            harmony=harmony_result["harmony"],
            trajectory=trajectory,
            intent=intent,
            provenance=provenance,
            # Phase β
            motifs_phrases=None,
            arrangement=None,
            drums=None,
        )
