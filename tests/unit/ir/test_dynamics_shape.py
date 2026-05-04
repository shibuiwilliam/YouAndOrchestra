"""Tests for DynamicsShape IR."""

from __future__ import annotations

import pytest

from yao.ir.dynamics_shape import BarAccent, DynamicsShape, DynamicsShapeType


class TestDynamicsShapeMultiplier:
    def test_steady_always_one(self) -> None:
        shape = DynamicsShape(shape=DynamicsShapeType.STEADY)
        assert shape.velocity_multiplier(0.0) == 1.0
        assert shape.velocity_multiplier(0.5) == 1.0
        assert shape.velocity_multiplier(1.0) == 1.0

    def test_crescendo_rises(self) -> None:
        shape = DynamicsShape(shape=DynamicsShapeType.CRESCENDO, intensity=0.6)
        start = shape.velocity_multiplier(0.0)
        mid = shape.velocity_multiplier(0.5)
        end = shape.velocity_multiplier(1.0)
        assert start < mid < end

    def test_decrescendo_falls(self) -> None:
        shape = DynamicsShape(shape=DynamicsShapeType.DECRESCENDO, intensity=0.6)
        start = shape.velocity_multiplier(0.0)
        mid = shape.velocity_multiplier(0.5)
        end = shape.velocity_multiplier(1.0)
        assert start > mid > end

    def test_arch_peak_at_position(self) -> None:
        """Arch with peak_position=0.7 should have maximum at position 0.7."""
        shape = DynamicsShape(
            shape=DynamicsShapeType.ARCH,
            peak_position=0.7,
            intensity=0.7,
        )
        # Sample multiple positions
        values = [(pos / 20.0, shape.velocity_multiplier(pos / 20.0)) for pos in range(21)]
        max_pos, max_val = max(values, key=lambda x: x[1])
        # Peak should be at or very near 0.7
        assert abs(max_pos - 0.7) <= 0.05

    def test_arch_symmetric_around_peak(self) -> None:
        """Arch with peak_position=0.5 should be symmetric."""
        shape = DynamicsShape(
            shape=DynamicsShapeType.ARCH,
            peak_position=0.5,
            intensity=0.8,
        )
        # 0.2 from peak in both directions should be equal
        left = shape.velocity_multiplier(0.3)
        right = shape.velocity_multiplier(0.7)
        assert abs(left - right) < 0.01

    def test_hairpin_behaves_like_arch(self) -> None:
        """Hairpin is the same algorithm as arch."""
        arch = DynamicsShape(shape=DynamicsShapeType.ARCH, peak_position=0.5, intensity=0.6)
        hairpin = DynamicsShape(shape=DynamicsShapeType.HAIRPIN, peak_position=0.5, intensity=0.6)
        for pos in (0.0, 0.25, 0.5, 0.75, 1.0):
            assert arch.velocity_multiplier(pos) == hairpin.velocity_multiplier(pos)

    def test_intensity_zero_means_flat(self) -> None:
        """With intensity=0, all shapes return 1.0."""
        for shape_type in DynamicsShapeType:
            shape = DynamicsShape(shape=shape_type, intensity=0.0, peak_position=0.5)
            assert shape.velocity_multiplier(0.3) == pytest.approx(1.0, abs=0.001)

    def test_multiplier_stays_in_reasonable_range(self) -> None:
        """Multiplier should stay within [0.3, 1.7] for typical intensities."""
        shape = DynamicsShape(shape=DynamicsShapeType.ARCH, peak_position=0.5, intensity=1.0)
        for pos_i in range(21):
            val = shape.velocity_multiplier(pos_i / 20.0)
            assert 0.3 <= val <= 1.7

    def test_position_clamped(self) -> None:
        """Positions outside [0,1] are clamped."""
        shape = DynamicsShape(shape=DynamicsShapeType.CRESCENDO, intensity=0.5)
        # Should not crash, result should equal boundary
        assert shape.velocity_multiplier(-0.5) == shape.velocity_multiplier(0.0)
        assert shape.velocity_multiplier(1.5) == shape.velocity_multiplier(1.0)


class TestBarAccent:
    def test_creation(self) -> None:
        accent = BarAccent(bar=2, beat=1.5, strength=1.3)
        assert accent.bar == 2
        assert accent.beat == 1.5
        assert accent.strength == 1.3

    def test_serialization(self) -> None:
        accent = BarAccent(bar=1, beat=0.0, strength=1.4)
        restored = BarAccent.from_dict(accent.to_dict())
        assert restored == accent


class TestDynamicsShapeSerialization:
    def test_round_trip_arch(self) -> None:
        shape = DynamicsShape(
            shape=DynamicsShapeType.ARCH,
            peak_position=0.7,
            intensity=0.8,
            accents=(BarAccent(bar=0, beat=0.0, strength=1.2),),
        )
        restored = DynamicsShape.from_dict(shape.to_dict())
        assert restored.shape == DynamicsShapeType.ARCH
        assert restored.peak_position == 0.7
        assert restored.intensity == 0.8
        assert len(restored.accents) == 1

    def test_round_trip_crescendo(self) -> None:
        shape = DynamicsShape(shape=DynamicsShapeType.CRESCENDO, intensity=0.5)
        data = shape.to_dict()
        assert "peak_position" not in data  # Not serialized for non-arch
        restored = DynamicsShape.from_dict(data)
        assert restored.shape == DynamicsShapeType.CRESCENDO
