"""Realtime Improvisation Engine — MIDI in/out loop.

Reads MIDI input, maintains context, generates responses via role handlers,
and sends output. All processing must complete within 50ms latency budget.

No disk writes during session. Export is explicit after stop().

Belongs to improvise/ package.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import structlog

from yao.improvise.context_buffer import ContextBuffer, NoteEvent
from yao.improvise.role_handlers import (
    ImprovisationRole,
    MidiResponse,
    get_handler,
)

logger = structlog.get_logger()

_LATENCY_BUDGET_MS = 50


@dataclass
class SessionLog:
    """Log of a live improvisation session (written after stop).

    Attributes:
        events_received: Total MIDI events received.
        responses_sent: Total responses sent.
        max_latency_ms: Maximum observed latency.
        avg_latency_ms: Average observed latency.
        duration_sec: Total session duration.
    """

    events_received: int = 0
    responses_sent: int = 0
    max_latency_ms: float = 0.0
    latency_sum_ms: float = 0.0
    duration_sec: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.responses_sent == 0:
            return 0.0
        return self.latency_sum_ms / self.responses_sent


class RealtimeImprovisationEngine:
    """Real-time MIDI improvisation engine.

    Runs a loop: MIDI input → context buffer → role handler → MIDI output.
    Latency budget: 50ms input-to-output.

    Usage::

        engine = RealtimeImprovisationEngine(
            role=ImprovisationRole.BASSIST,
            genre="jazz",
        )
        engine.start()  # blocks until stop() is called
        engine.stop()
        engine.export_log(Path("outputs/improvise/session.json"))
    """

    def __init__(
        self,
        role: ImprovisationRole = ImprovisationRole.ACCOMPANIST,
        genre: str = "default",
        buffer_size: int = 960,
        buffer_window_sec: float = 8.0,
    ) -> None:
        self._role = role
        self._genre = genre
        self._handler = get_handler(role)
        self._buffer = ContextBuffer(max_events=buffer_size, window_sec=buffer_window_sec)
        self._log = SessionLog()
        self._running = False
        self._start_time = 0.0

    @property
    def is_running(self) -> bool:
        """Whether the engine is currently running."""
        return self._running

    @property
    def session_log(self) -> SessionLog:
        """The current session log."""
        return self._log

    @property
    def context(self) -> ContextBuffer:
        """The context buffer (for testing)."""
        return self._buffer

    def process_note(self, pitch: int, velocity: int, channel: int = 0) -> list[MidiResponse]:
        """Process a single incoming MIDI note and generate responses.

        This is the core processing path. Must complete within 50ms.

        Args:
            pitch: MIDI note number.
            velocity: MIDI velocity (0 = note off).
            channel: MIDI channel.

        Returns:
            List of MidiResponse objects to send.
        """
        start = time.monotonic()

        # Add to context
        event = NoteEvent(
            pitch=pitch,
            velocity=velocity,
            timestamp=start,
            channel=channel,
        )
        self._buffer.push(event)
        self._log.events_received += 1

        # Generate response
        responses: list[MidiResponse] = []
        if velocity > 0:  # Only respond to note-on
            responses = self._handler.respond(self._buffer)

        # Record latency
        elapsed_ms = (time.monotonic() - start) * 1000.0
        self._log.responses_sent += len(responses)
        self._log.latency_sum_ms += elapsed_ms
        self._log.max_latency_ms = max(self._log.max_latency_ms, elapsed_ms)

        if elapsed_ms > _LATENCY_BUDGET_MS:
            logger.warning(
                "latency_budget_exceeded",
                latency_ms=round(elapsed_ms, 2),
                budget_ms=_LATENCY_BUDGET_MS,
            )

        return responses

    def start(self) -> None:
        """Mark the engine as running.

        In a full implementation, this would open MIDI ports via mido.
        For now, it sets the running flag for process_note() to be called
        externally.
        """
        self._running = True
        self._start_time = time.monotonic()
        self._log = SessionLog()
        logger.info(
            "improvisation_started",
            role=self._role.value,
            genre=self._genre,
        )

    def stop(self) -> SessionLog:
        """Stop the engine and return the session log.

        Returns:
            SessionLog with statistics.
        """
        self._running = False
        self._log.duration_sec = time.monotonic() - self._start_time
        logger.info(
            "improvisation_stopped",
            events=self._log.events_received,
            responses=self._log.responses_sent,
            avg_latency_ms=round(self._log.avg_latency_ms, 2),
            max_latency_ms=round(self._log.max_latency_ms, 2),
        )
        return self._log
