"""Regroove operation — replace rhythm with target genre's feel.

Adjusts note timing (swing, syncopation) and durations to match
a target groove style while preserving melody, harmony, and form.
"""

from __future__ import annotations

import random
from typing import Any

from yao.arrange.base import ArrangementOperation, Preservable, register_arrangement
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog

# Genre-specific groove parameters
_GROOVE_PRESETS: dict[str, dict[str, float]] = {
    "jazz": {"swing": 0.6, "offset_range": 0.03},
    "lofi_hiphop": {"swing": 0.35, "offset_range": 0.05},
    "rock": {"swing": 0.0, "offset_range": 0.01},
    "funk": {"swing": 0.2, "offset_range": 0.04},
    "bossa_nova": {"swing": 0.15, "offset_range": 0.02},
}


@register_arrangement("regroove")
class RegrooveOperation(ArrangementOperation):
    """Replace rhythm feel with a target genre's groove.

    Applies swing and micro-timing offsets to simulate a different
    rhythmic feel. Preserves melody pitches, harmony, and form.
    """

    @property
    def preserves(self) -> frozenset[Preservable]:
        """Regroove preserves melody, harmony, and form."""
        return frozenset({Preservable.MELODY, Preservable.HARMONY, Preservable.FORM})

    @property
    def name(self) -> str:
        """Operation name."""
        return "regroove"

    def apply(
        self,
        source: ScoreIR,
        params: dict[str, Any],
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        """Apply groove transformation.

        Args:
            source: Input ScoreIR.
            params: "target_genre" (str), "swing" (float, optional override),
                "seed" (int, optional).
            provenance: Provenance log for recording.

        Returns:
            ScoreIR with adjusted timing.
        """
        target_genre = str(params.get("target_genre", "jazz"))
        seed = int(params.get("seed", 42))
        rng = random.Random(seed)

        preset = _GROOVE_PRESETS.get(target_genre, {"swing": 0.0, "offset_range": 0.02})
        swing = float(params.get("swing", preset["swing"]))
        offset_range = preset["offset_range"]

        notes_adjusted = 0
        new_sections: list[Section] = []

        for section in source.sections:
            new_parts: list[Part] = []
            for part in section.parts:
                new_notes: list[Note] = []
                for note in part.notes:
                    new_start = _apply_swing(note.start_beat, swing)
                    # Add micro-timing humanization
                    new_start += rng.uniform(-offset_range, offset_range)
                    new_start = max(0.0, new_start)

                    new_notes.append(
                        Note(
                            pitch=note.pitch,
                            start_beat=new_start,
                            duration_beats=note.duration_beats,
                            velocity=note.velocity,
                            instrument=note.instrument,
                        )
                    )
                    notes_adjusted += 1
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
            operation="regroove",
            rationale=f"Applied {target_genre} groove (swing={swing:.2f}) to {notes_adjusted} notes",
            parameters={"target_genre": target_genre, "swing": swing, "seed": seed, "notes_adjusted": notes_adjusted},
        )

        return ScoreIR(
            title=source.title,
            tempo_bpm=source.tempo_bpm,
            time_signature=source.time_signature,
            key=source.key,
            sections=tuple(new_sections),
        )


def _apply_swing(beat: float, swing_amount: float) -> float:
    """Apply swing to a beat position.

    Swing delays off-beat eighth notes. A swing_amount of 0.0 is
    straight time; 0.67 is full triplet swing.

    Args:
        beat: Original beat position.
        swing_amount: Swing factor (0.0-1.0).

    Returns:
        Adjusted beat position.
    """
    if swing_amount < 0.01:
        return beat

    # Determine position within the beat
    beat_frac = beat % 1.0
    # Off-beat eighth notes (around 0.5 in the beat)
    if 0.4 < beat_frac < 0.6:
        shift = swing_amount * 0.167  # max shift = 1/6 beat (triplet feel)
        return beat + shift

    return beat
