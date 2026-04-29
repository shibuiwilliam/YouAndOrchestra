"""MIDI reader — loads MIDI files back into ScoreIR.

The inverse of midi_writer.py. Used by the evaluate CLI and critique
workflow to analyze existing iterations without re-generating.

Belongs to Layer 5 (Rendering), alongside midi_writer.py.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import pretty_midi

from yao.constants.midi import DEFAULT_BPM, GENERAL_MIDI_INSTRUMENTS
from yao.errors import RenderError
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import seconds_to_beats

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec

# Reverse lookup: GM program number → instrument name
_PROGRAM_TO_NAME: dict[int, str] = {v: k for k, v in GENERAL_MIDI_INSTRUMENTS.items()}


def load_midi_to_score_ir(
    midi_path: Path,
    spec: CompositionSpec | None = None,
    title: str | None = None,
) -> ScoreIR:
    """Load a MIDI file and convert it to a ScoreIR.

    Args:
        midi_path: Path to the .mid file.
        spec: Optional composition spec for section boundaries and metadata.
            If provided, notes are mapped to spec-defined sections.
            If None, all notes are placed in a single "full" section.
        title: Override title. Defaults to spec title or filename stem.

    Returns:
        A ScoreIR representing the MIDI file contents.

    Raises:
        RenderError: If the MIDI file cannot be read or parsed.
    """
    try:
        midi = pretty_midi.PrettyMIDI(str(midi_path))
    except Exception as e:
        raise RenderError(f"Failed to read MIDI file {midi_path}: {e}") from e

    # Extract tempo
    tempo_changes = midi.get_tempo_changes()
    bpm = float(tempo_changes[1][0]) if len(tempo_changes[1]) > 0 else DEFAULT_BPM

    # Determine title
    if title is not None:
        score_title = title
    elif spec is not None:
        score_title = spec.title
    else:
        score_title = midi_path.stem

    # Determine time signature and key from spec or defaults
    time_signature = spec.time_signature if spec else "4/4"
    key = spec.key if spec else "C major"

    # Parse all instruments and their notes
    instrument_notes: dict[str, list[Note]] = {}
    for midi_instr in midi.instruments:
        instr_name = _resolve_instrument_name(midi_instr)
        if instr_name not in instrument_notes:
            instrument_notes[instr_name] = []

        for midi_note in midi_instr.notes:
            start_beat = seconds_to_beats(midi_note.start, bpm)
            end_beat = seconds_to_beats(midi_note.end, bpm)
            duration = max(end_beat - start_beat, 0.01)

            note = Note(
                pitch=midi_note.pitch,
                start_beat=round(start_beat, 4),
                duration_beats=round(duration, 4),
                velocity=midi_note.velocity,
                instrument=instr_name,
            )
            instrument_notes[instr_name].append(note)

    # Sort notes per instrument by start beat
    for notes in instrument_notes.values():
        notes.sort(key=lambda n: (n.start_beat, n.pitch))

    # Build sections
    if spec is not None and spec.sections:
        sections = _build_sections_from_spec(instrument_notes, spec, time_signature)
    else:
        sections = _build_single_section(instrument_notes, bpm, time_signature)

    return ScoreIR(
        title=score_title,
        tempo_bpm=bpm,
        time_signature=time_signature,
        key=key,
        sections=tuple(sections),
    )


def _resolve_instrument_name(midi_instr: pretty_midi.Instrument) -> str:
    """Resolve a PrettyMIDI instrument to a canonical YaO instrument name.

    Args:
        midi_instr: The PrettyMIDI instrument.

    Returns:
        Canonical instrument name.
    """
    name: str = str(midi_instr.name) if midi_instr.name else ""
    program: int = int(midi_instr.program)

    # First try the instrument's name attribute (set by midi_writer)
    if name and name in GENERAL_MIDI_INSTRUMENTS:
        return name

    # Try program number lookup
    if program in _PROGRAM_TO_NAME:
        return _PROGRAM_TO_NAME[program]

    # Fallback: use the name if present, else "instrument_N"
    if name:
        return name

    return f"instrument_{program}"


def _build_sections_from_spec(
    instrument_notes: dict[str, list[Note]],
    spec: CompositionSpec,
    time_signature: str,
) -> list[Section]:
    """Map notes to spec-defined sections based on bar boundaries.

    Args:
        instrument_notes: Notes grouped by instrument.
        spec: The composition spec with section definitions.
        time_signature: Time signature string.

    Returns:
        List of sections with notes distributed by bar position.
    """
    from yao.ir.timing import bars_to_beats

    sections: list[Section] = []
    current_bar = 0

    for section_spec in spec.sections:
        start_bar = current_bar
        end_bar = current_bar + section_spec.bars
        start_beat = bars_to_beats(start_bar, time_signature)
        end_beat = bars_to_beats(end_bar, time_signature)

        parts: list[Part] = []
        for instr_name, notes in instrument_notes.items():
            section_notes = [
                n for n in notes
                if n.start_beat >= start_beat - 0.001 and n.start_beat < end_beat - 0.001
            ]
            parts.append(Part(instrument=instr_name, notes=tuple(section_notes)))

        sections.append(Section(
            name=section_spec.name,
            start_bar=start_bar,
            end_bar=end_bar,
            parts=tuple(parts),
        ))
        current_bar = end_bar

    return sections


def _build_single_section(
    instrument_notes: dict[str, list[Note]],
    bpm: float,
    time_signature: str,
) -> list[Section]:
    """Build a single section containing all notes.

    Args:
        instrument_notes: Notes grouped by instrument.
        bpm: Tempo in BPM.
        time_signature: Time signature string.

    Returns:
        A list with one section spanning all bars.
    """
    from yao.ir.timing import bars_to_beats

    # Find the latest note end to determine total bars
    max_beat = 0.0
    for notes in instrument_notes.values():
        for note in notes:
            max_beat = max(max_beat, note.start_beat + note.duration_beats)

    if max_beat == 0.0:
        total_bars = 0
    else:
        beats_per_bar = bars_to_beats(1, time_signature)
        total_bars = math.ceil(max_beat / beats_per_bar)

    parts = [
        Part(instrument=name, notes=tuple(notes))
        for name, notes in instrument_notes.items()
    ]

    return [Section(
        name="full",
        start_bar=0,
        end_bar=total_bars,
        parts=tuple(parts),
    )]
