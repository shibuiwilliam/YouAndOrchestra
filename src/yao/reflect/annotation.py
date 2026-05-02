"""Annotation models — time-tagged human feedback on compositions.

Annotations capture subjective listening judgments at specific time ranges.
They feed into the Reflection Layer for style profile learning.

Schema matches PROJECT.md §7.9 annotations.json format.

Belongs to Layer 7 (Reflection).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError


class Annotation(BaseModel):
    """A single time-tagged annotation.

    Attributes:
        time_start_sec: Start of the annotated region in seconds.
        time_end_sec: End of the annotated region in seconds.
        bars: Optional bar numbers corresponding to the region.
        sentiment: Overall sentiment (positive, negative, neutral).
        tags: Descriptive tags (e.g., memorable_motif, too_busy).
        comment: Optional free-text comment.
    """

    time_start_sec: float
    time_end_sec: float
    bars: list[int] = []  # noqa: RUF012
    sentiment: Literal["positive", "negative", "neutral"]
    tags: list[str] = []  # noqa: RUF012
    comment: str = ""

    @field_validator("time_end_sec")
    @classmethod
    def end_after_start(cls, v: float, info: object) -> float:
        """End time must be >= start time."""
        start = getattr(info, "data", {}).get("time_start_sec", 0.0)
        if isinstance(start, float) and v < start:
            raise SpecValidationError(
                f"time_end_sec ({v}) must be >= time_start_sec ({start})",
                field="time_end_sec",
            )
        return v


class AnnotationFile(BaseModel):
    """A collection of annotations for an iteration.

    Attributes:
        timestamp_iso: When annotations were saved (ISO 8601).
        iteration: Iteration identifier (e.g., "v005").
        annotations: List of time-tagged annotations.
    """

    timestamp_iso: str = ""
    iteration: str = ""
    annotations: list[Annotation] = []  # noqa: RUF012

    def save(self, path: Path) -> None:
        """Save annotations to a JSON file.

        Args:
            path: Output path for annotations.json.
        """
        if not self.timestamp_iso:
            self.timestamp_iso = datetime.now(tz=UTC).isoformat()

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> AnnotationFile:
        """Load annotations from a JSON file.

        Args:
            path: Path to annotations.json.

        Returns:
            Parsed AnnotationFile.

        Raises:
            SpecValidationError: If the file is invalid.
        """
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(
                f"Failed to load annotations: {e}",
                field="annotations",
            ) from e
