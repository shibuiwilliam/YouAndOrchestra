"""Context Buffer — fixed-size ring buffer for real-time MIDI context.

Stores recent MIDI note events and provides fast feature estimation
(key, chord, tempo) for role handlers. Fixed size prevents unbounded
memory growth during long sessions.

Belongs to improvise/ package.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class NoteEvent:
    """A timestamped MIDI note event.

    Attributes:
        pitch: MIDI note number (0-127).
        velocity: MIDI velocity (0-127, 0=note off).
        timestamp: Monotonic time in seconds.
        channel: MIDI channel (0-15).
    """

    pitch: int
    velocity: int
    timestamp: float
    channel: int = 0


# Note names for key estimation
_PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Major scale pitch class profiles (Krumhansl-Kessler weights)
_MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]


class ContextBuffer:
    """Fixed-size ring buffer for real-time MIDI context.

    Stores recent note events and provides instant feature estimation.
    The buffer never grows beyond ``max_events``.

    Args:
        max_events: Maximum number of events to store.
        window_sec: Time window for feature estimation (seconds).
    """

    def __init__(self, max_events: int = 960, window_sec: float = 8.0) -> None:
        self._buffer: deque[NoteEvent] = deque(maxlen=max_events)
        self._window_sec = window_sec
        self._max_events = max_events

    def push(self, event: NoteEvent) -> None:
        """Add a note event to the buffer.

        Args:
            event: The MIDI note event to add.
        """
        self._buffer.append(event)

    def recent_events(self, window_sec: float | None = None) -> list[NoteEvent]:
        """Get events within the time window.

        Args:
            window_sec: Time window (default: self._window_sec).

        Returns:
            List of recent events, oldest first.
        """
        now = monotonic()
        window = window_sec if window_sec is not None else self._window_sec
        cutoff = now - window
        return [e for e in self._buffer if e.timestamp >= cutoff]

    def all_events(self) -> list[NoteEvent]:
        """Get all events in the buffer."""
        return list(self._buffer)

    @property
    def size(self) -> int:
        """Current number of events."""
        return len(self._buffer)

    @property
    def max_size(self) -> int:
        """Maximum buffer capacity."""
        return self._max_events

    def clear(self) -> None:
        """Clear all events."""
        self._buffer.clear()

    def estimate_key(self) -> str:
        """Estimate the current key from pitch class distribution.

        Uses a simplified Krumhansl-Kessler algorithm on recent events.

        Returns:
            Key string (e.g., "C major"). Defaults to "C major" if empty.
        """
        events = self.all_events()
        if not events:
            return "C major"

        # Count pitch classes
        pc_counts = [0] * 12
        for e in events:
            if e.velocity > 0:
                pc_counts[e.pitch % 12] += 1

        if sum(pc_counts) == 0:
            return "C major"

        # Correlate with major profile for each root
        best_root = 0
        best_corr = -1.0
        for root in range(12):
            rotated = pc_counts[root:] + pc_counts[:root]
            corr = sum(a * b for a, b in zip(rotated, _MAJOR_PROFILE, strict=True))
            if corr > best_corr:
                best_corr = corr
                best_root = root

        return f"{_PC_NAMES[best_root]} major"

    def estimate_current_chord(self) -> str:
        """Estimate the most recent chord from the last beat of events.

        Returns:
            Chord name (e.g., "C", "Am"). Defaults to "C" if empty.
        """
        events = self.all_events()
        if not events:
            return "C"

        # Use last few events for chord estimation
        recent = events[-min(8, len(events)) :]
        pc_counts = [0] * 12
        for e in recent:
            if e.velocity > 0:
                pc_counts[e.pitch % 12] += 1

        if sum(pc_counts) == 0:
            return "C"

        root = pc_counts.index(max(pc_counts))
        return _PC_NAMES[root]

    def estimate_tempo(self) -> float:
        """Estimate tempo from inter-onset intervals.

        Returns:
            Estimated BPM. Defaults to 120.0 if insufficient data.
        """
        events = [e for e in self.all_events() if e.velocity > 0]
        if len(events) < 3:  # noqa: PLR2004
            return 120.0

        # Calculate inter-onset intervals
        intervals = [
            events[i].timestamp - events[i - 1].timestamp
            for i in range(1, len(events))
            if events[i].timestamp > events[i - 1].timestamp
        ]

        if not intervals:
            return 120.0

        avg_interval = sum(intervals) / len(intervals)
        if avg_interval <= 0:
            return 120.0

        # Assume each onset is approximately one beat
        bpm = 60.0 / avg_interval
        return max(40.0, min(300.0, bpm))
