"""MusicXML writer — converts ScoreIR to MusicXML via music21.

Produces .musicxml files that can be opened in MuseScore, Sibelius, Finale,
or any MusicXML-compatible notation software.

Optionally incorporates PerformanceLayer data as articulation and dynamics
markings in the score.

Belongs to Layer 5 (Rendering).

Note: music21 is largely untyped. This module uses ``type: ignore`` comments
where music21 APIs lack stubs. This is expected and approved.
"""
# mypy: disable-error-code="no-untyped-call,attr-defined"

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import music21

from yao.errors import RenderError
from yao.ir.notation import parse_key
from yao.ir.score_ir import ScoreIR

if TYPE_CHECKING:
    from yao.ir.expression import NoteId, PerformanceLayer


def write_musicxml(
    score: ScoreIR,
    output_path: Path,
    performance_layer: PerformanceLayer | None = None,
) -> Path:
    """Convert a ScoreIR to MusicXML and write to file.

    Args:
        score: The ScoreIR to convert.
        output_path: Path for the output .musicxml file.
        performance_layer: Optional performance expression overlay.
            If provided, accent and legato markings are added.

    Returns:
        Path to the written MusicXML file.

    Raises:
        RenderError: If conversion or writing fails.
    """
    try:
        m21_score = _score_ir_to_music21(score, performance_layer)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        m21_score.write("musicxml", fp=str(output_path))
    except RenderError:
        raise
    except Exception as e:
        raise RenderError(f"Failed to write MusicXML to {output_path}: {e}") from e

    return output_path


def _score_ir_to_music21(
    score: ScoreIR,
    performance_layer: PerformanceLayer | None = None,
) -> Any:
    """Convert ScoreIR to a music21 Score object.

    Args:
        score: The ScoreIR.
        performance_layer: Optional expression overlay.

    Returns:
        A music21 Score ready for export.
    """
    m21_score = music21.stream.Score()

    # Metadata
    m21_score.metadata = music21.metadata.Metadata()
    m21_score.metadata.title = score.title

    # Prepare key/time for insertion into each part
    m21_key: Any = None
    try:
        root, scale_type = parse_key(score.key)
        mode = "major" if scale_type == "major" else "minor"
        m21_key = music21.key.Key(root, mode)
    except Exception:
        pass

    m21_ts: Any = None
    with contextlib.suppress(Exception):
        m21_ts = music21.meter.TimeSignature(score.time_signature)

    # Collect notes per instrument across all sections
    instrument_notes: dict[str, list[tuple[float, float, int, int]]] = {}
    for section in score.sections:
        for part in section.parts:
            if part.instrument not in instrument_notes:
                instrument_notes[part.instrument] = []
            for note in part.notes:
                instrument_notes[part.instrument].append(
                    (note.start_beat, note.duration_beats, note.pitch, note.velocity)
                )

    # Build parts
    for instr_name, notes in instrument_notes.items():
        m21_part = music21.stream.Part()
        m21_part.partName = instr_name

        # Insert key, time, and tempo at the beginning of each part
        m21_part.insert(0, music21.tempo.MetronomeMark(number=score.tempo_bpm))
        if m21_key is not None:
            m21_part.insert(0, music21.key.Key(m21_key.tonic, m21_key.mode))
        if m21_ts is not None:
            m21_part.insert(0, music21.meter.TimeSignature(m21_ts.ratioString))

        # Try to set instrument
        try:
            m21_instr = music21.instrument.fromString(instr_name)
            m21_part.insert(0, m21_instr)
        except Exception:
            pass  # Unknown instrument — continue without

        # Sort notes by start beat
        notes.sort(key=lambda n: (n[0], n[2]))

        for start_beat, dur_beats, pitch, velocity in notes:
            m21_note = music21.note.Note(pitch)
            m21_note.quarterLength = dur_beats
            m21_note.volume.velocity = velocity

            # Apply performance layer if available
            if performance_layer is not None:
                note_id: NoteId = (instr_name, start_beat, pitch)
                expr = performance_layer.for_note(note_id)
                if expr is not None:
                    _apply_expression(m21_note, expr)

            m21_part.insert(start_beat, m21_note)

        m21_score.insert(0, m21_part)

    return m21_score


def _apply_expression(
    m21_note: Any,
    expr: object,
) -> None:
    """Apply basic NoteExpression markings to a music21 note.

    Args:
        m21_note: The music21 note to annotate.
        expr: A NoteExpression object (typed as object to avoid import cycle).
    """
    accent_strength = getattr(expr, "accent_strength", 0.0)
    legato_overlap = getattr(expr, "legato_overlap", 0.0)

    if accent_strength > 0.3:
        m21_note.articulations.append(music21.articulations.Accent())

    if legato_overlap > 0.0:
        m21_note.articulations.append(music21.articulations.Tenuto())
