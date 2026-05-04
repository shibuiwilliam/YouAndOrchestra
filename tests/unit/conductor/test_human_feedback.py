"""Tests for the human feedback to adaptation converter."""

from __future__ import annotations

from yao.conductor.human_feedback import (
    convert_feedback_to_adaptations,
    summarize_adaptations,
)
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec
from yao.schema.feedback import (
    FeedbackSeverity,
    FeedbackSpec,
    FeedbackTag,
    HumanFeedbackEntry,
)


def _minimal_spec() -> CompositionSpec:
    return CompositionSpec(
        title="Test",
        key="C major",
        tempo_bpm=120.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[
            SectionSpec(name="intro", bars=4, dynamics="mp"),
            SectionSpec(name="verse", bars=8, dynamics="mf"),
        ],
    )


class TestConvertFeedback:
    """Tests for tag → adaptation conversion."""

    def test_weak_climax_increases_dynamics(self) -> None:
        """Weak climax tag produces dynamics and temperature adaptations."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[
                HumanFeedbackEntry(bar=6, tag=FeedbackTag.WEAK_CLIMAX, severity=FeedbackSeverity.MAJOR),
            ],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        assert len(adaptations) >= 1
        reasons = [a.reason for a in adaptations]
        assert any("climax" in r.lower() for r in reasons)

    def test_boring_increases_temperature(self) -> None:
        """Boring tag increases temperature."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[HumanFeedbackEntry(bar=10, tag=FeedbackTag.BORING)],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        temp_adaptations = [a for a in adaptations if "temperature" in a.field]
        assert len(temp_adaptations) > 0
        assert float(temp_adaptations[0].new_value) > spec.generation.temperature

    def test_loved_produces_preserve(self) -> None:
        """Loved tag marks bars for preservation."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[
                HumanFeedbackEntry(bars=[22, 24], tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE),
            ],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        preserve = [a for a in adaptations if "preserve" in a.field]
        assert len(preserve) == 1

    def test_too_dense_reduces_temperature(self) -> None:
        """Too dense tag reduces temperature."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[HumanFeedbackEntry(bar=5, tag=FeedbackTag.TOO_DENSE)],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        temp_adaptations = [a for a in adaptations if "temperature" in a.field]
        assert len(temp_adaptations) > 0
        assert float(temp_adaptations[0].new_value) < spec.generation.temperature

    def test_cliche_changes_seed(self) -> None:
        """Cliche tag changes seed and increases temperature."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[HumanFeedbackEntry(bar=3, tag=FeedbackTag.CLICHE)],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        seed_adaptations = [a for a in adaptations if "seed" in a.field]
        assert len(seed_adaptations) > 0

    def test_empty_feedback_no_adaptations(self) -> None:
        """Empty feedback produces no adaptations."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(iteration="v001")
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        assert len(adaptations) == 0

    def test_multiple_entries_combine(self) -> None:
        """Multiple feedback entries produce combined adaptations."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[
                HumanFeedbackEntry(bar=3, tag=FeedbackTag.BORING),
                HumanFeedbackEntry(bar=8, tag=FeedbackTag.WEAK_CLIMAX),
                HumanFeedbackEntry(bars=[10, 11], tag=FeedbackTag.LOVED),
            ],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        assert len(adaptations) >= 3  # noqa: PLR2004


class TestSummarize:
    """Test summarize_adaptations."""

    def test_empty(self) -> None:
        """Empty list returns 'no adaptations'."""
        result = summarize_adaptations([])
        assert "No adaptations" in result

    def test_non_empty(self) -> None:
        """Non-empty list produces multi-line summary."""
        spec = _minimal_spec()
        feedback = FeedbackSpec(
            iteration="v001",
            human_feedback=[HumanFeedbackEntry(bar=3, tag=FeedbackTag.BORING)],
        )
        adaptations = convert_feedback_to_adaptations(feedback, spec)
        result = summarize_adaptations(adaptations)
        assert "Boring" in result
