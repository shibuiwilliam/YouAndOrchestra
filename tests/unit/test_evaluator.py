"""Tests for the structured evaluator."""

from __future__ import annotations

import json
from pathlib import Path

from yao.ir.score_ir import ScoreIR
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec
from yao.verify.evaluator import (
    EvaluationReport,
    evaluate_harmony,
    evaluate_melody,
    evaluate_rhythm,
    evaluate_score,
    evaluate_structure,
)


class TestEvaluateStructure:
    def test_bar_count_accuracy(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        results = evaluate_structure(score, minimal_spec)

        bar_result = next(r for r in results if r.metric == "bar_count_accuracy")
        assert bar_result.score == 1.0
        assert bar_result.passed

    def test_section_count_match(self) -> None:
        spec = CompositionSpec(
            title="Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="intro", bars=4),
                SectionSpec(name="verse", bars=8),
            ],
        )
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)
        results = evaluate_structure(score, spec)

        section_result = next(r for r in results if r.metric == "section_count_match")
        assert section_result.score == 1.0


class TestEvaluateMelody:
    def test_evaluates_pitch_range(self, sample_score_ir: ScoreIR) -> None:
        results = evaluate_melody(sample_score_ir)
        range_result = next(r for r in results if r.metric == "pitch_range_utilization")
        assert 0.0 <= range_result.score <= 1.0

    def test_evaluates_stepwise_motion(self, sample_score_ir: ScoreIR) -> None:
        results = evaluate_melody(sample_score_ir)
        step_result = next(r for r in results if r.metric == "stepwise_motion_ratio")
        assert 0.0 <= step_result.score <= 1.0

    def test_empty_score_returns_empty(self) -> None:
        empty = ScoreIR(
            title="Empty",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(),
        )
        results = evaluate_melody(empty)
        assert len(results) == 0

    def test_motif_recall_strength_present(self, sample_score_ir: ScoreIR) -> None:
        """MotifRecallStrength metric is computed for scored with enough notes."""
        results = evaluate_melody(sample_score_ir)
        recall_results = [r for r in results if r.metric == "motif_recall_strength"]
        if sample_score_ir.all_notes() and len(sample_score_ir.all_notes()) >= 8:  # noqa: PLR2004
            assert len(recall_results) == 1
            assert 0.0 <= recall_results[0].score <= 1.0

    def test_motif_recall_target_band(self, sample_score_ir: ScoreIR) -> None:
        """MotifRecallStrength uses TARGET_BAND goal type."""
        results = evaluate_melody(sample_score_ir)
        recall_results = [r for r in results if r.metric == "motif_recall_strength"]
        for r in recall_results:
            # TARGET_BAND maps to target=0.55, tolerance=0.15 → band [0.4, 0.7]
            assert r.target == 0.55  # noqa: PLR2004
            assert r.tolerance == 0.15  # noqa: PLR2004


class TestEvaluateHarmony:
    def test_pitch_class_variety(self, sample_score_ir: ScoreIR) -> None:
        results = evaluate_harmony(sample_score_ir)
        pc_result = next(r for r in results if r.metric == "pitch_class_variety")
        assert 0.0 <= pc_result.score <= 1.0


class TestEvaluateScore:
    def test_full_evaluation(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)

        assert report.title == minimal_spec.title
        assert len(report.scores) > 0
        assert 0.0 <= report.pass_rate <= 1.0

    def test_summary_output(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)
        summary = report.summary()
        assert "Evaluation" in summary
        assert "Pass rate" in summary


class TestEvaluationReportSerialization:
    def test_to_json_returns_valid_json(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)

        json_str = report.to_json()
        data = json.loads(json_str)
        assert data["title"] == minimal_spec.title
        assert isinstance(data["scores"], list)
        assert len(data["scores"]) > 0
        for score_data in data["scores"]:
            assert "dimension" in score_data
            assert "metric" in score_data
            assert "score" in score_data
            assert "target" in score_data

    def test_save_creates_file(self, minimal_spec: CompositionSpec, tmp_path: Path) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)

        out = tmp_path / "evaluation.json"
        report.save(out)
        assert out.exists()

        data = json.loads(out.read_text())
        assert data["title"] == minimal_spec.title
        assert len(data["scores"]) == len(report.scores)

    def test_empty_report_serializes(self) -> None:
        report = EvaluationReport(title="Empty")
        data = json.loads(report.to_json())
        assert data["title"] == "Empty"
        assert data["scores"] == []


class TestEvaluateRhythm:
    def test_rhythm_variety_calculated(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        results = evaluate_rhythm(score)

        variety = next(r for r in results if r.metric == "rhythm_variety")
        assert 0.0 <= variety.score <= 1.0

    def test_syncopation_ratio_calculated(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        results = evaluate_rhythm(score)

        synco = next(r for r in results if r.metric == "syncopation_ratio")
        assert 0.0 <= synco.score <= 1.0

    def test_rhythm_with_empty_score(self) -> None:
        score = ScoreIR(
            title="Empty",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(),
        )
        results = evaluate_rhythm(score)
        assert results == []


class TestQualityScore:
    def test_quality_score_empty_report(self) -> None:
        report = EvaluationReport(title="Empty")
        assert report.quality_score == 5.0

    def test_quality_score_in_range(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)
        assert 1.0 <= report.quality_score <= 10.0

    def test_quality_score_in_summary(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)
        assert "Quality Score:" in report.summary()

    def test_quality_score_in_json(self, minimal_spec: CompositionSpec) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(minimal_spec)
        report = evaluate_score(score, minimal_spec)
        data = json.loads(report.to_json())
        assert "quality_score" in data
        assert 1.0 <= data["quality_score"] <= 10.0
