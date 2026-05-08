"""Voice-Leading Optimizer — minimum-motion voicing transitions.

Implements ``optimal_voicing_transition()`` using a brute-force search
over inversions for small voice counts (typically 3–6 voices), selecting
the voicing that minimizes total voice motion subject to constraints.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §5.4, PROJECT.md §3.4.2, CLAUDE.md Phase 3.5 Step 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from yao.constants.music import CHORD_INTERVALS
from yao.ir.voicing import Voicing, check_parallel_fifths, check_parallel_octaves
from yao.types import MidiNote


@dataclass(frozen=True)
class VoicingConstraints:
    """Constraints for voice-leading optimization.

    Attributes:
        no_parallel_fifths: Reject voicings creating parallel fifths.
        no_parallel_octaves: Reject voicings creating parallel octaves.
        no_voice_crossing: Reject voicings where voices cross.
        max_leap: Maximum leap in semitones for any single voice.
        voice_ranges: Per-voice (low, high) MIDI ranges. If None, defaults used.
    """

    no_parallel_fifths: bool = True
    no_parallel_octaves: bool = True
    no_voice_crossing: bool = True
    max_leap: int = 12
    voice_ranges: tuple[tuple[int, int], ...] | None = None


# Default voice ranges for SATB-style voicing
_DEFAULT_RANGES: tuple[tuple[int, int], ...] = (
    (40, 60),  # bass
    (48, 67),  # tenor
    (55, 74),  # alto
    (60, 81),  # soprano
    (64, 84),  # soprano 2 (if 5+ voices)
    (67, 88),  # soprano 3 (if 6+ voices)
)


def optimal_voicing_transition(
    prev_voicing: list[MidiNote],
    next_chord_root: str,
    next_chord_quality: str,
    voice_count: int = 4,
    constraints: VoicingConstraints | None = None,
) -> list[MidiNote]:
    """Choose the next chord's voicing that minimizes total voice motion.

    This is the single entry point for voicing optimization.
    Never write ad-hoc voicing code — always call this function.

    Algorithm:
    1. Enumerate all inversions/octave placements of next_chord within ranges.
    2. Filter out voicings violating constraints.
    3. Return the minimum-motion candidate.
    4. Deterministic tie-breaking: lowest top-voice note wins.

    Args:
        prev_voicing: Previous voicing as a list of MIDI notes (lowest to highest).
        next_chord_root: Root note name of the next chord (e.g., "C", "G").
        next_chord_quality: Chord quality (e.g., "maj", "min7", "dom7").
        voice_count: Number of voices (default 4).
        constraints: Voicing constraints. If None, uses defaults.

    Returns:
        List of MIDI notes for the optimal voicing (lowest to highest).
    """
    if constraints is None:
        constraints = VoicingConstraints()

    # Get chord intervals
    chord_intervals = CHORD_INTERVALS.get(next_chord_quality, (0, 4, 7))
    root_pc = _note_name_to_pc(next_chord_root)

    # Get voice ranges
    ranges = constraints.voice_ranges or _DEFAULT_RANGES[:voice_count]
    if len(ranges) < voice_count:
        ranges = ranges + _DEFAULT_RANGES[len(ranges) : voice_count]

    # Generate pitch classes for the chord
    chord_pcs = [(root_pc + iv) % 12 for iv in chord_intervals]

    # For each voice, find all possible pitches from chord pitch classes within range
    voice_options: list[list[int]] = []
    for voice_idx in range(voice_count):
        low, high = ranges[voice_idx] if voice_idx < len(ranges) else (40, 84)
        options: list[int] = []
        for pc in chord_pcs:
            # Find all octave instances of this PC within range
            midi = pc
            while midi < low:
                midi += 12
            while midi <= high:
                options.append(midi)
                midi += 12
        voice_options.append(sorted(set(options)))

    if not all(voice_options):
        # If any voice has no options, return prev_voicing padded/truncated
        return list(prev_voicing[:voice_count])

    # Enumerate candidate voicings (limit search space)
    best_voicing: list[int] | None = None
    best_motion = float("inf")

    prev = prev_voicing[:voice_count]
    while len(prev) < voice_count:
        prev.append(prev[-1] if prev else 60)

    prev_voicing_obj = Voicing(pitches=tuple(sorted(prev)))

    # For tractability, limit candidates per voice
    max_per_voice = 8
    trimmed_options = [opts[:max_per_voice] for opts in voice_options]

    for combo in product(*trimmed_options):
        voicing = sorted(combo)

        # Check voice crossing
        if constraints.no_voice_crossing and voicing != list(combo):
            # Voices crossed if sorted order differs from assignment order
            # But we want voices in ascending order, so we just check sorted is valid
            pass  # sorted voicing is by definition non-crossing

        # Check max leap
        leap_ok = all(abs(voicing[i] - prev[i]) <= constraints.max_leap for i in range(min(len(voicing), len(prev))))
        if not leap_ok:
            continue

        voicing_obj = Voicing(pitches=tuple(voicing))

        # Check parallel fifths
        if constraints.no_parallel_fifths and check_parallel_fifths(prev_voicing_obj, voicing_obj):
            continue

        # Check parallel octaves
        if constraints.no_parallel_octaves and check_parallel_octaves(prev_voicing_obj, voicing_obj):
            continue

        # Compute total motion
        motion = sum(abs(voicing[i] - prev[i]) for i in range(voice_count))

        # Tie-breaking: prefer lower top voice for determinism
        is_better = motion < best_motion or (
            motion == best_motion and best_voicing is not None and voicing[-1] < best_voicing[-1]
        )
        if is_better:
            best_motion = motion
            best_voicing = voicing

    if best_voicing is None:
        # Fallback: use closest available pitches
        return _fallback_voicing(prev, chord_pcs, ranges, voice_count)

    return best_voicing


def _note_name_to_pc(name: str) -> int:
    """Convert a note name to pitch class (0-11)."""
    from yao.constants.music import ENHARMONIC_MAP, NOTE_NAMES

    normalized = name[0].upper() + name[1:] if len(name) > 1 else name.upper()
    if normalized in ENHARMONIC_MAP:
        normalized = ENHARMONIC_MAP[normalized]
    return NOTE_NAMES.index(normalized) if normalized in NOTE_NAMES else 0


def _fallback_voicing(
    prev: list[int],
    chord_pcs: list[int],
    ranges: tuple[tuple[int, int], ...],
    voice_count: int,
) -> list[int]:
    """Generate a fallback voicing when no constraint-satisfying option exists."""
    result: list[int] = []
    for i in range(voice_count):
        target = prev[i] if i < len(prev) else 60
        low, high = ranges[i] if i < len(ranges) else (40, 84)
        # Find nearest chord tone to the target within range
        best_pitch = target
        best_dist = float("inf")
        for pc in chord_pcs:
            midi = pc
            while midi < low:
                midi += 12
            while midi <= high:
                dist = abs(midi - target)
                if dist < best_dist:
                    best_dist = dist
                    best_pitch = midi
                midi += 12
        result.append(best_pitch)
    return sorted(result)
