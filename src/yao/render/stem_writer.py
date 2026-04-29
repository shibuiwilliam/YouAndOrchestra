"""Stem writer — write per-instrument MIDI files.

CLAUDE.md §12: stems are written as <instrument>.mid in a stems/ subdirectory.
Each stem contains only the notes for a single instrument.
"""

from __future__ import annotations

from pathlib import Path

import pretty_midi

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.midi import DEFAULT_PPQ, GENERAL_MIDI_INSTRUMENTS
from yao.errors import RenderError
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import beats_to_seconds


def write_stems(
    score: ScoreIR,
    output_dir: Path,
    ppq: int = DEFAULT_PPQ,
) -> dict[str, Path]:
    """Write per-instrument MIDI stem files.

    Creates a stems/ subdirectory and writes one .mid file per instrument.

    Args:
        score: The ScoreIR to split into stems.
        output_dir: Base output directory (stems/ is created inside it).
        ppq: Pulses per quarter note.

    Returns:
        Mapping of instrument name to written file path.

    Raises:
        RenderError: If writing fails.
    """
    stems_dir = output_dir / "stems"
    stems_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    for instrument in score.instruments():
        notes = score.part_for_instrument(instrument)
        if not notes:
            continue

        midi = pretty_midi.PrettyMIDI(
            initial_tempo=score.tempo_bpm,
            resolution=ppq,
        )

        program = _resolve_program(instrument)
        is_drum = instrument == "drums"

        midi_instrument = pretty_midi.Instrument(
            program=program,
            is_drum=is_drum,
            name=instrument,
        )

        for note in notes:
            start_time = beats_to_seconds(note.start_beat, score.tempo_bpm)
            end_time = beats_to_seconds(note.end_beat(), score.tempo_bpm)
            midi_instrument.notes.append(
                pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=start_time,
                    end=end_time,
                )
            )

        midi_instrument.notes.sort(key=lambda n: n.start)
        midi.instruments.append(midi_instrument)

        stem_path = stems_dir / f"{instrument}.mid"
        try:
            midi.write(str(stem_path))
        except Exception as e:
            raise RenderError(f"Failed to write stem for {instrument}: {e}") from e

        written[instrument] = stem_path

    return written


def _resolve_program(instrument_name: str) -> int:
    """Resolve an instrument name to a General MIDI program number."""
    if instrument_name in GENERAL_MIDI_INSTRUMENTS:
        return GENERAL_MIDI_INSTRUMENTS[instrument_name]
    inst_range = INSTRUMENT_RANGES.get(instrument_name)
    if inst_range is not None:
        return inst_range.program
    return 0
