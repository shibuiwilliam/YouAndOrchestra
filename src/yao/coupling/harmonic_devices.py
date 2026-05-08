"""Harmonic Devices Library — genre-typical harmonic gestures.

Loads and provides access to the harmonic device YAML library at
``src/yao/constants/harmonic_devices/``. Each device is a short chord
pattern used at specific structural positions.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §5.6, PROJECT.md §3.4.3, CLAUDE.md Phase 4.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_DEVICES_DIR = Path(__file__).resolve().parent.parent / "constants" / "harmonic_devices"
_DEVICE_CACHE: dict[str, HarmonicDevice] = {}


@dataclass(frozen=True)
class HarmonicDevice:
    """A genre-typical harmonic gesture.

    Attributes:
        name: Device identifier.
        description: What the device does harmonically.
        chord_pattern: List of Roman numeral chord symbols.
        placement: Where in the form this device is typically used.
        genres: List of compatible genre names.
        source: Provenance string.
        license: License string.
    """

    name: str
    description: str
    chord_pattern: tuple[str, ...]
    placement: str
    genres: tuple[str, ...]
    source: str
    license: str


def load_device(device_name: str) -> HarmonicDevice:
    """Load a harmonic device from YAML.

    Args:
        device_name: Filename without .yaml extension.

    Returns:
        Parsed HarmonicDevice.

    Raises:
        FileNotFoundError: If device file doesn't exist.
    """
    if device_name in _DEVICE_CACHE:
        return _DEVICE_CACHE[device_name]

    path = _DEVICES_DIR / f"{device_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Harmonic device not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    device = HarmonicDevice(
        name=data.get("name", device_name),
        description=data.get("description", ""),
        chord_pattern=tuple(data.get("chord_pattern", [])),
        placement=data.get("placement", "anywhere"),
        genres=tuple(data.get("genres", [])),
        source=data.get("source", ""),
        license=data.get("license", ""),
    )
    _DEVICE_CACHE[device_name] = device
    return device


def load_all_devices() -> list[HarmonicDevice]:
    """Load all harmonic devices from the library.

    Returns:
        List of all HarmonicDevice objects.
    """
    if not _DEVICES_DIR.exists():
        return []

    devices: list[HarmonicDevice] = []
    for path in sorted(_DEVICES_DIR.glob("*.yaml")):
        devices.append(load_device(path.stem))
    return devices


def devices_for_genre(genre: str) -> list[HarmonicDevice]:
    """Find devices compatible with a given genre.

    Args:
        genre: Genre name to filter by.

    Returns:
        List of HarmonicDevice objects that list this genre.
    """
    all_devices = load_all_devices()
    return [d for d in all_devices if genre in d.genres]


def devices_for_placement(placement: str) -> list[HarmonicDevice]:
    """Find devices suitable for a given structural placement.

    Args:
        placement: Placement type (e.g., "section_end", "intro").

    Returns:
        List of HarmonicDevice objects with matching placement.
    """
    all_devices = load_all_devices()
    return [d for d in all_devices if d.placement == placement or d.placement == "anywhere"]


def list_available_devices() -> list[str]:
    """List available harmonic device names.

    Returns:
        Sorted list of device names.
    """
    if not _DEVICES_DIR.exists():
        return []
    return sorted(p.stem for p in _DEVICES_DIR.glob("*.yaml"))


def clear_device_cache() -> None:
    """Clear the device cache."""
    _DEVICE_CACHE.clear()
