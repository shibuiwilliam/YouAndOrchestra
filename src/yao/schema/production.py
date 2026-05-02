"""Pydantic models for production.yaml specification.

Defines mix and mastering parameters: per-track EQ, compression, reverb,
and master bus processing. Belongs to Layer 1 (Specification).

Two levels of spec coexist:
- ``ProductionSpec`` (v1, simple) — target LUFS + stereo width + reverb amount.
- ``ProductionManifest`` (v2, full) — per-track chains + master bus.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError

# ---------------------------------------------------------------------------
# v1 simple spec (backward compatible)
# ---------------------------------------------------------------------------


class ProductionSpec(BaseModel):
    """Simple mix and mastering specification (v1).

    Attributes:
        target_lufs: Target integrated loudness in LUFS.
        stereo_width: Stereo width percentage (0.0=mono, 1.0=full stereo).
        reverb_amount: Global reverb send level (0.0-1.0).
        master_eq: Optional master EQ description.
    """

    target_lufs: float = -14.0
    stereo_width: float = 0.8
    reverb_amount: float = 0.3
    master_eq: str = ""

    @field_validator("target_lufs")
    @classmethod
    def lufs_reasonable(cls, v: float) -> float:
        if not -30.0 <= v <= 0.0:
            raise SpecValidationError(
                f"LUFS target must be between -30 and 0, got {v}",
                field="target_lufs",
            )
        return v

    @field_validator("stereo_width")
    @classmethod
    def width_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Stereo width must be 0.0-1.0, got {v}",
                field="stereo_width",
            )
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> ProductionSpec:
        """Load from a YAML file.

        Args:
            path: Path to production.yaml.

        Returns:
            Validated ProductionSpec.

        Raises:
            SpecValidationError: If loading fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load production spec: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Production YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Production validation failed: {e}") from e


# ---------------------------------------------------------------------------
# v2 full manifest (PROJECT.md §7.7)
# ---------------------------------------------------------------------------


class EQBand(BaseModel):
    """A single EQ band.

    Attributes:
        freq: Center/corner frequency in Hz.
        gain: Gain in dB (-24 to +24).
        q: Q factor (bandwidth). Higher = narrower.
        type: Filter type.
    """

    freq: float
    gain: float = 0.0
    q: float = 1.0
    type: Literal["high_pass", "low_pass", "peak", "low_shelf", "high_shelf"] = "peak"

    @field_validator("freq")
    @classmethod
    def freq_positive(cls, v: float) -> float:
        if v <= 0:
            raise SpecValidationError(f"EQ freq must be positive, got {v}", field="eq.freq")
        return v

    @field_validator("gain")
    @classmethod
    def gain_reasonable(cls, v: float) -> float:
        if not -24.0 <= v <= 24.0:
            raise SpecValidationError(f"EQ gain must be -24..+24 dB, got {v}", field="eq.gain")
        return v


class CompressionSpec(BaseModel):
    """Compressor parameters.

    Attributes:
        threshold_db: Threshold in dB.
        ratio: Compression ratio (e.g., 2.5 = 2.5:1).
        attack_ms: Attack time in milliseconds.
        release_ms: Release time in milliseconds.
    """

    threshold_db: float = -18.0
    ratio: float = 2.5
    attack_ms: float = 15.0
    release_ms: float = 80.0

    @field_validator("ratio")
    @classmethod
    def ratio_positive(cls, v: float) -> float:
        if v < 1.0:
            raise SpecValidationError(f"Compression ratio must be >= 1.0, got {v}", field="ratio")
        return v


class ReverbSpec(BaseModel):
    """Reverb parameters.

    Attributes:
        type: Reverb preset name.
        wet: Wet/dry mix (0.0=dry, 1.0=fully wet).
        decay_sec: Decay time in seconds.
    """

    type: Literal["hall", "room", "plate", "spring"] = "hall"
    wet: float = 0.25
    decay_sec: float = 1.8

    @field_validator("wet")
    @classmethod
    def wet_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(f"Reverb wet must be 0.0-1.0, got {v}", field="wet")
        return v


class TrackMixSpec(BaseModel):
    """Per-track mix specification.

    Attributes:
        eq: List of EQ bands to apply in order.
        compression: Optional compressor.
        reverb: Optional reverb send.
        pan: Stereo pan position (-1.0=hard left, 0.0=center, 1.0=hard right).
        gain_db: Track gain in dB.
    """

    eq: list[EQBand] = []  # noqa: RUF012
    compression: CompressionSpec | None = None
    reverb: ReverbSpec | None = None
    pan: float = 0.0
    gain_db: float = 0.0

    @field_validator("pan")
    @classmethod
    def pan_in_range(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            raise SpecValidationError(f"Pan must be -1.0..1.0, got {v}", field="pan")
        return v


class MasterSpec(BaseModel):
    """Master bus specification.

    Attributes:
        target_lufs: Target integrated loudness in LUFS.
        true_peak_max_dbfs: Maximum true-peak level in dBFS.
        stereo_width: Stereo width (0.0=mono, 1.0=full).
        compression: Optional master bus compressor.
    """

    target_lufs: float = -14.0
    true_peak_max_dbfs: float = -1.0
    stereo_width: float = 0.7
    compression: CompressionSpec | None = None

    @field_validator("target_lufs")
    @classmethod
    def lufs_reasonable(cls, v: float) -> float:
        if not -30.0 <= v <= 0.0:
            raise SpecValidationError(f"Master LUFS must be -30..0, got {v}", field="target_lufs")
        return v


class ProductionManifest(BaseModel):
    """Full production manifest (PROJECT.md §7.7).

    Attributes:
        master: Master bus processing spec.
        per_track: Per-instrument mix specs keyed by instrument name.
    """

    master: MasterSpec = MasterSpec()
    per_track: dict[str, TrackMixSpec] = {}  # noqa: RUF012

    @classmethod
    def from_yaml(cls, path: Path) -> ProductionManifest:
        """Load from a YAML file.

        Args:
            path: Path to production.yaml.

        Returns:
            Validated ProductionManifest.

        Raises:
            SpecValidationError: If loading fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load production manifest: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Production YAML root must be a mapping")
        # Support nested "production:" key
        if "production" in data:
            data = data["production"]
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Production manifest validation failed: {e}") from e
