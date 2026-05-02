"""Tests for DrumPattern IR."""

from __future__ import annotations

from yao.ir.drum import GM_DRUM_MAP, DrumHit, DrumPattern


class TestDrumHit:
    """Test DrumHit creation and MIDI conversion."""

    def test_create_hit(self) -> None:
        hit = DrumHit(time_beats=0.0, duration_beats=0.25, kit_piece="kick", velocity=100)
        assert hit.kit_piece == "kick"
        assert hit.velocity == 100
        assert hit.microtiming_ms == 0.0

    def test_to_midi_pitch(self) -> None:
        assert DrumHit(0, 0.25, "kick", 100).to_midi_pitch() == 36
        assert DrumHit(0, 0.25, "snare", 100).to_midi_pitch() == 38
        assert DrumHit(0, 0.25, "closed_hat", 80).to_midi_pitch() == 42
        assert DrumHit(0, 0.25, "ride", 80).to_midi_pitch() == 51

    def test_microtiming(self) -> None:
        hit = DrumHit(0.0, 0.25, "snare", 90, microtiming_ms=-5.0)
        assert hit.microtiming_ms == -5.0


class TestDrumPattern:
    """Test DrumPattern creation and queries."""

    def test_create_pattern(self) -> None:
        pattern = DrumPattern(
            id="test",
            genre="pop",
            hits=(
                DrumHit(0.0, 0.25, "kick", 100),
                DrumHit(1.0, 0.25, "snare", 105),
                DrumHit(0.0, 0.25, "closed_hat", 80),
            ),
        )
        assert len(pattern.hits) == 3  # noqa: PLR2004
        assert pattern.swing == 0.0

    def test_kit_pieces_used(self) -> None:
        pattern = DrumPattern(
            id="test",
            genre="pop",
            hits=(
                DrumHit(0.0, 0.25, "kick", 100),
                DrumHit(1.0, 0.25, "snare", 105),
                DrumHit(0.0, 0.25, "closed_hat", 80),
                DrumHit(0.5, 0.25, "closed_hat", 70),
            ),
        )
        assert pattern.kit_pieces_used() == {"kick", "snare", "closed_hat"}


class TestGMDrumMap:
    """Test General MIDI drum map completeness."""

    def test_all_pieces_mapped(self) -> None:
        expected = {
            "kick",
            "snare",
            "rim",
            "closed_hat",
            "open_hat",
            "pedal_hat",
            "clap",
            "tom_low",
            "tom_mid",
            "tom_high",
            "crash",
            "ride",
            "ride_bell",
            "shaker",
            "tambourine",
        }
        assert set(GM_DRUM_MAP.keys()) == expected

    def test_all_pitches_unique(self) -> None:
        pitches = list(GM_DRUM_MAP.values())
        assert len(pitches) == len(set(pitches))

    def test_pitches_in_gm_range(self) -> None:
        for pitch in GM_DRUM_MAP.values():
            assert 35 <= pitch <= 81  # noqa: PLR2004
