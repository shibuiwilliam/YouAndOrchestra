"""Reactive Fills — short fills after melodic phrase endings.

Detects silence gaps (≥ minimum_silence_beats) at the end of melodic
phrases and inserts short idiomatic fills from fill_capable instruments
as specified in the ConversationPlan.

Fills are always ≤ 1 bar and stay within instrument range.

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.conversation import ConversationPlan
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog


@dataclass(frozen=True)
class FillOpportunity:
    """A detected opportunity for a reactive fill.

    Attributes:
        section_id: Section where the gap occurs.
        start_beat: Beat where silence begins.
        duration_beats: Length of silence available.
        preceding_pitch: Last pitch before the gap (for tonal context).
    """

    section_id: str
    start_beat: float
    duration_beats: float
    preceding_pitch: int


def detect_fill_opportunities(
    score: ScoreIR,
    conversation: ConversationPlan,
    minimum_silence_beats: float = 1.0,
) -> list[FillOpportunity]:
    """Detect gaps after melodic phrase endings suitable for fills.

    Scans the primary voice instrument in each section for silences
    of at least minimum_silence_beats after note activity.

    Args:
        score: The current ScoreIR.
        conversation: The ConversationPlan with voice focus info.
        minimum_silence_beats: Minimum gap size to qualify.

    Returns:
        List of FillOpportunity objects, sorted by start_beat.
    """
    opportunities: list[FillOpportunity] = []

    for section in score.sections:
        primary = conversation.primary_voice_for_section(section.name)
        if primary is None:
            continue

        # Find the primary voice's notes in this section
        primary_notes: list[Note] = []
        for part in section.parts:
            if part.instrument == primary:
                primary_notes.extend(part.notes)

        if not primary_notes:
            continue

        # Sort by start_beat
        primary_notes.sort(key=lambda n: n.start_beat)

        # Detect gaps between consecutive notes
        for i in range(len(primary_notes) - 1):
            current_end = primary_notes[i].start_beat + primary_notes[i].duration_beats
            next_start = primary_notes[i + 1].start_beat
            gap = next_start - current_end

            if gap >= minimum_silence_beats:
                opportunities.append(
                    FillOpportunity(
                        section_id=section.name,
                        start_beat=current_end,
                        duration_beats=min(gap, 4.0),  # Cap at 1 bar (4/4)
                        preceding_pitch=primary_notes[i].pitch,
                    )
                )

        # Check gap after last note to section end
        if primary_notes:
            last_end = primary_notes[-1].start_beat + primary_notes[-1].duration_beats
            section_end_beat = (section.start_bar + section.end_bar - section.start_bar) * 4.0
            gap = section_end_beat - last_end
            if gap >= minimum_silence_beats:
                opportunities.append(
                    FillOpportunity(
                        section_id=section.name,
                        start_beat=last_end,
                        duration_beats=min(gap, 4.0),
                        preceding_pitch=primary_notes[-1].pitch,
                    )
                )

    return sorted(opportunities, key=lambda o: o.start_beat)


def generate_reactive_fills(
    score: ScoreIR,
    conversation: ConversationPlan,
    fill_instruments: list[str] | None = None,
    minimum_silence_beats: float = 1.0,
    seed: int = 42,
) -> tuple[ScoreIR, ProvenanceLog]:
    """Insert reactive fills into gaps after melodic phrases.

    Args:
        score: The current ScoreIR to augment.
        conversation: ConversationPlan with voice focus.
        fill_instruments: Instruments allowed to fill. If None, uses drums.
        minimum_silence_beats: Minimum gap to qualify.
        seed: Random seed for fill generation.

    Returns:
        Tuple of (modified ScoreIR, ProvenanceLog).
    """
    provenance = ProvenanceLog()
    rng = random.Random(seed)

    opportunities = detect_fill_opportunities(score, conversation, minimum_silence_beats)

    if not opportunities:
        provenance.record(
            layer="generator",
            operation="reactive_fills",
            parameters={"n_opportunities": 0, "n_fills_added": 0},
            source="generate_reactive_fills",
            rationale="No fill opportunities detected.",
        )
        return score, provenance

    # Determine fill instruments
    if fill_instruments is None:
        fill_instruments = ["drums"]

    fills_added = 0
    new_sections: list[Section] = []

    for section in score.sections:
        section_opps = [o for o in opportunities if o.section_id == section.name]
        if not section_opps or not fill_instruments:
            new_sections.append(section)
            continue

        # Generate fills for this section
        fill_notes: list[Note] = []
        for opp in section_opps:
            instrument = rng.choice(fill_instruments)
            fill = _generate_single_fill(opp, instrument, rng)
            fill_notes.extend(fill)
            fills_added += 1

        if fill_notes:
            # Add fill notes as a new part or append to existing fill instrument
            fill_instrument = fill_notes[0].instrument
            existing_parts = list(section.parts)

            # Find or create part for fill instrument
            found = False
            updated_parts: list[Part] = []
            for part in existing_parts:
                if part.instrument == fill_instrument:
                    merged_notes = tuple(list(part.notes) + fill_notes)
                    updated_parts.append(Part(instrument=part.instrument, notes=merged_notes))
                    found = True
                else:
                    updated_parts.append(part)

            if not found:
                updated_parts.append(Part(instrument=fill_instrument, notes=tuple(fill_notes)))

            new_sections.append(
                Section(
                    name=section.name,
                    start_bar=section.start_bar,
                    end_bar=section.end_bar,
                    parts=tuple(updated_parts),
                )
            )
        else:
            new_sections.append(section)

    provenance.record(
        layer="generator",
        operation="reactive_fills",
        parameters={
            "n_opportunities": len(opportunities),
            "n_fills_added": fills_added,
            "fill_instruments": fill_instruments,
        },
        source="generate_reactive_fills",
        rationale=f"Inserted {fills_added} reactive fills at phrase endings.",
    )

    result = ScoreIR(
        title=score.title,
        tempo_bpm=score.tempo_bpm,
        time_signature=score.time_signature,
        key=score.key,
        sections=tuple(new_sections),
    )
    return result, provenance


def _generate_single_fill(
    opportunity: FillOpportunity,
    instrument: str,
    rng: random.Random,
) -> list[Note]:
    """Generate a short fill for a single opportunity.

    Fills are 2-4 notes, stay within instrument range, and
    are rhythmically simple (eighth or quarter notes).

    Args:
        opportunity: The fill opportunity.
        instrument: Fill instrument name.
        rng: Random number generator.

    Returns:
        List of fill notes.
    """
    # Get instrument range
    inst_range = INSTRUMENT_RANGES.get(instrument)
    if inst_range is None:
        # Default to a safe range around the preceding pitch
        low = max(40, opportunity.preceding_pitch - 12)
        high = min(88, opportunity.preceding_pitch + 12)
    else:
        low = inst_range.midi_low
        high = inst_range.midi_high

    # Constrain around preceding pitch for tonal coherence
    center = max(low, min(high, opportunity.preceding_pitch))
    fill_low = max(low, center - 7)
    fill_high = min(high, center + 7)

    # Determine number of notes (2-4, fitting within available time)
    max_notes = min(4, int(opportunity.duration_beats / 0.25))
    n_notes = max(2, min(max_notes, rng.randint(2, 4)))

    # Simple rhythmic pattern
    note_duration = min(0.5, opportunity.duration_beats / n_notes)

    notes: list[Note] = []
    current_beat = opportunity.start_beat
    for _ in range(n_notes):
        if current_beat + note_duration > opportunity.start_beat + opportunity.duration_beats:
            break
        pitch = rng.randint(fill_low, fill_high)
        velocity = rng.randint(50, 80)  # Fills are quieter than melody
        notes.append(
            Note(
                pitch=pitch,
                start_beat=current_beat,
                duration_beats=note_duration,
                velocity=velocity,
                instrument=instrument,
            )
        )
        current_beat += note_duration

    return notes
