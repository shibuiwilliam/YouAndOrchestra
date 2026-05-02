"""Performance Expression IR — Layer 4.5.

This module defines the data structures for musical performance expression:
articulation, dynamics curves, microtiming, CC automation, and pedaling.

**Design principle**: PerformanceLayer is an *overlay* on ScoreIR.
It never mutates Note objects. Instead, it maps NoteId → NoteExpression,
allowing renderers to apply expression data during MIDI/audio output.

All types are frozen dataclasses for immutability and provenance compatibility.

Belongs to Layer 4.5 (conceptual), physically in ir/ (Layer 1 import level).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.errors import ExpressionValidationError
from yao.types import Beat, MidiNote

# ---------------------------------------------------------------------------
# NoteId — unique identifier for a Note within a ScoreIR
# ---------------------------------------------------------------------------

NoteId = tuple[str, Beat, MidiNote]
"""Unique note identifier: (instrument, start_beat, pitch).

This triple uniquely identifies a Note in a ScoreIR under the convention
that no two notes share the same instrument, start beat, and pitch.
"""


# ---------------------------------------------------------------------------
# NoteExpression — per-note performance data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NoteExpression:
    """Performance expression data for a single note.

    All fields are optional overlays — default values produce no modification.
    Renderers read these to adjust MIDI output without mutating the ScoreIR.

    Attributes:
        legato_overlap: Overlap with the next note in seconds. 0.0 = normal.
        accent_strength: Accent intensity [0.0, 1.0]. 0.0 = no accent.
        glissando_to: Target MIDI pitch for glissando, or None.
        pitch_bend_curve: Sequence of (beat_offset, value) pairs.
            beat_offset is relative to note start. value in [-8192, +8191].
        cc_curves: Mapping from CC number to curve points.
            Each curve is (beat_offset, value) with value in [0, 127].
        micro_timing_ms: Timing offset in milliseconds. Positive = late.
        micro_dynamics: Velocity modifier in [-1.0, +1.0].
            Applied as multiplicative factor: final_vel = vel * (1 + micro_dynamics).
    """

    legato_overlap: float = 0.0
    accent_strength: float = 0.0
    glissando_to: MidiNote | None = None
    pitch_bend_curve: tuple[tuple[float, float], ...] | None = None
    cc_curves: dict[int, tuple[tuple[float, float], ...]] | None = None
    micro_timing_ms: float = 0.0
    micro_dynamics: float = 0.0

    def validate(self) -> None:
        """Validate all fields are within allowed ranges.

        Raises:
            ExpressionValidationError: If any field violates constraints.
        """
        if not 0.0 <= self.accent_strength <= 1.0:
            raise ExpressionValidationError(f"accent_strength must be in [0.0, 1.0], got {self.accent_strength}.")

        if not -1.0 <= self.micro_dynamics <= 1.0:
            raise ExpressionValidationError(f"micro_dynamics must be in [-1.0, 1.0], got {self.micro_dynamics}.")

        if self.glissando_to is not None and not 0 <= self.glissando_to <= 127:
            raise ExpressionValidationError(f"glissando_to must be a valid MIDI note (0-127), got {self.glissando_to}.")

        if self.pitch_bend_curve is not None:
            for offset, value in self.pitch_bend_curve:
                if not -8192 <= value <= 8191:
                    raise ExpressionValidationError(
                        f"Pitch bend value must be in [-8192, +8191], got {value} at offset {offset}."
                    )

        if self.cc_curves is not None:
            for cc_num, points in self.cc_curves.items():
                if not 0 <= cc_num <= 127:
                    raise ExpressionValidationError(f"CC number must be in [0, 127], got {cc_num}.")
                for offset, value in points:
                    if not 0 <= value <= 127:
                        raise ExpressionValidationError(
                            f"CC value must be in [0, 127], got {value} for CC{cc_num} at offset {offset}."
                        )


# ---------------------------------------------------------------------------
# Section-level expression types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RubatoCurve:
    """Tempo variation curve for a section.

    Allows local speeding up and slowing down within a section.
    Waypoints define (beat_position, tempo_ratio) where 1.0 = written tempo.

    Attributes:
        section_name: Name of the section this applies to.
        waypoints: Sequence of (beat, tempo_ratio) pairs.
            tempo_ratio > 1.0 = faster, < 1.0 = slower.
    """

    section_name: str
    waypoints: tuple[tuple[Beat, float], ...]

    def validate(self) -> None:
        """Validate waypoints have positive tempo ratios.

        Raises:
            ExpressionValidationError: If any tempo ratio is non-positive.
        """
        for beat, ratio in self.waypoints:
            if ratio <= 0.0:
                raise ExpressionValidationError(f"Rubato tempo_ratio must be positive, got {ratio} at beat {beat}.")


@dataclass(frozen=True)
class BreathMark:
    """A breath mark — a brief silence for phrasing.

    Attributes:
        beat_position: Beat where the breath occurs.
        duration_beats: Length of the breath in beats.
        instrument: Instrument this applies to, or None for all instruments.
    """

    beat_position: Beat
    duration_beats: Beat
    instrument: str | None = None

    def validate(self) -> None:
        """Validate breath mark has non-negative duration.

        Raises:
            ExpressionValidationError: If duration is negative.
        """
        if self.duration_beats < 0:
            raise ExpressionValidationError(f"BreathMark duration must be non-negative, got {self.duration_beats}.")


@dataclass(frozen=True)
class PedalCurve:
    """A continuous controller curve for pedaling or similar effects.

    Typically CC64 (sustain pedal), but can be any CC.

    Attributes:
        cc_number: MIDI CC number (typically 64 for sustain).
        instrument: Instrument this applies to.
        events: Sequence of (beat, value) pairs. value in [0, 127].
    """

    cc_number: int
    instrument: str
    events: tuple[tuple[Beat, int], ...]

    def validate(self) -> None:
        """Validate CC number and event values.

        Raises:
            ExpressionValidationError: If values are out of MIDI range.
        """
        if not 0 <= self.cc_number <= 127:
            raise ExpressionValidationError(f"PedalCurve cc_number must be in [0, 127], got {self.cc_number}.")
        for beat, value in self.events:
            if not 0 <= value <= 127:
                raise ExpressionValidationError(
                    f"PedalCurve event value must be in [0, 127], got {value} at beat {beat}."
                )


# ---------------------------------------------------------------------------
# PerformanceLayer — the top-level overlay container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerformanceLayer:
    """Overlay of performance expression data on a ScoreIR.

    This is the primary output of Performance Realizers (Step 6.5).
    It does NOT modify the ScoreIR — renderers combine both at output time.

    Attributes:
        note_expressions: Mapping from NoteId to per-note expression.
        section_rubato: Mapping from section name to rubato curve.
        breath_marks: Sequence of breath marks.
        pedal_curves: Sequence of pedal/CC automation curves.
    """

    note_expressions: dict[NoteId, NoteExpression]
    section_rubato: dict[str, RubatoCurve]
    breath_marks: tuple[BreathMark, ...]
    pedal_curves: tuple[PedalCurve, ...]

    def for_note(self, note_id: NoteId) -> NoteExpression | None:
        """Look up expression for a specific note.

        Args:
            note_id: The (instrument, start_beat, pitch) triple.

        Returns:
            NoteExpression if found, None otherwise.
        """
        return self.note_expressions.get(note_id)

    def rubato_for_section(self, section_name: str) -> RubatoCurve | None:
        """Look up rubato curve for a section.

        Args:
            section_name: Section name.

        Returns:
            RubatoCurve if defined, None otherwise.
        """
        return self.section_rubato.get(section_name)

    def pedals_for_instrument(self, instrument: str) -> list[PedalCurve]:
        """Return all pedal curves for a given instrument.

        Args:
            instrument: Instrument name.

        Returns:
            List of PedalCurve objects for that instrument.
        """
        return [pc for pc in self.pedal_curves if pc.instrument == instrument]

    def breaths_for_instrument(self, instrument: str | None = None) -> list[BreathMark]:
        """Return breath marks for a specific instrument or all instruments.

        Args:
            instrument: Instrument name, or None for global breaths.

        Returns:
            List of matching BreathMark objects.
        """
        if instrument is None:
            return [bm for bm in self.breath_marks if bm.instrument is None]
        return [bm for bm in self.breath_marks if bm.instrument is None or bm.instrument == instrument]

    def validate(self) -> None:
        """Validate all contained expressions and curves.

        Raises:
            ExpressionValidationError: If any contained element is invalid.
        """
        for expr in self.note_expressions.values():
            expr.validate()
        for rubato in self.section_rubato.values():
            rubato.validate()
        for bm in self.breath_marks:
            bm.validate()
        for pc in self.pedal_curves:
            pc.validate()

    @classmethod
    def empty(cls) -> PerformanceLayer:
        """Create an empty PerformanceLayer (no expression data).

        Returns:
            A PerformanceLayer with empty collections.
        """
        return cls(
            note_expressions={},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )
