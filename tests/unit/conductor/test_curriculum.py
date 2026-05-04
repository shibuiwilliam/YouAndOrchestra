"""Tests for curriculum learning failure-pattern dictionary."""

from __future__ import annotations

from pathlib import Path

from yao.conductor.curriculum import CurriculumDictionary, FailurePattern


class TestFailurePattern:
    """Test FailurePattern dataclass."""

    def test_construction(self) -> None:
        fp = FailurePattern(
            rule_id="structure.climax_absence",
            genre="cinematic",
            severity="major",
            adaptation_applied="increase_climax_dynamics",
            adaptation_params={"target_dynamics": "fff"},
            improvement_delta=0.5,
        )
        assert fp.rule_id == "structure.climax_absence"
        assert fp.occurrence_count == 1

    def test_frozen(self) -> None:
        import pytest

        fp = FailurePattern(
            rule_id="test",
            genre="test",
            severity="minor",
            adaptation_applied="fix",
            adaptation_params={},
            improvement_delta=0.1,
        )
        with pytest.raises(AttributeError):
            fp.rule_id = "changed"  # type: ignore[misc]


class TestCurriculumDictionary:
    """Test the curriculum dictionary."""

    def test_record_new_failure(self) -> None:
        cd = CurriculumDictionary()
        cd.record_failure(
            rule_id="structure.climax_absence",
            genre="cinematic",
            severity="major",
            adaptation_applied="boost_dynamics",
            adaptation_params={"target": "fff"},
            improvement_delta=0.5,
        )
        assert len(cd.patterns) == 1

    def test_lookup_known_pattern(self) -> None:
        cd = CurriculumDictionary()
        cd.record_failure(
            rule_id="rhythm.monotony",
            genre="jazz_ballad",
            severity="minor",
            adaptation_applied="increase_syncopation",
            adaptation_params={"delta": 0.1},
            improvement_delta=0.3,
        )
        result = cd.lookup("rhythm.monotony", "jazz_ballad")
        assert result is not None
        assert result.adaptation_applied == "increase_syncopation"

    def test_lookup_unknown_returns_none(self) -> None:
        cd = CurriculumDictionary()
        assert cd.lookup("nonexistent", "jazz") is None

    def test_better_adaptation_replaces(self) -> None:
        cd = CurriculumDictionary()
        cd.record_failure(
            rule_id="test",
            genre="pop",
            severity="minor",
            adaptation_applied="fix_v1",
            adaptation_params={},
            improvement_delta=0.2,
        )
        cd.record_failure(
            rule_id="test",
            genre="pop",
            severity="minor",
            adaptation_applied="fix_v2",
            adaptation_params={},
            improvement_delta=0.5,
        )
        result = cd.lookup("test", "pop")
        assert result is not None
        assert result.adaptation_applied == "fix_v2"
        assert result.occurrence_count == 2

    def test_worse_adaptation_increments_count(self) -> None:
        cd = CurriculumDictionary()
        cd.record_failure(
            rule_id="test",
            genre="pop",
            severity="minor",
            adaptation_applied="good_fix",
            adaptation_params={},
            improvement_delta=0.5,
        )
        cd.record_failure(
            rule_id="test",
            genre="pop",
            severity="minor",
            adaptation_applied="bad_fix",
            adaptation_params={},
            improvement_delta=0.1,
        )
        result = cd.lookup("test", "pop")
        assert result is not None
        assert result.adaptation_applied == "good_fix"  # kept the better one
        assert result.occurrence_count == 2

    def test_most_frequent_failures(self) -> None:
        cd = CurriculumDictionary()
        for _ in range(5):
            cd.record_failure(
                rule_id="frequent",
                genre="pop",
                severity="minor",
                adaptation_applied="fix",
                adaptation_params={},
                improvement_delta=0.1,
            )
        cd.record_failure(
            rule_id="rare",
            genre="pop",
            severity="minor",
            adaptation_applied="fix",
            adaptation_params={},
            improvement_delta=0.1,
        )
        top = cd.most_frequent_failures(n=1)
        assert len(top) == 1
        assert top[0].rule_id == "frequent"
        assert top[0].occurrence_count == 5

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "curriculum.json"
        cd = CurriculumDictionary()
        cd.record_failure(
            rule_id="test.rule",
            genre="jazz",
            severity="major",
            adaptation_applied="fix_it",
            adaptation_params={"param": "value"},
            improvement_delta=0.4,
        )
        cd.save(path)

        loaded = CurriculumDictionary.load(path)
        result = loaded.lookup("test.rule", "jazz")
        assert result is not None
        assert result.adaptation_applied == "fix_it"
        assert result.improvement_delta == 0.4

    def test_load_missing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        loaded = CurriculumDictionary.load(path)
        assert len(loaded.patterns) == 0

    def test_genre_agnostic_fallback(self) -> None:
        cd = CurriculumDictionary()
        cd.record_failure(
            rule_id="generic.rule",
            genre="*",
            severity="minor",
            adaptation_applied="universal_fix",
            adaptation_params={},
            improvement_delta=0.3,
        )
        # Lookup with specific genre falls back to generic
        result = cd.lookup("generic.rule", "cinematic")
        assert result is not None
        assert result.adaptation_applied == "universal_fix"
