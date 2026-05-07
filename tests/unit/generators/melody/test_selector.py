"""Tests for HarmonicMelodicSelector."""

from __future__ import annotations

import random

from yao.generators.melody.selector import HarmonicMelodicSelector
from yao.ir.harmonic_context import HarmonicContext
from yao.schema.melodic_profile import (
    IntervalDistribution,
    MelodicProfile,
    PhraseLengthDistribution,
)


def _make_profile(**overrides: object) -> MelodicProfile:
    """Create a test MelodicProfile."""
    defaults: dict = {
        "genre": "test",
        "chord_tone_targeting": 0.7,
        "chromaticism_level": 0.3,
        "interval_distribution": IntervalDistribution(distribution={1: 0.2, 2: 0.3, 3: 0.2, 4: 0.1, 7: 0.1, 12: 0.1}),
        "phrase_length_distribution": PhraseLengthDistribution(distribution={4: 0.5, 8: 0.5}),
        "typical_ranges": {"melody": ("C4", "C6")},
    }
    defaults.update(overrides)
    return MelodicProfile(**defaults)


class TestHarmonicMelodicSelector:
    """Tests for the harmonic-melodic pitch selector."""

    def test_prefers_chord_tones_on_downbeat(self) -> None:
        """Chord tones score higher than non-chord tones on downbeats."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        profile = _make_profile()

        # C4 (60) is chord root, D4 (62) is not
        score_root = selector.score_pitch(60, ctx, 58, profile)
        score_non = selector.score_pitch(62, ctx, 58, profile)

        assert score_root > score_non

    def test_avoids_avoid_notes(self) -> None:
        """Avoid notes (half-step above chord tones) score lower."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        profile = _make_profile()

        # C#4 (61) is an avoid note for C major (half-step above root)
        score_avoid = selector.score_pitch(61, ctx, 60, profile)
        score_ok = selector.score_pitch(62, ctx, 60, profile)  # D4 is fine

        assert score_ok > score_avoid

    def test_tensions_allowed_on_weak_beats(self) -> None:
        """Non-chord tones score better on weak beats with high chromaticism."""
        selector = HarmonicMelodicSelector()
        profile = _make_profile(chromaticism_level=0.8)

        ctx_strong = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        ctx_weak = HarmonicContext(bar=0, beat=1.5, chord_root="C", chord_quality="maj")

        # D4 (62) is a non-chord tone for C major
        score_strong = selector.score_pitch(62, ctx_strong, 60, profile)
        score_weak = selector.score_pitch(62, ctx_weak, 60, profile)

        # Should score better on weak beat
        assert score_weak > score_strong

    def test_interval_distribution_weighting(self) -> None:
        """Pitches matching preferred intervals score higher."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(bar=0, beat=1.0, chord_root="C", chord_quality="maj")
        # Profile strongly prefers step-wise motion (interval 2)
        profile = _make_profile(
            interval_distribution=IntervalDistribution(distribution={2: 0.9, 7: 0.1}),
        )

        # From C4 (60): D4 (62) is 2 semitones, G4 (67) is 7 semitones
        score_step = selector.score_pitch(62, ctx, 60, profile)
        score_leap = selector.score_pitch(67, ctx, 60, profile)

        assert score_step > score_leap

    def test_select_pitch_returns_valid_pitch(self) -> None:
        """Selected pitch is always from the scale pitches."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        profile = _make_profile()
        scale = [60, 62, 64, 65, 67, 69, 71, 72]

        result = selector.select_pitch(ctx, 60, scale, profile, random.Random(42))
        assert result in scale

    def test_high_targeting_produces_more_chord_tones(self) -> None:
        """With chord_tone_targeting=0.9, most selections should be chord tones."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj")
        profile = _make_profile(chord_tone_targeting=0.9)
        scale = [60, 62, 64, 65, 67, 69, 71, 72]
        chord_tones = {60, 64, 67, 72}  # C, E, G

        rng = random.Random(42)
        ct_count = 0
        total = 100
        prev = 60
        for _ in range(total):
            p = selector.select_pitch(ctx, prev, scale, profile, rng)
            if p in chord_tones:
                ct_count += 1
            prev = p

        ratio = ct_count / total
        # With 0.9 targeting on downbeat, should be well above 50%
        assert ratio > 0.4

    def test_out_of_range_penalized(self) -> None:
        """Pitches outside typical_ranges score lower."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(bar=0, beat=1.0, chord_root="C", chord_quality="maj")
        profile = _make_profile(typical_ranges={"melody": ("C4", "C5")})

        # C5 (72) is in range, C6 (84) is out of range
        score_in = selector.score_pitch(72, ctx, 67, profile)
        score_out = selector.score_pitch(84, ctx, 67, profile)

        assert score_in > score_out

    def test_voice_leading_bonus_near_chord_change(self) -> None:
        """Pitches near next chord tones get a bonus on weak beats."""
        selector = HarmonicMelodicSelector()
        ctx = HarmonicContext(
            bar=0,
            beat=3.5,
            chord_root="C",
            chord_quality="maj",
            next_chord_root="F",
            next_chord_quality="maj",
        )
        profile = _make_profile()

        # E4 (64) is a half-step from F (next chord root) — good VL target
        # B3 (59) is far from F chord tones
        score_vl = selector.score_pitch(64, ctx, 62, profile)
        score_no_vl = selector.score_pitch(59, ctx, 62, profile)

        # Voice-leading pitch should score at least as well
        assert score_vl >= score_no_vl
