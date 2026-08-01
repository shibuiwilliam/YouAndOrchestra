"""Section-aware harmonic variation tests.

Guards the fix for "the piece keeps repeating the same harmony": every section
used to cycle the identical palette progression. Now each distinct section
gets a genre-idiomatic progression (from the genre's n-gram transitions) while
same-stem returns (A / A_prime) share their harmony — an A-B-A form, not four
identical loops.
"""

from __future__ import annotations

from collections import defaultdict

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.plan.harmony_planner import _contrast_start_chord, _genre_progression
from yao.generators.thematic_recall import auto_thematic_recall
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _chords_by_section(genre: str) -> dict[str, list[str]]:
    spec = CompositionSpec(
        title="P",
        genre=genre,
        key="D minor",
        tempo_bpm=100.0,
        time_signature="4/4",
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="strings", role="harmony"),
            InstrumentSpec(name="bass", role="bass"),
        ],
        sections=[
            SectionSpec(name="A", bars=4, dynamics="mf"),
            SectionSpec(name="B", bars=4, dynamics="mf"),
            SectionSpec(name="C", bars=4, dynamics="mf"),
            SectionSpec(name="A_prime", bars=4, dynamics="mf"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.55),
    )
    spec, _ = auto_thematic_recall(spec)
    _, plan, _ = generate_via_v2_pipeline(spec)
    by_section: dict[str, list[str]] = defaultdict(list)
    for ce in sorted(plan.harmony.chord_events, key=lambda c: c.start_beat):
        by_section[ce.section_id].append(ce.roman)
    return by_section


class TestSectionContrast:
    def test_contrasting_sections_differ(self) -> None:
        chords = _chords_by_section("pop_mainstream")
        # B and C must not be identical loops of A (the old monotony bug).
        assert chords["B"] != chords["A"] or chords["C"] != chords["A"]
        # At least one contrasting section opens on a non-tonic chord.
        assert chords["B"][0] != chords["A"][0] or chords["C"][0] != chords["A"][0]

    def test_return_section_shares_source_opening(self) -> None:
        # A_prime recalls A: their opening harmony should match (coherent return),
        # even though the final section's cadence rewrites its ending.
        chords = _chords_by_section("jazz_bebop")
        assert chords["A_prime"][0] == chords["A"][0]

    def test_progression_is_genre_idiomatic(self) -> None:
        # Jazz sections should use seventh-chord vocabulary from the palette.
        chords = _chords_by_section("jazz_bebop")
        flat = [c for cs in chords.values() for c in cs]
        assert any("7" in c for c in flat)


class TestGenreProgressionHelper:
    def test_walk_length_and_start(self) -> None:
        import random

        palette = ["Imaj7", "ii7", "V7", "vi7"]
        ngrams = {("Imaj7", "ii7"): 1.0, ("ii7", "V7"): 1.0, ("V7", "Imaj7"): 1.0}
        seq = _genre_progression(palette, ngrams, 6, "Imaj7", random.Random(1))
        assert len(seq) == 6
        assert seq[0] == "Imaj7"
        # Follows the n-gram chain deterministically here.
        assert seq[:4] == ["Imaj7", "ii7", "V7", "Imaj7"]

    def test_empty_palette_is_safe(self) -> None:
        import random

        assert _genre_progression([], {}, 4, "I", random.Random(1)) == []

    def test_contrast_start_home_is_tonic(self) -> None:
        palette = ["I", "IV", "V", "vi"]
        assert _contrast_start_chord(palette, 0) == "I"
        # Contrasting variants open elsewhere.
        assert _contrast_start_chord(palette, 1) != "I"
