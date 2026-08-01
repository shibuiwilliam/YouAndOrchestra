"""Inc 15: diatonic_quality returns correct triad qualities for the church modes.

Previously every mode fell back to the major table, so all modal chords were
rendered major — destroying modal harmony.
"""

from __future__ import annotations

import pytest

from yao.ir.harmony import diatonic_quality

# Each mode's diatonic triad qualities, degrees 0–6.
_EXPECTED = {
    "major": ["maj", "min", "min", "maj", "maj", "min", "dim"],
    "dorian": ["min", "min", "maj", "maj", "min", "dim", "maj"],
    "phrygian": ["min", "maj", "maj", "min", "dim", "maj", "min"],
    "lydian": ["maj", "maj", "min", "dim", "maj", "min", "min"],
    "mixolydian": ["maj", "min", "dim", "maj", "min", "min", "maj"],
    "aeolian": ["min", "dim", "maj", "min", "min", "maj", "maj"],
    "locrian": ["dim", "maj", "min", "min", "maj", "maj", "min"],
}


@pytest.mark.parametrize("scale", list(_EXPECTED))
def test_mode_triad_qualities(scale: str) -> None:
    assert [diatonic_quality(d, scale) for d in range(7)] == _EXPECTED[scale]


def test_dorian_v_is_minor_not_major() -> None:
    # The bug: dorian V used to come out major.
    assert diatonic_quality(4, "dorian") == "min"


def test_aeolian_matches_natural_minor() -> None:
    assert [diatonic_quality(d, "aeolian") for d in range(7)] == [diatonic_quality(d, "minor") for d in range(7)]
