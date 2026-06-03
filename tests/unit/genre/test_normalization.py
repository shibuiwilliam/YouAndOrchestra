"""Tests for genre normalization module."""

from __future__ import annotations

import pytest

from yao.genre.normalization import (
    _GENRE_ALIASES,
    _JA_GENRE_ALIASES,
    normalize_genre,
    normalize_genre_with_fallback,
)


class TestNormalizeGenre:
    """Test normalize_genre resolves user inputs to registered profile IDs."""

    @pytest.mark.parametrize(
        "user_input,expected",
        [
            # Rock family
            ("rock", "rock_classic"),
            ("Rock", "rock_classic"),
            ("ROCK", "rock_classic"),
            ("hard rock", "rock_classic"),
            ("metal", "metal"),
            ("heavy metal", "metal"),
            ("prog", "progressive_rock"),
            ("prog rock", "progressive_rock"),
            # Hip-hop family
            ("hip hop", "hiphop_boom_bap"),
            ("hip-hop", "hiphop_boom_bap"),
            ("hiphop", "hiphop_boom_bap"),
            ("rap", "hiphop_boom_bap"),
            ("trap", "hiphop_trap"),
            ("lofi", "lofi_hiphop"),
            ("lo-fi", "lofi_hiphop"),
            ("lo fi", "lofi_hiphop"),
            # Electronic
            ("edm", "electronic_house"),
            ("house", "electronic_house"),
            ("techno", "electronic_techno"),
            ("trance", "electronic_trance"),
            ("synthwave", "electronic_synthwave"),
            # Pop
            ("pop", "pop_mainstream"),
            ("j-pop", "j_pop"),
            ("jpop", "j_pop"),
            # Jazz
            ("jazz", "jazz_ballad"),
            ("bebop", "jazz_bebop"),
            ("modal jazz", "jazz_modal"),
            # Classical
            ("classical", "classical_romantic"),
            ("baroque", "classical_baroque"),
            # Cinematic / Ambient
            ("cinematic", "cinematic"),
            ("ambient", "ambient"),
            ("dark ambient", "ambient_dark"),
            # Blues / Country / Folk
            ("blues", "blues_chicago"),
            ("country", "country_traditional"),
            ("folk", "acoustic_folk"),
            ("celtic", "world_celtic"),
            # Latin
            ("bossa nova", "latin_bossa_nova"),
            ("bossa", "latin_bossa_nova"),
            # R&B / Funk
            ("funk", "funk_classic"),
            ("rnb", "rnb_neo_soul"),
            ("soul", "rnb_neo_soul"),
            # Reggae
            ("reggae", "reggae"),
            # Game
            ("chiptune", "game_8bit_chiptune"),
            ("8bit", "game_8bit_chiptune"),
        ],
    )
    def test_resolves_known_genres(self, user_input: str, expected: str) -> None:
        """Known genre keywords resolve to correct profile IDs."""
        assert normalize_genre(user_input) == expected

    @pytest.mark.parametrize(
        "user_input",
        [
            # Direct registered IDs should also work
            "rock_classic",
            "hiphop_boom_bap",
            "electronic_house",
            "jazz_ballad",
            "pop_mainstream",
        ],
    )
    def test_direct_registered_ids(self, user_input: str) -> None:
        """Registered IDs resolve to themselves."""
        assert normalize_genre(user_input) == user_input

    def test_case_insensitive(self) -> None:
        """Case variations all resolve correctly."""
        assert normalize_genre("JAZZ") == "jazz_ballad"
        assert normalize_genre("Jazz") == "jazz_ballad"
        assert normalize_genre("jAzZ") == "jazz_ballad"

    def test_underscore_space_interchangeable(self) -> None:
        """Underscores and spaces are interchangeable."""
        assert normalize_genre("hip hop") == "hiphop_boom_bap"
        assert normalize_genre("hip_hop") == normalize_genre("hip hop")

    def test_unknown_genre_returns_none(self) -> None:
        """Unknown genres return None."""
        assert normalize_genre("polka") is None
        assert normalize_genre("yodel") is None
        assert normalize_genre("") is None

    def test_empty_input(self) -> None:
        """Empty string returns None."""
        assert normalize_genre("") is None

    def test_whitespace_handling(self) -> None:
        """Leading/trailing whitespace is stripped."""
        assert normalize_genre("  rock  ") == "rock_classic"
        assert normalize_genre("\tpop\n") == "pop_mainstream"


class TestNormalizeGenreWithFallback:
    """Test normalize_genre_with_fallback."""

    def test_known_genre_returns_resolved(self) -> None:
        """Known genres return the resolved ID."""
        assert normalize_genre_with_fallback("rock") == "rock_classic"

    def test_unknown_genre_returns_fallback(self) -> None:
        """Unknown genres return the fallback."""
        assert normalize_genre_with_fallback("polka") == "pop_mainstream"

    def test_custom_fallback(self) -> None:
        """Custom fallback is used when specified."""
        assert normalize_genre_with_fallback("polka", fallback="ambient") == "ambient"

    def test_empty_input_returns_fallback(self) -> None:
        """Empty input returns fallback."""
        assert normalize_genre_with_fallback("") == "pop_mainstream"


class TestJapaneseGenres:
    """Test Japanese genre keywords."""

    @pytest.mark.parametrize(
        "user_input,expected",
        [
            ("ロック", "rock_classic"),
            ("ジャズ", "jazz_ballad"),
            ("アンビエント", "ambient"),
            ("ポップ", "pop_mainstream"),
            ("ヒップホップ", "hiphop_boom_bap"),
            ("ファンク", "funk_classic"),
            ("ボサノバ", "latin_bossa_nova"),
        ],
    )
    def test_japanese_genre_keywords(self, user_input: str, expected: str) -> None:
        """Japanese genre keywords resolve correctly."""
        assert normalize_genre(user_input) == expected


class TestAliasCompleteness:
    """Verify the alias map covers expected genres."""

    def test_all_aliases_point_to_registered_profiles(self) -> None:
        """Every alias value is a registered profile ID."""
        from yao.constants.genre_profile import all_genre_profiles

        registered = set(all_genre_profiles().keys())
        for alias, profile_id in _GENRE_ALIASES.items():
            assert profile_id in registered, (
                f"Alias '{alias}' -> '{profile_id}' but '{profile_id}' is not registered. "
                f"Registered: {sorted(registered)}"
            )

    def test_all_ja_aliases_point_to_registered_profiles(self) -> None:
        """Every Japanese alias value is a registered profile ID."""
        from yao.constants.genre_profile import all_genre_profiles

        registered = set(all_genre_profiles().keys())
        for alias, profile_id in _JA_GENRE_ALIASES.items():
            assert profile_id in registered, f"JA alias '{alias}' -> '{profile_id}' not registered"
