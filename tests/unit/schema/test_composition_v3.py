"""Tests for v3 spec composability (extends/overrides)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yao.errors import SpecValidationError
from yao.schema.composition_v3 import is_v3_spec, resolve_v3_spec
from yao.schema.deep_merge import deep_merge


class TestDeepMerge:
    """Test the deep merge utility."""

    def test_flat_merge(self) -> None:
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}
        result = deep_merge(base, overlay)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        base = {"a": {"b": 1, "c": 2}}
        overlay = {"a": {"c": 3, "d": 4}}
        result = deep_merge(base, overlay)
        assert result == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_overlay_none_skipped(self) -> None:
        base = {"a": 1, "b": 2}
        overlay = {"a": None, "b": 3}
        result = deep_merge(base, overlay)
        assert result == {"a": 1, "b": 3}

    def test_list_replaced_not_appended(self) -> None:
        base = {"items": [1, 2, 3]}
        overlay = {"items": [4, 5]}
        result = deep_merge(base, overlay)
        assert result == {"items": [4, 5]}

    def test_original_not_modified(self) -> None:
        base = {"a": {"b": 1}}
        overlay = {"a": {"b": 2}}
        deep_merge(base, overlay)
        assert base == {"a": {"b": 1}}  # unchanged

    def test_deep_nested(self) -> None:
        base = {"a": {"b": {"c": {"d": 1}}}}
        overlay = {"a": {"b": {"c": {"e": 2}}}}
        result = deep_merge(base, overlay)
        assert result == {"a": {"b": {"c": {"d": 1, "e": 2}}}}


class TestIsV3Spec:
    """Test v3 detection."""

    def test_extends_detected(self) -> None:
        assert is_v3_spec({"extends": ["base.yaml"]}) is True

    def test_overrides_detected(self) -> None:
        assert is_v3_spec({"overrides": {"tempo_bpm": 90}}) is True

    def test_v1_spec_not_v3(self) -> None:
        assert is_v3_spec({"title": "Test", "tempo_bpm": 120}) is False


class TestResolveV3Spec:
    """Test v3 spec resolution."""

    def test_no_extends_passes_through(self) -> None:
        data = {"title": "Test", "tempo_bpm": 120}
        result = resolve_v3_spec(data)
        assert result["title"] == "Test"
        assert result["tempo_bpm"] == 120

    def test_extends_from_fragment(self, tmp_path: Path) -> None:
        # Create a fragment
        frag = tmp_path / "base.yaml"
        frag.write_text(yaml.dump({"tempo_bpm": 90, "key": "C major"}))

        data = {"extends": [str(frag)], "title": "Extended"}
        result = resolve_v3_spec(data, fragments_dir=tmp_path)
        assert result["tempo_bpm"] == 90
        assert result["key"] == "C major"
        assert result["title"] == "Extended"

    def test_overrides_apply_last(self, tmp_path: Path) -> None:
        frag = tmp_path / "base.yaml"
        frag.write_text(yaml.dump({"tempo_bpm": 90, "key": "C major"}))

        data = {
            "extends": [str(frag)],
            "title": "Test",
            "overrides": {"tempo_bpm": 120},
        }
        result = resolve_v3_spec(data, fragments_dir=tmp_path)
        assert result["tempo_bpm"] == 120  # overridden
        assert result["key"] == "C major"  # from fragment

    def test_multiple_extends_merge_in_order(self, tmp_path: Path) -> None:
        frag1 = tmp_path / "first.yaml"
        frag1.write_text(yaml.dump({"tempo_bpm": 90, "key": "C major"}))
        frag2 = tmp_path / "second.yaml"
        frag2.write_text(yaml.dump({"key": "D minor", "genre": "jazz"}))

        data = {"extends": [str(frag1), str(frag2)], "title": "Multi"}
        result = resolve_v3_spec(data, fragments_dir=tmp_path)
        assert result["tempo_bpm"] == 90  # from first
        assert result["key"] == "D minor"  # second overrides first
        assert result["genre"] == "jazz"  # from second

    def test_fragment_by_name(self, tmp_path: Path) -> None:
        frag = tmp_path / "jazz_base.yaml"
        frag.write_text(yaml.dump({"tempo_bpm": 140, "key": "Bb major"}))

        data = {"extends": ["jazz_base"], "title": "Named"}
        result = resolve_v3_spec(data, fragments_dir=tmp_path)
        assert result["tempo_bpm"] == 140

    def test_missing_fragment_raises(self, tmp_path: Path) -> None:
        data = {"extends": ["nonexistent_fragment"]}
        with pytest.raises(SpecValidationError, match="not found"):
            resolve_v3_spec(data, fragments_dir=tmp_path)

    def test_circular_extends_raises(self, tmp_path: Path) -> None:
        frag = tmp_path / "self.yaml"
        frag.write_text(yaml.dump({"tempo_bpm": 100}))

        data = {"extends": [str(frag), str(frag)]}
        with pytest.raises(SpecValidationError, match="Circular"):
            resolve_v3_spec(data, fragments_dir=tmp_path)
