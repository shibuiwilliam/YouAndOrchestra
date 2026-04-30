"""Unit tests for the Conductor orchestration layer."""

from __future__ import annotations

from pathlib import Path

# Ensure generators are registered
import yao.generators.note.rule_based as _nrb  # noqa: F401
import yao.generators.note.stochastic as _nst  # noqa: F401
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.conductor.conductor import Conductor
from yao.conductor.feedback import (
    SpecAdaptation,
    apply_adaptations,
    suggest_adaptations,
)
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.verify.evaluator import EvaluationReport, EvaluationScore


def _make_spec(**overrides: object) -> CompositionSpec:
    defaults: dict[str, object] = {
        "title": "Test",
        "key": "C major",
        "instruments": [InstrumentSpec(name="piano", role="melody")],
        "sections": [SectionSpec(name="verse", bars=8, dynamics="mf")],
        "generation": GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
    }
    defaults.update(overrides)
    return CompositionSpec(**defaults)  # type: ignore[arg-type]


def _make_failing_report(
    metric: str, score: float, target: float, tolerance: float
) -> EvaluationReport:
    return EvaluationReport(
        title="Test",
        scores=[
            EvaluationScore(
                dimension="melody",
                metric=metric,
                score=score,
                target=target,
                tolerance=tolerance,
                detail="test",
            )
        ],
    )


class TestFeedbackAdaptation:
    def test_low_variety_increases_temperature(self) -> None:
        spec = _make_spec()
        report = _make_failing_report("pitch_class_variety", 0.1, 0.5, 0.3)
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) >= 1
        temp_adapt = [a for a in adaptations if "temperature" in a.field]
        assert len(temp_adapt) == 1
        assert float(temp_adapt[0].new_value) > spec.generation.temperature

    def test_low_variety_switches_to_stochastic(self) -> None:
        spec = _make_spec(generation=GenerationConfig(strategy="rule_based", temperature=0.5))
        report = _make_failing_report("pitch_class_variety", 0.1, 0.5, 0.3)
        adaptations = suggest_adaptations(report, spec)
        strat_adapt = [a for a in adaptations if "strategy" in a.field]
        assert len(strat_adapt) == 1
        assert strat_adapt[0].new_value == "stochastic"

    def test_too_dissonant_decreases_temperature(self) -> None:
        spec = _make_spec(
            generation=GenerationConfig(strategy="stochastic", seed=1, temperature=0.8)
        )
        report = _make_failing_report("consonance_ratio", 0.2, 0.7, 0.3)
        adaptations = suggest_adaptations(report, spec)
        temp_adapt = [a for a in adaptations if "temperature" in a.field]
        assert len(temp_adapt) == 1
        assert float(temp_adapt[0].new_value) < 0.8

    def test_passing_report_produces_no_adaptations(self) -> None:
        spec = _make_spec()
        report = EvaluationReport(
            title="Test",
            scores=[
                EvaluationScore(
                    dimension="melody",
                    metric="stepwise_motion_ratio",
                    score=0.6,
                    target=0.6,
                    tolerance=0.3,
                    detail="ok",
                )
            ],
        )
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) == 0

    def test_apply_adaptations_changes_temperature(self) -> None:
        spec = _make_spec()
        adaptations = [
            SpecAdaptation(
                field="generation.temperature",
                old_value="0.5",
                new_value="0.8",
                reason="test",
            )
        ]
        result = apply_adaptations(spec, adaptations)
        assert result.generation.temperature == 0.8

    def test_apply_adaptations_changes_strategy(self) -> None:
        spec = _make_spec()
        adaptations = [
            SpecAdaptation(
                field="generation.strategy",
                old_value="stochastic",
                new_value="rule_based",
                reason="test",
            )
        ]
        result = apply_adaptations(spec, adaptations)
        assert result.generation.strategy == "rule_based"


