"""Tests for v2.0 Genre Skill template loading and validation.

PR-1 acceptance criteria:
- Five+ genres are first-class
- Switching genre on the same composition spec produces measurably different evaluator scores
- Every Tier-1 Skill passes schema validation
- Skills missing YAML frontmatter are rejected
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from yao.ir.score_ir import ScoreIR
from yao.schema.composition import CompositionSpec
from yao.skills.genre_skill import GenreSkillFrontmatter, load_genre_skill, validate_genre_skill

# --- Fixtures ---

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "skills" / "genres"

VALID_FRONTMATTER = dedent("""\
    ---
    genre_id: test_genre
    display_name: "Test Genre"
    parent_genres: [electronic]
    related_genres: [ambient]
    typical_use_cases: [relaxation]
    ensemble_template: ambient_solo
    default_subagents:
      active: [texture_composer, sound_designer, mix_engineer, producer]
      inactive: [composer, harmony_theorist]
    ---

    ## Defining Characteristics
    - Test characteristic

    ## Required Spec Patterns
    tempo_bpm: 90

    ## Idiomatic Chord Progressions
    - I - IV - V

    ## Idiomatic Rhythms
    KICK: X . . . X . . .

    ## Anti-Patterns
    - Too fast tempo

    ## Reference Tracks
    - None yet

    ## Default Sound Design
    instruments: {}

    ## Evaluation Weight Adjustments
    harmony.consonance_ratio: 0.5

    ## Default Trajectories
    density: flat
""")

MISSING_GENRE_ID = dedent("""\
    ---
    display_name: "Bad Genre"
    parent_genres: []
    ---

    ## Defining Characteristics
    - Something
""")

MISSING_REQUIRED_SECTION = dedent("""\
    ---
    genre_id: incomplete
    display_name: "Incomplete"
    parent_genres: []
    related_genres: []
    typical_use_cases: []
    ensemble_template: classical_chamber
    default_subagents:
      active: [composer, producer]
      inactive: []
    ---

    ## Defining Characteristics
    - Something
