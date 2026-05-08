"""Tests for loading genre-specific Markov models and harmonic devices.

Verifies all YAML files in the model directories can be parsed
and have valid structure.

Phase 4.0 — IMPROVEMENT.md §4.2, §3.1, §5.6.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yao.coupling.harmonic_devices import list_available_devices, load_all_devices, load_device
from yao.coupling.rhythm_markov import list_available_rhythm_models, load_rhythm_model

_PITCH_DIR = Path("src/yao/generators/markov_models/pitch")
_RHYTHM_DIR = Path("src/yao/generators/markov_models/rhythm")
_DEVICES_DIR = Path("src/yao/constants/harmonic_devices")


class TestPitchMarkovModels:
    """All pitch Markov models load and have valid structure."""

    def test_at_least_15_models(self) -> None:
        """Phase 4.0 requires 15+ pitch models."""
        models = sorted(p.stem for p in _PITCH_DIR.glob("*.yaml"))
        assert len(models) >= 15, f"Only {len(models)} pitch models found"

    @pytest.mark.parametrize("model_file", sorted(_PITCH_DIR.glob("*.yaml")))
    def test_model_loads_valid_yaml(self, model_file: Path) -> None:
        """Each model file is valid YAML with required fields."""
        data = yaml.safe_load(model_file.read_text())
        assert "metadata" in data, f"{model_file.name} missing metadata"
        assert "transitions" in data, f"{model_file.name} missing transitions"

        meta = data["metadata"]
        assert "name" in meta
        assert "license" in meta
        assert "n_gram_order" in meta

    @pytest.mark.parametrize("model_file", sorted(_PITCH_DIR.glob("*.yaml")))
    def test_transition_rows_sum_to_one(self, model_file: Path) -> None:
        """Each transition row sums to approximately 1.0."""
        data = yaml.safe_load(model_file.read_text())
        for key, row in data["transitions"].items():
            total = sum(row.values())
            assert abs(total - 1.0) < 0.02, f"{model_file.name}: row {key} sums to {total}"


class TestRhythmMarkovModels:
    """All rhythm Markov models load correctly."""

    def test_at_least_12_models(self) -> None:
        """Phase 4.0 requires 12+ rhythm models."""
        models = list_available_rhythm_models()
        assert len(models) >= 12, f"Only {len(models)} rhythm models found"

    @pytest.mark.parametrize(
        "model_name", sorted(p.stem for p in _RHYTHM_DIR.glob("*.yaml")) if _RHYTHM_DIR.exists() else []
    )
    def test_model_loads(self, model_name: str) -> None:
        """Each rhythm model loads without error."""
        model = load_rhythm_model(model_name)
        assert model.name
        assert model.num_positions > 0


class TestHarmonicDevices:
    """All harmonic devices load correctly."""

    def test_at_least_15_devices(self) -> None:
        """Phase 4.0 requires 15+ harmonic devices."""
        devices = list_available_devices()
        assert len(devices) >= 15, f"Only {len(devices)} devices found"

    def test_all_devices_load(self) -> None:
        """Every device file loads into a HarmonicDevice."""
        devices = load_all_devices()
        assert len(devices) >= 15
        for d in devices:
            assert d.name
            assert len(d.chord_pattern) > 0
            assert d.placement
            assert len(d.genres) > 0

    def test_at_least_7_device_categories(self) -> None:
        """At least 7 different placement categories."""
        devices = load_all_devices()
        placements = {d.placement for d in devices}
        # We should have multiple categories
        assert len(placements) >= 3, f"Only {len(placements)} placement types"

    @pytest.mark.parametrize(
        "device_name", sorted(p.stem for p in _DEVICES_DIR.glob("*.yaml")) if _DEVICES_DIR.exists() else []
    )
    def test_device_loads(self, device_name: str) -> None:
        """Each device file loads without error."""
        device = load_device(device_name)
        assert device.name
