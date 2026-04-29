#!/usr/bin/env python3
"""Architecture lint — enforces YaO's 7-layer boundary rules.

This script uses AST parsing to check import statements without executing code.
It enforces two rules:

1. Layer boundary: lower layers cannot import from upper layers.
2. Library restriction: pretty_midi, music21, librosa can only be imported
   in ir/, render/, verify/.

Run via: python tools/architecture_lint.py
Exit code: 0 if clean, 1 if violations found.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Layer numbers — lower layers cannot import upper layers.
#
# Design note: IR data types (Note, ScoreIR) and provenance types are
# foundational — all layers produce/consume them. They are placed at
# layer 1 alongside schema. The "Layer 3" designation in PROJECT.md refers
# to IR *processing* capabilities (analysis, complex transformations), not
# the data types themselves. Similarly, provenance recording is a
# cross-cutting concern that all layers must participate in.
LAYER_MAP: dict[str, int] = {
    "constants": 0,  # available to all layers
    "schema": 1,
    "ir": 1,         # IR data types are shared across all layers
    "reflect": 1,    # provenance types are cross-cutting
    "generators": 2,
    "perception": 4,
    "render": 5,
    "verify": 6,
    "conductor": 7,  # orchestrator: can import all layers (like cli)
}

# These libraries can only be imported in specific modules
RESTRICTED_LIBRARIES: dict[str, set[str]] = {
    "pretty_midi": {"ir", "render"},
    "music21": {"ir", "verify"},
    "librosa": {"verify"},
}

SRC_DIR = Path("src/yao")


def get_module_layer(filepath: Path) -> str | None:
    """Determine which layer a file belongs to based on its path."""
    rel = filepath.relative_to(SRC_DIR)
    parts = rel.parts
    if len(parts) < 2:  # noqa: PLR2004
        return None  # top-level files (errors.py, types.py)
    return parts[0]


def get_layer_number(layer_name: str) -> int:
    """Get the layer number for a given module name."""
    return LAYER_MAP.get(layer_name, -1)


def extract_imports(tree: ast.AST) -> list[tuple[str, int]]:
    """Extract all import targets and their line numbers from an AST."""
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))
    return imports


def check_file(filepath: Path) -> list[str]:
    """Check a single Python file for architecture violations."""
    violations: list[str] = []

    try:
        source = filepath.read_text()
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return [f"{filepath}: SyntaxError — cannot parse"]

    source_layer = get_module_layer(filepath)
    if source_layer is None:
        return []  # top-level files don't have layer restrictions

    source_layer_num = get_layer_number(source_layer)
    imports = extract_imports(tree)

    for import_name, lineno in imports:
        # Check layer boundary violations
        if import_name.startswith("yao."):
            parts = import_name.split(".")
            if len(parts) >= 2:  # noqa: PLR2004
                target_module = parts[1]
                target_layer_num = get_layer_number(target_module)

                if target_layer_num > source_layer_num and source_layer_num >= 0:
                    violations.append(
                        f"{filepath}:{lineno}: Layer violation — "
                        f"{source_layer} (L{source_layer_num}) imports "
                        f"{target_module} (L{target_layer_num})"
                    )

        # Check restricted library imports
        top_level_import = import_name.split(".")[0]
        if top_level_import in RESTRICTED_LIBRARIES:
            allowed_layers = RESTRICTED_LIBRARIES[top_level_import]
            if source_layer not in allowed_layers:
                violations.append(
                    f"{filepath}:{lineno}: Library restriction — "
                    f"'{top_level_import}' cannot be imported in "
                    f"{source_layer}/ (allowed: {', '.join(sorted(allowed_layers))})"
                )

    return violations


def main() -> int:
    """Run architecture lint on all Python files under src/yao/."""
    if not SRC_DIR.exists():
        print(f"Source directory not found: {SRC_DIR}")
        return 1

    all_violations: list[str] = []
    py_files = sorted(SRC_DIR.rglob("*.py"))

    for filepath in py_files:
        violations = check_file(filepath)
        all_violations.extend(violations)

    if all_violations:
        print(f"Architecture lint: {len(all_violations)} violation(s) found\n")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print(f"Architecture lint: OK ({len(py_files)} files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
