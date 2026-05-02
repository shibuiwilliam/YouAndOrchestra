"""MIDI writer — converts ScoreIR to MIDI files via pretty_midi.

This is the only module that imports pretty_midi for writing.
All timing conversions go through yao.ir.timing (CLAUDE.md §7).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pretty_midi

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.midi import DEFAULT_PPQ, GENERAL_MIDI_INSTRUMENTS
from yao.errors import RenderError
from yao.ir.timing import beats_to_seconds

if TYPE_CHECKING:
    from yao.ir.drum import DrumHit
    from yao.ir.score_ir import ScoreIR


def score_ir_to_midi(
    score: ScoreIR,
    ppq: int = DEFAULT_PPQ,
) -> pretty_midi.PrettyMIDI:
    """Convert a ScoreIR to a PrettyMIDI object.

    Args:
        score: The ScoreIR to convert.
        ppq: Pulses per quarter note.

    Returns:
        A PrettyMIDI object ready for writing.

    Raises:
        RenderError: If conversion fails.
    """
    try:
        midi = pretty_midi.PrettyMIDI(
            initial_tempo=score.tempo_bpm,
            resolution=ppq,
        )
    except Exception as e:
        raise RenderError(f"Failed to create PrettyMIDI: {e}") from e

    # Collect all notes per instrument across sections
    instrument_notes: dict[str, list[pretty_midi.Note]] = {}

    for section in score.sections:
        for part in section.parts:
            if part.instrument not in instrument_notes:
                instrument_notes[part.instrument] = []

            for note in part.notes:
                start_time = beats_to_seconds(note.start_beat, score.tempo_bpm)
                end_time = beats_to_seconds(note.end_beat(), score.tempo_bpm)

                midi_note = pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=start_time,
                    end=end_time,
                )
                instrument_notes[part.instrument].append(midi_note)

    # Create MIDI instruments and add notes
    for instr_name, notes in instrument_notes.items():
        program = _resolve_program(instr_name)
        is_drum = instr_name == "drums"

        midi_instrument = pretty_midi.Instrument(
            program=program,
            is_drum=is_drum,
            name=instr_name,
        )
        midi_instrument.notes = sorted(notes, key=lambda n: n.start)
        midi.instruments.append(midi_instrument)

    return midi


def add_drum_hits_to_midi(
    midi: pretty_midi.PrettyMIDI,
    drum_hits: list[DrumHit],
    tempo_bpm: float,
) -> None:
    """Add drum hits to an existing PrettyMIDI object.

    Creates a dedicated drum instrument (is_drum=True, GM Channel 10)
    and appends all hits.

    Args:
        midi: The PrettyMIDI object to modify.
        drum_hits: List of DrumHit objects.
        tempo_bpm: Tempo for beat-to-time conversion.
    """
    if not drum_hits:
        return

    drum_inst = pretty_midi.Instrument(program=0, is_drum=True, name="drums")

    for hit in drum_hits:
        start = beats_to_seconds(hit.time_beats, tempo_bpm) + hit.microtiming_ms / 1000.0
        end = beats_to_seconds(hit.time_beats + hit.duration_beats, tempo_bpm)
        start = max(0.0, start)  # microtiming can push slightly negative

        drum_inst.notes.append(
            pretty_midi.Note(
                velocity=hit.velocity,
                pitch=hit.to_midi_pitch(),
                start=start,
                end=end,
            )
        )

    drum_inst.notes.sort(key=lambda n: n.start)
    midi.instruments.append(drum_inst)


def write_midi(
    score: ScoreIR,
    output_path: Path,
    ppq: int = DEFAULT_PPQ,
    drum_hits: list[DrumHit] | None = None,
) -> Path:
    """Convert a ScoreIR and write it to a MIDI file.

    Args:
        score: The ScoreIR to write.
        output_path: Path for the output .mid file.
        ppq: Pulses per quarter note.
        drum_hits: Optional drum hits to include as a drum track.

    Returns:
        The path to the written MIDI file.

    Raises:
        RenderError: If writing fails.
    """
    midi = score_ir_to_midi(score, ppq)

    if drum_hits:
        add_drum_hits_to_midi(midi, drum_hits, score.tempo_bpm)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        midi.write(str(output_path))
    except Exception as e:
        raise RenderError(f"Failed to write MIDI to {output_path}: {e}") from e

    return output_path


def _resolve_program(instrument_name: str) -> int:
    """Resolve an instrument name to a General MIDI program number.

    Args:
        instrument_name: Canonical instrument name.

    Returns:
        General MIDI program number.
    """
    if instrument_name in GENERAL_MIDI_INSTRUMENTS:
        return GENERAL_MIDI_INSTRUMENTS[instrument_name]

    # Try looking up via InstrumentRange
    inst_range = INSTRUMENT_RANGES.get(instrument_name)
    if inst_range is not None:
        return inst_range.program

    # Default to piano
    return 0
