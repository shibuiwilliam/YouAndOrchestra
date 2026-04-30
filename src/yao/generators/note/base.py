"""Base class and registry for note realizers.

Note realizers convert a MusicalPlan (MPIR) into concrete ScoreIR notes.
They are Step 6 of the 7-step pipeline (PROJECT.md §8).

IMPORTANT: Note realizers must NOT import CompositionSpec or read spec
data directly. All musical information comes through the MusicalPlan.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec

NOTE_REALIZERS: dict[str, type[NoteRealizerBase]] = {}


def register_note_realizer(name: str) -> Any:
    """Decorator to register a note realizer class by name.

    Args:
        name: Unique name (e.g., "rule_based", "stochastic").

    Returns:
        Decorator that registers the class.
    """

    def decorator(cls: type[NoteRealizerBase]) -> type[NoteRealizerBase]:
        NOTE_REALIZERS[name] = cls
        return cls

    return decorator


class NoteRealizerBase(ABC):
    """Abstract base for note realizers.

    A note realizer takes a complete MusicalPlan and produces a ScoreIR
    with concrete notes. It does NOT read CompositionSpec directly.
    """

    name: str

    @abstractmethod
    def realize(
        self,
        plan: MusicalPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
        original_spec: CompositionSpec | None = None,
    ) -> ScoreIR:
        """Realize a MusicalPlan into concrete notes.

        Args:
            plan: The musical plan to realize.
            seed: Random seed for reproducibility.
            temperature: Variation control (0.0–1.0).
            provenance: Provenance log to record decisions.
            original_spec: Optional original v1 spec to preserve metadata
                during Phase α migration.

        Returns:
            ScoreIR with concrete notes.
        """
        ...
