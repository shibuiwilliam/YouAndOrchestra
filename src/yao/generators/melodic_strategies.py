"""Melodic Generation Strategies — diverse approaches to melody creation.

Addresses Mode Collapse (CLAUDE.md §22 failure mode #1) by providing
8 distinct melodic generation strategies. The stochastic generator's
existing behavior maps to "contour_based" for backward compatibility.

Each strategy is a function that produces a sequence of MIDI pitches
given a starting pitch, key, scale, and parameters.

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

import random
from enum import StrEnum

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.notation import parse_key, scale_notes
from yao.types import MidiNote


class MelodicGenerationStrategy(StrEnum):
    """Available melodic generation strategies.

    Each strategy produces melodies with distinct characteristics:
    - contour_based: Shapes melody by arch/ascending/descending contours (existing default)
    - motif_development: Develops a short motif through transposition, inversion, augmentation
    - linear_voice: Stepwise motion with occasional leaps; classical voice-leading
    - arpeggiated: Derives pitches from broken chord patterns
    - scalar_runs: Runs up/down the scale in sequences
    - call_response: Alternates between question and answer phrases
    - pedal_tone: Melody revolves around a repeated pedal note
    - hocketing: Distributes melody across register gaps (high-low alternation)
    """

    CONTOUR_BASED = "contour_based"
    MOTIF_DEVELOPMENT = "motif_development"
    LINEAR_VOICE = "linear_voice"
    ARPEGGIATED = "arpeggiated"
    SCALAR_RUNS = "scalar_runs"
    CALL_RESPONSE = "call_response"
    PEDAL_TONE = "pedal_tone"
    HOCKETING = "hocketing"


def generate_melody_pitches(
    strategy: MelodicGenerationStrategy,
    n_notes: int,
    key: str,
    root_midi: int,
    instrument: str = "piano",
    seed: int = 42,
    temperature: float = 0.5,
) -> list[MidiNote]:
    """Generate a sequence of melody pitches using the specified strategy.

    Args:
        strategy: Which melodic strategy to use.
        n_notes: Number of pitches to generate.
        key: Key signature (e.g., "C major", "A minor").
        root_midi: MIDI note number for the root of the key.
        instrument: Instrument name for range constraints.
        seed: Random seed for reproducibility.
        temperature: Controls variation (0=conservative, 1=adventurous).

    Returns:
        List of MIDI note numbers.
    """
    rng = random.Random(seed)
    scale = _get_scale_pitches(key, root_midi)
    inst_range = INSTRUMENT_RANGES.get(instrument)
    low = inst_range.midi_low if inst_range else 48
    high = inst_range.midi_high if inst_range else 84

    dispatch = {
        MelodicGenerationStrategy.CONTOUR_BASED: _contour_based,
        MelodicGenerationStrategy.MOTIF_DEVELOPMENT: _motif_development,
        MelodicGenerationStrategy.LINEAR_VOICE: _linear_voice,
        MelodicGenerationStrategy.ARPEGGIATED: _arpeggiated,
        MelodicGenerationStrategy.SCALAR_RUNS: _scalar_runs,
        MelodicGenerationStrategy.CALL_RESPONSE: _call_response,
        MelodicGenerationStrategy.PEDAL_TONE: _pedal_tone,
        MelodicGenerationStrategy.HOCKETING: _hocketing,
    }

    fn = dispatch[strategy]
    pitches = fn(n_notes, scale, root_midi, low, high, rng, temperature)
    return [_clamp(p, low, high) for p in pitches]


def _get_scale_pitches(key: str, root_midi: int) -> list[int]:
    """Get scale pitches in the octave around root_midi."""
    try:
        root_name, scale_type = parse_key(key)
        octave = root_midi // 12 - 1  # MIDI to octave
        notes = scale_notes(root_name, scale_type, octave=max(1, octave))
        return list(notes)
    except Exception:
        # Fallback: major scale from root
        intervals = [0, 2, 4, 5, 7, 9, 11]
        base = root_midi - (root_midi % 12)
        return [base + i for i in intervals]


def _clamp(pitch: int, low: int, high: int) -> int:
    """Clamp pitch to range, adjusting by octave if needed."""
    while pitch < low:
        pitch += 12
    while pitch > high:
        pitch -= 12
    return max(low, min(high, pitch))


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------


def _contour_based(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Arch/ascending/descending contour shaping."""
    pitches: list[int] = []
    current = root
    mid = n // 2
    for i in range(n):
        if i < mid:
            # Ascending phase
            step = rng.choice([1, 2]) if rng.random() < 0.5 + temp * 0.3 else 0
            current += step
        else:
            # Descending phase
            step = rng.choice([-1, -2]) if rng.random() < 0.5 + temp * 0.3 else 0
            current += step
        # Snap to nearest scale tone
        pitches.append(_nearest_scale(current, scale))
    return pitches


