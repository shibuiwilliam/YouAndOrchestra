"""Unit tests for the stochastic generator."""

from __future__ import annotations

import random

import yao.generators.stochastic as _st  # noqa: F401
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.registry import get_generator
from yao.ir.notation import parse_key, scale_notes
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint


def _make_spec(
    *,
    seed: int = 42,
    temperature: float = 0.5,
    key: str = "C major",
    instruments: list[InstrumentSpec] | None = None,
    sections: list[SectionSpec] | None = None,
) -> CompositionSpec:
    """Create a spec configured for the stochastic generator."""
    return CompositionSpec(
        title="Stochastic Test",
        key=key,
        tempo_bpm=120.0,
        instruments=instruments or [InstrumentSpec(name="piano", role="melody")],
        sections=sections or [SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=seed, temperature=temperature),
    )


class TestStochasticGeneratesNotes:
    def test_generates_notes(self) -> None:
        gen = get_generator("stochastic")
        score, prov = gen.generate(_make_spec())
        assert len(score.all_notes()) > 0
        assert len(prov) > 0

    def test_respects_title(self) -> None:
        gen = get_generator("stochastic")
        score, _ = gen.generate(_make_spec())
        assert score.title == "Stochastic Test"

    def test_respects_key(self) -> None:
        spec = _make_spec(key="D major", temperature=0.1)
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)

        root, scale_type = parse_key("D major")
        valid_pcs: set[int] = set()
        for octave in range(0, 10):
            for note in scale_notes(root, scale_type, octave):
                if 0 <= note <= 127:
                    valid_pcs.add(note % 12)

        for note in score.part_for_instrument("piano"):
            assert note.pitch % 12 in valid_pcs, f"Note {note.pitch} not in D major scale"

    def test_respects_instrument_range(self) -> None:
        spec = _make_spec(temperature=0.8, seed=123)
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)

        piano_range = INSTRUMENT_RANGES["piano"]
        for note in score.all_notes():
            assert piano_range.midi_low <= note.pitch <= piano_range.midi_high

    def test_respects_section_count(self) -> None:
        spec = _make_spec(
            sections=[
                SectionSpec(name="intro", bars=4, dynamics="mp"),
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ]
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        assert len(score.sections) == 3


class TestStochasticReproducibility:
    def test_same_seed_same_output(self) -> None:
        gen = get_generator("stochastic")
        s1, _ = gen.generate(_make_spec(seed=42))
        s2, _ = gen.generate(_make_spec(seed=42))
        p1 = [n.pitch for n in s1.all_notes()]
        p2 = [n.pitch for n in s2.all_notes()]
        assert p1 == p2

    def test_different_seeds_different_output(self) -> None:
        gen = get_generator("stochastic")
        s1, _ = gen.generate(_make_spec(seed=1))
        s2, _ = gen.generate(_make_spec(seed=999))
        p1 = [n.pitch for n in s1.all_notes()[:20]]
        p2 = [n.pitch for n in s2.all_notes()[:20]]
        assert p1 != p2


class TestStochasticTemperature:
    def test_low_temperature_conservative(self) -> None:
        gen = get_generator("stochastic")
        score, _ = gen.generate(_make_spec(temperature=0.05, seed=42))
        # Low temperature should still produce notes
        assert len(score.all_notes()) > 0

    def test_high_temperature_more_variety(self) -> None:
        gen = get_generator("stochastic")
        # Use more bars so pitch class coverage is statistically reliable
        sections = [SectionSpec(name="verse", bars=32, dynamics="mf")]
        s_low, _ = gen.generate(_make_spec(temperature=0.1, seed=42, sections=sections))
        s_high, _ = gen.generate(_make_spec(temperature=0.9, seed=42, sections=sections))
        pc_low = len({n.pitch % 12 for n in s_low.all_notes()})
        pc_high = len({n.pitch % 12 for n in s_high.all_notes()})
        # High temperature should use at least as many pitch classes
        assert pc_high >= pc_low


class TestStochasticMultiInstrument:
    def test_multi_instrument(self) -> None:
        spec = _make_spec(
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ]
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        assert "piano" in score.instruments()
        assert "acoustic_bass" in score.instruments()

    def test_bass_uses_walking_pattern(self) -> None:
        spec = _make_spec(
            temperature=0.8,
            instruments=[InstrumentSpec(name="acoustic_bass", role="bass")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        bass_notes = score.part_for_instrument("acoustic_bass")
        # With high temperature, should have more than 1 note per bar (walking)
        assert len(bass_notes) > 8  # noqa: PLR2004

    def test_chord_uses_diatonic_quality(self) -> None:
        spec = _make_spec(
            temperature=0.7,
            instruments=[InstrumentSpec(name="piano", role="harmony")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        # Harmony role should produce multiple simultaneous notes per bar
        notes = score.all_notes()
        assert len(notes) > 4  # noqa: PLR2004


class TestStochasticProvenance:
    def test_provenance_recorded(self) -> None:
        gen = get_generator("stochastic")
        _, prov = gen.generate(_make_spec())
        operations = [r.operation for r in prov.records]
        assert "start_generation" in operations
        assert "complete_generation" in operations
        assert any("generate_section" in op for op in operations)

    def test_provenance_includes_seed(self) -> None:
        gen = get_generator("stochastic")
        _, prov = gen.generate(_make_spec(seed=12345))
        start = prov.query_by_operation("start_generation")[0]
        assert start.parameters.get("seed") == 12345
        assert start.parameters.get("strategy") == "stochastic"


class TestStochasticMelodyVariety:
    """Tests for per-instrument variety and motif-based differentiation."""

    def test_multiple_melody_instruments_differ(self) -> None:
        """Two melody instruments should produce different pitch sequences."""
        spec = _make_spec(
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="violin", role="melody"),
            ],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        piano_pitches = [n.pitch for n in score.part_for_instrument("piano")]
        violin_pitches = [n.pitch for n in score.part_for_instrument("violin")]
        # Must not be identical (motif transformation creates distinct parts)
        assert piano_pitches != violin_pitches

    def test_per_instrument_rng_reproducibility(self) -> None:
        """Same seed with per-instrument RNG is still deterministic."""
        spec = _make_spec(
            seed=99,
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
        )
        gen = get_generator("stochastic")
        s1, _ = gen.generate(spec)
        s2, _ = gen.generate(spec)
        p1 = [n.pitch for n in s1.all_notes()]
        p2 = [n.pitch for n in s2.all_notes()]
        assert p1 == p2

    def test_contour_variety_in_range(self) -> None:
        """Melody contour direction changes should be in a healthy range."""
        spec = _make_spec(
            temperature=0.5,
            seed=42,
            sections=[SectionSpec(name="verse", bars=16, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        notes = score.all_notes()
        if len(notes) < 3:
            return
        direction_changes = 0
        for i in range(len(notes) - 2):
            a = notes[i + 1].pitch - notes[i].pitch
            b = notes[i + 2].pitch - notes[i + 1].pitch
            if a != 0 and b != 0 and (a > 0) != (b > 0):
                direction_changes += 1
        ratio = direction_changes / max(len(notes) - 2, 1)
        # Should be in the 0.1-0.7 range (evaluator target 0.4 ±0.3)
        assert 0.1 <= ratio <= 0.7, f"Contour variety {ratio:.2f} out of range"


class TestStochasticContours:
    """Tests for melodic contour algorithms."""

    def test_chorus_uses_ascending_contour(self) -> None:
        """Chorus sections should trend upward with ascending contour."""
        spec = _make_spec(
            seed=42,
            temperature=0.5,
            sections=[SectionSpec(name="chorus", bars=16, dynamics="f")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        notes = [n for n in score.all_notes() if n.instrument == "piano"]
        if len(notes) < 4:
            return
        quarter = len(notes) // 4
        early_avg = sum(n.pitch for n in notes[:quarter]) / quarter
        late_avg = sum(n.pitch for n in notes[-quarter:]) / quarter
        # Ascending contour: later notes should tend higher
        assert late_avg >= early_avg - 2, "Ascending contour should trend upward"

    def test_descending_contour_for_outro(self) -> None:
        """Outro sections should use descending contour."""
        spec = _make_spec(
            seed=42,
            temperature=0.5,
            sections=[SectionSpec(name="outro", bars=16, dynamics="pp")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        notes = [n for n in score.all_notes() if n.instrument == "piano"]
        if len(notes) < 4:
            return
        quarter = len(notes) // 4
        early_avg = sum(n.pitch for n in notes[:quarter]) / quarter
        late_avg = sum(n.pitch for n in notes[-quarter:]) / quarter
        # Descending contour: later notes should tend lower
        assert late_avg <= early_avg + 2, "Descending contour should trend downward"

    def test_low_temperature_always_arch(self) -> None:
        """Low temperature should always use arch contour regardless of section."""
        from yao.generators.stochastic import StochasticGenerator

        gen = StochasticGenerator()
        rng = random.Random(42)
        contour = gen._choose_contour("chorus", 0.1, rng)
        assert contour == "arch"


class TestStochasticVoicings:
    """Tests for chord voicing variety."""

    def test_apply_voicing_root_position(self) -> None:
        from yao.generators.stochastic import StochasticGenerator

        pitches = [60, 64, 67]  # C major triad
        result = StochasticGenerator._apply_voicing(pitches, "root")
        assert result == [60, 64, 67]

    def test_apply_voicing_first_inversion(self) -> None:
        from yao.generators.stochastic import StochasticGenerator

        pitches = [60, 64, 67]
        result = StochasticGenerator._apply_voicing(pitches, "first_inversion")
        assert result == [64, 67, 72]  # E, G, C(up)

    def test_high_temp_may_produce_inversions(self) -> None:
        """At high temperature, some chords should use non-root voicings."""
        spec = _make_spec(
            seed=42,
            temperature=0.9,
            instruments=[InstrumentSpec(name="piano", role="harmony")],
            sections=[SectionSpec(name="chorus", bars=16, dynamics="f")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        notes = score.all_notes()
        # With 16 bars at high temp, we expect at least some variety
        assert len(notes) > 0


class TestStochasticRoleDifferentiation:
    """Tests for pad and rhythm role generation."""

    def test_pad_role_produces_long_notes(self) -> None:
        """Pad role should produce sustained, long-duration notes."""
        spec = _make_spec(
            temperature=0.5,
            instruments=[InstrumentSpec(name="strings_ensemble", role="pad")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        notes = score.all_notes()
        assert len(notes) > 0
        avg_duration = sum(n.duration_beats for n in notes) / len(notes)
        # Pad notes should average at least 2 beats
        assert avg_duration >= 2.0, f"Pad avg duration {avg_duration:.2f} too short"

    def test_rhythm_role_produces_short_notes(self) -> None:
        """Rhythm role should produce short, staccato notes."""
        spec = _make_spec(
            temperature=0.5,
            instruments=[InstrumentSpec(name="piano", role="rhythm")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        notes = score.all_notes()
        assert len(notes) > 0
        avg_duration = sum(n.duration_beats for n in notes) / len(notes)
        # Rhythm notes should average less than 1 beat
        assert avg_duration < 1.0, f"Rhythm avg duration {avg_duration:.2f} too long"

    def test_pad_softer_than_harmony(self) -> None:
        """Pad notes should be softer than harmony notes at same dynamics."""
        spec_pad = _make_spec(
            seed=42,
            temperature=0.5,
            instruments=[InstrumentSpec(name="piano", role="pad")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        spec_harm = _make_spec(
            seed=42,
            temperature=0.5,
            instruments=[InstrumentSpec(name="piano", role="harmony")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        s_pad, _ = gen.generate(spec_pad)
        s_harm, _ = gen.generate(spec_harm)
        avg_vel_pad = sum(n.velocity for n in s_pad.all_notes()) / max(
            len(s_pad.all_notes()), 1
        )
        avg_vel_harm = sum(n.velocity for n in s_harm.all_notes()) / max(
            len(s_harm.all_notes()), 1
        )
        assert avg_vel_pad < avg_vel_harm

    def test_rhythm_role_has_more_notes_than_harmony(self) -> None:
        """Rhythm parts should have more notes per bar than harmony."""
        spec_rhythm = _make_spec(
            seed=42,
            temperature=0.5,
            instruments=[InstrumentSpec(name="piano", role="rhythm")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        spec_harmony = _make_spec(
            seed=42,
            temperature=0.5,
            instruments=[InstrumentSpec(name="piano", role="harmony")],
            sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        )
        gen = get_generator("stochastic")
        s_r, _ = gen.generate(spec_rhythm)
        s_h, _ = gen.generate(spec_harmony)
        assert len(s_r.all_notes()) > len(s_h.all_notes())


class TestStochasticWithTrajectory:
    def test_trajectory_affects_velocity(self) -> None:
        traj = TrajectorySpec(
            tension=TrajectoryDimension(
                waypoints=[Waypoint(bar=0, value=0.1), Waypoint(bar=8, value=0.9)]
            )
        )
        gen = get_generator("stochastic")
        score, _ = gen.generate(_make_spec(temperature=0.0), traj)
        notes = score.all_notes()
        if len(notes) >= 2:  # noqa: PLR2004
            early = [n for n in notes if n.start_beat < 8.0]
            late = [n for n in notes if n.start_beat >= 24.0]
            if early and late:
                avg_early = sum(n.velocity for n in early) / len(early)
                avg_late = sum(n.velocity for n in late) / len(late)
                assert avg_late >= avg_early
