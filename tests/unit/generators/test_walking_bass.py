"""P4.2: walking bass — genres whose profile sets bass_motion_style=walking get
a moving quarter-note line; others keep the density-aware root pulse.
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.note.accompaniment import realize_accompaniment_for_role
from yao.generators.thematic_recall import auto_thematic_recall
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


def _spec(genre: str, key: str) -> CompositionSpec:
    return CompositionSpec(
        title="W",
        genre=genre,
        key=key,
        tempo_bpm=160.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody"), InstrumentSpec(name="bass", role="bass")],
        sections=[SectionSpec(name="A", bars=4, dynamics="mf"), SectionSpec(name="B", bars=4, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.5, thematic_development=True),
    )


def _bass(score) -> list:
    return sorted(
        (n for s in score.sections for p in s.parts if p.instrument == "bass" for n in p.notes),
        key=lambda n: n.start_beat,
    )


class TestWalkingBassUnit:
    def _chords(self) -> list[ChordEvent]:
        return [
            ChordEvent("A", 0.0, 4.0, "I", HarmonicFunction.TONIC, 0.4),
            ChordEvent("A", 4.0, 4.0, "V", HarmonicFunction.DOMINANT, 0.5),
        ]

    def test_walking_is_quarter_notes(self) -> None:
        notes = realize_accompaniment_for_role("bass", "bass", self._chords(), "C", "major", 90, 4.0, walking_bass=True)
        assert len(notes) == 8  # 2 bars x 4 quarter notes
        assert all(n.duration_beats == 1.0 for n in notes)

    def test_walking_line_moves(self) -> None:
        notes = realize_accompaniment_for_role("bass", "bass", self._chords(), "C", "major", 90, 4.0, walking_bass=True)
        pitches = [n.pitch for n in notes]
        assert len(set(pitches)) >= 3  # not a static root pulse

    def test_downbeat_is_root(self) -> None:
        notes = realize_accompaniment_for_role("bass", "bass", self._chords(), "C", "major", 90, 4.0, walking_bass=True)
        # First note of each chord (beats 0 and 4) is the chord root.
        by_beat = {n.start_beat: n.pitch for n in notes}
        assert by_beat[0.0] % 12 == 0  # C
        assert by_beat[4.0] % 12 == 7  # G (dominant root)


def test_jazz_gets_walking_bass_cinematic_does_not() -> None:
    jazz, _ = auto_thematic_recall(_spec("jazz_bebop", "C major"))
    jscore, _, _ = generate_via_v2_pipeline(jazz)
    jbass = _bass(jscore)
    assert all(n.duration_beats == 1.0 for n in jbass)  # quarter-note walk
    assert len({n.pitch for n in jbass}) >= 4  # moving line

    cine, _ = auto_thematic_recall(_spec("cinematic", "F major"))
    cscore, _, _ = generate_via_v2_pipeline(cine)
    cbass = _bass(cscore)
    # Non-walking genre keeps the (longer) pulse, not a quarter-note walk.
    assert any(n.duration_beats > 1.0 for n in cbass)


def test_rule_based_v2_also_walks() -> None:
    """rule_based_v2 has walking-bass parity (loads genre profile)."""
    from yao.generators.legacy_adapter import build_plan_from_v1
    from yao.generators.note.base import NOTE_REALIZERS
    from yao.reflect.provenance import ProvenanceLog

    spec = CompositionSpec(
        title="W",
        genre="jazz_bebop",
        key="C major",
        tempo_bpm=160.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody"), InstrumentSpec(name="bass", role="bass")],
        sections=[SectionSpec(name="A", bars=4, dynamics="mf")],
        generation=GenerationConfig(strategy="rule_based", seed=7, temperature=0.5),
    )
    plan, _ = build_plan_from_v1(spec)
    score = NOTE_REALIZERS["rule_based_v2"]().realize(
        plan, seed=7, temperature=0.5, provenance=ProvenanceLog(), original_spec=spec
    )
    bass = _bass(score)
    assert bass
    assert all(n.duration_beats == 1.0 for n in bass)
    assert len({n.pitch for n in bass}) >= 3
