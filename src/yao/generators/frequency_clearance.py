"""Frequency Clearance — avoid spectral collision between voices.

Computes a symbolic frequency occupancy model from the primary voice's
notes and adjusts accompaniment notes to reduce overlap.

Uses fundamental frequency approximation (MIDI note → Hz) rather than
audio rendering, allowing clearance before audio is produced.

Never silences accompaniment — always finds an alternative (octave
displacement or rhythmic offset).

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

from yao.ir.conversation import ConversationPlan
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


def midi_to_hz(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz.

    Uses standard A440 tuning.

    Args:
        midi_note: MIDI note number (0-127).

    Returns:
        Frequency in Hz.
    """
    return float(440.0 * (2.0 ** ((midi_note - 69) / 12.0)))


def notes_overlap_in_time(a: Note, b: Note) -> bool:
    """Check if two notes overlap in time.

    Args:
        a: First note.
        b: Second note.

    Returns:
        True if the notes overlap temporally.
    """
    a_end = a.start_beat + a.duration_beats
    b_end = b.start_beat + b.duration_beats
    return a.start_beat < b_end and b.start_beat < a_end


def frequency_collision(primary: Note, accompaniment: Note, bandwidth_semitones: int = 3) -> bool:
    """Check if an accompaniment note collides spectrally with a primary note.

    Collision is defined as being within bandwidth_semitones of the
    primary note's pitch AND overlapping in time.

    Args:
        primary: Primary voice note.
        accompaniment: Accompaniment note to check.
        bandwidth_semitones: Half-bandwidth for collision detection.

    Returns:
        True if there is a frequency collision.
    """
    if not notes_overlap_in_time(primary, accompaniment):
        return False
    return abs(accompaniment.pitch - primary.pitch) <= bandwidth_semitones


def apply_frequency_clearance(
    score: ScoreIR,
    conversation: ConversationPlan,
    bandwidth_semitones: int = 3,
) -> tuple[ScoreIR, ProvenanceLog]:
    """Apply frequency clearance to reduce spectral collisions.

    For each section, identifies the primary voice and checks
    accompaniment notes for collisions. Colliding notes are displaced
    by an octave (up or down, whichever keeps them in range).

    Args:
        score: The ScoreIR to process.
        conversation: ConversationPlan with primary voice assignments.
        bandwidth_semitones: Collision detection bandwidth.

    Returns:
        Tuple of (modified ScoreIR, ProvenanceLog).
    """
    provenance = ProvenanceLog()
    total_collisions = 0
    total_resolved = 0
    new_sections: list[Section] = []

    for section in score.sections:
        primary_instrument = conversation.primary_voice_for_section(section.name)
        if primary_instrument is None:
            new_sections.append(section)
            continue

        # Gather primary voice notes
        primary_notes: list[Note] = []
        for part in section.parts:
            if part.instrument == primary_instrument:
                primary_notes.extend(part.notes)

        if not primary_notes:
            new_sections.append(section)
            continue

        # Process accompaniment parts
        updated_parts: list[Part] = []
        for part in section.parts:
            if part.instrument == primary_instrument:
                updated_parts.append(part)
                continue

            # Check each accompaniment note for collision
            new_notes: list[Note] = []
            for acc_note in part.notes:
                collides = any(frequency_collision(pn, acc_note, bandwidth_semitones) for pn in primary_notes)

                if collides:
                    total_collisions += 1
                    resolved = _displace_note(acc_note)
                    if resolved is not None:
                        new_notes.append(resolved)
                        total_resolved += 1
                    else:
                        # Cannot displace — keep original (never silence)
                        new_notes.append(acc_note)
                else:
                    new_notes.append(acc_note)

            updated_parts.append(Part(instrument=part.instrument, notes=tuple(new_notes)))

        new_sections.append(
            Section(
                name=section.name,
                start_bar=section.start_bar,
                end_bar=section.end_bar,
                parts=tuple(updated_parts),
            )
        )

    provenance.record(
        layer="generator",
        operation="frequency_clearance",
        parameters={
            "bandwidth_semitones": bandwidth_semitones,
            "total_collisions": total_collisions,
            "total_resolved": total_resolved,
        },
        source="apply_frequency_clearance",
        rationale=(
            f"Detected {total_collisions} frequency collisions, resolved {total_resolved} via octave displacement."
        ),
    )

    result = ScoreIR(
        title=score.title,
        tempo_bpm=score.tempo_bpm,
        time_signature=score.time_signature,
        key=score.key,
        sections=tuple(new_sections),
    )
    return result, provenance


def _displace_note(note: Note) -> Note | None:
    """Displace a note by an octave to avoid collision.

    Tries octave down first, then octave up. Returns None if neither
    keeps the note in valid MIDI range (0-127).

    Args:
        note: Note to displace.

    Returns:
        Displaced note, or None if no valid displacement exists.
    """
    # Try octave down
    if note.pitch - 12 >= 0:
        return Note(
            pitch=note.pitch - 12,
            start_beat=note.start_beat,
            duration_beats=note.duration_beats,
            velocity=note.velocity,
            instrument=note.instrument,
        )
    # Try octave up
    if note.pitch + 12 <= 127:
        return Note(
            pitch=note.pitch + 12,
            start_beat=note.start_beat,
            duration_beats=note.duration_beats,
            velocity=note.velocity,
            instrument=note.instrument,
        )
    return None
