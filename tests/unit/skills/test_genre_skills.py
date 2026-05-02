"""Tests for genre Skill files and YAML sync."""

from __future__ import annotations

from pathlib import Path

from tools.skill_yaml_sync import extract_frontmatter

SKILLS_DIR = Path(".claude/skills/genres")

REQUIRED_FRONTMATTER_KEYS = {
    "genre",
    "tempo_range",
    "typical_keys",
    "preferred_instruments",
    "avoided_instruments",
}

EXPECTED_GENRES = [
    "cinematic",
    "lofi_hiphop",
    "j_pop",
    "neoclassical",
    "ambient",
    "jazz_ballad",
    "game_8bit_chiptune",
    "acoustic_folk",
]


class TestGenreSkillFiles:
    """Verify genre Skill file structure and content."""

    def test_minimum_genre_count(self) -> None:
        """v1.1 target: at least 8 genres."""
        md_files = list(SKILLS_DIR.glob("*.md"))
        assert len(md_files) >= 8, f"Expected 8+ genres, got {len(md_files)}"  # noqa: PLR2004

    def test_all_expected_genres_present(self) -> None:
        """All planned genres must have Skill files."""
        existing = {p.stem for p in SKILLS_DIR.glob("*.md")}
        for genre in EXPECTED_GENRES:
            assert genre in existing, f"Missing genre Skill: {genre}.md"

    def test_all_genres_have_frontmatter(self) -> None:
        """Every genre Skill must have valid YAML front-matter."""
        for md in SKILLS_DIR.glob("*.md"):
            fm = extract_frontmatter(md)
            assert fm is not None, f"{md.name} missing front-matter"

    def test_frontmatter_has_required_keys(self) -> None:
        """Front-matter must include genre, tempo_range, typical_keys, instruments."""
        for md in SKILLS_DIR.glob("*.md"):
            fm = extract_frontmatter(md)
            assert fm is not None, f"{md.name} missing front-matter"
            for key in REQUIRED_FRONTMATTER_KEYS:
                assert key in fm, f"{md.name} missing front-matter key: {key}"

    def test_tempo_range_is_valid(self) -> None:
        """tempo_range must be a list of 2 numbers, min < max."""
        for md in SKILLS_DIR.glob("*.md"):
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            tr = fm["tempo_range"]
            assert isinstance(tr, list) and len(tr) == 2, (  # noqa: PLR2004
                f"{md.name}: tempo_range must be [min, max]"
            )
            assert tr[0] < tr[1], f"{md.name}: tempo_range min >= max"

    def test_genre_slug_matches_filename(self) -> None:
        """The genre field must match the filename."""
        for md in SKILLS_DIR.glob("*.md"):
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            assert fm["genre"] == md.stem, f"{md.name}: genre '{fm['genre']}' doesn't match filename"
