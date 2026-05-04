"""Arrangement operation base class and registry.

Defines the ArrangementOperation ABC that all arrangement transformations
implement. Operations are registered via ``@register_arrangement("name")``
and looked up by name.

Belongs to the arrange/ package.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog


class Preservable(StrEnum):
    """Aspects of a composition that an operation may preserve."""

    MELODY = "melody"
    HARMONY = "harmony"
    RHYTHM = "rhythm"
    FORM = "form"
    NOTES = "notes"
    INTERVALS = "intervals"
    INSTRUMENTS = "instruments"


class ArrangementOperation(ABC):
    """Base class for arrangement transformations.

    Each operation transforms a ScoreIR into a new ScoreIR while
    preserving certain aspects (declared via ``preserves``).
    Every operation must record provenance for all changes made.
    """

    @abstractmethod
    def apply(
        self,
        source: ScoreIR,
        params: dict[str, Any],
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        """Apply this transformation to a ScoreIR.

        Args:
            source: The input ScoreIR to transform.
            params: Operation-specific parameters from arrangement.yaml.
            provenance: Provenance log to record decisions in.

        Returns:
            Transformed ScoreIR.
        """
        ...

    @property
    @abstractmethod
    def preserves(self) -> frozenset[Preservable]:
        """What this operation guarantees to preserve."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable operation name."""
        ...


# ── Registry ──────────────────────────────────────────────────────────────

_ARRANGEMENT_REGISTRY: dict[str, type[ArrangementOperation]] = {}


def register_arrangement(name: str) -> Any:
    """Decorator to register an ArrangementOperation by name.

    Args:
        name: Registry key (e.g. "reharmonize", "transpose").

    Returns:
        Class decorator.
    """

    def decorator(cls: type[ArrangementOperation]) -> type[ArrangementOperation]:
        _ARRANGEMENT_REGISTRY[name] = cls
        return cls

    return decorator


def get_arrangement(name: str) -> ArrangementOperation:
    """Look up and instantiate an arrangement operation.

    Args:
        name: Registered operation name.

    Returns:
        An instance of the operation.

    Raises:
        SpecValidationError: If the name is not registered.
    """
    from yao.errors import SpecValidationError

    cls = _ARRANGEMENT_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_ARRANGEMENT_REGISTRY.keys()))
        raise SpecValidationError(
            f"Unknown arrangement operation '{name}'. Available: {available}",
            field="transform.operation",
        )
    return cls()


def registered_arrangements() -> dict[str, type[ArrangementOperation]]:
    """Return the full arrangement operation registry.

    Returns:
        Dict mapping names to operation classes.
    """
    return dict(_ARRANGEMENT_REGISTRY)
