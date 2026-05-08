"""Tests for the Polyrhythm Engine.

Phase 5.0 — IMPROVEMENT.md §3.2.
"""

from __future__ import annotations

from yao.coupling.polyrhythm import (
    PolyrhythmLayer,
    PolyrhythmTexture,
    are_coprime,
    compose_polyrhythm,
    phase_shift,
)


class TestPolyrhythmLayer:
    def test_creation(self) -> None:
        layer = PolyrhythmLayer(
            cycle_length_beats=4.0,
            pattern=(0.0, 0.25, 0.5, 0.75),
            instrument="hi_hat",
        )
        assert layer.cycle_length_beats == 4.0
        assert len(layer.pattern) == 4


class TestPolyrhythmTexture:
    def test_layer_count(self) -> None:
        texture = PolyrhythmTexture(
            layers=(
                PolyrhythmLayer(4.0, (0.0, 0.5), "kick"),
                PolyrhythmLayer(3.0, (0.0, 0.33, 0.67), "snare"),
            ),
            base_meter="4/4",
            duration_bars=4,
        )
        assert texture.layer_count == 2

    def test_all_onsets(self) -> None:
        texture = PolyrhythmTexture(
            layers=(PolyrhythmLayer(4.0, (0.0,), "kick"),),
            base_meter="4/4",
            duration_bars=2,
        )
        onsets = texture.all_onsets(beats_per_bar=4)
        assert len(onsets) == 2  # One per bar
        assert all(inst == "kick" for _, inst in onsets)


class TestComposePolyrhythm:
    def test_3_against_4(self) -> None:
        texture = compose_polyrhythm((3, 4), duration_bars=4)
        assert texture.layer_count == 2
        onsets = texture.all_onsets()
        assert len(onsets) > 0

    def test_2_against_3(self) -> None:
        texture = compose_polyrhythm((2, 3), duration_bars=4)
        assert texture.layer_count == 2

    def test_custom_instruments(self) -> None:
        texture = compose_polyrhythm(
            (3, 4),
            duration_bars=2,
            instruments=("bell", "shaker"),
        )
        instruments = {inst for _, inst in texture.all_onsets()}
        assert "bell" in instruments
        assert "shaker" in instruments


class TestAreCoprime:
    def test_coprime(self) -> None:
        assert are_coprime(3, 4)
        assert are_coprime(5, 7)

    def test_not_coprime(self) -> None:
        assert not are_coprime(4, 6)
        assert not are_coprime(6, 9)


class TestPhaseShift:
    def test_shift_by_half(self) -> None:
        layer = PolyrhythmLayer(4.0, (0.0, 0.5), "kick")
        shifted = phase_shift(layer, 2.0)  # shift by half cycle
        assert shifted.instrument == "kick"
        # Original: 0.0, 0.5 → shifted by 0.5 of cycle → 0.5, 0.0 → sorted: 0.0, 0.5
        assert len(shifted.pattern) == 2

    def test_shift_preserves_pattern_count(self) -> None:
        layer = PolyrhythmLayer(4.0, (0.0, 0.25, 0.5, 0.75), "hi_hat")
        shifted = phase_shift(layer, 1.0)
        assert len(shifted.pattern) == 4
