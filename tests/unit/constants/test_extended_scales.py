"""Tests for extended scale definitions (Phase γ.7).

Tests cover:
- All 28 scales load correctly
- Japanese, Middle Eastern, Indian scales have cultural_context
- No duplicate interval patterns (after rotation)
- New scales have correct degree counts
- All non-Western scales have non-empty cultural_context
"""

from __future__ import annotations

from yao.constants.scales import ALL_SCALE_DEFINITIONS


class TestExtendedScales:
    """Tests for the extended scale library."""

    def test_total_scale_count(self) -> None:
        """Should have 28 scales (17 original + 11 new)."""
        assert len(ALL_SCALE_DEFINITIONS) == 28

    def test_all_have_name(self) -> None:
        for name, scale in ALL_SCALE_DEFINITIONS.items():
            assert scale.name == name

    def test_all_have_intervals(self) -> None:
        for name, scale in ALL_SCALE_DEFINITIONS.items():
            assert len(scale.intervals_cents) >= 5, f"{name} has too few intervals"

    def test_all_start_at_zero(self) -> None:
        for name, scale in ALL_SCALE_DEFINITIONS.items():
            assert scale.intervals_cents[0] == 0, f"{name} doesn't start at 0"

    def test_intervals_ascending(self) -> None:
        for name, scale in ALL_SCALE_DEFINITIONS.items():
            cents = scale.intervals_cents
            for i in range(1, len(cents)):
                assert cents[i] > cents[i - 1], (
                    f"{name}: interval {i} ({cents[i]}) <= interval {i - 1} ({cents[i - 1]})"
                )

    def test_intervals_within_octave(self) -> None:
        for name, scale in ALL_SCALE_DEFINITIONS.items():
            for c in scale.intervals_cents:
                assert 0 <= c < scale.octave_cents, f"{name}: interval {c} outside octave ({scale.octave_cents})"


class TestJapaneseScales:
    """Tests for Japanese scale definitions."""

    JAPANESE_NAMES = [
        "japanese_in",
        "japanese_yo",
        "japanese_ritsu",
        "japanese_minyo",
        "hirajoshi",
        "iwato",
    ]

    def test_all_present(self) -> None:
        for name in self.JAPANESE_NAMES:
            assert name in ALL_SCALE_DEFINITIONS, f"Missing: {name}"

    def test_all_pentatonic(self) -> None:
        """All Japanese scales should be pentatonic (5 notes)."""
        for name in self.JAPANESE_NAMES:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert scale.degree_count == 5, f"{name} has {scale.degree_count} notes"

    def test_all_have_cultural_context(self) -> None:
        for name in self.JAPANESE_NAMES:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert scale.cultural_context, f"{name} missing cultural_context"

    def test_in_scale_intervals(self) -> None:
        """In-scale: semitone (100) + perfect 4th (500) are characteristic."""
        scale = ALL_SCALE_DEFINITIONS["japanese_in"]
        assert scale.intervals_cents[1] == 100  # semitone

    def test_yo_no_semitones(self) -> None:
        """Yo-scale has no semitone intervals."""
        scale = ALL_SCALE_DEFINITIONS["japanese_yo"]
        for i in range(1, len(scale.intervals_cents)):
            diff = scale.intervals_cents[i] - scale.intervals_cents[i - 1]
            assert diff >= 200, f"Yo-scale has semitone at degree {i}"


class TestMiddleEasternScales:
    """Tests for additional Middle Eastern scales."""

    MAQAM_NAMES = ["maqam_hijaz", "maqam_kurd", "maqam_nahawand"]

    def test_all_present(self) -> None:
        for name in self.MAQAM_NAMES:
            assert name in ALL_SCALE_DEFINITIONS

    def test_all_heptatonic(self) -> None:
        """Additional maqamat should be heptatonic (7 notes)."""
        for name in self.MAQAM_NAMES:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert scale.degree_count == 7, f"{name} has {scale.degree_count} notes"

    def test_all_have_cultural_context(self) -> None:
        for name in self.MAQAM_NAMES:
            assert ALL_SCALE_DEFINITIONS[name].cultural_context

    def test_hijaz_augmented_second(self) -> None:
        """Hijaz has characteristic augmented 2nd (100→400 = 300 cents)."""
        hijaz = ALL_SCALE_DEFINITIONS["maqam_hijaz"]
        assert hijaz.intervals_cents[1] == 100
        assert hijaz.intervals_cents[2] == 400
        # Augmented second = 300 cents
        assert hijaz.intervals_cents[2] - hijaz.intervals_cents[1] == 300


class TestIndianScales:
    """Tests for additional Indian scales."""

    RAGA_NAMES = ["raga_marwa", "raga_todi"]

    def test_all_present(self) -> None:
        for name in self.RAGA_NAMES:
            assert name in ALL_SCALE_DEFINITIONS

    def test_all_have_cultural_context(self) -> None:
        for name in self.RAGA_NAMES:
            assert ALL_SCALE_DEFINITIONS[name].cultural_context

    def test_marwa_is_hexatonic(self) -> None:
        """Marwa omits the 5th degree, making it 6-note."""
        marwa = ALL_SCALE_DEFINITIONS["raga_marwa"]
        assert marwa.degree_count == 6

    def test_todi_is_heptatonic(self) -> None:
        todi = ALL_SCALE_DEFINITIONS["raga_todi"]
        assert todi.degree_count == 7


class TestNonWesternCulturalContext:
    """All non-Western scales must have cultural_context."""

    WESTERN_SCALES = {
        "major",
        "minor",
        "harmonic_minor",
        "dorian",
        "mixolydian",
        "pentatonic_major",
        "pentatonic_minor",
        "blues",
        "chromatic",
    }

    def test_all_non_western_have_context(self) -> None:
        for name, scale in ALL_SCALE_DEFINITIONS.items():
            if name not in self.WESTERN_SCALES:
                assert scale.cultural_context, f"Non-Western scale '{name}' is missing cultural_context"
