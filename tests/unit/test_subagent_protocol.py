"""Tests for subagent protocol — PR-5.

Verifies that:
- ProvenanceRecord can store agent, phase, confidence fields
- SubagentMessage dataclass works correctly
- Backward compatibility is preserved (old records still work)
"""

from __future__ import annotations

from pathlib import Path

from yao.conductor.protocol import Phase
from yao.conductor.subagent_message import Decision, Question, SubagentMessage
from yao.reflect.provenance import ProvenanceLog, ProvenanceRecord


class TestProvenanceSubagentFields:
    """Test that ProvenanceRecord supports v2.0 subagent fields."""

    def test_create_record_with_agent_and_phase(self) -> None:
        """ProvenanceRecord.create accepts agent, phase, confidence."""
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="choose_chord_progression",
            parameters={"key": "C", "mode": "major"},
            source="harmony_theorist",
            rationale="ii-V-I is idiomatic for jazz",
            agent="harmony_theorist",
            phase="SKELETAL_GENERATION",
            confidence=0.85,
        )

        assert rec.agent == "harmony_theorist"
        assert rec.phase == "SKELETAL_GENERATION"
        assert rec.confidence == 0.85

    def test_create_record_with_alternatives_rejected(self) -> None:
        """ProvenanceRecord stores alternatives_rejected."""
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="choose_voicing",
            parameters={"chord": "Dm7"},
            source="harmony_theorist",
            rationale="Drop-2 voicing for smooth voice leading",
            agent="harmony_theorist",
            phase="DETAILED_FILLING",
            confidence=0.72,
            alternatives_rejected=("root_position", "drop_3"),
        )

        assert rec.alternatives_rejected == ("root_position", "drop_3")

    def test_create_record_with_skill_referenced(self) -> None:
        """ProvenanceRecord stores skill_referenced."""
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="select_groove",
            parameters={"bpm": 90},
            source="rhythm_architect",
            rationale="Boom-bap pattern per lo-fi Skill",
            agent="rhythm_architect",
            phase="SKELETAL_GENERATION",
            confidence=0.9,
            skill_referenced="lo_fi_hiphop",
        )

        assert rec.skill_referenced == "lo_fi_hiphop"

    def test_backward_compatibility_no_new_fields(self) -> None:
        """Records created without v2.0 fields still work."""
        rec = ProvenanceRecord.create(
            layer="render",
            operation="write_midi",
            parameters={"path": "output.mid"},
            source="midi_writer",
            rationale="Final render output",
        )

        assert rec.agent is None
        assert rec.phase is None
        assert rec.confidence is None
        assert rec.alternatives_rejected == ()
        assert rec.skill_referenced is None

    def test_provenance_log_record_with_subagent_fields(self) -> None:
        """ProvenanceLog.record() passes through v2.0 fields."""
        log = ProvenanceLog()
        rec = log.record(
            layer="generator",
            operation="generate_melody",
            parameters={"scale": "dorian"},
            source="composer",
            rationale="Dorian mode fits the modal jazz spec",
            agent="composer",
            phase="DETAILED_FILLING",
            confidence=0.78,
            alternatives_rejected=("mixolydian", "aeolian"),
            skill_referenced="modal_jazz",
        )

        assert len(log) == 1
        assert rec.agent == "composer"
        assert rec.phase == "DETAILED_FILLING"
        assert rec.confidence == 0.78
        assert rec.alternatives_rejected == ("mixolydian", "aeolian")
        assert rec.skill_referenced == "modal_jazz"

    def test_provenance_record_is_frozen(self) -> None:
        """ProvenanceRecord remains immutable with new fields."""
        rec = ProvenanceRecord.create(
            layer="generator",
            operation="test",
            parameters={},
            source="test",
            rationale="test",
            agent="composer",
            phase="INTENT_CRYSTALLIZATION",
            confidence=0.5,
        )

        import dataclasses

        assert dataclasses.is_dataclass(rec)
        # Frozen dataclass should raise on attribute assignment
        try:
            rec.agent = "other"  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except dataclasses.FrozenInstanceError:
            pass

    def test_provenance_json_includes_new_fields(self) -> None:
        """Serialization to JSON includes the v2.0 fields."""
        import json

        log = ProvenanceLog()
        log.record(
            layer="generator",
            operation="test_op",
            parameters={},
            source="test",
            rationale="test rationale",
            agent="mix_engineer",
            phase="LISTENING_SIMULATION",
            confidence=0.65,
        )

        data = json.loads(log.to_json())
        assert len(data) == 1
        assert data[0]["agent"] == "mix_engineer"
        assert data[0]["phase"] == "LISTENING_SIMULATION"
        assert data[0]["confidence"] == 0.65


class TestSubagentMessage:
    """Test SubagentMessage dataclass."""

    def test_create_basic_message(self) -> None:
        """SubagentMessage can be instantiated with required fields."""
        msg = SubagentMessage(
            agent="harmony_theorist",
            phase=Phase.SKELETAL_GENERATION,
            input_hash="abc123def456",
        )

        assert msg.agent == "harmony_theorist"
        assert msg.phase == Phase.SKELETAL_GENERATION
        assert msg.input_hash == "abc123def456"
        assert msg.decisions == []
        assert msg.questions_to_other_agents == []
        assert msg.flags == []
        assert msg.artifacts == []

    def test_create_full_message(self) -> None:
        """SubagentMessage with all fields populated."""
        decision = Decision(
            domain="harmony",
            description="Selected Dm7-G7-Cmaj7",
            rationale="ii-V-I for jazz",
            confidence=0.85,
            alternatives_rejected=["Dm-G-C", "Dm7b5-G7alt-Cmaj7#11"],
        )
        question = Question(
            target_agent="rhythm_architect",
            content="Anticipation on beat 4?",
            context="Medium swing 132 BPM",
        )

        msg = SubagentMessage(
            agent="harmony_theorist",
            phase=Phase.SKELETAL_GENERATION,
            input_hash="abc123def456",
            decisions=[decision],
            questions_to_other_agents=[question],
            flags=["genre_boundary"],
            artifacts=[Path("output/harmony.json")],
        )

        assert len(msg.decisions) == 1
        assert msg.decisions[0].confidence == 0.85
        assert msg.decisions[0].alternatives_rejected == ["Dm-G-C", "Dm7b5-G7alt-Cmaj7#11"]
        assert len(msg.questions_to_other_agents) == 1
        assert msg.questions_to_other_agents[0].target_agent == "rhythm_architect"
        assert msg.flags == ["genre_boundary"]
        assert msg.artifacts == [Path("output/harmony.json")]

    def test_message_is_frozen(self) -> None:
        """SubagentMessage is immutable."""
        import dataclasses

        msg = SubagentMessage(
            agent="composer",
            phase=Phase.DETAILED_FILLING,
            input_hash="xyz",
        )

        try:
            msg.agent = "other"  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except dataclasses.FrozenInstanceError:
            pass

    def test_decision_dataclass(self) -> None:
        """Decision dataclass works correctly."""
        d = Decision(
            domain="rhythm",
            description="4/4 time signature",
            rationale="Standard for pop",
            confidence=0.95,
        )

        assert d.domain == "rhythm"
        assert d.alternatives_rejected == []

    def test_question_dataclass(self) -> None:
        """Question dataclass works correctly."""
        q = Question(
            target_agent="orchestrator",
            content="Should strings double the melody?",
        )

        assert q.target_agent == "orchestrator"
        assert q.context == ""