def _motif_development(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Develop a short motif through transposition, inversion, augmentation."""
    # Generate a short motif (3-5 notes)
    motif_len = rng.randint(3, 5)
    motif: list[int] = [root]
    for _ in range(motif_len - 1):
        interval = rng.choice([-2, -1, 1, 2, 3, 4])
        motif.append(motif[-1] + interval)

    # Develop by repeating with transformations
    pitches: list[int] = []
    transformations = ["identity", "transpose_up", "transpose_down", "invert", "retrograde"]
    while len(pitches) < n:
        transform = rng.choice(transformations)
        variant = _apply_motif_transform(motif, transform, rng)
        pitches.extend(variant)

    return [_nearest_scale(p, scale) for p in pitches[:n]]


def _linear_voice(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Stepwise motion with occasional leaps (voice-leading style)."""
    pitches: list[int] = [root]
    for _ in range(n - 1):
        if rng.random() < 0.8 - temp * 0.3:
            # Stepwise (±1-2 semitones)
            step = rng.choice([-2, -1, 1, 2])
        else:
            # Occasional leap (±3-7 semitones)
            step = rng.choice([-7, -5, -4, -3, 3, 4, 5, 7])
        pitches.append(pitches[-1] + step)
    return [_nearest_scale(p, scale) for p in pitches]


def _arpeggiated(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Broken chord patterns (arpeggios)."""
    # Common chord intervals from root
    chord_patterns = [
        [0, 4, 7],  # major triad
        [0, 3, 7],  # minor triad
        [0, 4, 7, 11],  # major 7th
        [0, 3, 7, 10],  # minor 7th
        [0, 4, 7, 10],  # dominant 7th
    ]
    pitches: list[int] = []
    base = root
    while len(pitches) < n:
        pattern = rng.choice(chord_patterns)
        direction = rng.choice(["up", "down", "up_down"])
        notes = [base + i for i in pattern]
        if direction == "down":
            notes = list(reversed(notes))
        elif direction == "up_down":
            notes = notes + list(reversed(notes[1:-1]))
        pitches.extend(notes)
        # Move to next chord root
        base += rng.choice([-5, -3, -2, 2, 3, 5, 7])
    return [_nearest_scale(p, scale) for p in pitches[:n]]


def _scalar_runs(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Runs up/down the scale in sequences."""
    pitches: list[int] = []
    current = root
    direction = 1  # 1 = up, -1 = down
    run_length = rng.randint(3, 6)
    count = 0

    while len(pitches) < n:
        pitches.append(current)
        current += direction * rng.choice([1, 2])
        count += 1
        if count >= run_length:
            # Change direction or start new run
            direction *= -1
            run_length = rng.randint(3, 6)
            count = 0
            # Occasionally shift start
            if rng.random() < temp * 0.5:
                current += rng.choice([-3, -2, 2, 3])

    return [_nearest_scale(p, scale) for p in pitches[:n]]


def _call_response(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Alternating question and answer phrases."""
    pitches: list[int] = []
    phrase_len = max(2, n // 4)

    while len(pitches) < n:
        # "Call" phrase — ascends, ends on non-root
        call: list[int] = [root]
        for _ in range(phrase_len - 1):
            call.append(call[-1] + rng.choice([1, 2, 3]))

        # "Response" phrase — descends, resolves to root/fifth
        response: list[int] = [call[-1]]
        for _ in range(phrase_len - 1):
            response.append(response[-1] + rng.choice([-1, -2, -3]))

        pitches.extend(call)
        pitches.extend(response)

    return [_nearest_scale(p, scale) for p in pitches[:n]]


def _pedal_tone(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Melody revolves around a repeated pedal note."""
    pedal = root
    pitches: list[int] = []
    for i in range(n):
        if i % 2 == 0 or rng.random() < 0.3:
            # Return to pedal
            pitches.append(pedal)
        else:
            # Depart from pedal
            departure = rng.choice([-5, -4, -3, -2, 2, 3, 4, 5, 7])
            pitches.append(pedal + departure)
    return [_nearest_scale(p, scale) for p in pitches]


def _hocketing(
    n: int,
    scale: list[int],
    root: int,
    low: int,
    high: int,
    rng: random.Random,
    temp: float,
) -> list[int]:
    """Distributes melody across register gaps (high-low alternation)."""
    pitches: list[int] = []
    high_register = root + 12
    low_register = root - 5
    use_high = True

    for _ in range(n):
        if use_high:
            pitch = high_register + rng.choice([-2, -1, 0, 1, 2, 3])
            high_register = pitch
        else:
            pitch = low_register + rng.choice([-2, -1, 0, 1, 2])
            low_register = pitch
        pitches.append(pitch)
        # Alternate with some randomness
        if rng.random() < 0.7:
            use_high = not use_high

    return [_nearest_scale(p, scale) for p in pitches]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _nearest_scale(pitch: int, scale: list[int]) -> int:
    """Snap a pitch to the nearest scale tone."""
    if not scale:
        return pitch
    pc = pitch % 12
    octave = pitch // 12
    scale_pcs = [s % 12 for s in scale]

    # Find nearest pitch class in scale
    best_pc = min(scale_pcs, key=lambda s: min(abs(s - pc), 12 - abs(s - pc)))
    result = octave * 12 + best_pc

    # Check if the adjacent octave is closer
    if abs(result - pitch) > abs(result + 12 - pitch):
        result += 12
    elif abs(result - pitch) > abs(result - 12 - pitch):
        result -= 12

    return result


def _apply_motif_transform(motif: list[int], transform: str, rng: random.Random) -> list[int]:
    """Apply a transformation to a motif."""
    if transform == "identity":
        return list(motif)
    elif transform == "transpose_up":
        offset = rng.choice([2, 3, 4, 5, 7])
        return [p + offset for p in motif]
    elif transform == "transpose_down":
        offset = rng.choice([2, 3, 4, 5, 7])
        return [p - offset for p in motif]
    elif transform == "invert":
        # Invert around the first note
        axis = motif[0]
        return [2 * axis - p for p in motif]
    elif transform == "retrograde":
        return list(reversed(motif))
    return list(motif)
