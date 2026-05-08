"""Tests for the Harmonic Devices library.

Phase 4.0 — IMPROVEMENT.md §5.6.
"""

from __future__ import annotations

import pytest

from yao.coupling.harmonic_devices import (
    HarmonicDevice,
    clear_device_cache,
    devices_for_genre,
    devices_for_placement,
    list_available_devices,
    load_all_devices,
    load_device,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_device_cache()


class TestHarmonicDevice:
    def test_creation(self) -> None:
        device = HarmonicDevice(
            name="test_turnaround",
            description="Test turnaround",
            chord_pattern=("I", "vi", "ii", "V"),
            placement="section_end",
            genres=("jazz_ballad", "bebop"),
            source="test",
            license="CC0",
        )
        assert device.name == "test_turnaround"
        assert len(device.chord_pattern) == 4

    def test_frozen(self) -> None:
        device = HarmonicDevice(
            name="test",
            description="",
            chord_pattern=(),
            placement="",
            genres=(),
            source="",
            license="",
        )
        with pytest.raises(AttributeError):
            device.name = "changed"  # type: ignore[misc]


class TestLoadDevices:
    def test_list_available(self) -> None:
        """Should list devices if directory has YAMLs."""
        devices = list_available_devices()
        assert isinstance(devices, list)

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_device("nonexistent_device_xyz")

    def test_load_all_returns_list(self) -> None:
        devices = load_all_devices()
        assert isinstance(devices, list)
        for d in devices:
            assert isinstance(d, HarmonicDevice)

    def test_devices_for_genre_returns_list(self) -> None:
        result = devices_for_genre("jazz_ballad")
        assert isinstance(result, list)

    def test_devices_for_placement_returns_list(self) -> None:
        result = devices_for_placement("section_end")
        assert isinstance(result, list)
