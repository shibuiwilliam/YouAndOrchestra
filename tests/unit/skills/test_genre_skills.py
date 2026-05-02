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
    # Original 8 (v1.1)
    "cinematic",
    "lofi_hiphop",
    "j_pop",
    "neoclassical",
    "ambient",
    "jazz_ballad",
    "game_8bit_chiptune",
    "acoustic_folk",
    # New 8 (v2.0 Tier 1)
    "rock_classic",
    "jazz_swing",
    "blues",
    "funk",
    "edm_house",
    "synthwave",
    "baroque",
    "romantic",
]


def _all_skill_files() -> list[Path]:
    """Collect all .md skill files from genres/ and subdirectories."""
    return sorted(SKILLS_DIR.rglob("*.md"))


class TestGenreSkillFiles:
    """Verify genre Skill file structure and content."""

    def test_minimum_genre_count(self) -> None:
        """v2.0 target: at least 16 genres."""
        md_files = _all_skill_files()
        assert len(md_files) >= 16, f"Expected 16+ genres, got {len(md_files)}"  # noqa: PLR2004

    def test_all_expected_genres_present(self) -> None:
        """All planned genres must have Skill files."""
        existing = {p.stem for p in _all_skill_files()}
        for genre in EXPECTED_GENRES:
            assert genre in existing, f"Missing genre Skill: {genre}.md"

    def test_all_genres_have_frontmatter(self) -> None:
        """Every genre Skill must have valid YAML front-matter."""
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            assert fm is not None, f"{md.name} missing front-matter"

    def test_frontmatter_has_required_keys(self) -> None:
        """Front-matter must include genre, tempo_range, typical_keys, instruments."""
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            assert fm is not None, f"{md.name} missing front-matter"
            for key in REQUIRED_FRONTMATTER_KEYS:
                assert key in fm, f"{md.name} missing front-matter key: {key}"

    def test_tempo_range_is_valid(self) -> None:
        """tempo_range must be a list of 2 numbers, min < max."""
        for md in _all_skill_files():
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
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            assert fm["genre"] == md.stem, f"{md.name}: genre '{fm['genre']}' doesn't match filename"

    def test_new_genres_have_chord_progressions(self) -> None:
        """v2.0 new genres must have typical_chord_progressions."""
        new_genres = {"rock_classic", "jazz_swing", "blues", "funk", "edm_house", "synthwave", "baroque", "romantic"}
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None or fm["genre"] not in new_genres:
                continue
            assert "typical_chord_progressions" in fm, f"{md.name} missing typical_chord_progressions"
            assert len(fm["typical_chord_progressions"]) >= 3, (  # noqa: PLR2004
                f"{md.name}: expected 3+ chord progressions"
            )

    def test_new_genres_have_characteristic_rhythms(self) -> None:
        """v2.0 new genres must have characteristic_rhythms."""
        new_genres = {"rock_classic", "jazz_swing", "blues", "funk", "edm_house", "synthwave", "baroque", "romantic"}
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None or fm["genre"] not in new_genres:
                continue
            assert "characteristic_rhythms" in fm, f"{md.name} missing characteristic_rhythms"