class TestConductor:
    def test_compose_from_description(self, tmp_path: Path) -> None:
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            conductor = Conductor()
            result = conductor.compose_from_description(
                description="a calm piano piece",
                project_name="test-calm",
                max_iterations=1,
            )
            assert result.midi_path.exists()
            assert len(result.score.all_notes()) > 0
            assert result.iterations >= 1
            assert result.evaluation is not None
        finally:
            os.chdir(original)

    def test_compose_from_spec(self, tmp_path: Path) -> None:
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            spec = _make_spec(title="Spec Test")
            conductor = Conductor()
            result = conductor.compose_from_spec(
                spec=spec,
                project_name="test-spec",
                max_iterations=2,
            )
            assert result.midi_path.exists()
            assert result.iterations >= 1
            assert result.iterations <= 2
            assert len(result.provenance) > 0
        finally:
            os.chdir(original)

    def test_max_iterations_respected(self, tmp_path: Path) -> None:
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            spec = _make_spec()
            conductor = Conductor()
            result = conductor.compose_from_spec(
                spec=spec,
                project_name="test-max",
                max_iterations=2,
            )
            assert result.iterations <= 2
        finally:
            os.chdir(original)

    def test_result_summary(self, tmp_path: Path) -> None:
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            conductor = Conductor()
            result = conductor.compose_from_description(
                description="a fast energetic piece",
                project_name="test-summary",
                max_iterations=1,
            )
            summary = result.summary()
            assert "Conductor Result" in summary
            assert "Iterations" in summary
            assert "Pass rate" in summary
        finally:
            os.chdir(original)

    def test_description_parsing_key(self, tmp_path: Path) -> None:
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            conductor = Conductor()
            result = conductor.compose_from_description(
                description="a melancholic piece",
                project_name="test-key",
                max_iterations=1,
            )
            assert "minor" in result.spec.key.lower()
        finally:
            os.chdir(original)

    def test_regenerate_section_preserves_others(self, tmp_path: Path) -> None:
        """Regenerating one section should not change notes in other sections."""
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            spec = CompositionSpec(
                title="Regen Test",
                key="C major",
                instruments=[InstrumentSpec(name="piano", role="melody")],
                sections=[
                    SectionSpec(name="verse", bars=4, dynamics="mf"),
                    SectionSpec(name="chorus", bars=4, dynamics="f"),
                ],
                generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
            )
            conductor = Conductor()
            # First, generate the full piece
            initial = conductor.compose_from_spec(
                spec=spec, project_name="test-regen", max_iterations=1,
            )
            # Regenerate only the chorus
            result = conductor.regenerate_section(
                current_score=initial.score,
                spec=spec,
                section_name="chorus",
                project_name="test-regen",
                seed_override=999,
            )
            # Verse should be unchanged
            original_verse = initial.score.sections[0]
            new_verse = result.score.sections[0]
            assert original_verse.name == "verse"
            assert new_verse.name == "verse"
            assert original_verse.parts == new_verse.parts
            # Chorus should be different (different seed)
            assert result.score.sections[1].name == "chorus"
            assert result.midi_path.exists()
        finally:
            os.chdir(original)

    def test_regenerate_section_invalid_name(self, tmp_path: Path) -> None:
        """Regenerating a non-existent section should raise an error."""
        import os

        import pytest

        from yao.errors import SpecValidationError

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            spec = _make_spec()
            conductor = Conductor()
            initial = conductor.compose_from_spec(
                spec=spec, project_name="test-bad-regen", max_iterations=1,
            )
            with pytest.raises(SpecValidationError, match="not found"):
                conductor.regenerate_section(
                    current_score=initial.score,
                    spec=spec,
                    section_name="nonexistent",
                    project_name="test-bad-regen",
                )
        finally:
            os.chdir(original)

    def test_description_parsing_tempo(self, tmp_path: Path) -> None:
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            conductor = Conductor()
            result = conductor.compose_from_description(
                description="a fast energetic rock piece",
                project_name="test-tempo",
                max_iterations=1,
            )
            assert result.spec.tempo_bpm >= 130
        finally:
            os.chdir(original)

    def test_evaluation_json_saved(self, tmp_path: Path) -> None:
        """Conductor must save evaluation.json alongside analysis.json."""
        import os

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            conductor = Conductor()
            result = conductor.compose_from_description(
                description="a calm piano piece",
                project_name="test-eval-json",
                max_iterations=1,
            )
            eval_path = result.output_dir / "evaluation.json"
            assert eval_path.exists(), "evaluation.json not found in output dir"
            import json

            data = json.loads(eval_path.read_text())
            assert "title" in data
            assert "scores" in data
        finally:
            os.chdir(original)
