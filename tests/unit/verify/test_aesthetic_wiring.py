"""P2.2: the aesthetic dimension is wired into evaluate_score.

`verify/aesthetic.py` (surprise/memorability/contrast/pacing) was orphaned
while the `aesthetic` dimension carried 0.20 weight and produced zero scores —
making the quality-score weighting a fiction. When a MusicalPlan is provided,
those four metrics now appear in the report.
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.thematic_recall import auto_thematic_recall
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.verify.evaluator import evaluate_score

_AESTHETIC_METRICS = {"surprise_index", "memorability_index", "contrast_index", "pacing_index"}


def _spec() -> CompositionSpec:
    return CompositionSpec(
        title="Aes",
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
        generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.5, thematic_development=True),
    )


def test_aesthetic_scores_present_when_plan_given() -> None:
    spec, _ = auto_thematic_recall(_spec())
    score, plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None, plan=plan)
    metrics = {s.metric for s in report.scores if s.dimension == "aesthetic"}
    assert metrics >= _AESTHETIC_METRICS


def test_aesthetic_absent_without_plan_backward_compatible() -> None:
    """No plan → no aesthetic scores (existing callers unaffected)."""
    spec, _ = auto_thematic_recall(_spec())
    score, _plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None)  # no plan
    assert not [s for s in report.scores if s.dimension == "aesthetic"]


def test_aesthetic_dimension_contributes_to_quality() -> None:
    """The aesthetic dimension now changes the quality score (0.20 weight real)."""
    spec, _ = auto_thematic_recall(_spec())
    score, plan, _ = generate_via_v2_pipeline(spec)
    with_plan = evaluate_score(score, spec, None, plan=plan)
    without = evaluate_score(score, spec, None)
    assert with_plan.quality_score != without.quality_score


def test_good_output_passes_aesthetic_metrics() -> None:
    spec, _ = auto_thematic_recall(_spec())
    score, plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None, plan=plan)
    aesthetic = [s for s in report.scores if s.dimension == "aesthetic"]
    assert all(s.passed for s in aesthetic), [s.metric for s in aesthetic if not s.passed]
