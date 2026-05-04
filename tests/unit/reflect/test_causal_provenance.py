"""Tests for causal provenance graph features."""

from __future__ import annotations

from yao.reflect.provenance import ProvenanceLog, ProvenanceRecord


class TestCausalProvenanceRecord:
    """Test ProvenanceRecord causal fields."""

    def test_record_has_id(self) -> None:
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="generate_melody",
            parameters={},
            source="spec",
            rationale="test",
        )
        assert rec.record_id != ""
        assert len(rec.record_id) == 12

    def test_record_default_no_causes(self) -> None:
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="test",
            parameters={},
            source="spec",
            rationale="test",
        )
        assert rec.caused_by == ()

    def test_record_with_causes(self) -> None:
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="test",
            parameters={},
            source="spec",
            rationale="test",
            caused_by=("abc123", "def456"),
        )
        assert rec.caused_by == ("abc123", "def456")

    def test_backward_compat_no_id(self) -> None:
        """Records created without the new fields still work."""
        rec = ProvenanceRecord(
            timestamp="2024-01-01T00:00:00",
            layer="generator",
            operation="test",
            parameters={},
            source="spec",
            rationale="test",
        )
        assert rec.record_id == ""
        assert rec.caused_by == ()


class TestCausalProvenanceLog:
    """Test ProvenanceLog causal graph methods."""

    def _build_chain(self) -> tuple[ProvenanceLog, ProvenanceRecord, ProvenanceRecord, ProvenanceRecord]:
        """Build a 3-node causal chain: spec → plan → notes."""
        log = ProvenanceLog()
        r1 = log.record(
            layer="spec",
            operation="load_spec",
            parameters={"file": "comp.yaml"},
            source="user",
            rationale="user request",
        )
        r2 = log.record(
            layer="planner",
            operation="plan_form",
            parameters={"sections": 4},
            source="spec",
            rationale="from spec structure",
            caused_by=(r1.record_id,),
        )
        r3 = log.record(
            layer="generator",
            operation="generate_notes",
            parameters={"bars": 16},
            source="plan",
            rationale="fill sections with notes",
            caused_by=(r2.record_id,),
        )
        return log, r1, r2, r3

    def test_get_by_id(self) -> None:
        log, r1, _, _ = self._build_chain()
        found = log.get_by_id(r1.record_id)
        assert found is not None
        assert found.operation == "load_spec"

    def test_get_by_id_not_found(self) -> None:
        log, _, _, _ = self._build_chain()
        assert log.get_by_id("nonexistent") is None

    def test_get_causes(self) -> None:
        log, r1, r2, _ = self._build_chain()
        causes = log.get_causes(r2)
        assert len(causes) == 1
        assert causes[0].record_id == r1.record_id

    def test_get_effects(self) -> None:
        log, r1, r2, _ = self._build_chain()
        effects = log.get_effects(r1)
        assert len(effects) == 1
        assert effects[0].record_id == r2.record_id

    def test_root_has_no_causes(self) -> None:
        log, r1, _, _ = self._build_chain()
        assert log.get_causes(r1) == []

    def test_leaf_has_no_effects(self) -> None:
        log, _, _, r3 = self._build_chain()
        assert log.get_effects(r3) == []

    def test_trace_ancestry(self) -> None:
        log, r1, r2, r3 = self._build_chain()
        ancestry = log.trace_ancestry(r3)
        assert len(ancestry) == 2
        assert ancestry[0].record_id == r2.record_id  # nearest first
        assert ancestry[1].record_id == r1.record_id  # root last

    def test_trace_ancestry_from_root(self) -> None:
        log, r1, _, _ = self._build_chain()
        assert log.trace_ancestry(r1) == []

    def test_explain_chain_includes_causes(self) -> None:
        log, _, _, _ = self._build_chain()
        explanation = log.explain_chain()
        assert "Caused by:" in explanation

    def test_record_returns_record(self) -> None:
        log = ProvenanceLog()
        rec = log.record(
            layer="test",
            operation="op",
            parameters={},
            source="src",
            rationale="why",
        )
        assert isinstance(rec, ProvenanceRecord)
        assert rec.record_id != ""

    def test_multiple_causes(self) -> None:
        log = ProvenanceLog()
        r1 = log.record(layer="a", operation="op1", parameters={}, source="s", rationale="r")
        r2 = log.record(layer="b", operation="op2", parameters={}, source="s", rationale="r")
        r3 = log.record(
            layer="c",
            operation="merge",
            parameters={},
            source="s",
            rationale="merge two inputs",
            caused_by=(r1.record_id, r2.record_id),
        )
        causes = log.get_causes(r3)
        assert len(causes) == 2
