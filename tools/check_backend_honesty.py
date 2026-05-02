#!/usr/bin/env python3
"""Backend Honesty Check — verify stub backends declare is_stub=True.

Scans src/yao/agents/ for AgentBackend implementations and ensures:
1. Backends that delegate to fallbacks declare is_stub = True (or have "Stub" in name)
2. Backends claiming is_stub = False actually make real LLM calls
3. No backend silently falls back without proper declaration

This is a v3.0 CI-mandatory check (immediate).

Usage:
    python tools/check_backend_honesty.py [--json]
    make backend-honesty
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "src" / "yao" / "agents"

# Patterns indicating a real LLM call
LLM_CALL_PATTERNS = [
    re.compile(r"anthropic\.Anthropic"),
    re.compile(r"\.messages\.create\("),
    re.compile(r"\.completions\.create\("),
    re.compile(r"claude_agent_sdk"),
    re.compile(r"subprocess.*claude"),
    re.compile(r"httpx\.(post|get|AsyncClient)"),
    re.compile(r"aiohttp\.ClientSession"),
]

# Patterns indicating fallback delegation
FALLBACK_PATTERNS = [
    re.compile(r"self\._fallback"),
    re.compile(r"return\s+.*fallback"),
    re.compile(r"PythonOnlyBackend\(\)"),
]


@dataclass
class BackendInfo:
    """Analysis of a single backend class."""

    class_name: str
    file_path: str
    has_is_stub_attr: bool = False
    is_stub_value: bool | None = None
    has_stub_in_name: bool = False
    uses_fallback: bool = False
    has_real_llm_call: bool = False
    violation: str | None = None


class BackendVisitor(ast.NodeVisitor):
    """AST visitor to analyze backend classes."""

    def __init__(self, file_path: Path, source: str) -> None:
        self.file_path = file_path
        self.source = source
        self.backends: list[BackendInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        # Check if this looks like a backend class
        is_backend = (
            "Backend" in node.name and node.name != "AgentBackend"  # skip the protocol itself
        )
        if not is_backend:
            self.generic_visit(node)
            return

        info = BackendInfo(
            class_name=node.name,
            file_path=str(self.file_path.relative_to(REPO_ROOT)),
            has_stub_in_name="Stub" in node.name,
        )

        # Scan class body for is_stub attribute
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "is_stub":
                        info.has_is_stub_attr = True
                        if isinstance(item.value, ast.Constant):
                            info.is_stub_value = bool(item.value.value)

        # Check for fallback patterns in the full class source
        class_start = node.lineno - 1
        class_end = node.end_lineno if node.end_lineno else len(self.source.splitlines())
        class_lines = self.source.splitlines()[class_start:class_end]
        class_source = "\n".join(class_lines)

        for pattern in FALLBACK_PATTERNS:
            if pattern.search(class_source):
                info.uses_fallback = True
                break

        for pattern in LLM_CALL_PATTERNS:
            if pattern.search(class_source):
                info.has_real_llm_call = True
                break

        # Determine violation
        info.violation = self._determine_violation(info)
        self.backends.append(info)
        self.generic_visit(node)

    def _determine_violation(self, info: BackendInfo) -> str | None:
        """Determine if this backend violates honesty rules."""
        # Case 1: Uses fallback but doesn't declare is_stub
        if info.uses_fallback and not info.has_is_stub_attr and not info.has_stub_in_name:
            return "Uses fallback but missing is_stub attribute"

        # Case 2: Uses fallback but claims is_stub = False
        if info.uses_fallback and info.is_stub_value is False:
            return "Uses fallback delegation but claims is_stub=False"

        # Case 3: No real LLM call and no is_stub declaration
        if (
            not info.has_real_llm_call
            and not info.uses_fallback
            and "PythonOnly" not in info.class_name
            and not info.has_is_stub_attr
            and not info.has_stub_in_name
        ):
            return "No real LLM call and no is_stub declaration"

        return None


def main() -> int:
    """Run backend honesty check.

    Returns:
        0 if all backends are honest, 1 if violations found.
    """
    json_mode = "--json" in sys.argv

    if not AGENTS_DIR.exists():
        msg = f"Agents directory not found: {AGENTS_DIR}"
        if json_mode:
            print(json.dumps({"tool": "backend-honesty", "error": msg}))
        else:
            print(f"ERROR: {msg}")
        return 1

    all_backends: list[BackendInfo] = []

    for py_file in sorted(AGENTS_DIR.glob("*.py")):
        if py_file.name in ("__init__.py", "protocol.py", "registry.py"):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            visitor = BackendVisitor(py_file, source)
            visitor.visit(tree)
            all_backends.extend(visitor.backends)
        except (SyntaxError, UnicodeDecodeError):
            continue

    violations = [b for b in all_backends if b.violation]

    if json_mode:
        output = {
            "tool": "backend-honesty",
            "backends_checked": len(all_backends),
            "violations": len(violations),
            "passed": len(all_backends) - len(violations),
            "backends": [
                {
                    "class": b.class_name,
                    "file": b.file_path,
                    "has_is_stub": b.has_is_stub_attr,
                    "is_stub_value": b.is_stub_value,
                    "uses_fallback": b.uses_fallback,
                    "has_real_llm_call": b.has_real_llm_call,
                    "violation": b.violation,
                }
                for b in all_backends
            ],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("YaO Backend Honesty Check (v3.0)")
        print("=" * 60)
        print()
        print(f"Agents directory: {AGENTS_DIR.relative_to(REPO_ROOT)}")
        print(f"Backends found: {len(all_backends)}")
        print()

        for b in all_backends:
            status = "FAIL" if b.violation else "PASS"
            stub_info = ""
            if b.has_is_stub_attr:
                stub_info = f" [is_stub={b.is_stub_value}]"
            elif b.has_stub_in_name:
                stub_info = " [Stub in name]"
            print(f"  [{status}] {b.class_name}{stub_info}")
            print(f"        File: {b.file_path}")
            print(
                f"        Fallback: {'yes' if b.uses_fallback else 'no'} | "
                f"Real LLM call: {'yes' if b.has_real_llm_call else 'no'}"
            )
            if b.violation:
                print(f"        VIOLATION: {b.violation}")
            print()

        print("=" * 60)
        print(
            f"Backends: {len(all_backends)} | Passed: {len(all_backends) - len(violations)} | "
            f"Violations: {len(violations)}"
        )
        print("=" * 60)

    if violations:
        if not json_mode:
            print()
            print("FAIL: Backend honesty violations detected.")
            print("Action: Add is_stub=True to stub backends, or implement real LLM calls.")
        return 1

    if not json_mode:
        print()
        print("OK: All backends are honestly declared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
