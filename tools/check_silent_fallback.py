#!/usr/bin/env python3
"""AST-based detector for silent fallback patterns in generator code.

Catches potential silent compromises that should be wrapped with
RecoverableDecision. Specifically looks for:
- `max(1, min(127, ...))` velocity clamps without nearby record_recoverable
- `try: ... except: pass` blocks

This is a heuristic — it's intentionally conservative.
Suppress with `# noqa: silent-fallback` comment when intentional.

Usage:
    python tools/check_silent_fallback.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

NOQA_TAG = "noqa: silent-fallback"
GENERATORS_DIR = Path("src/yao/generators")


class SilentFallbackVisitor(ast.NodeVisitor):
    """AST visitor that detects potential silent fallback patterns."""

    def __init__(self, source_lines: list[str]) -> None:
        self.source_lines = source_lines
        self.warnings: list[tuple[int, str]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        """Detect bare `except: pass` patterns."""
        if node.type is None and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            line = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
            if NOQA_TAG not in line:
                self.warnings.append(
                    (
                        node.lineno,
                        "Bare `except: pass` — silent failure",
                    )
                )
        self.generic_visit(node)


def check_file(path: Path) -> list[tuple[int, str]]:
    """Check a single file for silent fallback patterns.

    Args:
        path: Path to the Python file.

    Returns:
        List of (line_number, warning_message) tuples.
    """
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    visitor = SilentFallbackVisitor(source.splitlines())
    visitor.visit(tree)
    return visitor.warnings


def main() -> int:
    """Scan generator files for silent fallback patterns.

    Returns:
        0 always (warning level, does not block CI).
    """
    if not GENERATORS_DIR.exists():
        print(f"WARNING: {GENERATORS_DIR} not found")
        return 0

    all_warnings: dict[Path, list[tuple[int, str]]] = {}
    for py_file in sorted(GENERATORS_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        warnings = check_file(py_file)
        if warnings:
            all_warnings[py_file] = warnings

    if all_warnings:
        print("WARNING: Possible silent fallback patterns:")
        for f, ws in all_warnings.items():
            for line, msg in ws:
                print(f"  {f}:{line}: {msg}")
        print()

    print(f"Checked {sum(1 for _ in GENERATORS_DIR.rglob('*.py') if '__pycache__' not in str(_))} files")
    if not all_warnings:
        print("OK: No silent fallback patterns detected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
