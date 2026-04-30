"""Constraint checker — evaluates constraints against a ScoreIR.

Implements PROJECT_IMPROVEMENT §5.5: a unified system for checking
must / must_not / prefer / avoid rules with scope (global, section,
instrument, bar range).

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

import re

from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR
from yao.ir.voicing import Voicing, check_parallel_fifths
from yao.schema.constraints import Constraint, ConstraintsSpec
from yao.verify.music_lint import LintResult

_BAR_RANGE_PATTERN = re.compile(r"^bars:(\d+)-(\d+)$")


def check_constraints(
    score: ScoreIR,
    constraints: ConstraintsSpec,
) -> list[LintResult]:
    """Evaluate all constraints against a ScoreIR.

    Args:
        score: The ScoreIR to check.
        constraints: The constraint specification.

    Returns:
        List of LintResult for any violations found.
    """
    results: list[LintResult] = []
    for constraint in constraints.constraints:
        results.extend(_check_single(score, constraint))
    return results


def _get_scoped_notes(score: ScoreIR, scope: str) -> list[Note]:
    """Filter notes by scope string.

    Scope formats:
    - "global" — all notes
    - "section:chorus" — notes in the named section
    - "instrument:piano" — notes for the named instrument
    - "bars:8-16" — notes in bar range [8, 16)
    """
    all_notes = score.all_notes()

    if scope == "global":
        return all_notes

    if scope.startswith("section:"):
        section_name = scope[len("section:") :]
        section_notes: list[Note] = []
        for section in score.sections:
            if section.name == section_name:
                for part in section.parts:
                    section_notes.extend(part.notes)
        return section_notes

    if scope.startswith("instrument:"):
        instr_name = scope[len("instrument:") :]
        return score.part_for_instrument(instr_name)

    match = _BAR_RANGE_PATTERN.match(scope)
    if match:
        from yao.ir.timing import bars_to_beats

        bar_start = int(match.group(1))
        bar_end = int(match.group(2))
        beat_start = bars_to_beats(bar_start, score.time_signature)
        beat_end = bars_to_beats(bar_end, score.time_signature)
        return [n for n in all_notes if beat_start <= n.start_beat < beat_end]

    return all_notes


def _check_single(score: ScoreIR, constraint: Constraint) -> list[LintResult]:
    """Check a single constraint."""
    notes = _get_scoped_notes(score, constraint.scope)
    rule = constraint.rule

    if rule == "no_parallel_fifths":
        return _check_no_parallel_fifths(score, constraint)
    if rule.startswith("max_density:"):
        max_val = float(rule.split(":")[1])
        return _check_max_density(notes, max_val, constraint)
    if rule.startswith("note_above:"):
        from yao.ir.notation import note_name_to_midi

        limit_name = rule.split(":")[1]
        limit = note_name_to_midi(limit_name)
        return _check_note_limit(notes, limit, "above", constraint)
    if rule.startswith("note_below:"):
        from yao.ir.notation import note_name_to_midi

        limit_name = rule.split(":")[1]
        limit = note_name_to_midi(limit_name)
        return _check_note_limit(notes, limit, "below", constraint)
    if rule.startswith("min_rest_ratio:"):
        min_ratio = float(rule.split(":")[1])
        return _check_rest_ratio(notes, score, min_ratio, constraint)

    return []


def _check_no_parallel_fifths(score: ScoreIR, constraint: Constraint) -> list[LintResult]:
    """Check for parallel fifths in chord voicings."""
    results: list[LintResult] = []
    for section in score.sections:
        for part in section.parts:
            sorted_notes = sorted(part.notes, key=lambda n: n.start_beat)
            # Group simultaneous notes into voicings
            voicings: list[tuple[float, Voicing]] = []
            current_beat = -1.0
            current_pitches: list[int] = []
            for note in sorted_notes:
                if abs(note.start_beat - current_beat) > 0.01:
                    if current_pitches:
                        voicings.append((current_beat, Voicing(pitches=tuple(sorted(current_pitches)))))
                    current_beat = note.start_beat
                    current_pitches = [note.pitch]
                else:
                    current_pitches.append(note.pitch)
            if current_pitches:
                voicings.append((current_beat, Voicing(pitches=tuple(sorted(current_pitches)))))

            for i in range(len(voicings) - 1):
                beat_a, v_a = voicings[i]
                beat_b, v_b = voicings[i + 1]
                parallels = check_parallel_fifths(v_a, v_b)
                if parallels:
                    is_violation = constraint.type in ("must_not", "avoid")
                    if is_violation:
                        results.append(
                            LintResult(
                                rule="constraint:no_parallel_fifths",
                                severity=constraint.severity,  # type: ignore[arg-type]
                                message=(
                                    f"Parallel fifths at beat {beat_a:.1f}→{beat_b:.1f} "
                                    f"in {part.instrument}: voice pairs {parallels}. "
                                    f"{constraint.description}"
                                ),
                                location=f"section '{section.name}', beat {beat_a:.1f}",
                            )
                        )
    return results


def _check_max_density(notes: list[Note], max_density: float, constraint: Constraint) -> list[LintResult]:
    """Check that note density doesn't exceed a maximum."""
    if not notes:
        return []
    # Count notes per beat
    from collections import Counter

    beats = Counter(round(n.start_beat) for n in notes)
    violations: list[LintResult] = []
    for beat, count in beats.items():
        if count > max_density:
            violations.append(
                LintResult(
                    rule="constraint:max_density",
                    severity=constraint.severity,  # type: ignore[arg-type]
                    message=(f"Density {count} exceeds max {max_density} at beat {beat}. {constraint.description}"),
                    location=f"beat {beat}",
                )
            )
    return violations


