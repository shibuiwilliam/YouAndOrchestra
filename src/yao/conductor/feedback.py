"""Feedback adapter — maps evaluation failures to spec modifications.

This module bridges the gap between "what's wrong" (EvaluationReport)
and "what to change" (CompositionSpec modifications). It enables
the Conductor to autonomously iterate without human intervention.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.schema.composition import CompositionSpec
from yao.verify.critique.types import Finding
from yao.verify.evaluator import EvaluationReport, EvaluationScore


@dataclass(frozen=True)
class SpecAdaptation:
    """A single proposed modification to a CompositionSpec.

    Attributes:
        field: Which spec field to change.
        old_value: Previous value (for provenance).
        new_value: Proposed new value.
        reason: Why this change is suggested (linked to evaluation).
    """

    field: str
    old_value: str
    new_value: str
    reason: str


def suggest_adaptations(
    eval_report: EvaluationReport,
    spec: CompositionSpec,
) -> list[SpecAdaptation]:
    """Map evaluation failures to concrete spec modifications.

    Args:
        eval_report: The evaluation report with pass/fail metrics.
        spec: The current composition spec.

    Returns:
        List of suggested adaptations, ordered by priority.
    """
    adaptations: list[SpecAdaptation] = []

    for score in eval_report.scores:
        if score.passed:
            continue
        adaptation = _adaptation_for_metric(score, spec)
        if adaptation is not None:
            adaptations.append(adaptation)

    return adaptations


def _adaptation_for_metric(
    score: EvaluationScore,
    spec: CompositionSpec,
) -> SpecAdaptation | None:
    """Suggest an adaptation for a single failing metric."""
    metric = score.metric
    current_temp = spec.generation.temperature

    if metric == "pitch_range_utilization":
        if score.score < score.target:
            # Range too narrow — increase temperature for more interval variety
            new_temp = min(current_temp + 0.2, 1.0)
            return SpecAdaptation(
                field="generation.temperature",
                old_value=str(current_temp),
                new_value=str(new_temp),
                reason=f"Pitch range too narrow ({score.detail}). Increasing temperature for wider intervals.",
            )
        # Range too wide — decrease temperature
        new_temp = max(current_temp - 0.15, 0.05)
        return SpecAdaptation(
            field="generation.temperature",
            old_value=str(current_temp),
            new_value=str(new_temp),
            reason=f"Pitch range too wide ({score.detail}). Decreasing temperature for tighter intervals.",
        )

    if metric == "stepwise_motion_ratio":
        if score.score < score.target - score.tolerance:
            # Too many leaps — decrease temperature
            new_temp = max(current_temp - 0.2, 0.05)
            return SpecAdaptation(
                field="generation.temperature",
                old_value=str(current_temp),
                new_value=str(new_temp),
                reason=f"Too many leaps ({score.detail}). Decreasing temperature for smoother motion.",
            )
        if score.score > score.target + score.tolerance:
            # Too stepwise — increase temperature
            new_temp = min(current_temp + 0.15, 1.0)
            return SpecAdaptation(
                field="generation.temperature",
                old_value=str(current_temp),
                new_value=str(new_temp),
                reason=f"Motion too stepwise ({score.detail}). Increasing temperature for more leaps.",
            )

    if metric == "contour_variety":
        if score.score < score.target - score.tolerance:
            # Too few direction changes — increase temperature for more randomness
            new_temp = min(current_temp + 0.15, 1.0)
            return SpecAdaptation(
                field="generation.temperature",
                old_value=str(current_temp),
                new_value=str(new_temp),
                reason=f"Contour too monotonic ({score.detail}). Increasing temperature for more direction changes.",
            )
        if score.score > score.target + score.tolerance:
            # Too erratic — decrease temperature
            new_temp = max(current_temp - 0.15, 0.05)
            return SpecAdaptation(
                field="generation.temperature",
                old_value=str(current_temp),
                new_value=str(new_temp),
                reason=f"Contour too erratic ({score.detail}). Decreasing temperature for smoother contour.",
            )

    if metric == "section_contrast" and score.score < score.target - score.tolerance:
        return _differentiate_dynamics(spec)

    if metric == "pitch_class_variety" and score.score < score.target - score.tolerance:
        # Not enough harmonic variety — switch to stochastic + higher temp
        if spec.generation.strategy == "rule_based":
            return SpecAdaptation(
                field="generation.strategy",
                old_value="rule_based",
                new_value="stochastic",
                reason=f"Low pitch class variety ({score.detail}). Switching to stochastic generator for more variety.",
            )
        new_temp = min(current_temp + 0.2, 1.0)
        return SpecAdaptation(
            field="generation.temperature",
            old_value=str(current_temp),
            new_value=str(new_temp),
            reason=f"Low pitch class variety ({score.detail}). Increasing temperature.",
        )

    if metric == "consonance_ratio" and score.score < score.target - score.tolerance:
        # Too dissonant — decrease temperature
        new_temp = max(current_temp - 0.2, 0.05)
        return SpecAdaptation(
            field="generation.temperature",
            old_value=str(current_temp),
            new_value=str(new_temp),
            reason=f"Too dissonant ({score.detail}). Decreasing temperature for more consonance.",
        )

    if metric == "bar_count_accuracy" and score.score < score.target - score.tolerance:
        # Bar count mismatch — adjust total_bars to match spec
        spec_bars = spec.computed_total_bars()
        return SpecAdaptation(
            field="total_bars",
            old_value=str(spec.total_bars or "auto"),
            new_value=str(spec_bars),
            reason=f"Bar count mismatch ({score.detail}). Setting total_bars explicitly to {spec_bars}.",
        )

    if metric == "section_count_match" and score.score < score.target - score.tolerance:
        # Sections don't match — this usually means the spec and generator disagree.
        # Re-affirm the section structure by adjusting dynamics for clarity.
        return _differentiate_dynamics(spec)

    return None


def _differentiate_dynamics(spec: CompositionSpec) -> SpecAdaptation | None:
    """Suggest differentiating section dynamics for more contrast."""
    current_dynamics = [s.dynamics for s in spec.sections]

    # If all sections have the same dynamics, spread them
    if len(set(current_dynamics)) <= 1:
        return SpecAdaptation(
            field="sections.dynamics",
            old_value=str(current_dynamics),
            new_value="varied (pp→mf→f→mp)",
            reason="All sections have identical dynamics. Differentiating for more contrast.",
        )
    return None


def apply_adaptations(
    spec: CompositionSpec,
    adaptations: list[SpecAdaptation],
) -> CompositionSpec:
    """Apply a list of adaptations to produce a modified spec.

    Args:
        spec: The original spec.
        adaptations: List of adaptations to apply.

    Returns:
        New CompositionSpec with adaptations applied.
    """
    updates: dict[str, object] = {}
    gen_updates: dict[str, object] = {}

    for adaptation in adaptations:
        if adaptation.field == "generation.temperature":
            gen_updates["temperature"] = float(adaptation.new_value)
        elif adaptation.field == "generation.strategy":
            gen_updates["strategy"] = adaptation.new_value
        elif adaptation.field == "generation.seed":
            gen_updates["seed"] = int(adaptation.new_value)
        elif adaptation.field == "sections.dynamics":
            # Apply a dynamic arc: pp → mp → f → mp for 4 sections
            dynamic_arc = ["pp", "mp", "f", "mp", "mf", "p", "ff", "pp"]
            new_sections = []
            for i, section in enumerate(spec.sections):
                dyn = dynamic_arc[i % len(dynamic_arc)]
                new_sections.append(section.model_copy(update={"dynamics": dyn}))
            updates["sections"] = new_sections
        elif adaptation.field == "total_bars":
            updates["total_bars"] = int(adaptation.new_value)

    if gen_updates:
        new_gen = spec.generation.model_copy(update=gen_updates)
        updates["generation"] = new_gen

    if not updates:
        return spec

    return spec.model_copy(update=updates)


def suggest_adaptations_from_findings(
    findings: list[Finding],
    spec: CompositionSpec,
) -> list[SpecAdaptation]:
    """Map Adversarial Critic findings to concrete spec modifications.

    This bridges the Critic's structured findings into actionable spec
    changes that the Conductor can apply before the next iteration.

    Args:
        findings: Structured findings from the Critic rules.
        spec: The current composition spec.

    Returns:
        List of suggested adaptations, ordered by severity.
    """
    adaptations: list[SpecAdaptation] = []
    current_temp = spec.generation.temperature

    for finding in findings:
        adaptation = _adaptation_for_finding(finding, spec, current_temp)
        if adaptation is not None:
            adaptations.append(adaptation)

    return adaptations


def _adaptation_for_finding(
    finding: Finding,
    spec: CompositionSpec,
    current_temp: float,
) -> SpecAdaptation | None:
    """Suggest an adaptation for a single Critic finding."""
    rule_id = finding.rule_id

    if rule_id == "structure.section_monotony":
        return _differentiate_dynamics(spec)

    if rule_id == "structure.climax_absence":
        # Increase dynamics range so at least one section is 'ff'
        sections = list(spec.sections)
        if len(sections) >= 2:  # noqa: PLR2004
            climax_idx = max(0, len(sections) - 2)
            return SpecAdaptation(
                field="sections.dynamics",
                old_value=sections[climax_idx].dynamics,
                new_value="ff",
                reason=f"Critic: {finding.issue}. Setting climax dynamics.",
            )
        return None

    if rule_id == "harmonic.monotony":
        # Increase temperature for more harmonic variety
        new_temp = min(current_temp + 0.15, 1.0)
        return SpecAdaptation(
            field="generation.temperature",
            old_value=str(current_temp),
            new_value=str(new_temp),
            reason=f"Critic: {finding.issue}. Increasing temperature for chord variety.",
        )

    if rule_id == "harmonic.cliche_progression":
        new_temp = min(current_temp + 0.2, 1.0)
        return SpecAdaptation(
            field="generation.temperature",
            old_value=str(current_temp),
            new_value=str(new_temp),
            reason=f"Critic: {finding.issue}. Increasing temperature to break cliche patterns.",
        )

    if rule_id == "rhythm.monotony":
        return _differentiate_dynamics(spec)

    if rule_id == "emotional.intent_divergence":
        # Intent mismatch is hard to fix automatically — change seed
        current_seed = spec.generation.seed or 42
        return SpecAdaptation(
            field="generation.seed",
            old_value=str(current_seed),
            new_value=str(current_seed + 7),
            reason=f"Critic: {finding.issue}. Trying new seed for better intent alignment.",
        )

    return None
