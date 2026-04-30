"""Musical scenario tests — prove that the system produces musically meaningful output.

These tests go beyond mechanical correctness (notes in range, valid MIDI)
to verify that the generation pipeline produces music with the properties
promised by the spec (PROJECT_IMPROVEMENT §3.2).
"""

from __future__ import annotations

import pytest

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.registry import get_generator
from yao.ir.timing import bars_to_beats
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint
from yao.verify.evaluator import evaluate_score


class TestTensionArcCreatesClimax:
    """A trajectory with rising tension should produce denser, louder notes at peak."""

    def test_climax_is_louder_than_intro(self) -> None:
        spec = CompositionSpec(
            title="Tension Arc Test",
            key="C major",
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="intro", bars=8, dynamics="mp"),
                SectionSpec(name="climax", bars=8, dynamics="ff"),
                SectionSpec(name="outro", bars=8, dynamics="pp"),
            ],
        )
        traj = TrajectorySpec(
            tension=TrajectoryDimension(
                waypoints=[
                    Waypoint(bar=0, value=0.1),
                    Waypoint(bar=8, value=0.5),
                    Waypoint(bar=16, value=1.0),
                    Waypoint(bar=24, value=0.2),
                ]
            )
        )

        gen = get_generator("rule_based")
        score, _ = gen.generate(spec, traj)

        # Collect average velocity per section
        notes = score.all_notes()
        intro_notes = [n for n in notes if n.start_beat < bars_to_beats(8)]
        climax_notes = [n for n in notes if bars_to_beats(8) <= n.start_beat < bars_to_beats(16)]
        outro_notes = [n for n in notes if n.start_beat >= bars_to_beats(16)]

        avg_intro = sum(n.velocity for n in intro_notes) / max(len(intro_notes), 1)
        avg_climax = sum(n.velocity for n in climax_notes) / max(len(climax_notes), 1)
        avg_outro = sum(n.velocity for n in outro_notes) / max(len(outro_notes), 1)

        assert avg_climax > avg_intro, f"Climax ({avg_climax:.0f}) should be louder than intro ({avg_intro:.0f})"
        assert avg_climax > avg_outro, f"Climax ({avg_climax:.0f}) should be louder than outro ({avg_outro:.0f})"


class TestDifferentSpecsProduceDifferentMusic:
    """Different keys, tempos, and dynamics should produce meaningfully different output."""

    def test_different_keys(self) -> None:
        base = dict(
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        score_c = get_generator("rule_based").generate(CompositionSpec(title="C Major", key="C major", **base))[0]
        score_g = get_generator("rule_based").generate(CompositionSpec(title="G Major", key="G major", **base))[0]

        pitches_c = {n.pitch % 12 for n in score_c.all_notes()}
        pitches_g = {n.pitch % 12 for n in score_g.all_notes()}

        # Different keys should produce different pitch class sets
        assert pitches_c != pitches_g, "Different keys should use different pitch classes"

    def test_different_dynamics_affect_velocity(self) -> None:
        base = dict(
            key="C major",
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
        )
        score_pp = get_generator("rule_based").generate(
            CompositionSpec(
                title="Soft",
                sections=[SectionSpec(name="v", bars=8, dynamics="pp")],
                **base,
            )
        )[0]
        score_ff = get_generator("rule_based").generate(
            CompositionSpec(
                title="Loud",
                sections=[SectionSpec(name="v", bars=8, dynamics="ff")],
                **base,
            )
        )[0]

        avg_pp = sum(n.velocity for n in score_pp.all_notes()) / len(score_pp.all_notes())
        avg_ff = sum(n.velocity for n in score_ff.all_notes()) / len(score_ff.all_notes())

        assert avg_ff > avg_pp + 30, f"ff ({avg_ff:.0f}) should be much louder than pp ({avg_pp:.0f})"


class TestStochasticVariation:
    """Different seeds should produce different compositions from the same spec."""

    def test_different_seeds_different_output(self) -> None:
        spec_seed1 = CompositionSpec(
            title="Seed 1",
            key="C major",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="stochastic", seed=1, temperature=0.7),
        )
        spec_seed2 = CompositionSpec(
            title="Seed 2",
            key="C major",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="stochastic", seed=999, temperature=0.7),
        )

        score1, _ = get_generator("stochastic").generate(spec_seed1)
        score2, _ = get_generator("stochastic").generate(spec_seed2)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()

        # Different seeds must produce different pitch sequences
        pitches1 = [n.pitch for n in notes1[:20]]
        pitches2 = [n.pitch for n in notes2[:20]]
        assert pitches1 != pitches2, "Different seeds should produce different melodies"

    def test_same_seed_same_output(self) -> None:
        spec = CompositionSpec(
            title="Reproducible",
            key="C major",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        score1, _ = get_generator("stochastic").generate(spec)
        score2, _ = get_generator("stochastic").generate(spec)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()
        assert len(notes1) == len(notes2)

        pitches1 = [n.pitch for n in notes1]
        pitches2 = [n.pitch for n in notes2]
        assert pitches1 == pitches2, "Same seed should produce identical output"

    def test_temperature_affects_variety(self) -> None:
        base = dict(
            title="Temp Test",
            key="C major",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=16, dynamics="mf")],
        )

        spec_low = CompositionSpec(
            **base,
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.1),
        )
        spec_high = CompositionSpec(
            **base,
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.9),
        )

        score_low, _ = get_generator("stochastic").generate(spec_low)
        score_high, _ = get_generator("stochastic").generate(spec_high)

        # Higher temperature → more pitch class variety
        pcs_low = len({n.pitch % 12 for n in score_low.all_notes()})
        pcs_high = len({n.pitch % 12 for n in score_high.all_notes()})

        assert pcs_high >= pcs_low, f"High temp ({pcs_high} PCs) should have >= variety than low temp ({pcs_low} PCs)"


class TestGeneratorRegistry:
    """Generator registry works correctly."""

    def test_rule_based_registered(self) -> None:
        gen = get_generator("rule_based")
        assert gen is not None

    def test_stochastic_registered(self) -> None:
        gen = get_generator("stochastic")
        assert gen is not None

    def test_unknown_generator_raises(self) -> None:
        from yao.errors import SpecValidationError

        with pytest.raises(SpecValidationError, match="Unknown generator"):
            get_generator("nonexistent")


class TestEvaluationProvesMusicality:
    """Evaluation metrics should detect quality differences."""

    def test_multi_instrument_scores_higher_variety(self) -> None:
        single = CompositionSpec(
            title="Single",
            key="C major",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=8)],
        )
        multi = CompositionSpec(
            title="Multi",
            key="C major",
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
            sections=[SectionSpec(name="verse", bars=8)],
        )

        score_s, _ = get_generator("rule_based").generate(single)
        score_m, _ = get_generator("rule_based").generate(multi)

        eval_s = evaluate_score(score_s, single)
        eval_m = evaluate_score(score_m, multi)

        # Multi-instrument should use more pitch classes
        pc_s = next(s for s in eval_s.scores if s.metric == "pitch_class_variety")
        pc_m = next(s for s in eval_m.scores if s.metric == "pitch_class_variety")

        assert pc_m.score >= pc_s.score, (
            f"Multi-instrument ({pc_m.score:.2f}) should have >= pitch variety than single ({pc_s.score:.2f})"
        )
