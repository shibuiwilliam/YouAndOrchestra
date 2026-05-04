"""Scenario test: Surprise distribution varies meaningfully across genres.

Tests that different harmonic contexts produce observably different
surprise distributions — validating that the surprise scorer is
sensitive to tonal context, not just note patterns.
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.surprise import SurpriseScorer


def _make_score(pitches: list[int], key: str = "C major") -> ScoreIR:
    notes = tuple(
        Note(pitch=p, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano")
        for i, p in enumerate(pitches)
    )
    part = Part(instrument="piano", notes=notes)
    section = Section(name="test", start_bar=0, end_bar=len(pitches) // 4 + 1, parts=(part,))
    return ScoreIR(title="test", sections=(section,), tempo_bpm=120.0, time_signature="4/4", key=key)


class TestSurpriseDistributionScenarios:
    """Scenario tests for surprise distribution."""

    def test_key_context_matters(self) -> None:
        """Same notes in different keys should have different surprise."""
        # C major scale notes
        pitches = [60, 62, 64, 65, 67, 69, 71, 72] * 3

        scorer_c = SurpriseScorer(key="C major")
        scorer_fsharp = SurpriseScorer(key="F# major")

        score = _make_score(pitches)
        analysis_c = scorer_c.analyze(score)
        analysis_fs = scorer_fsharp.analyze(score)

        # In C major, these notes are diatonic — low surprise
        # In F# major, these same notes are mostly chromatic — higher surprise
        assert analysis_fs.overall_predictability > analysis_c.overall_predictability

    def test_repetition_reduces_surprise(self) -> None:
        """Repeated patterns should produce lower surprise over time."""
        pattern = [60, 64, 67, 72]
        pitches = pattern * 8  # 8 repetitions

        scorer = SurpriseScorer(key="C major")
        score = _make_score(pitches)
        analysis = scorer.analyze(score)

        # First few notes should have higher surprise than later ones
        # (the n-gram model learns the pattern)
        first_quarter = analysis.per_note[: len(pattern)]
        last_quarter = analysis.per_note[-len(pattern) :]

        avg_first = sum(n.combined_surprise for n in first_quarter) / len(first_quarter)
        avg_last = sum(n.combined_surprise for n in last_quarter) / len(last_quarter)

        # Later notes should be less surprising (n-gram has learned)
        assert avg_last <= avg_first

    def test_variance_differs_between_monotone_and_varied(self) -> None:
        """Monotone pieces have low variance; varied pieces have more."""
        monotone = [60] * 24  # All same note
        varied = [60, 63, 67, 61, 68, 62, 66, 64] * 3  # Varied

        scorer = SurpriseScorer(key="C major")
        analysis_m = scorer.analyze(_make_score(monotone))
        analysis_v = scorer.analyze(_make_score(varied))

        assert analysis_v.surprise_variance > analysis_m.surprise_variance
