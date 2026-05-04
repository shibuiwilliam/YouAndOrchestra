"""Reharmonize operation — substitute chords while preserving melody.

Applies chord substitution patterns: secondary dominants, tritone subs,
modal interchange. Operates on note pitches that are likely chord tones
(non-melody notes in harmony/pad parts).
"""

from __future__ import annotations

import random
from typing import Any

from yao.arrange.base import ArrangementOperation, Preservable, register_arrangement
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


@register_arrangement("reharmonize")
class ReharmonizeOperation(ArrangementOperation):
    """Replace chord voicings while preserving melody and form.

    MVP: shifts non-melody chord tones by chromatic intervals to simulate
    chord substitution. The level parameter controls how many chord tones
    are affected (0.0 = no change, 1.0 = all chords substituted).
    """

    @property
    def preserves(self) -> frozenset[Preservable]:
        """Reharmonization preserves melody and form."""
        return frozenset({Preservable.MELODY, Preservable.FORM})

    @property
    def name(self) -> str:
        """Operation name."""
        return "reharmonize"

    def apply(
        self,
        source: ScoreIR,
        params: dict[str, Any],
        provenance: ProvenanceLog,
    ) -> ScoreIR:
        """Reharmonize the composition.

        Args:
            source: Input ScoreIR.
            params: "level" (0.0-1.0), "seed" (int, optional),
                "style" (str, optional — e.g. "jazz_substitution").
            provenance: Provenance log for recording.

        Returns:
            Reharmonized ScoreIR.
        """
        level = float(params.get("level", 0.5))
        seed = int(params.get("seed", 42))
        style = str(params.get("style", "chromatic_substitution"))
        rng = random.Random(seed)

        chords_modified = 0
        new_sections: list[Section] = []

        for section in source.sections:
            new_parts: list[Part] = []
            for part in section.parts:
                # Only modify non-melody parts (harmony, pad, bass roles)
                if _is_melody_part(part):
                    new_parts.append(part)
                    continue

                new_notes: list[Note] = []
                for note in part.notes:
                    if rng.random() < level:
                        shift = _pick_substitution_shift(style, rng)
                        new_pitch = max(0, min(127, note.pitch + shift))
                        new_notes.append(
                            Note(
                                pitch=new_pitch,
                                start_beat=note.start_beat,
                                duration_beats=note.duration_beats,
                                velocity=note.velocity,
                                instrument=note.instrument,
                            )
                        )
                        chords_modified += 1
                    else:
                        new_notes.append(note)
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
            operation="reharmonize",
            rationale=f"Reharmonized {chords_modified} chord tones (style={style}, level={level})",
            parameters={"level": level, "seed": seed, "style": style, "chords_modified": chords_modified},
        )

        return ScoreIR(
            title=source.title,
            tempo_bpm=source.tempo_bpm,
            time_signature=source.time_signature,
            key=source.key,
            sections=tuple(new_sections),
        )


def _is_melody_part(part: Part) -> bool:
    """Heuristic: melody parts tend to have the highest average pitch.

    MVP simplification: a part with "melody" in the instrument name or
    having the fewest simultaneous notes is likely melody.
    """
    # Simple name heuristic
    name_lower = part.instrument.lower()
    return any(kw in name_lower for kw in ("melody", "lead", "vocal", "flute", "violin"))


def _pick_substitution_shift(style: str, rng: random.Random) -> int:
    """Pick a chromatic interval for chord substitution.

    Args:
        style: Substitution style name.
        rng: Random generator.

    Returns:
        Semitone shift value.
    """
    if "jazz" in style:
        # Jazz: tritone sub (+6), secondary dominant (+7), minor sub (-3)
        return rng.choice([6, 7, -3, -5, 3])
    # Default: chromatic neighboring tones
    return rng.choice([-2, -1, 1, 2, 3, -3])
