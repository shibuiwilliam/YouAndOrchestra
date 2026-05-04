"""Tests for HooksSpec schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.errors import SpecValidationError
from yao.schema.hooks import HookAppearanceSpec, HookSpec, HooksSpec


class TestHookSpec:
    def test_valid_hook(self) -> None:
        hook = HookSpec(
            id="main_hook",
            motif_ref="M1",
            deployment="withhold_then_release",
            appearances=[HookAppearanceSpec(section_id="chorus_1", bar=0)],
            distinctive_strength=0.9,
        )
        assert hook.id == "main_hook"
        assert hook.deployment == "withhold_then_release"

    def test_strength_out_of_range_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            HookSpec(id="h1", motif_ref="M1", distinctive_strength=1.5)

    def test_max_uses_zero_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            HookSpec(id="h1", motif_ref="M1", maximum_uses=0)

    def test_negative_bar_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            HookAppearanceSpec(section_id="chorus", bar=-1)


class TestHooksSpec:
    def test_empty_hooks(self) -> None:
        spec = HooksSpec(hooks=[])
        assert len(spec.hooks) == 0

    def test_duplicate_ids_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            HooksSpec(
                hooks=[
                    HookSpec(id="h1", motif_ref="M1"),
                    HookSpec(id="h1", motif_ref="M2"),
                ]
            )

    def test_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """
hooks:
  - id: main_hook
    motif_ref: M_chorus_main
    deployment: withhold_then_release
    appearances:
      - section_id: chorus_1
        bar: 0
      - section_id: chorus_2
        bar: 0
    variations_allowed: true
    maximum_uses: 4
    distinctive_strength: 0.9
"""
        path = tmp_path / "hooks.yaml"
        path.write_text(yaml_content)
        spec = HooksSpec.from_yaml(path)
        assert len(spec.hooks) == 1
        assert spec.hooks[0].id == "main_hook"
        assert spec.hooks[0].deployment == "withhold_then_release"
        assert len(spec.hooks[0].appearances) == 2

    def test_from_yaml_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SpecValidationError):
            HooksSpec.from_yaml(tmp_path / "nonexistent.yaml")

    def test_from_yaml_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "hooks.yaml"
        path.write_text("")
        spec = HooksSpec.from_yaml(path)
        assert len(spec.hooks) == 0
