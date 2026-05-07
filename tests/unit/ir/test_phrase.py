"""Tests for phrase IR types: Phrase, PhrasePlan, PhraseFunction, CadenceType."""

from __future__ import annotations

from yao.ir.phrase import CadenceType, Phrase, PhraseFunction, PhrasePlan


class TestPhraseFunction:
    """Tests for PhraseFunction enum."""

    def test_all_values(self) -> None:
        """All expected phrase functions exist."""
        assert PhraseFunction.STATEMENT.value == "statement"
        assert PhraseFunction.QUESTION.value == "question"
        assert PhraseFunction.ANSWER.value == "answer"
        assert PhraseFunction.DEVELOPMENT.value == "development"
        assert PhraseFunction.RECAPITULATION.value == "recapitulation"
        assert PhraseFunction.CODA.value == "coda"


class TestCadenceType:
    """Tests for CadenceType enum."""

    def test_all_values(self) -> None:
        """All expected cadence types exist."""
        assert CadenceType.AUTHENTIC.value == "authentic"
        assert CadenceType.HALF.value == "half"
        assert CadenceType.PLAGAL.value == "plagal"
        assert CadenceType.DECEPTIVE.value == "deceptive"
        assert CadenceType.PHRYGIAN.value == "phrygian"
        assert CadenceType.NONE.value == "none"


class TestPhrase:
    """Tests for Phrase dataclass."""

    def test_creation(self) -> None:
        """Phrase can be created with required fields."""
        p = Phrase(
            start_bar=0,
            end_bar=4,
            function=PhraseFunction.STATEMENT,
            cadence=CadenceType.HALF,
        )
        assert p.start_bar == 0
        assert p.end_bar == 4
        assert p.function == PhraseFunction.STATEMENT
        assert p.cadence == CadenceType.HALF

    def test_length_bars(self) -> None:
        """length_bars returns correct span."""
        p = Phrase(
            start_bar=4,
            end_bar=12,
            function=PhraseFunction.DEVELOPMENT,
            cadence=CadenceType.NONE,
        )
        assert p.length_bars == 8

    def test_frozen(self) -> None:
        """Phrase is immutable (frozen dataclass)."""
        p = Phrase(
            start_bar=0,
            end_bar=4,
            function=PhraseFunction.STATEMENT,
            cadence=CadenceType.AUTHENTIC,
        )
        import pytest

        with pytest.raises(AttributeError):
            p.start_bar = 1  # type: ignore[misc]

    def test_optional_fields(self) -> None:
        """Optional fields have correct defaults."""
        p = Phrase(
            start_bar=0,
            end_bar=4,
            function=PhraseFunction.ANSWER,
            cadence=CadenceType.AUTHENTIC,
        )
        assert p.motif_id is None
        assert p.motif_transformation is None
        assert p.target_pitch is None
        assert p.contour_archetype == "arch"

    def test_with_motif(self) -> None:
        """Phrase with motif assignment."""
        p = Phrase(
            start_bar=0,
            end_bar=4,
            function=PhraseFunction.STATEMENT,
            cadence=CadenceType.HALF,
            motif_id="primary",
            motif_transformation="identity",
            target_pitch=67,
            contour_archetype="ascending",
        )
        assert p.motif_id == "primary"
        assert p.motif_transformation == "identity"
        assert p.target_pitch == 67
        assert p.contour_archetype == "ascending"


class TestPhrasePlan:
    """Tests for PhrasePlan dataclass."""

    def test_empty_plan(self) -> None:
        """Empty phrase plan is valid."""
        plan = PhrasePlan(phrases=())
        assert plan.phrase_count == 0
        assert plan.total_bars == 0

    def test_plan_with_phrases(self) -> None:
        """Plan with phrases computes total bars correctly."""
        phrases = (
            Phrase(start_bar=0, end_bar=4, function=PhraseFunction.STATEMENT, cadence=CadenceType.HALF),
            Phrase(start_bar=4, end_bar=8, function=PhraseFunction.ANSWER, cadence=CadenceType.AUTHENTIC),
        )
        plan = PhrasePlan(phrases=phrases)
        assert plan.phrase_count == 2
        assert plan.total_bars == 8

    def test_motif_library_default(self) -> None:
        """Default motif_library is empty dict."""
        plan = PhrasePlan(phrases=())
        assert plan.motif_library == {}

    def test_motif_library_custom(self) -> None:
        """Custom motif_library is preserved."""
        plan = PhrasePlan(phrases=(), motif_library={"primary": "mock_motif"})
        assert "primary" in plan.motif_library
