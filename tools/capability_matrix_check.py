#!/usr/bin/env python3
"""Capability Matrix consistency checker.

Parses PROJECT.md §4 Capability Matrix and verifies that every ✅ entry
has the corresponding source files and test files listed in
tools/capability_matrix_mapping.yaml.

Exit code 0 = all checks pass.
Exit code 1 = at least one inconsistency found.

Usage:
    python tools/capability_matrix_check.py
    make matrix-check
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_MD = REPO_ROOT / "PROJECT.md"
MAPPING_FILE = REPO_ROOT / "tools" / "capability_matrix_mapping.yaml"


def parse_matrix(project_md: Path) -> dict[str, str]:
    """Parse the Capability Matrix table from PROJECT.md.

    Returns a dict mapping feature name -> status emoji.
    Searches for the section containing "Capability Matrix" in heading.
    """
    text = project_md.read_text(encoding="utf-8")

    # Find the Capability Matrix section (may be §3, §4, etc.)
    section_match = re.search(
        r"^## \d+\. Capability Matrix.*?\n(.*?)(?=\n## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        print("ERROR: Could not find Capability Matrix section in PROJECT.md")
        sys.exit(1)

    section_text = section_match.group(1)

    # Parse markdown table rows: | Area | Feature | Status | ...
    # Skip header and separator rows
    features: dict[str, str] = {}
    table_pattern = re.compile(r"^\|(.+)\|$", re.MULTILINE)
    rows = table_pattern.findall(section_text)

    header_seen = False
    separator_seen = False

    for row in rows:
        cells = [c.strip() for c in row.split("|")]
        # Remove empty strings from split
        cells = [c for c in cells if c != ""]

        if not header_seen:
            header_seen = True
            continue
        if not separator_seen:
            # Separator row (---+---)
            if all(re.match(r"^-+$", c) for c in cells):
                separator_seen = True
                continue
            separator_seen = True

        if len(cells) < 3:
            continue

        # Feature is column 2 (index 1), Status is column 3 (index 2)
        # But Area column may be empty for continuation rows
        feature = cells[1] if len(cells) >= 7 else cells[0]
        status_col = cells[2] if len(cells) >= 7 else cells[1]

        # Clean up feature name - strip bold markers
        feature = re.sub(r"\*\*(.+?)\*\*", r"\1", feature).strip()

        # Extract status emoji
        status = status_col.strip()

        if feature and status:
            features[feature] = status

    return features


def load_mapping(mapping_file: Path) -> dict[str, dict[str, list[str]]]:
    """Load the feature -> file path mapping from YAML."""
    with open(mapping_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def check_paths_exist(paths: list[str], label: str) -> list[str]:
    """Check that all paths exist. Returns list of error messages."""
    errors = []
    for p in paths:
        full = REPO_ROOT / p
        if not full.exists():
            errors.append(f"  {label} missing: {p}")
    return errors


def main() -> int:
    """Run the capability matrix consistency check."""
    if not PROJECT_MD.exists():
        print("ERROR: PROJECT.md not found")
        return 1

    if not MAPPING_FILE.exists():
        print("ERROR: tools/capability_matrix_mapping.yaml not found")
        return 1

    features = parse_matrix(PROJECT_MD)
    mapping = load_mapping(MAPPING_FILE)

    if not features:
        print("ERROR: No features parsed from Capability Matrix")
        return 1

    print(f"Parsed {len(features)} features from Capability Matrix")
    print(f"Loaded {len(mapping)} entries from mapping file")
    print()

    errors: list[str] = []
    checked = 0
    skipped_no_mapping = 0

    for feature, status in features.items():
        if status != "✅":
            continue

        if feature not in mapping:
            skipped_no_mapping += 1
            continue

        checked += 1
        entry = mapping[feature]
        feature_errors: list[str] = []

        # Check source files
        src_paths = entry.get("src", [])
        if src_paths:
            feature_errors.extend(check_paths_exist(src_paths, "src"))

        # Check test files
        test_paths = entry.get("tests", [])
        if test_paths:
            feature_errors.extend(check_paths_exist(test_paths, "test"))

        if feature_errors:
            errors.append(f"✅ {feature}:")
            errors.extend(feature_errors)

    # Check for mapping entries that reference non-existent features
    unmapped_in_matrix = []
    for feature_key in mapping:
        if feature_key not in features:
            unmapped_in_matrix.append(feature_key)

    print(f"Checked {checked} ✅ entries against mapping")
    if skipped_no_mapping > 0:
        print(f"Skipped {skipped_no_mapping} ✅ entries with no mapping (add to mapping file)")
    print()

    if unmapped_in_matrix:
        print(f"WARNING: {len(unmapped_in_matrix)} mapping entries not found in matrix:")
        for f in unmapped_in_matrix:
            print(f"  - {f}")
        print()

    if errors:
        print("ERRORS: The following ✅ entries have missing files:")
        print()
        for e in errors:
            print(e)
        print()
        print(f"FAILED: {len(errors)} inconsistencies found")
        return 1

    print("OK: All ✅ entries have matching source and test files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
