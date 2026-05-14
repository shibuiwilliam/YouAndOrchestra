"""Tests for yao.sdk._frontmatter — Markdown parser."""

from __future__ import annotations

from pathlib import Path

from yao.sdk._frontmatter import parse_agent_md


class TestParseAgentMd:
    def test_yaml_front_matter(self, tmp_path: Path) -> None:
        md = tmp_path / "test-agent.md"
        md.write_text(
            "---\n"
            "name: test-agent\n"
            "description: A test agent\n"
            "model: claude-sonnet-4-6\n"
            "---\n"
            "# Test Agent\n\n"
            "Body text here.\n"
        )
        meta, body = parse_agent_md(md)
        assert meta["name"] == "test-agent"
        assert meta["description"] == "A test agent"
        assert meta["model"] == "claude-sonnet-4-6"
        assert "Body text here" in body

    def test_pure_markdown(self, tmp_path: Path) -> None:
        md = tmp_path / "my-agent.md"
        md.write_text("# My Agent\n\n## Role\nDo amazing things with music.\n\n## Inputs\n- composition.yaml\n")
        meta, body = parse_agent_md(md)
        assert meta["name"] == "my-agent"
        assert meta["description"] == "Do amazing things with music."

    def test_name_from_filename(self, tmp_path: Path) -> None:
        md = tmp_path / "harmony-theorist.md"
        md.write_text("# Harmony Theorist\n\nTheory stuff.\n")
        meta, _body = parse_agent_md(md)
        assert meta["name"] == "harmony-theorist"

    def test_disallowed_tools_detected(self, tmp_path: Path) -> None:
        md = tmp_path / "critic.md"
        md.write_text(
            "# Critic\n\n"
            "## Role\n"
            "Find weaknesses. Never praises, never modifies.\n\n"
            "disallowedTools: Write, Edit\n"
            "Read-only by design.\n"
        )
        meta, _body = parse_agent_md(md)
        assert meta.get("disallowed_tools") == ["Write", "Edit"]
        assert meta.get("read_only") is True

    def test_real_agent_file(self) -> None:
        """Parse a real agent file from the project."""
        agent_dir = Path(".claude/agents")
        if not agent_dir.exists():
            return
        composer = agent_dir / "composer.md"
        if not composer.exists():
            return
        meta, body = parse_agent_md(composer)
        assert meta["name"] == "composer"
        assert len(body) > 0
