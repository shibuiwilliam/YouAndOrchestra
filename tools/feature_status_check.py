#!/usr/bin/env python3
"""Verify FEATURE_STATUS.md matches actual code state.

Parses the feature status tables and checks that ✅ entries have
corresponding source and test files. Outputs warnings (exit 0)
for drift — the goal is to catch documentation drift early,
not to block development.

Usage:
    python tools/feature_status_check.py
    make feature-status
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "FEATURE_STATUS.md"
MAPPING_FILE = REPO_ROOT / "tools" / "feature_status_mapping.yaml"


@dataclass
class FeatureEntry:
    """A parsed row from a FEATURE_STATUS.md table."""

    area: str
    feature: str
    status: str
    tests: str
    notes: str


def parse_feature_status(path: Path) -> list[FeatureEntry]:
    """Extract feature entries from FEATURE_STATUS.md tables.

    Parses all markdown tables with columns: Feature | Status | Tests | Notes.
    Also handles 3-column tables (Feature | Status | Notes) in the
    "Not Yet Implemented" section.

    Args:
        path: Path to FEATURE_STATUS.md.

    Returns:
        List of FeatureEntry objects.
    """
    text = path.read_text(encoding="utf-8")
    entries: list[FeatureEntry] = []
    current_area = ""

    for line in text.splitlines():
        # Track area headings (## Spec / Input, ## Generation, etc.)
        heading_match = re.match(r"^## (.+)", line)
        if heading_match:
            current_area = heading_match.group(1).strip()
            continue

        # Skip non-table lines
        if not line.startswith("|"):
            continue

        # Skip header and separator rows
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]

        if not cells or len(cells) < 2:  # noqa: PLR2004
            continue

        # Skip separator rows (---|---|---|---)
        if all(re.match(r"^-+$", c) for c in cells):
            continue

        # Skip header rows
        if cells[0] in ("Feature", "Status", "Tests"):
            continue

        # Parse the row
        feature = cells[0].strip()
        status_raw = cells[1].strip() if len(cells) > 1 else ""

        # Extract status emoji
        status = ""
        for emoji in ("✅", "🟢", "🟡", "⚪", "🔴"):
            if emoji in status_raw:
                status = emoji
                break

        tests = cells[2].strip() if len(cells) > 2 else ""  # noqa: PLR2004
        notes = cells[3].strip() if len(cells) > 3 else ""  # noqa: PLR2004

        if feature and status:
            entries.append(
                FeatureEntry(
                    area=current_area,
                    feature=feature,
                    status=status,
                    tests=tests,
                    notes=notes,
                )
            )

    return entries


def load_mapping(path: Path) -> dict[str, dict[str, list[str]]]:
    """Load the feature → file path mapping from YAML.

    Args:
        path: Path to feature_status_mapping.yaml.

    Returns:
        Dict mapping feature name → {src: [...], tests: [...]}.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def check_paths_exist(paths: list[str], label: str) -> list[str]:
    """Check that all paths exist relative to repo root.

    Args:
        paths: List of relative paths.
        label: Label for error messages (e.g., "src", "test").

    Returns:
        List of warning messages for missing paths.
    """
    warnings: list[str] = []
    for p in paths:
        full = REPO_ROOT / p
        if not full.exists():
            warnings.append(f"    {label} missing: {p}")
    return warnings


def verify_entry(entry: FeatureEntry, mapping: dict[str, dict[str, list[str]]]) -> list[str]:
    """Return list of warnings for a single feature entry.

    Only ✅ entries are verified. Other statuses are informational.

    Args:
        entry: The feature entry to verify.
        mapping: The feature → file mapping.

    Returns:
        List of warning strings.
    """
    warnings: list[str] = []

    if entry.status != "✅":
        return warnings

    if entry.feature not in mapping:
        # ✅ but no mapping — can't verify
        return warnings

    files = mapping[entry.feature]

    # Check source files
    src_paths = files.get("src", [])
    if src_paths:
        warnings.extend(check_paths_exist(src_paths, "src"))

    # Check test files
    test_paths = files.get("tests", [])
    if test_paths:
        warnings.extend(check_paths_exist(test_paths, "test"))

    if warnings:
        warnings.insert(0, f"  {entry.feature}:")

    return warnings


def main() -> int:
    """Run the feature status consistency check.

    Returns:
        0 always (warning-level only).
    """
    if not STATUS_FILE.exists():
        print("ERROR: FEATURE_STATUS.md not found")
        return 1

    if not MAPPING_FILE.exists():
        print("ERROR: tools/feature_status_mapping.yaml not found")
        return 1

    entries = parse_feature_status(STATUS_FILE)
    mapping = load_mapping(MAPPING_FILE)

    if not entries:
        print("ERROR: No features parsed from FEATURE_STATUS.md")
        return 1

    stable_entries = [e for e in entries if e.status == "✅"]
    mapped_stable = [e for e in stable_entries if e.feature in mapping]
    unmapped_stable = [e for e in stable_entries if e.feature not in mapping]

    print(f"Parsed {len(entries)} features from FEATURE_STATUS.md")
    print(f"  ✅ Stable: {len(stable_entries)}")
    print(f"  🟢 Working: {sum(1 for e in entries if e.status == '🟢')}")
    print(f"  🟡 Partial: {sum(1 for e in entries if e.status == '🟡')}")
    print(f"  🔴 Gap: {sum(1 for e in entries if e.status == '🔴')}")
    print(f"  ⚪ Designed: {sum(1 for e in entries if e.status == '⚪')}")
    print()

    all_warnings: list[str] = []
    for entry in mapped_stable:
        all_warnings.extend(verify_entry(entry, mapping))

    if unmapped_stable:
        print(f"INFO: {len(unmapped_stable)} ✅ entries have no mapping (add to feature_status_mapping.yaml):")
        for e in unmapped_stable:
            print(f"  - {e.feature}")
        print()

    if all_warnings:
        print("WARNING: Feature status drift detected:")
        for w in all_warnings:
            print(w)
        print()

    print(f"Verified {len(mapped_stable)} ✅ entries against mapping")

    if not all_warnings:
        print("OK: All ✅ entries have matching source and test files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
