"""Tests for Skeleton IR types: SkeletonNote, Skeleton."""

from __future__ import annotations

import pytest

from yao.ir.skeleton import Skeleton, SkeletonNote


class TestSkeletonNote:
    """Tests for SkeletonNote dataclass."""

    def test_creation(self) -> None:
        """SkeletonNote can be created with required fields."""
        sn = SkeletonNote(bar=0, beat=0.0, midi_pitch=60)
        assert sn.bar == 0
        assert sn.beat == 0.0
        assert sn.midi_pitch == 60

    def test_defaults(self) -> None:
        """Default values are correct."""
        sn = SkeletonNote(bar=0, beat=0.0, midi_pitch=60)
        assert sn.chord_relation == "root"
        assert sn.structural_role == "passing"
        assert sn.phrase_id == 0

    def test_absolute_beat(self) -> None:
        """Absolute beat computed correctly for 4/4 time."""
        sn = SkeletonNote(bar=2, beat=1.5, midi_pitch=64)
        assert sn.absolute_beat == 9.5  # 2 * 4 + 1.5

    def test_frozen(self) -> None:
        """SkeletonNote is immutable."""
        sn = SkeletonNote(bar=0, beat=0.0, midi_pitch=60)
        with pytest.raises(AttributeError):
            sn.midi_pitch = 61  # type: ignore[misc]

    def test_structural_roles(self) -> None:
        """Skeleton notes with various structural roles."""
        start = SkeletonNote(bar=0, beat=0.0, midi_pitch=60, structural_role="phrase_start")
        climax = SkeletonNote(bar=3, beat=0.0, midi_pitch=72, structural_role="climax")
        target = SkeletonNote(bar=7, beat=0.0, midi_pitch=60, structural_role="cadence_target")
        assert start.structural_role == "phrase_start"
        assert climax.structural_role == "climax"
        assert target.structural_role == "cadence_target"


class TestSkeleton:
    """Tests for Skeleton dataclass."""

    def test_empty_skeleton(self) -> None:
        """Empty skeleton is valid."""
        skel = Skeleton(notes=())
        assert skel.note_count == 0
        assert skel.pitch_range == (0, 0)

    def test_skeleton_with_notes(self) -> None:
        """Skeleton properties computed correctly."""
        notes = (
            SkeletonNote(bar=0, beat=0.0, midi_pitch=60),
            SkeletonNote(bar=1, beat=0.0, midi_pitch=67),
            SkeletonNote(bar=2, beat=0.0, midi_pitch=64),
        )
        skel = Skeleton(notes=notes)
        assert skel.note_count == 3
        assert skel.pitch_range == (60, 67)

    def test_target_pitches_default(self) -> None:
        """Default target_pitches is empty dict."""
        skel = Skeleton(notes=())
        assert skel.target_pitches == {}

    def test_target_pitches_custom(self) -> None:
        """Custom target_pitches preserved."""
        skel = Skeleton(notes=(), target_pitches={0: 60, 4: 67})
        assert skel.target_pitches[0] == 60
        assert skel.target_pitches[4] == 67
