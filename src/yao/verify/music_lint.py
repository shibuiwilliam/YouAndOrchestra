"""Music lint — automated detection of musical constraint violations.

Belongs to Layer 6 (Verification). Evaluates ScoreIR objects for common
errors: out-of-range notes, overlapping pitches, unreasonable tempos, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.notation import midi_to_note_name
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class LintResult:
    """A single lint finding.

    Attributes:
        rule: Identifier for the lint rule that triggered.
        severity: How serious the finding is.
        message: Human-readable description.
        location: Where in the score the issue was found.
    """

    rule: str
    severity: Literal["error", "warning", "info"]
    message: str
    location: str


def lint_score(score: ScoreIR) -> list[LintResult]:
    """Run all lint checks on a ScoreIR.

    Args:
        score: The ScoreIR to lint.

    Returns:
        List of lint findings, sorted by severity (errors first).
    """
    results: list[LintResult] = []
    results.extend(_check_empty_score(score))
    results.extend(_check_tempo(score))
    results.extend(_check_time_signature(score))
    results.extend(_check_note_ranges(score))
    results.extend(_check_overlapping_notes(score))
    results.extend(_check_velocity(score))
    results.extend(_check_duration(score))

    # Sort: errors first, then warnings, then info
    severity_order = {"error": 0, "warning": 1, "info": 2}
    results.sort(key=lambda r: severity_order.get(r.severity, 3))
    return results


def _check_empty_score(score: ScoreIR) -> list[LintResult]:
    """Check that the score has at least one note."""
    if not score.all_notes():
        return [
            LintResult(
                rule="empty_score",
                severity="error",
                message="Score contains no notes.",
                location="global",
            )
        ]
    return []


def _check_tempo(score: ScoreIR) -> list[LintResult]:
    """Check that tempo is within reasonable bounds."""
    results: list[LintResult] = []
    if score.tempo_bpm < 20.0:
        results.append(
            LintResult(
                rule="tempo_too_slow",
                severity="warning",
                message=f"Tempo {score.tempo_bpm} BPM is unusually slow (< 20).",
                location="global",
            )
        )
    if score.tempo_bpm > 300.0:
        results.append(
            LintResult(
                rule="tempo_too_fast",
                severity="warning",
                message=f"Tempo {score.tempo_bpm} BPM is unusually fast (> 300).",
                location="global",
            )
        )
    return results


def _check_time_signature(score: ScoreIR) -> list[LintResult]:
    """Check that time signature is valid."""
    parts = score.time_signature.split("/")
    if len(parts) != 2:  # noqa: PLR2004
        return [
            LintResult(
                rule="invalid_time_signature",
                severity="error",
                message=f"Invalid time signature '{score.time_signature}'.",
                location="global",
            )
        ]
    return []


def _check_note_ranges(score: ScoreIR) -> list[LintResult]:
    """Check that all notes are within their instrument's range."""
    results: list[LintResult] = []
    for section in score.sections:
        for part in section.parts:
            inst_range = INSTRUMENT_RANGES.get(part.instrument)
            if inst_range is None:
                continue
            for note in part.notes:
                if not inst_range.midi_low <= note.pitch <= inst_range.midi_high:
                    note_name = midi_to_note_name(note.pitch)
                    results.append(
                        LintResult(
                            rule="note_out_of_range",
                            severity="error",
                            message=(
                                f"{note_name} (MIDI {note.pitch}) out of range "
                                f"for {part.instrument} "
                                f"({inst_range.midi_low}–{inst_range.midi_high})."
                            ),
                            location=f"section '{section.name}', beat {note.start_beat:.1f}",
                        )
                    )
    return results


def _check_overlapping_notes(score: ScoreIR) -> list[LintResult]:
    """Check for overlapping notes on the same pitch within an instrument."""
    results: list[LintResult] = []
    for instrument in score.instruments():
        notes = score.part_for_instrument(instrument)
        # Group by pitch
        by_pitch: dict[int, list[Note]] = {}
        for note in notes:
            by_pitch.setdefault(note.pitch, []).append(note)

        for pitch, pitch_notes in by_pitch.items():
            sorted_notes = sorted(pitch_notes, key=lambda n: n.start_beat)
            for i in range(len(sorted_notes) - 1):
                current = sorted_notes[i]
                next_note = sorted_notes[i + 1]
                if current.end_beat() > next_note.start_beat + 0.001:
                    note_name = midi_to_note_name(pitch)
                    results.append(
                        LintResult(
                            rule="overlapping_notes",
                            severity="warning",
                            message=(
                                f"Overlapping {note_name} in {instrument}: "
                                f"ends at beat {current.end_beat():.1f}, "
                                f"next starts at beat {next_note.start_beat:.1f}."
                            ),
                            location=f"beat {current.start_beat:.1f}, {instrument}",
                        )
                    )
    return results


def _check_velocity(score: ScoreIR) -> list[LintResult]:
    """Check for velocity values outside valid MIDI range."""
    results: list[LintResult] = []
    for note in score.all_notes():
        if not 1 <= note.velocity <= 127:
            results.append(
                LintResult(
                    rule="invalid_velocity",
                    severity="error",
                    message=f"Velocity {note.velocity} out of range (1–127).",
                    location=f"beat {note.start_beat:.1f}, {note.instrument}",
                )
            )
    return results


def _check_duration(score: ScoreIR) -> list[LintResult]:
    """Check for notes with zero or negative duration."""
    results: list[LintResult] = []
    for note in score.all_notes():
        if note.duration_beats <= 0:
            results.append(
                LintResult(
                    rule="invalid_duration",
                    severity="error",
                    message=f"Note has non-positive duration: {note.duration_beats}.",
                    location=f"beat {note.start_beat:.1f}, {note.instrument}",
                )
            )
    return results
