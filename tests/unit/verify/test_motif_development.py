"""P2.1: motif_development_index distinguishes real theme-and-development
from an in-key random walk (a metric a random walk *fails*).
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.stochastic import StochasticGenerator
from yao.generators.thematic_recall import auto_thematic_recall
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.verify.evaluator import _compute_motif_development, evaluate_score


def _spec(thematic: bool, seed: int = 7) -> CompositionSpec:
    return CompositionSpec(
        title="M",
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
        generation=GenerationConfig(strategy="stochastic", seed=seed, temperature=0.5, thematic_development=thematic),
    )


def test_developed_form_scores_high() -> None:
    spec, _ = auto_thematic_recall(_spec(thematic=True))
    score, _plan, _ = generate_via_v2_pipeline(spec)
    # A return section now *develops* the theme (genre-aware variation) rather
    # than copying it note-for-note, so the score is high-but-not-perfect —
    # still far above the <0.5 random walk, proving a recognizable return.
    assert _compute_motif_development(score) >= 0.85


def test_random_walk_scores_low() -> None:
    """No auto-recall, legacy random-walk primary melody → low recurrence."""
    score, _ = StochasticGenerator().generate(_spec(thematic=False))
    assert _compute_motif_development(score) < 0.5


def test_metric_in_report_and_passes_on_good_output() -> None:
    spec, _ = auto_thematic_recall(_spec(thematic=True))
    score, plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None, plan=plan)
    md = [s for s in report.scores if s.metric == "motif_development_index"]
    assert len(md) == 1
    assert md[0].passed


def test_metric_absent_without_plan() -> None:
    """Plan-gated: additive for legacy plan-less callers."""
    spec, _ = auto_thematic_recall(_spec(thematic=True))
    score, _plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None)  # no plan
    assert not [s for s in report.scores if s.metric == "motif_development_index"]


def test_none_for_single_section() -> None:
    spec = _spec(thematic=False)
    single = spec.model_copy(update={"sections": [spec.sections[0]]})
    score, _ = StochasticGenerator().generate(single)
    assert _compute_motif_development(score) is None
