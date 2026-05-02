#!/usr/bin/env python3
"""Extract front-matter YAML from genre Skills to machine-readable YAML files.

Reads .claude/skills/genres/*.md, extracts the YAML front-matter between
--- delimiters, and writes it to src/yao/skills/genres/<name>.yaml.

This makes Skill data programmatically accessible to generators while
keeping the human-readable Markdown as the source of truth.

Usage:
    python tools/skill_yaml_sync.py
    make sync-skills
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

SKILLS_DIR = Path(".claude/skills/genres")
YAML_DIR = Path("src/yao/skills/genres")

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def extract_frontmatter(md_path: Path) -> dict | None:
    """Extract YAML front-matter from a Markdown file.

    Args:
        md_path: Path to the Markdown file.

    Returns:
        Parsed YAML dict, or None if no front-matter found.
    """
    text = md_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.search(text)
    if not match:
        return None
    result: dict = yaml.safe_load(match.group(1))
    return result


def main() -> int:
    """Extract all genre Skill front-matter to YAML files."""
    if not SKILLS_DIR.exists():
        print(f"ERROR: {SKILLS_DIR} not found")
        return 1

    YAML_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    warnings = 0

    for md_path in sorted(SKILLS_DIR.glob("*.md")):
        fm = extract_frontmatter(md_path)
        if fm is None:
            print(f"  WARNING: No front-matter in {md_path.name}, skipping")
            warnings += 1
            continue

        out = YAML_DIR / f"{md_path.stem}.yaml"
        with out.open("w") as f:
            yaml.safe_dump(fm, f, default_flow_style=False, sort_keys=False)
        print(f"  OK: {md_path.name} -> {out.name}")
        count += 1

    print(f"\nSynced {count} genre Skills to {YAML_DIR}/")
    if warnings:
        print(f"  {warnings} file(s) skipped (no front-matter)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
