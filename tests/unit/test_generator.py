"""Tests for the rule-based generator."""

from __future__ import annotations

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.rule_based import RuleBasedGenerator
from yao.ir.notation import parse_key, scale_notes
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint


class TestRuleBasedGenerator:
    def test_generates_notes(self, minimal_spec: CompositionSpec) -> None:
        gen = RuleBasedGenerator()
        score, prov = gen.generate(minimal_spec)
        assert len(score.all_notes()) > 0

    def test_respects_title(self, minimal_spec: CompositionSpec) -> None:
        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        assert score.title == minimal_spec.title

    def test_respects_key(self) -> None:
        spec = CompositionSpec(
            title="Key Test",
            key="D major",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
        )
        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)

        # All melody notes should be from the D major scale
        root, scale_type = parse_key("D major")
        d_major_pcs = set()
        for octave in range(0, 10):
            for note in scale_notes(root, scale_type, octave):
                if 0 <= note <= 127:
                    d_major_pcs.add(note % 12)

        melody_notes = score.part_for_instrument("piano")
        for note in melody_notes:
            assert note.pitch % 12 in d_major_pcs, f"Note {note.pitch} not in D major scale"

    def test_respects_instrument_range(self, minimal_spec: CompositionSpec) -> None:
        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)

        piano_range = INSTRUMENT_RANGES["piano"]
        for note in score.all_notes():
            assert piano_range.midi_low <= note.pitch <= piano_range.midi_high, (
                f"Note {note.pitch} out of piano range ({piano_range.midi_low}–{piano_range.midi_high})"
            )

    def test_respects_section_count(self) -> None:
        spec = CompositionSpec(
            title="Section Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="intro", bars=4, dynamics="mp"),
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
        )
        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)
        assert len(score.sections) == 3
        assert [s.name for s in score.sections] == ["intro", "verse", "outro"]

    def test_generates_provenance(self, minimal_spec: CompositionSpec) -> None:
        gen = RuleBasedGenerator()
        _, prov = gen.generate(minimal_spec)
        assert len(prov) > 0
        records = prov.records
        operations = [r.operation for r in records]
        assert "start_generation" in operations
        assert "complete_generation" in operations

    def test_multi_instrument(self, multi_instrument_spec: CompositionSpec) -> None:
        gen = RuleBasedGenerator()
        score, _ = gen.generate(multi_instrument_spec)
        instruments = score.instruments()
        assert "piano" in instruments
        assert "acoustic_bass" in instruments

    def test_with_trajectory(self, minimal_spec: CompositionSpec) -> None:
        traj = TrajectorySpec(
            tension=TrajectoryDimension(
                waypoints=[
                    Waypoint(bar=0, value=0.2),
                    Waypoint(bar=8, value=0.9),
                ]
            )
        )
        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec, traj)
        assert len(score.all_notes()) > 0

    def test_deterministic(self, minimal_spec: CompositionSpec) -> None:
        gen = RuleBasedGenerator()
        score1, _ = gen.generate(minimal_spec)
        score2, _ = gen.generate(minimal_spec)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()
        assert len(notes1) == len(notes2)
        for n1, n2 in zip(notes1, notes2, strict=True):
            assert n1.pitch == n2.pitch
            assert n1.start_beat == n2.start_beat
