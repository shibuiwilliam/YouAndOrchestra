"""Tests for Pin IR (Phase δ.2).

Tests cover:
- Pin creation and validation
- PinLocation parsing from string
- Serialization round-trip
- Affected bar range calculation
- Immutability
"""

from __future__ import annotations

import pytest

from yao.feedback.pin import Pin, PinLocation


class TestPinLocation:
    """Tests for PinLocation."""

    def test_creation(self) -> None:
        loc = PinLocation(section="chorus", bar=6, beat=3.0, instrument="piano")
        assert loc.section == "chorus"
        assert loc.bar == 6
        assert loc.beat == 3.0
        assert loc.instrument == "piano"

    def test_minimal(self) -> None:
        loc = PinLocation(section="verse", bar=1)
        assert loc.beat is None
        assert loc.instrument is None

    def test_bar_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="Bar must be >= 1"):
            PinLocation(section="verse", bar=0)

    def test_beat_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="Beat must be >= 1"):
            PinLocation(section="verse", bar=1, beat=0.5)

    def test_round_trip(self) -> None:
        loc = PinLocation(section="chorus", bar=6, beat=3.0, instrument="piano")
        data = loc.to_dict()
        restored = PinLocation.from_dict(data)
        assert restored == loc

    def test_from_string_full(self) -> None:
        loc = PinLocation.from_string("section:chorus,bar:6,beat:3,instrument:piano")
        assert loc.section == "chorus"
        assert loc.bar == 6
        assert loc.beat == 3.0
        assert loc.instrument == "piano"

    def test_from_string_minimal(self) -> None:
        loc = PinLocation.from_string("section:verse,bar:2")
        assert loc.section == "verse"
        assert loc.bar == 2
        assert loc.beat is None
        assert loc.instrument is None

    def test_from_string_missing_section(self) -> None:
        with pytest.raises(ValueError, match="section"):
            PinLocation.from_string("bar:6")

    def test_from_string_missing_bar(self) -> None:
        with pytest.raises(ValueError, match="bar"):
            PinLocation.from_string("section:chorus")

    def test_from_string_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid location pair"):
            PinLocation.from_string("chorus")


class TestPin:
    """Tests for Pin."""

    def _make_pin(self, **kwargs: object) -> Pin:
        defaults: dict[str, object] = {
            "id": "pin-001",
            "location": PinLocation(section="chorus", bar=6, beat=3.0, instrument="piano"),
            "note": "this dissonance is too harsh",
            "user_intent": "soften_dissonance",
            "severity": "medium",
        }
        defaults.update(kwargs)
        return Pin(**defaults)  # type: ignore[arg-type]

    def test_creation(self) -> None:
        pin = self._make_pin()
        assert pin.id == "pin-001"
        assert pin.note == "this dissonance is too harsh"
        assert pin.user_intent == "soften_dissonance"
        assert pin.severity == "medium"

    def test_created_at_auto_set(self) -> None:
        pin = self._make_pin()
        assert pin.created_at != ""

    def test_frozen(self) -> None:
        pin = self._make_pin()
        with pytest.raises(AttributeError):
            pin.note = "modified"  # type: ignore[misc]

    def test_round_trip(self) -> None:
        pin = self._make_pin()
        data = pin.to_dict()
        restored = Pin.from_dict(data)
        assert restored.id == pin.id
        assert restored.location == pin.location
        assert restored.note == pin.note
        assert restored.user_intent == pin.user_intent

    def test_affected_bar_range_default_padding(self) -> None:
        pin = self._make_pin()  # bar=6
        start, end = pin.affected_bar_range()
        assert start == 5  # 6 - 1
        assert end == 7  # 6 + 1

    def test_affected_bar_range_at_start(self) -> None:
        pin = self._make_pin(
            location=PinLocation(section="verse", bar=1),
        )
        start, end = pin.affected_bar_range()
        assert start == 1  # Clamped to 1

    def test_affected_bar_range_custom_padding(self) -> None:
        pin = self._make_pin()  # bar=6
        start, end = pin.affected_bar_range(padding=2)
        assert start == 4
        assert end == 8

    def test_default_intent(self) -> None:
        pin = Pin(
            id="pin-002",
            location=PinLocation(section="verse", bar=1),
            note="something seems off",
        )
        assert pin.user_intent == "unclear"
