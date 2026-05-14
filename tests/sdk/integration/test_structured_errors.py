"""Integration test: structured error payloads for domain errors.

§6.4: RangeViolationError and SpecValidationError must return
structured payloads with error_type, instrument, note, etc.
"""

from __future__ import annotations

import json

from yao.errors import RangeViolationError, SpecValidationError
from yao.sdk.server import _err


class TestStructuredErrorPayloads:
    def test_range_violation_includes_instrument_and_note(self) -> None:
        exc = RangeViolationError(
            instrument="violin",
            note=20,  # way below violin range
            valid_low=55,
            valid_high=103,
        )
        result = _err(exc)
        assert result["isError"] is True
        data = json.loads(result["content"][0]["text"])
        assert data["error_type"] == "RangeViolationError"
        assert data["instrument"] == "violin"
        assert data["note"] == 20
        assert data["valid_low"] == 55
        assert data["valid_high"] == 103

    def test_spec_validation_includes_field(self) -> None:
        exc = SpecValidationError("Invalid tempo", field="tempo_bpm")
        result = _err(exc)
        data = json.loads(result["content"][0]["text"])
        assert data["error_type"] == "SpecValidationError"
        assert data["field"] == "tempo_bpm"

    def test_generic_error_includes_type(self) -> None:
        exc = ValueError("something went wrong")
        result = _err(exc)
        data = json.loads(result["content"][0]["text"])
        assert data["error_type"] == "ValueError"
        assert "something went wrong" in data["message"]
