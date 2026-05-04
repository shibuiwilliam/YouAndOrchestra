"""Tests for SurpriseScorer and SurpriseAnalysis (Layer 4).

Tests cover:
- Known predictable sequences (diatonic scale) have low surprise
- Known chromatic sequences have higher surprise
- SurpriseAnalysis serialization round-trip
- Edge cases (empty score, single note)
- Krumhansl profile correctness
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.surprise import (
    KRUMHANSL_MAJOR,
    KRUMHANSL_MINOR,
    NoteSurprise,
    SurpriseAnalysis,
    SurpriseScorer,
    _parse_key,
)


def _make_score(pitches: list[int], instrument: str = "piano") -> ScoreIR:
    """Create a minimal ScoreIR from a pitch sequence."""
    notes = tuple(
        Note(
            pitch=p,
            start_beat=float(i),
            duration_beats=1.0,
            velocity=80,
            instrument=instrument,
        )
        for i, p in enumerate(pitches)
    )
    part = Part(instrument=instrument, notes=notes)
    section = Section(name="test", start_bar=0, end_bar=len(pitches) // 4 + 1, parts=(part,))
    return ScoreIR(
        title="test",
        sections=(section,),
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
    )


class TestKrumhansProfile:
    """Verify Krumhansl profiles are plausible."""

    def test_major_tonic_most_stable(self) -> None:
        assert KRUMHANSL_MAJOR[0] == max(KRUMHANSL_MAJOR)

    def test_minor_tonic_most_stable(self) -> None:
        assert KRUMHANSL_MINOR[0] == max(KRUMHANSL_MINOR)

    def test_major_dominant_high(self) -> None:
        # G (perfect fifth = index 7) should be 2nd or 3rd highest
        sorted_major = sorted(range(12), key=lambda i: KRUMHANSL_MAJOR[i], reverse=True)
        assert 7 in sorted_major[:3]

    def test_profile_length(self) -> None:
        assert len(KRUMHANSL_MAJOR) == 12
        assert len(KRUMHANSL_MINOR) == 12


class TestParseKey:
    """Tests for key parsing."""

    def test_c_major(self) -> None:
        root_pc, profile = _parse_key("C major")
        assert root_pc == 0
        assert len(profile) == 12

    def test_d_minor(self) -> None:
        root_pc, profile = _parse_key("D minor")
        assert root_pc == 2

    def test_fsharp_major(self) -> None:
        root_pc, _ = _parse_key("F# major")
        assert root_pc == 6

    def test_profile_sums_to_one(self) -> None:
        _, profile = _parse_key("G major")
        assert abs(sum(profile) - 1.0) < 1e-6


class TestSurpriseScorer:
    """Tests for SurpriseScorer."""

    def test_diatonic_scale_low_surprise(self) -> None:
        """C major scale repeated should have relatively low surprise."""
        pitches = [60, 62, 64, 65, 67, 69, 71, 72] * 3  # C-D-E-F-G-A-B-C x3
        score = _make_score(pitches)
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        # Diatonic scale in its own key should be fairly predictable
        assert analysis.overall_predictability < 0.5

    def test_chromatic_sequence_higher_surprise(self) -> None:
        """Chromatic sequence should have higher surprise than diatonic."""
        diatonic = [60, 62, 64, 65, 67, 69, 71, 72] * 3
        chromatic = [60, 61, 62, 63, 64, 65, 66, 67] * 3

        score_d = _make_score(diatonic)
        score_c = _make_score(chromatic)

        scorer = SurpriseScorer(key="C major")
        analysis_d = scorer.analyze(score_d)
        analysis_c = scorer.analyze(score_c)

        # Chromatic should be more surprising in C major context
        assert analysis_c.overall_predictability > analysis_d.overall_predictability

    def test_repeated_note_very_low_surprise(self) -> None:
        """A single repeated note should have very low surprise."""
        pitches = [60] * 20  # C repeated
        score = _make_score(pitches)
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        assert analysis.overall_predictability < 0.2

    def test_empty_score(self) -> None:
        """Empty score produces empty analysis."""
        score = ScoreIR(
            title="test",
            sections=(),
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
        )
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        assert len(analysis.per_note) == 0
        assert analysis.overall_predictability == 0.0

    def test_single_note(self) -> None:
        """Single note has moderate surprise (not enough context)."""
        score = _make_score([60])
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        assert len(analysis.per_note) == 1

    def test_moving_average_length(self) -> None:
        """Moving average has same length as per_note."""
        pitches = [60, 64, 67, 72, 60, 64, 67, 72] * 2
        score = _make_score(pitches)
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        assert len(analysis.moving_average) == len(analysis.per_note)

    def test_peak_locations_are_subset(self) -> None:
        """Peak locations must be beats that exist in per_note."""
        pitches = [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71]
        score = _make_score(pitches)
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        note_beats = {ns.start_beat for ns in analysis.per_note}
        for peak_beat in analysis.peak_locations:
            assert peak_beat in note_beats

    def test_variance_non_negative(self) -> None:
        """Variance must be >= 0."""
        pitches = [60, 62, 64, 67, 60, 62, 64, 67]
        score = _make_score(pitches)
        scorer = SurpriseScorer(key="C major")
        analysis = scorer.analyze(score)

        assert analysis.surprise_variance >= 0.0


class TestSurpriseAnalysisSerialization:
    """Tests for SurpriseAnalysis serialization."""

    def test_to_dict(self) -> None:
        analysis = SurpriseAnalysis(
            per_note=(
                NoteSurprise(
                    pitch=60,
                    start_beat=0.0,
                    instrument="piano",
                    ngram_surprise=0.3,
                    tonal_surprise=0.1,
                    combined_surprise=0.18,
                ),
            ),
            moving_average=(0.18,),
            peak_locations=(0.0,),
            overall_predictability=0.18,
            surprise_variance=0.0,
        )
        data = analysis.to_dict()
        assert "overall_predictability" in data
        assert "surprise_variance" in data
        assert "peak_locations" in data

    def test_round_trip_summary(self) -> None:
        analysis = SurpriseAnalysis(
            per_note=(),
            moving_average=(),
            peak_locations=(4.0, 12.0),
            overall_predictability=0.35,
            surprise_variance=0.02,
        )
        data = analysis.to_dict()
        restored = SurpriseAnalysis.from_dict(data)
        assert abs(restored.overall_predictability - 0.35) < 1e-4
        assert abs(restored.surprise_variance - 0.02) < 1e-4
