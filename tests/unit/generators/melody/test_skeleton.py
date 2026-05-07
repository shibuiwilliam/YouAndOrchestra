"""Tests for Layer M2: SkeletonGenerator."""

from __future__ import annotations

import pytest

from yao.generators.melody.motif_developer import MotifDevelopmentPlanner
from yao.generators.melody.skeleton import SkeletonGenerator
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
    """Create a minimal CompositionSpec."""
    if sections is None:
        sections = [("verse", 8)]
    return CompositionSpec(
        title="Test",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=b) for n, b in sections],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


def _get_plan(spec: CompositionSpec, profile_name: str) -> tuple:
    """Helper to get phrase plan, profile, and provenance."""
    profile = load_melodic_profile(profile_name)
    prov = ProvenanceLog()
    planner = MotifDevelopmentPlanner()
    plan = planner.plan(spec, profile, prov)
    return plan, profile, prov


class TestSkeletonGenerator:
    """Tests for the M2 skeleton generator."""

    def test_basic_generation(self) -> None:
        """Skeleton generates notes for all phrases."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, "bebop_jazz")
        gen = SkeletonGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        assert skeleton.note_count > 0
        assert skeleton.pitch_range[0] > 0
        assert skeleton.pitch_range[1] <= 127

    def test_notes_cover_phrase_bars(self) -> None:
        """Skeleton has at least one note per phrase."""
        spec = _make_spec(sections=[("verse", 8)])
        plan, profile, prov = _get_plan(spec, "classical_romantic")
        gen = SkeletonGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        # Each phrase should have at least one note
        phrase_indices = {n.phrase_id for n in skeleton.notes}
        assert len(phrase_indices) == len(plan.phrases)

    def test_chord_tone_targeting(self) -> None:
        """High chord-tone-targeting profile produces mostly chord tones."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, "j_pop_ballad")
        gen = SkeletonGenerator()

        # J-pop has chord_tone_targeting=0.75
        skeleton = gen.generate(plan, spec, profile, prov)

        chord_tones = sum(1 for n in skeleton.notes if n.chord_relation in ("root", "3rd", "5th", "7th"))
        ratio = chord_tones / skeleton.note_count if skeleton.note_count > 0 else 0
        # Should be reasonably high (> 0.3) given high targeting
        assert ratio > 0.3

    def test_with_harmonic_contexts(self) -> None:
        """Skeleton generation works with explicit harmonic contexts."""
        spec = _make_spec(sections=[("verse", 4)])
        plan, profile, prov = _get_plan(spec, "bebop_jazz")

        contexts = [
            HarmonicContext(bar=0, beat=0.0, chord_root="C", chord_quality="maj7"),
            HarmonicContext(bar=1, beat=0.0, chord_root="F", chord_quality="maj7"),
            HarmonicContext(bar=2, beat=0.0, chord_root="G", chord_quality="dom7"),
            HarmonicContext(bar=3, beat=0.0, chord_root="C", chord_quality="maj7"),
        ]

        gen = SkeletonGenerator()
        skeleton = gen.generate(plan, spec, profile, prov, harmonic_contexts=contexts)

        assert skeleton.note_count > 0

    def test_provenance_recorded(self) -> None:
        """M2 records provenance with correct layer tag."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, "rock_classic")
        gen = SkeletonGenerator()

        gen.generate(plan, spec, profile, prov)

        m2_records = [r for r in prov.records if r.layer == "M2_skeleton"]
        assert len(m2_records) >= 1
        assert m2_records[0].agent == "composer-subagent"

    def test_seed_reproducibility(self) -> None:
        """Same seed produces the same skeleton."""
        spec = _make_spec(seed=99)
        plan, profile, prov1 = _get_plan(spec, "lofi_hiphop")
        gen = SkeletonGenerator()

        skel1 = gen.generate(plan, spec, profile, prov1)

        _, _, prov2 = _get_plan(spec, "lofi_hiphop")
        skel2 = gen.generate(plan, spec, profile, prov2)

        assert skel1.note_count == skel2.note_count
        for n1, n2 in zip(skel1.notes, skel2.notes, strict=False):
            assert n1.midi_pitch == n2.midi_pitch
            assert n1.bar == n2.bar

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_skeleton_for_each_genre(self, genre: str) -> None:
        """Each Tier-1 genre produces a valid skeleton."""
        spec = _make_spec()
        plan, profile, prov = _get_plan(spec, genre)
        gen = SkeletonGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        assert skeleton.note_count > 0
        # All pitches in valid MIDI range
        for note in skeleton.notes:
            assert 0 <= note.midi_pitch <= 127

    def test_target_pitches_recorded(self) -> None:
        """Target pitches dict is populated."""
        spec = _make_spec(sections=[("verse", 8)])
        plan, profile, prov = _get_plan(spec, "classical_romantic")
        gen = SkeletonGenerator()

        skeleton = gen.generate(plan, spec, profile, prov)

        assert len(skeleton.target_pitches) > 0
