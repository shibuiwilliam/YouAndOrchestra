"""Tests for Layer M4: OrnamentEngine."""

from __future__ import annotations

import pytest

from yao.generators.melody.motif_developer import MotifDevelopmentPlanner
from yao.generators.melody.ornament import OrnamentEngine
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
    if sections is None:
        sections = [("verse", 8)]
    return CompositionSpec(
        title="Test",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=b) for n, b in sections],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


def _get_melody(spec, genre):
    """Helper to run M1+M2+M3."""
    profile = load_melodic_profile(genre)
    prov = ProvenanceLog()
    plan = MotifDevelopmentPlanner().plan(spec, profile, prov)
    skeleton = SkeletonGenerator().generate(plan, spec, profile, prov)
    melody = SurfaceRealizer().realize(skeleton, spec, profile, prov)
    return melody, profile, prov


class TestOrnamentEngine:
    """Tests for the M4 ornament engine."""

    def test_basic_application(self) -> None:
        """Ornament engine produces OrnamentedMelodyLine."""
        spec = _make_spec()
        melody, profile, prov = _get_melody(spec, "bebop_jazz")
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        assert result.note_count == melody.note_count

    def test_ornaments_applied(self) -> None:
        """Some notes should have ornaments (bebop has non-zero probabilities)."""
        spec = _make_spec(sections=[("verse", 16)])
        melody, profile, prov = _get_melody(spec, "bebop_jazz")
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        ornamented = [n for n in result.notes if len(n.ornaments) > 0]
        # Bebop has grace_note=0.15, bend=0.05, slide=0.10 — should get some
        assert len(ornamented) > 0

    def test_articulation_from_profile(self) -> None:
        """Articulation distribution reflects the profile ratios."""
        spec = _make_spec(sections=[("verse", 16)])
        melody, profile, prov = _get_melody(spec, "j_pop_ballad")
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        legato_count = sum(1 for n in result.notes if n.articulation == "legato")
        # J-pop has legato_ratio=0.85
        ratio = legato_count / result.note_count if result.note_count > 0 else 0
        assert ratio > 0.5  # should be mostly legato

    def test_jazz_swing_groove(self) -> None:
        """Jazz swing groove applies non-zero timing offsets."""
        spec = _make_spec()
        melody, profile, prov = _get_melody(spec, "bebop_jazz")
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        # Bebop uses jazz_swing groove — some notes should have timing offsets
        has_offset = any(n.micro_timing_offset_ms != 0.0 for n in result.notes)
        assert has_offset

    def test_straight_groove_no_timing(self) -> None:
        """Straight groove has no timing offsets."""
        spec = _make_spec()
        melody, profile, prov = _get_melody(spec, "classical_romantic")
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        # Classical uses straight groove
        all_zero = all(n.micro_timing_offset_ms == 0.0 for n in result.notes)
        assert all_zero

    def test_provenance_recorded(self) -> None:
        """M4 records provenance with correct layer tag."""
        spec = _make_spec()
        melody, profile, prov = _get_melody(spec, "rock_classic")
        engine = OrnamentEngine()

        engine.apply(melody, profile, prov)

        m4_records = [r for r in prov.records if r.layer == "M4_ornament"]
        assert len(m4_records) >= 1
        assert m4_records[0].agent == "composer-subagent"

    def test_effective_velocity_clamped(self) -> None:
        """Effective velocity is clamped to [0, 127]."""
        spec = _make_spec()
        melody, profile, prov = _get_melody(spec, "bebop_jazz")
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        for note in result.notes:
            assert 0 <= note.effective_velocity <= 127

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_ornament_for_each_genre(self, genre: str) -> None:
        """Each Tier-1 genre produces valid ornamented output."""
        spec = _make_spec()
        melody, profile, prov = _get_melody(spec, genre)
        engine = OrnamentEngine()

        result = engine.apply(melody, profile, prov)

        assert result.note_count > 0
        for note in result.notes:
            assert 0 <= note.midi_pitch <= 127
            assert note.articulation in ("legato", "staccato", "accent", "normal")

    def test_ghost_notes_in_lofi(self) -> None:
        """Lo-fi profile has ghost_note_probability > 0."""
        profile = load_melodic_profile("lofi_hiphop")
        assert profile.ornament_profile.ghost_note_probability > 0

    def test_classical_trills(self) -> None:
        """Classical Romantic profile has trill probability > 0."""
        spec = _make_spec(sections=[("verse", 16)])
        melody, profile, prov = _get_melody(spec, "classical_romantic")
        engine = OrnamentEngine()

        engine.apply(melody, profile, prov)

        # Verify the profile has trill probability configured
        assert profile.ornament_profile.trill_probability > 0
