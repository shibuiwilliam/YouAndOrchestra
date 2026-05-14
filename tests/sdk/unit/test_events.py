"""Tests for yao.sdk.events — streaming event types."""

from __future__ import annotations

from yao.sdk.events import (
    AudioReadyEvent,
    ConductorFinishedEvent,
    CritiqueAvailableEvent,
    EvaluationReportEvent,
    IterationCompletedEvent,
    PhaseCompletedEvent,
    PhaseStartedEvent,
    ProvenanceUpdatedEvent,
    SubagentStartedEvent,
    YaoEvent,
)


class TestYaoEvent:
    def test_base_event_defaults(self) -> None:
        event = YaoEvent()
        assert event.iteration == 0
        assert event.phase == ""
        assert event.timestamp_ms > 0

    def test_phase_started(self) -> None:
        event = PhaseStartedEvent(phase="intent_crystallization")
        assert event.phase == "intent_crystallization"
        assert event.intent_summary is None

    def test_phase_completed(self) -> None:
        event = PhaseCompletedEvent(phase="skeletal_generation")
        assert event.phase == "skeletal_generation"

    def test_subagent_started(self) -> None:
        event = SubagentStartedEvent(subagent_name="composer")
        assert event.subagent_name == "composer"

    def test_iteration_completed(self) -> None:
        event = IterationCompletedEvent(
            iteration=1,
            iteration_path="outputs/projects/test/iterations/v001",
            evaluation={"pass_rate": 0.8},
            pass_status=True,
        )
        assert event.iteration == 1
        assert event.pass_status is True

    def test_evaluation_report(self) -> None:
        event = EvaluationReportEvent(
            evaluation_json_path="path/to/eval.json",
            scores={"melody": 0.9},
        )
        assert event.scores["melody"] == 0.9

    def test_critique_available(self) -> None:
        event = CritiqueAvailableEvent(
            critique_md_path="path/to/critique.md",
            severity_counts={"critical": 0, "major": 2},
        )
        assert event.severity_counts["major"] == 2

    def test_audio_ready(self) -> None:
        event = AudioReadyEvent(wav_path="audio.wav", duration_seconds=90.0)
        assert event.duration_seconds == 90.0

    def test_provenance_updated(self) -> None:
        event = ProvenanceUpdatedEvent(provenance_path="prov.json", record_count=5)
        assert event.record_count == 5

    def test_conductor_finished(self) -> None:
        event = ConductorFinishedEvent(
            final_iteration_path="v003",
            total_iterations=3,
            status="completed",
        )
        assert event.status == "completed"
        assert event.total_iterations == 3


class TestEventInheritance:
    def test_all_events_are_yao_events(self) -> None:
        event_classes = [
            PhaseStartedEvent,
            PhaseCompletedEvent,
            SubagentStartedEvent,
            IterationCompletedEvent,
            EvaluationReportEvent,
            CritiqueAvailableEvent,
            AudioReadyEvent,
            ProvenanceUpdatedEvent,
            ConductorFinishedEvent,
        ]
        for cls in event_classes:
            instance = cls()
            assert isinstance(instance, YaoEvent), f"{cls.__name__} not a YaoEvent"
