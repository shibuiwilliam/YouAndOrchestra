"""P1.4: the harmony planner ends the piece with an authentic cadence (V–I),
giving real harmonic closure that resolves home to the tonic.
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.note.accompaniment import chord_pitches
from yao.generators.thematic_recall import auto_thematic_recall
from yao.ir.notation import note_name_to_midi
from yao.ir.plan.harmony import CadenceRole
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


def _spec(seed: int = 7) -> CompositionSpec:
    return CompositionSpec(
        title="Cad",
        genre="cinematic",
        key="F major",
        tempo_bpm=110.0,
        time_signature="4/4",
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="strings", role="harmony"),
            InstrumentSpec(name="bass", role="bass"),
        ],
        sections=[
            SectionSpec(name="A", bars=8, dynamics="mp"),
            SectionSpec(name="B", bars=8, dynamics="mf"),
            SectionSpec(name="A_prime", bars=8, dynamics="mp"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=seed, temperature=0.5, thematic_development=True),
    )


def test_piece_ends_on_authentic_cadence() -> None:
    spec, _ = auto_thematic_recall(_spec())
    _score, plan, _ = generate_via_v2_pipeline(spec)
    chords = sorted(plan.harmony.chord_events, key=lambda c: c.start_beat)
    assert chords[-1].roman == "I"
    assert chords[-1].cadence_role == CadenceRole.AUTHENTIC
    assert chords[-2].roman == "V"  # dominant approach


def test_bass_resolves_to_tonic() -> None:
    spec, _ = auto_thematic_recall(_spec())
    score, _plan, _ = generate_via_v2_pipeline(spec)
    tonic_pc = note_name_to_midi("F4") % 12
    bass = [n for s in score.sections for p in s.parts if p.instrument == "bass" for n in p.notes]
    assert bass
    assert max(bass, key=lambda n: n.start_beat).pitch % 12 == tonic_pc


def test_final_chord_contains_tonic() -> None:
    spec, _ = auto_thematic_recall(_spec())
    _score, plan, _ = generate_via_v2_pipeline(spec)
    final = max(plan.harmony.chord_events, key=lambda c: c.start_beat)
    tonic_pc = note_name_to_midi("F4") % 12
    assert tonic_pc in {p % 12 for p in chord_pitches(final, "F", "major")}
