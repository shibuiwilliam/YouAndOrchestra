"""Tests for TensionArcsSpec schema (Layer 1).

Tests cover:
- Valid spec loading
- Cross-spec validation against section names
- Span validation (2–8 bars)
- Duplicate id rejection
- Round-trip from YAML
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from yao.errors import SpecValidationError
from yao.schema.tension_arcs import TensionArcsSpec


def _write_yaml(content: str) -> Path:
    """Write YAML content to a temp file and return its path."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        return Path(tmp.name)


class TestTensionArcsSpec:
    """Tests for TensionArcsSpec."""

    def test_valid_spec(self) -> None:
        spec = TensionArcsSpec.model_validate(
            {
                "schema_version": "1.0",
                "tension_arcs": [
                    {
                        "id": "approach_chorus",
                        "location": {"section": "verse", "bars": [5, 8]},
                        "pattern": "linear_rise",
                        "target_release": {"section": "chorus", "bar": 1},
                        "intensity": 0.8,
                        "mechanism": "secondary_dominant_chain",
                    },
                ],
            }
        )
        assert len(spec.tension_arcs) == 1
        assert spec.tension_arcs[0].id == "approach_chorus"

    def test_empty_arcs(self) -> None:
        spec = TensionArcsSpec.model_validate(
            {
                "schema_version": "1.0",
                "tension_arcs": [],
            }
        )
        assert len(spec.tension_arcs) == 0

    def test_duplicate_ids_rejected(self) -> None:
        with pytest.raises(SpecValidationError, match="Duplicate"):
            TensionArcsSpec.model_validate(
                {
                    "tension_arcs": [
                        {
                            "id": "dupe",
                            "location": {"section": "verse", "bars": [1, 4]},
                            "pattern": "linear_rise",
                            "intensity": 0.5,
                        },
                        {
                            "id": "dupe",
                            "location": {"section": "chorus", "bars": [1, 4]},
                            "pattern": "spike",
                            "intensity": 0.7,
                        },
                    ],
                }
            )

    def test_span_too_short(self) -> None:
        with pytest.raises(SpecValidationError, match="span must be 2–8"):
            TensionArcsSpec.model_validate(
                {
                    "tension_arcs": [
                        {
                            "id": "short",
                            "location": {"section": "verse", "bars": [3, 3]},
                            "pattern": "spike",
                            "intensity": 0.5,
                        },
                    ],
                }
            )

    def test_span_too_long(self) -> None:
        with pytest.raises(SpecValidationError, match="span must be 2–8"):
            TensionArcsSpec.model_validate(
                {
                    "tension_arcs": [
                        {
                            "id": "long",
                            "location": {"section": "verse", "bars": [1, 10]},
                            "pattern": "plateau",
                            "intensity": 0.5,
                        },
                    ],
                }
            )

    def test_intensity_out_of_range(self) -> None:
        with pytest.raises((Exception, ValueError)):
            TensionArcsSpec.model_validate(
                {
                    "tension_arcs": [
                        {
                            "id": "hot",
                            "location": {"section": "verse", "bars": [1, 4]},
                            "pattern": "spike",
                            "intensity": 1.5,
                        },
                    ],
                }
            )

    def test_cross_spec_valid(self) -> None:
        spec = TensionArcsSpec.model_validate(
            {
                "tension_arcs": [
                    {
                        "id": "a1",
                        "location": {"section": "verse", "bars": [1, 4]},
                        "pattern": "linear_rise",
                        "target_release": {"section": "chorus", "bar": 1},
                        "intensity": 0.5,
                    },
                ],
            }
        )
        errors = spec.validate_against_sections(["verse", "chorus", "outro"])
        assert len(errors) == 0

    def test_cross_spec_unknown_section(self) -> None:
        spec = TensionArcsSpec.model_validate(
            {
                "tension_arcs": [
                    {
                        "id": "a1",
                        "location": {"section": "nonexistent", "bars": [1, 4]},
                        "pattern": "linear_rise",
                        "intensity": 0.5,
                    },
                ],
            }
        )
        errors = spec.validate_against_sections(["verse", "chorus"])
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_cross_spec_unknown_release_section(self) -> None:
        spec = TensionArcsSpec.model_validate(
            {
                "tension_arcs": [
                    {
                        "id": "a1",
                        "location": {"section": "verse", "bars": [1, 4]},
                        "pattern": "linear_rise",
                        "target_release": {"section": "nowhere", "bar": 1},
                        "intensity": 0.5,
                    },
                ],
            }
        )
        errors = spec.validate_against_sections(["verse", "chorus"])
        assert len(errors) == 1
        assert "nowhere" in errors[0]


class TestTensionArcsYamlLoading:
    """Tests for loading from YAML files."""

    def test_load_valid_yaml(self) -> None:
        content = """
schema_version: "1.0"
tension_arcs:
  - id: "test_arc"
    location:
      section: verse
      bars: [1, 4]
    pattern: linear_rise
    target_release:
      section: chorus
      bar: 1
    intensity: 0.7
    mechanism: "dominant_prolongation"
"""
        path = _write_yaml(content)
        spec = TensionArcsSpec.from_yaml(path)
        assert len(spec.tension_arcs) == 1
        assert spec.tension_arcs[0].mechanism == "dominant_prolongation"

    def test_load_empty_yaml(self) -> None:
        content = """
schema_version: "1.0"
tension_arcs: []
"""
        path = _write_yaml(content)
        spec = TensionArcsSpec.from_yaml(path)
        assert len(spec.tension_arcs) == 0

    def test_all_patterns_accepted(self) -> None:
        for pattern in ["linear_rise", "dip", "plateau", "spike", "deceptive"]:
            spec = TensionArcsSpec.model_validate(
                {
                    "tension_arcs": [
                        {
                            "id": f"arc_{pattern}",
                            "location": {"section": "verse", "bars": [1, 4]},
                            "pattern": pattern,
                            "intensity": 0.5,
                        },
                    ],
                }
            )
            assert spec.tension_arcs[0].pattern == pattern

    def test_no_release_allowed(self) -> None:
        spec = TensionArcsSpec.model_validate(
            {
                "tension_arcs": [
                    {
                        "id": "unresolved",
                        "location": {"section": "verse", "bars": [1, 4]},
                        "pattern": "deceptive",
                        "intensity": 0.6,
                    },
                ],
            }
        )
        assert spec.tension_arcs[0].target_release is None
