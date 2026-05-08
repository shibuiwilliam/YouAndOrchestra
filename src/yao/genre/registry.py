"""GenreRegistry — singleton registry for genre profile lookup.

Loads genre profiles from ``src/yao/genre/profiles/*.yaml`` at first access,
validates them against the GenreProfile Pydantic schema, resolves inheritance,
and caches results.

Also integrates with the two pre-existing genre systems (System 1 in
``genre_profiles/`` and System 2 in ``src/yao/skills/genres/``) for
backward compatibility.

Belongs to Layer 0/1 boundary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from yao.errors import YaOError
from yao.genre.inheritance import resolve_inheritance
from yao.genre.profile import GenreProfile

logger = structlog.get_logger()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Primary location for v2.0 genre profiles
_V2_PROFILES_DIR = Path(__file__).resolve().parent / "profiles"

# Legacy locations (System 1 and System 2)
_SYSTEM1_DIR = _PROJECT_ROOT / "genre_profiles"
_SYSTEM2_DIR = _PROJECT_ROOT / "src" / "yao" / "skills" / "genres"


class GenreNotFoundError(YaOError):
    """Raised when a requested genre is not in the registry."""

    def __init__(self, genre_name: str) -> None:
        self.genre_name = genre_name
        available = ", ".join(sorted(GenreRegistry.available())) if GenreRegistry._cache else "(not loaded)"
        super().__init__(f"Genre '{genre_name}' not found in registry. Available genres: {available}")


class GenreRegistry:
    """Singleton registry for genre profile lookup and management.

    Usage::

        profile = GenreRegistry.get("jazz")
        all_profiles = GenreRegistry.all()
        GenreRegistry.register(custom_profile)

    The registry loads profiles lazily on first access from three
    sources in priority order:
        1. ``src/yao/genre/profiles/*.yaml`` (v2.0 canonical)
        2. ``genre_profiles/*.yaml`` (System 1 legacy)
        3. ``src/yao/skills/genres/*.yaml`` (System 2 legacy)
    """

    _cache: dict[str, GenreProfile] = {}
    _loaded: bool = False

    @classmethod
    def get(cls, name: str) -> GenreProfile:
        """Look up a genre profile by name.

        Args:
            name: Genre identifier (e.g., "jazz", "lofi_hip_hop").

        Returns:
            Resolved GenreProfile (with inheritance applied).

        Raises:
            GenreNotFoundError: If the genre is not registered.
        """
        cls._ensure_loaded()
        if name not in cls._cache:
            raise GenreNotFoundError(name)
        return cls._cache[name]

    @classmethod
    def get_or_none(cls, name: str) -> GenreProfile | None:
        """Look up a genre profile, returning None if not found.

        Args:
            name: Genre identifier.

        Returns:
            GenreProfile or None.
        """
        cls._ensure_loaded()
        return cls._cache.get(name)

    @classmethod
    def all(cls) -> dict[str, GenreProfile]:
        """Return all registered genre profiles.

        Returns:
            Dict mapping genre name to GenreProfile.
        """
        cls._ensure_loaded()
        return dict(cls._cache)

    @classmethod
    def available(cls) -> list[str]:
        """Return sorted list of all registered genre names.

        Returns:
            Sorted list of genre identifiers.
        """
        cls._ensure_loaded()
        return sorted(cls._cache.keys())

    @classmethod
    def register(cls, profile: GenreProfile) -> None:
        """Register a genre profile (or replace an existing one).

        If the profile has a ``parent`` and the parent is already
        registered, inheritance is resolved automatically.

        Args:
            profile: GenreProfile to register.
        """
        cls._ensure_loaded()
        if profile.parent and profile.parent in cls._cache:
            parent = cls._cache[profile.parent]
            profile = resolve_inheritance(profile, parent)
        cls._cache[profile.name] = profile
        logger.debug("genre_registered", name=profile.name, parent=profile.parent)

    @classmethod
    def reload(cls) -> None:
        """Clear the cache and reload all profiles from disk."""
        cls._cache.clear()
        cls._loaded = False
        cls._ensure_loaded()

    @classmethod
    def _ensure_loaded(cls) -> None:
        """Load profiles from all sources on first access."""
        if cls._loaded:
            return
        cls._loaded = True
        cls._load_from_directory(_V2_PROFILES_DIR)
        cls._load_from_directory(_SYSTEM1_DIR)
        cls._load_system2_profiles()
        cls._resolve_all_inheritance()

    @classmethod
    def _load_from_directory(cls, directory: Path) -> None:
        """Load YAML profiles from a directory."""
        if not directory.exists():
            return
        for yaml_path in sorted(directory.glob("*.yaml")):
            try:
                data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("genre_profile_load_error", path=str(yaml_path))
                continue
            if not isinstance(data, dict) or "name" not in data:
                continue
            name = data["name"]
            if name in cls._cache:
                continue  # Don't overwrite higher-priority source
            try:
                profile = GenreProfile.from_yaml_data(data)
                cls._cache[name] = profile
            except Exception:
                logger.warning("genre_profile_parse_error", path=str(yaml_path), name=name)

    @classmethod
    def _load_system2_profiles(cls) -> None:
        """Load System 2 skill-based genre profiles."""
        if not _SYSTEM2_DIR.exists():
            return
        for yaml_path in sorted(_SYSTEM2_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("skill_genre_load_error", path=str(yaml_path))
                continue
            if not isinstance(data, dict):
                continue
            # System 2 uses "genre" or "genre_id" instead of "name"
            name = data.get("genre", data.get("genre_id", data.get("name", "")))
            if not name or name in cls._cache:
                continue
            adapted = _adapt_system2_to_profile(data, name)
            if adapted is not None:
                cls._cache[name] = adapted

    @classmethod
    def _resolve_all_inheritance(cls) -> None:
        """Resolve inheritance for all loaded profiles."""
        resolved: dict[str, GenreProfile] = {}
        for name, profile in cls._cache.items():
            resolved[name] = cls._resolve_chain(profile, set())
        cls._cache = resolved

    @classmethod
    def _resolve_chain(cls, profile: GenreProfile, visited: set[str]) -> GenreProfile:
        """Recursively resolve a profile's inheritance chain."""
        if profile.parent is None or profile.parent not in cls._cache:
            return profile
        if profile.name in visited:
            logger.warning("genre_circular_inheritance", name=profile.name)
            return profile
        visited.add(profile.name)
        parent = cls._resolve_chain(cls._cache[profile.parent], visited)
        return resolve_inheritance(profile, parent)


def _adapt_system2_to_profile(data: dict[str, Any], name: str) -> GenreProfile | None:
    """Adapt a System 2 skill YAML to a GenreProfile."""
    try:
        tempo_range = data.get("tempo_range")
        return GenreProfile(
            name=name,
            typical_tempo_range=tuple(tempo_range) if tempo_range and len(tempo_range) == 2 else (80.0, 140.0),  # noqa: PLR2004
            typical_keys=data.get("typical_keys", []),
            typical_modes=data.get("modal_options", []),
            chord_palette_extended=data.get("chord_palette", []),
            swing_8th=data.get("default_swing", 0.5) or 0.5,
            drum_pattern_ids=[data["typical_drum_pattern"]] if data.get("typical_drum_pattern") else [],
            melodic_devices=data.get("characteristic_rhythms", []),
            typical_scales=data.get("modal_options", []),
        )
    except Exception:
        logger.warning("system2_adapt_error", name=name)
        return None
