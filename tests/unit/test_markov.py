"""Unit tests for the Markov chain generator."""

from __future__ import annotations

import yao.generators.markov as _mk  # noqa: F401
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.markov import _load_model, _temperature_scale
from yao.generators.registry import get_generator
from yao.ir.notation import parse_key, scale_notes
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec


def _make_spec(
    *,
    seed: int = 42,
    temperature: float = 0.5,
    key: str = "C major",
    instruments: list[InstrumentSpec] | None = None,
    sections: list[SectionSpec] | None = None,
) -> CompositionSpec:
    """Create a spec for the markov generator."""
    return CompositionSpec(
        title="Markov Test",
        key=key,
        tempo_bpm=120.0,
        instruments=instruments or [InstrumentSpec(name="piano", role="melody")],
        sections=sections or [SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="markov", seed=seed, temperature=temperature),
    )


class TestMarkovGeneratesNotes:
    def test_generates_notes(self) -> None:
        gen = get_generator("markov")
        score, prov = gen.generate(_make_spec())
        assert len(score.all_notes()) > 0
        assert len(prov) > 0

    def test_respects_title(self) -> None:
        gen = get_generator("markov")
        score, _ = gen.generate(_make_spec())
        assert score.title == "Markov Test"

    def test_respects_key(self) -> None:
        spec = _make_spec(key="D major", temperature=0.1)
        gen = get_generator("markov")
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
        gen = get_generator("markov")
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
        gen = get_generator("markov")
        score, _ = gen.generate(spec)
        assert len(score.sections) == 3

    def test_respects_bar_count(self) -> None:
        spec = _make_spec(sections=[SectionSpec(name="verse", bars=16, dynamics="mf")])
        gen = get_generator("markov")
        score, _ = gen.generate(spec)
        assert score.total_bars() == 16


class TestMarkovReproducibility:
    def test_same_seed_same_output(self) -> None:
        gen = get_generator("markov")
        s1, _ = gen.generate(_make_spec(seed=42))
        s2, _ = gen.generate(_make_spec(seed=42))
        p1 = [n.pitch for n in s1.all_notes()]
        p2 = [n.pitch for n in s2.all_notes()]
        assert p1 == p2

    def test_different_seeds_different_output(self) -> None:
        gen = get_generator("markov")
        s1, _ = gen.generate(_make_spec(seed=1))
        s2, _ = gen.generate(_make_spec(seed=999))
        p1 = [n.pitch for n in s1.all_notes()]
        p2 = [n.pitch for n in s2.all_notes()]
        assert p1 != p2


class TestMarkovNGramOrder:
    def test_model_loads_with_correct_order(self) -> None:
        model = _load_model("diatonic_bigram")
        assert model.n_gram_order == 2
        assert model.num_degrees == 7

    def test_pentatonic_model_has_5_degrees(self) -> None:
        model = _load_model("pentatonic_bigram")
        assert model.n_gram_order == 2
        assert model.num_degrees == 5

    def test_pentatonic_selected_for_pentatonic_key(self) -> None:
        spec = _make_spec(key="C pentatonic_major", temperature=0.5)
        gen = get_generator("markov")
        score, prov = gen.generate(spec)
        # Should use pentatonic model — check provenance
        found = False
        for rec in prov.records:
            params = rec.parameters or {}
            if params.get("model_name") == "pentatonic_bigram":
                found = True
                break
        assert found, "Expected pentatonic_bigram model in provenance"


class TestMarkovTemperature:
    def test_low_temperature_conservative(self) -> None:
        """Low temperature should produce less pitch variety."""
        gen = get_generator("markov")
        s_low, _ = gen.generate(_make_spec(seed=42, temperature=0.05))
        s_high, _ = gen.generate(_make_spec(seed=42, temperature=0.9))

        pcs_low = len({n.pitch % 12 for n in s_low.all_notes()})
        pcs_high = len({n.pitch % 12 for n in s_high.all_notes()})
        # Low temperature should use fewer distinct pitch classes
        assert pcs_low <= pcs_high

    def test_temperature_scale_sharpens(self) -> None:
        """Temperature scaling should make the argmax probability higher."""
        probs = {0: 0.3, 1: 0.2, 2: 0.5}
        cold = _temperature_scale(probs, 0.1)
        warm = _temperature_scale(probs, 1.0)
        # Cold distribution should have higher max probability
        assert max(cold.values()) >= max(warm.values())


