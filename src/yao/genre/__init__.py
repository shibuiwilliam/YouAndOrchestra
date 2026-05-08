"""Genre System — first-class genre support for YaO (v2.0).

This package is the canonical home for all genre-related data structures,
the genre registry, profile inheritance, and the genre briefing system.

Belongs to Layer 0/1 boundary.

Public API:
    GenreProfile        — Pydantic model capturing a genre's musical fingerprint.
    GenreRegistry       — Singleton registry for loading and querying profiles.
    GenreBriefing       — Resolved constraint set distributed to subagents.
    resolve_inheritance — Additive override resolver for parent-child profiles.
"""

from yao.genre.briefing import GenreBriefing
from yao.genre.profile import GenreProfile
from yao.genre.registry import GenreRegistry

__all__ = [
    "GenreBriefing",
    "GenreProfile",
    "GenreRegistry",
]
