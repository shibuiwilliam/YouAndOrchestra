"""Tests for MelodicProfile schema and supporting types.

Covers: validation, malformed input rejection, blending, and normalization.
"""

from __future__ import annotations

import pytest

from yao.errors import SpecValidationError
from yao.schema.melodic_profile import (
    AntiPattern,
    CadencePattern,
    IntervalDistribution,
    MelodicProfile,
    OrnamentProfile,
    PhraseLengthDistribution,
    RhythmTemplate,
    blend_profiles,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _minimal_profile(**overrides: object) -> MelodicProfile:
    """Create a minimal valid MelodicProfile for testing."""
    defaults: dict = {
        "genre": "test_genre",
        "interval_distribution": IntervalDistribution(distribution={2: 0.5, 3: 0.5}),
        "phrase_length_distribution": PhraseLengthDistribution(distribution={4: 0.6, 8: 0.4}),
    }
    defaults.update(overrides)
    return MelodicProfile(**defaults)


# ---------------------------------------------------------------------------
# IntervalDistribution
# ---------------------------------------------------------------------------


class TestIntervalDistribution:
    """Tests for IntervalDistribution validation and normalization."""

    def test_valid_distribution(self) -> None:
        """Valid distribution is accepted."""
        dist = IntervalDistribution(distribution={0: 0.1, 2: 0.5, 4: 0.4})
        assert dist.distribution[2] == 0.5

    def test_empty_distribution_rejected(self) -> None:
        """Empty distribution raises SpecValidationError."""
        with pytest.raises(SpecValidationError, match="at least one entry"):
            IntervalDistribution(distribution={})

    def test_negative_probability_rejected(self) -> None:
        """Negative probability raises SpecValidationError."""
        with pytest.raises(SpecValidationError, match="non-negative"):
            IntervalDistribution(distribution={2: -0.1})

    def test_normalized(self) -> None:
        """Normalization produces probabilities summing to 1.0."""
        dist = IntervalDistribution(distribution={1: 3.0, 2: 7.0})
        normed = dist.normalized()
        assert abs(sum(normed.values()) - 1.0) < 1e-9
        assert abs(normed[1] - 0.3) < 1e-9
        assert abs(normed[2] - 0.7) < 1e-9


# ---------------------------------------------------------------------------
# PhraseLengthDistribution
# ---------------------------------------------------------------------------


class TestPhraseLengthDistribution:
    """Tests for PhraseLengthDistribution validation."""

    def test_valid(self) -> None:
        """Valid distribution accepted."""
        dist = PhraseLengthDistribution(distribution={4: 0.5, 8: 0.5})
        assert dist.distribution[4] == 0.5

    def test_empty_rejected(self) -> None:
        """Empty distribution rejected."""
        with pytest.raises(SpecValidationError, match="at least one entry"):
            PhraseLengthDistribution(distribution={})

    def test_zero_length_rejected(self) -> None:
        """Zero or negative phrase length rejected."""
        with pytest.raises(SpecValidationError, match="positive"):
            PhraseLengthDistribution(distribution={0: 1.0})

    def test_negative_probability_rejected(self) -> None:
        """Negative probability rejected."""
        with pytest.raises(SpecValidationError, match="non-negative"):
            PhraseLengthDistribution(distribution={4: -0.1})

    def test_normalized(self) -> None:
        """Normalization works correctly."""
        dist = PhraseLengthDistribution(distribution={4: 2.0, 8: 8.0})
        normed = dist.normalized()
        assert abs(normed[4] - 0.2) < 1e-9


# ---------------------------------------------------------------------------
# RhythmTemplate
# ---------------------------------------------------------------------------


class TestRhythmTemplate:
    """Tests for RhythmTemplate validation."""

    def test_valid(self) -> None:
        """Valid template accepted."""
        rt = RhythmTemplate(name="swing_8ths", swing_ratio=0.67)
        assert rt.swing_ratio == 0.67

    def test_straight_swing(self) -> None:
        """Straight swing (0.5) is valid."""
        rt = RhythmTemplate(name="straight", swing_ratio=0.5)
        assert rt.swing_ratio == 0.5

    def test_invalid_swing_ratio(self) -> None:
        """Swing ratio outside [0.5, 0.75] rejected."""
        with pytest.raises(SpecValidationError, match="swing_ratio"):
            RhythmTemplate(name="bad", swing_ratio=0.4)
        with pytest.raises(SpecValidationError, match="swing_ratio"):
            RhythmTemplate(name="bad", swing_ratio=0.8)


# ---------------------------------------------------------------------------
# OrnamentProfile
# ---------------------------------------------------------------------------


class TestOrnamentProfile:
    """Tests for OrnamentProfile validation."""

    def test_defaults(self) -> None:
        """Default profile is valid."""
        op = OrnamentProfile()
        assert op.grace_note_probability == 0.0
        assert op.legato_ratio == 0.5

    def test_invalid_probability(self) -> None:
        """Probability > 1.0 rejected."""
        with pytest.raises(SpecValidationError, match="0.0, 1.0"):
            OrnamentProfile(grace_note_probability=1.5)

    def test_negative_probability(self) -> None:
        """Negative probability rejected."""
        with pytest.raises(SpecValidationError, match="0.0, 1.0"):
            OrnamentProfile(trill_probability=-0.1)


# ---------------------------------------------------------------------------
# AntiPattern
# ---------------------------------------------------------------------------


class TestAntiPattern:
    """Tests for AntiPattern validation."""

    def test_valid(self) -> None:
        """Valid anti-pattern accepted."""
        ap = AntiPattern(name="straight_8ths", description="No swing", severity="critical")
        assert ap.severity == "critical"

    def test_invalid_severity(self) -> None:
        """Unknown severity rejected."""
        with pytest.raises(SpecValidationError, match="severity"):
            AntiPattern(name="x", description="y", severity="blocker")


# ---------------------------------------------------------------------------
# CadencePattern
# ---------------------------------------------------------------------------


class TestCadencePattern:
    """Tests for CadencePattern."""

    def test_valid(self) -> None:
        """Valid cadence pattern accepted."""
        cp = CadencePattern(name="ii-V-I", chord_sequence=["ii7", "V7", "Imaj7"])
        assert cp.melodic_target == "1"


# ---------------------------------------------------------------------------
# MelodicProfile
# ---------------------------------------------------------------------------


class TestMelodicProfile:
    """Tests for the MelodicProfile model."""

    def test_minimal_valid(self) -> None:
        """Minimal profile with required fields is accepted."""
        profile = _minimal_profile()
        assert profile.genre == "test_genre"
        assert profile.chord_tone_targeting == 0.5

    def test_full_profile(self) -> None:
        """Full profile with all fields is accepted."""
        profile = _minimal_profile(
            description="Test genre description",
            scale_preferences={"major": 0.5, "dorian": 0.5},
            chord_tone_targeting=0.75,
            chromaticism_level=0.3,
            syncopation_level=0.4,
            cadence_patterns=[CadencePattern(name="PAC", chord_sequence=["V", "I"])],
            rhythm_templates=[RhythmTemplate(name="straight")],
            ornament_profile=OrnamentProfile(grace_note_probability=0.1),
            typical_ranges={"melody": ("C4", "C6")},
            motif_length_bars=2.0,
            motif_recurrence_rate=0.6,
            motif_transformations={"identity": 0.3, "transposed": 0.7},
            groove_profile_name="jazz_swing",
            anti_patterns=[AntiPattern(name="no_swing", description="Must use swing", severity="critical")],
        )
        assert profile.chord_tone_targeting == 0.75
        assert len(profile.anti_patterns) == 1

    def test_chord_tone_targeting_out_of_range(self) -> None:
        """chord_tone_targeting > 1.0 rejected."""
        with pytest.raises(SpecValidationError):
            _minimal_profile(chord_tone_targeting=1.5)

    def test_chromaticism_negative(self) -> None:
        """Negative chromaticism_level rejected."""
        with pytest.raises(SpecValidationError):
            _minimal_profile(chromaticism_level=-0.1)

    def test_motif_length_zero(self) -> None:
        """Zero motif_length_bars rejected."""
        with pytest.raises(SpecValidationError, match="positive"):
            _minimal_profile(motif_length_bars=0.0)

    def test_motif_recurrence_out_of_range(self) -> None:
        """motif_recurrence_rate > 1.0 rejected."""
        with pytest.raises(SpecValidationError):
            _minimal_profile(motif_recurrence_rate=1.1)

    def test_extra_fields_rejected(self) -> None:
        """Extra fields not in schema are rejected (extra=forbid)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _minimal_profile(unknown_field="value")  # type: ignore[call-overload]

    def test_typical_ranges_list_coercion(self) -> None:
        """Ranges specified as lists are coerced to tuples."""
        profile = _minimal_profile(typical_ranges={"melody": ["C4", "C6"]})
        assert profile.typical_ranges["melody"] == ("C4", "C6")


# ---------------------------------------------------------------------------
# blend_profiles
# ---------------------------------------------------------------------------


class TestBlendProfiles:
    """Tests for profile blending."""

    def test_blend_50_50(self) -> None:
        """50/50 blend produces averaged values."""
        p1 = _minimal_profile(
            genre="jazz",
            chord_tone_targeting=0.6,
            chromaticism_level=0.8,
            interval_distribution=IntervalDistribution(distribution={1: 1.0, 2: 0.0}),
            phrase_length_distribution=PhraseLengthDistribution(distribution={4: 1.0}),
        )
        p2 = _minimal_profile(
            genre="pop",
            chord_tone_targeting=0.4,
            chromaticism_level=0.2,
            interval_distribution=IntervalDistribution(distribution={1: 0.0, 2: 1.0}),
            phrase_length_distribution=PhraseLengthDistribution(distribution={8: 1.0}),
        )
        blended = blend_profiles(p1, p2, ratio=0.5)

        assert blended.genre == "jazz_x_pop"
        assert abs(blended.chord_tone_targeting - 0.5) < 1e-9
        assert abs(blended.chromaticism_level - 0.5) < 1e-9
        assert abs(blended.interval_distribution.distribution[1] - 0.5) < 1e-9
        assert abs(blended.interval_distribution.distribution[2] - 0.5) < 1e-9

    def test_blend_100_0(self) -> None:
        """100% primary produces the primary's values."""
        p1 = _minimal_profile(genre="jazz", chord_tone_targeting=0.9)
        p2 = _minimal_profile(genre="pop", chord_tone_targeting=0.1)
        blended = blend_profiles(p1, p2, ratio=1.0)
        assert abs(blended.chord_tone_targeting - 0.9) < 1e-9

    def test_blend_disjoint_intervals(self) -> None:
        """Blending profiles with disjoint interval sets includes all keys."""
        p1 = _minimal_profile(
            genre="a",
            interval_distribution=IntervalDistribution(distribution={1: 1.0}),
        )
        p2 = _minimal_profile(
            genre="b",
            interval_distribution=IntervalDistribution(distribution={7: 1.0}),
        )
        blended = blend_profiles(p1, p2, ratio=0.5)
        assert 1 in blended.interval_distribution.distribution
        assert 7 in blended.interval_distribution.distribution
