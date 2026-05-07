"""Tests for Layer M3: SurfaceRealizer."""

from __future__ import annotations

import pytest

from yao.generators.melody.motif_developer import MotifDevelopmentPlanner
from yao.generators.melody.skeleton import SkeletonGenerator
from yao.generators.melody.surface import SurfaceRealizer
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.melodic_profile import load_melodic_profile

TIER_1_GENRES = ["bebop_jazz", "j_pop_ballad", "classical_romantic", "lofi_hiphop", "rock_classic"]


def _make_spec(
    *,
    sections: list[tuple[str, int]] | None = None,
    seed: int = 42,
) -> CompositionSpec:
    """Create a minimal CompositionSpec."""
    if sections is None:
        sections = [("verse", 8)]
    return CompositionSpec(
        title="Test",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=b) for n, b in sections],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


def _get_skeleton(spec, genre):
    """Helper to run M1+M2 and get skeleton."""
    profile = load_melodic_profile(genre)
    prov = ProvenanceLog()
    plan = MotifDevelopmentPlanner().plan(spec, profile, prov)
    skeleton = SkeletonGenerator().generate(plan, spec, profile, prov)
    return skeleton, profile, prov


class TestSurfaceRealizer:
    """Tests for the M3 surface realizer."""

    def test_basic_realization(self) -> None:
        """Surface produces more notes than skeleton."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, "bebop_jazz")
        realizer = SurfaceRealizer()

        melody = realizer.realize(skeleton, spec, profile, prov)

        assert melody.note_count >= skeleton.note_count

    def test_surface_includes_chord_tones(self) -> None:
        """Surface melody includes chord_tone notes from skeleton."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, "classical_romantic")
        realizer = SurfaceRealizer()

        melody = realizer.realize(skeleton, spec, profile, prov)

        chord_tones = [n for n in melody.notes if n.note_type == "chord_tone"]
        assert len(chord_tones) >= skeleton.note_count

    def test_surface_has_fill_notes(self) -> None:
        """Surface melody has passing/neighbor/other fill notes."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, "bebop_jazz")
        realizer = SurfaceRealizer()

        melody = realizer.realize(skeleton, spec, profile, prov)

        fill_types = {"passing", "neighbor", "appoggiatura", "escape", "anticipation"}
        fills = [n for n in melody.notes if n.note_type in fill_types]
        # With 8 bars of bebop, there should be some fills
        assert len(fills) > 0

    def test_notes_in_valid_range(self) -> None:
        """All surface notes are in valid MIDI range."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, "rock_classic")
        realizer = SurfaceRealizer()

        melody = realizer.realize(skeleton, spec, profile, prov)

        for note in melody.notes:
            assert 0 <= note.midi_pitch <= 127
            assert note.velocity > 0
            assert note.duration_beats > 0

    def test_provenance_recorded(self) -> None:
        """M3 records provenance with correct layer tag."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, "j_pop_ballad")
        realizer = SurfaceRealizer()

        realizer.realize(skeleton, spec, profile, prov)

        m3_records = [r for r in prov.records if r.layer == "M3_surface"]
        assert len(m3_records) >= 1
        assert m3_records[0].agent == "composer-subagent"

    def test_seed_reproducibility(self) -> None:
        """Same seed produces the same surface."""
        spec = _make_spec(seed=77)
        skeleton, profile, prov1 = _get_skeleton(spec, "lofi_hiphop")
        r = SurfaceRealizer()

        mel1 = r.realize(skeleton, spec, profile, prov1)

        _, _, prov2 = _get_skeleton(spec, "lofi_hiphop")
        mel2 = r.realize(skeleton, spec, profile, prov2)

        assert mel1.note_count == mel2.note_count

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_surface_for_each_genre(self, genre: str) -> None:
        """Each Tier-1 genre produces a valid surface."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, genre)
        realizer = SurfaceRealizer()

        melody = realizer.realize(skeleton, spec, profile, prov)

        assert melody.note_count > 0
        for note in melody.notes:
            assert 0 <= note.midi_pitch <= 127

    def test_notes_sorted_by_position(self) -> None:
        """Output notes are sorted by (bar, beat)."""
        spec = _make_spec()
        skeleton, profile, prov = _get_skeleton(spec, "classical_romantic")
        realizer = SurfaceRealizer()

        melody = realizer.realize(skeleton, spec, profile, prov)

        for i in range(1, len(melody.notes)):
            prev = melody.notes[i - 1]
            curr = melody.notes[i]
            assert (curr.bar, curr.beat) >= (prev.bar, prev.beat)
