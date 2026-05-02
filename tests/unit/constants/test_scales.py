"""Tests for scale definitions — structure and cultural integrity."""

from __future__ import annotations

from yao.constants.scales import ALL_SCALE_DEFINITIONS


class TestScaleDefinitions:
    def test_all_12edo_scales_have_100_multiples(self) -> None:
        """12-EDO scales must have intervals that are multiples of 100 cents."""
        edo_scales = [
            "major",
            "minor",
            "harmonic_minor",
            "dorian",
            "mixolydian",
            "pentatonic_major",
            "pentatonic_minor",
            "blues",
            "chromatic",
        ]
        for name in edo_scales:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert scale.is_12edo, f"{name} should be 12-EDO"
            for c in scale.intervals_cents:
                assert c % 100 == 0, f"{name}: {c} cents is not a 12-EDO interval"

    def test_raga_scales_have_cultural_context(self) -> None:
        """Raga scales must have non-empty cultural_context."""
        raga_names = ["raga_yaman", "raga_bhairav", "raga_darbari"]
        for name in raga_names:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert scale.cultural_context, f"{name} missing cultural_context"
            assert "raga" in scale.cultural_context.lower() or "hindustani" in scale.cultural_context.lower()

    def test_maqam_scales_have_quarter_tones(self) -> None:
        """Maqam scales must contain intervals that are not multiples of 100."""
        maqam_names = ["maqam_rast", "maqam_bayati"]
        for name in maqam_names:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert not scale.is_12edo, f"{name} should NOT be 12-EDO"
            has_quarter = any(c % 100 != 0 for c in scale.intervals_cents)
            assert has_quarter, f"{name} should have quarter-tone intervals"

    def test_gamelan_scales_have_cultural_context(self) -> None:
        """Gamelan scales must have cultural context."""
        for name in ["pelog", "slendro"]:
            scale = ALL_SCALE_DEFINITIONS[name]
            assert scale.cultural_context, f"{name} missing cultural_context"
            assert "gamelan" in scale.cultural_context.lower()

    def test_just_intonation_is_non_equal(self) -> None:
        """Just intonation must have non-100-multiple intervals."""
        ji = ALL_SCALE_DEFINITIONS["just_intonation_major"]
        assert not ji.is_12edo

    def test_all_scales_have_unique_names(self) -> None:
        """No duplicate scale names."""
        names = [s.name for s in ALL_SCALE_DEFINITIONS.values()]
        assert len(names) == len(set(names))

    def test_minimum_scale_count(self) -> None:
        """Should have at least 17 scales (9 EDO + 3 raga + 2 maqam + 2 gamelan + 1 JI)."""
        assert len(ALL_SCALE_DEFINITIONS) >= 17  # noqa: PLR2004
