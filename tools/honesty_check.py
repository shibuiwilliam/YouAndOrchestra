#!/usr/bin/env python3
"""Honesty Check — verify ✅ features are not stubs.

Goes beyond feature_status_check.py (which only checks file existence)
by inspecting actual code content for stub indicators:
- Classes/functions that delegate entirely to a fallback
- Empty data structures returned unconditionally
- "stub", "not yet implemented", "Phase α" in comments/docstrings
- is_stub attribute absence on backend classes
- Zero references from src/ for skill files

This is a v3.0 CI-mandatory check. Exit code 1 if any ✅ feature
is identified as a stub without proper limitation: annotation.

Usage:
    python tools/honesty_check.py [--json]
    make honesty-check
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "FEATURE_STATUS.md"

# Feature name → FEATURE_STATUS.md feature key mapping
# Used to cross-reference with the markdown file's status column
_FEATURE_STATUS_KEYS: dict[str, list[str]] = {
    "7 Subagent Python implementations": ["7 Subagent Python implementations"],
    "Backend-Agnostic Agent Protocol (AnthropicAPI)": ["Backend-Agnostic Agent Protocol"],
    "Backend-Agnostic Agent Protocol (ClaudeCode)": ["Backend-Agnostic Agent Protocol"],
    "SpecCompiler (NL → spec)": ["SpecCompiler (NL → spec)"],
    "Genre Skills (22)": ["Genre Skills (22)"],
    "NoteRealizer (V2 pipeline)": ["rule_based generator", "stochastic generator"],
    "DAW MCP integration": ["DAW MCP integration"],
}


def _parse_feature_statuses(path: Path) -> dict[str, str]:
    """Parse FEATURE_STATUS.md and return feature name → status emoji mapping."""
    if not path.exists():
        return {}
    statuses: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) < 2 or cells[0] in ("Feature", "Status"):  # noqa: PLR2004
            continue
        if all(re.match(r"^-+$", c) for c in cells):
            continue
        feature = cells[0].strip()
        status_raw = cells[1].strip()
        for emoji in ("✅", "🟢", "🟡", "⚪", "🔴"):
            if emoji in status_raw:
                statuses[feature] = emoji
                break
    return statuses


def _is_feature_stable(feature_name: str, statuses: dict[str, str]) -> bool:
    """Check if a feature is marked ✅ in FEATURE_STATUS.md."""
    keys = _FEATURE_STATUS_KEYS.get(feature_name, [feature_name])
    return any(statuses.get(k) == "✅" for k in keys)


# Patterns that indicate stub implementations
STUB_INDICATORS = [
    re.compile(r"\bstub\b", re.IGNORECASE),
    re.compile(r"\bnot yet implemented\b", re.IGNORECASE),
    re.compile(r"\bPhase [αβγδ]\b"),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bfallback\b.*\bnot.*implemented\b", re.IGNORECASE),
]

# Patterns that indicate silent fallback delegation
FALLBACK_PATTERNS = [
    re.compile(r"self\._fallback\.invoke\("),
    re.compile(r"return\s+self\._fallback\b"),
]


@dataclass
class HonestyFinding:
    """A honesty violation found during the check."""

    feature: str
    file_path: str
    line: int
    indicator: str
    severity: str  # "error" or "warning"

    def __str__(self) -> str:
        return f"  [{self.severity.upper()}] {self.feature}\n    {self.file_path}:{self.line} — {self.indicator}"


@dataclass
class HonestyCheckResult:
    """Aggregated result of the honesty check."""

    findings: list[HonestyFinding] = field(default_factory=list)
    checked: int = 0
    passed: int = 0

    @property
    def failed(self) -> int:
        return len([f for f in self.findings if f.severity == "error"])


# ── Check definitions ──────────────────────────────────────────────────
# Each check targets a specific ✅ feature and inspects the actual code.


def check_composer_subagent(result: HonestyCheckResult) -> None:
    """Check that ComposerSubagent returns non-empty MotifPlan."""
    result.checked += 1
    path = REPO_ROOT / "src" / "yao" / "subagents" / "composer.py"
    if not path.exists():
        result.findings.append(HonestyFinding("Composer Subagent", str(path), 0, "File not found", "error"))
        return

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    # Check for empty MotifPlan construction
    for i, line in enumerate(lines, 1):
        if "MotifPlan(seeds=[]" in line or "MotifPlan(seeds = []" in line:
            result.findings.append(
                HonestyFinding(
                    "7 Subagent Python implementations",
                    str(path.relative_to(REPO_ROOT)),
                    i,
                    "Composer returns empty MotifPlan(seeds=[])",
                    "error",
                )
            )
            return

    # Check for stub indicators in comments/docstrings
    _check_stub_indicators(source, lines, path, "7 Subagent Python implementations", result)

    if not any(f.feature == "7 Subagent Python implementations" for f in result.findings):
        result.passed += 1


def check_anthropic_backend(result: HonestyCheckResult) -> None:
    """Check that AnthropicAPIBackend is not a stub."""
    result.checked += 1
    path = REPO_ROOT / "src" / "yao" / "agents" / "anthropic_api_backend.py"
    if not path.exists():
        result.findings.append(
            HonestyFinding("Backend-Agnostic Agent Protocol", str(path), 0, "File not found", "error")
        )
        return

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    # Check for fallback delegation
    for i, line in enumerate(lines, 1):
        for pattern in FALLBACK_PATTERNS:
            if pattern.search(line):
                result.findings.append(
                    HonestyFinding(
                        "Backend-Agnostic Agent Protocol (AnthropicAPI)",
                        str(path.relative_to(REPO_ROOT)),
                        i,
                        "Silent fallback to PythonOnlyBackend",
                        "error",
                    )
                )
                return

    # Check for is_stub attribute
    if "is_stub" not in source:
        result.findings.append(
            HonestyFinding(
                "Backend-Agnostic Agent Protocol (AnthropicAPI)",
                str(path.relative_to(REPO_ROOT)),
                0,
                "Missing is_stub attribute (required by principle 7)",
                "warning",
            )
        )
        return

    result.passed += 1


def check_claude_code_backend(result: HonestyCheckResult) -> None:
    """Check that ClaudeCodeBackend is not a stub."""
    result.checked += 1
    path = REPO_ROOT / "src" / "yao" / "agents" / "claude_code_backend.py"
    if not path.exists():
        result.findings.append(
            HonestyFinding("Backend-Agnostic Agent Protocol", str(path), 0, "File not found", "error")
        )
        return

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    for i, line in enumerate(lines, 1):
        for pattern in FALLBACK_PATTERNS:
            if pattern.search(line):
                result.findings.append(
                    HonestyFinding(
                        "Backend-Agnostic Agent Protocol (ClaudeCode)",
                        str(path.relative_to(REPO_ROOT)),
                        i,
                        "Silent fallback to PythonOnlyBackend",
                        "error",
                    )
                )
                return

    if "is_stub" not in source:
        result.findings.append(
            HonestyFinding(
                "Backend-Agnostic Agent Protocol (ClaudeCode)",
                str(path.relative_to(REPO_ROOT)),
                0,
                "Missing is_stub attribute (required by principle 7)",
                "warning",
            )
        )
        return

    result.passed += 1


def check_spec_compiler(result: HonestyCheckResult) -> None:
    """Check that SpecCompiler has LLM integration and Japanese support."""
    result.checked += 1
    path = REPO_ROOT / "src" / "yao" / "sketch" / "compiler.py"
    if not path.exists():
        result.findings.append(HonestyFinding("SpecCompiler (NL → spec)", str(path), 0, "File not found", "error"))
        return

    source = path.read_text(encoding="utf-8")

    # Check for Japanese keyword support
    has_japanese = any(
        ord(c) > 0x3000
        for c in source  # CJK character range
    )

    if not has_japanese:
        result.findings.append(
            HonestyFinding(
                "SpecCompiler (NL → spec)",
                str(path.relative_to(REPO_ROOT)),
                0,
                "No Japanese language support (zero CJK characters in source)",
                "warning",
            )
        )

    # Count mood keywords
    mood_matches = re.findall(r'"(\w+)":\s*"[A-G]', source)
    if len(mood_matches) < 30:  # noqa: PLR2004
        result.findings.append(
            HonestyFinding(
                "SpecCompiler (NL → spec)",
                str(path.relative_to(REPO_ROOT)),
                0,
                f"Only {len(mood_matches)} mood keywords (keyword-only, no LLM integration)",
                "warning",
            )
        )

    if not any(f.feature == "SpecCompiler (NL → spec)" for f in result.findings):
        result.passed += 1


def check_genre_skills_integration(result: HonestyCheckResult) -> None:
    """Check that genre skills are referenced from src/."""
    result.checked += 1
    src_dir = REPO_ROOT / "src"
    skills_dir = REPO_ROOT / ".claude" / "skills" / "genres"

    if not skills_dir.exists():
        result.findings.append(
            HonestyFinding("Genre Skills (22)", str(skills_dir), 0, "Skills directory not found", "error")
        )
        return

    skill_count = len(list(skills_dir.rglob("*.md")))

    # Search for any reference to skills/genres in src/
    references_found = 0
    for py_file in src_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "skills/genres" in content or "skills_dir" in content or "SkillRegistry" in content:
            references_found += 1

    if references_found == 0:
        result.findings.append(
            HonestyFinding(
                "Genre Skills (22)",
                str(skills_dir.relative_to(REPO_ROOT)),
                0,
                f"{skill_count} skill files exist but 0 references from src/ (not integrated into pipeline)",
                "error",
            )
        )
        return

    result.passed += 1


def check_note_realizer_plan_consumption(result: HonestyCheckResult) -> None:
    """Check that NoteRealizers consume MusicalPlan, not just convert to v1."""
    result.checked += 1
    path = REPO_ROOT / "src" / "yao" / "generators" / "note" / "rule_based.py"
    if not path.exists():
        result.findings.append(HonestyFinding("rule_based generator", str(path), 0, "File not found", "error"))
        return

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    for i, line in enumerate(lines, 1):
        if "_plan_to_v1_spec" in line and "def _plan_to_v1_spec" not in line:
            result.findings.append(
                HonestyFinding(
                    "NoteRealizer (V2 pipeline)",
                    str(path.relative_to(REPO_ROOT)),
                    i,
                    "NoteRealizer converts MusicalPlan to v1 spec instead of consuming it directly",
                    "warning",
                )
            )
            return

    result.passed += 1


def check_daw_mcp(result: HonestyCheckResult) -> None:
    """Check that DAW MCP bridge is not a stub."""
    result.checked += 1
    path = REPO_ROOT / "src" / "yao" / "render" / "daw" / "mcp_bridge.py"
    if not path.exists():
        result.findings.append(HonestyFinding("DAW MCP integration", str(path), 0, "File not found", "error"))
        return

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()

    _check_stub_indicators(source, lines, path, "DAW MCP integration", result)

    # Check for always-disconnected pattern
    for i, line in enumerate(lines, 1):
        if "connected=False" in line and "Stub" not in line:
            result.findings.append(
                HonestyFinding(
                    "DAW MCP integration",
                    str(path.relative_to(REPO_ROOT)),
                    i,
                    "MCP bridge always returns disconnected (stub)",
                    "error",
                )
            )
            return

    if not any(f.feature == "DAW MCP integration" for f in result.findings):
        result.passed += 1


# ── Helpers ────────────────────────────────────────────────────────────


def _check_stub_indicators(
    source: str,
    lines: list[str],
    path: Path,
    feature: str,
    result: HonestyCheckResult,
) -> None:
    """Scan source for stub indicator patterns."""
    for i, line in enumerate(lines, 1):
        # Skip import lines
        if line.strip().startswith(("import ", "from ")):
            continue
        for pattern in STUB_INDICATORS:
            if pattern.search(line):
                result.findings.append(
                    HonestyFinding(
                        feature,
                        str(path.relative_to(REPO_ROOT)),
                        i,
                        f"Stub indicator found: {line.strip()[:80]}",
                        "warning",
                    )
                )
                return


# ── Main ───────────────────────────────────────────────────────────────


ALL_CHECKS = [
    check_composer_subagent,
    check_anthropic_backend,
    check_claude_code_backend,
    check_spec_compiler,
    check_genre_skills_integration,
    check_note_realizer_plan_consumption,
    check_daw_mcp,
]


def main() -> int:
    """Run the honesty check.

    Checks all known stub-risk features. Severity depends on FEATURE_STATUS.md:
    - If a feature is ✅ and the code is a stub → ERROR (exit 1)
    - If a feature is 🟡 and the code is a stub → INFO (expected, acknowledged)
    - Warnings are always informational

    Returns:
        0 if no ✅ features are stubs, 1 if any ✅ feature is a stub.
    """
    json_mode = "--json" in sys.argv

    result = HonestyCheckResult()
    statuses = _parse_feature_statuses(STATUS_FILE)

    if not json_mode:
        print("=" * 60)
        print("YaO Honesty Check (v3.0)")
        print("=" * 60)
        print()

    for check_fn in ALL_CHECKS:
        check_fn(result)

    # Cross-reference with FEATURE_STATUS.md:
    # Downgrade errors to "info" for features already marked 🟡
    for finding in result.findings:
        if finding.severity == "error" and not _is_feature_stable(finding.feature, statuses):
            finding.severity = "info"

    errors = [f for f in result.findings if f.severity == "error"]
    warnings = [f for f in result.findings if f.severity == "warning"]
    infos = [f for f in result.findings if f.severity == "info"]

    if json_mode:
        output = {
            "tool": "honesty-check",
            "checked": result.checked,
            "passed": result.passed,
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "findings": [asdict(f) for f in result.findings],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 1 if errors else 0

    if errors:
        print(f"ERRORS ({len(errors)}) — ✅ features with stub code:")
        print("-" * 40)
        for f in errors:
            print(f)
            print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        print("-" * 40)
        for f in warnings:
            print(f)
            print()

    if infos:
        print(f"INFO ({len(infos)}) — acknowledged 🟡 stubs (not blocking):")
        print("-" * 40)
        for f in infos:
            print(f)
            print()

    print("=" * 60)
    print(
        f"Checked: {result.checked} | Passed: {result.passed} | "
        f"Errors: {len(errors)} | Warnings: {len(warnings)} | Info: {len(infos)}"
    )
    print("=" * 60)

    if errors:
        print()
        print("FAIL: ✅ features with stub implementations detected.")
        print("Action: Downgrade to 🟡 with limitation: or implement fully.")
        return 1

    if warnings:
        print()
        print("WARN: Some features have partial limitations noted above.")
        return 0

    print()
    print("OK: All ✅ features pass honesty check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
