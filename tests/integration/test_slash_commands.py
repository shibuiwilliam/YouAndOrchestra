"""Integration tests for slash command definition files.

Verifies that each command markdown file is parseable, has the required
structure, and enforces the 6-phase compositional cognition protocol.
"""

from __future__ import annotations

from pathlib import Path

import pytest

COMMANDS_DIR = Path(__file__).parent.parent.parent / ".claude" / "commands"

REQUIRED_COMMANDS = [
    "compose.md",
    "conduct.md",
    "critique.md",
    "sketch.md",
    "arrange.md",
    "regenerate-section.md",
    "explain.md",
    "render.md",
]


class TestSlashCommandDefinitions:
    """Tests for .claude/commands/ markdown files."""

    def test_commands_directory_exists(self) -> None:
        """The .claude/commands/ directory must exist."""
        assert COMMANDS_DIR.exists(), f"Missing directory: {COMMANDS_DIR}"

    @pytest.mark.parametrize("command_file", REQUIRED_COMMANDS)
    def test_required_command_exists(self, command_file: str) -> None:
        """Each required slash command must have a definition file."""
        path = COMMANDS_DIR / command_file
        assert path.exists(), f"Missing command definition: {path}"

    @pytest.mark.parametrize("command_file", REQUIRED_COMMANDS)
    def test_command_has_title(self, command_file: str) -> None:
        """Each command file must start with a markdown title."""
        path = COMMANDS_DIR / command_file
        if not path.exists():
            pytest.skip(f"Command file not found: {command_file}")

        content = path.read_text().strip()
        first_line = content.split("\n")[0]
        assert first_line.startswith("# "), f"{command_file} must start with '# <title>', got: {first_line!r}"

    @pytest.mark.parametrize("command_file", REQUIRED_COMMANDS)
    def test_command_not_empty(self, command_file: str) -> None:
        """Each command definition must have substantial content."""
        path = COMMANDS_DIR / command_file
        if not path.exists():
            pytest.skip(f"Command file not found: {command_file}")

        content = path.read_text().strip()
        assert len(content) > 100, (  # noqa: PLR2004
            f"{command_file} has insufficient content ({len(content)} chars)"
        )

    def test_compose_enforces_protocol(self) -> None:
        """The /compose command must not skip directly to note generation.

        Per PROJECT.md Section 6, the 6-phase compositional cognition protocol
        must be followed: intent → trajectory → skeleton → critique → fill → simulate.
        """
        path = COMMANDS_DIR / "compose.md"
        if not path.exists():
            pytest.skip("compose.md not found")

        content = path.read_text().lower()
        # The compose command should reference the conductor or multi-phase protocol
        assert any(term in content for term in ["conductor", "phase", "evaluate", "iterate", "feedback"]), (
            "compose.md must reference the Conductor or multi-phase protocol"
        )

    def test_sketch_is_dialogue(self) -> None:
        """The /sketch command should establish a dialogue (not one-shot)."""
        path = COMMANDS_DIR / "sketch.md"
        if not path.exists():
            pytest.skip("sketch.md not found")

        content = path.read_text().lower()
        assert any(term in content for term in ["dialogue", "question", "clarif", "ask", "confirm"]), (
            "sketch.md must involve a dialogue with the user"
        )

    def test_arrange_marked_planned_or_implemented(self) -> None:
        """The /arrange command should exist (may be marked planned)."""
        path = COMMANDS_DIR / "arrange.md"
        if not path.exists():
            pytest.skip("arrange.md not found")

        content = path.read_text()
        # It should exist and have content
        assert len(content.strip()) > 50  # noqa: PLR2004

    def test_no_command_references_living_artist(self) -> None:
        """No command definition should reference a living artist by name."""
        forbidden_patterns = ["taylor swift", "beyonce", "drake", "ed sheeran", "billie eilish"]

        for command_file in COMMANDS_DIR.glob("*.md"):
            content = command_file.read_text().lower()
            for pattern in forbidden_patterns:
                assert pattern not in content, f"{command_file.name} references living artist '{pattern}'"
