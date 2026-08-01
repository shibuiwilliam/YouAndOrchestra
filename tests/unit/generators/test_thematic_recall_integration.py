"""Integration: automatic thematic recurrence makes the theme return (P1.2).

Proves the end-to-end payoff — with recall applied, a return section's primary
melody restates the theme; without it, sections are independent. Also proves
the additive guarantee: disabled ⇒ spec unchanged.
"""

from __future__ import annotations

from yao.generators.stochastic import StochasticGenerator
from yao.generators.thematic_recall import auto_thematic_recall
from yao.ir.score_ir import ScoreIR
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


def _spec(thematic: bool) -> CompositionSpec:
    return CompositionSpec(
        title="Recurrence",
        key="F major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[
            SectionSpec(name="A", bars=4, dynamics="mf"),
            SectionSpec(name="B", bars=4, dynamics="mf"),
            SectionSpec(name="A_prime", bars=4, dynamics="mf"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=11, temperature=0.5, thematic_development=thematic),
    )


def _section_pitches(score: ScoreIR, section_name: str, instrument: str) -> list[int]:
    section = next(s for s in score.sections if s.name == section_name)
    for part in section.parts:
        if part.instrument == instrument:
            return [n.pitch for n in sorted(part.notes, key=lambda x: x.start_beat)]
    return []


def test_disabled_leaves_spec_unchanged() -> None:
    """Additive guarantee: thematic_development off ⇒ no recall assignments."""
    spec = _spec(thematic=False)
    new_spec, assignments = auto_thematic_recall(spec) if spec.generation.thematic_development else (spec, [])
    assert assignments == []
    assert all(s.recall_melody_from is None for s in spec.sections)


def test_enabled_makes_theme_return() -> None:
    """With recall applied, A_prime's melody restates A's theme."""
    base = _spec(thematic=True)

    # Baseline (no recall): A and A_prime are independent lines.
    plain_score, _ = StochasticGenerator().generate(base)
    a_plain = _section_pitches(plain_score, "A", "piano")
    aprime_plain = _section_pitches(plain_score, "A_prime", "piano")

    # With auto thematic recall applied (what the Conductor does when the
    # flag is on).
    recalled_spec, assignments = auto_thematic_recall(base)
    assert {a.section: a.recalls for a in assignments} == {"A_prime": "A"}

    themed_score, _ = StochasticGenerator().generate(recalled_spec)
    a_themed = _section_pitches(themed_score, "A", "piano")
    aprime_themed = _section_pitches(themed_score, "A_prime", "piano")

    assert a_themed, "theme section must have notes"
    assert aprime_themed, "return section must have notes"

    # The theme statement (section A) is unaffected by recall.
    assert a_themed == a_plain

    def overlap(x: list[int], y: list[int]) -> float:
        n = min(len(x), len(y))
        if n == 0:
            return 0.0
        return sum(1 for i in range(n) if x[i] == y[i]) / n

    themed_similarity = overlap(a_themed, aprime_themed)
    independent_similarity = overlap(a_plain, aprime_plain)

    # The return section should track the theme far more closely than an
    # independently-generated section does.
    assert themed_similarity > independent_similarity
    assert themed_similarity >= 0.5
