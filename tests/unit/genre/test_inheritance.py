"""Tests for genre profile inheritance resolution."""

from __future__ import annotations

from yao.genre.inheritance import resolve_inheritance
from yao.genre.profile import GenreProfile, InstrumentRoleSpec


class TestResolveInheritance:
    """Test parent-child profile merging."""

    def test_child_overrides_parent(self) -> None:
        """Child values should override parent values."""
        parent = GenreProfile(
            name="jazz",
            typical_tempo_range=(60.0, 240.0),
            swing_8th=0.67,
            seventh_chord_probability=0.85,
        )
        child = GenreProfile(
            name="bebop",
            parent="jazz",
            typical_tempo_range=(180.0, 300.0),
        )
        resolved = resolve_inheritance(child, parent)
        assert resolved.name == "bebop"
        assert resolved.parent == "jazz"
        assert resolved.typical_tempo_range == (180.0, 300.0)
        # Inherited from parent
        assert resolved.swing_8th == 0.67
        assert resolved.seventh_chord_probability == 0.85

    def test_empty_child_lists_do_not_override(self) -> None:
        """Empty lists in child should not wipe out parent lists."""
        parent = GenreProfile(
            name="jazz",
            chord_palette_extended=["maj7", "min7", "dom7"],
            melodic_devices=["bebop_scale", "enclosure"],
        )
        child = GenreProfile(
            name="modal_jazz",
            parent="jazz",
            # chord_palette_extended is empty by default
        )
        resolved = resolve_inheritance(child, parent)
        assert resolved.chord_palette_extended == ["maj7", "min7", "dom7"]
        assert resolved.melodic_devices == ["bebop_scale", "enclosure"]

    def test_child_explicit_lists_override(self) -> None:
        """Non-empty lists in child should replace parent lists."""
        parent = GenreProfile(
            name="jazz",
            typical_scales=["major", "dorian"],
        )
        child = GenreProfile(
            name="bebop",
            parent="jazz",
            typical_scales=["bebop_major", "altered"],
        )
        resolved = resolve_inheritance(child, parent)
        assert resolved.typical_scales == ["bebop_major", "altered"]

    def test_child_preserves_identity(self) -> None:
        """The resolved profile keeps child's name and parent reference."""
        parent = GenreProfile(name="rock")
        child = GenreProfile(name="punk", parent="rock")
        resolved = resolve_inheritance(child, parent)
        assert resolved.name == "punk"
        assert resolved.parent == "rock"

    def test_numeric_fields_override(self) -> None:
        """Numeric fields in child should override parent."""
        parent = GenreProfile(
            name="hip_hop",
            syncopation_density=0.4,
            target_lufs=-10.0,
        )
        child = GenreProfile(
            name="lofi_hip_hop",
            parent="hip_hop",
            syncopation_density=0.25,
            target_lufs=-16.0,
        )
        resolved = resolve_inheritance(child, parent)
        assert resolved.syncopation_density == 0.25
        assert resolved.target_lufs == -16.0

    def test_instrument_lists_override(self) -> None:
        """Instrument lists in child override parent."""
        parent = GenreProfile(
            name="rock",
            core_instruments=[InstrumentRoleSpec(name="electric_guitar")],
        )
        child = GenreProfile(
            name="punk",
            parent="rock",
            core_instruments=[
                InstrumentRoleSpec(name="electric_guitar"),
                InstrumentRoleSpec(name="bass_guitar"),
            ],
        )
        resolved = resolve_inheritance(child, parent)
        assert len(resolved.core_instruments) == 2

    def test_string_fields_inherit(self) -> None:
        """String fields at default in child should inherit from parent."""
        parent = GenreProfile(
            name="electronic",
            bass_motion_style="syncopated",
            stereo_imaging="wide",
        )
        child = GenreProfile(
            name="house",
            parent="electronic",
        )
        resolved = resolve_inheritance(child, parent)
        assert resolved.bass_motion_style == "syncopated"
        assert resolved.stereo_imaging == "wide"
