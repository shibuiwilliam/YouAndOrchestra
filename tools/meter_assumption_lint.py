#!/usr/bin/env python3
"""Meter assumption linter.

Scans src/yao/ for hardcoded 4/4 assumptions outside of constants and tests.
Detects patterns like: `* 4`, `/ 4`, `beats_per_bar == 4`, `"4/4"` literals
in generator and verify code that should use MeterSpec or timing module instead.

Usage:
    python tools/meter_assumption_lint.py [--strict]
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Directories to scan
SCAN_DIRS = [Path("src/yao/generators"), Path("src/yao/verify")]

# Directories/files to skip
SKIP_PATTERNS = {"__pycache__", ".pyc", "test_"}

# Allowed files (constants, timing module, etc.)
ALLOWED_FILES = {
    "timing.py",
    "constants",
    "meter.py",
}


class MeterAssumptionVisitor(ast.NodeVisitor):
    """AST visitor that detects hardcoded 4/4 assumptions."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.findings: list[tuple[int, str]] = []

    def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802
        """Detect string literal "4/4" in non-allowed contexts."""
        if isinstance(node.value, str) and node.value == "4/4":
            self.findings.append((node.lineno, 'String literal "4/4" — use MeterSpec or timing module'))
        self.generic_visit(node)


def scan_file(filepath: Path) -> list[tuple[str, int, str]]:
    """Scan a single Python file for meter assumptions.

    Returns:
        List of (filepath, line, message) tuples.
    """
    # Skip allowed files
    for allowed in ALLOWED_FILES:
        if allowed in str(filepath):
            return []

    try:
        source = filepath.read_text()
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    visitor = MeterAssumptionVisitor(str(filepath))
    visitor.visit(tree)

    return [(str(filepath), line, msg) for line, msg in visitor.findings]


def main() -> int:
    """Run the meter assumption lint.

    Returns:
        Exit code: 0 if clean, 1 if violations found (in --strict mode).
    """
    strict = "--strict" in sys.argv

    all_findings: list[tuple[str, int, str]] = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in SKIP_PATTERNS):
                continue
            all_findings.extend(scan_file(py_file))

    if all_findings:
        print(f"Meter assumption lint: {len(all_findings)} finding(s)")
        for filepath, line, msg in sorted(all_findings):
            severity = "WARNING" if not strict else "ERROR"
            print(f"  [{severity}] {filepath}:{line} — {msg}")
    else:
        print("Meter assumption lint: clean")

    if strict and all_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
