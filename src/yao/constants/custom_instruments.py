"""Custom instrument profile definitions.

Loads non-Western and specialized instrument profiles from
``custom_instruments/*.yaml``. Each profile describes range,
GM mapping, idiomatic techniques, and cultural origin.

Belongs to Layer 0 (Constants).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CustomInstrument:
    """A custom instrument profile for non-GM or non-Western instruments.

    Attributes:
        name: Instrument name (e.g., "shakuhachi", "oud").
        midi_low: Lowest playable MIDI note.
        midi_high: Highest playable MIDI note.
        gm_program: GM program number for approximation (0-indexed).
        custom_sf2_path: Optional path to a dedicated SoundFont.
        cultural_origin: Cultural tradition (e.g., "japanese", "indian").
        idiomatic_techniques: List of characteristic playing techniques.
        typical_velocity_range: Tuple of (min, max) typical velocities.
        typical_scales: List of scale names this instrument commonly uses.
        notes: Additional notes about the instrument.

    Example:
        >>> shaku = load_custom_instrument("shakuhachi")
        >>> shaku.cultural_origin
        'japanese'
    """

    name: str
    midi_low: int
    midi_high: int
    gm_program: int | None = None
    custom_sf2_path: str | None = None
    cultural_origin: str = ""
    idiomatic_techniques: tuple[str, ...] = ()
    typical_velocity_range: tuple[int, int] = (40, 100)
    typical_scales: tuple[str, ...] = ()
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CustomInstrument:
        """Create from a dict (YAML-loaded data)."""
        vel = data.get("typical_velocity_range", [40, 100])
        return cls(
            name=data["name"],
            midi_low=data["midi_low"],
            midi_high=data["midi_high"],
            gm_program=data.get("gm_program"),
            custom_sf2_path=data.get("custom_sf2_path"),
            cultural_origin=data.get("cultural_origin", ""),
            idiomatic_techniques=tuple(data.get("idiomatic_techniques", [])),
            typical_velocity_range=(vel[0], vel[1]) if len(vel) >= 2 else (40, 100),
            typical_scales=tuple(data.get("typical_scales", [])),
            notes=data.get("notes", "").strip(),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> CustomInstrument:
        """Load from a YAML file."""
        with open(path) as f:
            data: Any = yaml.safe_load(f) or {}
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# Custom instruments directory and registry
# ---------------------------------------------------------------------------

_CUSTOM_DIR = Path(__file__).resolve().parent.parent.parent.parent / "custom_instruments"


def load_custom_instrument(name: str) -> CustomInstrument:
    """Load a named custom instrument profile.

    Args:
        name: Instrument name (e.g., "shakuhachi"). Must match a YAML file.

    Returns:
        The loaded CustomInstrument.

    Raises:
        FileNotFoundError: If the instrument YAML does not exist.
    """
    path = _CUSTOM_DIR / f"{name}.yaml"
    if not path.exists():
        msg = f"Custom instrument '{name}' not found at {path}"
        raise FileNotFoundError(msg)
    return CustomInstrument.from_yaml(path)


def available_custom_instruments() -> list[str]:
    """Return names of all available custom instrument profiles.

    Returns:
        Sorted list of instrument names (without .yaml extension).
    """
    if not _CUSTOM_DIR.exists():
        return []
    return sorted(p.stem for p in _CUSTOM_DIR.glob("*.yaml"))
