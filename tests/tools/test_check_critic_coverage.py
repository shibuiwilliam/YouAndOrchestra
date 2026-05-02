"""Tests for tools/check_critic_coverage.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))

import check_critic_coverage  # noqa: E402


class TestCritiqueRuleVisitor:
    """Tests for the AST visitor."""

    def test_extracts_rule_metadata(self, tmp_path: Path) -> None:
        import ast

        source = """
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Severity, Role

class MyRule(CritiqueRule):
    rule_id = "test.my_rule"
    severity = Severity.MAJOR
    role = Role.MELODY

    def detect(self, plan, spec):
        return []
"""
        tree = ast.parse(source)
        visitor = check_critic_coverage.CritiqueRuleVisitor(tmp_path / "test.py")
        with patch.object(check_critic_coverage, "REPO_ROOT", tmp_path):
            visitor.visit(tree)
        assert len(visitor.rules) == 1
        assert visitor.rules[0].rule_id == "test.my_rule"
        assert visitor.rules[0].severity == "major"
        assert visitor.rules[0].role == "melody"

    def test_detects_early_return_on_empty_seeds(self, tmp_path: Path) -> None:
        import ast

        source = """
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Severity, Role

class EmptyCheckRule(CritiqueRule):
    rule_id = "test.empty_check"
    severity = Severity.CRITICAL
    role = Role.MELODY

    def detect(self, plan, spec):
        if not plan.motif.seeds:
            return []
        return [Finding()]
"""
        tree = ast.parse(source)
        visitor = check_critic_coverage.CritiqueRuleVisitor(tmp_path / "test.py")
        with patch.object(check_critic_coverage, "REPO_ROOT", tmp_path):
            visitor.visit(tree)
        assert len(visitor.rules) == 1
        assert visitor.rules[0].has_early_return_on_empty is True


class TestComputeCoverage:
    """Tests for _compute_coverage."""

    def test_all_severities_covered(self) -> None:
        rules = [
            check_critic_coverage.CritiqueRuleInfo(
                rule_id=f"test.{sev}",
                class_name=f"Rule{sev}",
                file_path="test.py",
                severity=sev,
                role="melody",
            )
            for sev in check_critic_coverage.EXPECTED_SEVERITIES
        ]
        coverage = check_critic_coverage._compute_coverage(rules)
        assert all(c.effective_rules > 0 for c in coverage)

    def test_gap_detected(self) -> None:
        rules = [
            check_critic_coverage.CritiqueRuleInfo(
                rule_id="test.major",
                class_name="RuleMajor",
                file_path="test.py",
                severity="major",
                role="melody",
            )
        ]
        coverage = check_critic_coverage._compute_coverage(rules)
        gaps = [c for c in coverage if c.effective_rules == 0]
        # critical, minor, suggestion should be gaps
        assert len(gaps) == 3

    def test_early_return_reduces_effective(self) -> None:
        rules = [
            check_critic_coverage.CritiqueRuleInfo(
                rule_id="test.critical",
                class_name="RuleCritical",
                file_path="test.py",
                severity="critical",
                role="melody",
                has_early_return_on_empty=True,
            )
        ]
        coverage = check_critic_coverage._compute_coverage(rules)
        critical = next(c for c in coverage if c.severity == "critical")
        assert critical.rule_count == 1
        assert critical.effective_rules == 0


class TestMainExitCode:
    """Tests for main()."""

    def test_returns_zero_non_strict_with_gaps(self, tmp_path: Path) -> None:
        critique_dir = tmp_path / "src" / "yao" / "verify" / "critique"
        critique_dir.mkdir(parents=True)
        (critique_dir / "test_rule.py").write_text("""
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Severity, Role

class OnlyMajorRule(CritiqueRule):
    rule_id = "test.only_major"
    severity = Severity.MAJOR
    role = Role.MELODY

    def detect(self, plan, spec):
        return []
""")
        with (
            patch.object(check_critic_coverage, "REPO_ROOT", tmp_path),
            patch.object(check_critic_coverage, "CRITIQUE_DIR", critique_dir),
            patch.object(sys, "argv", ["check_critic_coverage.py"]),
        ):
            result = check_critic_coverage.main()
        assert result == 0  # non-strict
