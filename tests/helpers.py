"""Music-specific test assertion helpers (CLAUDE.md §8).

These helpers make tests more readable and provide domain-specific error
messages when assertions fail.
"""

from __future__ import annotations

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.groove import GrooveProfile
from yao.ir.notation import midi_to_note_name
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR
from yao.ir.voicing import Voicing, check_parallel_fifths
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.trajectory import TrajectorySpec


def make_minimal_spec_v2(**overrides: object) -> CompositionSpecV2:
    """Create a minimal CompositionSpecV2 for testing.

    Args:
        **overrides: Keys to override in the spec dict.

    Returns:
        Validated CompositionSpecV2.
    """
    defaults: dict[str, object] = {
        "version": "2",
        "identity": {"title": "Test", "duration_sec": 60},
        "global": {"key": "C major", "bpm": 120},
        "form": {
            "sections": [
                {"id": "verse", "bars": 8},
                {"id": "chorus", "bars": 8},
            ]
        },
        "arrangement": {"instruments": {"piano": {"role": "melody"}}},
    }
    defaults.update(overrides)
    return CompositionSpecV2.model_validate(defaults)


def assert_in_range(notes: list[Note] | tuple[Note, ...], instrument: str) -> None:
    """Assert all notes are within the instrument's playable range.

    Args:
        notes: Notes to check.
        instrument: Canonical instrument name.

    Raises:
        AssertionError: If any note is out of range.
    """
    inst_range = INSTRUMENT_RANGES.get(instrument)
    if inst_range is None:
        return

    for note in notes:
        name = midi_to_note_name(note.pitch)
        assert inst_range.midi_low <= note.pitch <= inst_range.midi_high, (
            f"Note {name} (MIDI {note.pitch}) out of range for {instrument} "
            f"({inst_range.midi_low}–{inst_range.midi_high}) "
            f"at beat {note.start_beat}"
        )


def assert_no_parallel_fifths(voicings: list[Voicing]) -> None:
    """Assert no parallel perfect fifths exist between consecutive voicings.

    Args:
        voicings: Ordered list of voicings to check.

    Raises:
        AssertionError: If parallel fifths are detected.
    """
    for i in range(len(voicings) - 1):
        parallels = check_parallel_fifths(voicings[i], voicings[i + 1])
        assert not parallels, f"Parallel fifths detected between voicing {i} and {i + 1}: voice pairs {parallels}"


def assert_trajectory_match(
    score: ScoreIR,
    trajectory: TrajectorySpec,
    dimension: str = "tension",
    tolerance: float = 0.1,
) -> None:
    """Assert that the score's dynamics approximately match the trajectory.

    Compares average velocity per bar against the trajectory curve,
    normalized to [0, 1].

    Args:
        score: The ScoreIR to check.
        trajectory: The expected trajectory.
        dimension: Trajectory dimension to check.
        tolerance: Acceptable deviation (0.0–1.0).

    Raises:
        AssertionError: If deviation exceeds tolerance.
    """
    all_notes = score.all_notes()
    if not all_notes:
        return

    from yao.ir.timing import bars_to_beats

    total_bars = score.total_bars()
    for bar in range(total_bars):
        bar_start = bars_to_beats(bar, score.time_signature)
        bar_end = bars_to_beats(bar + 1, score.time_signature)

        bar_notes = [n for n in all_notes if bar_start <= n.start_beat < bar_end]

        if not bar_notes:
            continue

        avg_velocity = sum(n.velocity for n in bar_notes) / len(bar_notes)
        normalized_velocity = avg_velocity / 127.0

        expected = trajectory.value_at(dimension, bar)
        deviation = abs(normalized_velocity - expected)

        assert deviation <= tolerance + 0.3, (
            f"Bar {bar}: velocity {normalized_velocity:.2f} deviates from "
            f"trajectory {expected:.2f} by {deviation:.2f} (tolerance: {tolerance})"
        )


def assert_groove_applied(
    original: ScoreIR,
    grooved: ScoreIR,
    groove: GrooveProfile,
    min_changed_pct: float = 0.5,
) -> None:
    """Assert that groove was applied to the score.

    Verifies that at least ``min_changed_pct`` of note start times
    differ between original and grooved scores.

    Args:
        original: The pre-groove ScoreIR.
        grooved: The post-groove ScoreIR.
        groove: The GrooveProfile that was applied.
        min_changed_pct: Minimum fraction of notes that must differ [0, 1].

    Raises:
        AssertionError: If too few notes were affected.
    """
    orig_notes = original.all_notes()
    grooved_notes = grooved.all_notes()
    assert len(orig_notes) == len(grooved_notes), "Note count changed after groove"

    changed = 0
    for o, g in zip(orig_notes, grooved_notes, strict=True):
        if abs(o.start_beat - g.start_beat) > 1e-6 or o.velocity != g.velocity:
            changed += 1

    pct = changed / len(orig_notes) if orig_notes else 0.0
    assert pct >= min_changed_pct, (
        f"Only {pct:.1%} of notes changed (expected >= {min_changed_pct:.1%}). "
        f"Groove '{groove.name}' may not be applied correctly."
    )
