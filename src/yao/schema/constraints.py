"""Pydantic models for constraint specifications.

Implements a unified constraint system (PROJECT_IMPROVEMENT §5.5) that
generalizes negative space, instrument ranges, theory rules, and style
preferences into a single first-class abstraction.

Each constraint has:
- type: must / must_not / prefer / avoid
- scope: where it applies (global, section:name, instrument:name, bars:N-M)
- rule: what it checks
- severity: error / warning / hint

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from yao.errors import SpecValidationError


class Constraint(BaseModel):
    """A single musical constraint.

    Attributes:
        type: Whether this is a hard requirement or soft preference.
        scope: Where the constraint applies.
        rule: The rule to check (e.g., "no_parallel_fifths", "max_density:5").
        severity: How serious a violation is.
        description: Human-readable explanation.
    """

    type: Literal["must", "must_not", "prefer", "avoid"]
    scope: str = "global"
    rule: str
    severity: Literal["error", "warning", "hint"] = "warning"
    description: str = ""


class EnsembleConstraint(BaseModel):
    """A constraint on the interaction between two or more instrument parts.

    Unlike single-part Constraint, EnsembleConstraint expresses relationships
    *between* instruments (register separation, consonance, parallel motion).

    Attributes:
        rule: The ensemble rule to check.
        instruments: Which instruments are involved (empty = all pairs).
        scope: Section scope (global or section:name).
        severity: How serious a violation is.
        parameters: Rule-specific parameters (e.g., min_separation_semitones).
    """

    rule: Literal[
        "register_separation",
        "downbeat_consonance",
        "no_parallel_octaves",
        "no_frequency_collision",
        "bass_below_melody",
    ]
    instruments: list[str] = []
    scope: str = "global"
    severity: Literal["error", "warning", "hint"] = "warning"
    parameters: dict[str, float] = {}


class ConstraintsSpec(BaseModel):
    """Collection of constraints for a composition.

    Attributes:
        constraints: List of single-part constraints.
        ensemble_constraints: List of inter-part constraints.
    """

    constraints: list[Constraint] = []
    ensemble_constraints: list[EnsembleConstraint] = []

    @classmethod
    def from_yaml(cls, path: Path) -> ConstraintsSpec:
        """Load constraints from a YAML file.

        Args:
            path: Path to constraints YAML file.

        Returns:
            Validated ConstraintsSpec.

        Raises:
            SpecValidationError: If loading or validation fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load constraints: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Constraints YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Constraints validation failed: {e}") from e
