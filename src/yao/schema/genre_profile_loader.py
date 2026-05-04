"""Unified GenreProfile loader with adapter layer.

Loads genre profiles from multiple sources and converts them to the
unified ``UnifiedGenreProfile`` schema. Supports inheritance via
the ``parent`` field with recursive resolution and deep merge.

Resolution order:
1. Unified profiles (genre_profiles_v2/*.yaml) — future
2. System 1 (genre_profiles/*.yaml) via adapter
3. System 2 (src/yao/skills/genres/*.yaml) via adapter
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import structlog
import yaml

from yao.schema.genre_profile import (
    GenreDrumsSection,
    GenreGrooveSection,
    GenreHarmonySection,
    GenreIdentitySection,
    GenreInstrumentationSection,
    GenreMelodySection,
    GenreTempoSection,
    UnifiedGenreProfile,
)

logger = structlog.get_logger()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_GENRE_PROFILES_DIR = _PROJECT_ROOT / "genre_profiles"
_SKILLS_GENRES_DIR = _PROJECT_ROOT / "src" / "yao" / "skills" / "genres"

_cache: dict[str, UnifiedGenreProfile] = {}


def load_unified_genre_profile(genre_id: str) -> UnifiedGenreProfile | None:
    """Load a unified genre profile by ID.

    Checks cache first, then attempts to load from available sources.
    Resolves ``parent`` inheritance recursively.

    Args:
        genre_id: Canonical genre identifier (e.g. "lofi_hiphop").

    Returns:
        UnifiedGenreProfile or None if not found.
    """
    if genre_id in _cache:
        return _cache[genre_id]

    profile = _try_load_system1(genre_id)
    if profile is None:
        profile = _try_load_system2(genre_id)
    if profile is None:
        return None

    # Resolve inheritance
    if profile.parent is not None:
        parent = load_unified_genre_profile(profile.parent)
        if parent is not None:
            profile = _merge_profiles(parent, profile)

    _cache[genre_id] = profile
    return profile


def all_unified_profiles() -> dict[str, UnifiedGenreProfile]:
    """Load and return all available unified genre profiles.

    Returns:
        Dict mapping genre_id to UnifiedGenreProfile.
    """
    profiles: dict[str, UnifiedGenreProfile] = {}

    # System 1
    if _GENRE_PROFILES_DIR.exists():
        for yaml_path in sorted(_GENRE_PROFILES_DIR.glob("*.yaml")):
            name = yaml_path.stem
            p = load_unified_genre_profile(name)
            if p is not None:
                profiles[name] = p

    # System 2 (add any not already loaded)
    if _SKILLS_GENRES_DIR.exists():
        for yaml_path in sorted(_SKILLS_GENRES_DIR.glob("*.yaml")):
            name = yaml_path.stem
            if name not in profiles:
                p = load_unified_genre_profile(name)
                if p is not None:
                    profiles[name] = p

    return profiles


def reload_unified_profiles() -> None:
    """Clear the profile cache (for testing)."""
    _cache.clear()


def _try_load_system1(genre_id: str) -> UnifiedGenreProfile | None:
    """Adapt a System 1 genre_profiles/*.yaml to UnifiedGenreProfile."""
    yaml_path = _GENRE_PROFILES_DIR / f"{genre_id}.yaml"
    if not yaml_path.exists():
        return None

    try:
        data = yaml.safe_load(yaml_path.read_text())
    except Exception:
        logger.warning("genre_profile_load_error", path=str(yaml_path))
        return None

    if not isinstance(data, dict):
        return None

    return _adapt_system1(data)


def _adapt_system1(data: dict[str, Any]) -> UnifiedGenreProfile:
    """Convert System 1 YAML dict to UnifiedGenreProfile."""
    name = data.get("name", "")
    tempo_range = data.get("tempo_range")

    return UnifiedGenreProfile(
        genre_id=name,
        identity=GenreIdentitySection(name=name),
        tempo=GenreTempoSection(
            range=tuple(tempo_range) if tempo_range else None,
            central=sum(tempo_range) / 2 if tempo_range else None,
        ),
        harmony=GenreHarmonySection(
            chord_palette=data.get("chord_palette", []),
            progression_n_grams=data.get("progression_n_grams", {}),
            seventh_chord_probability=data.get("seventh_chord_probability", 0.3),
            secondary_dominant_probability=data.get("secondary_dominant_probability", 0.1),
            modal_interchange_probability=data.get("modal_interchange_probability", 0.1),
        ),
        melody=GenreMelodySection(
            melodic_contour_weights=data.get("melodic_contour_weights", {}),
            leap_probability=data.get("leap_probability", 0.3),
            blue_note_probability=data.get("blue_note_probability", 0.0),
        ),
        drums=_extract_drums_system1(data),
        instrumentation=GenreInstrumentationSection(
            preferred=data.get("preferred_instruments", []),
        ),
        voicing_density_target=data.get("voicing_density_target", 4),
        bass_motion_style=data.get("bass_motion_style", "root_fifth"),
        typical_dynamics_range=data.get("typical_dynamics_range", ("mp", "f")),
        target_spectral_centroid=data.get("target_spectral_centroid", 0.5),
    )


def _extract_drums_system1(data: dict[str, Any]) -> Any:
    """Extract drums section from System 1 data."""
    from yao.schema.genre_profile import GenreDrumsSection

    return GenreDrumsSection(
        swing_ratio=data.get("swing_ratio", 0.5),
        syncopation_density=data.get("syncopation_density", 0.3),
        rhythm_template_weights=data.get("rhythm_template_weights", {}),
    )


def _try_load_system2(genre_id: str) -> UnifiedGenreProfile | None:
    """Adapt a System 2 skills/genres/*.yaml to UnifiedGenreProfile."""
    yaml_path = _SKILLS_GENRES_DIR / f"{genre_id}.yaml"
    if not yaml_path.exists():
        return None

    try:
        data = yaml.safe_load(yaml_path.read_text())
    except Exception:
        logger.warning("skill_genre_load_error", path=str(yaml_path))
        return None

    if not isinstance(data, dict):
        return None

    return _adapt_system2(data)


def _adapt_system2(data: dict[str, Any]) -> UnifiedGenreProfile:
    """Convert System 2 skill YAML dict to UnifiedGenreProfile."""
    genre_id = data.get("genre", data.get("genre_id", ""))
    tempo_range = data.get("tempo_range")

    return UnifiedGenreProfile(
        genre_id=genre_id,
        cultural_context=data.get("cultural_context"),
        identity=GenreIdentitySection(name=genre_id),
        tempo=GenreTempoSection(
            range=tuple(tempo_range) if tempo_range else None,
            central=sum(tempo_range) / 2 if tempo_range else None,
        ),
        groove=GenreGrooveSection(
            default=data.get("typical_drum_pattern"),
            swing_value=data.get("default_swing"),
        ),
        harmony=GenreHarmonySection(
            chord_progressions=data.get("chord_progressions", []),
        ),
        drums=GenreDrumsSection(
            default_pattern=data.get("typical_drum_pattern"),
            characteristic_rhythms=data.get("characteristic_rhythms", []),
        ),
        instrumentation=GenreInstrumentationSection(
            preferred=data.get("preferred_instruments", []),
            avoided=data.get("avoided_instruments", []),
            typical_keys=data.get("typical_keys", []),
            modal_options=data.get("modal_options", []),
        ),
    )


def _merge_profiles(
    parent: UnifiedGenreProfile,
    child: UnifiedGenreProfile,
) -> UnifiedGenreProfile:
    """Deep-merge parent profile into child (child overrides parent).

    Args:
        parent: Base profile to inherit from.
        child: Child profile that overrides parent values.

    Returns:
        Merged UnifiedGenreProfile.
    """
    parent_dict = parent.model_dump()
    child_dict = child.model_dump()
    merged = _deep_merge(parent_dict, child_dict)
    # Preserve child's genre_id and parent reference
    merged["genre_id"] = child.genre_id
    merged["parent"] = child.parent
    return UnifiedGenreProfile.model_validate(merged)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay dict into base dict.

    Overlay values take precedence. None values in overlay are skipped.
    """
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        elif _is_non_default(value):
            result[key] = copy.deepcopy(value)
    return result


def _is_non_default(value: object) -> bool:
    """Check if a value is non-default (non-empty, non-zero for collections)."""
    if isinstance(value, list | tuple) and len(value) == 0:
        return False
    if isinstance(value, dict) and len(value) == 0:
        return False
    return bool(value != "")
