"""P2.4: genre-aware evaluation — beat-driven genres are judged with rhythm/
structure weighted over melody/harmony (percussion_centric).
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.thematic_recall import auto_thematic_recall
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.schema.genre_profile_loader import load_unified_genre_profile
from yao.verify.evaluator import evaluate_score


def _spec(genre: str) -> CompositionSpec:
    return CompositionSpec(
        title="G",
        genre=genre,
        key="C major",
        tempo_bpm=90.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody"), InstrumentSpec(name="bass", role="bass")],
        sections=[SectionSpec(name="A", bars=8, dynamics="mf"), SectionSpec(name="B", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.5, thematic_development=True),
    )


def test_loader_reads_percussion_centric_from_yaml() -> None:
    assert load_unified_genre_profile("hiphop_boom_bap").evaluation.percussion_centric is True
    assert load_unified_genre_profile("cinematic").evaluation.percussion_centric is False


def test_percussion_centric_reweights_evaluation() -> None:
    """percussion_centric applies even without explicit weights (bug fix)."""
    spec, _ = auto_thematic_recall(_spec("hiphop_boom_bap"))
    score, plan, _ = generate_via_v2_pipeline(spec)
    gp = load_unified_genre_profile("hiphop_boom_bap")
    with_genre = evaluate_score(score, spec, None, genre_profile=gp, plan=plan)
    default = evaluate_score(score, spec, None, plan=plan)
    # Genre-aware weighting is applied and de-emphasizes melody/harmony.
    assert with_genre.dimension_weights is not None
    assert with_genre.dimension_weights["melody"] == 0.05
    assert with_genre.quality_score != default.quality_score


def test_non_percussion_genre_unchanged() -> None:
    spec, _ = auto_thematic_recall(_spec("cinematic"))
    score, plan, _ = generate_via_v2_pipeline(spec)
    gp = load_unified_genre_profile("cinematic")
    with_genre = evaluate_score(score, spec, None, genre_profile=gp, plan=plan)
    default = evaluate_score(score, spec, None, plan=plan)
    assert with_genre.dimension_weights is None
    assert with_genre.quality_score == default.quality_score


class TestStaticTextureContrast:
    """Ambient/drone genres (static_texture) omit the contrast penalty."""

    def _ambient_spec(self):
        return CompositionSpec(
            title="Amb",
            genre="ambient",
            key="A minor",
            tempo_bpm=70.0,
            time_signature="4/4",
            instruments=[InstrumentSpec(name="piano", role="melody"), InstrumentSpec(name="strings", role="harmony")],
            sections=[SectionSpec(name="A", bars=8, dynamics="p"), SectionSpec(name="B", bars=8, dynamics="mp")],
            generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.4, thematic_development=True),
        )

    def test_loader_reads_static_texture(self) -> None:
        assert load_unified_genre_profile("ambient").evaluation.static_texture is True
        assert load_unified_genre_profile("cinematic").evaluation.static_texture is False

    def test_ambient_report_omits_contrast(self) -> None:
        spec, _ = auto_thematic_recall(self._ambient_spec())
        score, plan, _ = generate_via_v2_pipeline(spec)
        gp = load_unified_genre_profile("ambient")
        report = evaluate_score(score, spec, None, genre_profile=gp, plan=plan)
        assert not any(s.metric == "contrast_index" for s in report.scores)
        # Non-ambient still gets contrast.
        default = evaluate_score(score, spec, None, plan=plan)
        assert any(s.metric == "contrast_index" for s in default.scores)