class TestMarkovProvenance:
    def test_provenance_has_required_fields(self) -> None:
        gen = get_generator("markov")
        _, prov = gen.generate(_make_spec())

        # Find the start_generation record
        start_rec = None
        for rec in prov.records:
            if rec.operation == "start_generation":
                start_rec = rec
                break
        assert start_rec is not None, "Missing start_generation provenance record"

        params = start_rec.parameters or {}
        assert params["strategy"] == "markov"
        assert "seed" in params
        assert "n_gram_order" in params
        assert "model_name" in params

    def test_provenance_has_section_records(self) -> None:
        gen = get_generator("markov")
        _, prov = gen.generate(_make_spec())

        section_recs = [r for r in prov.records if r.operation == "generate_section"]
        assert len(section_recs) >= 1


class TestMarkovTrajectoryCoupling:
    def test_high_tension_wider_pitch_range(self) -> None:
        """Higher tension should produce wider pitch range (more leaps)."""
        gen = get_generator("markov")

        low_traj = TrajectorySpec(tension=TrajectoryDimension(type="linear", target=0.2, waypoints=[]))
        high_traj = TrajectorySpec(tension=TrajectoryDimension(type="linear", target=0.8, waypoints=[]))

        s_low, _ = gen.generate(_make_spec(seed=42, temperature=0.5), trajectory=low_traj)
        s_high, _ = gen.generate(_make_spec(seed=42, temperature=0.5), trajectory=high_traj)

        notes_low = s_low.all_notes()
        notes_high = s_high.all_notes()
        if notes_low and notes_high:
            range_low = max(n.pitch for n in notes_low) - min(n.pitch for n in notes_low)
            range_high = max(n.pitch for n in notes_high) - min(n.pitch for n in notes_high)
            # High tension should use wider range (more leaps)
            assert range_high >= range_low

    def test_density_affects_note_count(self) -> None:
        """Higher density trajectory should produce more notes."""
        gen = get_generator("markov")

        low_dens = TrajectorySpec(density=TrajectoryDimension(type="linear", target=0.1, waypoints=[]))
        high_dens = TrajectorySpec(density=TrajectoryDimension(type="linear", target=0.9, waypoints=[]))

        s_low, _ = gen.generate(_make_spec(seed=42, temperature=0.5), trajectory=low_dens)
        s_high, _ = gen.generate(_make_spec(seed=42, temperature=0.5), trajectory=high_dens)

        assert len(s_high.all_notes()) >= len(s_low.all_notes())


class TestMarkovMultiInstrument:
    def test_multi_instrument(self) -> None:
        spec = _make_spec(
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ]
        )
        gen = get_generator("markov")
        score, _ = gen.generate(spec)
        assert len(score.instruments()) == 2
        assert len(score.part_for_instrument("piano")) > 0
        assert len(score.part_for_instrument("acoustic_bass")) > 0

    def test_all_roles(self) -> None:
        spec = _make_spec(
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
                InstrumentSpec(name="acoustic_guitar", role="harmony"),
            ]
        )
        gen = get_generator("markov")
        score, _ = gen.generate(spec)
        assert len(score.instruments()) == 3

    def test_bass_respects_range(self) -> None:
        spec = _make_spec(
            instruments=[
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
            seed=77,
            temperature=0.8,
        )
        gen = get_generator("markov")
        score, _ = gen.generate(spec)

        bass_range = INSTRUMENT_RANGES["acoustic_bass"]
        for note in score.all_notes():
            assert bass_range.midi_low <= note.pitch <= bass_range.midi_high


class TestMarkovModelLoading:
    def test_lazy_load_caches(self) -> None:
        """Loading the same model twice returns the same object."""
        m1 = _load_model("diatonic_bigram")
        m2 = _load_model("diatonic_bigram")
        assert m1 is m2

    def test_model_has_required_metadata(self) -> None:
        model = _load_model("diatonic_bigram")
        assert model.name
        assert model.description
        assert model.source
        assert model.license
        assert model.n_gram_order >= 1

    def test_transitions_probabilities_sum_to_one(self) -> None:
        model = _load_model("diatonic_bigram")
        for degree, targets in model.transitions.items():
            total = sum(targets.values())
            assert abs(total - 1.0) < 0.01, f"Degree {degree} probabilities sum to {total}, expected ~1.0"

    def test_nonexistent_model_raises(self) -> None:
        import pytest

        with pytest.raises(FileNotFoundError):
            _load_model("nonexistent_model_xyz")
