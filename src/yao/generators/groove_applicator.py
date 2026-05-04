"""GrooveApplicator — applies ensemble-wide groove to a ScoreIR.

This is a post-processing step between Note Realization (Step 6) and
MIDI writing (Step 7). It adjusts note start times and velocities
according to a GrooveProfile.

Order of operations in the pipeline:
  1. Note Realizer → ScoreIR
  2. DynamicsShape applies (if present)
  3. **GrooveApplicator applies** (this module)
  4. Humanize jitter applies (existing)

The GrooveApplicator must NOT be applied inside the MIDI writer.

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

import random

from yao.ir.groove import GrooveProfile
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import beats_per_bar_from_sig, parse_time_signature, seconds_to_beats
from yao.reflect.provenance import ProvenanceLog

# Instruments treated as drums/percussion for apply_to_all_instruments=False
DRUM_INSTRUMENTS = frozenset(
    {
        "drums",
        "drum_kit",
        "percussion",
        "shaker",
        "tambourine",
        "congas",
        "bongos",
        "timbales",
        "cowbell",
        "claves",
    }
)


def _beat_to_16th_position(
    beat: float,
    beats_per_bar: float,
) -> int:
    """Convert a beat position to a 16th-note position within its bar.

    Args:
        beat: Absolute beat position.
        beats_per_bar: Beats per bar for the time signature.

    Returns:
        16th-note position (0–15) within the bar.
    """
    beat_in_bar = beat % beats_per_bar
    # 16 subdivisions per bar (in 4/4: 4 beats × 4 sixteenths)
    sixteenths_per_bar = 16.0 * (beats_per_bar / 4.0)
    if sixteenths_per_bar <= 0:
        return 0
    raw_position = (beat_in_bar / beats_per_bar) * sixteenths_per_bar
    return int(round(raw_position)) % 16


def _ms_to_beats(ms: float, bpm: float) -> float:
    """Convert milliseconds to beats.

    Args:
        ms: Milliseconds.
        bpm: Tempo in beats per minute.

    Returns:
        Duration in beats.
    """
    seconds = ms / 1000.0
    return seconds_to_beats(seconds, bpm)


def apply_groove(
    score_ir: ScoreIR,
    groove: GrooveProfile,
    seed: int = 42,
) -> tuple[ScoreIR, ProvenanceLog]:
    """Apply an ensemble-wide groove to a ScoreIR.

    For each note, computes the 16th-note subdivision position within
    its bar, applies the corresponding microtiming offset and velocity
    multiplier from the GrooveProfile.

    If ``groove.apply_to_all_instruments`` is False, only drum/percussion
    parts are affected.

    Args:
        score_ir: The input ScoreIR (immutable — a new one is returned).
        groove: The GrooveProfile to apply.
        seed: Random seed for jitter reproducibility.

    Returns:
        Tuple of (grooved ScoreIR, ProvenanceLog recording the changes).

    Example:
        >>> grooved, prov = apply_groove(score_ir, lofi_profile)
        >>> assert grooved != score_ir  # note timings differ
    """
    provenance = ProvenanceLog()
    rng = random.Random(seed)

    num, den = parse_time_signature(score_ir.time_signature)
    bpb = beats_per_bar_from_sig(num, den)

    adjusted_count = 0
    new_sections: list[Section] = []

    for section in score_ir.sections:
        new_parts: list[Part] = []
        for part in section.parts:
            is_drum = part.instrument.lower() in DRUM_INSTRUMENTS
            should_groove = groove.apply_to_all_instruments or is_drum

            if not should_groove:
                new_parts.append(part)
                continue

            new_notes: list[Note] = []
            for note in part.notes:
                pos_16th = _beat_to_16th_position(note.start_beat, bpb)

                # Microtiming offset
                offset_ms = groove.microtiming_at(pos_16th)
                # Add jitter
                if groove.timing_jitter_sigma > 0:
                    jitter_ms = rng.gauss(0.0, groove.timing_jitter_sigma)
                    offset_ms += jitter_ms

                offset_beats = _ms_to_beats(offset_ms, score_ir.tempo_bpm)
                new_start = max(0.0, note.start_beat + offset_beats)

                # Velocity multiplier
                vel_mult = groove.velocity_mult_at(pos_16th)
                new_velocity = max(1, min(127, round(note.velocity * vel_mult)))

                new_note = Note(
                    pitch=note.pitch,
                    start_beat=new_start,
                    duration_beats=note.duration_beats,
                    velocity=new_velocity,
                    instrument=note.instrument,
                )
                new_notes.append(new_note)
                adjusted_count += 1

            new_parts.append(
                Part(
                    instrument=part.instrument,
                    notes=tuple(new_notes),
                )
            )
        new_sections.append(
            Section(
                name=section.name,
                start_bar=section.start_bar,
                end_bar=section.end_bar,
                parts=tuple(new_parts),
            )
        )

    grooved_ir = ScoreIR(
        title=score_ir.title,
        tempo_bpm=score_ir.tempo_bpm,
        time_signature=score_ir.time_signature,
        key=score_ir.key,
        sections=tuple(new_sections),
    )

    provenance.record(
        layer="generator",
        operation="groove_application",
        parameters={
            "groove_name": groove.name,
            "swing_ratio": groove.swing_ratio,
            "timing_jitter_sigma": groove.timing_jitter_sigma,
            "apply_to_all_instruments": groove.apply_to_all_instruments,
            "seed": seed,
        },
        source="GrooveApplicator",
        rationale=(
            f"Applied ensemble groove '{groove.name}' to "
            f"{adjusted_count} notes across "
            f"{'all instruments' if groove.apply_to_all_instruments else 'drums only'}"
        ),
    )

    return grooved_ir, provenance
