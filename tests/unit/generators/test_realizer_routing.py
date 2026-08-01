"""The default pipeline routes legacy strategies to the v2 realizers (P1.1).

Locks in the flip: `stochastic`/`rule_based` now resolve to the
plan-consuming v2 realizers, which produce full voice-led arrangements with
cross-section thematic recall — instead of the deprecated discard realizers.
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.note.base import resolve_realizer_name
from yao.generators.thematic_recall import auto_thematic_recall
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


class TestResolveRealizerName:
    def test_legacy_names_route_to_v2(self) -> None:
        assert resolve_realizer_name("stochastic") == "stochastic_v2"
        assert resolve_realizer_name("rule_based") == "rule_based_v2"

    def test_v2_names_pass_through(self) -> None:
        assert resolve_realizer_name("stochastic_v2") == "stochastic_v2"
        assert resolve_realizer_name("rule_based_v2") == "rule_based_v2"

    def test_unknown_falls_back_to_plan_realizer_not_legacy(self) -> None:
        # Unknown strategies must not degrade to the deprecated legacy realizer.
        assert resolve_realizer_name("does_not_exist") == "rule_based_v2"


def _spec() -> CompositionSpec:
    return CompositionSpec(
        title="Flip",
        genre="cinematic",
        key="F major",
        tempo_bpm=120.0,
        time_signature="4/4",
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="strings", role="harmony"),
            InstrumentSpec(name="contrabass", role="bass"),
        ],
        sections=[
            SectionSpec(name="A", bars=8, dynamics="mp"),
            SectionSpec(name="B", bars=8, dynamics="mf"),
            SectionSpec(name="A_prime", bars=8, dynamics="mp"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.5, thematic_development=True),
    )


def _section_pitches(score, name: str, instrument: str) -> list[int]:
    section = next(s for s in score.sections if s.name == name)
    for part in section.parts:
        if part.instrument == instrument:
            return [n.pitch for n in sorted(part.notes, key=lambda x: x.start_beat)]
    return []


def test_default_pipeline_produces_full_arrangement_and_recall() -> None:
    """strategy='stochastic' now yields a full, voice-led, thematic arrangement."""
    spec, _ = auto_thematic_recall(_spec())
    score, plan, prov = generate_via_v2_pipeline(spec)

    # Full arrangement: every spec instrument sounds.
    sounding = {p.instrument for s in score.sections for p in s.parts if p.notes}
    assert {"piano", "strings", "contrabass"} <= sounding

    # Cross-section thematic recall: A_prime *develops* A's theme — recognizable
    # (same length, anchored first/last note, high overlap) but not a mechanical
    # note-for-note copy (which reads as monotony).
    a = _section_pitches(score, "A", "piano")
    a_prime = _section_pitches(score, "A_prime", "piano")
    assert a and a_prime
    assert len(a) == len(a_prime)  # rhythm/structure preserved
    assert a[0] == a_prime[0] and a[-1] == a_prime[-1]  # phrase anchors held
    overlap = sum(1 for x, y in zip(a, a_prime, strict=False) if x == y) / len(a)
    assert 0.5 <= overlap < 1.0  # thematically related, yet varied

    # Provenance shows the plan-consuming v2 realizer ran (not the legacy one).
    ops = {r.operation for r in prov.records}
    assert "note_realization_v2" in ops
    assert "thematic_recall_v2" in ops
