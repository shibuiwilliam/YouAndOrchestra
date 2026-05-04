"""Tests for the Form Library (Layer 0 constants)."""

from __future__ import annotations

from yao.constants.forms import FORM_LIBRARY, SongForm, get_form, list_forms


class TestFormLibrary:
    def test_has_20_forms(self) -> None:
        """Library contains at least 20 forms."""
        assert len(FORM_LIBRARY) >= 20

    def test_all_form_ids_are_unique(self) -> None:
        """All form IDs are unique strings."""
        ids = list_forms()
        assert len(ids) == len(set(ids))

    def test_all_forms_have_sections(self) -> None:
        """Every form has at least one section."""
        for form_id, form in FORM_LIBRARY.items():
            assert len(form.sections) > 0, f"Form {form_id} has no sections"

    def test_all_forms_have_positive_bars(self) -> None:
        """Every section has positive bar count."""
        for form_id, form in FORM_LIBRARY.items():
            for section in form.sections:
                assert section.bars > 0, f"Form {form_id}.{section.id} has {section.bars} bars"

    def test_total_bars_computed(self) -> None:
        """total_bars property matches sum of section bars."""
        for form in FORM_LIBRARY.values():
            expected = sum(s.bars for s in form.sections)
            assert form.total_bars == expected

    def test_section_ids_property(self) -> None:
        """section_ids returns ordered list."""
        form = get_form("aaba_32bar")
        assert form is not None
        assert form.section_ids == ["a1", "a2", "b", "a3"]

    def test_density_and_tension_in_range(self) -> None:
        """All density and tension values are in [0, 1]."""
        for form in FORM_LIBRARY.values():
            for section in form.sections:
                assert 0.0 <= section.density <= 1.0
                assert 0.0 <= section.tension <= 1.0


class TestSpecificForms:
    def test_aaba_32bar(self) -> None:
        form = get_form("aaba_32bar")
        assert form is not None
        assert form.total_bars == 32
        assert len(form.sections) == 4

    def test_verse_chorus_bridge(self) -> None:
        form = get_form("verse_chorus_bridge")
        assert form is not None
        assert any(s.role == "chorus" for s in form.sections)
        assert any(s.role == "bridge" for s in form.sections)

    def test_blues_12bar(self) -> None:
        form = get_form("blues_12bar")
        assert form is not None
        assert form.total_bars == 12

    def test_j_pop_has_sabi(self) -> None:
        form = get_form("j_pop_intro_a_b_chorus")
        assert form is not None
        assert "sabi" in form.section_ids

    def test_nonexistent_returns_none(self) -> None:
        assert get_form("nonexistent_form") is None


class TestFormSerialization:
    def test_round_trip(self) -> None:
        form = get_form("aaba_32bar")
        assert form is not None
        data = form.to_dict()
        restored = SongForm.from_dict(data)
        assert restored.id == form.id
        assert restored.total_bars == form.total_bars
        assert len(restored.sections) == len(form.sections)
