"""Genre resolver — resolves genre spec into generation context.

Runs at the top of the generation pipeline. Takes a genre name from the
composition spec and resolves it into a complete set of generation defaults:
tempo, instruments, drum pattern, groove, and melodic biases.

This is the single point of genre resolution — downstream generators
should not perform their own genre lookups.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.constants.genre_profile import GenreProfile, get_genre_profile
from yao.generators.genre_adapter import GenreBias, resolve_genre_bias
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec, DrumsSpec, InstrumentSpec


@dataclass(frozen=True)
class ResolvedGenreContext:
    """Complete generation context resolved from a genre profile.

    Attributes:
        genre_name: The resolved genre name.
        profile: The underlying GenreProfile, or None if unresolved.
        bias: Generation biases derived from the profile.
        default_drums: DrumsSpec to use when spec.drums is None, or None.
        suggested_tempo: Midpoint of genre tempo range, or None.
        preferred_instruments: Instruments typical of this genre.
        is_default: True if no genre profile was found (using defaults).
    """

    genre_name: str
    profile: GenreProfile | None
    bias: GenreBias | None
    default_drums: DrumsSpec | None
    suggested_tempo: float | None
    preferred_instruments: tuple[str, ...]
    is_default: bool


def resolve_genre(
    genre_name: str,
    provenance: ProvenanceLog,
) -> ResolvedGenreContext:
    """Resolve a genre name into a complete generation context.

    Args:
        genre_name: Genre identifier from the composition spec.
        provenance: Provenance log for recording the resolution.

    Returns:
        ResolvedGenreContext with all resolved defaults.
    """
    profile = get_genre_profile(genre_name)

    if profile is None:
        provenance.record(
            layer="generator",
            operation="genre_resolved",
            parameters={"genre": genre_name, "resolved": False},
            source="genre_resolver.resolve_genre",
            rationale=f"No profile found for genre '{genre_name}'; using defaults.",
        )
        return ResolvedGenreContext(
            genre_name=genre_name,
            profile=None,
            bias=None,
            default_drums=None,
            suggested_tempo=None,
            preferred_instruments=(),
            is_default=True,
        )

    bias = resolve_genre_bias(profile)

    # Build drums spec from profile if it requires drums
    default_drums: DrumsSpec | None = None
    if profile.requires_drums and profile.default_drum_pattern is not None:
        default_drums = DrumsSpec(
            pattern_family=profile.default_drum_pattern,
            swing=max(0.0, (profile.swing_ratio - 0.5) * 2.0),
            humanize_ms=5.0,
            ghost_notes_density=0.0,
        )

    # Suggested tempo is midpoint of genre range
    suggested_tempo = (profile.tempo_range[0] + profile.tempo_range[1]) / 2.0

    provenance.record(
        layer="generator",
        operation="genre_resolved",
        parameters={
            "genre": genre_name,
            "resolved": True,
            "tempo_range": list(profile.tempo_range),
            "suggested_tempo": suggested_tempo,
            "requires_drums": profile.requires_drums,
            "default_drum_pattern": profile.default_drum_pattern,
            "preferred_instruments": list(profile.preferred_instruments),
            "leap_probability": profile.leap_probability,
            "syncopation_density": profile.syncopation_density,
            "swing_ratio": profile.swing_ratio,
        },
        source="genre_resolver.resolve_genre",
        rationale=(
            f"Genre '{genre_name}' resolved: tempo {profile.tempo_range}, "
            f"drums={'yes' if profile.requires_drums else 'no'}, "
            f"{len(profile.preferred_instruments)} instruments."
        ),
    )

    return ResolvedGenreContext(
        genre_name=genre_name,
        profile=profile,
        bias=bias,
        default_drums=default_drums,
        suggested_tempo=suggested_tempo,
        preferred_instruments=profile.preferred_instruments,
        is_default=False,
    )


def inject_theme_recall(
    spec: CompositionSpec,
    provenance: ProvenanceLog,
) -> CompositionSpec:
    """Auto-inject recall_melody_from on the last section if none is set.

    For compositions with 3+ sections, the last section recalls the first
    section's melody (A→...→A′ form). This ensures thematic coherence
    without requiring manual spec configuration.

    Only injects when no section already has recall_melody_from set.

    Args:
        spec: The composition spec.
        provenance: Provenance log for recording the injection.

    Returns:
        Updated spec with recall_melody_from set on the last section,
        or the original spec if recall is already configured.
    """
    if len(spec.sections) < 3:
        return spec

    # If any section already has recall, don't interfere
    if any(s.recall_melody_from is not None for s in spec.sections):
        return spec

    first_section = spec.sections[0]
    last_section = spec.sections[-1]

    # Don't recall if first and last are the same section
    if first_section.name == last_section.name:
        return spec

    # Build updated last section with recall using model_copy
    updated_last = last_section.model_copy(update={"recall_melody_from": first_section.name})

    updated_sections = list(spec.sections[:-1]) + [updated_last]

    provenance.record(
        layer="generator",
        operation="theme_recall_injected",
        parameters={
            "source_section": first_section.name,
            "target_section": last_section.name,
        },
        source="genre_resolver.inject_theme_recall",
        rationale=(
            f"Auto-injected theme recall: last section '{last_section.name}' "
            f"recalls melody from '{first_section.name}' for thematic coherence."
        ),
    )

    return spec.model_copy(update={"sections": updated_sections})


# Default instrument set — when spec only has these, it's considered generic
_DEFAULT_INSTRUMENTS = frozenset({"piano"})

# Role assignment rules for genre instruments
_BASS_KEYWORDS = frozenset({"bass", "bass_guitar", "upright_bass", "synth_bass", "electric_bass"})


def enrich_instruments_from_genre(
    spec: CompositionSpec,
    genre_ctx: ResolvedGenreContext,
    provenance: ProvenanceLog,
) -> CompositionSpec:
    """Auto-populate instruments from genre profile when spec has only defaults.

    Only activates when the spec's instrument set is a single generic
    instrument (e.g., just "piano") and the genre profile provides
    preferred_instruments. Preserves existing instruments if they appear
    intentional (multiple instruments or non-default names).

    Args:
        spec: The composition spec.
        genre_ctx: Resolved genre context.
        provenance: Provenance log.

    Returns:
        Updated spec with genre-appropriate instruments, or unchanged.
    """
    if genre_ctx.is_default or not genre_ctx.preferred_instruments:
        return spec

    # Only replace if the user specified a single default instrument
    current_names = {i.name for i in spec.instruments}
    if len(spec.instruments) > 1 or not current_names.issubset(_DEFAULT_INSTRUMENTS):
        return spec

    from typing import Literal

    instruments: list[InstrumentSpec] = []
    for i, name in enumerate(genre_ctx.preferred_instruments[:5]):
        role: Literal["melody", "harmony", "bass", "rhythm", "pad", "counter_melody", "vocal_lead"]
        if i == 0:
            role = "melody"
        elif name.lower() in _BASS_KEYWORDS:
            role = "bass"
        elif i == len(genre_ctx.preferred_instruments[:5]) - 1:
            role = "pad"
        else:
            role = "harmony"
        instruments.append(InstrumentSpec(name=name, role=role))

    provenance.record(
        layer="generator",
        operation="instruments_auto_populated",
        parameters={
            "genre": genre_ctx.genre_name,
            "original": [i.name for i in spec.instruments],
            "enriched": [i.name for i in instruments],
        },
        source="genre_resolver.enrich_instruments_from_genre",
        rationale=(
            f"Spec had only default instruments ({current_names}); "
            f"replaced with {len(instruments)} genre-typical instruments."
        ),
    )

    return spec.model_copy(update={"instruments": instruments})
