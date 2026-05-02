"""User Style Profile — cross-project pattern mining from annotations.

Aggregates listening annotations to build a user preference profile.
Profile influence on generation is opt-in via spec ``style_profile.use: true``.

Belongs to Layer 7 (Reflection).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StylePreference:
    """A single learned preference.

    Attributes:
        dimension: What aspect (e.g., "tempo", "density", "harmony_complexity").
        preferred_range: Preferred value range [low, high].
        confidence: How confident the preference is (0.0-1.0).
        source_count: Number of annotations contributing to this preference.
    """

    dimension: str
    preferred_range: tuple[float, float]
    confidence: float
    source_count: int


@dataclass
class UserStyleProfile:
    """Aggregated user preference profile.

    Built from annotations across projects. Updated explicitly
    via ``yao reflect ingest <annotations>`` — never automatically.

    Attributes:
        user_id: User identifier (default: "local").
        preferences: Learned preferences.
        total_annotations: Total annotations ingested.
    """

    user_id: str = "local"
    preferences: list[StylePreference] = field(default_factory=list)
    total_annotations: int = 0

    def add_preference(self, pref: StylePreference) -> None:
        """Add or update a preference dimension.

        Args:
            pref: The preference to add.
        """
        # Replace existing preference for same dimension
        self.preferences = [p for p in self.preferences if p.dimension != pref.dimension]
        self.preferences.append(pref)

    def get_preference(self, dimension: str) -> StylePreference | None:
        """Look up a preference by dimension.

        Args:
            dimension: The dimension name.

        Returns:
            StylePreference or None.
        """
        for p in self.preferences:
            if p.dimension == dimension:
                return p
        return None

    def save(self, path: Path) -> None:
        """Save profile to JSON.

        Args:
            path: Output path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "user_id": self.user_id,
            "total_annotations": self.total_annotations,
            "preferences": [
                {
                    "dimension": p.dimension,
                    "preferred_range": list(p.preferred_range),
                    "confidence": p.confidence,
                    "source_count": p.source_count,
                }
                for p in self.preferences
            ],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> UserStyleProfile:
        """Load profile from JSON.

        Args:
            path: Path to profile JSON.

        Returns:
            Loaded profile, or empty profile if file doesn't exist.
        """
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        prefs = [
            StylePreference(
                dimension=p["dimension"],
                preferred_range=tuple(p["preferred_range"]),
                confidence=p["confidence"],
                source_count=p["source_count"],
            )
            for p in data.get("preferences", [])
        ]
        return cls(
            user_id=data.get("user_id", "local"),
            preferences=prefs,
            total_annotations=data.get("total_annotations", 0),
        )
