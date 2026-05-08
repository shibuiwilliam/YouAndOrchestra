"""Tests for GenreProfile Pydantic model."""

from __future__ import annotations

import pytest

from yao.errors import IncompleteGenreProfileError
from yao.genre.profile import GenreProfile, InstrumentRoleSpec


class TestGenreProfileCreation:
    """Test basic GenreProfile construction and validation."""

    def test_minimal_profile(self) -> None:
        """A profile with only a name should create with defaults."""
        profile = GenreProfile(name="test_genre")
        assert profile.name == "test_genre"
        assert profile.parent is None
        assert profile.swing_8th == 0.5
        assert profile.typical_tempo_range == (80.0, 140.0)

    def test_full_profile(self) -> None:
        """A profile with all fields set should preserve them."""
        profile = GenreProfile(
            name="jazz",
            description="Jazz genre",
            typical_tempo_range=(60.0, 240.0),
            swing_8th=0.67,
            seventh_chord_probability=0.85,
            chord_palette_extended=["maj7", "min7", "dom7"],
            core_instruments=[InstrumentRoleSpec(name="upright_bass", role="bass")],
        )
        assert profile.name == "jazz"
        assert profile.typical_tempo_range == (60.0, 240.0)
        assert profile.swing_8th == 0.67
        assert profile.seventh_chord_probability == 0.85
        assert len(profile.chord_palette_extended) == 3
        assert len(profile.core_instruments) == 1

    def test_tempo_range_coercion_from_list(self) -> None:
        """Tempo range should accept a list and coerce to tuple."""
        profile = GenreProfile(name="test", typical_tempo_range=[100, 180])
        assert profile.typical_tempo_range == (100.0, 180.0)

    def test_dynamics_range_coercion_from_list(self) -> None:
        """Dynamics range should accept a list and coerce to tuple."""
        profile = GenreProfile(name="test", typical_dynamics_range=["pp", "ff"])
        assert profile.typical_dynamics_range == ("pp", "ff")

    def test_instrument_coercion_from_strings(self) -> None:
        """Core instruments should accept a list of plain strings."""
        profile = GenreProfile(
            name="test",
            core_instruments=["piano", "guitar"],  # type: ignore[arg-type]
        )
        assert len(profile.core_instruments) == 2
        assert profile.core_instruments[0].name == "piano"
        assert profile.core_instruments[1].name == "guitar"

    def test_instrument_coercion_from_dicts(self) -> None:
        """Core instruments should accept a list of dicts."""
        profile = GenreProfile(
            name="test",
            core_instruments=[{"name": "piano", "role": "harmony"}],  # type: ignore[arg-type]
        )
        assert len(profile.core_instruments) == 1
        assert profile.core_instruments[0].role == "harmony"


class TestGenreProfileFromYaml:
    """Test loading from YAML data."""

    def test_from_yaml_data(self) -> None:
        """from_yaml_data should produce a valid profile."""
        data = {
            "name": "blues",
            "typical_tempo_range": [70, 130],
            "swing_8th": 0.6,
            "blue_note_probability": 0.3,
            "chord_palette_extended": ["dom7", "9"],
        }
        profile = GenreProfile.from_yaml_data(data)
        assert profile.name == "blues"
        assert profile.typical_tempo_range == (70.0, 130.0)
        assert profile.swing_8th == 0.6
        assert profile.blue_note_probability == 0.3

    def test_extra_fields_allowed(self) -> None:
        """Extra fields in YAML should not cause validation errors."""
        data = {
            "name": "test",
            "custom_field": "custom_value",
        }
        profile = GenreProfile.from_yaml_data(data)
        assert profile.name == "test"


class TestGenreProfileValidation:
    """Test profile validation."""

    def test_validate_complete_raises_for_missing_name(self) -> None:
        """validate_complete should raise for an empty name."""
        profile = GenreProfile(name="")
        with pytest.raises(IncompleteGenreProfileError):
            profile.validate_complete()

    def test_validate_complete_ok_with_parent(self) -> None:
        """A profile with a parent can have default tempo_range."""
        profile = GenreProfile(name="bebop", parent="jazz")
        # Should not raise since parent provides defaults
        result = profile.validate_complete()
        assert result == []

    def test_frozen_profile_is_hashable(self) -> None:
        """Profiles should be usable in sets/dicts by name."""
        p1 = GenreProfile(name="jazz")
        p2 = GenreProfile(name="rock")
        profiles = {p1.name: p1, p2.name: p2}
        assert len(profiles) == 2
