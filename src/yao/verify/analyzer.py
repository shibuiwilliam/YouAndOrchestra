"""Score analyzer — generates analysis reports from ScoreIR.

Belongs to Layer 6 (Verification). Produces structured reports with
note counts, duration, pitch statistics, and lint results.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from yao.errors import VerificationError
from yao.ir.notation import midi_to_note_name
from yao.ir.score_ir import ScoreIR
from yao.verify.music_lint import LintResult, lint_score


@dataclass
class AnalysisReport:
    """Structured analysis of a ScoreIR.

    Attributes:
        title: Composition title.
        total_notes: Total number of notes across all parts.
        duration_seconds: Total duration in seconds.
        pitch_range: (lowest MIDI, highest MIDI) across all notes.
        pitch_range_names: (lowest name, highest name) in scientific notation.
        instruments_used: List of instrument names.
        sections: List of section names.
        tempo_bpm: Tempo in BPM.
        key: Key signature.
        time_signature: Time signature.
        total_bars: Total bar count.
        notes_per_instrument: Note count per instrument.
        lint_results: List of lint findings.
    """

    title: str
    total_notes: int
    duration_seconds: float
    pitch_range: tuple[int, int]
    pitch_range_names: tuple[str, str]
    instruments_used: list[str]
    sections: list[str]
    tempo_bpm: float
    key: str
    time_signature: str
    total_bars: int
    notes_per_instrument: dict[str, int]
    lint_results: list[LintResult] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize the report to a JSON string.

        Returns:
            JSON string with all analysis data.
        """
        data = asdict(self)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, path: Path) -> None:
        """Save the analysis report to a JSON file.

        Args:
            path: Output file path.

        Raises:
            VerificationError: If saving fails.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(self.to_json())
        except OSError as e:
            raise VerificationError(f"Failed to save analysis: {e}") from e

    def summary(self) -> str:
        """Generate a human-readable summary.

        Returns:
            Multi-line summary string.
        """
        errors = [r for r in self.lint_results if r.severity == "error"]
        warnings = [r for r in self.lint_results if r.severity == "warning"]

        lines = [
            f"=== Analysis: {self.title} ===",
            f"Key: {self.key} | Tempo: {self.tempo_bpm} BPM | Time: {self.time_signature}",
            f"Duration: {self.duration_seconds:.1f}s | Bars: {self.total_bars}",
            f"Notes: {self.total_notes} | Instruments: {', '.join(self.instruments_used)}",
            f"Pitch range: {self.pitch_range_names[0]} – {self.pitch_range_names[1]}",
            f"Sections: {', '.join(self.sections)}",
        ]

        for instr, count in self.notes_per_instrument.items():
            lines.append(f"  {instr}: {count} notes")

        if errors:
            lines.append(f"\nLint errors: {len(errors)}")
            for r in errors:
                lines.append(f"  [ERROR] {r.message} ({r.location})")
        if warnings:
            lines.append(f"Lint warnings: {len(warnings)}")
            for r in warnings:
                lines.append(f"  [WARN] {r.message} ({r.location})")
        if not errors and not warnings:
            lines.append("\nLint: all checks passed.")

        return "\n".join(lines)


def analyze_score(score: ScoreIR) -> AnalysisReport:
    """Analyze a ScoreIR and produce a structured report.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        AnalysisReport with complete analysis data.
    """
    all_notes = score.all_notes()
    lint_results = lint_score(score)

    if all_notes:
        pitches = [n.pitch for n in all_notes]
        pitch_low = min(pitches)
        pitch_high = max(pitches)
        pitch_range = (pitch_low, pitch_high)
        pitch_range_names = (midi_to_note_name(pitch_low), midi_to_note_name(pitch_high))
    else:
        pitch_range = (0, 0)
        pitch_range_names = ("N/A", "N/A")

    instruments = score.instruments()
    notes_per_instrument: dict[str, int] = {}
    for instr in instruments:
        notes_per_instrument[instr] = len(score.part_for_instrument(instr))

    return AnalysisReport(
        title=score.title,
        total_notes=len(all_notes),
        duration_seconds=score.duration_seconds(),
        pitch_range=pitch_range,
        pitch_range_names=pitch_range_names,
        instruments_used=instruments,
        sections=[s.name for s in score.sections],
        tempo_bpm=score.tempo_bpm,
        key=score.key,
        time_signature=score.time_signature,
        total_bars=score.total_bars(),
        notes_per_instrument=notes_per_instrument,
        lint_results=lint_results,
    )
