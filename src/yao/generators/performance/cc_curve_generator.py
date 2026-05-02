"""CC Curve Generator — instrument-specific CC automation.

Generates CC curves for:
- Strings: CC1 (vibrato depth) — gradual onset on long notes
- Winds: CC11 (expression) — phrase shaping
- Keyboard: CC64 (sustain pedal) — pedal changes on harmonic boundaries

Never mutates ScoreIR — writes to PerformanceLayer only.
"""

from __future__ import annotations

from yao.ir.expression import NoteExpression, NoteId, PedalCurve, PerformanceLayer
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import bars_to_beats
from yao.types import Beat

# Reuse family mapping from articulation_realizer
_INSTRUMENT_FAMILY: dict[str, str] = {
    "violin": "strings",
    "viola": "strings",
    "cello": "strings",
    "contrabass": "strings",
    "strings_ensemble": "strings",
    "flute": "winds",
    "oboe": "winds",
    "clarinet": "winds",
    "bassoon": "winds",
    "french_horn": "winds",
    "trumpet": "winds",
    "trombone": "winds",
    "alto_saxophone": "winds",
    "tenor_saxophone": "winds",
    "piano": "keyboard",
    "harpsichord": "keyboard",
    "organ": "keyboard",
    "celesta": "keyboard",
    "clavinet": "keyboard",
}


class CCCurveGenerator:
    """Generates CC automation curves per instrument family."""

    def generate(self, score: ScoreIR) -> PerformanceLayer:
        """Generate CC curves for all instruments.

        Args:
            score: The ScoreIR to process.

        Returns:
            PerformanceLayer with cc_curves and pedal_curves.
        """
        expressions: dict[NoteId, NoteExpression] = {}
        pedal_curves: list[PedalCurve] = []

        for section in score.sections:
            for part in section.parts:
                family = _INSTRUMENT_FAMILY.get(part.instrument, "default")

                if family == "strings":
                    self._add_vibrato(part.instrument, part.notes, expressions)
                elif family == "winds":
                    self._add_expression_cc(part.instrument, part.notes, expressions)
                elif family == "keyboard":
                    pedal = self._generate_pedal(
                        part.instrument,
                        section.start_bar,
                        section.end_bar,
                        score.time_signature,
                    )
                    if pedal is not None:
                        pedal_curves.append(pedal)

        return PerformanceLayer(
            note_expressions=expressions,
            section_rubato={},
            breath_marks=(),
            pedal_curves=tuple(pedal_curves),
        )

    @staticmethod
    def _add_vibrato(
        instrument: str,
        notes: tuple[Note, ...],
        expressions: dict[NoteId, NoteExpression],
    ) -> None:
        """Add CC1 vibrato curves for string instruments."""
        for note in notes:
            nid: NoteId = (note.instrument, note.start_beat, note.pitch)
            dur = note.duration_beats

            cc_points: tuple[tuple[float, int], ...]
            if dur >= 1.0:
                # Gradual vibrato onset: 0 at start, peak at 60% of duration
                onset = dur * 0.2
                peak = dur * 0.6
                cc_points = (
                    (0.0, 0),
                    (onset, 30),
                    (peak, 64),
                    (dur * 0.9, 50),
                    (dur, 0),
                )
            else:
                # Short notes: minimal vibrato
                cc_points = ((0.0, 0), (dur, 20))

            expressions[nid] = NoteExpression(
                cc_curves={1: cc_points},
            )

    @staticmethod
    def _add_expression_cc(
        instrument: str,
        notes: tuple[Note, ...],
        expressions: dict[NoteId, NoteExpression],
    ) -> None:
        """Add CC11 expression curves for wind instruments."""
        for note in notes:
            nid: NoteId = (note.instrument, note.start_beat, note.pitch)
            dur = note.duration_beats

            # Expression: start strong, slight dip, taper at end
            cc_points = (
                (0.0, 100),
                (dur * 0.3, 90),
                (dur * 0.7, 95),
                (dur * 0.95, 60),
                (dur, 40),
            )

            expressions[nid] = NoteExpression(
                cc_curves={11: cc_points},
            )

    @staticmethod
    def _generate_pedal(
        instrument: str,
        start_bar: int,
        end_bar: int,
        time_signature: str,
    ) -> PedalCurve | None:
        """Generate CC64 sustain pedal curve for keyboard instruments."""
        beats_per_bar = bars_to_beats(1, time_signature)
        events: list[tuple[Beat, int]] = []

        for bar in range(start_bar, end_bar):
            bar_start = bars_to_beats(bar, time_signature)
            # Pedal down at start of bar, up briefly before next bar
            events.append((bar_start, 127))
            events.append((bar_start + beats_per_bar - 0.1, 0))
            events.append((bar_start + beats_per_bar, 127))

        if not events:
            return None

        return PedalCurve(
            cc_number=64,
            instrument=instrument,
            events=tuple(events),
        )
