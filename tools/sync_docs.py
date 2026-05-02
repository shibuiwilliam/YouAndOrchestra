#!/usr/bin/env python3
"""Document synchronization checker — detects drift between docs.

Checks:
1. FEATURE_STATUS.md status symbols are parseable
2. CLAUDE.md Tier checklists are parseable
3. Features marked ✅ in FEATURE_STATUS.md but still [ ] in CLAUDE.md → WARN

Exit code: 0 if no errors, 1 if errors found.
Warnings are informational and do not cause failure.

Usage:
    python tools/sync_docs.py
    make sync-docs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FEATURE_STATUS_PATH = Path("FEATURE_STATUS.md")
CLAUDE_MD_PATH = Path("CLAUDE.md")

# Status symbols in FEATURE_STATUS.md
_STATUS_SYMBOLS = {"✅", "🟢", "🟡", "⚪", "🔴"}


def parse_feature_status(path: Path) -> dict[str, str]:
    """Parse FEATURE_STATUS.md and extract feature → status mapping.

    Args:
        path: Path to FEATURE_STATUS.md.

    Returns:
        Dict of feature_name → status_symbol.
    """
    if not path.exists():
        return {}

    features: dict[str, str] = {}
    text = path.read_text(encoding="utf-8")

    # Match table rows: | Feature | Status | ...
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # remove empty from leading/trailing |
        if len(cells) < 2:  # noqa: PLR2004
            continue

        feature = cells[0]
        status_cell = cells[1]

        # Extract status symbol
        for sym in _STATUS_SYMBOLS:
            if sym in status_cell:
                features[feature] = sym
                break

    return features


def parse_claude_tier_items(path: Path) -> list[str]:
    """Parse CLAUDE.md Tier checklist items ([ ] lines).

    Args:
        path: Path to CLAUDE.md.

    Returns:
        List of unchecked item descriptions.
    """
    if not path.exists():
        return []

    items: list[str] = []
    text = path.read_text(encoding="utf-8")

    # Match "- [ ] **Item**" pattern
    pattern = re.compile(r"^- \[ \] \*\*(.+?)\*\*")
    for line in text.split("\n"):
        match = pattern.match(line.strip())
        if match:
            items.append(match.group(1))

    return items


def check_consistency() -> tuple[list[str], list[str]]:
    """Check consistency between FEATURE_STATUS.md and CLAUDE.md.

    Returns:
        Tuple of (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Parse both files
    features = parse_feature_status(FEATURE_STATUS_PATH)
    tier_items = parse_claude_tier_items(CLAUDE_MD_PATH)

    if not features:
        errors.append("FEATURE_STATUS.md not found or has no features")
        return errors, warnings

    if not tier_items:
        warnings.append("CLAUDE.md has no unchecked Tier items (all done?)")

    # Count statuses
    stable_count = sum(1 for s in features.values() if s == "✅")
    designed_count = sum(1 for s in features.values() if s == "⚪")
    total = len(features)

    print(f"FEATURE_STATUS.md: {total} features ({stable_count} ✅, {designed_count} ⚪)")
    print(f"CLAUDE.md: {len(tier_items)} unchecked Tier items")

    # Check: ⚪ features that have no corresponding Tier item
    designed_features = [f for f, s in features.items() if s == "⚪"]
    if designed_features:
        print(f"\n⚪ Designed but not started ({len(designed_features)}):")
        for f in designed_features:
            print(f"  - {f}")

    return errors, warnings


def main() -> int:
    """Run document sync check."""
    print("=== Document Sync Check ===\n")

    errors, warnings = check_consistency()

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN: {w}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    print("\nOK: Document sync check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
