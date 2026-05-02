"""Counter-melody generator following species counterpoint principles.

Produces a secondary melodic line that:
- Maintains consonance on strong beats with the main melody
- Prefers contrary motion when the main melody leaps
- Avoids parallel fifths and octaves
- Stays within the target instrument's range
- Has lower note density than the main melody (density_factor)

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random

from yao.constants.instruments import INSTRUMENT_RANGES, InstrumentRange
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part
from yao.reflect.provenance import ProvenanceLog

# Consonant intervals with the main melody (in semitones mod 12).
# Perfect consonances (P1, P5, P8) + imperfect consonances (m3, M3, m6, M6).
_CONSONANT_INTERVALS = {0, 3, 4, 5, 7, 8, 9}


def generate_counter_melody(
    main_part: Part,
    target_instrument: str,
    key: str,
    tempo_bpm: float,
    time_signature: str,
    density_factor: float = 0.5,
    seed: int = 42,
) -> tuple[Part, ProvenanceLog]:
    """Generate a counter-melody to accompany a main melody part.

    Uses species counterpoint principles:
    1. Strong-beat notes must be consonant with the main melody
    2. Contrary motion is preferred when the main melody moves
    3. Parallel fifths and octaves are avoided
    4. Notes stay within the target instrument's range

    Args:
        main_part: The main melody Part to counter.
        target_instrument: Instrument name for the counter-melody.
        key: Key signature (e.g., "C major").
        tempo_bpm: Tempo in BPM.
        time_signature: Time signature string.
        density_factor: Note density relative to main (0.0-1.0).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (counter-melody Part, ProvenanceLog).
    """
    provenance = ProvenanceLog()
    rng = random.Random(seed)

    root_note, scale_type = parse_key(key)
    inst_range = INSTRUMENT_RANGES.get(target_instrument)

    # Build scale pitches across a wide range for candidate selection
    candidates_scale = _build_scale_range(root_note, scale_type, inst_range)

    main_notes = list(main_part.notes)
    counter_notes: list[Note] = []

    provenance.record(
        layer="generator",
        operation="counter_melody_start",
        parameters={
            "main_instrument": main_part.instrument,
            "target_instrument": target_instrument,
            "main_notes": len(main_notes),
            "density_factor": density_factor,
        },
        source="counter_melody.generate_counter_melody",
        rationale=f"Generating counter-melody for {main_part.instrument} on {target_instrument}.",
    )

    for i, main_note in enumerate(main_notes):
        # Density control: skip notes probabilistically
        if rng.random() > density_factor:
            continue

        is_strong = _is_strong_beat(main_note.start_beat, time_signature)

        # Find candidate pitches: scale tones in instrument range
        candidates = list(candidates_scale)

        # Filter for consonance on strong beats
        if is_strong:
            candidates = [p for p in candidates if (abs(p - main_note.pitch) % 12) in _CONSONANT_INTERVALS]

        # Filter for instrument range
        if inst_range is not None:
            candidates = [p for p in candidates if inst_range.midi_low <= p <= inst_range.midi_high]

        # Avoid unison with main melody
        candidates = [p for p in candidates if p != main_note.pitch]

        # Parallel motion filter
        if counter_notes and i > 0:
            prev_main = main_notes[i - 1]
            prev_counter = counter_notes[-1]
            candidates = _filter_parallels(
                candidates,
                main_note.pitch,
                prev_main.pitch,
                prev_counter.pitch,
            )

        if not candidates:
            provenance.record(
                layer="generator",
                operation="counter_melody_rest",
                parameters={"beat": main_note.start_beat, "reason": "no valid candidates"},
                source="counter_melody.generate_counter_melody",
                rationale="No consonant, non-parallel candidate found; inserting rest.",
            )
            continue

        # Prefer contrary motion
        chosen = _select_contrary_motion(
            candidates,
            main_note.pitch,
            main_notes[i - 1].pitch if i > 0 else None,
            counter_notes[-1].pitch if counter_notes else None,
            rng,
        )

        counter_notes.append(
            Note(
                pitch=chosen,
                start_beat=main_note.start_beat,
                duration_beats=main_note.duration_beats,
                velocity=max(1, int(main_note.velocity * 0.8)),
                instrument=target_instrument,
            )
        )

    provenance.record(
        layer="generator",
        operation="counter_melody_complete",
        parameters={
            "counter_notes": len(counter_notes),
            "density_achieved": len(counter_notes) / max(len(main_notes), 1),
        },
        source="counter_melody.generate_counter_melody",
        rationale=f"Generated {len(counter_notes)} counter-melody notes.",
    )

    return Part(instrument=target_instrument, notes=tuple(counter_notes)), provenance


def _build_scale_range(
    root_note: str,
    scale_type: str,
    inst_range: InstrumentRange | None,
) -> list[int]:
    """Build scale pitches across a wide range for candidate selection."""
    pitches: list[int] = []
    for octave in range(2, 7):
        pitches.extend(scale_notes(root_note, scale_type, octave))
    # Filter to instrument range if available
    if inst_range is not None:
        pitches = [p for p in pitches if inst_range.midi_low <= p <= inst_range.midi_high]
    return sorted(set(pitches))


def _is_strong_beat(beat: float, time_signature: str) -> bool:
    """Check if a beat position is a strong beat."""
    parts = time_signature.split("/")
    beats_per_bar = int(parts[0]) if len(parts) == 2 else 4  # noqa: PLR2004
    beat_in_bar = beat % beats_per_bar
    # Beat 1 and beat 3 (in 4/4) are strong
    return beat_in_bar % 2 < 0.01


def _filter_parallels(
    candidates: list[int],
    main_curr: int,
    main_prev: int,
    counter_prev: int,
) -> list[int]:
    """Remove candidates that would create parallel fifths or octaves."""
    filtered = []
    for c in candidates:
        # Check interval between main and counter in both positions
        prev_interval = (main_prev - counter_prev) % 12
        curr_interval = (main_curr - c) % 12

        # Both P5 (7 semitones) and similar motion → parallel fifth
        main_motion = main_curr - main_prev
        counter_motion = c - counter_prev
        similar = main_motion != 0 and counter_motion != 0 and (main_motion > 0) == (counter_motion > 0)

        if prev_interval == 7 and curr_interval == 7 and similar:
            continue  # parallel fifth
        if prev_interval == 0 and curr_interval == 0 and similar:
            continue  # parallel unison/octave

        filtered.append(c)

    return filtered if filtered else candidates  # fallback to all if everything filtered


def _select_contrary_motion(
    candidates: list[int],
    main_curr: int,
    main_prev: int | None,
    counter_prev: int | None,
    rng: random.Random,
) -> int:
    """Select a candidate pitch that moves contrary to the main melody."""
    if main_prev is None or counter_prev is None:
        return rng.choice(candidates)

    main_direction = main_curr - main_prev

    if main_direction == 0:
        # Main melody stays — pick something close to previous counter
        closest = min(candidates, key=lambda c: abs(c - counter_prev))
        return closest

    # Contrary: if main goes up, counter should go down (and vice versa)
    contrary = [c for c in candidates if (c - counter_prev) * main_direction < 0]
    if contrary:
        # Prefer stepwise contrary motion
        closest_contrary = min(contrary, key=lambda c: abs(c - counter_prev))
        return closest_contrary

    # Oblique motion (counter stays) as fallback
    oblique = [c for c in candidates if abs(c - counter_prev) <= 2]  # noqa: PLR2004
    if oblique:
        return rng.choice(oblique)

    return rng.choice(candidates)
