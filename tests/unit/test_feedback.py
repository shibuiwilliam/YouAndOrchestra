"""Tests for the conductor feedback adaptation module."""

from __future__ import annotations

from yao.conductor.feedback import apply_adaptations, suggest_adaptations
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.verify.evaluator import EvaluationReport, EvaluationScore


def _make_spec(temperature: float = 0.5) -> CompositionSpec:
    """Create a minimal spec for feedback testing."""
    return CompositionSpec(
        title="Feedback Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=42, temperature=temperature),
    )


def _make_report(
    metric: str,
    dimension: str,
    score: float,
    target: float,
    tolerance: float,
) -> EvaluationReport:
    """Create a report with a single failing metric."""
    return EvaluationReport(
        title="Test",
        scores=[
            EvaluationScore(
                dimension=dimension,
                metric=metric,
                score=score,
                target=target,
                tolerance=tolerance,
                detail="test detail",
            )
        ],
    )


class TestContourVarietyAdaptation:
    """Tests for contour_variety feedback handling."""

    def test_too_low_suggests_temperature_increase(self) -> None:
        """Low contour variety should suggest increasing temperature."""
        spec = _make_spec(temperature=0.4)
        report = _make_report("contour_variety", "melody", 0.05, 0.4, 0.3)
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "generation.temperature"
        assert float(adaptations[0].new_value) > 0.4

    def test_too_high_suggests_temperature_decrease(self) -> None:
        """High contour variety should suggest decreasing temperature."""
        spec = _make_spec(temperature=0.8)
        report = _make_report("contour_variety", "melody", 0.95, 0.4, 0.3)
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "generation.temperature"
        assert float(adaptations[0].new_value) < 0.8

    def test_within_tolerance_no_adaptation(self) -> None:
        """Contour variety within tolerance should not trigger adaptation."""
        spec = _make_spec(temperature=0.5)
        report = _make_report("contour_variety", "melody", 0.4, 0.4, 0.3)
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) == 0


class TestBarCountAdaptation:
    """Tests for bar_count_accuracy feedback handling."""

    def test_bar_mismatch_suggests_total_bars(self) -> None:
        """Bar count mismatch should suggest setting total_bars."""
        spec = _make_spec()
        report = _make_report("bar_count_accuracy", "structure", 0.5, 1.0, 0.05)
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "total_bars"
        assert int(adaptations[0].new_value) == spec.computed_total_bars()

    def test_apply_total_bars(self) -> None:
        """apply_adaptations should update total_bars."""
        spec = _make_spec()
        from yao.conductor.feedback import SpecAdaptation

        adaptations = [SpecAdaptation(field="total_bars", old_value="auto", new_value="16", reason="test")]
        result = apply_adaptations(spec, adaptations)
        assert result.total_bars == 16


class TestSectionContrastAdaptation:
    """Tests for section_contrast and section_count_match feedback."""

    def test_low_contrast_suggests_dynamics_differentiation(self) -> None:
        """Low section contrast should suggest varied dynamics."""
        spec = CompositionSpec(
            title="Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=4, dynamics="mf"),
                SectionSpec(name="chorus", bars=4, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        report = _make_report("section_contrast", "structure", 0.0, 0.5, 0.4)
        adaptations = suggest_adaptations(report, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "sections.dynamics"

    def test_apply_dynamics_arc(self) -> None:
        """apply_adaptations should spread dynamics across sections."""
        spec = CompositionSpec(
            title="Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=4, dynamics="mf"),
                SectionSpec(name="chorus", bars=4, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        from yao.conductor.feedback import SpecAdaptation

        adaptations = [
            SpecAdaptation(
                field="sections.dynamics",
                old_value="['mf', 'mf']",
                new_value="varied",
                reason="test",
            )
        ]
        result = apply_adaptations(spec, adaptations)
        dynamics = [s.dynamics for s in result.sections]
        assert len(set(dynamics)) > 1  # dynamics should now differ
