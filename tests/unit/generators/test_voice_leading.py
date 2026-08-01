"""Voice-leading in accompaniment (P1.3).

The harmony part must connect chords with minimal voice motion and avoid
parallel fifths/octaves, rather than lurching to root position each change.
"""

from __future__ import annotations

from yao.generators.note.accompaniment import chord_pitches, voice_lead_sequence
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction
from yao.ir.voicing import Voicing, check_parallel_fifths, check_parallel_octaves


def _progression() -> list[list[int]]:
    """A I–IV–V–I progression in F major as root-position pitch lists."""
    romans = ["I", "IV", "V", "I"]
    events = [ChordEvent("A", float(i) * 4, 4.0, r, HarmonicFunction.TONIC, 0.4) for i, r in enumerate(romans)]
    return [chord_pitches(e, "F", "major") for e in events]


def _total_motion(voicings: list[list[int]]) -> int:
    total = 0
    for a, b in zip(voicings, voicings[1:], strict=False):
        n = min(len(a), len(b))
        total += sum(abs(b[i] - a[i]) for i in range(n))
    return total


def test_voice_leading_reduces_motion_vs_block() -> None:
    root_position = _progression()
    led = voice_lead_sequence(root_position, num_voices=3)

    block = [sorted(p[:3]) for p in root_position]
    assert _total_motion(led) < _total_motion(block)


def test_voice_leading_has_no_parallel_fifths_or_octaves() -> None:
    led = voice_lead_sequence(_progression(), num_voices=3)
    for a, b in zip(led, led[1:], strict=False):
        va, vb = Voicing(pitches=tuple(a)), Voicing(pitches=tuple(b))
        assert check_parallel_fifths(va, vb) == []
        assert check_parallel_octaves(va, vb) == []


def test_voice_leading_preserves_chord_tones() -> None:
    root_position = _progression()
    led = voice_lead_sequence(root_position, num_voices=3)
    for pitches, voicing in zip(root_position, led, strict=True):
        chord_pcs = {p % 12 for p in pitches}
        assert all(v % 12 in chord_pcs for v in voicing), "every voice must be a chord tone"


def test_stable_voice_count() -> None:
    led = voice_lead_sequence(_progression(), num_voices=3)
    counts = {len(v) for v in led}
    assert counts == {3}


def test_empty_and_single() -> None:
    assert voice_lead_sequence([]) == []
    single = voice_lead_sequence([[65, 69, 72]], num_voices=3)
    assert len(single) == 1 and len(single[0]) == 3
