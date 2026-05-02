"""Tests for SkillRegistry and GenreProfile loader."""

from __future__ import annotations

from yao.skills.loader import SkillRegistry


class TestSkillRegistry:
    """Tests for the genre skill loader."""

    def test_loads_all_genres(self) -> None:
        registry = SkillRegistry()
        assert registry.genre_count() >= 20

    def test_list_genres(self) -> None:
        registry = SkillRegistry()
        genres = registry.list_genres()
        assert "cinematic" in genres
        assert "lofi_hiphop" in genres

    def test_get_genre_cinematic(self) -> None:
        registry = SkillRegistry()
        profile = registry.get_genre("cinematic")
        assert profile is not None
        assert profile.genre_id == "cinematic"
        assert profile.tempo_range[0] < profile.tempo_range[1]
        assert len(profile.typical_keys) >= 1
        assert len(profile.preferred_instruments) >= 1

    def test_get_genre_not_found(self) -> None:
        registry = SkillRegistry()
        assert registry.get_genre("nonexistent_genre") is None

    def test_tempo_range_valid(self) -> None:
        registry = SkillRegistry()
        for genre_id in registry.list_genres():
            profile = registry.get_genre(genre_id)
            assert profile is not None
            lo, hi = profile.tempo_range
            assert 20 <= lo < hi <= 300, f"{genre_id}: tempo range ({lo}, {hi}) invalid"

    def test_lofi_has_swing(self) -> None:
        registry = SkillRegistry()
        profile = registry.get_genre("lofi_hiphop")
        assert profile is not None
        assert profile.default_swing > 0

    def test_jazz_swing_has_chord_progressions(self) -> None:
        registry = SkillRegistry()
        profile = registry.get_genre("jazz_swing")
        assert profile is not None
        assert len(profile.chord_progressions) >= 1
        # ii-V-I should be in there
        has_ii_v_i = any("ii7" in prog and "V7" in prog for prog in profile.chord_progressions)
        assert has_ii_v_i, "Jazz swing should have ii-V-I progression"

    def test_chord_palette_for(self) -> None:
        registry = SkillRegistry()
        palette = registry.chord_palette_for("jazz_swing")
        assert palette is not None
        assert "V7" in palette

    def test_chord_palette_for_missing_genre(self) -> None:
        registry = SkillRegistry()
        assert registry.chord_palette_for("nonexistent") is None

    def test_tempo_range_for(self) -> None:
        registry = SkillRegistry()
        r = registry.tempo_range_for("cinematic")
        assert r is not None
        assert r == (60.0, 160.0)

    def test_world_genre_has_cultural_context(self) -> None:
        registry = SkillRegistry()
        profile = registry.get_genre("arab_maqam")
        assert profile is not None
        assert profile.cultural_context is not None
        assert len(profile.cultural_context) > 10

    def test_reload(self) -> None:
        registry = SkillRegistry()
        count_before = registry.genre_count()
        registry.reload()
        assert registry.genre_count() == count_before

    def test_drum_pattern_family(self) -> None:
        registry = SkillRegistry()
        lofi = registry.get_genre("lofi_hiphop")
        assert lofi is not None
        assert lofi.drum_pattern_family is not None
        assert lofi.drum_pattern_family == "lofi_laidback"
