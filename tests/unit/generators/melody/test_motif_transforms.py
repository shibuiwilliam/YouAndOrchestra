"""Tests for extended motif transformations (Phase B).

Tests the 8 new transformations added alongside the original 5:
sequence, fragment, extend, truncate, chromatic_decoration,
rhythmic_displacement, interpolate, plus the TRANSFORMATION_REGISTRY.
"""

from __future__ import annotations

from yao.ir.motif import (
    TRANSFORMATION_REGISTRY,
    Motif,
    chromatic_decoration,
    extend,
    fragment,
    interpolate,
    rhythmic_displacement,
    sequence,
    truncate,
)
from yao.ir.note import Note


def _make_motif(pitches: list[int], dur: float = 1.0) -> Motif:
    """Create a simple motif from a pitch list."""
    notes = tuple(
        Note(pitch=p, start_beat=i * dur, duration_beats=dur, velocity=80, instrument="melody")
        for i, p in enumerate(pitches)
    )
    return Motif(notes=notes, label="test")


class TestSequence:
    """Tests for sequential repetition."""

    def test_basic_sequence(self) -> None:
        """Sequence produces original + transposed copies."""
        m = _make_motif([60, 62, 64])
        result = sequence(m, semitones=2, repetitions=1)
        # Original 3 notes + 1 copy of 3 = 6
        assert len(result.notes) == 6
        # Copy should be 2 semitones higher
        assert result.notes[3].pitch == 62
        assert result.notes[4].pitch == 64
        assert result.notes[5].pitch == 66

    def test_sequence_records_transformation(self) -> None:
        """Sequence records its transformation."""
        m = _make_motif([60])
        result = sequence(m, semitones=3, repetitions=2)
        assert "sequence(3x2)" in result.transformations_applied

    def test_empty_motif(self) -> None:
        """Empty motif returns empty."""
        m = Motif(notes=(), label="empty")
        assert sequence(m, 2).notes == ()


class TestFragment:
    """Tests for motif fragmentation."""

    def test_basic_fragment(self) -> None:
        """Fragment extracts a subset of notes."""
        m = _make_motif([60, 62, 64, 65, 67])
        result = fragment(m, start_idx=1, length=3)
        assert len(result.notes) == 3
        assert result.notes[0].pitch == 62
        assert result.notes[2].pitch == 65

    def test_fragment_normalizes_beats(self) -> None:
        """Fragment normalizes start_beat to 0."""
        m = _make_motif([60, 62, 64])
        result = fragment(m, start_idx=1, length=2)
        assert result.notes[0].start_beat == 0.0


class TestExtend:
    """Tests for motif extension."""

    def test_basic_extend(self) -> None:
        """Extension appends notes continuing the pattern."""
        m = _make_motif([60, 62])  # ascending by 2
        result = extend(m, extra_notes=2)
        assert len(result.notes) == 4
        assert result.notes[2].pitch == 64
        assert result.notes[3].pitch == 66


class TestTruncate:
    """Tests for motif truncation."""

    def test_basic_truncate(self) -> None:
        """Truncation keeps only first N notes."""
        m = _make_motif([60, 62, 64, 65, 67])
        result = truncate(m, keep=3)
        assert len(result.notes) == 3
        assert result.notes[-1].pitch == 64

    def test_truncate_more_than_length(self) -> None:
        """Truncating with keep > length returns original."""
        m = _make_motif([60, 62])
        result = truncate(m, keep=10)
        assert len(result.notes) == 2


class TestChromaticDecoration:
    """Tests for chromatic approach tones."""

    def test_doubles_notes(self) -> None:
        """Each note gets a chromatic approach, doubling the count."""
        m = _make_motif([60, 64])
        result = chromatic_decoration(m)
        assert len(result.notes) == 4  # 2 approach + 2 main

    def test_approach_from_below(self) -> None:
        """Approach tone is one semitone below."""
        m = _make_motif([60])
        result = chromatic_decoration(m)
        assert result.notes[0].pitch == 59  # approach
        assert result.notes[1].pitch == 60  # target


class TestRhythmicDisplacement:
    """Tests for rhythmic displacement."""

    def test_shift_forward(self) -> None:
        """Displacement shifts all notes forward."""
        m = _make_motif([60, 62])
        result = rhythmic_displacement(m, offset_beats=0.5)
        assert result.notes[0].start_beat == 0.5
        assert result.notes[1].start_beat == 1.5

    def test_records_transformation(self) -> None:
        """Displacement records its offset."""
        m = _make_motif([60])
        result = rhythmic_displacement(m, offset_beats=1.0)
        assert "rhythmic_displacement(1.0)" in result.transformations_applied


class TestInterpolate:
    """Tests for interpolation."""

    def test_inserts_midpoints(self) -> None:
        """Interpolation inserts notes between existing ones."""
        m = _make_motif([60, 64])
        result = interpolate(m)
        assert len(result.notes) == 3  # original 2 + 1 interpolated
        assert result.notes[1].pitch == 62  # midpoint


class TestTransformationRegistry:
    """Tests for the TRANSFORMATION_REGISTRY."""

    def test_all_13_transforms(self) -> None:
        """Registry contains all 13 transformations."""
        expected = {
            "identity",
            "transposed",
            "inverted",
            "retrograde",
            "augmented",
            "diminished",
            "sequential",
            "fragmented",
            "extension",
            "truncation",
            "chromatic_decoration",
            "rhythmic_displacement",
            "interpolation",
        }
        assert set(TRANSFORMATION_REGISTRY.keys()) == expected

    def test_identity_returns_same(self) -> None:
        """Identity transformation returns the motif unchanged."""
        m = _make_motif([60, 62])
        identity = TRANSFORMATION_REGISTRY["identity"]
        result = identity(m)
        assert result.notes == m.notes
