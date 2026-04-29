"""Audio renderer — MIDI to WAV conversion.

Uses fluidsynth as an external subprocess for SoundFont-based rendering.
This is best-effort: if fluidsynth is unavailable, the renderer reports
the issue clearly rather than failing silently.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import structlog

from yao.errors import RenderError

logger = structlog.get_logger()


def render_midi_to_wav(
    midi_path: Path,
    output_path: Path,
    soundfont_path: Path | None = None,
) -> Path:
    """Render a MIDI file to WAV audio using fluidsynth.

    Args:
        midi_path: Path to the input MIDI file.
        output_path: Path for the output WAV file.
        soundfont_path: Path to a SoundFont file. If None, searches
            the soundfonts/ directory.

    Returns:
        Path to the written WAV file.

    Raises:
        RenderError: If fluidsynth is not available or rendering fails.
    """
    if not midi_path.exists():
        raise RenderError(f"MIDI file not found: {midi_path}")

    fluidsynth_path = shutil.which("fluidsynth")
    if fluidsynth_path is None:
        raise RenderError(
            "fluidsynth is not installed. "
            "Install it with: brew install fluid-synth (macOS) "
            "or apt-get install fluidsynth (Linux)"
        )

    if soundfont_path is None:
        soundfont_path = _find_default_soundfont()
    if soundfont_path is None or not soundfont_path.exists():
        raise RenderError(
            "No SoundFont found. Place a .sf2 file in the soundfonts/ directory. "
            "See soundfonts/README.md for instructions."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        fluidsynth_path,
        "-ni",
        str(soundfont_path),
        str(midi_path),
        "-F",
        str(output_path),
        "-r",
        "44100",
    ]

    logger.info(
        "rendering_midi_to_wav",
        midi=str(midi_path),
        output=str(output_path),
        soundfont=str(soundfont_path),
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise RenderError("fluidsynth timed out after 120 seconds") from e
    except OSError as e:
        raise RenderError(f"Failed to run fluidsynth: {e}") from e

    if result.returncode != 0:
        raise RenderError(f"fluidsynth exited with code {result.returncode}: {result.stderr}")

    if not output_path.exists():
        raise RenderError(f"fluidsynth completed but output not found: {output_path}")

    return output_path


def _find_default_soundfont() -> Path | None:
    """Search for a SoundFont file in the soundfonts/ directory.

    Returns:
        Path to the first .sf2 file found, or None.
    """
    soundfonts_dir = Path("soundfonts")
    if not soundfonts_dir.exists():
        return None

    for sf_file in sorted(soundfonts_dir.glob("*.sf2")):
        return sf_file

    return None
