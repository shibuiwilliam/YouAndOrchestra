"""Tests for voice-leading smoothness metric.

Phase 3.5 Step 6 — PROJECT.md §12.10.
"""

from __future__ import annotations

from yao.ir.voicing import Voicing
from yao.verify.voice_leading_smoothness import (
    VoiceLeadingReport,
    evaluate_voice_leading_smoothness,
)


class TestVoiceLeadingReport:
    def test_report_fields(self) -> None:
        report = VoiceLeadingReport(total_motion=24, transition_count=3, average_motion=8.0, max_single_voice_leap=5)
        assert report.total_motion == 24
        assert report.average_motion == 8.0


class TestEvaluateVoiceLeadingSmoothness:
    def test_empty_sequence(self) -> None:
        report = evaluate_voice_leading_smoothness([])
        assert report.total_motion == 0
        assert report.transition_count == 0

    def test_single_voicing(self) -> None:
        voicings = [Voicing(pitches=(48, 55, 60, 67))]
        report = evaluate_voice_leading_smoothness(voicings)
        assert report.total_motion == 0
        assert report.transition_count == 0

    def test_smooth_progression(self) -> None:
        """C major -> F major with smooth voice leading."""
        voicings = [
            Voicing(pitches=(48, 52, 55, 60)),  # C E G C
            Voicing(pitches=(48, 53, 57, 60)),  # C F A C (smooth: E->F, G->A)
        ]
        report = evaluate_voice_leading_smoothness(voicings)
        assert report.transition_count == 1
        assert report.total_motion > 0
        assert report.average_motion == float(report.total_motion)

    def test_large_leap_detected(self) -> None:
        """A large jump should be reflected in max_single_voice_leap."""
        voicings = [
            Voicing(pitches=(48, 55, 60, 67)),
            Voicing(pitches=(48, 55, 60, 79)),  # top voice jumps 12
        ]
        report = evaluate_voice_leading_smoothness(voicings)
        assert report.max_single_voice_leap == 12

    def test_no_motion_same_voicing(self) -> None:
        """Repeated same voicing = zero motion."""
        v = Voicing(pitches=(48, 55, 60, 67))
        report = evaluate_voice_leading_smoothness([v, v, v])
        assert report.total_motion == 0
        assert report.transition_count == 2
        assert report.average_motion == 0.0
        assert report.max_single_voice_leap == 0

    def test_multiple_transitions(self) -> None:
        voicings = [
            Voicing(pitches=(48, 52, 55, 60)),
            Voicing(pitches=(48, 53, 57, 60)),
            Voicing(pitches=(47, 55, 59, 62)),
        ]
        report = evaluate_voice_leading_smoothness(voicings)
        assert report.transition_count == 2
        assert report.total_motion > 0
