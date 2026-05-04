"""GrooveProfile — ensemble-wide microtiming and velocity profile.

A GrooveProfile defines a groove as an ensemble-wide property, not
just a drum parameter. It specifies microtiming offsets per 16th-note
position, velocity patterns, ghost note probability, swing, and
humanization jitter.

The GrooveApplicator applies this profile to ALL instruments (unless
apply_to_all_instruments is False, in which case only drums are grooved).

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GrooveProfile:
    """Ensemble-wide groove specification.

    Applied to all instruments by the GrooveApplicator before MIDI output.
    Genre-specific profiles live in ``grooves/*.yaml``.

    Attributes:
        name: Profile identifier (e.g., "lofi_hiphop", "jazz_swing").
        microtiming: 16th-note position (0–15) → ms offset from grid.
            Positive = late (laid-back), negative = ahead (pushing).
            Values must be in [-50, 50] ms.
        velocity_pattern: 16th-note position (0–15) → velocity multiplier.
            1.0 = no change; >1.0 = accent; <1.0 = softer.
        ghost_probability: Probability [0, 1] that ghost notes are inserted.
        swing_ratio: 0.5 = straight, 0.667 = triplet swing.
        timing_jitter_sigma: Standard deviation in ms for humanization noise.
        apply_to_all_instruments: If True, all instruments get groove.
            If False, only drum/percussion parts are affected.

    Example:
        >>> profile = GrooveProfile(
        ...     name="lofi_hiphop",
        ...     microtiming={0: 0.0, 4: 5.0, 8: -3.0, 12: 8.0},
        ...     velocity_pattern={0: 1.1, 4: 0.9, 8: 1.0, 12: 0.85},
        ...     ghost_probability=0.15,
        ...     swing_ratio=0.58,
        ...     timing_jitter_sigma=6.0,
        ... )
    """

    name: str
    microtiming: dict[int, float] = field(default_factory=dict)
    velocity_pattern: dict[int, float] = field(default_factory=dict)
    ghost_probability: float = 0.0
    swing_ratio: float = 0.5
    timing_jitter_sigma: float = 0.0
    apply_to_all_instruments: bool = True

    def __post_init__(self) -> None:
        """Validate invariants."""
        for pos, offset in self.microtiming.items():
            if not 0 <= pos <= 15:
                msg = f"Microtiming position must be 0–15, got {pos}"
                raise ValueError(msg)
            if abs(offset) > 50.0:
                msg = f"Microtiming offset must be in [-50, 50] ms, got {offset} at position {pos}"
                raise ValueError(msg)
        for pos, mult in self.velocity_pattern.items():
            if not 0 <= pos <= 15:
                msg = f"Velocity pattern position must be 0–15, got {pos}"
                raise ValueError(msg)
            if mult < 0.0:
                msg = f"Velocity multiplier must be non-negative, got {mult}"
                raise ValueError(msg)
        if not 0.0 <= self.ghost_probability <= 1.0:
            msg = f"Ghost probability must be in [0, 1], got {self.ghost_probability}"
            raise ValueError(msg)
        if not 0.0 <= self.swing_ratio <= 1.0:
            msg = f"Swing ratio must be in [0, 1], got {self.swing_ratio}"
            raise ValueError(msg)
        if self.timing_jitter_sigma < 0.0:
            msg = f"Timing jitter sigma must be non-negative, got {self.timing_jitter_sigma}"
            raise ValueError(msg)

    def microtiming_at(self, position_16th: int) -> float:
        """Return the microtiming offset for a 16th-note position.

        Args:
            position_16th: 16th-note position within the bar (0–15).

        Returns:
            Offset in milliseconds. 0.0 if position not in pattern.
        """
        return self.microtiming.get(position_16th % 16, 0.0)

    def velocity_mult_at(self, position_16th: int) -> float:
        """Return the velocity multiplier for a 16th-note position.

        Args:
            position_16th: 16th-note position within the bar (0–15).

        Returns:
            Multiplier. 1.0 if position not in pattern.
        """
        return self.velocity_pattern.get(position_16th % 16, 1.0)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "name": self.name,
            "microtiming": {str(k): v for k, v in self.microtiming.items()},
            "velocity_pattern": {str(k): v for k, v in self.velocity_pattern.items()},
            "ghost_probability": self.ghost_probability,
            "swing_ratio": self.swing_ratio,
            "timing_jitter_sigma": self.timing_jitter_sigma,
            "apply_to_all_instruments": self.apply_to_all_instruments,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GrooveProfile:
        """Deserialize from dict."""
        microtiming = {int(k): float(v) for k, v in data.get("microtiming", {}).items()}
        velocity_pattern = {int(k): float(v) for k, v in data.get("velocity_pattern", {}).items()}
        return cls(
            name=data["name"],
            microtiming=microtiming,
            velocity_pattern=velocity_pattern,
            ghost_probability=data.get("ghost_probability", 0.0),
            swing_ratio=data.get("swing_ratio", 0.5),
            timing_jitter_sigma=data.get("timing_jitter_sigma", 0.0),
            apply_to_all_instruments=data.get("apply_to_all_instruments", True),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> GrooveProfile:
        """Load a GrooveProfile from a YAML file.

        Args:
            path: Path to a groove YAML file.

        Returns:
            Validated GrooveProfile.

        Raises:
            ValueError: If the YAML is invalid.
        """
        with open(path) as f:
            data: Any = yaml.safe_load(f) or {}
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Groove library loader
# ---------------------------------------------------------------------------

_GROOVES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "grooves"


def load_groove(name: str) -> GrooveProfile:
    """Load a named groove profile from the grooves/ directory.

    Args:
        name: Groove name (e.g., "lofi_hiphop"). Must match a YAML file.

    Returns:
        The loaded GrooveProfile.

    Raises:
        FileNotFoundError: If the groove YAML does not exist.
    """
    path = _GROOVES_DIR / f"{name}.yaml"
    if not path.exists():
        msg = f"Groove profile '{name}' not found at {path}"
        raise FileNotFoundError(msg)
    return GrooveProfile.from_yaml(path)


def available_grooves() -> list[str]:
    """Return names of all available groove profiles.

    Returns:
        Sorted list of groove names (without .yaml extension).
    """
    if not _GROOVES_DIR.exists():
        return []
    return sorted(p.stem for p in _GROOVES_DIR.glob("*.yaml"))
