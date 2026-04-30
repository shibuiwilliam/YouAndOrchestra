"""RecoverableDecision — explicit, logged compromises.

Replaces silent fallbacks with traceable decisions. Every time the system
must compromise (clamp a value, skip a note, default a parameter), it
records a RecoverableDecision instead of silently proceeding.

This is Pillar 3 of the v2.0 verification system (PROJECT.md §9.1).
See CLAUDE.md Rule #3: "No silent fallbacks."

Cross-cutting concern, lives in reflect/ (Layer 1) alongside provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from yao.reflect.recoverable_codes import validate_code


@dataclass(frozen=True)
class RecoverableDecision:
    """A logged compromise — a non-silent fallback with full context.

    Attributes:
        code: SCREAMING_SNAKE_CASE identifier (must be in KNOWN_CODES).
        severity: How serious the compromise is.
        original_value: What was intended.
        recovered_value: What was used instead.
        reason: Human-readable cause.
        musical_impact: What the listener will perceive.
        suggested_fix: Upstream remedies the user could apply.
    """

    code: str
    severity: Literal["info", "warning", "error"]
    original_value: Any
    recovered_value: Any
    reason: str
    musical_impact: str
    suggested_fix: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate that the code is registered."""
        validate_code(self.code)

    @property
    def is_blocking(self) -> bool:
        """Whether this decision should halt the pipeline."""
        return self.severity == "error"
