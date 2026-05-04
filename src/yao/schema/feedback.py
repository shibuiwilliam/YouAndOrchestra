"""Pydantic models for feedback.yaml — structured human feedback.

Defines the schema for bar-level tagged feedback that the Conductor
can translate into generation adaptations.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from yao.errors import SpecValidationError


class FeedbackTag(StrEnum):
    """Preset feedback tags for bar-level annotation."""

    LOVED = "loved"
    BORING = "boring"
    WEAK_CLIMAX = "weak_climax"
    TOO_DENSE = "too_dense"
    TOO_SPARSE = "too_sparse"
    WRONG_EMOTION = "wrong_emotion"
    CLICHE = "cliche"
    CONFUSING = "confusing"


class FeedbackSeverity(StrEnum):
    """Severity of a feedback entry."""

    POSITIVE = "positive"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class HumanFeedbackEntry(BaseModel):
    """A single bar-level feedback entry.

    Attributes:
        bar: The bar number (1-indexed) this feedback targets.
        bars: Optional list of bar numbers for multi-bar feedback.
        tag: Feedback tag from the preset vocabulary.
        severity: How important this feedback is.
        note: Optional free-text clarification.
    """

    bar: int | None = None
    bars: list[int] = Field(default_factory=list)
    tag: FeedbackTag
    severity: FeedbackSeverity = FeedbackSeverity.MINOR
    note: str = ""

    @field_validator("bar")
    @classmethod
    def bar_positive(cls, v: int | None) -> int | None:
        """Bar numbers must be positive."""
        if v is not None and v < 1:
            raise SpecValidationError(
                f"Bar number must be >= 1, got {v}",
                field="bar",
            )
        return v

    @property
    def target_bars(self) -> list[int]:
        """Return all targeted bars as a list.

        Returns:
            List of 1-indexed bar numbers.
        """
        if self.bars:
            return list(self.bars)
        if self.bar is not None:
            return [self.bar]
        return []


class FeedbackSpec(BaseModel):
    """Complete feedback specification for an iteration.

    Parsed from ``feedback.yaml`` files produced by ``yao annotate``
    or hand-written by users.

    Attributes:
        iteration: Which iteration this feedback targets (e.g. "v002").
        human_feedback: List of bar-level feedback entries.
    """

    iteration: str = ""
    human_feedback: list[HumanFeedbackEntry] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> FeedbackSpec:
        """Load feedback from a YAML file.

        Args:
            path: Path to feedback.yaml.

        Returns:
            Validated FeedbackSpec.

        Raises:
            SpecValidationError: If loading or validation fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load feedback YAML: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Feedback YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Feedback validation failed: {e}") from e
