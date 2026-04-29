"""Abstract base class for all generators.

Generators belong to Layer 2 (Generation). They consume Layer 1 specs
and produce Layer 3 IR objects. Every generator MUST return a ProvenanceLog
alongside the ScoreIR (Principle 2: explainability).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.trajectory import TrajectorySpec


class GeneratorBase(ABC):
    """Abstract base for composition generators.

    All generators follow the same contract: they take a composition spec
    (and optional trajectory) and produce a ScoreIR with full provenance.
    """

    @abstractmethod
    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a composition from a specification.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory specification for dynamic shaping.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        ...
