"""Tests for groove integration: loading, ghost notes, swing measurement."""

from __future__ import annotations

import random

from yao.generators.melody.groove import (
    add_ghost_notes,
    load_groove_profile,
    measure_swing_ratio,
)
from yao.ir.melody_line import MelodyLine, MelodyNote
from yao.schema.melodic_profile import (
    IntervalDistribution,
    MelodicProfile,
    OrnamentProfile,
    PhraseLengthDistribution,
)


def _make_melody(notes_data: list[tuple[int, float, float, int]]) -> MelodyLine:
    """Create MelodyLine from (bar, beat, duration, pitch) tuples."""
    notes = tuple(
        MelodyNote(bar=bar, beat=beat, duration_beats=dur, midi_pitch=pitch) for bar, beat, dur, pitch in notes_data
    )
    return MelodyLine(notes=notes)


def _make_profile(**overrides: object) -> MelodicProfile:
    """Create a test MelodicProfile."""
    defaults: dict = {
        "genre": "test",
        "interval_distribution": IntervalDistribution(distribution={2: 0.5, 3: 0.5}),
        "phrase_length_distribution": PhraseLengthDistribution(distribution={4: 1.0}),
    }
    defaults.update(overrides)
    return MelodicProfile(**defaults)


class TestLoadGrooveProfile:
    """Tests for groove profile loading."""

    def test_load_jazz_swing(self) -> None:
        """Jazz swing groove loads from grooves/ directory."""
        profile = load_groove_profile("jazz_swing")
        assert profile.name == "jazz_swing"
        assert profile.swing_ratio > 0.6

    def test_load_lofi(self) -> None:
        """Lo-fi groove loads successfully."""
        profile = load_groove_profile("lofi_hiphop")
        assert profile.name == "lofi_hiphop"

    def test_unknown_returns_default(self) -> None:
        """Unknown groove name returns a default profile."""
        profile = load_groove_profile("nonexistent_xyz")
        assert profile.name == "nonexistent_xyz"
        assert profile.swing_ratio == 0.5


class TestGhostNotes:
    """Tests for ghost note insertion."""

    def test_ghost_notes_added(self) -> None:
        """Ghost notes are added when probability > 0."""
        melody = _make_melody(
            [
                (0, 0.0, 1.0, 60),
                (0, 1.0, 1.0, 64),
                (0, 2.0, 1.0, 67),
                (0, 3.0, 1.0, 64),
                (1, 0.0, 1.0, 60),
                (1, 1.0, 1.0, 62),
                (1, 2.0, 1.0, 64),
                (1, 3.0, 1.0, 67),
            ]
        )
        profile = _make_profile(
            ornament_profile=OrnamentProfile(ghost_note_probability=0.5),
        )

        result = add_ghost_notes(melody, profile, random.Random(42))

        # Should have more notes than original
        assert result.note_count > melody.note_count
        # Ghost notes should have low velocity
        ghosts = [n for n in result.notes if n.note_type == "ghost"]
        assert len(ghosts) > 0
        for g in ghosts:
            assert g.velocity < 40

    def test_no_ghosts_when_probability_zero(self) -> None:
        """No ghost notes when probability is 0."""
        melody = _make_melody([(0, 0.0, 1.0, 60), (0, 1.0, 1.0, 64)])
        profile = _make_profile(
            ornament_profile=OrnamentProfile(ghost_note_probability=0.0),
        )

        result = add_ghost_notes(melody, profile, random.Random(42))
        assert result.note_count == melody.note_count

    def test_ghost_notes_sorted(self) -> None:
        """Output notes are sorted by position."""
        melody = _make_melody(
            [
                (0, 0.0, 1.0, 60),
                (0, 1.0, 1.0, 64),
                (0, 2.0, 1.0, 67),
                (0, 3.0, 1.0, 60),
            ]
        )
        profile = _make_profile(
            ornament_profile=OrnamentProfile(ghost_note_probability=0.8),
        )

        result = add_ghost_notes(melody, profile, random.Random(42))
        for i in range(1, len(result.notes)):
            assert (result.notes[i].bar, result.notes[i].beat) >= (
                result.notes[i - 1].bar,
                result.notes[i - 1].beat,
            )


class TestSwingMeasurement:
    """Tests for swing ratio measurement."""

    def test_straight_8ths(self) -> None:
        """Straight 8ths measure close to 0.5."""
        melody = _make_melody(
            [
                (0, 0.0, 0.5, 60),
                (0, 0.5, 0.5, 62),
                (0, 1.0, 0.5, 64),
                (0, 1.5, 0.5, 65),
                (0, 2.0, 0.5, 67),
                (0, 2.5, 0.5, 69),
                (0, 3.0, 0.5, 71),
                (0, 3.5, 0.5, 72),
            ]
        )
        ratio = measure_swing_ratio(melody)
        assert abs(ratio - 0.5) < 0.05

    def test_swung_8ths(self) -> None:
        """Swung 8ths (triplet feel) measure close to 0.67."""
        melody = _make_melody(
            [
                (0, 0.0, 0.67, 60),
                (0, 0.67, 0.33, 62),
                (0, 1.0, 0.67, 64),
                (0, 1.67, 0.33, 65),
                (0, 2.0, 0.67, 67),
                (0, 2.67, 0.33, 69),
                (0, 3.0, 0.67, 71),
                (0, 3.67, 0.33, 72),
            ]
        )
        ratio = measure_swing_ratio(melody)
        assert ratio > 0.55

    def test_empty_melody(self) -> None:
        """Empty melody returns 0.5 (straight)."""
        melody = MelodyLine(notes=())
        assert measure_swing_ratio(melody) == 0.5
