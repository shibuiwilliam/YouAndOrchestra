"""Tests for GenreCritic — genre-specific anti-pattern detection."""

from __future__ import annotations

import pytest

from yao.generators.melody.phrase_aware import PhraseAwareGenerator
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.melodic_profile import load_melodic_profile
from yao.verify.genre_critic import CritiqueReport, GenreCritic

TIER_1_GENRES = ["bebop_jazz", "j_pop_ballad", "classical_romantic", "lofi_hiphop", "rock_classic"]


def _make_spec(genre: str = "bebop_jazz", seed: int = 42) -> CompositionSpec:
    return CompositionSpec(
        title="Test",
        genre=genre,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8), SectionSpec(name="chorus", bars=8)],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


class TestGenreCritic:
    """Tests for the GenreCritic."""

    def test_critique_returns_report(self) -> None:
        """Critique produces a CritiqueReport."""
        spec = _make_spec("bebop_jazz")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("bebop_jazz")
        critic = GenreCritic()

        report = critic.critique(score, profile)

        assert isinstance(report, CritiqueReport)
        assert report.genre == "bebop_jazz"

    def test_report_has_conformity_scores(self) -> None:
        """Report includes genre conformity scores."""
        spec = _make_spec("classical_romantic")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("classical_romantic")
        critic = GenreCritic()

        report = critic.critique(score, profile)

        assert "overall_genre_conformity" in report.conformity_scores
        assert 0.0 <= report.conformity_scores["overall_genre_conformity"] <= 1.0

    def test_report_has_coherence_score(self) -> None:
        """Report includes motif coherence score."""
        spec = _make_spec("lofi_hiphop")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("lofi_hiphop")
        critic = GenreCritic()

        report = critic.critique(score, profile)

        assert 0.0 <= report.coherence_score <= 1.0

    def test_issue_severity_levels(self) -> None:
        """Issues have valid severity levels."""
        spec = _make_spec("bebop_jazz")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("bebop_jazz")
        critic = GenreCritic()

        report = critic.critique(score, profile)

        valid_severities = {"critical", "major", "minor", "hint"}
        for issue in report.issues:
            assert issue.severity in valid_severities

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_critique_for_each_genre(self, genre: str) -> None:
        """Each genre produces a valid critique report."""
        spec = _make_spec(genre)
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile(genre)
        critic = GenreCritic()

        report = critic.critique(score, profile)

        assert isinstance(report, CritiqueReport)
        assert report.genre == genre

    def test_critical_count(self) -> None:
        """critical_count property works correctly."""
        spec = _make_spec("rock_classic")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("rock_classic")
        critic = GenreCritic()

        report = critic.critique(score, profile)

        assert report.critical_count >= 0
        assert report.total_issues >= report.critical_count

    def test_never_praises(self) -> None:
        """The critic only reports problems, never positive feedback."""
        spec = _make_spec("j_pop_ballad")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("j_pop_ballad")
        critic = GenreCritic()

        report = critic.critique(score, profile)

        # All issues should be negative/corrective, never praise
        for issue in report.issues:
            assert issue.severity in ("critical", "major", "minor", "hint")
            assert issue.suggestion  # every issue has a fix suggestion
