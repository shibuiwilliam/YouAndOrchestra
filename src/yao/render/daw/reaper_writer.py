"""Reaper RPP writer — export ScoreIR to Reaper project format.

Generates a text-based .rpp file that Reaper can open.
Each instrument becomes a track with MIDI items.

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

from pathlib import Path

from yao.ir.score_ir import ScoreIR
from yao.ir.timing import beats_to_seconds


def write_reaper_project(
    score: ScoreIR,
    output_path: Path,
    stems_dir: Path | None = None,
) -> Path:
    """Write a Reaper RPP project file.

    Args:
        score: The ScoreIR to export.
        output_path: Path for the .rpp file.
        stems_dir: Optional directory with MIDI stems to reference.

    Returns:
        Path to the written RPP file.
    """
    rpp = _generate_rpp(score, stems_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rpp, encoding="utf-8")
    return output_path


def _generate_rpp(score: ScoreIR, stems_dir: Path | None) -> str:
    """Generate RPP text content."""
    lines: list[str] = []
    lines.append('<REAPER_PROJECT 0.1 "7.0" 1')
    lines.append(f"  TEMPO {score.tempo_bpm} 4 4")
    lines.append("  SAMPLERATE 44100 0 0")

    for instrument in score.instruments():
        notes = score.part_for_instrument(instrument)
        if not notes:
            continue

        lines.append("  <TRACK")
        lines.append(f'    NAME "{instrument}"')
        lines.append("    PEAKCOL 16576")

        # Reference MIDI stem if available
        if stems_dir:
            stem_path = stems_dir / f"{instrument}.mid"
            if stem_path.exists():
                duration = beats_to_seconds(score.total_beats(), score.tempo_bpm)
                lines.append("    <ITEM")
                lines.append("      POSITION 0")
                lines.append(f"      LENGTH {duration:.3f}")
                lines.append("      <SOURCE MIDI")
                lines.append(f'        FILE "{stem_path}"')
                lines.append("      >")
                lines.append("    >")

        lines.append("  >")

    lines.append(">")
    return "\n".join(lines)
