"""LilyPond writer — converts ScoreIR to LilyPond .ly format.

Generates .ly text files and optionally renders to PDF via the
``lilypond`` binary (subprocess). If lilypond is not installed,
PDF rendering is skipped with a warning (never a hard error).

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import structlog

from yao.errors import RenderError
from yao.ir.notation import parse_key
from yao.ir.score_ir import ScoreIR

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Pitch/duration conversion helpers
# ---------------------------------------------------------------------------

_NOTE_NAMES_SHARP = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]


def _midi_to_lilypond_pitch(midi_pitch: int) -> str:
    """Convert a MIDI note number to LilyPond pitch notation.

    Args:
        midi_pitch: MIDI note number (0-127).

    Returns:
        LilyPond pitch string, e.g., "c'", "fis''", "a,".
    """
    pitch_class = midi_pitch % 12
    octave = (midi_pitch // 12) - 1  # MIDI octave
    name = _NOTE_NAMES_SHARP[pitch_class]

    # LilyPond middle C (C4, MIDI 60) = c'
    # Each octave up adds ', each octave down adds ,
    ly_octave = octave - 3  # c' = octave 4, relative base is 3
    if ly_octave > 0:
        name += "'" * ly_octave
    elif ly_octave < 0:
        name += "," * (-ly_octave)

    return name


def _beats_to_lilypond_duration(beats: float) -> str:
    """Convert beat duration to LilyPond duration string.

    Args:
        beats: Duration in quarter-note beats.

    Returns:
        LilyPond duration string (e.g., "4" for quarter, "8" for eighth).
        Falls back to the nearest standard duration.
    """
    # Standard durations: whole=4beats, half=2, quarter=1, eighth=0.5, sixteenth=0.25
    durations = [
        (4.0, "1"),
        (3.0, "2."),
        (2.0, "2"),
        (1.5, "4."),
        (1.0, "4"),
        (0.75, "8."),
        (0.5, "8"),
        (0.375, "16."),
        (0.25, "16"),
        (0.125, "32"),
    ]

    best_dur = "4"
    best_diff = float("inf")
    for beat_val, ly_dur in durations:
        diff = abs(beats - beat_val)
        if diff < best_diff:
            best_diff = diff
            best_dur = ly_dur

    return best_dur


def _key_to_lilypond(key_str: str) -> str:
    """Convert YaO key string to LilyPond key command.

    Args:
        key_str: Key string like "C major", "D minor".

    Returns:
        LilyPond key command, e.g., "\\key c \\major".
    """
    try:
        root, scale_type = parse_key(key_str)
    except Exception:
        return "\\key c \\major"

    ly_root = root.lower().replace("#", "is").replace("b", "es")
    if len(ly_root) > 1 and ly_root[1:] == "es" and ly_root[0] in ("a", "e"):
        pass  # aes, ees are correct
    ly_mode = "\\major" if scale_type == "major" else "\\minor"
    return f"\\key {ly_root} {ly_mode}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_lilypond(score: ScoreIR, output_path: Path) -> Path:
    """Convert a ScoreIR to a LilyPond .ly file.

    Args:
        score: The ScoreIR to convert.
        output_path: Path for the output .ly file.

    Returns:
        Path to the written .ly file.

    Raises:
        RenderError: If writing fails.
    """
    try:
        ly_text = _score_ir_to_lilypond(score)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ly_text, encoding="utf-8")
    except Exception as e:
        raise RenderError(f"Failed to write LilyPond file: {e}") from e

    return output_path


def render_lilypond_pdf(
    ly_path: Path,
    output_pdf: Path | None = None,
) -> Path | None:
    """Render a .ly file to PDF using the lilypond binary.

    Args:
        ly_path: Path to the .ly source file.
        output_pdf: Desired output PDF path. If None, uses the .ly path
            with .pdf extension.

    Returns:
        Path to the generated PDF, or None if lilypond is not installed.
    """
    lilypond_bin = shutil.which("lilypond")
    if lilypond_bin is None:
        logger.warning(
            "lilypond_not_installed",
            message="lilypond binary not found. PDF rendering skipped. "
            "Install with: brew install lilypond (macOS) or "
            "apt-get install lilypond (Linux).",
        )
        return None

    if output_pdf is None:
        output_pdf = ly_path.with_suffix(".pdf")

    output_dir = output_pdf.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        lilypond_bin,
        "--output",
        str(output_dir / output_pdf.stem),
        "-dno-point-and-click",
        str(ly_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("lilypond_timeout", message="lilypond timed out after 30 seconds")
        return None
    except OSError as e:
        logger.warning("lilypond_error", message=f"Failed to run lilypond: {e}")
        return None

    if result.returncode != 0:
        logger.warning(
            "lilypond_failed",
            returncode=result.returncode,
            stderr=result.stderr[:500],
        )
        return None

    if output_pdf.exists():
        return output_pdf

    return None


# ---------------------------------------------------------------------------
# Internal conversion
# ---------------------------------------------------------------------------


def _score_ir_to_lilypond(score: ScoreIR) -> str:
    """Convert ScoreIR to LilyPond source text.

    Args:
        score: The ScoreIR.

    Returns:
        Complete LilyPond source as a string.
    """
    lines: list[str] = []

    lines.append('\\version "2.24.0"')
    lines.append("")
    lines.append("\\header {")
    lines.append(f'  title = "{score.title}"')
    lines.append("}")
    lines.append("")

    # Collect notes per instrument
    instrument_notes: dict[str, list[tuple[float, float, int]]] = {}
    for section in score.sections:
        for part in section.parts:
            if part.instrument not in instrument_notes:
                instrument_notes[part.instrument] = []
            for note in part.notes:
                instrument_notes[part.instrument].append((note.start_beat, note.duration_beats, note.pitch))

    # Global settings
    key_cmd = _key_to_lilypond(score.key)
    time_cmd = f"\\time {score.time_signature}"

    lines.append("<<")

    for instr_name, notes in instrument_notes.items():
        notes.sort(key=lambda n: (n[0], n[2]))

        # Choose clef based on average pitch
        if notes:
            avg_pitch = sum(n[2] for n in notes) / len(notes)
            clef = "bass" if avg_pitch < 55 else "treble"
        else:
            clef = "treble"

        lines.append(f'  \\new Staff \\with {{ instrumentName = "{instr_name}" }} {{')
        lines.append(f"    \\clef {clef}")
        lines.append(f"    {key_cmd}")
        lines.append(f"    {time_cmd}")
        lines.append(f"    \\tempo 4 = {int(score.tempo_bpm)}")

        # Convert notes to LilyPond notation
        note_strs: list[str] = []
        for _start, dur, pitch in notes:
            ly_pitch = _midi_to_lilypond_pitch(pitch)
            ly_dur = _beats_to_lilypond_duration(dur)
            note_strs.append(f"{ly_pitch}{ly_dur}")

        # Wrap in lines of ~8 notes each
        for i in range(0, len(note_strs), 8):
            chunk = " ".join(note_strs[i : i + 8])
            lines.append(f"    {chunk}")

        lines.append("  }")

    lines.append(">>")
    lines.append("")

    return "\n".join(lines)
