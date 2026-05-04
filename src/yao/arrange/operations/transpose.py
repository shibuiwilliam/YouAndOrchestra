"""Transpose operation — shift all notes by semitones.

Respects instrument ranges: raises RangeViolationError if any transposed
note falls outside the playable range.
"""

from __future__ import annotations

from typing import Any

from yao.arrange.base import ArrangementOperation, Preservable, register_arrangement
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.errors import RangeViolationError
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


@register_arrangement("transpose")
class TransposeOperation(ArrangementOperation):
    """Transpose all notes by a number of semitones.

    Preserves intervals, rhythm, and form. Raises RangeViolationError
    if any note falls outside its instrument's playable range.
    """

    @property
    def preserves(self) -> frozenset[Preservable]:
        """Transposition preserves intervals, rhythm, and form."""
        return frozenset({Preservable.INTERVALS, Preservable.RHYTHM, Preservable.FORM})

    @property
    def name(self) -> str:
        """Operation name."""
        return "transpose"

    def apply(
        self,
        source: ScoreIR,
        params: dict[str, Any],
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        """Transpose the entire score by semitones.

        Args:
            source: Input ScoreIR.
            params: Must contain "semitones" (int).
            provenance: Provenance log for recording.

        Returns:
            Transposed ScoreIR.

        Raises:
            RangeViolationError: If any note goes out of range.
        """
        semitones: int = int(params.get("semitones", 0))
        if semitones == 0:
            return source

        new_sections: list[Section] = []
        for section in source.sections:
            new_parts: list[Part] = []
            for part in section.parts:
                new_notes: list[Note] = []
                for note in part.notes:
                    new_pitch = note.pitch + semitones
                    # Range check
                    inst_range = INSTRUMENT_RANGES.get(part.instrument)
                    if inst_range is not None and not inst_range.midi_low <= new_pitch <= inst_range.midi_high:
                        raise RangeViolationError(
                            instrument=part.instrument,
                            note=new_pitch,
                            valid_low=inst_range.midi_low,
                            valid_high=inst_range.midi_high,
                        )
                    new_notes.append(
                        Note(
                            pitch=new_pitch,
                            start_beat=note.start_beat,
                            duration_beats=note.duration_beats,
                            velocity=note.velocity,
                            instrument=note.instrument,
                        )
                    )
                new_parts.append(Part(instrument=part.instrument, notes=tuple(new_notes)))
            new_sections.append(
                Section(
                    name=section.name,
                    start_bar=section.start_bar,
                    end_bar=section.end_bar,
                    parts=tuple(new_parts),
                )
            )

        provenance.record(
            source="arrangement",
            layer="arrange",
            operation="transpose",
            rationale=f"Transposed by {semitones} semitones",
            parameters={"semitones": semitones},
        )

        return ScoreIR(
            title=source.title,
            tempo_bpm=source.tempo_bpm,
            time_signature=source.time_signature,
            key=source.key,
            sections=tuple(new_sections),
        )
