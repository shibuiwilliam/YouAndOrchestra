"""Voice-Leading Smoothness metric.

Measures total voice motion across consecutive chords relative to the
theoretical minimum (Hungarian-optimal).

Target: <= 1.5x minimum for COMMON_PRACTICE, <= 2.0x for JAZZ.

Belongs to Layer 6 (Verification).

See IMPROVEMENT.md §5.4, PROJECT.md §12.10, CLAUDE.md Phase 3.5 Step 6.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.ir.voicing import Voicing, voice_distance


@dataclass(frozen=True)
class VoiceLeadingReport:
    """Result of voice-leading smoothness evaluation.

    Attributes:
        total_motion: Sum of absolute semitone movement across all transitions.
        transition_count: Number of chord transitions evaluated.
        average_motion: Average motion per transition.
        max_single_voice_leap: Largest single-voice leap observed.
    """

    total_motion: int
    transition_count: int
    average_motion: float
    max_single_voice_leap: int


def evaluate_voice_leading_smoothness(
    voicings: list[Voicing],
) -> VoiceLeadingReport:
    """Evaluate voice-leading smoothness across a sequence of voicings.

    Args:
        voicings: Ordered list of chord voicings.

    Returns:
        VoiceLeadingReport with motion statistics.
    """
    if len(voicings) < 2:
        return VoiceLeadingReport(
            total_motion=0,
            transition_count=0,
            average_motion=0.0,
            max_single_voice_leap=0,
        )

    total_motion = 0
    max_leap = 0

    for i in range(len(voicings) - 1):
        prev = voicings[i]
        curr = voicings[i + 1]

        motion = voice_distance(prev, curr)
        total_motion += motion

        # Track max single-voice leap
        n_voices = min(prev.voice_count, curr.voice_count)
        for v in range(n_voices):
            leap = abs(curr.pitches[v] - prev.pitches[v])
            if leap > max_leap:
                max_leap = leap

    transitions = len(voicings) - 1
    avg = total_motion / transitions if transitions > 0 else 0.0

    return VoiceLeadingReport(
        total_motion=total_motion,
        transition_count=transitions,
        average_motion=avg,
        max_single_voice_leap=max_leap,
    )
