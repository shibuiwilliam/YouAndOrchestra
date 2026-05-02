"""Articulation Realizer — assigns legato, accent, tenuto per note context.

Analyzes each note's position (phrase boundary, strong beat, leap) and
assigns articulation markings as NoteExpression overlays.

Never mutates ScoreIR — writes to PerformanceLayer only.
"""

from __future__ import annotations

from yao.ir.expression import NoteExpression, NoteId, PerformanceLayer
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import bars_to_beats

# Instrument family → default articulation parameters
_FAMILY_DEFAULTS: dict[str, dict[str, float]] = {
    "strings": {"legato_overlap": 0.02, "accent_strength": 0.4},
    "winds": {"legato_overlap": 0.01, "accent_strength": 0.3},
    "keyboard": {"legato_overlap": 0.0, "accent_strength": 0.3},
    "default": {"legato_overlap": 0.0, "accent_strength": 0.2},
}

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


def _get_family(instrument: str) -> str:
    """Get the instrument family for articulation defaults."""
    return _INSTRUMENT_FAMILY.get(instrument, "default")


class ArticulationRealizer:
    """Assigns articulation markings based on musical context.

    Rules:
    - Strong beats (beat 1 in any time signature): accent
    - Phrase boundaries (last note before gap): tenuto (legato_overlap=0)
    - Default: family-specific legato overlap
    - Large leaps (>5 semitones): slight accent
    """

    def realize(self, score: ScoreIR) -> PerformanceLayer:
        """Generate articulation expressions for all notes.

        Args:
            score: The ScoreIR to analyze.

        Returns:
            PerformanceLayer with articulation-only NoteExpressions.
        """
        expressions: dict[NoteId, NoteExpression] = {}
        beats_per_bar = bars_to_beats(1, score.time_signature)

        for section in score.sections:
            for part in section.parts:
                family = _get_family(part.instrument)
                defaults = _FAMILY_DEFAULTS.get(family, _FAMILY_DEFAULTS["default"])
                notes = sorted(part.notes, key=lambda n: (n.start_beat, n.pitch))

                for i, note in enumerate(notes):
                    nid: NoteId = (note.instrument, note.start_beat, note.pitch)

                    legato = defaults["legato_overlap"]
                    accent = 0.0

                    # Strong beat detection (beat 1 of any bar)
                    beat_in_bar = note.start_beat % beats_per_bar
                    if beat_in_bar < 0.01:
                        accent = defaults["accent_strength"]

                    # Leap detection
                    if i > 0:
                        interval = abs(note.pitch - notes[i - 1].pitch)
                        if interval > 5:
                            accent = max(accent, defaults["accent_strength"] * 0.7)

                    # Phrase end: last note or gap > 1 beat before next
                    if i == len(notes) - 1:
                        legato = 0.0  # tenuto-like: no overlap at phrase end
                    elif i < len(notes) - 1:
                        gap = notes[i + 1].start_beat - note.end_beat()
                        if gap > 0.5:
                            legato = 0.0

                    expressions[nid] = NoteExpression(
                        legato_overlap=legato,
                        accent_strength=min(accent, 1.0),
                    )

        return PerformanceLayer(
            note_expressions=expressions,
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )
