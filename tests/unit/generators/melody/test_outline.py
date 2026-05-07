"""Tests for OutlineGenerator — chord-progression-outlining skeleton."""

from __future__ import annotations

import pytest

from yao.generators.melody.motif_developer import MotifDevelopmentPlanner
from yao.generators.melody.outline import OutlineGenerator
from yao.ir.harmonic_context import HarmonicContext
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


def _get_plan(spec, genre):
    profile = load_melodic_profile(genre)
    prov = ProvenanceLog()
    plan = MotifDevelopmentPlanner().plan(spec, profile, prov)
    return plan, profile, prov


class TestOutlineGenerator:
    """Tests for the OutlineGenerator."""

    def test_basic_outline(self) -> None:
        """Outline generator produces skeleton notes."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, "bebop_jazz")
        gen = OutlineGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        assert skeleton.note_count > 0

    def test_chord_tone_ratio_high_for_bebop(self) -> None:
        """Bebop (chord_tone_targeting=0.6) produces high chord-tone ratio."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, "bebop_jazz")
        gen = OutlineGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        ct_count = sum(1 for n in skeleton.notes if n.chord_relation in ("root", "3rd", "5th", "7th"))
        ratio = ct_count / skeleton.note_count if skeleton.note_count > 0 else 0
        assert ratio > 0.3

    def test_with_explicit_harmony(self) -> None:
        """Outline works with explicit harmonic contexts."""
        spec = _make_spec(sections=[("verse", 4)])
        plan, profile, prov = _get_plan(spec, "classical_romantic")

        contexts = [
            HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj", next_chord_root="G"),
            HarmonicContext(bar=1, beat=0.0, chord_root="G", chord_quality="dom7", next_chord_root="A"),
            HarmonicContext(bar=2, beat=0.0, chord_root="A", chord_quality="min", next_chord_root="F"),
            HarmonicContext(bar=3, beat=0.0, chord_root="F", chord_quality="maj", next_chord_root="C"),
        ]

        gen = OutlineGenerator()
        skeleton = gen.generate(plan, spec, profile, prov, harmonic_contexts=contexts)

        assert skeleton.note_count >= 4  # at least one note per bar

    def test_provenance_recorded(self) -> None:
        """Outline records provenance with M2_skeleton layer."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, "rock_classic")
        gen = OutlineGenerator()

        gen.generate(plan, spec, profile, prov)

        m2_records = [r for r in prov.records if r.layer == "M2_skeleton"]
        assert len(m2_records) >= 1

    def test_phrase_start_and_cadence_roles(self) -> None:
        """Output has phrase_start and cadence_target structural roles."""
        spec = _make_spec(sections=[("verse", 8)])
        plan, profile, prov = _get_plan(spec, "j_pop_ballad")
        gen = OutlineGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        roles = {n.structural_role for n in skeleton.notes}
        assert "phrase_start" in roles
        assert "cadence_target" in roles

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_outline_for_each_genre(self, genre: str) -> None:
        """Each Tier-1 genre produces valid outline."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, genre)
        gen = OutlineGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        assert skeleton.note_count > 0
        for note in skeleton.notes:
            assert 0 <= note.midi_pitch <= 127

    def test_seed_reproducibility(self) -> None:
        """Same seed produces same outline."""
        spec = _make_spec(seed=88)
        plan, profile, prov1 = _get_plan(spec, "lofi_hiphop")
        gen = OutlineGenerator()

        s1 = gen.generate(plan, spec, profile, prov1)

        _, _, prov2 = _get_plan(spec, "lofi_hiphop")
        s2 = gen.generate(plan, spec, profile, prov2)

        assert s1.note_count == s2.note_count
        for n1, n2 in zip(s1.notes, s2.notes, strict=False):
            assert n1.midi_pitch == n2.midi_pitch
