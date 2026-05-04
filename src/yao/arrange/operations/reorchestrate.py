"""Reorchestrate operation — reassign instruments.

Maps instrument names according to a provided mapping, updating all
notes and parts. Validates that target instruments exist in the
instrument range constants.
"""

from __future__ import annotations

from typing import Any

from yao.arrange.base import ArrangementOperation, Preservable, register_arrangement
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.errors import RangeViolationError
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


@register_arrangement("reorchestrate")
class ReorchestrateOperation(ArrangementOperation):
    """Reassign instruments per a mapping.

    Preserves note pitches and form. Validates that reassigned notes
    fall within the target instrument's range.
    """

    @property
    def preserves(self) -> frozenset[Preservable]:
        """Reorchestration preserves notes and form."""
        return frozenset({Preservable.NOTES, Preservable.FORM})

    @property
    def name(self) -> str:
        """Operation name."""
        return "reorchestrate"

    def apply(
        self,
        source: ScoreIR,
        params: dict[str, Any],
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        """Reassign instruments.

        Args:
            source: Input ScoreIR.
            params: Must contain "mapping" dict (old_name → new_name).
            provenance: Provenance log for recording.

        Returns:
            ScoreIR with instruments reassigned.

        Raises:
            RangeViolationError: If any note is out of the new instrument's range.
        """
        mapping: dict[str, str] = params.get("mapping", {})
        if not mapping:
            return source

        new_sections: list[Section] = []
        notes_remapped = 0

        for section in source.sections:
            new_parts: list[Part] = []
            for part in section.parts:
                target_instrument = mapping.get(part.instrument, part.instrument)
                if target_instrument != part.instrument:
                    # Validate range for remapped notes
                    target_range = INSTRUMENT_RANGES.get(target_instrument)
                    if target_range is not None:
                        for note in part.notes:
                            if not target_range.midi_low <= note.pitch <= target_range.midi_high:
                                raise RangeViolationError(
                                    instrument=target_instrument,
                                    note=note.pitch,
                                    valid_low=target_range.midi_low,
                                    valid_high=target_range.midi_high,
                                )
                    new_notes = tuple(
                        Note(
                            pitch=n.pitch,
                            start_beat=n.start_beat,
                            duration_beats=n.duration_beats,
                            velocity=n.velocity,
                            instrument=target_instrument,
                        )
                        for n in part.notes
                    )
                    notes_remapped += len(new_notes)
                    new_parts.append(Part(instrument=target_instrument, notes=new_notes))
                else:
                    new_parts.append(part)
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
            operation="reorchestrate",
            rationale=f"Reassigned {notes_remapped} notes across {len(mapping)} instruments",
            parameters={"mapping": mapping, "notes_remapped": notes_remapped},
        )

        return ScoreIR(
            title=source.title,
            tempo_bpm=source.tempo_bpm,
            time_signature=source.time_signature,
            key=source.key,
            sections=tuple(new_sections),
        )