""")


class TestGenreSkillFrontmatter:
    """Test the Pydantic model for genre skill frontmatter."""

    def test_valid_frontmatter_parses(self) -> None:
        """A valid frontmatter dict produces a GenreSkillFrontmatter instance."""
        data = {
            "genre_id": "deep_house",
            "display_name": "Deep House",
            "parent_genres": ["house", "electronic_dance"],
            "related_genres": ["tech_house"],
            "typical_use_cases": ["club_dance"],
            "ensemble_template": "hip_hop_producer",
            "default_subagents": {
                "active": ["sound_designer", "beatmaker", "loop_architect", "mix_engineer", "producer"],
                "inactive": ["composer", "harmony_theorist"],
            },
        }
        skill = GenreSkillFrontmatter(**data)
        assert skill.genre_id == "deep_house"
        assert skill.display_name == "Deep House"
        assert "house" in skill.parent_genres
        assert skill.ensemble_template == "hip_hop_producer"
        assert "sound_designer" in skill.default_subagents.active
        assert "composer" in skill.default_subagents.inactive

    def test_missing_genre_id_raises(self) -> None:
        """genre_id is required."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenreSkillFrontmatter(
                display_name="Bad",
                parent_genres=[],
                related_genres=[],
                typical_use_cases=[],
                ensemble_template="classical_chamber",
                default_subagents={"active": [], "inactive": []},
            )

    def test_missing_ensemble_template_raises(self) -> None:
        """ensemble_template is required."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenreSkillFrontmatter(
                genre_id="test",
                display_name="Test",
                parent_genres=[],
                related_genres=[],
                typical_use_cases=[],
                default_subagents={"active": [], "inactive": []},
            )


class TestLoadGenreSkill:
    """Test loading genre skills from markdown files."""

    def test_load_valid_skill(self, tmp_path: Path) -> None:
        """Loading a well-formed skill file succeeds."""
        skill_file = tmp_path / "test_genre.md"
        skill_file.write_text(VALID_FRONTMATTER)

        skill = load_genre_skill(skill_file)
        assert skill is not None
        assert skill.frontmatter.genre_id == "test_genre"
        assert skill.frontmatter.display_name == "Test Genre"
        assert "Anti-Patterns" in skill.sections

    def test_load_missing_frontmatter_returns_none(self, tmp_path: Path) -> None:
        """A file without YAML frontmatter returns None (with warning)."""
        skill_file = tmp_path / "no_front.md"
        skill_file.write_text("# Just a title\n\nNo frontmatter here.\n")

        skill = load_genre_skill(skill_file)
        assert skill is None

    def test_load_invalid_frontmatter_returns_none(self, tmp_path: Path) -> None:
        """A file with invalid frontmatter (missing required fields) returns None."""
        skill_file = tmp_path / "bad.md"
        skill_file.write_text(MISSING_GENRE_ID)

        skill = load_genre_skill(skill_file)
        assert skill is None


class TestValidateGenreSkill:
    """Test skill body section validation."""

    def test_valid_skill_passes_validation(self, tmp_path: Path) -> None:
        """A skill with all required sections passes validation."""
        skill_file = tmp_path / "test_genre.md"
        skill_file.write_text(VALID_FRONTMATTER)

        skill = load_genre_skill(skill_file)
        assert skill is not None
        errors = validate_genre_skill(skill)
        assert len(errors) == 0

    def test_missing_anti_patterns_fails_validation(self, tmp_path: Path) -> None:
        """A skill missing Anti-Patterns section fails validation."""
        skill_file = tmp_path / "incomplete.md"
        skill_file.write_text(MISSING_REQUIRED_SECTION)

        skill = load_genre_skill(skill_file)
        # Should still load (frontmatter is valid) but fail validation
        if skill is not None:
            errors = validate_genre_skill(skill)
            assert any("Anti-Patterns" in e for e in errors)


class TestTier1SkillsValid:
    """Every Tier-1 genre skill passes schema validation."""

    TIER_1_SKILLS = [
        "cinematic",
        "lo_fi_hiphop",
        "pop_japan",
        "pop_western",
        "ambient",
        "deep_house",
    ]

    @pytest.mark.parametrize("skill_id", TIER_1_SKILLS)
    def test_tier1_skill_loads_and_validates(self, skill_id: str) -> None:
        """Each Tier-1 skill file exists, loads, and passes validation."""
        # Skills may be at different filenames
        candidates = [
            SKILLS_DIR / f"{skill_id}.md",
            SKILLS_DIR / f"{skill_id.replace('_', '-')}.md",
        ]
        skill_path = None
        for c in candidates:
            if c.exists():
                skill_path = c
                break

        assert skill_path is not None, f"Tier-1 skill file not found for {skill_id}"
        skill = load_genre_skill(skill_path)
        assert skill is not None, f"Failed to load skill {skill_id}"
        errors = validate_genre_skill(skill)
        assert len(errors) == 0, f"Skill {skill_id} validation errors: {errors}"


class TestEvaluatorGenreWeights:
    """Switching genre on the same spec produces different evaluator scores."""

    def test_different_genres_produce_different_scores(
        self, minimal_spec: CompositionSpec, sample_score_ir: ScoreIR
    ) -> None:
        """The same ScoreIR evaluated with two different genre profiles
        produces measurably different quality scores."""
        from yao.verify.evaluator import evaluate_score

        # Evaluate without genre
        report_base = evaluate_score(sample_score_ir, minimal_spec)

        # Evaluate with a genre that heavily weights groove
        from yao.schema.genre_profile import GenreEvaluationSection, UnifiedGenreProfile

        groove_genre = UnifiedGenreProfile(
            genre_id="groove_test",
            evaluation=GenreEvaluationSection(
                weights={"melody": 0.05, "harmony": 0.05, "structure": 0.05, "acoustics": 0.85}
            ),
        )
        report_genre = evaluate_score(sample_score_ir, minimal_spec, genre_profile=groove_genre)

        # Scores should differ because weight distribution changed
        assert report_base.quality_score != report_genre.quality_score
