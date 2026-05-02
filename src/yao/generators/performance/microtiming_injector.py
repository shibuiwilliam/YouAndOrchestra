"""Microtiming Injector — genre-specific timing offsets.

Applies subtle timing deviations to notes based on genre conventions:
- Jazz: laid-back feel, beats 2/4 delayed
- Classical: slight rubato tendencies
- Default: minimal deviation

Never mutates ScoreIR — writes to PerformanceLayer only.
"""

from __future__ import annotations

from yao.ir.expression import NoteExpression, NoteId, PerformanceLayer
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import bars_to_beats

# Genre → microtiming profile
_PROFILES: dict[str, dict[str, float]] = {
    "jazz": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": 12.0,
        "offbeat_ms": 8.0,
    },
    "jazz_ballad": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": 18.0,
        "offbeat_ms": 10.0,
    },
    "jazz_swing": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": 15.0,
        "offbeat_ms": 8.0,
    },
    "blues": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": 8.0,
        "offbeat_ms": 5.0,
    },
    "funk": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": -3.0,  # slightly ahead (pushing)
        "offbeat_ms": -2.0,
    },
    "classical": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": 3.0,
        "offbeat_ms": 2.0,
    },
    "default": {
        "beat_1_3_ms": 0.0,
        "beat_2_4_ms": 0.0,
        "offbeat_ms": 0.0,
    },
}


class MicrotimingInjector:
    """Injects genre-appropriate microtiming offsets.

    Analyzes each note's beat position and applies timing deviations
    based on the genre's characteristic feel.
    """

    def inject(self, score: ScoreIR, genre: str = "default") -> PerformanceLayer:
        """Apply microtiming to all notes.

        Args:
            score: The ScoreIR to process.
            genre: Genre name for profile selection.

        Returns:
            PerformanceLayer with micro_timing_ms values.
        """
        profile = _PROFILES.get(genre, _PROFILES["default"])
        expressions: dict[NoteId, NoteExpression] = {}
        beats_per_bar = bars_to_beats(1, score.time_signature)

        for section in score.sections:
            for part in section.parts:
                for note in part.notes:
                    nid: NoteId = (note.instrument, note.start_beat, note.pitch)
                    beat_in_bar = note.start_beat % beats_per_bar

                    # Determine beat position
                    timing_ms = profile["offbeat_ms"]  # default: offbeat
                    if abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01:
                        timing_ms = profile["beat_1_3_ms"]  # beats 1, 3
                    elif abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01:
                        timing_ms = profile["beat_2_4_ms"]  # beats 2, 4

                    expressions[nid] = NoteExpression(micro_timing_ms=timing_ms)

        return PerformanceLayer(
            note_expressions=expressions,
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )
