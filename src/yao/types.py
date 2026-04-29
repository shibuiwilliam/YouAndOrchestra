"""Shared type aliases used across all YaO layers.

These aliases improve readability and make the domain semantics explicit.
Do not confuse Tick (MIDI resolution) with Beat (musical pulse) or Seconds
(wall-clock time). See CLAUDE.md §7 for the strict separation rules.

NOTE: This module intentionally does NOT use ``from __future__ import annotations``
because deferred evaluation converts TypeAlias annotations to strings, which mypy
cannot resolve as valid types in downstream modules.
"""

from typing import TypeAlias

MidiNote: TypeAlias = int
"""MIDI note number (0–127). C4 = 60."""

Velocity: TypeAlias = int
"""MIDI velocity (0–127)."""

Tick: TypeAlias = int
"""MIDI tick — depends on PPQ resolution."""

Beat: TypeAlias = float
"""Musical beat position (1.0 = one quarter note)."""

Seconds: TypeAlias = float
"""Wall-clock time in seconds."""

BPM: TypeAlias = float
"""Tempo in beats per minute."""
