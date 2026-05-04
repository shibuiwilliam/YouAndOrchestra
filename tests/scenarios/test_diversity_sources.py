"""Scenario tests for diversity sources (Phase γ.6).

Verifies that the form library, vocabulary profiles, and melodic
strategies provide genuine diversity across generations.
"""

from __future__ import annotations

from yao.constants.forms import FORM_LIBRARY, get_form


class TestFormDiversity:
    """Verify the form library provides structural diversity."""

    def test_at_least_20_forms_available(self) -> None:
        """Form library has at least 20 distinct structures."""
        assert len(FORM_LIBRARY) >= 20

    def test_forms_have_varying_lengths(self) -> None:
        """Forms span a range of total bar counts (not all identical)."""
        bar_counts = {f.total_bars for f in FORM_LIBRARY.values()}
        # Should have at least 5 distinct lengths
        assert len(bar_counts) >= 5

    def test_forms_cover_multiple_genres(self) -> None:
        """Forms collectively reference at least 8 different genres."""
        all_genres: set[str] = set()
        for form in FORM_LIBRARY.values():
            all_genres.update(form.typical_genres)
        assert len(all_genres) >= 8

    def test_forms_have_varying_section_counts(self) -> None:
        """Forms have different numbers of sections (diversity of structure)."""
        section_counts = {len(f.sections) for f in FORM_LIBRARY.values()}
        assert len(section_counts) >= 4

    def test_multiple_forms_available_per_genre(self) -> None:
        """At least one genre has 3+ forms associated with it."""
        genre_form_count: dict[str, int] = {}
        for form in FORM_LIBRARY.values():
            for genre in form.typical_genres:
                genre_form_count[genre] = genre_form_count.get(genre, 0) + 1
        max_count = max(genre_form_count.values()) if genre_form_count else 0
        assert max_count >= 3

    def test_form_selection_for_pop(self) -> None:
        """Pop genre has at least 2 forms to choose from."""
        pop_forms = [f for f in FORM_LIBRARY.values() if "pop" in f.typical_genres or "j_pop" in f.typical_genres]
        assert len(pop_forms) >= 2

    def test_form_selection_for_jazz(self) -> None:
        """Jazz genre has at least 2 forms to choose from."""
        jazz_forms = [f for f in FORM_LIBRARY.values() if "jazz_ballad" in f.typical_genres]
        assert len(jazz_forms) >= 2

    def test_aaba_produces_expected_sequence(self) -> None:
        """AABA form produces A1(8), A2(8), B(8), A3(8) = 32 bars."""
        form = get_form("aaba_32bar")
        assert form is not None
        bars = [s.bars for s in form.sections]
        assert bars == [8, 8, 8, 8]
        roles = [s.role for s in form.sections]
        assert roles == ["verse", "verse", "bridge", "verse"]
