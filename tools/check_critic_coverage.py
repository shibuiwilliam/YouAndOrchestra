#!/usr/bin/env python3
"""Critic Coverage Check — verify critique rules produce meaningful detections.

Inspects src/yao/verify/critique/ to enumerate rules by Severity,
then verifies that each severity level has at least one rule capable
of producing findings on non-empty plans.

Wave 1.1 completion requirement: all severity levels covered.
Before Wave 1.1: WARN only (exit 0). After: exit 1 on failure.

Usage:
    python tools/check_critic_coverage.py [--json] [--strict]
    make critic-coverage
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CRITIQUE_DIR = REPO_ROOT / "src" / "yao" / "verify" / "critique"

# Expected severity levels from types.py
EXPECTED_SEVERITIES = ["critical", "major", "minor", "suggestion"]


@dataclass
class CritiqueRuleInfo:
    """Information about a detected critique rule."""

    rule_id: str
    class_name: str
    file_path: str
    severity: str | None = None
    role: str | None = None
    has_early_return_on_empty: bool = False


@dataclass
class CoverageSummary:
    """Coverage summary per severity level."""

    severity: str
    rule_count: int = 0
    rules_with_early_return: int = 0
    effective_rules: int = 0


class CritiqueRuleVisitor(ast.NodeVisitor):
    """AST visitor to extract critique rule metadata."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.rules: list[CritiqueRuleInfo] = []
        self._current_class: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        # Check if this class inherits from CritiqueRule
        is_rule = any(
            (isinstance(base, ast.Name) and base.id == "CritiqueRule")
            or (isinstance(base, ast.Attribute) and base.attr == "CritiqueRule")
            for base in node.bases
        )
        if not is_rule:
            self.generic_visit(node)
            return

        self._current_class = node.name
        rule_id = None
        severity = None
        role = None
        has_early_return = False

        # Extract class-level attributes
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "rule_id" and isinstance(item.value, ast.Constant):
                            rule_id = item.value.value
                        elif target.id == "severity" and isinstance(item.value, ast.Attribute):
                            severity = item.value.attr.lower()
                        elif target.id == "role" and isinstance(item.value, ast.Attribute):
                            role = item.value.attr.lower()

            # Check detect() method for severity used in Finding() and early returns
            if isinstance(item, ast.FunctionDef) and item.name == "detect":
                has_early_return = self._check_early_return_on_empty(item)
                # If severity not at class level, scan detect() for Finding severities
                if severity is None:
                    severity = self._extract_finding_severity(item)

        if rule_id:
            self.rules.append(
                CritiqueRuleInfo(
                    rule_id=rule_id,
                    class_name=node.name,
                    file_path=str(self.file_path.relative_to(REPO_ROOT)),
                    severity=severity,
                    role=role,
                    has_early_return_on_empty=has_early_return,
                )
            )

        self._current_class = None
        self.generic_visit(node)

    def _extract_finding_severity(self, func: ast.FunctionDef) -> str | None:
        """Extract severity from Finding() calls within detect() method."""
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Finding":
                for kw in node.keywords:
                    if kw.arg == "severity" and isinstance(kw.value, ast.Attribute):
                        return kw.value.attr.lower()
                # Also check positional: Finding(rule_id, severity, ...)
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Attribute):
                    return node.args[1].attr.lower()
        return None

    def _check_early_return_on_empty(self, func: ast.FunctionDef) -> bool:
        """Check if detect() returns early when plan fields are empty."""
        for node in ast.walk(func):
            if isinstance(node, ast.If):
                # Look for patterns like "if not plan.motif.seeds:" or "if not seeds:"
                test_src = ast.dump(node.test)
                if "seeds" in test_src or "empty" in test_src.lower():
                    # Check if the body is a return []
                    for stmt in node.body:
                        if isinstance(stmt, ast.Return):
                            return True
        return False


