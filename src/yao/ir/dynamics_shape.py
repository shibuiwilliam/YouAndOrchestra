"""DynamicsShape — phrase-level velocity shaping within sections.

Instead of a flat per-section velocity, DynamicsShape defines a curve
that modulates velocity across the phrase. Applied AFTER GrooveProfile
but BEFORE humanize jitter (CLAUDE.md §11.1).

Supported shapes:
- crescendo: linear rise from start to end
- decrescendo: linear fall from start to end
- arch: rise to peak_position, then fall
- hairpin: swell to peak then return (symmetric arch)
- steady: no modulation (multiplier = 1.0 everywhere)

Belongs to Layer 3 (ScoreIR) — it modifies note velocities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DynamicsShapeType(StrEnum):
    """Available phrase-level dynamics shapes."""

    CRESCENDO = "crescendo"
    DECRESCENDO = "decrescendo"
    ARCH = "arch"
    HAIRPIN = "hairpin"
    STEADY = "steady"


@dataclass(frozen=True)
class BarAccent:
    """An accent at a specific position within a section.

    Attributes:
        bar: Bar number within the section (0-indexed).
        beat: Beat within the bar (0-indexed).
        strength: Velocity multiplier for the accent (1.0–1.5 typical).
    """

    bar: int
    beat: float = 0.0
    strength: float = 1.2

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"bar": self.bar, "beat": self.beat, "strength": self.strength}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BarAccent:
        """Deserialize from dict."""
        return cls(
            bar=data["bar"],
            beat=data.get("beat", 0.0),
            strength=data.get("strength", 1.2),
        )


@dataclass(frozen=True)
class DynamicsShape:
    """Phrase-level dynamics shape for a section.

    Attributes:
        shape: Type of dynamics curve.
        peak_position: Position of peak for arch/hairpin [0, 1].
            Required for arch/hairpin, ignored for others.
        intensity: How strong the shaping is [0, 1].
            0 = no effect, 1 = full range from pp to ff.
        accents: Specific beat positions with accent marks.
    """

    shape: DynamicsShapeType = DynamicsShapeType.STEADY
    peak_position: float = 0.5
    intensity: float = 0.7
    accents: tuple[BarAccent, ...] = ()

    def velocity_multiplier(self, position: float) -> float:
        """Compute the velocity multiplier at a given phrase position.

        Args:
            position: Normalized position within the phrase [0, 1].
                0 = start of section, 1 = end of section.

        Returns:
            Multiplier in range [1.0 - intensity/2, 1.0 + intensity/2].
            For steady shape, always returns 1.0.

        Example:
            >>> shape = DynamicsShape(shape=DynamicsShapeType.ARCH, peak_position=0.7)
            >>> shape.velocity_multiplier(0.7)  # At peak
            1.35
            >>> shape.velocity_multiplier(0.0)  # At start
            0.65
        """
        pos = max(0.0, min(1.0, position))
        half_range = self.intensity / 2.0

        if self.shape == DynamicsShapeType.STEADY:
            return 1.0

        if self.shape == DynamicsShapeType.CRESCENDO:
            # Linear rise: min at start, max at end
            return 1.0 - half_range + (self.intensity * pos)

        if self.shape == DynamicsShapeType.DECRESCENDO:
            # Linear fall: max at start, min at end
            return 1.0 + half_range - (self.intensity * pos)

        if self.shape in (DynamicsShapeType.ARCH, DynamicsShapeType.HAIRPIN):
            # Rise to peak_position, then fall
            peak = self.peak_position
            if pos <= peak:
                # Rising phase
                t = pos / peak if peak > 0 else 1.0
                return 1.0 - half_range + (self.intensity * t)
            else:
                # Falling phase
                remaining = 1.0 - peak
                t = (pos - peak) / remaining if remaining > 0 else 0.0
                return 1.0 + half_range - (self.intensity * t)

        return 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        result: dict[str, Any] = {
            "shape": self.shape.value,
            "intensity": self.intensity,
        }
        if self.shape in (DynamicsShapeType.ARCH, DynamicsShapeType.HAIRPIN):
            result["peak_position"] = self.peak_position
        if self.accents:
            result["accents"] = [a.to_dict() for a in self.accents]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DynamicsShape:
        """Deserialize from dict."""
        return cls(
            shape=DynamicsShapeType(data["shape"]),
            peak_position=data.get("peak_position", 0.5),
            intensity=data.get("intensity", 0.7),
            accents=tuple(BarAccent.from_dict(a) for a in data.get("accents", [])),
        )
