"""Base class for critique rules.

Every critique rule inherits CritiqueRule and implements detect().
Rules emit structured Finding objects, never free text.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.types import Finding, Role


class CritiqueRule(ABC):
    """Abstract base for all critique rules.

    Subclasses must set rule_id and role, and implement detect().
    """

    rule_id: str
    role: Role

    @abstractmethod
    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect issues in a MusicalPlan.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification (for reference values).

        Returns:
            List of Finding objects. Empty if no issues found.
        """
        ...
