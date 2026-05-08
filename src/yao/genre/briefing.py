"""GenreBriefing — resolved genre constraint set for subagent distribution.

When a composition specifies a genre, the Genre Specialist produces a
GenreBriefing: a structured object that tells every downstream subagent
exactly how to constrain its output for genre authenticity.

The briefing supports:
    - Single genre (primary only)
    - Genre fusion (primary + weighted secondary genres)
    - User overrides (explicit field-level overrides)

Belongs to Layer 0/1 boundary.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from yao.genre.profile import GenreProfile
from yao.genre.registry import GenreRegistry


@dataclass(frozen=True)
class FusionComponent:
    """A genre and its weight in a fusion blend."""

    genre: str
    weight: float
    profile: GenreProfile


@dataclass(frozen=True)
class GenreBriefing:
    """Resolved genre constraint set distributed to all subagents.

    The briefing is the single source of truth for genre-aware generation.
    Every subagent receives the same briefing and records its ``id`` in
    provenance for traceability.

    Attributes:
        id: Unique identifier for provenance linking.
        primary_genre: Name of the primary genre.
        primary_profile: Resolved GenreProfile for the primary genre.
        fusion_components: Optional secondary genres with weights.
        resolved_profile: Final blended profile (or primary if no fusion).
        user_overrides: Explicit user field overrides applied on top.
        tempo_range: Final tempo range after overrides.
        core_instruments: Instruments that must be present.
        forbidden_instruments: Instruments that must not appear.
        swing_8th: Final swing ratio.
        chord_palette: Final chord palette.
        cliches_to_avoid: Anti-patterns to reject.
    """

    id: str
    primary_genre: str
    primary_profile: GenreProfile
    fusion_components: tuple[FusionComponent, ...] = ()
    resolved_profile: GenreProfile = field(init=False)
    user_overrides: dict[str, Any] = field(default_factory=dict)

    # Convenience fields derived from resolved_profile
    tempo_range: tuple[float, float] = field(init=False)
    core_instruments: tuple[str, ...] = field(init=False)
    forbidden_instruments: tuple[str, ...] = field(init=False)
    swing_8th: float = field(init=False)
    chord_palette: tuple[str, ...] = field(init=False)
    cliches_to_avoid: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        """Resolve the final profile from primary + fusion + overrides."""
        if self.fusion_components:
            blended = _blend_profiles(self.primary_profile, self.fusion_components)
        else:
            blended = self.primary_profile

        if self.user_overrides:
            override_data = blended.model_dump()
            override_data.update(self.user_overrides)
            blended = GenreProfile.model_validate(override_data)

        # Use object.__setattr__ since this is a frozen dataclass
        object.__setattr__(self, "resolved_profile", blended)
        object.__setattr__(self, "tempo_range", blended.typical_tempo_range)
        object.__setattr__(
            self,
            "core_instruments",
            tuple(i.name for i in blended.core_instruments),
        )
        object.__setattr__(
            self,
            "forbidden_instruments",
            tuple(blended.forbidden_instruments),
        )
        object.__setattr__(self, "swing_8th", blended.swing_8th)
        object.__setattr__(
            self,
            "chord_palette",
            tuple(blended.chord_palette_extended),
        )
        object.__setattr__(
            self,
            "cliches_to_avoid",
            tuple(blended.cliches_to_avoid),
        )


def synthesize_briefing(
    primary_genre: str,
    fusion: list[tuple[str, float]] | None = None,
    overrides: dict[str, Any] | None = None,
) -> GenreBriefing:
    """Synthesize a GenreBriefing from a genre name and optional fusion spec.

    This is the main entry point for creating genre briefings. It:
    1. Resolves the primary genre through the GenreRegistry.
    2. Resolves any fusion genres and their weights.
    3. Applies user overrides.
    4. Returns a fully resolved briefing.

    Args:
        primary_genre: Name of the primary genre (must be in registry).
        fusion: Optional list of (genre_name, weight) pairs for fusion.
        overrides: Optional dict of field-level overrides.

    Returns:
        Fully resolved GenreBriefing.

    Raises:
        GenreNotFoundError: If primary or any fusion genre is not registered.
    """
    primary_profile = GenreRegistry.get(primary_genre)

    fusion_components: list[FusionComponent] = []
    if fusion:
        for genre_name, weight in fusion:
            profile = GenreRegistry.get(genre_name)
            fusion_components.append(FusionComponent(genre=genre_name, weight=weight, profile=profile))

    return GenreBriefing(
        id=f"briefing_{uuid.uuid4().hex[:12]}",
        primary_genre=primary_genre,
        primary_profile=primary_profile,
        fusion_components=tuple(fusion_components),
        user_overrides=overrides or {},
    )


def _blend_profiles(
    primary: GenreProfile,
    components: tuple[FusionComponent, ...],
) -> GenreProfile:
    """Blend a primary profile with fusion components.

    Numeric fields are interpolated linearly by weight.
    List fields are merged with deduplication.
    The primary genre's weight is ``1 - sum(component weights)``.

    Args:
        primary: Primary genre profile.
        components: Fusion components with their weights.

    Returns:
        Blended GenreProfile.
    """
    total_secondary_weight = sum(c.weight for c in components)
    primary_weight = max(0.0, 1.0 - total_secondary_weight)

    # Start with primary dict
    blended = primary.model_dump()

    # Numeric fields to interpolate
    numeric_fields = [
        "swing_8th",
        "swing_16th",
        "chromaticism_level",
        "syncopation_density",
        "leap_probability",
        "blue_note_probability",
        "seventh_chord_probability",
        "secondary_dominant_probability",
        "modal_interchange_probability",
        "call_response_density",
        "polyrhythm_tolerance",
        "target_lufs",
        "target_peak_db",
        "target_spectral_centroid",
    ]

    for field_name in numeric_fields:
        val = getattr(primary, field_name, 0.0) * primary_weight
        for comp in components:
            val += getattr(comp.profile, field_name, 0.0) * comp.weight
        blended[field_name] = val

    # Tuple-of-float fields (interpolate element-wise)
    range_fields = ["typical_tempo_range", "harmonic_rhythm", "phrase_length_beats"]
    for field_name in range_fields:
        primary_val = getattr(primary, field_name)
        blended_val = [v * primary_weight for v in primary_val]
        for comp in components:
            comp_val = getattr(comp.profile, field_name)
            for i in range(len(blended_val)):
                blended_val[i] += comp_val[i] * comp.weight
        blended[field_name] = tuple(blended_val)

    # List fields: merge and deduplicate
    list_fields = [
        "typical_keys",
        "typical_modes",
        "typical_scales",
        "chord_palette_extended",
        "melodic_devices",
        "typical_effects",
        "typical_grooves",
        "cliches_to_avoid",
    ]
    for field_name in list_fields:
        merged: list[str] = list(getattr(primary, field_name, []))
        seen = set(merged)
        for comp in components:
            for item in getattr(comp.profile, field_name, []):
                if item not in seen:
                    merged.append(item)
                    seen.add(item)
        blended[field_name] = merged

    # Keep primary's name for identification
    blended["name"] = primary.name

    return GenreProfile.model_validate(blended)
