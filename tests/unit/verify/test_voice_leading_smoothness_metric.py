"""P2.1: voice_leading_smoothness rewards connected harmony and fails block-chord
lurching. Validates that the harmony craft the v2 arrangement produces is measured.
"""

from __future__ import annotations

from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.thematic_recall import auto_thematic_recall
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.verify.evaluator import _compute_voice_leading_smoothness, evaluate_score


def _spec() -> CompositionSpec:
    return CompositionSpec(
        title="VL",
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


def _score_with_harmony(voicings: list[list[int]]) -> ScoreIR:
    notes = []
    for i, chord in enumerate(voicings):
        for pitch in chord:
            notes.append(
                Note(pitch=pitch, start_beat=float(i) * 2, duration_beats=2.0, velocity=70, instrument="strings")
            )
    section = Section(name="A", start_bar=0, end_bar=4, parts=(Part(instrument="strings", notes=tuple(notes)),))
    return ScoreIR(title="t", tempo_bpm=110.0, time_signature="4/4", key="F major", sections=(section,))


def test_smooth_harmony_scores_higher_than_block() -> None:
    # Voice-led (small motion) must score clearly above block root position.
    led = [[60, 64, 67], [60, 65, 69], [59, 62, 67], [60, 64, 67]]
    block = [[41, 45, 48], [65, 69, 72], [43, 47, 50], [65, 69, 72]]
    smooth = _compute_voice_leading_smoothness(_score_with_harmony(led), _spec())
    lurching = _compute_voice_leading_smoothness(_score_with_harmony(block), _spec())
    assert smooth >= 0.7
    assert smooth - lurching > 0.3


def test_block_root_position_scores_low() -> None:
    # Block root position: big leaps to root each chord.
    block = [[41, 45, 48], [65, 69, 72], [43, 47, 50], [65, 69, 72]]
    score = _score_with_harmony(block)
    assert _compute_voice_leading_smoothness(score, _spec()) < 0.5


def test_real_v2_harmony_is_smooth_and_in_report() -> None:
    spec, _ = auto_thematic_recall(_spec())
    score, plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None, plan=plan)
    vl = [s for s in report.scores if s.metric == "voice_leading_smoothness"]
    assert len(vl) == 1
    assert vl[0].passed


def test_metric_absent_without_plan() -> None:
    spec, _ = auto_thematic_recall(_spec())
    score, _plan, _ = generate_via_v2_pipeline(spec)
    report = evaluate_score(score, spec, None)  # no plan
    assert not [s for s in report.scores if s.metric == "voice_leading_smoothness"]


def test_none_without_harmony_instrument() -> None:
    spec = _spec().model_copy(update={"instruments": [InstrumentSpec(name="piano", role="melody")]})
    led = [[60, 64, 67], [60, 65, 69]]
    assert _compute_voice_leading_smoothness(_score_with_harmony(led), spec) is None