def _scan_critique_rules() -> list[CritiqueRuleInfo]:
    """Scan all critique rule files and extract rule metadata."""
    all_rules: list[CritiqueRuleInfo] = []

    if not CRITIQUE_DIR.exists():
        return all_rules

    for py_file in sorted(CRITIQUE_DIR.glob("*.py")):
        if py_file.name in ("__init__.py", "types.py", "base.py", "registry.py"):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            visitor = CritiqueRuleVisitor(py_file)
            visitor.visit(tree)
            all_rules.extend(visitor.rules)
        except (SyntaxError, UnicodeDecodeError):
            continue

    return all_rules


def _compute_coverage(rules: list[CritiqueRuleInfo]) -> list[CoverageSummary]:
    """Compute coverage summary per severity level."""
    summaries: list[CoverageSummary] = []
    for sev in EXPECTED_SEVERITIES:
        sev_rules = [r for r in rules if r.severity == sev]
        early_return_count = sum(1 for r in sev_rules if r.has_early_return_on_empty)
        summaries.append(
            CoverageSummary(
                severity=sev,
                rule_count=len(sev_rules),
                rules_with_early_return=early_return_count,
                effective_rules=len(sev_rules) - early_return_count,
            )
        )
    return summaries


def main() -> int:
    """Run critic coverage analysis.

    Returns:
        0 if all severity levels have effective rules (or --strict not set), 1 if gaps.
    """
    json_mode = "--json" in sys.argv
    strict = "--strict" in sys.argv

    rules = _scan_critique_rules()
    coverage = _compute_coverage(rules)
    gaps = [c for c in coverage if c.effective_rules == 0]

    if json_mode:
        output = {
            "tool": "critic-coverage",
            "total_rules": len(rules),
            "severity_coverage": [
                {
                    "severity": c.severity,
                    "total_rules": c.rule_count,
                    "early_return_on_empty": c.rules_with_early_return,
                    "effective_rules": c.effective_rules,
                    "covered": c.effective_rules > 0,
                }
                for c in coverage
            ],
            "uncovered_severities": [c.severity for c in gaps],
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "class": r.class_name,
                    "file": r.file_path,
                    "severity": r.severity,
                    "role": r.role,
                    "early_return_on_empty": r.has_early_return_on_empty,
                }
                for r in rules
            ],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("YaO Critic Coverage Check (v3.0)")
        print("=" * 60)
        print()
        print(f"Critique directory: {CRITIQUE_DIR.relative_to(REPO_ROOT)}")
        print(f"Total rules found: {len(rules)}")
        print()

        print("Coverage by severity:")
        print("-" * 40)
        for c in coverage:
            status = "OK" if c.effective_rules > 0 else "GAP"
            print(
                f"  [{status}] {c.severity}: {c.rule_count} rules "
                f"({c.rules_with_early_return} with early-return-on-empty, "
                f"{c.effective_rules} effective)"
            )
        print()

        if rules:
            print("All rules:")
            print("-" * 40)
            for r in rules:
                early = " [SILENT ON EMPTY]" if r.has_early_return_on_empty else ""
                print(f"  {r.rule_id} ({r.severity}/{r.role}) — {r.class_name}{early}")
            print()

        print("=" * 60)
        print(
            f"Rules: {len(rules)} | Severities covered: "
            f"{len(EXPECTED_SEVERITIES) - len(gaps)}/{len(EXPECTED_SEVERITIES)}"
        )
        print("=" * 60)

    if gaps:
        if strict:
            if not json_mode:
                print()
                print(f"FAIL: Severity levels without effective coverage: {', '.join(c.severity for c in gaps)}")
                print("Action: Ensure rules produce findings on non-empty plans.")
            return 1
        else:
            if not json_mode:
                print()
                print("WARN: Coverage gaps detected (not strict, exit 0).")
                print("This will become a hard failure after Wave 1.1.")
            return 0

    if not json_mode:
        print()
        print("OK: All severity levels have effective critique rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
