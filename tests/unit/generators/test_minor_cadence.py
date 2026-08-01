"""Inc 14: harmonic-minor dominant — V in a minor key is rendered major (raised
leading tone) so cadences pull to the tonic (natural-minor v has none).
"""

from __future__ import annotations

from yao.generators.note.accompaniment import chord_pitches
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction


def _pc_set(roman: str, key: str, scale: str) -> set[int]:
    ce = ChordEvent("A", 0.0, 4.0, roman, HarmonicFunction.DOMINANT, 0.5)
    return {p % 12 for p in chord_pitches(ce, key, scale)}


def test_minor_v_has_raised_leading_tone() -> None:
    # F minor: V root = C. Major V = C-E-G; E (pc 4) is the leading tone.
    pcs = _pc_set("V", "F", "minor")
    assert 4 in pcs  # E natural (leading tone), not Eb (pc 3)
    assert 3 not in pcs


def test_major_key_v_unchanged() -> None:
    # C major V = G-B-D; already major, rule is a no-op.
    pcs = _pc_set("V", "C", "major")
    assert {7, 11, 2} <= pcs  # G, B, D


def test_minor_tonic_stays_minor() -> None:
    # The rule only touches the dominant; i stays minor.
    ce = ChordEvent("A", 0.0, 4.0, "i", HarmonicFunction.TONIC, 0.3)
    pcs = {p % 12 for p in chord_pitches(ce, "F", "minor")}
    assert 5 in pcs and 8 in pcs  # F, Ab (minor third)
