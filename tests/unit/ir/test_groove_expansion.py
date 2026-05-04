"""Tests for groove library expansion to 20 profiles."""

from __future__ import annotations

import pytest

from yao.ir.groove import available_grooves, load_groove

# The 8 new grooves added in PR 2.9
NEW_GROOVES = [
    "waltz_viennese",
    "shuffle_blues",
    "samba",
    "afrobeat",
    "new_orleans_second_line",
    "drum_n_bass",
    "flamenco_bulerias",
    "bollywood_filmi",
]


class TestGrooveExpansion:
    """Verify groove library has been expanded to 20+ profiles."""

    def test_total_groove_count(self) -> None:
        grooves = available_grooves()
        assert len(grooves) >= 20, f"Expected >=20 grooves, got {len(grooves)}: {grooves}"

    @pytest.mark.parametrize("name", NEW_GROOVES)
    def test_new_groove_loads(self, name: str) -> None:
        groove = load_groove(name)
        assert groove.name == name

    @pytest.mark.parametrize("name", NEW_GROOVES)
    def test_new_groove_has_valid_microtiming(self, name: str) -> None:
        groove = load_groove(name)
        for pos, offset in groove.microtiming.items():
            assert 0 <= pos <= 15, f"Position {pos} out of 16th-note range"
            assert -50.0 <= offset <= 50.0, f"Offset {offset}ms out of [-50, 50] range"

    @pytest.mark.parametrize("name", NEW_GROOVES)
    def test_new_groove_has_valid_velocity_pattern(self, name: str) -> None:
        groove = load_groove(name)
        for pos, mult in groove.velocity_pattern.items():
            assert 0 <= pos <= 15, f"Position {pos} out of 16th-note range"
            assert 0.0 < mult <= 2.0, f"Velocity multiplier {mult} out of range"

    @pytest.mark.parametrize("name", NEW_GROOVES)
    def test_new_groove_has_valid_swing_ratio(self, name: str) -> None:
        groove = load_groove(name)
        assert 0.5 <= groove.swing_ratio <= 0.75, f"Swing ratio {groove.swing_ratio} out of [0.5, 0.75]"

    @pytest.mark.parametrize("name", NEW_GROOVES)
    def test_new_groove_has_valid_ghost_probability(self, name: str) -> None:
        groove = load_groove(name)
        assert 0.0 <= groove.ghost_probability <= 1.0

    @pytest.mark.parametrize("name", NEW_GROOVES)
    def test_new_groove_has_valid_jitter(self, name: str) -> None:
        groove = load_groove(name)
        assert 0.0 <= groove.timing_jitter_sigma <= 20.0
