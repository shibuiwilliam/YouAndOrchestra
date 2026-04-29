"""Tests for the custom exception hierarchy."""

from __future__ import annotations

from yao.errors import (
    ConstraintViolationError,
    ProvenanceError,
    RangeViolationError,
    RenderError,
    SpecValidationError,
    VerificationError,
    YaOError,
)


class TestExceptionHierarchy:
    def test_all_exceptions_are_yao_errors(self) -> None:
        exceptions = [
            SpecValidationError("test"),
            ConstraintViolationError("test"),
            RangeViolationError("piano", 200, 21, 108),
            RenderError("test"),
            VerificationError("test"),
            ProvenanceError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, YaOError)

    def test_range_violation_is_constraint_violation(self) -> None:
        exc = RangeViolationError("violin", 130, 55, 103)
        assert isinstance(exc, ConstraintViolationError)
        assert isinstance(exc, YaOError)

    def test_range_violation_stores_context(self) -> None:
        exc = RangeViolationError("violin", 130, 55, 103)
        assert exc.instrument == "violin"
        assert exc.note == 130
        assert exc.valid_low == 55
        assert exc.valid_high == 103
        msg = str(exc)
        assert "130" in msg
        assert "violin" in msg
        # Musical error messages include note name and suggestions
        assert "above" in msg
        assert "transpose" in msg

    def test_spec_validation_error_stores_field(self) -> None:
        exc = SpecValidationError("bad value", field="tempo_bpm")
        assert exc.field == "tempo_bpm"
        assert "bad value" in str(exc)

    def test_spec_validation_error_field_optional(self) -> None:
        exc = SpecValidationError("generic error")
        assert exc.field is None
