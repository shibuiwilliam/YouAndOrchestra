"""Genre Skill v2.0 loader — validates and loads .md Skills with YAML frontmatter.

Genre Skills follow the template defined in PROJECT.md §10. Each Skill is a
markdown file with YAML frontmatter containing structured metadata (genre_id,
display_name, ensemble_template, default_subagents, etc.) and body sections
(Defining Characteristics, Anti-Patterns, Reference Tracks, etc.).

Skills missing the YAML frontmatter are rejected at load time. Skills that
load but lack required body sections fail validation (usable by Conductor
for basic evaluation but not by the Adversarial Critic or Reference Matcher).

Belongs to the skills package (cross-cutting, similar to reflect/).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
import yaml
from pydantic import BaseModel

logger = structlog.get_logger()


# Required body sections per PROJECT.md §10
REQUIRED_BODY_SECTIONS: list[str] = [
    "Defining Characteristics",
    "Anti-Patterns",
    "Evaluation Weight Adjustments",
]

# All expected body sections (required + optional)
ALL_BODY_SECTIONS: list[str] = [
    "Defining Characteristics",
    "Required Spec Patterns",
    "Idiomatic Chord Progressions",
    "Idiomatic Rhythms",
    "Anti-Patterns",
    "Reference Tracks",
    "Default Sound Design",
    "Evaluation Weight Adjustments",
    "Default Trajectories",
]


class DefaultSubagents(BaseModel):
    """Active and inactive subagent configuration for a genre."""

    active: list[str] = []
    inactive: list[str] = []


class GenreSkillFrontmatter(BaseModel):
    """Pydantic model for v2.0 Genre Skill YAML frontmatter.

    All fields listed here are required for a Skill to be considered
    loadable. Additional fields are allowed for forward compatibility.
    """

    genre_id: str
    display_name: str
    parent_genres: list[str] = []
    related_genres: list[str] = []
    typical_use_cases: list[str] = []
    ensemble_template: str
    default_subagents: DefaultSubagents

    model_config = {"extra": "allow"}


@dataclass(frozen=True)
class GenreSkill:
    """A loaded and parsed Genre Skill.

    Attributes:
        path: Source file path.
        frontmatter: Validated YAML frontmatter.
        sections: Mapping of section heading to section content.
        raw_body: The full markdown body below the frontmatter.
    """

    path: Path
    frontmatter: GenreSkillFrontmatter
    sections: dict[str, str] = field(default_factory=dict)
    raw_body: str = ""


def load_genre_skill(path: Path) -> GenreSkill | None:
    """Load a Genre Skill from a markdown file with YAML frontmatter.

    Args:
        path: Path to the .md skill file.

    Returns:
        GenreSkill if loading and frontmatter validation succeed, None otherwise.
        Logs a warning on failure.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("genre_skill_read_error", path=str(path), error=str(e))
        return None

    # Parse YAML frontmatter (between --- markers)
    frontmatter_data, body = _parse_frontmatter(content)
    if frontmatter_data is None:
        logger.warning("genre_skill_no_frontmatter", path=str(path))
        return None

    # Validate frontmatter against Pydantic model
    try:
        frontmatter = GenreSkillFrontmatter(**frontmatter_data)
    except Exception as e:
        logger.warning(
            "genre_skill_invalid_frontmatter",
            path=str(path),
            error=str(e),
        )
        return None

    # Parse body sections
    sections = _parse_sections(body)

    return GenreSkill(
        path=path,
        frontmatter=frontmatter,
        sections=sections,
        raw_body=body,
    )


def validate_genre_skill(skill: GenreSkill) -> list[str]:
    """Validate that a loaded Genre Skill has all required body sections.

    Args:
        skill: A successfully loaded GenreSkill.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []
    for section_name in REQUIRED_BODY_SECTIONS:
        if section_name not in skill.sections:
            errors.append(
                f"Missing required section: '## {section_name}'. "
                f"Genre Skill '{skill.frontmatter.genre_id}' cannot be used "
                f"by the Adversarial Critic without Anti-Patterns."
            )
    return errors


def load_all_genre_skills(skills_dir: Path | None = None) -> dict[str, GenreSkill]:
    """Load all valid Genre Skills from a directory.

    Args:
        skills_dir: Directory containing .md skill files. Defaults to
            .claude/skills/genres/ relative to project root.

    Returns:
        Mapping of genre_id to loaded GenreSkill (only valid skills included).
    """
    if skills_dir is None:
        skills_dir = Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "skills" / "genres"

    if not skills_dir.exists():
        logger.warning("genre_skills_dir_not_found", path=str(skills_dir))
        return {}

    skills: dict[str, GenreSkill] = {}
    for md_file in sorted(skills_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue  # Skip template files
        skill = load_genre_skill(md_file)
        if skill is not None:
            skills[skill.frontmatter.genre_id] = skill

    return skills


def _parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:
    """Extract YAML frontmatter and body from markdown content.

    Args:
        content: Full markdown file content.

    Returns:
        Tuple of (frontmatter dict or None, body string).
    """
    # Match content between opening --- and closing ---
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
    if not match:
        return None, content

    yaml_str = match.group(1)
    body = match.group(2)

    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError:
        return None, content

    if not isinstance(data, dict):
        return None, content

    return data, body


def _parse_sections(body: str) -> dict[str, str]:
    """Parse markdown body into heading -> content mapping.

    Only parses ## level headings (h2).

    Args:
        body: Markdown body (below frontmatter).

    Returns:
        Dict mapping section heading text to section content.
    """
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in body.split("\n"):
        heading_match = re.match(r"^##\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = heading_match.group(1).strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    # Save last section
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections
