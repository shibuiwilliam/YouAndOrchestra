"""Tests for the feedback.yaml schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.errors import SpecValidationError
from yao.schema.feedback import (
    FeedbackSeverity,
    FeedbackSpec,
    FeedbackTag,
    HumanFeedbackEntry,
)


class TestHumanFeedbackEntry:
    """Tests for individual feedback entries."""

    def test_basic_entry(self) -> None:
        """Entry with bar and tag."""
        entry = HumanFeedbackEntry(bar=8, tag=FeedbackTag.WEAK_CLIMAX)
        assert entry.target_bars == [8]
        assert entry.severity == FeedbackSeverity.MINOR

    def test_multi_bar_entry(self) -> None:
        """Entry targeting multiple bars."""
        entry = HumanFeedbackEntry(bars=[22, 24], tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE)
        assert entry.target_bars == [22, 24]

    def test_invalid_bar_raises(self) -> None:
        """Bar 0 or negative raises validation error."""
        with pytest.raises(SpecValidationError):
            HumanFeedbackEntry(bar=0, tag=FeedbackTag.BORING)

    def test_all_tags_valid(self) -> None:
        """All 8 preset tags are valid."""
        for tag in FeedbackTag:
            entry = HumanFeedbackEntry(bar=1, tag=tag)
            assert entry.tag == tag


class TestFeedbackSpec:
    """Tests for the complete FeedbackSpec."""

    def test_empty_feedback(self) -> None:
        """Empty feedback is valid."""
        spec = FeedbackSpec(iteration="v001")
        assert len(spec.human_feedback) == 0

    def test_from_yaml(self, tmp_path: Path) -> None:
        """Load from YAML file."""
        yaml_content = """\
iteration: v002
human_feedback:
  - bar: 8
    tag: weak_climax
    severity: major
    note: "expected more buildup"
  - bars: [22, 24]
    tag: loved
    severity: positive
    note: "great counter-melody"
  - bar: 16
    tag: boring
"""
        path = tmp_path / "feedback.yaml"
        path.write_text(yaml_content)

        spec = FeedbackSpec.from_yaml(path)
        assert spec.iteration == "v002"
        assert len(spec.human_feedback) == 3
        assert spec.human_feedback[0].tag == FeedbackTag.WEAK_CLIMAX
        assert spec.human_feedback[0].severity == FeedbackSeverity.MAJOR
        assert spec.human_feedback[1].target_bars == [22, 24]

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        """Invalid YAML raises SpecValidationError."""
        path = tmp_path / "bad.yaml"
        path.write_text("not: [a: valid: yaml")
        with pytest.raises(SpecValidationError):
            FeedbackSpec.from_yaml(path)
