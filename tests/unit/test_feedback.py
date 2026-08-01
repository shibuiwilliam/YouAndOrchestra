"""Tests for the conductor feedback adaptation module."""

from __future__ import annotations

from yao.conductor.feedback import (
    apply_adaptations,
    suggest_adaptations,
    suggest_adaptations_from_findings,
)
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.verify.critique.types import Finding
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


class TestFindingsBasedAdaptations:
    """Tests for suggest_adaptations_from_findings (Critic → feedback)."""

    def _make_finding(self, rule_id: str, issue: str = "test") -> Finding:
        from yao.verify.critique.types import Finding, Role, Severity

        return Finding(
            rule_id=rule_id,
            severity=Severity.MAJOR,
            role=Role.STRUCTURE,
            issue=issue,
        )

    def test_section_monotony_suggests_dynamics(self) -> None:
        spec = CompositionSpec(
            title="Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        findings = [self._make_finding("structure.section_monotony")]
        adaptations = suggest_adaptations_from_findings(findings, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "sections.dynamics"

    def test_climax_absence_suggests_ff(self) -> None:
        spec = _make_spec()
        findings = [self._make_finding("structure.climax_absence")]
        adaptations = suggest_adaptations_from_findings(findings, spec)
        assert len(adaptations) == 0  # single section, no climax possible

        # With multiple sections
        spec_multi = CompositionSpec(
            title="Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="f"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        adaptations = suggest_adaptations_from_findings(findings, spec_multi)
        assert len(adaptations) == 1
        assert "ff" in adaptations[0].new_value
        assert adaptations[0].field.startswith("sections.dynamics.")

    def test_harmonic_monotony_increases_temperature(self) -> None:
        spec = _make_spec(temperature=0.4)
        findings = [self._make_finding("harmonic.monotony")]
        adaptations = suggest_adaptations_from_findings(findings, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "generation.temperature"
        assert float(adaptations[0].new_value) > 0.4

    def test_cliche_progression_increases_temperature(self) -> None:
        spec = _make_spec(temperature=0.3)
        findings = [self._make_finding("harmonic.cliche_progression")]
        adaptations = suggest_adaptations_from_findings(findings, spec)
        assert len(adaptations) == 1
        assert float(adaptations[0].new_value) > 0.3

    def test_intent_divergence_changes_seed(self) -> None:
        spec = _make_spec()
        findings = [self._make_finding("emotional.intent_divergence")]
        adaptations = suggest_adaptations_from_findings(findings, spec)
        assert len(adaptations) == 1
        assert adaptations[0].field == "generation.seed"

    def test_unknown_rule_produces_no_adaptation(self) -> None:
        spec = _make_spec()
        findings = [self._make_finding("unknown.nonexistent_rule")]
        adaptations = suggest_adaptations_from_findings(findings, spec)
        assert len(adaptations) == 0


class TestAdaptationIntegrity:
    """P0.1: no adaptation is reported applied unless it mutates the spec."""

    def _spec3(self) -> CompositionSpec:
        return CompositionSpec(
            title="Integrity",
            key="C major",
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="a", bars=8, dynamics="mf"),
                SectionSpec(name="b", bars=8, dynamics="mf"),
                SectionSpec(name="c", bars=8, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

    def test_recall_melody_from_last_is_applied(self) -> None:
        """recall_melody_from.last handler sets the last section's recall."""
        from yao.conductor.feedback import SpecAdaptation, apply_adaptations

        spec = self._spec3()
        adaptation = SpecAdaptation(
            field="sections.recall_melody_from.last",
            old_value="None",
            new_value="a",
            reason="test",
        )
        result = apply_adaptations(spec, [adaptation])
        assert result.sections[-1].recall_melody_from == "a"
        assert result.sections[0].recall_melody_from is None

    def test_numeric_tempo_is_applied(self) -> None:
        from yao.conductor.feedback import SpecAdaptation, apply_adaptations

        spec = self._spec3()
        adaptation = SpecAdaptation(field="tempo_bpm", old_value="120", new_value="96", reason="t")
        result = apply_adaptations(spec, [adaptation])
        assert result.tempo_bpm == 96.0

    def test_applicability_predicate(self) -> None:
        """Unsupported fields report not-applicable; supported ones report True."""
        from yao.conductor.feedback import SpecAdaptation, is_adaptation_applicable

        spec = self._spec3()

        def adapt(field: str, new: str = "x") -> SpecAdaptation:
            return SpecAdaptation(field=field, old_value="o", new_value=new, reason="r")

        # Supported
        assert is_adaptation_applicable(adapt("generation.temperature", "0.6"), spec)
        assert is_adaptation_applicable(adapt("sections.recall_melody_from.last", "a"), spec)
        assert is_adaptation_applicable(adapt("tempo_bpm", "100"), spec)
        assert is_adaptation_applicable(adapt("sections.dynamics.1"), spec)
        # Unsupported (these were the silent no-ops)
        assert not is_adaptation_applicable(adapt("instruments", "add_core_instruments"), spec)
        assert not is_adaptation_applicable(adapt("generation.motif_density", "high"), spec)
        assert not is_adaptation_applicable(adapt("trajectory.adjustment"), spec)
        assert not is_adaptation_applicable(adapt("tempo_bpm", "genre_default"), spec)
        assert not is_adaptation_applicable(adapt("sections.dynamics.99"), spec)

    def test_every_applicable_adaptation_actually_mutates(self) -> None:
        """The core integrity invariant: applicable ⟹ spec changes."""
        from yao.conductor.feedback import SpecAdaptation, apply_adaptations, is_adaptation_applicable

        spec = self._spec3()
        candidates = [
            SpecAdaptation(field="generation.temperature", old_value="0.5", new_value="0.7", reason="r"),
            SpecAdaptation(field="tempo_bpm", old_value="120", new_value="90", reason="r"),
            SpecAdaptation(field="sections.recall_melody_from.last", old_value="None", new_value="a", reason="r"),
            SpecAdaptation(field="total_bars", old_value="auto", new_value="16", reason="r"),
        ]
        for a in candidates:
            assert is_adaptation_applicable(a, spec)
            mutated = apply_adaptations(spec, [a])
            assert mutated != spec, f"{a.field} claimed applicable but did not mutate"
