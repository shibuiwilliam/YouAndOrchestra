"""Tests for RecoverableDecision and integration with ProvenanceLog."""

from __future__ import annotations

import pytest

from yao.errors import VerificationError
from yao.reflect.provenance import ProvenanceLog
from yao.reflect.recoverable import RecoverableDecision
from yao.reflect.recoverable_codes import KNOWN_CODES, validate_code

# ---------------------------------------------------------------------------
# RecoverableDecision construction
# ---------------------------------------------------------------------------


class TestRecoverableDecision:
    def test_basic_construction(self) -> None:
        d = RecoverableDecision(
            code="BASS_NOTE_OUT_OF_RANGE",
            severity="warning",
            original_value=36,
            recovered_value=40,
            reason="Walking bass below range",
            musical_impact="Bass jumps up",
        )
        assert d.code == "BASS_NOTE_OUT_OF_RANGE"
        assert d.severity == "warning"
        assert d.original_value == 36
        assert d.recovered_value == 40

    def test_is_blocking_error(self) -> None:
        d = RecoverableDecision(
            code="VELOCITY_CLAMPED",
            severity="error",
            original_value=200,
            recovered_value=127,
            reason="test",
            musical_impact="test",
        )
        assert d.is_blocking

    def test_is_not_blocking_warning(self) -> None:
        d = RecoverableDecision(
            code="VELOCITY_CLAMPED",
            severity="warning",
            original_value=200,
            recovered_value=127,
            reason="test",
            musical_impact="test",
        )
        assert not d.is_blocking

    def test_is_not_blocking_info(self) -> None:
        d = RecoverableDecision(
            code="VELOCITY_CLAMPED",
            severity="info",
            original_value=0,
            recovered_value=1,
            reason="test",
            musical_impact="test",
        )
        assert not d.is_blocking

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(VerificationError, match="Unknown recoverable code"):
            RecoverableDecision(
                code="TOTALLY_UNKNOWN_CODE",
                severity="info",
                original_value=0,
                recovered_value=0,
                reason="test",
                musical_impact="test",
            )

    def test_suggested_fix_default(self) -> None:
        d = RecoverableDecision(
            code="VELOCITY_CLAMPED",
            severity="info",
            original_value=0,
            recovered_value=1,
            reason="test",
            musical_impact="test",
        )
        assert d.suggested_fix == []

    def test_suggested_fix_provided(self) -> None:
        d = RecoverableDecision(
            code="BASS_NOTE_OUT_OF_RANGE",
            severity="warning",
            original_value=36,
            recovered_value=40,
            reason="test",
            musical_impact="test",
            suggested_fix=["widen range", "use synth bass"],
        )
        assert len(d.suggested_fix) == 2

    def test_frozen(self) -> None:
        d = RecoverableDecision(
            code="VELOCITY_CLAMPED",
            severity="info",
            original_value=0,
            recovered_value=1,
            reason="test",
            musical_impact="test",
        )
        with pytest.raises(AttributeError):
            d.code = "OTHER"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Code registry
# ---------------------------------------------------------------------------


class TestRecoverableCodes:
    def test_all_known_codes_exist(self) -> None:
        assert len(KNOWN_CODES) >= 9

    def test_validate_known_code(self) -> None:
        validate_code("BASS_NOTE_OUT_OF_RANGE")  # should not raise

    def test_validate_unknown_code_raises(self) -> None:
        with pytest.raises(VerificationError, match="Unknown"):
            validate_code("NOT_A_REAL_CODE")

    def test_all_codes_are_screaming_snake(self) -> None:
        import re

        for code in KNOWN_CODES:
            assert re.match(r"^[A-Z][A-Z0-9_]+$", code), f"Code '{code}' not SCREAMING_SNAKE"


# ---------------------------------------------------------------------------
# ProvenanceLog integration
# ---------------------------------------------------------------------------


class TestProvenanceLogRecoverable:
    def test_record_recoverable(self) -> None:
        prov = ProvenanceLog()
        d = RecoverableDecision(
            code="BASS_NOTE_OUT_OF_RANGE",
            severity="warning",
            original_value=36,
            recovered_value=40,
            reason="Bass below range",
            musical_impact="Bass jumps up",
        )
        prov.record_recoverable(d)
        assert len(prov.recoverables) == 1
        assert prov.recoverables[0].code == "BASS_NOTE_OUT_OF_RANGE"

    def test_also_creates_provenance_record(self) -> None:
        prov = ProvenanceLog()
        d = RecoverableDecision(
            code="VELOCITY_CLAMPED",
            severity="info",
            original_value=200,
            recovered_value=127,
            reason="Over MIDI max",
            musical_impact="Negligible",
        )
        prov.record_recoverable(d)
        assert len(prov.records) == 1
        assert prov.records[0].operation == "compromise"
        assert "VELOCITY_CLAMPED" in prov.records[0].source

    def test_recoverables_by_severity(self) -> None:
        prov = ProvenanceLog()
        prov.record_recoverable(RecoverableDecision(
            code="VELOCITY_CLAMPED", severity="info",
            original_value=0, recovered_value=1,
            reason="r", musical_impact="m",
        ))
        prov.record_recoverable(RecoverableDecision(
            code="BASS_NOTE_OUT_OF_RANGE", severity="warning",
            original_value=36, recovered_value=40,
            reason="r", musical_impact="m",
        ))
        prov.record_recoverable(RecoverableDecision(
            code="VELOCITY_CLAMPED", severity="info",
            original_value=0, recovered_value=1,
            reason="r", musical_impact="m",
        ))
        assert len(prov.recoverables_by_severity("info")) == 2
        assert len(prov.recoverables_by_severity("warning")) == 1
        assert len(prov.recoverables_by_severity("error")) == 0

    def test_recoverables_by_code(self) -> None:
        prov = ProvenanceLog()
        prov.record_recoverable(RecoverableDecision(
            code="VELOCITY_CLAMPED", severity="info",
            original_value=0, recovered_value=1,
            reason="r", musical_impact="m",
        ))
        prov.record_recoverable(RecoverableDecision(
            code="BASS_NOTE_OUT_OF_RANGE", severity="warning",
            original_value=36, recovered_value=40,
            reason="r", musical_impact="m",
        ))
        assert len(prov.recoverables_by_code("VELOCITY_CLAMPED")) == 1
        assert len(prov.recoverables_by_code("BASS_NOTE_OUT_OF_RANGE")) == 1
        assert len(prov.recoverables_by_code("NONEXISTENT")) == 0

    def test_has_blocking_decisions_false(self) -> None:
        prov = ProvenanceLog()
        prov.record_recoverable(RecoverableDecision(
            code="VELOCITY_CLAMPED", severity="info",
            original_value=0, recovered_value=1,
            reason="r", musical_impact="m",
        ))
        assert not prov.has_blocking_decisions()

    def test_has_blocking_decisions_true(self) -> None:
        prov = ProvenanceLog()
        prov.record_recoverable(RecoverableDecision(
            code="VELOCITY_CLAMPED", severity="error",
            original_value=200, recovered_value=127,
            reason="r", musical_impact="m",
        ))
        assert prov.has_blocking_decisions()

    def test_empty_provenance_no_blocking(self) -> None:
        prov = ProvenanceLog()
        assert not prov.has_blocking_decisions()
