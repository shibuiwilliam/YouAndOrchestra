"""Tests for GrooveProfile IR (Layer 3.5).

Tests cover:
- Creation and validation
- Serialization round-trip
- YAML loading
- Library discovery
- Boundary validation (offset limits, position range)
"""

from __future__ import annotations

import pytest

from yao.ir.groove import GrooveProfile, available_grooves, load_groove


class TestGrooveProfile:
    """Tests for GrooveProfile."""

    def _make_profile(self, **kwargs: object) -> GrooveProfile:
        defaults: dict[str, object] = {
            "name": "test",
            "microtiming": {0: 0.0, 4: 5.0, 8: -3.0, 12: 8.0},
            "velocity_pattern": {0: 1.1, 4: 0.9, 8: 1.0, 12: 0.85},
            "ghost_probability": 0.15,
            "swing_ratio": 0.58,
            "timing_jitter_sigma": 6.0,
        }
        defaults.update(kwargs)
        return GrooveProfile(**defaults)  # type: ignore[arg-type]

    def test_creation(self) -> None:
        profile = self._make_profile()
        assert profile.name == "test"
        assert profile.swing_ratio == 0.58

    def test_microtiming_at(self) -> None:
        profile = self._make_profile()
        assert profile.microtiming_at(0) == 0.0
        assert profile.microtiming_at(4) == 5.0
        assert profile.microtiming_at(1) == 0.0  # Not in pattern

    def test_velocity_mult_at(self) -> None:
        profile = self._make_profile()
        assert profile.velocity_mult_at(0) == 1.1
        assert profile.velocity_mult_at(1) == 1.0  # Default

    def test_frozen(self) -> None:
        profile = self._make_profile()
        with pytest.raises(AttributeError):
            profile.name = "modified"  # type: ignore[misc]

    def test_round_trip(self) -> None:
        profile = self._make_profile()
        data = profile.to_dict()
        restored = GrooveProfile.from_dict(data)
        assert restored.name == profile.name
        assert restored.microtiming == profile.microtiming
        assert restored.velocity_pattern == profile.velocity_pattern
        assert restored.swing_ratio == profile.swing_ratio

    def test_offset_too_large(self) -> None:
        with pytest.raises(ValueError, match="offset must be in"):
            self._make_profile(microtiming={0: 60.0})

    def test_offset_too_negative(self) -> None:
        with pytest.raises(ValueError, match="offset must be in"):
            self._make_profile(microtiming={0: -55.0})

    def test_position_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="position must be 0–15"):
            self._make_profile(microtiming={16: 5.0})

    def test_negative_ghost_probability(self) -> None:
        with pytest.raises(ValueError, match="Ghost probability"):
            self._make_profile(ghost_probability=-0.1)

    def test_swing_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="Swing ratio"):
            self._make_profile(swing_ratio=1.5)

    def test_negative_jitter(self) -> None:
        with pytest.raises(ValueError, match="jitter sigma"):
            self._make_profile(timing_jitter_sigma=-1.0)

    def test_negative_velocity_multiplier(self) -> None:
        with pytest.raises(ValueError, match="Velocity multiplier"):
            self._make_profile(velocity_pattern={0: -0.5})

    def test_apply_to_all_default(self) -> None:
        profile = self._make_profile()
        assert profile.apply_to_all_instruments is True

    def test_apply_drums_only(self) -> None:
        profile = self._make_profile(apply_to_all_instruments=False)
        assert profile.apply_to_all_instruments is False


class TestGrooveLibrary:
    """Tests for groove YAML loading and discovery."""

    def test_available_grooves_not_empty(self) -> None:
        grooves = available_grooves()
        assert len(grooves) >= 12

    def test_load_all_grooves(self) -> None:
        for name in available_grooves():
            profile = load_groove(name)
            assert profile.name == name

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            load_groove("nonexistent_groove_xyz")

    def test_lofi_hiphop_has_swing(self) -> None:
        profile = load_groove("lofi_hiphop")
        assert profile.swing_ratio > 0.5

    def test_edm_is_straight(self) -> None:
        profile = load_groove("edm_4onfloor")
        assert profile.swing_ratio == 0.5

    def test_jazz_has_high_swing(self) -> None:
        profile = load_groove("jazz_swing")
        assert profile.swing_ratio >= 0.6

    def test_all_offsets_within_bounds(self) -> None:
        """All groove profiles must have offsets in [-50, 50] ms."""
        for name in available_grooves():
            profile = load_groove(name)
            for pos, offset in profile.microtiming.items():
                assert abs(offset) <= 50.0, f"Groove '{name}' has offset {offset} at position {pos}"
