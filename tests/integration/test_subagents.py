"""Integration tests for subagent definition files.

Verifies that each subagent markdown file is parseable and contains
the required sections per PROJECT.md Section 5.
"""

from __future__ import annotations

from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "agents"

REQUIRED_AGENTS = [
    "composer.md",
    "harmony-theorist.md",
    "rhythm-architect.md",
    "orchestrator.md",
    "adversarial-critic.md",
    "mix-engineer.md",
    "producer.md",
]

# Required sections per PROJECT.md Section 5
REQUIRED_SECTIONS = {
    "responsibility",
    "input",
    "output",
    "constraints",
    "evaluation criteria",
}


class TestSubagentDefinitions:
    """Tests for .claude/agents/ markdown files."""

    def test_agents_directory_exists(self) -> None:
        """The .claude/agents/ directory must exist."""
        assert AGENTS_DIR.exists(), f"Missing directory: {AGENTS_DIR}"

    @pytest.mark.parametrize("agent_file", REQUIRED_AGENTS)
    def test_required_agent_exists(self, agent_file: str) -> None:
        """Each of the 7 required subagents must have a definition file."""
        path = AGENTS_DIR / agent_file
        assert path.exists(), f"Missing subagent definition: {path}"

    @pytest.mark.parametrize("agent_file", REQUIRED_AGENTS)
    def test_agent_has_required_sections(self, agent_file: str) -> None:
        """Each subagent must have responsibility, input, output, constraints, evaluation criteria."""
        path = AGENTS_DIR / agent_file
        if not path.exists():
            pytest.skip(f"Agent file not found: {agent_file}")

        content = path.read_text().lower()
        headers = {line.strip("# ").strip() for line in content.splitlines() if line.startswith("## ")}

        for section in REQUIRED_SECTIONS:
            # Allow variations like "Constraints" vs "Forbidden" vs "Constraints"
            found = any(section in h for h in headers)
            assert found, f"{agent_file} missing required section '## {section}'. Found headers: {sorted(headers)}"

    @pytest.mark.parametrize("agent_file", REQUIRED_AGENTS)
    def test_agent_has_role_description(self, agent_file: str) -> None:
        """Each subagent must start with a role description."""
        path = AGENTS_DIR / agent_file
        if not path.exists():
            pytest.skip(f"Agent file not found: {agent_file}")

        content = path.read_text()
        assert "## Role" in content or "# " in content.split("\n")[0], (
            f"{agent_file} must start with a title or have a '## Role' section"
        )

    @pytest.mark.parametrize("agent_file", REQUIRED_AGENTS)
    def test_agent_not_empty(self, agent_file: str) -> None:
        """Each subagent definition must have substantial content."""
        path = AGENTS_DIR / agent_file
        if not path.exists():
            pytest.skip(f"Agent file not found: {agent_file}")

        content = path.read_text().strip()
        # At minimum 200 characters of content
        assert len(content) > 200, (  # noqa: PLR2004
            f"{agent_file} has insufficient content ({len(content)} chars)"
        )

    def test_no_living_artist_references(self) -> None:
        """No subagent definition should reference a living artist by name."""
        # Common living artist names that should not appear
        forbidden_patterns = ["taylor swift", "beyonce", "drake", "ed sheeran", "billie eilish"]

        for agent_file in AGENTS_DIR.glob("*.md"):
            content = agent_file.read_text().lower()
            for pattern in forbidden_patterns:
                assert pattern not in content, f"{agent_file.name} references living artist '{pattern}'"