def _check_note_limit(
    notes: list[Note],
    limit: int,
    direction: str,
    constraint: Constraint,
) -> list[LintResult]:
    """Check notes above or below a pitch limit."""
    violations: list[LintResult] = []
    for note in notes:
        is_violation = False
        if direction == "above" and constraint.type in ("must_not", "avoid"):
            is_violation = note.pitch > limit
        elif direction == "below" and constraint.type in ("must_not", "avoid"):
            is_violation = note.pitch < limit
        elif direction == "above" and constraint.type in ("must", "prefer"):
            is_violation = note.pitch <= limit
        elif direction == "below" and constraint.type in ("must", "prefer"):
            is_violation = note.pitch >= limit

        if is_violation:
            from yao.ir.notation import midi_to_note_name

            violations.append(
                LintResult(
                    rule=f"constraint:note_{direction}",
                    severity=constraint.severity,  # type: ignore[arg-type]
                    message=(
                        f"Note {midi_to_note_name(note.pitch)} violates "
                        f"{constraint.type} note_{direction} constraint. "
                        f"{constraint.description}"
                    ),
                    location=f"beat {note.start_beat:.1f}",
                )
            )
    return violations


def _check_rest_ratio(
    notes: list[Note],
    score: ScoreIR,
    min_ratio: float,
    constraint: Constraint,
) -> list[LintResult]:
    """Check that there's enough silence (rest ratio)."""
    if not notes:
        return []
    total_duration = score.duration_seconds()
    if total_duration <= 0:
        return []

    from yao.ir.timing import beats_to_seconds

    sounding_time = sum(beats_to_seconds(n.duration_beats, score.tempo_bpm) for n in notes)
    rest_ratio = 1.0 - (sounding_time / total_duration)

    if rest_ratio < min_ratio:
        return [
            LintResult(
                rule="constraint:min_rest_ratio",
                severity=constraint.severity,  # type: ignore[arg-type]
                message=(f"Rest ratio {rest_ratio:.2f} below minimum {min_ratio}. {constraint.description}"),
                location="global",
            )
        ]
    return []
