"""Tests for genre profile data structure and loading.

Verifies that all 8 genre profiles load successfully and have
all required fields populated with valid values.
"""

from __future__ import annotations

import pytest

from yao.constants.genre_profile import (
    BassStyle,
    GenreProfile,
    all_genre_profiles,
    genre_chord_sequence,
    get_genre_profile,
    reload_profiles,
    roman_to_degree,
)

EXPECTED_GENRES = [
    "cinematic",
    "lofi_hiphop",
    "j_pop",
    "neoclassical",
    "ambient",
    "jazz_ballad",
    "game_8bit_chiptune",
    "acoustic_folk",
]


@pytest.fixture(autouse=True)
def _fresh_profiles() -> None:
    """Reload profiles before each test to avoid stale state."""
    reload_profiles()


class TestGenreProfileLoading:
    """Tests for loading genre profiles from YAML."""

    def test_all_8_profiles_load(self) -> None:
        """All 8 expected genre profiles must load successfully."""
        profiles = all_genre_profiles()
        for genre in EXPECTED_GENRES:
            assert genre in profiles, f"Missing genre profile: {genre}"

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_profile_has_name(self, genre: str) -> None:
        """Each profile must have a matching name."""
        profile = get_genre_profile(genre)
        assert profile is not None, f"Profile not found: {genre}"
        assert profile.name == genre

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_profile_has_chord_palette(self, genre: str) -> None:
        """Each profile must have a non-empty chord palette."""
        profile = get_genre_profile(genre)
        assert profile is not None
        assert len(profile.chord_palette) > 0, f"{genre} has empty chord_palette"

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_profile_has_preferred_instruments(self, genre: str) -> None:
        """Each profile must list preferred instruments."""
        profile = get_genre_profile(genre)
        assert profile is not None
        assert len(profile.preferred_instruments) > 0, f"{genre} has no preferred_instruments"

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_swing_ratio_in_range(self, genre: str) -> None:
        """Swing ratio must be between 0.5 (straight) and 0.75."""
        profile = get_genre_profile(genre)
        assert profile is not None
        assert 0.5 <= profile.swing_ratio <= 0.75, f"{genre} swing_ratio={profile.swing_ratio} out of range"

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_probabilities_in_range(self, genre: str) -> None:
        """All probability fields must be between 0.0 and 1.0."""
        profile = get_genre_profile(genre)
        assert profile is not None
        for field_name in [
            "seventh_chord_probability",
            "secondary_dominant_probability",
            "modal_interchange_probability",
            "leap_probability",
            "blue_note_probability",
            "syncopation_density",
            "target_spectral_centroid",
        ]:
            val = getattr(profile, field_name)
            assert 0.0 <= val <= 1.0, f"{genre}.{field_name}={val} out of [0,1]"

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_tempo_range_valid(self, genre: str) -> None:
        """Tempo range must have min < max, both positive."""
        profile = get_genre_profile(genre)
        assert profile is not None
        low, high = profile.tempo_range
        assert 20 < low < high < 300, f"{genre} tempo_range=({low},{high}) invalid"

    @pytest.mark.parametrize("genre", EXPECTED_GENRES)
    def test_bass_motion_style_valid(self, genre: str) -> None:
        """Bass motion style must be a valid BassStyle enum."""
        profile = get_genre_profile(genre)
        assert profile is not None
        assert isinstance(profile.bass_motion_style, BassStyle)


class TestGenreProfileDistinctness:
    """Tests that profiles are meaningfully different from each other."""

    def test_not_all_same_swing(self) -> None:
        """Profiles should have varying swing ratios."""
        profiles = all_genre_profiles()
        swings = {p.swing_ratio for p in profiles.values()}
        assert len(swings) > 1, "All genres have the same swing_ratio"

    def test_not_all_same_spectral_centroid(self) -> None:
        """Profiles should have varying spectral centroid targets."""
        profiles = all_genre_profiles()
        centroids = {p.target_spectral_centroid for p in profiles.values()}
        assert len(centroids) > 1, "All genres have the same spectral centroid"

    def test_not_all_same_seventh_probability(self) -> None:
        """Profiles should have varying seventh chord probability."""
        profiles = all_genre_profiles()
        probs = {p.seventh_chord_probability for p in profiles.values()}
        assert len(probs) > 1, "All genres have the same seventh_chord_probability"

    def test_jazz_has_highest_swing(self) -> None:
        """Jazz ballad should have the highest swing ratio."""
        profiles = all_genre_profiles()
        jazz = profiles["jazz_ballad"]
        for name, p in profiles.items():
            if name != "jazz_ballad":
                assert jazz.swing_ratio >= p.swing_ratio, (
                    f"jazz_ballad swing ({jazz.swing_ratio}) should be >= {name} ({p.swing_ratio})"
                )

    def test_chiptune_is_brightest(self) -> None:
        """Chiptune should have the highest spectral centroid target."""
        profiles = all_genre_profiles()
        chip = profiles["game_8bit_chiptune"]
        for name, p in profiles.items():
            if name != "game_8bit_chiptune":
                assert chip.target_spectral_centroid >= p.target_spectral_centroid, (
                    f"chiptune centroid ({chip.target_spectral_centroid}) "
                    f"should be >= {name} ({p.target_spectral_centroid})"
                )


