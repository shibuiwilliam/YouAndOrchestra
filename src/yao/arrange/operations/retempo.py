"""Retempo operation — change composition tempo.

Adjusts tempo and optionally scales note durations to maintain
the musical feel at the new tempo.
"""

from __future__ import annotations

from typing import Any

from yao.arrange.base import ArrangementOperation, Preservable, register_arrangement
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


@register_arrangement("retempo")
class RetempoOperation(ArrangementOperation):
    """Change the tempo of a composition.

    Preserves notes, harmony, and form structure.
    """

    @property
    def preserves(self) -> frozenset[Preservable]:
        """Retempo preserves notes, harmony, and form."""
        return frozenset({Preservable.NOTES, Preservable.HARMONY, Preservable.FORM})

    @property
    def name(self) -> str:
        """Operation name."""
        return "retempo"

    def apply(
        self,
        source: ScoreIR,
        params: dict[str, Any],
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        """Change the tempo.

        Args:
            source: Input ScoreIR.
            params: Must contain "target_bpm" (float). Optional
                "scale_durations" (bool, default False) to proportionally
                adjust note durations.
            provenance: Provenance log for recording.

        Returns:
            ScoreIR with updated tempo.
        """
        target_bpm = float(params.get("target_bpm", source.tempo_bpm))
        scale_durations = bool(params.get("scale_durations", False))

        ratio = source.tempo_bpm / target_bpm if scale_durations and target_bpm > 0 else 1.0
        sections = source.sections

        if scale_durations and abs(ratio - 1.0) > 0.001:
            new_sections: list[Section] = []
            for section in source.sections:
                new_parts: list[Part] = []
                for part in section.parts:
                    new_notes = tuple(
                        Note(
                            pitch=n.pitch,
                            start_beat=n.start_beat * ratio,
                            duration_beats=n.duration_beats * ratio,
                            velocity=n.velocity,
                            instrument=n.instrument,
                        )
                        for n in part.notes
                    )
                    new_parts.append(Part(instrument=part.instrument, notes=new_notes))
                new_sections.append(
                    Section(
                        name=section.name,
                        start_bar=section.start_bar,
                        end_bar=section.end_bar,
                        parts=tuple(new_parts),
                    )
                )
            sections = tuple(new_sections)

        provenance.record(
            source="arrangement",
            layer="arrange",
            operation="retempo",
            rationale=f"Changed tempo from {source.tempo_bpm} to {target_bpm} BPM",
            parameters={"original_bpm": source.tempo_bpm, "target_bpm": target_bpm, "scale_durations": scale_durations},
        )

        return ScoreIR(
            title=source.title,
            tempo_bpm=target_bpm,
            time_signature=source.time_signature,
            key=source.key,
            sections=sections,
        )
