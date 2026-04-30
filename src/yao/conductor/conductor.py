"""Conductor — the orchestration engine for multi-phase composition.

The Conductor is YaO's primary programmatic interface. It replaces
manual CLI chaining with an automated feedback loop:

    describe → build spec → generate → evaluate → adapt → regenerate

Claude Code (or any client) calls the Conductor instead of individual
CLI commands. The Conductor manages iteration, adaptation, and provenance.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import structlog

from yao.conductor.feedback import (
    apply_adaptations,
    suggest_adaptations,
    suggest_adaptations_from_findings,
)
from yao.conductor.result import ConductorResult
from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.ir.score_ir import ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog
from yao.render.iteration import next_iteration_dir
from yao.render.midi_writer import write_midi
from yao.render.stem_writer import write_stems
from yao.schema.composition import (
    CompositionSpec,
)
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.trajectory import TrajectorySpec
from yao.verify.analyzer import analyze_score
from yao.verify.critique import CRITIQUE_RULES
from yao.verify.evaluator import EvaluationReport, evaluate_score

_RoleType = Literal["melody", "harmony", "bass", "rhythm", "pad"]

logger = structlog.get_logger()


# Musical knowledge (mood→key, instruments, genre) is in src/yao/sketch/compiler.py.
# The Conductor delegates NL parsing to SpecCompiler (CLAUDE.md anti-pattern #7).


class Conductor:
    """Orchestrates the full composition workflow.

    The Conductor is the primary programmatic entry point for YaO.
    It manages the generate → evaluate → adapt → regenerate loop,
    enabling Claude Code to compose music in a single call.
    """

    def compose_from_description(
        self,
        description: str,
        project_name: str | None = None,
        max_iterations: int = 3,
    ) -> ConductorResult:
        """Generate a composition from a natural language description.

        Builds a spec from the description, then runs the feedback loop.

        Args:
            description: Natural language description of the desired music.
            project_name: Project name for output directory. Auto-generated if None.
            max_iterations: Maximum number of generation rounds.

        Returns:
            ConductorResult with the final composition and all metadata.
        """
        if project_name is None:
            project_name = _slugify(description[:40])

        spec, trajectory = self._build_spec_from_description(description, project_name)

        logger.info(
            "conductor_compose_from_description",
            project=project_name,
            key=spec.key,
            tempo=spec.tempo_bpm,
            instruments=[i.name for i in spec.instruments],
            sections=[s.name for s in spec.sections],
        )

        return self.compose_from_spec(
            spec=spec,
            trajectory=trajectory,
            project_name=project_name,
            max_iterations=max_iterations,
        )

    def compose_from_spec(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
        project_name: str | None = None,
        max_iterations: int = 3,
    ) -> ConductorResult:
        """Generate a composition from an existing spec with feedback iteration.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory for dynamic shaping.
            project_name: Project name for output directory.
            max_iterations: Maximum number of generation rounds.

        Returns:
            ConductorResult with the final composition and all metadata.
        """
        if project_name is None:
            project_name = _slugify(spec.title)

        project_dir = Path(f"outputs/projects/{project_name}")
        combined_provenance = ProvenanceLog()
        iteration_history: list[EvaluationReport] = []
        adaptations_log: list[str] = []
        current_spec = spec

        combined_provenance.record(
            layer="conductor",
            operation="start_workflow",
            parameters={
                "title": spec.title,
                "project": project_name,
                "max_iterations": max_iterations,
                "strategy": spec.generation.strategy,
            },
            source="Conductor.compose_from_spec",
            rationale="Beginning conductor-managed composition workflow.",
        )

        # Iteration loop: generate → evaluate → adapt → regenerate
        for iteration in range(1, max_iterations + 1):
            output_dir = next_iteration_dir(project_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate via v2 pipeline (Spec → MPIR → ScoreIR)
            score, plan, gen_provenance = generate_via_v2_pipeline(current_spec, trajectory)

            # Merge provenance
            for record in gen_provenance.records:
                combined_provenance.add(record)
            for dec in gen_provenance.recoverables:
                combined_provenance.record_recoverable(dec)

            # Adversarial Critic Gate (CLAUDE.md Rule B)
            spec_v2 = _v1_to_v2_for_critic(current_spec)
            critic_findings = CRITIQUE_RULES.run_all(plan, spec_v2)
            if critic_findings:
                combined_provenance.record(
                    layer="conductor",
                    operation="critic_gate",
                    parameters={
                        "iteration": iteration,
                        "findings_count": len(critic_findings),
                        "critical": sum(1 for f in critic_findings if f.severity.value == "critical"),
                        "major": sum(1 for f in critic_findings if f.severity.value == "major"),
                    },
                    source="Conductor.compose_from_spec",
                    rationale=(f"Adversarial Critic found {len(critic_findings)} issue(s) in iteration {iteration}."),
                )

            # Write outputs
            midi_path = write_midi(score, output_dir / "full.mid")
            stems = write_stems(score, output_dir)

            # Evaluate
            analysis = analyze_score(score)
            eval_report = evaluate_score(score, current_spec, trajectory)
            iteration_history.append(eval_report)

            # Save artifacts
            analysis.save(output_dir / "analysis.json")
            eval_report.save(output_dir / "evaluation.json")

            combined_provenance.record(
                layer="conductor",
                operation="iteration_complete",
                parameters={
                    "iteration": iteration,
                    "pass_rate": eval_report.pass_rate,
                    "total_notes": len(score.all_notes()),
                    "failed_metrics": [s.metric for s in eval_report.scores if not s.passed],
                },
                source="Conductor.compose_from_spec",
                rationale=f"Iteration {iteration}: {eval_report.pass_rate:.0%} pass rate.",
            )

            logger.info(
                "conductor_iteration",
                iteration=iteration,
                pass_rate=f"{eval_report.pass_rate:.0%}",
                quality_score=f"{eval_report.quality_score:.1f}",
                notes=len(score.all_notes()),
            )

            # Check if all metrics pass — we're done
            if eval_report.passed:
                combined_provenance.record(
                    layer="conductor",
                    operation="workflow_complete",
                    parameters={"iterations": iteration, "pass_rate": 1.0},
                    source="Conductor.compose_from_spec",
                    rationale="All evaluation metrics passed. Workflow complete.",
                )
                combined_provenance.save(output_dir / "provenance.json")
                return ConductorResult(
                    score=score,
                    spec=current_spec,
                    midi_path=midi_path,
                    stems=stems,
                    analysis=analysis,
                    evaluation=eval_report,
                    provenance=combined_provenance,
                    iterations=iteration,
                    iteration_history=iteration_history,
                    output_dir=output_dir,
                    adaptations_applied=adaptations_log,
                    critic_findings=critic_findings,
                )

            # Not all passed and we have iterations left — adapt
            if iteration < max_iterations:
                # Combine evaluator-based and critic-based adaptations
                adaptations = suggest_adaptations(eval_report, current_spec)
                if critic_findings:
                    critic_adaptations = suggest_adaptations_from_findings(
                        critic_findings,
                        current_spec,
                    )
                    adaptations.extend(critic_adaptations)
                if adaptations:
                    current_spec = apply_adaptations(current_spec, adaptations)
                    for a in adaptations:
                        msg = f"v{iteration:03d}→v{iteration + 1:03d}: {a.reason}"
                        adaptations_log.append(msg)
                        combined_provenance.record(
                            layer="conductor",
                            operation="adapt_spec",
                            parameters={
                                "field": a.field,
                                "old": a.old_value,
                                "new": a.new_value,
                            },
                            source="Conductor.compose_from_spec",
                            rationale=a.reason,
                        )
                else:
                    # No adaptations possible — try a different seed
                    current_seed = current_spec.generation.seed or 42
                    new_gen = current_spec.generation.model_copy(update={"seed": current_seed + iteration})
                    current_spec = current_spec.model_copy(update={"generation": new_gen})
                    adaptations_log.append(
                        f"v{iteration:03d}→v{iteration + 1:03d}: "
                        f"No targeted adaptations; trying seed={current_seed + iteration}"
                    )

        # Max iterations reached — return best result
        combined_provenance.record(
            layer="conductor",
            operation="workflow_complete",
            parameters={
                "iterations": max_iterations,
                "pass_rate": eval_report.pass_rate,
            },
            source="Conductor.compose_from_spec",
            rationale=f"Max iterations ({max_iterations}) reached. Final pass rate: {eval_report.pass_rate:.0%}.",
        )
        combined_provenance.save(output_dir / "provenance.json")

        return ConductorResult(
            score=score,
            spec=current_spec,
            midi_path=midi_path,
            stems=stems,
            analysis=analysis,
            evaluation=eval_report,
            provenance=combined_provenance,
            iterations=max_iterations,
            iteration_history=iteration_history,
            output_dir=output_dir,
            adaptations_applied=adaptations_log,
            critic_findings=critic_findings,
        )

    def regenerate_section(
        self,
        current_score: ScoreIR,
        spec: CompositionSpec,
        section_name: str,
        trajectory: TrajectorySpec | None = None,
        project_name: str | None = None,
        seed_override: int | None = None,
    ) -> ConductorResult:
        """Regenerate a single section while preserving all others.

        Args:
            current_score: The existing ScoreIR to modify.
            spec: The composition specification.
            section_name: Name of the section to regenerate (e.g., "chorus").
            trajectory: Optional trajectory for dynamic shaping.
            project_name: Project name for output directory.
            seed_override: Optional seed override for the regenerated section.

        Returns:
            ConductorResult with the merged composition.

        Raises:
            SpecValidationError: If the section name is not found.
        """
        from yao.errors import SpecValidationError

        if project_name is None:
            project_name = _slugify(spec.title)

        # Validate section exists
        section_specs = {s.name: s for s in spec.sections}
        if section_name not in section_specs:
            available = ", ".join(section_specs.keys())
            raise SpecValidationError(
                f"Section '{section_name}' not found. Available: {available}",
                field="section_name",
            )

        # Find the section in the current score
        old_section_idx = None
        for i, section in enumerate(current_score.sections):
            if section.name == section_name:
                old_section_idx = i
                break
        if old_section_idx is None:
            raise SpecValidationError(
                f"Section '{section_name}' not found in current score.",
                field="section_name",
            )

        provenance = ProvenanceLog()
        provenance.record(
            layer="conductor",
            operation="regenerate_section_start",
            parameters={
                "section": section_name,
                "seed_override": seed_override,
                "original_notes": sum(len(p.notes) for p in current_score.sections[old_section_idx].parts),
            },
            source="Conductor.regenerate_section",
            rationale=f"Regenerating section '{section_name}' while preserving others.",
        )

        # Build a temporary spec with only the target section
        target_section_spec = section_specs[section_name]
        gen_config = spec.generation
        if seed_override is not None:
            gen_config = gen_config.model_copy(update={"seed": seed_override})
        else:
            # Use a different seed than the original to get different output
            current_seed = gen_config.seed or 42
            gen_config = gen_config.model_copy(update={"seed": current_seed + 1000})

        temp_spec = spec.model_copy(
            update={
                "sections": [target_section_spec],
                "generation": gen_config,
            }
        )

        # Generate just this section via v2 pipeline (Rule A: Plan-First Boundary)
        new_score, _plan, gen_prov = generate_via_v2_pipeline(temp_spec, trajectory)

        for record in gen_prov.records:
            provenance.add(record)
        for dec in gen_prov.recoverables:
            provenance.record_recoverable(dec)

        # Extract the new section (it will be the only one in new_score)
        if not new_score.sections:
            raise SpecValidationError(
                f"Generator produced no sections for '{section_name}'.",
                field="section_name",
            )
        new_section = new_score.sections[0]

        # Remap the new section to have correct bar boundaries
        old_section = current_score.sections[old_section_idx]
        remapped_section = Section(
            name=section_name,
            start_bar=old_section.start_bar,
            end_bar=old_section.end_bar,
            parts=new_section.parts,
        )

        # Merge: replace the old section with the new one
        merged_sections = list(current_score.sections)
        merged_sections[old_section_idx] = remapped_section
        merged_score = ScoreIR(
            title=current_score.title,
            tempo_bpm=current_score.tempo_bpm,
            time_signature=current_score.time_signature,
            key=current_score.key,
            sections=tuple(merged_sections),
        )

        # Write outputs
        project_dir = Path(f"outputs/projects/{project_name}")
        output_dir = next_iteration_dir(project_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        midi_path = write_midi(merged_score, output_dir / "full.mid")
        stems = write_stems(merged_score, output_dir)

        analysis = analyze_score(merged_score)
        eval_report = evaluate_score(merged_score, spec, trajectory)
        analysis.save(output_dir / "analysis.json")
        eval_report.save(output_dir / "evaluation.json")

        provenance.record(
            layer="conductor",
            operation="regenerate_section_complete",
            parameters={
                "section": section_name,
                "new_notes": sum(len(p.notes) for p in remapped_section.parts),
                "total_notes": len(merged_score.all_notes()),
            },
            source="Conductor.regenerate_section",
            rationale=f"Section '{section_name}' regenerated and merged.",
        )
        provenance.save(output_dir / "provenance.json")

        logger.info(
            "conductor_regenerate_section",
            section=section_name,
            new_notes=sum(len(p.notes) for p in remapped_section.parts),
            total_notes=len(merged_score.all_notes()),
        )

        return ConductorResult(
            score=merged_score,
            spec=spec,
            midi_path=midi_path,
            stems=stems,
            analysis=analysis,
            evaluation=eval_report,
            provenance=provenance,
            iterations=1,
            output_dir=output_dir,
        )

    def _build_spec_from_description(
        self,
        description: str,
        project_name: str,
    ) -> tuple[CompositionSpec, TrajectorySpec]:
        """Build a CompositionSpec from a natural language description.

        Delegates to SpecCompiler which houses all musical knowledge
        (mood→key, pace→tempo, keyword→instruments).

        Args:
            description: Natural language description.
            project_name: Project name for the title.

        Returns:
            Tuple of (CompositionSpec, TrajectorySpec).
        """
        from yao.sketch.compiler import SpecCompiler

        compiler = SpecCompiler()
        return compiler.compile(description, project_name)


def _v1_to_v2_for_critic(spec: CompositionSpec) -> CompositionSpecV2:
    """Convert a v1 spec to v2 for the Adversarial Critic.

    The Critic's detect() methods accept CompositionSpecV2. This bridge
    converts on the fly during Phase α. Will be unnecessary when the
    Conductor migrates to v2 specs natively.
    """
    from yao.generators.legacy_adapter import _v1_to_v2

    return _v1_to_v2(spec)


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug for project names."""
    slug = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:40] if slug else "untitled"
