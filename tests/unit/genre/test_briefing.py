"""Tests for GenreBriefing synthesis."""

from __future__ import annotations

import pytest

from yao.genre.briefing import FusionComponent, GenreBriefing, synthesize_briefing
from yao.genre.profile import GenreProfile, InstrumentRoleSpec
from yao.genre.registry import GenreNotFoundError, GenreRegistry


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    """Reset the registry before each test."""
    GenreRegistry._cache.clear()
    GenreRegistry._loaded = False


class TestGenreBriefingCreation:
    """Test GenreBriefing construction."""

    def test_single_genre_briefing(self) -> None:
        """Briefing for a single genre should resolve correctly."""
        profile = GenreProfile(
            name="jazz",
            typical_tempo_range=(60.0, 240.0),
            swing_8th=0.67,
            chord_palette_extended=["maj7", "min7"],
            core_instruments=[InstrumentRoleSpec(name="upright_bass")],
            forbidden_instruments=["distorted_electric_guitar"],
            cliches_to_avoid=["generic swing"],
        )
        briefing = GenreBriefing(
            id="test_001",
            primary_genre="jazz",
            primary_profile=profile,
        )
        assert briefing.primary_genre == "jazz"
        assert briefing.tempo_range == (60.0, 240.0)
        assert briefing.swing_8th == 0.67
        assert "maj7" in briefing.chord_palette
        assert "upright_bass" in briefing.core_instruments
        assert "distorted_electric_guitar" in briefing.forbidden_instruments
        assert "generic swing" in briefing.cliches_to_avoid

    def test_briefing_has_unique_id(self) -> None:
        """Each briefing should have a unique ID for provenance."""
        profile = GenreProfile(name="test")
        b1 = GenreBriefing(id="b1", primary_genre="test", primary_profile=profile)
        b2 = GenreBriefing(id="b2", primary_genre="test", primary_profile=profile)
        assert b1.id != b2.id


class TestGenreBriefingFusion:
    """Test genre fusion blending."""

    def test_fusion_interpolates_numeric_fields(self) -> None:
        """Fusion should linearly interpolate numeric fields."""
        primary = GenreProfile(name="jazz", swing_8th=0.67, syncopation_density=0.4)
        secondary = GenreProfile(name="rock", swing_8th=0.5, syncopation_density=0.2)

        briefing = GenreBriefing(
            id="fusion_001",
            primary_genre="jazz",
            primary_profile=primary,
            fusion_components=(FusionComponent(genre="rock", weight=0.3, profile=secondary),),
        )
        # Primary weight = 0.7, secondary weight = 0.3
        expected_swing = 0.67 * 0.7 + 0.5 * 0.3
        assert abs(briefing.swing_8th - expected_swing) < 0.01

    def test_fusion_merges_list_fields(self) -> None:
        """Fusion should merge list fields with deduplication."""
        primary = GenreProfile(
            name="jazz",
            typical_scales=["dorian", "mixolydian"],
        )
        secondary = GenreProfile(
            name="blues",
            typical_scales=["blues", "dorian"],  # dorian is shared
        )

        briefing = GenreBriefing(
            id="fusion_002",
            primary_genre="jazz",
            primary_profile=primary,
            fusion_components=(FusionComponent(genre="blues", weight=0.3, profile=secondary),),
        )
        resolved_scales = list(briefing.resolved_profile.typical_scales)
        assert "dorian" in resolved_scales
        assert "mixolydian" in resolved_scales
        assert "blues" in resolved_scales
        # dorian should appear only once
        assert resolved_scales.count("dorian") == 1


class TestGenreBriefingOverrides:
    """Test user override application."""

    def test_user_overrides_applied(self) -> None:
        """User overrides should take precedence over profile values."""
        profile = GenreProfile(name="jazz", target_lufs=-16.0)
        briefing = GenreBriefing(
            id="override_001",
            primary_genre="jazz",
            primary_profile=profile,
            user_overrides={"target_lufs": -18.0},
        )
        assert briefing.resolved_profile.target_lufs == -18.0


class TestSynthesizeBriefing:
    """Test the synthesize_briefing convenience function."""

    def test_synthesize_single_genre(self) -> None:
        """synthesize_briefing should produce a valid briefing for a known genre."""
        briefing = synthesize_briefing("jazz")
        assert briefing.primary_genre == "jazz"
        assert briefing.id.startswith("briefing_")
        assert briefing.swing_8th >= 0.6

    def test_synthesize_unknown_genre_raises(self) -> None:
        """synthesize_briefing should raise for an unknown genre."""
        with pytest.raises(GenreNotFoundError):
            synthesize_briefing("nonexistent_xyz")

    def test_synthesize_with_fusion(self) -> None:
        """synthesize_briefing with fusion should blend genres."""
        briefing = synthesize_briefing(
            "jazz",
            fusion=[("rock", 0.3)],
        )
        assert briefing.primary_genre == "jazz"
        assert len(briefing.fusion_components) == 1
        # Swing should be between jazz (0.67) and rock (0.5)
        assert 0.5 <= briefing.swing_8th <= 0.67

    def test_synthesize_with_overrides(self) -> None:
        """synthesize_briefing with overrides should apply them."""
        briefing = synthesize_briefing(
            "pop",
            overrides={"target_lufs": -12.0},
        )
        assert briefing.resolved_profile.target_lufs == -12.0
