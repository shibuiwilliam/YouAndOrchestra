"""Tests for tools/check_plan_consumption.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))

import check_plan_consumption  # noqa: E402


class TestPlanFieldVisitor:
    """Tests for the AST visitor."""

    def test_detects_plan_attribute_access(self) -> None:
        import ast

        source = """
def realize(self, plan):
    form = plan.form
    harmony = plan.harmony
    return form, harmony
"""
        tree = ast.parse(source)
        visitor = check_plan_consumption.PlanFieldVisitor()
        visitor.visit(tree)
        assert "form" in visitor.accessed_attrs
        assert "harmony" in visitor.accessed_attrs

    def test_detects_plan_to_v1_call(self) -> None:
        import ast

        source = """
def realize(self, plan):
    spec = _plan_to_v1_spec(plan)
    return generate(spec)
"""
        tree = ast.parse(source)
        visitor = check_plan_consumption.PlanFieldVisitor()
        visitor.visit(tree)
        assert visitor.uses_plan_to_v1 is True

    def test_no_false_positive_on_define(self) -> None:
        import ast

        source = """
def _plan_to_v1_spec(plan):
    return CompositionSpec()
"""
        tree = ast.parse(source)
        visitor = check_plan_consumption.PlanFieldVisitor()
        visitor.visit(tree)
        # Defining the function is not the same as calling it
        assert visitor.uses_plan_to_v1 is False


class TestDetectConsumedFields:
    """Tests for _detect_consumed_fields."""

    def test_maps_form_access(self) -> None:
        result = check_plan_consumption._detect_consumed_fields({"form", "sections"})
        assert "form" in result

    def test_maps_harmony_access(self) -> None:
        result = check_plan_consumption._detect_consumed_fields({"chord_events"})
        assert "harmony" in result

    def test_maps_trajectory_access(self) -> None:
        result = check_plan_consumption._detect_consumed_fields({"tension", "density"})
        assert "trajectory" in result

    def test_empty_attrs(self) -> None:
        result = check_plan_consumption._detect_consumed_fields(set())
        assert result == []


class TestAnalyzeRealizer:
    """Tests for analyze_realizer."""

    def test_analyzes_file_with_plan_access(self, tmp_path: Path) -> None:
        realizer = tmp_path / "my_realizer.py"
        realizer.write_text("""
class MyNoteRealizer:
    def realize(self, plan):
        form = plan.form
        harmony = plan.harmony
        motifs = plan.motifs_phrases
        arrangement = plan.arrangement
        drums = plan.drums
        trajectory = plan.trajectory
        return self._generate(form, harmony)
""")
        with patch.object(check_plan_consumption, "REPO_ROOT", tmp_path):
            result = check_plan_consumption.analyze_realizer(realizer)
        assert result.consumed_ratio >= 0.8
        assert not result.uses_legacy_adapter

    def test_detects_legacy_adapter_usage(self, tmp_path: Path) -> None:
        realizer = tmp_path / "legacy_realizer.py"
        realizer.write_text("""
class LegacyNoteRealizer:
    def realize(self, plan):
        spec = _plan_to_v1_spec(plan)
        return old_generate(spec)
""")
        with patch.object(check_plan_consumption, "REPO_ROOT", tmp_path):
            result = check_plan_consumption.analyze_realizer(realizer)
        assert result.uses_legacy_adapter is True
        assert result.passed is False


class TestMainExitCode:
    """Tests for main() exit code."""

    def test_returns_zero_in_non_strict_mode(self, tmp_path: Path) -> None:
        note_dir = tmp_path / "src" / "yao" / "generators" / "note"
        note_dir.mkdir(parents=True)
        (note_dir / "rule_based.py").write_text("""
class RuleBasedNoteRealizer:
    def realize(self, plan):
        spec = _plan_to_v1_spec(plan)
        return generate(spec)
""")
        with (
            patch.object(check_plan_consumption, "REPO_ROOT", tmp_path),
            patch.object(sys, "argv", ["check_plan_consumption.py"]),
        ):
            result = check_plan_consumption.main()
        assert result == 0  # non-strict → warn only
