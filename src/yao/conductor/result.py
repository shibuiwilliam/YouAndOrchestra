"""ConductorResult — the output of a full composition workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.verify.analyzer import AnalysisReport
from yao.verify.critique.types import Finding
from yao.verify.evaluator import EvaluationReport


@dataclass
class ConductorResult:
    """Complete result of a Conductor composition workflow.

    Attributes:
        score: The final ScoreIR.
        spec: The final (possibly adapted) CompositionSpec.
        midi_path: Path to the generated MIDI file.
        stems: Mapping of instrument name to stem MIDI path.
        analysis: Final analysis report.
        evaluation: Final evaluation report.
        provenance: Full provenance log across all iterations.
        iterations: Number of generation rounds performed.
        iteration_history: Evaluation reports from each round.
        output_dir: Path to the output directory.
        adaptations_applied: Human-readable log of spec changes made.
        critic_findings: Structured findings from the Adversarial Critic.
    """

    score: ScoreIR
    spec: CompositionSpec
    midi_path: Path
    stems: dict[str, Path]
    analysis: AnalysisReport
    evaluation: EvaluationReport
    provenance: ProvenanceLog
    iterations: int
    iteration_history: list[EvaluationReport] = field(default_factory=list)
    output_dir: Path = field(default_factory=lambda: Path("."))
    adaptations_applied: list[str] = field(default_factory=list)
    critic_findings: list[Finding] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary of the composition result.

        Returns:
            Multi-line summary string.
        """
        lines = [
            f"=== Conductor Result: {self.score.title} ===",
            f"Iterations: {self.iterations}",
            f"Pass rate: {self.evaluation.pass_rate:.0%}",
            f"Duration: {self.score.duration_seconds():.1f}s | "
            f"Bars: {self.score.total_bars()} | "
            f"Notes: {len(self.score.all_notes())}",
            f"Instruments: {', '.join(self.score.instruments())}",
            f"Output: {self.output_dir}",
        ]

        if self.adaptations_applied:
            lines.append(f"\nAdaptations applied ({len(self.adaptations_applied)}):")
            for adaptation in self.adaptations_applied:
                lines.append(f"  - {adaptation}")

        # Critic findings
        if self.critic_findings:
            critical = sum(1 for f in self.critic_findings if f.severity.value == "critical")
            major = sum(1 for f in self.critic_findings if f.severity.value == "major")
            minor = sum(1 for f in self.critic_findings if f.severity.value == "minor")
            lines.append(
                f"\nCritic findings: {len(self.critic_findings)} (critical={critical}, major={major}, minor={minor})"
            )
            for finding in self.critic_findings:
                lines.append(f"  [{finding.severity.value.upper()}] {finding.issue}")

        # Convergence: show pass rate per iteration
        if len(self.iteration_history) > 1:
            lines.append("\nConvergence:")
            for i, report in enumerate(self.iteration_history, 1):
                lines.append(f"  v{i:03d}: {report.pass_rate:.0%}")

        return "\n".join(lines)
