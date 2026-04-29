"""Tests for the voicing IR module."""

from __future__ import annotations

from yao.ir.voicing import (
    Voicing,
    check_parallel_fifths,
    check_parallel_octaves,
    voice_distance,
)


class TestVoicing:
    def test_voice_count(self) -> None:
        v = Voicing(pitches=(60, 64, 67))
        assert v.voice_count == 3

    def test_span(self) -> None:
        v = Voicing(pitches=(60, 64, 67))
        assert v.span == 7  # C4 to G4

    def test_interval_between(self) -> None:
        v = Voicing(pitches=(60, 64, 67))
        assert v.interval_between(0, 1) == 4  # C to E = major 3rd
        assert v.interval_between(0, 2) == 7  # C to G = perfect 5th


class TestParallelFifths:
    def test_detects_parallel_fifths(self) -> None:
        # C-G moving to D-A = parallel fifths
        v1 = Voicing(pitches=(60, 67))  # C4, G4
        v2 = Voicing(pitches=(62, 69))  # D4, A4
        parallels = check_parallel_fifths(v1, v2)
        assert len(parallels) == 1
        assert parallels[0] == (0, 1)

    def test_no_parallel_fifths_with_contrary_motion(self) -> None:
        # C-G to D-F# = both are fifths but voices cross (not parallel)
        v1 = Voicing(pitches=(60, 67))  # C4, G4
        v2 = Voicing(pitches=(62, 66))  # D4, F#4 (not a fifth)
        parallels = check_parallel_fifths(v1, v2)
        assert len(parallels) == 0

    def test_no_parallel_when_stationary(self) -> None:
        v1 = Voicing(pitches=(60, 67))
        v2 = Voicing(pitches=(60, 67))  # same voicing = no motion
        parallels = check_parallel_fifths(v1, v2)
        assert len(parallels) == 0


class TestParallelOctaves:
    def test_detects_parallel_octaves(self) -> None:
        v1 = Voicing(pitches=(60, 72))  # C4, C5
        v2 = Voicing(pitches=(62, 74))  # D4, D5
        parallels = check_parallel_octaves(v1, v2)
        assert len(parallels) == 1

    def test_no_parallel_octaves(self) -> None:
        v1 = Voicing(pitches=(60, 72))  # C4, C5
        v2 = Voicing(pitches=(62, 71))  # D4, B4 (not octave)
        parallels = check_parallel_octaves(v1, v2)
        assert len(parallels) == 0


class TestVoiceDistance:
    def test_minimal_movement(self) -> None:
        v1 = Voicing(pitches=(60, 64, 67))
        v2 = Voicing(pitches=(60, 65, 67))  # only middle voice moves 1 semitone
        assert voice_distance(v1, v2) == 1

    def test_no_movement(self) -> None:
        v1 = Voicing(pitches=(60, 64, 67))
        assert voice_distance(v1, v1) == 0

    def test_large_movement(self) -> None:
        v1 = Voicing(pitches=(60, 64, 67))
        v2 = Voicing(pitches=(72, 76, 79))  # all move up an octave
        assert voice_distance(v1, v2) == 36
