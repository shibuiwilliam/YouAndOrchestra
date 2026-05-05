"""Singability evaluator — validates vocal lines for human performance.

Checks vocal parts for:
- Awkward leaps (intervals > 7 semitones that are difficult to sing)
- Breath violations (phrases too long without rest)
- Tessitura strain (too many notes at extremes of the vocal range)

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR

# Vocal range definitions (MIDI note numbers)
_VOCAL_RANGES: dict[str, tuple[int, int]] = {
    "soprano": (60, 84),  # C4 to C6
    "mezzo_soprano": (57, 81),  # A3 to A5
    "alto": (53, 77),  # F3 to F5
    "tenor": (48, 72),  # C3 to C5
    "baritone": (45, 69),  # A2 to A4
    "bass_voice": (40, 64),  # E2 to E4
    "voice": (48, 79),  # C3 to G5 (generic)
    "vocal": (48, 79),  # alias
}

# Maximum comfortable phrase length in beats without a breath
_MAX_PHRASE_BEATS: float = 8.0

# Minimum rest duration that counts as a breath opportunity
_MIN_BREATH_BEATS: float = 0.5

# Leap threshold in semitones
_AWKWARD_LEAP_THRESHOLD: int = 7

# Tessitura comfort zone: notes in the outer 20% of range are strained
_TESSITURA_STRAIN_FRACTION: float = 0.2


@dataclass(frozen=True)
class SingabilityReport:
    """Report on the singability of a vocal line.

    Attributes:
        awkward_leaps: Number of intervals exceeding the leap threshold.
        breath_violations: Number of phrases exceeding max length without breath.
        tessitura_strain: Fraction of notes in the strained outer range [0.0, 1.0].
        total_notes: Total notes analyzed.
        score: Overall singability score [0.0, 1.0], 1.0 = perfectly singable.
        issues: Human-readable list of specific issues found.
    """

    awkward_leaps: int
    breath_violations: int
    tessitura_strain: float
    total_notes: int
    score: float
    issues: tuple[str, ...]


def evaluate_singability(
    score: ScoreIR,
    vocal_instrument: str = "voice",
) -> SingabilityReport:
    """Evaluate the singability of a vocal part in the score.

    Analyzes the notes for the given vocal instrument and checks
    for awkward leaps, breath violations, and tessitura strain.

    Args:
        score: The ScoreIR containing the vocal part.
        vocal_instrument: Name of the vocal instrument to evaluate.

    Returns:
        SingabilityReport with metrics and issues.
    """
    notes = score.part_for_instrument(vocal_instrument)
    if not notes:
        return SingabilityReport(
            awkward_leaps=0,
            breath_violations=0,
            tessitura_strain=0.0,
            total_notes=0,
            score=1.0,
            issues=(),
        )

    # Sort by start beat
    sorted_notes = sorted(notes, key=lambda n: n.start_beat)

    # Determine vocal range
    vocal_range = _get_vocal_range(vocal_instrument)

    awkward_leaps = _count_awkward_leaps(sorted_notes)
    breath_violations = _count_breath_violations(sorted_notes)
    tessitura_strain = _compute_tessitura_strain(sorted_notes, vocal_range)

    issues: list[str] = []
    if awkward_leaps > 0:
        issues.append(f"{awkward_leaps} awkward leap(s) exceeding {_AWKWARD_LEAP_THRESHOLD} semitones")
    if breath_violations > 0:
        issues.append(f"{breath_violations} phrase(s) exceeding {_MAX_PHRASE_BEATS} beats without breath")
    if tessitura_strain > 0.3:
        issues.append(f"Tessitura strain: {tessitura_strain:.0%} of notes in strained range")

    # Compute overall score
    total_notes = len(sorted_notes)
    leap_penalty = min(1.0, awkward_leaps / max(total_notes * 0.1, 1))
    breath_penalty = min(1.0, breath_violations * 0.2)
    strain_penalty = tessitura_strain

    overall = max(0.0, 1.0 - (leap_penalty * 0.4 + breath_penalty * 0.3 + strain_penalty * 0.3))

    return SingabilityReport(
        awkward_leaps=awkward_leaps,
        breath_violations=breath_violations,
        tessitura_strain=tessitura_strain,
        total_notes=total_notes,
        score=overall,
        issues=tuple(issues),
    )


def _get_vocal_range(vocal_instrument: str) -> tuple[int, int]:
    """Get the MIDI note range for a vocal instrument.

    Args:
        vocal_instrument: Vocal instrument name.

    Returns:
        Tuple of (low_midi, high_midi).
    """
    # Check custom vocal ranges first
    if vocal_instrument in _VOCAL_RANGES:
        return _VOCAL_RANGES[vocal_instrument]

    # Check INSTRUMENT_RANGES
    inst_range = INSTRUMENT_RANGES.get(vocal_instrument)
    if inst_range is not None:
        return (inst_range.midi_low, inst_range.midi_high)

    # Default to generic voice range
    return _VOCAL_RANGES["voice"]


def _count_awkward_leaps(notes: list[Note]) -> int:
    """Count intervals that exceed the awkward leap threshold.

    Args:
        notes: Sorted notes.

    Returns:
        Number of awkward leaps.
    """
    count = 0
    for i in range(1, len(notes)):
        interval = abs(notes[i].pitch - notes[i - 1].pitch)
        if interval > _AWKWARD_LEAP_THRESHOLD:
            count += 1
    return count


def _count_breath_violations(notes: list[Note]) -> int:
    """Count phrases that are too long without a breath opportunity.

    A breath opportunity is a gap of at least _MIN_BREATH_BEATS between
    consecutive notes.

    Args:
        notes: Sorted notes.

    Returns:
        Number of breath violations.
    """
    if not notes:
        return 0

    violations = 0
    phrase_start = notes[0].start_beat

    for i in range(1, len(notes)):
        prev_end = notes[i - 1].start_beat + notes[i - 1].duration_beats
        gap = notes[i].start_beat - prev_end

        if gap >= _MIN_BREATH_BEATS:
            # Breath opportunity found — check if phrase was too long
            phrase_length = prev_end - phrase_start
            if phrase_length > _MAX_PHRASE_BEATS:
                violations += 1
            phrase_start = notes[i].start_beat

    # Check final phrase
    final_end = notes[-1].start_beat + notes[-1].duration_beats
    final_phrase_length = final_end - phrase_start
    if final_phrase_length > _MAX_PHRASE_BEATS:
        violations += 1

    return violations


def _compute_tessitura_strain(notes: list[Note], vocal_range: tuple[int, int]) -> float:
    """Compute the fraction of notes in the strained outer range.

    The comfort zone is the inner portion of the range. Notes in the
    outer _TESSITURA_STRAIN_FRACTION are considered strained.

    Args:
        notes: Notes to analyze.
        vocal_range: Tuple of (low_midi, high_midi).

    Returns:
        Fraction of notes that are strained [0.0, 1.0].
    """
    if not notes:
        return 0.0

    low, high = vocal_range
    range_span = high - low
    strain_margin = range_span * _TESSITURA_STRAIN_FRACTION

    comfort_low = low + strain_margin
    comfort_high = high - strain_margin

    strained_count = 0
    for note in notes:
        if note.pitch < comfort_low or note.pitch > comfort_high:
            strained_count += 1

    return strained_count / len(notes)
