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
from yao.schema.constraints import Constraint, ConstraintsSpec, EnsembleConstraint
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
    for ec in constraints.ensemble_constraints:
        results.extend(_check_ensemble(score, ec))
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


# ---------------------------------------------------------------------------
# Ensemble constraint checking (Wave 3.2)
# ---------------------------------------------------------------------------


def _check_ensemble(score: ScoreIR, ec: EnsembleConstraint) -> list[LintResult]:
    """Check a single ensemble constraint across instrument pairs."""
    if ec.rule == "register_separation":
        return _check_register_separation(score, ec)
    elif ec.rule == "downbeat_consonance":
        return _check_downbeat_consonance(score, ec)
    elif ec.rule == "no_parallel_octaves":
        return _check_no_parallel_octaves(score, ec)
    elif ec.rule == "no_frequency_collision":
        return _check_no_frequency_collision(score, ec)
    elif ec.rule == "bass_below_melody":
        return _check_bass_below_melody(score, ec)
    return []


def _get_instrument_notes(score: ScoreIR, instrument: str) -> list[Note]:
    """Get all notes for an instrument across all sections."""
    notes: list[Note] = []
    for section in score.sections:
        for part in section.parts:
            if part.instrument == instrument:
                notes.extend(part.notes)
    return sorted(notes, key=lambda n: n.start_beat)


def _get_all_instruments(score: ScoreIR) -> list[str]:
    """Get unique instruments in the score."""
    instruments: set[str] = set()
    for section in score.sections:
        for part in section.parts:
            instruments.add(part.instrument)
    return sorted(instruments)


def _instrument_pairs(score: ScoreIR, ec: EnsembleConstraint) -> list[tuple[str, str]]:
    """Determine which instrument pairs to check."""
    if len(ec.instruments) >= 2:
        # Explicit instrument list → all pairwise combinations
        pairs = []
        for i, a in enumerate(ec.instruments):
            for b in ec.instruments[i + 1 :]:
                pairs.append((a, b))
        return pairs
    # All pairs in the score
    instruments = _get_all_instruments(score)
    pairs = []
    for i, a in enumerate(instruments):
        for b in instruments[i + 1 :]:
            pairs.append((a, b))
    return pairs


def _check_register_separation(score: ScoreIR, ec: EnsembleConstraint) -> list[LintResult]:
    """Check that instruments maintain minimum register separation."""
    min_sep = ec.parameters.get("min_separation_semitones", 12.0)
    results: list[LintResult] = []

    for instr_a, instr_b in _instrument_pairs(score, ec):
        notes_a = _get_instrument_notes(score, instr_a)
        notes_b = _get_instrument_notes(score, instr_b)
        if not notes_a or not notes_b:
            continue

        avg_a = sum(n.pitch for n in notes_a) / len(notes_a)
        avg_b = sum(n.pitch for n in notes_b) / len(notes_b)
        separation = abs(avg_a - avg_b)

        if separation < min_sep:
            results.append(
                LintResult(
                    rule="ensemble:register_separation",
                    severity=ec.severity,  # type: ignore[arg-type]
                    message=(
                        f"Instruments '{instr_a}' and '{instr_b}' have only "
                        f"{separation:.1f} semitones average separation "
                        f"(minimum: {min_sep:.0f}). Risk of frequency masking."
                    ),
                    location="global",
                )
            )
    return results


def _check_downbeat_consonance(score: ScoreIR, ec: EnsembleConstraint) -> list[LintResult]:
    """Check bass-melody consonance on downbeats."""
    results: list[LintResult] = []
    consonant_intervals = {0, 3, 4, 5, 7, 8, 9, 12}  # unison, 3rd, 4th, 5th, octave

    instruments = _get_all_instruments(score)
    if len(instruments) < 2:
        return results

    # Find bass and melody by register
    instr_notes = {i: _get_instrument_notes(score, i) for i in instruments}
    avg_pitches = {i: (sum(n.pitch for n in ns) / len(ns) if ns else 60) for i, ns in instr_notes.items()}
    sorted_instrs = sorted(avg_pitches.keys(), key=lambda i: avg_pitches[i])
    bass_instr = sorted_instrs[0]
    melody_instr = sorted_instrs[-1]

    if bass_instr == melody_instr:
        return results

    bass_notes = instr_notes[bass_instr]
    melody_notes = instr_notes[melody_instr]

    # Check downbeats (beats 0, 4, 8, ...)
    beats_per_bar = 4.0  # assume 4/4
    for bass_note in bass_notes:
        if bass_note.start_beat % beats_per_bar != 0:
            continue
        # Find melody note at same beat
        for mel_note in melody_notes:
            if abs(mel_note.start_beat - bass_note.start_beat) < 0.1:
                interval = abs(mel_note.pitch - bass_note.pitch) % 12
                if interval not in consonant_intervals:
                    results.append(
                        LintResult(
                            rule="ensemble:downbeat_consonance",
                            severity=ec.severity,  # type: ignore[arg-type]
                            message=(
                                f"Dissonant interval ({interval} semitones) between "
                                f"'{bass_instr}' and '{melody_instr}' at beat {bass_note.start_beat:.0f}."
                            ),
                            location=f"beat {bass_note.start_beat:.0f}",
                        )
                    )
                break

    return results


