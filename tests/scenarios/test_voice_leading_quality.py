"""Scenario test: voice-leading optimizer reduces total motion.

Tests that optimal_voicing_transition produces smoother voice leading
than naive root-position voicings.

Phase 3.5 Step 7 — IMPROVEMENT.md §5.4.
"""

from __future__ import annotations

from yao.coupling.voice_leading import optimal_voicing_transition
from yao.ir.voicing import Voicing
from yao.verify.voice_leading_smoothness import evaluate_voice_leading_smoothness


def _naive_voicing(root_pc: int, quality_intervals: tuple[int, ...], base_octave: int = 48) -> list[int]:
    """Build a naive root-position voicing."""
    return sorted(base_octave + (root_pc + iv) % 12 for iv in quality_intervals)


class TestVoiceLeadingQuality:
    """Scenario: optimized voicings have less motion than naive ones."""

    def test_optimized_less_motion_than_naive(self) -> None:
        """I-IV-V-I: optimized total motion < naive total motion."""
        # Naive root-position voicings in C major
        naive_voicings = [
            Voicing(pitches=tuple(_naive_voicing(0, (0, 4, 7)))),  # C maj
            Voicing(pitches=tuple(_naive_voicing(5, (0, 4, 7)))),  # F maj
            Voicing(pitches=tuple(_naive_voicing(7, (0, 4, 7)))),  # G maj
            Voicing(pitches=tuple(_naive_voicing(0, (0, 4, 7)))),  # C maj
        ]
        naive_report = evaluate_voice_leading_smoothness(naive_voicings)

        # Optimized voicings: start from C, optimize each transition
        prev = list(naive_voicings[0].pitches)
        optimized: list[Voicing] = [naive_voicings[0]]
        for chord_root, chord_quality in [("F", "maj"), ("G", "maj"), ("C", "maj")]:
            next_voicing = optimal_voicing_transition(prev, chord_root, chord_quality, voice_count=3)
            optimized.append(Voicing(pitches=tuple(next_voicing)))
            prev = next_voicing

        opt_report = evaluate_voice_leading_smoothness(optimized)

        # Optimized should have equal or less total motion
        assert opt_report.total_motion <= naive_report.total_motion, (
            f"Optimized motion ({opt_report.total_motion}) should be <= naive ({naive_report.total_motion})"
        )

    def test_smooth_ii_v_i_progression(self) -> None:
        """ii-V-I progression should have smooth voice leading."""
        prev = [50, 53, 57, 60]  # Dm voicing
        v7 = optimal_voicing_transition(prev, "G", "dom7", voice_count=4)
        i_maj = optimal_voicing_transition(v7, "C", "maj", voice_count=4)

        voicings = [
            Voicing(pitches=tuple(prev)),
            Voicing(pitches=tuple(v7)),
            Voicing(pitches=tuple(i_maj)),
        ]
        report = evaluate_voice_leading_smoothness(voicings)

        # Each transition should average modest motion (< 6 semitones per voice)
        assert report.average_motion < 24, f"ii-V-I average motion {report.average_motion:.1f} too large"

    def test_parallel_fifths_avoided(self) -> None:
        """Optimized voicings should not contain parallel fifths."""
        from yao.ir.voicing import check_parallel_fifths

        prev = [48, 55, 60, 67]  # C major
        next_v = optimal_voicing_transition(prev, "G", "maj", voice_count=4)

        parallels = check_parallel_fifths(
            Voicing(pitches=tuple(prev)),
            Voicing(pitches=tuple(next_v)),
        )
        assert len(parallels) == 0, f"Found parallel fifths: {parallels}"

    def test_deterministic_across_calls(self) -> None:
        """Same input produces identical voice leading."""
        prev = [48, 52, 55, 60]
        r1 = optimal_voicing_transition(prev, "F", "maj", voice_count=4)
        r2 = optimal_voicing_transition(prev, "F", "maj", voice_count=4)
        assert r1 == r2
