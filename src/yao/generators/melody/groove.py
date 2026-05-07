"""Groove integration for the phrase-first melody pipeline.

Provides rhythm template loading, groove profile resolution, and
ghost note insertion. Bridges the GrooveProfile system (ir/groove.py)
with the melody pipeline's Layer M4 (OrnamentEngine).

See IMPROVEMENT.md §4.5 and PROJECT.md §3.2 (Layer M4).
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

from yao.ir.groove import GrooveProfile
from yao.ir.melody_line import MelodyLine, MelodyNote
from yao.schema.melodic_profile import MelodicProfile, RhythmTemplate
from yao.types import MidiNote


def load_groove_profile(name: str) -> GrooveProfile:
    """Load a GrooveProfile from the grooves/ directory.

    Args:
        name: Profile name matching a YAML file (e.g., "jazz_swing").

    Returns:
        A GrooveProfile instance.

    Raises:
        FileNotFoundError: If the groove file doesn't exist.
    """
    grooves_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "grooves"
    path = grooves_dir / f"{name}.yaml"

    if not path.exists():
        # Try alternate locations
        alt_dir = Path(__file__).resolve().parent.parent / "constants" / "grooves"
        alt_path = alt_dir / f"{name}.yaml"
        if alt_path.exists():
            path = alt_path
        else:
            # Return a default straight profile
            return GrooveProfile(name=name)

    with open(path) as f:
        data = yaml.safe_load(f)

    return GrooveProfile(
        name=data.get("name", name),
        microtiming={int(k): float(v) for k, v in data.get("microtiming", {}).items()},
        velocity_pattern={int(k): float(v) for k, v in data.get("velocity_pattern", {}).items()},
        ghost_probability=float(data.get("ghost_probability", 0.0)),
        swing_ratio=float(data.get("swing_ratio", 0.5)),
        timing_jitter_sigma=float(data.get("timing_jitter_sigma", 0.0)),
        apply_to_all_instruments=data.get("apply_to_all_instruments", True),
    )


def load_rhythm_template(genre: str, role: str = "melody") -> RhythmTemplate | None:
    """Load a rhythm template from the constants/rhythms/ directory.

    Args:
        genre: Genre identifier to search for.
        role: Instrument role to filter by.

    Returns:
        A matching RhythmTemplate, or None if not found.
    """
    rhythms_dir = Path(__file__).resolve().parent.parent / "constants" / "rhythms"
    if not rhythms_dir.exists():
        return None

    for path in sorted(rhythms_dir.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            continue
        template_genre = data.get("genre", "")
        applies_to = data.get("applies_to", [])
        if genre in template_genre and (not applies_to or role in applies_to):
            return RhythmTemplate(
                name=data.get("name", path.stem),
                pattern=data.get("beat_positions", []),
                durations=data.get("duration_pattern", []),
                swing_ratio=float(data.get("swing_ratio", 0.5)),
                syncopation_level=float(data.get("syncopation_level", 0.0)),
            )

    return None


def add_ghost_notes(
    melody: MelodyLine,
    profile: MelodicProfile,
    rng: random.Random,
) -> MelodyLine:
    """Add ghost notes around strong-beat targets.

    Ghost notes are low-velocity decorative notes placed just before
    or after strong-beat notes, adding rhythmic depth. Important for
    funk, R&B, hip-hop, and certain jazz contexts.

    Args:
        melody: The melody to augment.
        profile: MelodicProfile with ghost_note_probability.
        rng: Random number generator.

    Returns:
        A new MelodyLine with ghost notes inserted.
    """
    ghost_prob = profile.ornament_profile.ghost_note_probability
    if ghost_prob <= 0:
        return melody

    new_notes: list[MelodyNote] = list(melody.notes)

    for note in melody.notes:
        if rng.random() >= ghost_prob:
            continue

        # Place ghost note just before the main note
        ghost_beat = note.beat - 0.0833  # 1/12 beat earlier
        if ghost_beat < 0:
            ghost_beat = note.beat + note.duration_beats  # after instead

        # Ghost pitch: half-step below or same pitch
        ghost_pitch: MidiNote = note.midi_pitch - rng.choice([0, 1, 2])
        ghost_pitch = max(0, min(127, ghost_pitch))

        ghost = MelodyNote(
            bar=note.bar,
            beat=round(ghost_beat, 4),
            duration_beats=0.0833,
            midi_pitch=ghost_pitch,
            velocity=int(note.velocity * 0.35),
            note_type="ghost",
            skeleton_id=note.skeleton_id,
        )
        new_notes.append(ghost)

    # Sort by position
    new_notes.sort(key=lambda n: (n.bar, n.beat))
    return MelodyLine(notes=tuple(new_notes))


def measure_swing_ratio(melody: MelodyLine) -> float:
    """Measure the effective swing ratio of a melody.

    Examines consecutive note pairs that start near downbeats (0, 1, 2, 3)
    and measures the duration ratio of the first note to the total pair.
    Straight 8ths give 0.5; triplet swing gives ~0.67.

    Args:
        melody: The melody to analyze.

    Returns:
        Swing ratio in [0.5, 0.75]. 0.5 = straight, 0.67 = triplet swing.
    """
    if melody.note_count < 2:  # noqa: PLR2004
        return 0.5

    ratios: list[float] = []
    sorted_notes = sorted(melody.notes, key=lambda n: (n.bar, n.beat))

    for i in range(0, len(sorted_notes) - 1, 2):
        curr = sorted_notes[i]
        nxt = sorted_notes[i + 1]

        # Check if curr is near a beat boundary (downbeat of an 8th pair)
        beat_in_bar = curr.beat % 1.0
        if beat_in_bar > 0.1:
            continue

        # Check that the pair spans roughly one beat
        pair_duration = (nxt.bar * 4.0 + nxt.beat + nxt.duration_beats) - (curr.bar * 4.0 + curr.beat)
        if not 0.8 <= pair_duration <= 1.2:
            continue

        total = curr.duration_beats + nxt.duration_beats
        if total > 0:
            ratio = curr.duration_beats / total
            if 0.4 <= ratio <= 0.8:
                ratios.append(ratio)

    if not ratios:
        return 0.5

    return sum(ratios) / len(ratios)
