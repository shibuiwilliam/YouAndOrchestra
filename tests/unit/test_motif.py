"""Tests for the motif IR module."""

from __future__ import annotations

from yao.ir.motif import Motif, augment, diminish, invert, retrograde, transpose
from yao.ir.note import Note


def _make_simple_motif() -> Motif:
    """Create a simple C-D-E motif for testing."""
    return Motif(
        notes=(
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
            Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="piano"),
            Note(pitch=64, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="piano"),
        ),
        label="test_motif",
    )


class TestMotif:
    def test_duration_beats(self) -> None:
        m = _make_simple_motif()
        assert m.duration_beats == 3.0

    def test_pitch_range(self) -> None:
        m = _make_simple_motif()
        assert m.pitch_range == (60, 64)

    def test_empty_motif(self) -> None:
        m = Motif(notes=())
        assert m.duration_beats == 0.0
        assert m.pitch_range == (0, 0)

    def test_frozen(self) -> None:
        m = _make_simple_motif()
        import pytest

        with pytest.raises(AttributeError):
            m.label = "changed"  # type: ignore[misc]


class TestTranspose:
    def test_transpose_up(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, 5)
        assert [n.pitch for n in result.notes] == [65, 67, 69]

    def test_transpose_down(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, -2)
        assert [n.pitch for n in result.notes] == [58, 60, 62]

    def test_transpose_records_transformation(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, 3)
        assert "transpose(3)" in result.transformations_applied

    def test_transpose_preserves_rhythm(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, 5)
        for orig, trans in zip(m.notes, result.notes, strict=True):
            assert orig.start_beat == trans.start_beat
            assert orig.duration_beats == trans.duration_beats


class TestInvert:
    def test_invert_around_first_note(self) -> None:
        m = _make_simple_motif()
        result = invert(m)
        # C(60) stays, D(62) → Bb(58), E(64) → Ab(56)
        assert [n.pitch for n in result.notes] == [60, 58, 56]

    def test_invert_around_axis(self) -> None:
        m = _make_simple_motif()
        result = invert(m, axis=62)
        # C(60) → D(64), D(62) stays, E(64) → C(60)
        assert [n.pitch for n in result.notes] == [64, 62, 60]


class TestRetrograde:
    def test_retrograde_reverses_order(self) -> None:
        m = _make_simple_motif()
        result = retrograde(m)
        # E plays first (at beat 0), then D, then C
        assert result.notes[0].pitch == 64
        assert result.notes[1].pitch == 62
        assert result.notes[2].pitch == 60

    def test_retrograde_records_transformation(self) -> None:
        m = _make_simple_motif()
        result = retrograde(m)
        assert "retrograde" in result.transformations_applied


class TestAugment:
    def test_augment_doubles_duration(self) -> None:
        m = _make_simple_motif()
        result = augment(m, 2.0)
        for note in result.notes:
            assert note.duration_beats == 2.0

    def test_augment_stretches_positions(self) -> None:
        m = _make_simple_motif()
        result = augment(m, 2.0)
        assert result.notes[0].start_beat == 0.0
        assert result.notes[1].start_beat == 2.0
        assert result.notes[2].start_beat == 4.0


class TestDiminish:
    def test_diminish_halves_duration(self) -> None:
        m = _make_simple_motif()
        result = diminish(m, 2.0)
        for note in result.notes:
            assert note.duration_beats == 0.5
