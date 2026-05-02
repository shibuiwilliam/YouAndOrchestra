"""Live Improvisation Engine — real-time MIDI accompaniment.

Requires optional dependencies: ``pip install yao[live]``

All ``mido`` and real-time MIDI imports are confined to this package.
Missing dependencies produce ``LiveBackendUnavailableError``.
"""

from __future__ import annotations

from yao.errors import YaOError


class LiveBackendUnavailableError(YaOError):
    """Raised when live improvisation dependencies are not installed."""
