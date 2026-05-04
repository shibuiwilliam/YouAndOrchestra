"""Pydantic model for conversation.yaml specification.

Defines inter-instrument dialogue patterns and voice focus assignments.
Cross-spec validates instrument names and section names against composition.yaml.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from yao.errors import SpecValidationError


class ConversationEventSpec(BaseModel):
    """Specification for a single conversation event.

    Attributes:
        type: Dialogue pattern type.
        initiator: Instrument that starts.
        responder: Instrument that responds (optional for tutti/solo_break).
        section_id: Section where this event occurs.
        start_bar: Start bar within section (0-indexed).
        end_bar: End bar within section (exclusive).
        minimum_silence_beats: Minimum silence before a fill triggers.
    """

    type: Literal["call_response", "fill_in_response", "tutti", "solo_break", "trade"]
    initiator: str
    responder: str | None = None
    section_id: str
    start_bar: int = 0
    end_bar: int = 4
    minimum_silence_beats: float = 1.0

    @field_validator("start_bar")
    @classmethod
    def start_bar_non_negative(cls, v: int) -> int:
        """Start bar must be non-negative."""
        if v < 0:
            raise SpecValidationError(
                f"start_bar must be >= 0, got {v}",
                field="conversation.events.start_bar",
            )
        return v

    @model_validator(mode="after")
    def end_after_start(self) -> ConversationEventSpec:
        """End bar must be after start bar."""
        if self.end_bar <= self.start_bar:
            raise SpecValidationError(
                f"end_bar ({self.end_bar}) must be > start_bar ({self.start_bar})",
                field="conversation.events",
            )
        return self


class VoiceFocusSpec(BaseModel):
    """Voice focus assignment for a section.

    Attributes:
        section_id: Which section this applies to.
        primary: The primary (lead) instrument.
        accompaniment: Supporting instruments.
        fill_capable: Instruments that can insert reactive fills.
    """

    section_id: str
    primary: str
    accompaniment: list[str] = Field(default_factory=list)
    fill_capable: list[str] = Field(default_factory=list)


class ConversationSpec(BaseModel):
    """Root model for conversation.yaml.

    Attributes:
        voice_focus: Per-section voice focus assignments.
        events: Conversation events (call-response, fills, etc.).
    """

    voice_focus: list[VoiceFocusSpec] = Field(default_factory=list)
    events: list[ConversationEventSpec] = Field(default_factory=list)

    @field_validator("voice_focus")
    @classmethod
    def unique_sections(cls, v: list[VoiceFocusSpec]) -> list[VoiceFocusSpec]:
        """Section IDs must be unique in voice_focus."""
        ids = [vf.section_id for vf in v]
        if len(ids) != len(set(ids)):
            dupes = [s for s in ids if ids.count(s) > 1]
            raise SpecValidationError(
                f"Duplicate section IDs in voice_focus: {set(dupes)}",
                field="conversation.voice_focus",
            )
        return v

    def primary_for_section(self, section_id: str) -> str | None:
        """Get primary voice for a section."""
        for vf in self.voice_focus:
            if vf.section_id == section_id:
                return vf.primary
        return None

    def fill_capable_for_section(self, section_id: str) -> list[str]:
        """Get fill-capable instruments for a section."""
        for vf in self.voice_focus:
            if vf.section_id == section_id:
                return vf.fill_capable
        return []

    @classmethod
    def from_yaml(cls, path: Path) -> ConversationSpec:
        """Load ConversationSpec from a YAML file.

        Args:
            path: Path to conversation.yaml.

        Returns:
            Validated ConversationSpec.

        Raises:
            SpecValidationError: If file is invalid.
        """
        if not path.exists():
            raise SpecValidationError(
                f"conversation.yaml not found: {path}",
                field="conversation",
            )
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SpecValidationError(
                f"Invalid YAML in conversation.yaml: {e}",
                field="conversation",
            ) from e
        if data is None:
            return cls(voice_focus=[], events=[])
        if not isinstance(data, dict):
            raise SpecValidationError(
                "conversation.yaml root must be a mapping",
                field="conversation",
            )
        return cls.model_validate(data)
