"""Tests for GrooveSpec schema (Layer 1).

Tests cover:
- Valid spec loading
- Override validation
- YAML loading
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from yao.schema.groove import GrooveSpec


def _write_yaml(content: str) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        return Path(tmp.name)


class TestGrooveSpec:
    """Tests for GrooveSpec."""

    def test_valid_spec(self) -> None:
        spec = GrooveSpec.model_validate(
            {
                "base": "lofi_hiphop",
                "overrides": {"swing_ratio": 0.58},
                "apply_to_all_instruments": True,
            }
        )
        assert spec.base == "lofi_hiphop"
        assert spec.overrides.swing_ratio == 0.58

    def test_empty_spec(self) -> None:
        spec = GrooveSpec.model_validate({})
        assert spec.base == ""
        assert spec.apply_to_all_instruments is True

    def test_overrides_only(self) -> None:
        spec = GrooveSpec.model_validate(
            {
                "overrides": {
                    "timing_jitter_sigma": 8.0,
                    "ghost_probability": 0.2,
                },
            }
        )
        assert spec.overrides.timing_jitter_sigma == 8.0
        assert spec.overrides.ghost_probability == 0.2

    def test_load_from_yaml(self) -> None:
        content = """
schema_version: "1.0"
base: jazz_swing
overrides:
  swing_ratio: 0.7
apply_to_all_instruments: true
"""
        path = _write_yaml(content)
        spec = GrooveSpec.from_yaml(path)
        assert spec.base == "jazz_swing"
        assert spec.overrides.swing_ratio == 0.7

    def test_load_nested_groove_key(self) -> None:
        """Support groove.yaml with a top-level 'groove:' key."""
        content = """
groove:
  base: pop_straight
  apply_to_all_instruments: false
"""
        path = _write_yaml(content)
        spec = GrooveSpec.from_yaml(path)
        assert spec.base == "pop_straight"
        assert spec.apply_to_all_instruments is False

    def test_drums_only(self) -> None:
        spec = GrooveSpec.model_validate(
            {
                "base": "rock_backbeat",
                "apply_to_all_instruments": False,
            }
        )
        assert spec.apply_to_all_instruments is False