class TestGenreProfileFromYaml:
    """Tests for the from_yaml constructor."""

    def test_minimal_yaml(self) -> None:
        """Minimal YAML with just name and chord_palette should load."""
        data = {"name": "test_genre", "chord_palette": ["I", "IV", "V"]}
        profile = GenreProfile.from_yaml(data)
        assert profile.name == "test_genre"
        assert profile.chord_palette == ("I", "IV", "V")
        # Defaults should apply
        assert profile.swing_ratio == 0.5
        assert profile.seventh_chord_probability == 0.3

    def test_missing_name_raises(self) -> None:
        """YAML without 'name' should raise KeyError."""
        with pytest.raises(KeyError):
            GenreProfile.from_yaml({"chord_palette": ["I"]})

    def test_ngram_parsing(self) -> None:
        """N-gram strings should be parsed into tuple keys."""
        data = {
            "name": "test",
            "progression_n_grams": {"I,IV": 0.5, "IV,V": 0.3},
        }
        profile = GenreProfile.from_yaml(data)
        assert ("I", "IV") in profile.progression_n_grams
        assert profile.progression_n_grams[("I", "IV")] == 0.5


class TestRomanToDegree:
    """Tests for roman_to_degree utility."""

    def test_basic_numerals(self) -> None:
        """Standard Roman numerals map to correct degrees."""
        assert roman_to_degree("I") == 0
        assert roman_to_degree("ii") == 1
        assert roman_to_degree("iii") == 2
        assert roman_to_degree("IV") == 3
        assert roman_to_degree("V") == 4
        assert roman_to_degree("vi") == 5
        assert roman_to_degree("vii") == 6

    def test_seventh_chords(self) -> None:
        """7th chord suffixes are stripped correctly."""
        assert roman_to_degree("Imaj7") == 0
        assert roman_to_degree("ii7") == 1
        assert roman_to_degree("V7") == 4
        assert roman_to_degree("viimin7") == 6

    def test_accidentals(self) -> None:
        """Flat/sharp accidentals are stripped (degree is diatonic base)."""
        assert roman_to_degree("bVII") == 6
        assert roman_to_degree("bVI") == 5
        assert roman_to_degree("bIII") == 2
        assert roman_to_degree("♭VII7") == 6

    def test_extended_suffixes(self) -> None:
        """Extended quality suffixes like dim, aug are handled."""
        assert roman_to_degree("viidim") == 6
        assert roman_to_degree("IIIaug") == 2
        assert roman_to_degree("vii°") == 6
        assert roman_to_degree("iiø") == 1


class TestGenreChordSequence:
    """Tests for genre_chord_sequence Markov chain generation."""

    def test_produces_correct_length(self) -> None:
        """Output sequence has the requested length."""
        import random

        profile = GenreProfile.from_yaml(
            {
                "name": "test",
                "chord_palette": ["I", "IV", "V", "vi"],
                "progression_n_grams": {"I,IV": 0.5, "IV,V": 0.3, "V,I": 0.2},
            }
        )
        seq = genre_chord_sequence(profile, "verse", 8, random.Random(42))
        assert len(seq) == 8

    def test_uses_palette_degrees(self) -> None:
        """All degrees in result should come from the chord palette."""
        import random

        profile = GenreProfile.from_yaml(
            {
                "name": "test",
                "chord_palette": ["I", "IV", "V"],
                "progression_n_grams": {"I,IV": 0.5, "IV,V": 0.5, "V,I": 0.5},
            }
        )
        palette_degrees = {0, 3, 4}
        seq = genre_chord_sequence(profile, "verse", 20, random.Random(42))
        assert all(d in palette_degrees for d in seq)

    def test_deterministic_with_seed(self) -> None:
        """Same seed produces same sequence."""
        import random

        profile = GenreProfile.from_yaml(
            {
                "name": "test",
                "chord_palette": ["I", "ii", "IV", "V", "vi"],
                "progression_n_grams": {"I,IV": 0.3, "IV,V": 0.3, "V,vi": 0.2, "vi,I": 0.2},
            }
        )
        seq1 = genre_chord_sequence(profile, "verse", 8, random.Random(99))
        seq2 = genre_chord_sequence(profile, "verse", 8, random.Random(99))
        assert seq1 == seq2

    def test_empty_palette_falls_back(self) -> None:
        """Empty chord_palette uses diatonic I-IV-V-vi fallback."""
        import random

        profile = GenreProfile.from_yaml({"name": "test"})
        seq = genre_chord_sequence(profile, "verse", 4, random.Random(42))
        assert len(seq) == 4
        assert all(d in {0, 3, 4, 5} for d in seq)

    def test_lofi_produces_jazz_degrees(self) -> None:
        """Lofi profile should produce chord degrees from its jazz palette."""
        import random

        reload_profiles()
        profile = get_genre_profile("lofi_hiphop")
        assert profile is not None
        seq = genre_chord_sequence(profile, "verse", 16, random.Random(42))
        # Lofi palette includes ii(1), V(4), I(0), vi(5), IV(3), iii(2), iv(3), bVI(5), bVII(6)
        # All degrees should be 0-6
        assert all(0 <= d <= 6 for d in seq)
