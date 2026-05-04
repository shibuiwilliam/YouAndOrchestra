"""Pin-aware regeneration — targeted regeneration driven by user pins.

Regenerates only the regions affected by pins, preserving everything
else bit-identically. This is the third tier of the feedback system
(after spec-level and section-level regeneration).

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

from yao.feedback.pin import Pin
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog


def _compute_affected_region(
    pin: Pin,
    section: Section,
    time_signature: str,
    padding: int = 1,
) -> tuple[float, float]:
    """Compute the beat range affected by a pin.

    Args:
        pin: The pin to compute the region for.
        section: The section containing the pin.
        time_signature: Time signature (for bar → beat conversion).
        padding: Bars of padding on each side.

    Returns:
        Tuple of (start_beat, end_beat) in absolute beats.
    """
    bar_start, bar_end = pin.affected_bar_range(padding)

    # Convert section-relative bars to absolute bars
    abs_bar_start = section.start_bar + bar_start - 1  # 1-indexed → 0-indexed
    abs_bar_end = min(section.end_bar, section.start_bar + bar_end)

    start_beat = bars_to_beats(abs_bar_start, time_signature)
    end_beat = bars_to_beats(abs_bar_end, time_signature)

    return (start_beat, end_beat)


def _is_note_in_region(
    note: Note,
    start_beat: float,
    end_beat: float,
    instrument: str | None,
) -> bool:
    """Check if a note falls within the affected region.

    Args:
        note: The note to check.
        start_beat: Region start beat.
        end_beat: Region end beat.
        instrument: If set, only match this instrument. None matches all.

    Returns:
        True if the note is in the affected region.
    """
    if instrument and note.instrument != instrument:
        return False
    return start_beat <= note.start_beat < end_beat


def _regenerate_note(note: Note, pin: Pin, seed: int) -> Note:
    """Regenerate a single note based on pin intent.

    This is a simplified regeneration that adjusts the note based
    on the pin's user_intent. In a full implementation, this would
    call a Note Realizer with derived constraints.

    Args:
        note: Original note to regenerate.
        pin: Pin driving the regeneration.
        seed: Random seed for reproducibility.

    Returns:
        Regenerated note.
    """
    import random

    rng = random.Random(seed + hash(note.start_beat))
    velocity = note.velocity
    pitch = note.pitch

    intent = pin.user_intent

    if intent == "soften_dissonance":
        # Move toward consonant intervals, reduce velocity
        velocity = max(1, velocity - 15)
    elif intent == "increase_intensity":
        velocity = min(127, velocity + 12)
    elif intent == "decrease_intensity":
        velocity = max(1, velocity - 12)
    elif intent == "too_loud":
        velocity = max(1, velocity - 20)
    elif intent == "too_soft":
        velocity = min(127, velocity + 20)
    elif intent == "add_variation":
        # Slight pitch variation
        offset = rng.choice([-2, -1, 1, 2])
        pitch = max(0, min(127, pitch + offset))
    elif intent == "simplify":
        # Keep note but reduce ornamentation by normalizing velocity
        velocity = 80
    elif intent == "too_busy":
        # Reduce velocity to thin texture
        velocity = max(1, velocity - 10)
    elif intent == "too_sparse":
        velocity = min(127, velocity + 10)
    # For "change_rhythm", "change_harmony", "change_melody", "unclear":
    # minimal adjustment — these need deeper regeneration

    return Note(
        pitch=pitch,
        start_beat=note.start_beat,
        duration_beats=note.duration_beats,
        velocity=velocity,
        instrument=note.instrument,
    )


def regenerate_with_pins(
    score_ir: ScoreIR,
    pins: list[Pin],
    seed: int = 42,
    padding: int = 1,
) -> tuple[ScoreIR, ProvenanceLog]:
    """Regenerate regions affected by pins, preserving everything else.

    Algorithm:
      1. For each pin, compute affected region (pin bar ± padding)
      2. For each note, check if it's in an affected region
      3. If yes, regenerate based on pin intent
      4. If no, preserve the note exactly
      5. Stitch back into the ScoreIR

    Args:
        score_ir: Previous iteration's ScoreIR.
        pins: List of pins to apply.
        seed: Random seed for reproducibility.
        padding: Bars of padding around each pin.

    Returns:
        Tuple of (regenerated ScoreIR, ProvenanceLog).
    """
    provenance = ProvenanceLog()

    if not pins:
        provenance.record(
            layer="feedback",
            operation="pin_regeneration",
            parameters={"pin_count": 0},
            source="regenerate_with_pins",
            rationale="No pins to apply; returning original score unchanged.",
        )
        return score_ir, provenance

    # Build affected regions per pin
    pin_regions: list[tuple[Pin, str, float, float]] = []
    for pin in pins:
        # Find the section
        section = next(
            (s for s in score_ir.sections if s.name == pin.location.section),
            None,
        )
        if section is None:
            continue
        start_beat, end_beat = _compute_affected_region(pin, section, score_ir.time_signature, padding)
        pin_regions.append((pin, pin.location.section, start_beat, end_beat))

    # Rebuild sections
    new_sections: list[Section] = []
    notes_changed = 0
    notes_preserved = 0

    for section in score_ir.sections:
        # Collect pins for this section
        section_pins = [(p, sb, eb) for p, sec_name, sb, eb in pin_regions if sec_name == section.name]

        if not section_pins:
            # No pins in this section — preserve entirely
            new_sections.append(section)
            for part in section.parts:
                notes_preserved += len(part.notes)
            continue

        new_parts: list[Part] = []
        for part in section.parts:
            new_notes: list[Note] = []
            for note in part.notes:
                regenerated = False
                for pin, start_beat, end_beat in section_pins:
                    if _is_note_in_region(note, start_beat, end_beat, pin.location.instrument):
                        new_notes.append(_regenerate_note(note, pin, seed))
                        notes_changed += 1
                        regenerated = True
                        break
                if not regenerated:
                    new_notes.append(note)
                    notes_preserved += 1

            new_parts.append(
                Part(
                    instrument=part.instrument,
                    notes=tuple(new_notes),
                )
            )

        new_sections.append(
            Section(
                name=section.name,
                start_bar=section.start_bar,
                end_bar=section.end_bar,
                parts=tuple(new_parts),
            )
        )

    result = ScoreIR(
        title=score_ir.title,
        tempo_bpm=score_ir.tempo_bpm,
        time_signature=score_ir.time_signature,
        key=score_ir.key,
        sections=tuple(new_sections),
    )

    for pin, _sec, _sb, _eb in pin_regions:
        provenance.record(
            layer="feedback",
            operation="pin_regeneration",
            parameters={
                "pin_id": pin.id,
                "section": pin.location.section,
                "bar": pin.location.bar,
                "intent": pin.user_intent,
                "notes_changed": notes_changed,
                "notes_preserved": notes_preserved,
            },
            source="regenerate_with_pins",
            rationale=(
                f"Applied pin '{pin.id}' ({pin.user_intent}) at "
                f"{pin.location.section}:bar{pin.location.bar}. "
                f"Changed {notes_changed} notes, preserved {notes_preserved}."
            ),
        )

    return result, provenance