def _check_no_parallel_octaves(score: ScoreIR, ec: EnsembleConstraint) -> list[LintResult]:
    """Check for parallel octaves between instrument pairs."""
    results: list[LintResult] = []

    for instr_a, instr_b in _instrument_pairs(score, ec):
        notes_a = _get_instrument_notes(score, instr_a)
        notes_b = _get_instrument_notes(score, instr_b)
        if not notes_a or not notes_b:
            continue

        # Find simultaneous note pairs
        for i in range(len(notes_a) - 1):
            na1 = notes_a[i]
            na2 = notes_a[i + 1] if i + 1 < len(notes_a) else None
            if na2 is None:
                break

            # Find corresponding notes in instrument B
            nb1 = None
            nb2 = None
            for nb in notes_b:
                if abs(nb.start_beat - na1.start_beat) < 0.1:
                    nb1 = nb
                if abs(nb.start_beat - na2.start_beat) < 0.1:
                    nb2 = nb

            if nb1 and nb2:
                interval1 = abs(na1.pitch - nb1.pitch) % 12
                interval2 = abs(na2.pitch - nb2.pitch) % 12
                if interval1 == 0 and interval2 == 0:
                    motion_a = na2.pitch - na1.pitch
                    motion_b = nb2.pitch - nb1.pitch
                    if motion_a == motion_b and motion_a != 0:
                        results.append(
                            LintResult(
                                rule="ensemble:no_parallel_octaves",
                                severity=ec.severity,  # type: ignore[arg-type]
                                message=(
                                    f"Parallel octaves between '{instr_a}' and '{instr_b}' "
                                    f"at beats {na1.start_beat:.1f}→{na2.start_beat:.1f}."
                                ),
                                location=f"beat {na1.start_beat:.1f}",
                            )
                        )
                        break  # One finding per pair is enough

    return results


def _check_no_frequency_collision(score: ScoreIR, ec: EnsembleConstraint) -> list[LintResult]:
    """Check that active instrument pairs don't overlap excessively in pitch space."""
    max_overlap = ec.parameters.get("max_overlap_ratio", 0.6)
    results: list[LintResult] = []

    for instr_a, instr_b in _instrument_pairs(score, ec):
        notes_a = _get_instrument_notes(score, instr_a)
        notes_b = _get_instrument_notes(score, instr_b)
        if not notes_a or not notes_b:
            continue

        range_a = (min(n.pitch for n in notes_a), max(n.pitch for n in notes_a))
        range_b = (min(n.pitch for n in notes_b), max(n.pitch for n in notes_b))

        overlap_low = max(range_a[0], range_b[0])
        overlap_high = min(range_a[1], range_b[1])
        if overlap_high <= overlap_low:
            continue

        overlap_size = overlap_high - overlap_low
        smaller_range = min(range_a[1] - range_a[0], range_b[1] - range_b[0])
        if smaller_range <= 0:
            continue

        overlap_ratio = overlap_size / smaller_range
        if overlap_ratio > max_overlap:
            results.append(
                LintResult(
                    rule="ensemble:no_frequency_collision",
                    severity=ec.severity,  # type: ignore[arg-type]
                    message=(
                        f"Instruments '{instr_a}' (range {range_a[0]}-{range_a[1]}) and "
                        f"'{instr_b}' (range {range_b[0]}-{range_b[1]}) overlap "
                        f"{overlap_ratio:.0%} (max: {max_overlap:.0%})."
                    ),
                    location="global",
                )
            )
    return results


def _check_bass_below_melody(score: ScoreIR, ec: EnsembleConstraint) -> list[LintResult]:
    """Check that the bass instrument stays below the melody in register."""
    results: list[LintResult] = []
    instruments = _get_all_instruments(score)
    if len(instruments) < 2:
        return results

    instr_notes = {i: _get_instrument_notes(score, i) for i in instruments}
    avg_pitches = {i: (sum(n.pitch for n in ns) / len(ns) if ns else 60) for i, ns in instr_notes.items()}
    sorted_instrs = sorted(avg_pitches.keys(), key=lambda i: avg_pitches[i])

    bass_instr = sorted_instrs[0]
    melody_instr = sorted_instrs[-1]

    if bass_instr == melody_instr:
        return results

    bass_notes = instr_notes[bass_instr]
    instr_notes[melody_instr]

    # Check if any bass note is above average melody pitch
    melody_avg = avg_pitches[melody_instr]
    violations = [n for n in bass_notes if n.pitch > melody_avg]
    if violations:
        results.append(
            LintResult(
                rule="ensemble:bass_below_melody",
                severity=ec.severity,  # type: ignore[arg-type]
                message=(
                    f"Bass instrument '{bass_instr}' has {len(violations)} notes above "
                    f"melody average ({melody_avg:.0f}). Bass should stay in lower register."
                ),
                location="global",
            )
        )

    return results
