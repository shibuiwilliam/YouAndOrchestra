"""Base class and registry for plan generators.

Plan generators produce partial MusicalPlan components (form, harmony, etc.)
from a CompositionSpecV2 and trajectory. They are Step 1–5 of the 7-step
pipeline (PROJECT.md §8).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2

PLAN_GENERATORS: dict[str, type[PlanGeneratorBase]] = {}


def register_plan_generator(name: str) -> Any:
    """Decorator to register a plan generator class by name.

    Args:
        name: Unique name (e.g., "rule_based_form").

    Returns:
        Decorator that registers the class.
    """

    def decorator(cls: type[PlanGeneratorBase]) -> type[PlanGeneratorBase]:
        PLAN_GENERATORS[name] = cls
        return cls

    return decorator


class PlanGeneratorBase(ABC):
    """Abstract base for plan generators.

    Each plan generator contributes one or more fields to the MusicalPlan.
    It receives the spec and trajectory, and returns a dict of plan components.
    """

    name: str

    @abstractmethod
    def generate(
        self,
        spec: CompositionSpecV2,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> dict[str, Any]:
        """Generate partial plan components.

        Args:
            spec: The v2 composition specification.
            trajectory: Multi-dimensional trajectory (control signal).
            provenance: Provenance log to record decisions.

        Returns:
            Dict with plan component keys (e.g., {"form": SongFormPlan(...)}).
        """
        ...
