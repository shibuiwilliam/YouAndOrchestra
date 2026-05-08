"""Tests for the voice-leading optimizer.

Phase 3.5 Step 4 — IMPROVEMENT.md §5.4, PROJECT.md §3.4.2.
"""

from __future__ import annotations

from yao.coupling.voice_leading import (
    VoicingConstraints,
    optimal_voicing_transition,
)


class TestOptimalVoicingTransition:
    """Core voice-leading optimization tests."""

    def test_returns_correct_voice_count(self) -> None:
        prev = [48, 55, 60, 67]
        result = optimal_voicing_transition(prev, "C", "maj", voice_count=4)
        assert len(result) == 4

    def test_result_is_sorted_ascending(self) -> None:
        prev = [48, 55, 60, 67]
        result = optimal_voicing_transition(prev, "F", "maj", voice_count=4)
        assert result == sorted(result)

    def test_minimal_motion_same_chord(self) -> None:
        """Same chord should produce minimal (possibly zero) motion."""
        prev = [48, 55, 60, 67]  # C major voicing
        result = optimal_voicing_transition(prev, "C", "maj", voice_count=4)
        motion = sum(abs(r - p) for r, p in zip(result, prev, strict=False))
        assert motion <= 12  # reasonable threshold

    def test_close_position_preferred(self) -> None:
        """Moving from C to G should produce smooth voice leading."""
        prev = [48, 52, 55, 60]  # C major close
        result = optimal_voicing_transition(prev, "G", "maj", voice_count=4)
        motion = sum(abs(r - p) for r, p in zip(result, prev, strict=False))
        # Should be modest motion for a closely-related chord
        assert motion <= 20

    def test_deterministic(self) -> None:
        """Same inputs produce same outputs."""
        prev = [48, 55, 60, 67]
        r1 = optimal_voicing_transition(prev, "F", "maj", voice_count=4)
        r2 = optimal_voicing_transition(prev, "F", "maj", voice_count=4)
        assert r1 == r2

    def test_all_notes_are_chord_tones(self) -> None:
        """All result notes should be pitch classes of the target chord."""
        prev = [48, 55, 60, 67]
        result = optimal_voicing_transition(prev, "F", "maj", voice_count=4)
        # F major: F=5, A=9, C=0
        f_maj_pcs = {5, 9, 0}
        for note in result:
            assert note % 12 in f_maj_pcs, f"MIDI {note} (pc={note % 12}) not in F major"

    def test_three_voices(self) -> None:
        prev = [48, 55, 60]
        result = optimal_voicing_transition(prev, "G", "maj", voice_count=3)
        assert len(result) == 3

    def test_dom7_chord(self) -> None:
        """Dominant 7th chord produces 4 pitch classes."""
        prev = [48, 55, 60, 67]
        result = optimal_voicing_transition(prev, "G", "dom7", voice_count=4)
        g7_pcs = {7, 11, 2, 5}  # G B D F
        for note in result:
            assert note % 12 in g7_pcs


class TestVoicingConstraints:
    """Constraint filtering tests."""

    def test_max_leap_respected(self) -> None:
        """No voice should leap more than max_leap."""
        prev = [48, 55, 60, 67]
        constraints = VoicingConstraints(max_leap=7)
        result = optimal_voicing_transition(prev, "F", "maj", voice_count=4, constraints=constraints)
        for i in range(len(result)):
            assert abs(result[i] - prev[i]) <= 7 or result == prev[:4]

    def test_default_constraints_applied(self) -> None:
        """Default constraints don't crash."""
        prev = [48, 55, 60, 67]
        result = optimal_voicing_transition(prev, "D", "min7", voice_count=4)
        assert len(result) == 4

    def test_relaxed_constraints(self) -> None:
        """With all constraints off, still returns valid voicing."""
        prev = [48, 55, 60, 67]
        constraints = VoicingConstraints(
            no_parallel_fifths=False,
            no_parallel_octaves=False,
            no_voice_crossing=False,
            max_leap=24,
        )
        result = optimal_voicing_transition(prev, "F", "maj", voice_count=4, constraints=constraints)
        assert len(result) == 4


class TestEdgeCases:
    """Edge case handling."""

    def test_enharmonic_root(self) -> None:
        """Handles Bb correctly."""
        prev = [48, 55, 60, 67]
        result = optimal_voicing_transition(prev, "Bb", "maj", voice_count=4)
        bb_pcs = {10, 2, 5}  # Bb D F
        for note in result:
            assert note % 12 in bb_pcs

    def test_short_prev_voicing_padded(self) -> None:
        """Handles prev voicing shorter than voice_count."""
        prev = [60, 64]
        result = optimal_voicing_transition(prev, "C", "maj", voice_count=4)
        assert len(result) == 4
