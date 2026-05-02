"""YaO custom exception hierarchy.

All exceptions raised by YaO code MUST be subclasses of ``YaOError``.
Raw ``ValueError`` / ``TypeError`` raises are prohibited (see CLAUDE.md §6).
"""

from __future__ import annotations


class YaOError(Exception):
    """Base exception for all YaO errors."""


class SpecValidationError(YaOError):
    """Raised when a YAML specification fails validation."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class ConstraintViolationError(YaOError):
    """Raised when a musical constraint is violated."""


class RangeViolationError(ConstraintViolationError):
    """Raised when a note falls outside an instrument's playable range.

    Error messages include the note name in scientific pitch notation
    and actionable suggestions (PROJECT_IMPROVEMENT §5.4).

    Attributes:
        instrument: Name of the instrument.
        note: MIDI note number that violated the range.
        valid_low: Lowest valid MIDI note for the instrument.
        valid_high: Highest valid MIDI note for the instrument.
    """

    def __init__(
        self,
        instrument: str,
        note: int,
        valid_low: int,
        valid_high: int,
    ) -> None:
        self.instrument = instrument
        self.note = note
        self.valid_low = valid_low
        self.valid_high = valid_high

        note_name = _midi_to_name(note)
        low_name = _midi_to_name(valid_low)
        high_name = _midi_to_name(valid_high)

        direction = "above" if note > valid_high else "below"
        semitones_off = note - valid_high if note > valid_high else valid_low - note

        suggestions: list[str] = []
        if note > valid_high:
            suggestions.append(f"transpose down {semitones_off} semitones")
            suggestions.append("assign to a higher-range instrument")
        else:
            suggestions.append(f"transpose up {semitones_off} semitones")
            suggestions.append("assign to a lower-range instrument")

        msg = (
            f"{note_name} (MIDI {note}) is {direction} the range for "
            f"{instrument} ({low_name}={valid_low} to {high_name}={valid_high}). "
            f"Consider: {'; '.join(suggestions)}."
        )
        super().__init__(msg)


def _midi_to_name(midi: int) -> str:
    """Convert MIDI note to name without importing from ir.notation (avoid circular)."""
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    if not 0 <= midi <= 127:
        return str(midi)
    octave = (midi // 12) - 1
    pitch_class = midi % 12
    return f"{names[pitch_class]}{octave}"


class ExpressionValidationError(ConstraintViolationError):
    """Raised when a performance expression value is out of valid range.

    Examples: CC value outside [0, 127], pitch bend outside [-8192, +8191],
    accent_strength outside [0.0, 1.0].
    """


class LayerViolationError(YaOError):
    """Raised when an architectural layer boundary is violated."""


class RenderError(YaOError):
    """Raised when rendering (MIDI/audio/score) fails."""


class VerificationError(YaOError):
    """Raised when verification detects a critical issue."""


class ProvenanceError(YaOError):
    """Raised when provenance recording fails or is violated."""


class MissingRightsStatusError(YaOError):
    """Raised when a reference has unknown or missing rights status.

    All reference material must have explicit licensing.
    ``unknown`` is not acceptable (CLAUDE.md copyright rules).
    """


class ForbiddenExtractionError(YaOError):
    """Raised when attempting to extract a forbidden feature from a reference.

    Features like melody_contour and chord_progression are blocked at
    both schema level and runtime for copyright protection.
    """


class NeuralBackendUnavailableError(YaOError):
    """Raised when a neural backend (torch, audiocraft, etc.) is not installed.

    The error message includes installation instructions.
    """


class NeuralGenerationTimeoutError(YaOError):
    """Raised when neural generation exceeds the timeout budget."""


class BackendNotConfiguredError(YaOError):
    """Raised when an agent backend is used without required configuration.

    For AnthropicAPIBackend: missing ANTHROPIC_API_KEY.
    For ClaudeCodeBackend: Claude Code SDK not available.
    """


class AgentBackendError(YaOError):
    """Raised when an agent backend encounters an operational error.

    Covers: API errors, timeout, malformed responses.
    Never silently falls back — always raises.
    """


class AgentOutputParseError(AgentBackendError):
    """Raised when the LLM response cannot be parsed into AgentOutput.

    The raw response content is attached for debugging.
    """

    def __init__(self, message: str, *, raw_content: str | None = None) -> None:
        self.raw_content = raw_content
        super().__init__(message)
