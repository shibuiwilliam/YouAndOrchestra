"""Skill Loader — loads and queries genre profiles from YAML skill files.

Provides SkillRegistry (singleton-friendly) that loads all genre profiles
from src/yao/skills/genres/*.yaml and exposes lookup by genre_id.

These YAML files are synced from .claude/skills/genres/*.md frontmatter
by tools/skill_yaml_sync.py (make sync-skills).

Belongs to Layer 1 (Specification) — provides input to generators, critics, and compilers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_SKILLS_DIR = Path(__file__).resolve().parent / "genres"


@dataclass(frozen=True)
class GenreProfile:
    """A genre's musical profile loaded from a skill YAML file.

    Fields map directly to the YAML frontmatter of genre skill .md files.

    Attributes:
        genre_id: Canonical genre identifier (e.g., "cinematic", "jazz_swing").
        tempo_range: (min_bpm, max_bpm) typical tempo range.
        typical_keys: Key signatures commonly used (e.g., ["Dm", "Cm"]).
        modal_options: Scale/mode options (e.g., ["minor", "dorian"]).
        default_swing: Default swing amount [0.0, 1.0].
        drum_pattern_family: Drum pattern YAML to use (e.g., "jazz_swing_ride").
        preferred_instruments: Instruments commonly used.
        avoided_instruments: Instruments to avoid.
        chord_progressions: Typical chord progressions as lists of roman numerals.
        characteristic_rhythms: Rhythm patterns typical of this genre.
        cultural_context: Cultural notes (required for non-Western genres).
        raw: Original YAML dict for extension fields.
    """

    genre_id: str
    tempo_range: tuple[float, float]
    typical_keys: tuple[str, ...]
    modal_options: tuple[str, ...]
    default_swing: float
    drum_pattern_family: str | None
    preferred_instruments: tuple[str, ...]
    avoided_instruments: tuple[str, ...]
    chord_progressions: tuple[tuple[str, ...], ...]
    characteristic_rhythms: tuple[str, ...]
    cultural_context: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_yaml(cls, data: dict[str, Any]) -> GenreProfile:
        """Construct a GenreProfile from a parsed YAML dict.

        Args:
            data: Parsed YAML data from a genre skill file.

        Returns:
            GenreProfile instance.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If field values are invalid.
        """
        genre_id = data["genre"]
        tempo_range_raw = data.get("tempo_range", [80, 140])
        if len(tempo_range_raw) != 2:  # noqa: PLR2004
            msg = f"tempo_range must have 2 elements, got {len(tempo_range_raw)}"
            raise ValueError(msg)

        # Parse chord progressions (list of lists of roman numerals)
        raw_progs = data.get("typical_chord_progressions", [])
        chord_progressions = tuple(tuple(str(c) for c in prog) for prog in raw_progs)

        return cls(
            genre_id=genre_id,
            tempo_range=(float(tempo_range_raw[0]), float(tempo_range_raw[1])),
            typical_keys=tuple(data.get("typical_keys", [])),
            modal_options=tuple(data.get("modal_options", ["major"])),
            default_swing=float(data.get("default_swing", 0.0)),
            drum_pattern_family=data.get("typical_drum_pattern"),
            preferred_instruments=tuple(data.get("preferred_instruments", [])),
            avoided_instruments=tuple(data.get("avoided_instruments", [])),
            chord_progressions=chord_progressions,
            characteristic_rhythms=tuple(data.get("characteristic_rhythms", [])),
            cultural_context=data.get("cultural_context"),
            raw=data,
        )


class SkillRegistry:
    """Registry of all genre profiles.

    Loads all YAML files from the genres directory at construction time.
    Provides lookup by genre_id and listing of all available genres.

    Usage:
        registry = SkillRegistry()
        profile = registry.get_genre("cinematic")
        if profile:
            print(profile.typical_keys)
    """

    def __init__(self, skills_dir: Path | None = None) -> None:
        self._genres: dict[str, GenreProfile] = {}
        self._dir = skills_dir or _SKILLS_DIR
        self._load_all()

    def _load_all(self) -> None:
        """Load all genre YAML files from the skills directory."""
        if not self._dir.exists():
            return

        for yaml_path in sorted(self._dir.glob("*.yaml")):
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "genre" in data:
                    profile = GenreProfile.from_yaml(data)
                    self._genres[profile.genre_id] = profile
            except (yaml.YAMLError, KeyError, ValueError) as e:
                import structlog

                structlog.get_logger().warning(
                    "skill_load_error",
                    path=str(yaml_path),
                    error=str(e),
                )

    def get_genre(self, genre_id: str) -> GenreProfile | None:
        """Look up a genre profile by ID.

        Args:
            genre_id: The genre identifier (e.g., "cinematic").

        Returns:
            GenreProfile if found, None otherwise.
        """
        return self._genres.get(genre_id)

    def list_genres(self) -> list[str]:
        """Return sorted list of all loaded genre IDs."""
        return sorted(self._genres.keys())

    def genre_count(self) -> int:
        """Return number of loaded genres."""
        return len(self._genres)

    def reload(self) -> None:
        """Reload all genre profiles from disk (for development hot-reload)."""
        self._genres.clear()
        self._load_all()

    def tempo_range_for(self, genre_id: str) -> tuple[float, float] | None:
        """Get tempo range for a genre. Convenience method.

        Args:
            genre_id: Genre identifier.

        Returns:
            (min_bpm, max_bpm) or None if genre not found.
        """
        profile = self.get_genre(genre_id)
        return profile.tempo_range if profile else None

    def chord_palette_for(self, genre_id: str) -> list[str] | None:
        """Get flattened chord palette for a genre.

        Extracts unique chord symbols from all typical_chord_progressions.

        Args:
            genre_id: Genre identifier.

        Returns:
            List of unique chord symbols, or None if genre not found or no progressions.
        """
        profile = self.get_genre(genre_id)
        if not profile or not profile.chord_progressions:
            return None

        seen: set[str] = set()
        palette: list[str] = []
        for prog in profile.chord_progressions:
            for chord in prog:
                if chord not in seen:
                    palette.append(chord)
                    seen.add(chord)
        return palette


# Module-level singleton (lazy, thread-safe enough for YaO's use)
_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get the global SkillRegistry singleton.

    Returns:
        The shared SkillRegistry instance.
    """
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
