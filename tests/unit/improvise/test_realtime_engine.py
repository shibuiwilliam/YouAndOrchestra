"""Tests for Realtime Improvisation Engine."""

from __future__ import annotations

from yao.improvise.realtime_engine import RealtimeImprovisationEngine
from yao.improvise.role_handlers import ImprovisationRole


class TestEngine:
    def test_creates_without_crash(self) -> None:
        engine = RealtimeImprovisationEngine(
            role=ImprovisationRole.BASSIST,
            genre="jazz",
        )
        assert not engine.is_running

    def test_process_note_returns_responses(self) -> None:
        engine = RealtimeImprovisationEngine(role=ImprovisationRole.ACCOMPANIST)
        engine.start()
        responses = engine.process_note(60, 80)
        assert len(responses) > 0
        engine.stop()

    def test_latency_within_budget(self) -> None:
        engine = RealtimeImprovisationEngine(role=ImprovisationRole.BASSIST)
        engine.start()
        # Process multiple notes
        for i in range(20):
            engine.process_note(60 + (i % 12), 80)
        log = engine.stop()
        # Max latency should be well within 50ms for mock processing
        assert log.max_latency_ms < 50.0

    def test_session_log_statistics(self) -> None:
        engine = RealtimeImprovisationEngine(role=ImprovisationRole.DRUMMER)
        engine.start()
        for _ in range(5):
            engine.process_note(60, 80)
        log = engine.stop()
        assert log.events_received == 5
        assert log.responses_sent > 0
        assert log.avg_latency_ms >= 0
        assert log.duration_sec > 0

    def test_graceful_stop(self) -> None:
        engine = RealtimeImprovisationEngine()
        engine.start()
        assert engine.is_running
        log = engine.stop()
        assert not engine.is_running
        assert log.duration_sec >= 0
