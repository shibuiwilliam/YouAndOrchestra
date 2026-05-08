"""ProductionProfile — genre-specific mix and master settings.

Each profile captures the production characteristics that make a genre
sound authentic: target loudness, effect chains, stereo imaging,
and signature processing (sidechain, tape saturation, vinyl simulation).

Profiles are authored as YAML in ``src/yao/production/profiles/<name>.yaml``
and loaded by the Mix Engineer subagent during audio rendering.

Belongs to Layer 5 (Rendering adjunct).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator

_PROFILES_DIR = Path(__file__).resolve().parent / "profiles"


class EffectSpec(BaseModel):
    """Specification for a single audio effect in a chain."""

    type: str
    params: dict[str, float | str | bool] = {}

    model_config = {"extra": "allow"}


class CompressorSettings(BaseModel):
    """Compressor configuration."""

    threshold_db: float = -12.0
    ratio: float = 2.0
    attack_ms: float = 10.0
    release_ms: float = 100.0
    makeup_db: float = 0.0

    model_config = {"extra": "allow"}


class LimiterSettings(BaseModel):
    """Brick-wall limiter configuration."""

    threshold_db: float = -1.0
    release_ms: float = 50.0

    model_config = {"extra": "allow"}


class ProductionProfile(BaseModel):
    """Genre-specific production/mixing profile.

    Attributes:
        name: Profile identifier.
        genre_tags: Genres this profile applies to.
        target_lufs: Target integrated loudness.
        target_peak_db: Maximum peak level.
        stereo_width: 0.0 (mono) to 1.0 (maximum stereo).
        effect_chains: Per-instrument-role effect chains.
        master_compressor: Master bus compressor settings.
        master_limiter: Master bus limiter settings.
        tape_saturation: 0.0 (none) to 1.0 (heavy).
        sidechain_enabled: Whether sidechain compression is active.
        sidechain_source: Instrument triggering the sidechain.
        vinyl_simulation: Whether vinyl crackle/warmth is applied.
        reverb_type: Reverb character (room, plate, hall, spring).
        reverb_amount: 0.0 (dry) to 1.0 (heavy).
        bit_crush: 0.0 (none) to 1.0 (heavy bit reduction).
        lo_pass_hz: Low-pass filter cutoff (0 = disabled).
    """

    name: str
    genre_tags: list[str] = []

    # Loudness targets
    target_lufs: float = -14.0
    target_peak_db: float = -1.0
    stereo_width: float = 0.5

    # Effect chains per instrument role
    effect_chains: dict[str, list[EffectSpec]] = {}

    # Master bus
    master_compressor: CompressorSettings | None = None
    master_limiter: LimiterSettings | None = None

    # Signature processing
    tape_saturation: float = 0.0
    sidechain_enabled: bool = False
    sidechain_source: str = "kick"
    vinyl_simulation: bool = False
    reverb_type: str = "room"
    reverb_amount: float = 0.3
    bit_crush: float = 0.0
    lo_pass_hz: int = 0

    model_config = {"extra": "allow"}

    @field_validator("tape_saturation", "stereo_width", "reverb_amount", "bit_crush")
    @classmethod
    def _clamp_0_1(cls, v: float) -> float:
        """Clamp to [0.0, 1.0] range."""
        return max(0.0, min(1.0, v))

    @classmethod
    def from_yaml_data(cls, data: dict[str, Any]) -> ProductionProfile:
        """Create a ProductionProfile from parsed YAML data."""
        return cls.model_validate(data)


# ── Profile loading ──────────────────────────────────────────────────

_cache: dict[str, ProductionProfile] = {}


def load_production_profile(name: str) -> ProductionProfile | None:
    """Load a production profile by name.

    Args:
        name: Profile identifier (e.g., "lofi_hip_hop", "modern_rock").

    Returns:
        ProductionProfile if found, None otherwise.
    """
    if name in _cache:
        return _cache[name]

    yaml_path = _PROFILES_DIR / f"{name}.yaml"
    if not yaml_path.exists():
        return None

    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    profile = ProductionProfile.from_yaml_data(data)
    _cache[name] = profile
    return profile


def all_production_profiles() -> dict[str, ProductionProfile]:
    """Load and return all production profiles.

    Returns:
        Dict mapping profile name to ProductionProfile.
    """
    profiles: dict[str, ProductionProfile] = {}
    if not _PROFILES_DIR.exists():
        return profiles

    for yaml_path in sorted(_PROFILES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "name" in data:
                profile = ProductionProfile.from_yaml_data(data)
                profiles[profile.name] = profile
        except Exception:
            continue

    return profiles
