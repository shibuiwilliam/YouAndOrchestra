"""Tests for genre Skill files and YAML sync."""

from __future__ import annotations

from pathlib import Path

from tools.skill_yaml_sync import extract_frontmatter

SKILLS_DIR = Path(".claude/skills/genres")

# v1.0 frontmatter keys (legacy skills not yet migrated to v2.0 template)
REQUIRED_FRONTMATTER_KEYS_V1 = {
    "genre",
    "tempo_range",
    "typical_keys",
    "preferred_instruments",
    "avoided_instruments",
}

# v2.0 frontmatter keys (migrated Tier-1 skills)
REQUIRED_FRONTMATTER_KEYS_V2 = {
    "genre_id",
    "display_name",
    "ensemble_template",
    "default_subagents",
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
    # New 6 (v2.0 Tier 4)
    "indian_classical_hindustani",
    "arab_maqam",
    "bossa_nova",
    "celtic_traditional",
    "film_score_dramatic",
    "game_bgm_rpg",
    "baroque",
    "romantic",
]


def _all_skill_files() -> list[Path]:
    """Collect all .md skill files from genres/ and subdirectories."""
    return sorted(p for p in SKILLS_DIR.rglob("*.md") if not p.name.startswith("_"))


class TestGenreSkillFiles:
    """Verify genre Skill file structure and content."""

    def test_minimum_genre_count(self) -> None:
        """v2.0 target: at least 22 genres."""
        md_files = _all_skill_files()
        assert len(md_files) >= 22, f"Expected 22+ genres, got {len(md_files)}"  # noqa: PLR2004

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
        """Front-matter must include either v1 or v2.0 required keys."""
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            assert fm is not None, f"{md.name} missing front-matter"
            # Accept either v1 or v2.0 format
            has_v1 = all(key in fm for key in REQUIRED_FRONTMATTER_KEYS_V1)
            has_v2 = all(key in fm for key in REQUIRED_FRONTMATTER_KEYS_V2)
            assert has_v1 or has_v2, (
                f"{md.name} missing required front-matter keys. "
                f"Needs either v1 keys {REQUIRED_FRONTMATTER_KEYS_V1} "
                f"or v2 keys {REQUIRED_FRONTMATTER_KEYS_V2}"
            )

    def test_tempo_range_is_valid(self) -> None:
        """tempo_range must be a list of 2 numbers, min < max (v1 format only)."""
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            # v2.0 skills define tempo in body sections, not frontmatter
            if "genre_id" in fm:
                continue
            tr = fm["tempo_range"]
            assert isinstance(tr, list) and len(tr) == 2, (  # noqa: PLR2004
                f"{md.name}: tempo_range must be [min, max]"
            )
            assert tr[0] < tr[1], f"{md.name}: tempo_range min >= max"

    def test_genre_slug_matches_filename(self) -> None:
        """The genre/genre_id field must match the filename."""
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            # Support both v1 ("genre") and v2.0 ("genre_id") field names
            genre_slug = fm.get("genre_id", fm.get("genre"))
            assert genre_slug == md.stem, f"{md.name}: genre '{genre_slug}' doesn't match filename"

    def test_new_genres_have_chord_progressions(self) -> None:
        """v2.0 new genres (v1 format) must have typical_chord_progressions."""
        new_genres = {"rock_classic", "jazz_swing", "blues", "funk", "edm_house", "synthwave", "baroque", "romantic"}
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in new_genres:
                continue
            # Only enforce for v1-format skills (v2.0 has body sections instead)
            if "genre_id" in fm:
                continue
            assert "typical_chord_progressions" in fm, f"{md.name} missing typical_chord_progressions"
            assert len(fm["typical_chord_progressions"]) >= 3, (  # noqa: PLR2004
                f"{md.name}: expected 3+ chord progressions"
            )

    def test_new_genres_have_characteristic_rhythms(self) -> None:
        """v2.0 new genres (v1 format) must have characteristic_rhythms."""
        new_genres = {"rock_classic", "jazz_swing", "blues", "funk", "edm_house", "synthwave", "baroque", "romantic"}
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in new_genres:
                continue
            # Only enforce for v1-format skills (v2.0 has body sections instead)
            if "genre_id" in fm:
                continue
            assert "characteristic_rhythms" in fm, f"{md.name} missing characteristic_rhythms"


class TestWorldGenreSkills:
    """Tests specific to world/non-Western genre Skills."""

    _WORLD_GENRES = {
        "indian_classical_hindustani",
        "arab_maqam",
        "bossa_nova",
        "celtic_traditional",
    }

    def test_world_genres_have_cultural_context(self) -> None:
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in self._WORLD_GENRES:
                continue
            assert "cultural_context" in fm, f"{md.name} missing cultural_context"
            assert fm["cultural_context"], f"{md.name} has empty cultural_context"

    def test_world_genres_have_forbidden_in_pure_form(self) -> None:
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in self._WORLD_GENRES:
                continue
            assert "forbidden_in_pure_form" in fm, f"{md.name} missing forbidden_in_pure_form"
            assert len(fm["forbidden_in_pure_form"]) > 0, f"{md.name} has empty forbidden_in_pure_form"

    def test_world_genres_have_allowed_relaxations(self) -> None:
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in self._WORLD_GENRES:
                continue
            assert "allowed_relaxations" in fm, f"{md.name} missing allowed_relaxations"

    def test_world_genres_have_expert_review_note(self) -> None:
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in self._WORLD_GENRES:
                continue
            assert "expert_review_note" in fm, f"{md.name} missing expert_review_note"
            assert fm["expert_review_note"], f"{md.name} has empty expert_review_note"

    def test_forbidden_and_relaxations_no_overlap(self) -> None:
        for md in _all_skill_files():
            fm = extract_frontmatter(md)
            if fm is None:
                continue
            genre_slug = fm.get("genre_id", fm.get("genre"))
            if genre_slug not in self._WORLD_GENRES:
                continue
            forbidden = set(fm.get("forbidden_in_pure_form", []))
            relaxations = fm.get("allowed_relaxations", [])
            if isinstance(relaxations, list):
                for r in relaxations:
                    if isinstance(r, dict):
                        pass
                    elif isinstance(r, str):
                        assert r not in forbidden, f"{md.name}: '{r}' in both forbidden and relaxations"
