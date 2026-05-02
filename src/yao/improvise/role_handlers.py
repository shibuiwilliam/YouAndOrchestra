"""Role Handlers — improvisation role logic for real-time response.

Each role responds to the current context within the 50ms latency budget.
No heavy computation allowed in the response path.

Belongs to improvise/ package.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from yao.improvise.context_buffer import ContextBuffer


class ImprovisationRole(Enum):
    """Available improvisation roles."""

    BASSIST = "bassist"
    DRUMMER = "drummer"
    ACCOMPANIST = "accompanist"
    MELODY_FOLLOWER = "melody_follower"


@dataclass(frozen=True)
class MidiResponse:
    """A MIDI response to send to the output port.

    Attributes:
        pitch: MIDI note number.
        velocity: MIDI velocity (0 = note off).
        channel: MIDI channel.
        duration_ms: How long to hold the note (ms).
    """

    pitch: int
    velocity: int
    channel: int = 0
    duration_ms: int = 200


class RoleHandler:
    """Base class for role-specific improvisation handlers."""

    def respond(self, context: ContextBuffer) -> list[MidiResponse]:
        """Generate a response based on current context.

        Must complete within 50ms.

        Args:
            context: The current MIDI context buffer.

        Returns:
            List of MIDI responses to send.
        """
        return []


class BassistHandler(RoleHandler):
    """Plays bass notes following the chord root."""

    def respond(self, context: ContextBuffer) -> list[MidiResponse]:
        """Generate bass response.

        Plays the root of the estimated current chord in a low octave.
        """
        chord = context.estimate_current_chord()
        # Map chord name to pitch class
        pc_map = {
            "C": 0,
            "C#": 1,
            "D": 2,
            "D#": 3,
            "E": 4,
            "F": 5,
            "F#": 6,
            "G": 7,
            "G#": 8,
            "A": 9,
            "A#": 10,
            "B": 11,
        }
        pc = pc_map.get(chord, 0)
        # Bass octave: MIDI 36-47 (C2-B2)
        pitch = 36 + pc
        return [MidiResponse(pitch=pitch, velocity=80, duration_ms=400)]


class DrummerHandler(RoleHandler):
    """Plays simple drum pattern on channel 9 (GM drums)."""

    def respond(self, context: ContextBuffer) -> list[MidiResponse]:
        """Generate drum response.

        Plays a kick on the estimated downbeat.
        """
        # GM drum mapping: kick=36, snare=38, hi-hat=42
        return [
            MidiResponse(pitch=36, velocity=90, channel=9, duration_ms=100),
            MidiResponse(pitch=42, velocity=60, channel=9, duration_ms=50),
        ]


class AccompanistHandler(RoleHandler):
    """Plays chord voicings based on estimated harmony."""

    def respond(self, context: ContextBuffer) -> list[MidiResponse]:
        """Generate accompaniment response.

        Plays a simple triad based on the estimated chord.
        """
        chord = context.estimate_current_chord()
        pc_map = {
            "C": 0,
            "C#": 1,
            "D": 2,
            "D#": 3,
            "E": 4,
            "F": 5,
            "F#": 6,
            "G": 7,
            "G#": 8,
            "A": 9,
            "A#": 10,
            "B": 11,
        }
        pc = pc_map.get(chord, 0)
        # Major triad in octave 4
        root = 60 + pc
        return [
            MidiResponse(pitch=root, velocity=65, duration_ms=300),
            MidiResponse(pitch=root + 4, velocity=60, duration_ms=300),
            MidiResponse(pitch=root + 7, velocity=60, duration_ms=300),
        ]


class MelodyFollowerHandler(RoleHandler):
    """Follows the melody with harmonized intervals."""

    def respond(self, context: ContextBuffer) -> list[MidiResponse]:
        """Generate melody-following response.

        Adds a third or fifth above the most recent note.
        """
        events = context.all_events()
        if not events:
            return []

        last = events[-1]
        if last.velocity == 0:
            return []

        # Harmonize a third above
        harmony_pitch = last.pitch + 4  # major third
        if harmony_pitch > 127:
            harmony_pitch = last.pitch - 8  # octave below + third

        return [MidiResponse(pitch=harmony_pitch, velocity=last.velocity - 10, duration_ms=200)]


def get_handler(role: ImprovisationRole) -> RoleHandler:
    """Get the handler for a given role.

    Args:
        role: The improvisation role.

    Returns:
        A RoleHandler instance.
    """
    handlers: dict[ImprovisationRole, type[RoleHandler]] = {
        ImprovisationRole.BASSIST: BassistHandler,
        ImprovisationRole.DRUMMER: DrummerHandler,
        ImprovisationRole.ACCOMPANIST: AccompanistHandler,
        ImprovisationRole.MELODY_FOLLOWER: MelodyFollowerHandler,
    }
    cls = handlers.get(role)
    if cls is None:
        msg = f"Unknown role: {role}"
        raise ValueError(msg)
    return cls()
