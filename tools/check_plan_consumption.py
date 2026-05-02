#!/usr/bin/env python3
"""Plan Consumption Check — verify NoteRealizers consume MusicalPlan fields.

Uses AST analysis to determine which MusicalPlan attributes are actually
accessed by NoteRealizer implementations. Compares against declared
consumed_plan_fields and the total available fields.

Wave 1.4 completion requirement: 80% of major fields consumed.
Before Wave 1.4: WARN only (exit 0). After: exit 1 on failure.

Usage:
    python tools/check_plan_consumption.py [--json] [--strict]
    make plan-consumption
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Major fields of MusicalPlan that NoteRealizers should consume
MAJOR_PLAN_FIELDS = [
    "intent_normalized",
    "form",
    "harmony",
    "motifs_phrases",
    "arrangement",
    "drums",
    "trajectory",
]

# Sub-fields that count as consumption of the parent
FIELD_ACCESS_PATTERNS: dict[str, list[str]] = {
    "intent_normalized": ["intent_normalized", "intent"],
    "form": ["form", "song_form", "sections", "section_plan", "form_plan"],
    "harmony": ["harmony", "chord_events", "cadences", "modulations", "harmony_plan"],
    "motifs_phrases": ["motifs_phrases", "motif", "phrase", "seeds", "placements", "motif_plan", "phrase_plan"],
    "arrangement": ["arrangement", "layers", "counter_melody", "arrangement_plan"],
    "drums": ["drums", "drum_pattern", "drum"],
    "trajectory": ["trajectory", "tension", "density", "energy_curve", "target_tension", "target_density"],
}


@dataclass
class PlanConsumptionResult:
    """Result of plan consumption analysis for one realizer."""

    realizer_name: str
    file_path: str
    declared_fields: list[str] = field(default_factory=list)
    accessed_fields: list[str] = field(default_factory=list)
    consumed_ratio: float = 0.0
    uses_legacy_adapter: bool = False
    passed: bool = False


class PlanFieldVisitor(ast.NodeVisitor):
    """AST visitor that detects MusicalPlan attribute access patterns."""

    def __init__(self) -> None:
        self.accessed_attrs: set[str] = set()
        self.uses_plan_to_v1: bool = False

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        self.accessed_attrs.add(node.attr)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:  # noqa: N802
        if isinstance(node.value, ast.Attribute):
            self.accessed_attrs.add(node.value.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if (
            isinstance(node.func, ast.Name)
            and "_plan_to_v1_spec" in node.func.id
            or isinstance(node.func, ast.Attribute)
            and "_plan_to_v1_spec" in node.func.attr
        ):
            self.uses_plan_to_v1 = True
        self.generic_visit(node)


def _detect_consumed_fields(accessed_attrs: set[str]) -> list[str]:
    """Map raw attribute accesses to major plan fields."""
    consumed = []
    for major_field, patterns in FIELD_ACCESS_PATTERNS.items():
        if any(p in accessed_attrs for p in patterns):
            consumed.append(major_field)
    return consumed


def _get_declared_fields(tree: ast.Module) -> list[str]:
    """Extract consumed_plan_fields class attribute if declared."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "consumed_plan_fields"
                    and isinstance(node.value, ast.List | ast.Tuple)
                ):
                    return [
                        elt.value
                        for elt in node.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
    return []


def analyze_realizer(path: Path) -> PlanConsumptionResult:
    """Analyze a single NoteRealizer file for plan consumption."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    visitor = PlanFieldVisitor()
    visitor.visit(tree)

    declared = _get_declared_fields(tree)
    consumed = _detect_consumed_fields(visitor.accessed_attrs)
    ratio = len(consumed) / len(MAJOR_PLAN_FIELDS) if MAJOR_PLAN_FIELDS else 0.0

    # Get realizer class name
    realizer_name = path.stem
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and "Realizer" in node.name:
            realizer_name = node.name
            break

    return PlanConsumptionResult(
        realizer_name=realizer_name,
        file_path=str(path.relative_to(REPO_ROOT)),
        declared_fields=declared,
        accessed_fields=consumed,
        consumed_ratio=ratio,
        uses_legacy_adapter=visitor.uses_plan_to_v1,
        passed=ratio >= 0.8 and not visitor.uses_plan_to_v1,
    )


def main() -> int:
    """Run plan consumption analysis on all NoteRealizer implementations.

    Returns:
        0 if all realizers pass (or --strict not set), 1 if failures.
    """
    json_mode = "--json" in sys.argv
    strict = "--strict" in sys.argv

    note_dir = REPO_ROOT / "src" / "yao" / "generators" / "note"
    if not note_dir.exists():
        if json_mode:
            print(json.dumps({"tool": "plan-consumption", "error": "note/ directory not found"}))
        else:
            print("ERROR: src/yao/generators/note/ not found")
        return 1

    results: list[PlanConsumptionResult] = []
    for py_file in sorted(note_dir.glob("*.py")):
        if py_file.name in ("__init__.py", "base.py"):
            continue
        try:
            results.append(analyze_realizer(py_file))
        except SyntaxError as e:
            if not json_mode:
                print(f"  SKIP: {py_file.name} (syntax error: {e})")

    if json_mode:
        output = {
            "tool": "plan-consumption",
            "realizers_checked": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "results": [
                {
                    "realizer": r.realizer_name,
                    "file": r.file_path,
                    "consumed_ratio": round(r.consumed_ratio, 2),
                    "accessed_fields": r.accessed_fields,
                    "declared_fields": r.declared_fields,
                    "uses_legacy_adapter": r.uses_legacy_adapter,
                    "passed": r.passed,
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("YaO Plan Consumption Check (v3.0)")
        print("=" * 60)
        print()
        print(f"Major plan fields ({len(MAJOR_PLAN_FIELDS)}): {', '.join(MAJOR_PLAN_FIELDS)}")
        print("Required consumption: 80%")
        print()

        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  [{status}] {r.realizer_name} ({r.file_path})")
            print(
                f"        Consumed: {len(r.accessed_fields)}/{len(MAJOR_PLAN_FIELDS)} "
                f"({r.consumed_ratio:.0%}) — {', '.join(r.accessed_fields) or 'none'}"
            )
            if r.uses_legacy_adapter:
                print("        WARNING: Uses _plan_to_v1_spec (legacy adapter)")
            if r.declared_fields:
                print(f"        Declared: {', '.join(r.declared_fields)}")
            print()

        total_pass = sum(1 for r in results if r.passed)
        print("=" * 60)
        print(f"Realizers: {len(results)} | Passed: {total_pass} | Failed: {len(results) - total_pass}")
        print("=" * 60)

    failures = [r for r in results if not r.passed]
    if failures:
        if strict:
            if not json_mode:
                print()
                print("FAIL: NoteRealizers do not consume MusicalPlan adequately.")
                print("Action: Implement direct plan consumption (Wave 1.4).")
            return 1
        else:
            if not json_mode:
                print()
                print("WARN: Plan consumption below 80% (not strict mode, exit 0).")
                print("This will become a hard failure after Wave 1.4.")
            return 0

    if not json_mode:
        print()
        print("OK: All NoteRealizers consume MusicalPlan adequately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
