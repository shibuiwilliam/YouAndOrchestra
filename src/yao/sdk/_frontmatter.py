"""Internal Markdown parser for .claude/agents/*.md files.

Extracts agent metadata from Markdown files that may or may not
have YAML front matter. When no front matter is present, the parser
extracts name and description from the Markdown heading and first
paragraph.

The Markdown files are the source of truth — this parser generates
the Python ``AgentDefinition`` mirror, never the other way around.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def parse_agent_md(path: Path) -> tuple[dict[str, Any], str]:
    """Parse a .claude/agents/*.md file into metadata and body.

    Supports two formats:
    1. YAML front matter delimited by ``---`` (standard Jekyll format)
    2. Pure Markdown (name extracted from filename, description from body)

    Args:
        path: Path to the agent Markdown file.

    Returns:
        Tuple of (metadata dict, body text).
        Metadata always includes at least ``name`` and ``description``.
    """
    content = path.read_text()

    # Try YAML front matter first
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front_matter = parts[1].strip()
            body = parts[2].strip()
            try:
                meta = yaml.safe_load(front_matter) or {}
                if isinstance(meta, dict):
                    meta.setdefault("name", _name_from_path(path))
                    meta.setdefault("description", _first_paragraph(body))
                    return meta, body
            except yaml.YAMLError:
                pass

    # Pure Markdown — extract from structure
    meta = _extract_from_markdown(path, content)
    return meta, content


def _name_from_path(path: Path) -> str:
    """Derive the agent name from the filename.

    Converts ``harmony-theorist.md`` to ``harmony-theorist``.
    Skips files starting with ``_`` (protocols, internal docs).

    Args:
        path: Path to the agent file.

    Returns:
        Agent name string.
    """
    return path.stem


def _first_paragraph(text: str) -> str:
    """Extract the first non-heading paragraph from text.

    Args:
        text: Markdown text.

    Returns:
        First paragraph text, or empty string.
    """
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            return line
    return ""


def _extract_from_markdown(path: Path, content: str) -> dict[str, Any]:
    """Extract metadata from a pure-Markdown agent definition.

    Args:
        path: Path to the file.
        content: File content.

    Returns:
        Metadata dict with name, description, and optional fields.
    """
    name = _name_from_path(path)
    lines = content.split("\n")

    # Extract description from the first ## Role section
    description = ""
    in_role = False
    for line in lines:
        if line.strip().startswith("## Role"):
            in_role = True
            continue
        if in_role:
            stripped = line.strip()
            if stripped.startswith("##"):
                break
            if stripped:
                description = stripped
                break

    if not description:
        description = _first_paragraph(content)

    meta: dict[str, Any] = {
        "name": name,
        "description": description,
    }

    # Check for tool restrictions mentioned in the body
    content_lower = content.lower()
    if (
        ("disallowedtools" in content_lower or "never modifies" in content_lower)
        and "write" in content_lower
        and "edit" in content_lower
    ):
        meta["disallowed_tools"] = ["Write", "Edit"]

    # Check for read-only hints
    if "read-only" in content_lower or "never modif" in content_lower:
        meta["read_only"] = True

    return meta
