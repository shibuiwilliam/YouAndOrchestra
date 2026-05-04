"""Tests for PinsSpec schema (Phase δ.2).

Tests cover:
- Valid spec loading
- Pin id validation
- YAML round-trip
- Section filtering
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from yao.errors import SpecValidationError
from yao.schema.pins import PinsSpec


class TestPinsSpec:
    """Tests for PinsSpec."""

    def test_valid_spec(self) -> None:
        spec = PinsSpec.model_validate(
            {
                "project": "my-song",
                "iteration": "v003",
                "pins": [
                    {
                        "id": "pin-001",
                        "location": {"section": "chorus", "bar": 6, "beat": 3.0, "instrument": "piano"},
                        "note": "too dissonant",
                        "user_intent": "soften_dissonance",
                        "severity": "medium",
                    },
                ],
            }
        )
        assert len(spec.pins) == 1
        assert spec.pins[0].id == "pin-001"

    def test_empty_pins(self) -> None:
        spec = PinsSpec.model_validate({"pins": []})
        assert len(spec.pins) == 0

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(SpecValidationError, match="cannot be empty"):
            PinsSpec.model_validate(
                {
                    "pins": [{"id": "", "location": {"section": "v", "bar": 1}, "note": "x"}],
                }
            )

    def test_empty_note_rejected(self) -> None:
        with pytest.raises(SpecValidationError, match="cannot be empty"):
            PinsSpec.model_validate(
                {
                    "pins": [{"id": "p1", "location": {"section": "v", "bar": 1}, "note": ""}],
                }
            )

    def test_pin_ids(self) -> None:
        spec = PinsSpec.model_validate(
            {
                "pins": [
                    {"id": "p1", "location": {"section": "v", "bar": 1}, "note": "a"},
                    {"id": "p2", "location": {"section": "c", "bar": 2}, "note": "b"},
                ],
            }
        )
        assert spec.pin_ids() == ["p1", "p2"]

    def test_pins_for_section(self) -> None:
        spec = PinsSpec.model_validate(
            {
                "pins": [
                    {"id": "p1", "location": {"section": "verse", "bar": 1}, "note": "a"},
                    {"id": "p2", "location": {"section": "chorus", "bar": 2}, "note": "b"},
                    {"id": "p3", "location": {"section": "verse", "bar": 3}, "note": "c"},
                ],
            }
        )
        verse_pins = spec.pins_for_section("verse")
        assert len(verse_pins) == 2
        chorus_pins = spec.pins_for_section("chorus")
        assert len(chorus_pins) == 1

    def test_yaml_round_trip(self) -> None:
        spec = PinsSpec.model_validate(
            {
                "project": "test",
                "iteration": "v001",
                "pins": [
                    {"id": "p1", "location": {"section": "verse", "bar": 3}, "note": "harsh"},
                ],
            }
        )
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = Path(f.name)
        spec.to_yaml(path)
        loaded = PinsSpec.from_yaml(path)
        assert loaded.project == "test"
        assert len(loaded.pins) == 1
        assert loaded.pins[0].note == "harsh"
