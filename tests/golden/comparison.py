"""Golden MIDI comparison — detects unintended musical regression.

Compares an actual MIDI file against an expected golden MIDI, reporting
structural differences. Bit-exact comparison is the default; tolerance
mode exists only for documented exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pretty_midi


@dataclass(frozen=True)
class MidiDiff:
    """Summary of differences between two MIDI files.

    Attributes:
        note_count_diff: Difference in total note count (actual - expected).
        pitch_set_diff: Pitches present in one but not the other.
        velocity_avg_diff: Difference in average velocity.
        duration_total_diff: Difference in total duration (seconds).
        structural_match: True if the files are structurally identical.
        details: Human-readable description of differences.
    """

    note_count_diff: int
    pitch_set_diff: set[int]
    velocity_avg_diff: float
    duration_total_diff: float
    structural_match: bool
    details: list[str] = field(default_factory=list)


def _extract_notes(midi: pretty_midi.PrettyMIDI) -> list[tuple[int, float, float, int]]:
    """Extract (pitch, start, end, velocity) tuples from a PrettyMIDI, sorted."""
    notes = []
    for instrument in midi.instruments:
        for note in instrument.notes:
            notes.append((note.pitch, round(note.start, 4), round(note.end, 4), note.velocity))
    notes.sort()
    return notes


def compare_midi(actual_path: Path, expected_path: Path) -> MidiDiff:
    """Compare two MIDI files and return a diff summary.

    Args:
        actual_path: Path to the generated MIDI.
        expected_path: Path to the golden expected MIDI.

    Returns:
        MidiDiff with comparison results.
    """
    actual = pretty_midi.PrettyMIDI(str(actual_path))
    expected = pretty_midi.PrettyMIDI(str(expected_path))

    actual_notes = _extract_notes(actual)
    expected_notes = _extract_notes(expected)

    details: list[str] = []

    # Note count
    note_count_diff = len(actual_notes) - len(expected_notes)
    if note_count_diff != 0:
        details.append(
            f"Note count: {len(actual_notes)} vs {len(expected_notes)}"
            f" (diff={note_count_diff})"
        )

    # Pitch sets
    actual_pitches = {n[0] for n in actual_notes}
    expected_pitches = {n[0] for n in expected_notes}
    pitch_set_diff = actual_pitches.symmetric_difference(expected_pitches)
    if pitch_set_diff:
        details.append(f"Pitch set diff: {pitch_set_diff}")

    # Average velocity
    avg_vel_actual = sum(n[3] for n in actual_notes) / max(len(actual_notes), 1)
    avg_vel_expected = sum(n[3] for n in expected_notes) / max(len(expected_notes), 1)
    velocity_avg_diff = avg_vel_actual - avg_vel_expected

    # Duration
    dur_actual = actual.get_end_time()
    dur_expected = expected.get_end_time()
    duration_total_diff = dur_actual - dur_expected
    if abs(duration_total_diff) > 0.01:
        details.append(f"Duration: {dur_actual:.2f}s vs {dur_expected:.2f}s")

    # Structural match: exact note-by-note comparison
    structural_match = actual_notes == expected_notes
    if not structural_match and not details:
        # Find first difference
        for i, (a, e) in enumerate(zip(actual_notes, expected_notes, strict=False)):
            if a != e:
                details.append(f"First diff at note {i}: actual={a} expected={e}")
                break

    return MidiDiff(
        note_count_diff=note_count_diff,
        pitch_set_diff=pitch_set_diff,
        velocity_avg_diff=velocity_avg_diff,
        duration_total_diff=duration_total_diff,
        structural_match=structural_match,
        details=details,
    )


def assert_midi_match(
    actual_path: Path,
    expected_path: Path,
    tolerance: float = 0.0,
) -> None:
    """Assert that an actual MIDI matches the golden expected MIDI.

    Args:
        actual_path: Path to the generated MIDI.
        expected_path: Path to the golden MIDI.
        tolerance: If 0.0, require bit-exact match. If > 0, allow
            tolerance in velocity and timing (degraded mode).

    Raises:
        AssertionError: If the MIDI files don't match.
    """
    if not expected_path.exists():
        raise AssertionError(
            f"Golden MIDI not found: {expected_path}\n"
            "Run: python tests/golden/tools/regenerate_goldens.py "
            '--reason "Initial generation" --confirm'
        )

    diff = compare_midi(actual_path, expected_path)

    if tolerance == 0.0:
        assert diff.structural_match, (
            "Golden MIDI mismatch (bit-exact mode):\n"
            + "\n".join(f"  - {d}" for d in diff.details)
        )
    else:
        # Tolerance mode: allow minor velocity and timing differences
        assert abs(diff.note_count_diff) == 0, (
            f"Note count mismatch: {diff.note_count_diff}"
        )
        assert abs(diff.velocity_avg_diff) <= tolerance * 127, (
            f"Velocity avg diff {diff.velocity_avg_diff:.1f} exceeds tolerance"
        )
