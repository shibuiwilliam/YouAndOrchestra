#!/usr/bin/env python3
"""Skill Grounding Check — verify genre Skills are referenced from src/.

Parses .claude/skills/genres/**/*.md frontmatter for genre_id,
then searches src/ for references to the skill loader or genre profiles.
Ungrounded skills (not referenced anywhere in production code) are flagged.

Wave 2.1 completion requirement: all skills referenced from generation pipeline.
Before Wave 2.1: WARN only (exit 0). After: exit 1 on failure.

Usage:
    python tools/check_skill_grounding.py [--json] [--strict]
    make skill-grounding
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".claude" / "skills" / "genres"
SRC_DIR = REPO_ROOT / "src"


@dataclass
class SkillInfo:
    """Information about a genre skill file."""

    genre_id: str
    file_path: str
    referenced_from: list[str] = field(default_factory=list)
    grounded: bool = False


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract YAML frontmatter from a markdown file."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    frontmatter = content[3:end].strip()
    result: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _find_skill_references(genre_id: str) -> list[str]:
    """Search src/ for references to a genre skill."""
    references: list[str] = []
    patterns = [
        re.compile(re.escape(genre_id)),
        re.compile(rf'["\']genres?[/\\]{re.escape(genre_id)}'),
    ]

    for py_file in SRC_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in patterns:
            if pattern.search(content):
                references.append(str(py_file.relative_to(REPO_ROOT)))
                break

    return references


def _find_pipeline_integration() -> dict[str, list[str]]:
    """Check for general skill/genre integration patterns in src/."""
    integration_patterns = {
        "skill_loader": re.compile(r"(SkillLoader|GenreProfile|skill_registry|load_genre)", re.IGNORECASE),
        "genre_config": re.compile(r"(genre_skill|genre_profile|genre_config)", re.IGNORECASE),
        "skills_dir": re.compile(r"skills[/\\]genres"),
    }

    found: dict[str, list[str]] = {}
    for py_file in SRC_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in integration_patterns.items():
            if pattern.search(content):
                found.setdefault(name, []).append(str(py_file.relative_to(REPO_ROOT)))

    return found


def main() -> int:
    """Run skill grounding check.

    Returns:
        0 if all skills are grounded (or --strict not set), 1 if failures.
    """
    json_mode = "--json" in sys.argv
    strict = "--strict" in sys.argv

    if not SKILLS_DIR.exists():
        msg = f"Skills directory not found: {SKILLS_DIR}"
        if json_mode:
            print(json.dumps({"tool": "skill-grounding", "error": msg}))
        else:
            print(f"ERROR: {msg}")
        return 1

    # Collect all genre skill files
    skills: list[SkillInfo] = []
    for md_file in sorted(SKILLS_DIR.rglob("*.md")):
        fm = _parse_frontmatter(md_file)
        genre_id = fm.get("genre", md_file.stem)
        refs = _find_skill_references(genre_id)
        skills.append(
            SkillInfo(
                genre_id=genre_id,
                file_path=str(md_file.relative_to(REPO_ROOT)),
                referenced_from=refs,
                grounded=len(refs) > 0,
            )
        )

    # Check for general pipeline integration
    integration = _find_pipeline_integration()
    has_loader = bool(integration.get("skill_loader"))

    grounded_count = sum(1 for s in skills if s.grounded)
    ungrounded = [s for s in skills if not s.grounded]

    if json_mode:
        output = {
            "tool": "skill-grounding",
            "total_skills": len(skills),
            "grounded": grounded_count,
            "ungrounded": len(ungrounded),
            "has_skill_loader": has_loader,
            "pipeline_integration": {k: v for k, v in integration.items()},
            "skills": [
                {
                    "genre_id": s.genre_id,
                    "file": s.file_path,
                    "grounded": s.grounded,
                    "referenced_from": s.referenced_from,
                }
                for s in skills
            ],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("YaO Skill Grounding Check (v3.0)")
        print("=" * 60)
        print()
        print(f"Skills directory: {SKILLS_DIR.relative_to(REPO_ROOT)}")
        print(f"Total genre skills: {len(skills)}")
        print(f"Skill loader in src/: {'YES' if has_loader else 'NO'}")
        print()

        if ungrounded:
            print(f"UNGROUNDED SKILLS ({len(ungrounded)}):")
            print("-" * 40)
            for s in ungrounded:
                print(f"  [{s.genre_id}] {s.file_path}")
            print()

        if grounded_count > 0:
            print(f"GROUNDED SKILLS ({grounded_count}):")
            print("-" * 40)
            for s in skills:
                if s.grounded:
                    print(f"  [{s.genre_id}] → {', '.join(s.referenced_from[:3])}")
            print()

        if integration:
            print("Pipeline integration points:")
            for name, files in integration.items():
                print(f"  {name}: {', '.join(files[:3])}")
            print()

        print("=" * 60)
        print(f"Skills: {len(skills)} | Grounded: {grounded_count} | Ungrounded: {len(ungrounded)}")
        print("=" * 60)

    if ungrounded:
        if strict:
            if not json_mode:
                print()
                print("FAIL: Ungrounded genre skills detected.")
                print("Action: Integrate skills into generation pipeline (Wave 2.1).")
            return 1
        else:
            if not json_mode:
                print()
                print("WARN: Ungrounded skills (not strict mode, exit 0).")
                print("This will become a hard failure after Wave 2.1.")
            return 0

    if not json_mode:
        print()
        print("OK: All genre skills are grounded in the pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
