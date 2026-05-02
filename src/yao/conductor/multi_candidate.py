"""Multi-candidate orchestrator — parallel plan generation + critic ranking.

Generates N musical plans with different seeds in parallel, ranks them
by Adversarial Critic severity, and selects the best one. This implements
PROJECT.md §6.3 "Multi-Candidate Generation and Selection".

Belongs to Layer 7 (Conductor).
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass

import structlog

from yao.generators.legacy_adapter import _v1_to_v2, build_plan_from_v1
from yao.ir.plan.musical_plan import MusicalPlan
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec, GenerationConfig
from yao.schema.trajectory import TrajectorySpec
from yao.verify.critique import CRITIQUE_RULES
from yao.verify.critique.types import Finding

logger = structlog.get_logger()

# Severity weights for ranking (CLAUDE.md Tier 2 Rules)
_SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 10,
    "major": 3,
    "minor": 1,
    "suggestion": 0,
}


@dataclass(frozen=True)
class CandidateScore:
    """A scored candidate plan.

    Attributes:
        plan: The generated MusicalPlan.
        provenance: Provenance from this candidate's generation.
        seed: The seed used for this candidate.
        findings: Critique findings for this candidate.
        weighted_severity: Weighted sum of finding severities.
    """

    plan: MusicalPlan
    provenance: ProvenanceLog
    seed: int
    findings: tuple[Finding, ...]
    weighted_severity: float


def _compute_weighted_severity(findings: list[Finding]) -> float:
    """Compute weighted severity sum from findings.

    Args:
        findings: List of critique findings.

    Returns:
        Weighted sum: critical*10 + major*3 + minor*1 + suggestion*0.
    """
    total = 0.0
    for f in findings:
        total += _SEVERITY_WEIGHTS.get(f.severity.value, 0)
    return total


class MultiCandidateOrchestrator:
    """Generates multiple plan candidates and selects the best.

    Usage::

        mco = MultiCandidateOrchestrator()
        candidates = mco.generate_candidates(spec, trajectory, n=5)
        ranked = mco.critic_rank(candidates, spec)
        best = mco.producer_select(ranked)
    """

    def generate_candidates(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
        n: int = 5,
        base_seed: int = 42,
    ) -> list[tuple[MusicalPlan, ProvenanceLog, int]]:
        """Generate N plan candidates with different seeds in parallel.

        Args:
            spec: Composition specification.
            trajectory: Optional trajectory.
            n: Number of candidates (default 5, max 10).
            base_seed: Base seed; each candidate uses base_seed + i.

        Returns:
            List of (MusicalPlan, ProvenanceLog, seed) tuples.
            Failed candidates are excluded.
        """
        n = min(max(n, 1), 10)
        seeds = [base_seed + i for i in range(n)]

        results: list[tuple[MusicalPlan, ProvenanceLog, int]] = []

        def _build_one(seed: int) -> tuple[MusicalPlan, ProvenanceLog, int]:
            # Create a spec variant with the candidate's seed
            modified_gen = GenerationConfig(
                strategy=spec.generation.strategy,
                seed=seed,
                temperature=spec.generation.temperature,
            )
            modified_spec = CompositionSpec(
                title=spec.title,
                genre=spec.genre,
                key=spec.key,
                tempo_bpm=spec.tempo_bpm,
                time_signature=spec.time_signature,
                total_bars=spec.total_bars,
                instruments=spec.instruments,
                sections=spec.sections,
                drums=spec.drums,
                generation=modified_gen,
            )
            plan, prov = build_plan_from_v1(modified_spec, trajectory)
            return plan, prov, seed

        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
            futures = {executor.submit(_build_one, s): s for s in seeds}
            for future in concurrent.futures.as_completed(futures):
                seed = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception:
                    logger.warning(
                        "candidate_generation_failed",
                        seed=seed,
                    )

        # Sort by seed for deterministic ordering
        results.sort(key=lambda r: r[2])
        return results

    def critic_rank(
        self,
        candidates: list[tuple[MusicalPlan, ProvenanceLog, int]],
        spec: CompositionSpec,
    ) -> list[CandidateScore]:
        """Rank candidates by Adversarial Critic severity.

        Args:
            candidates: List of (plan, provenance, seed) tuples.
            spec: The composition spec (for v2 conversion).

        Returns:
            List of CandidateScore sorted by weighted_severity (lowest first).
        """
        spec_v2 = _v1_to_v2(spec)
        scores: list[CandidateScore] = []

        for plan, prov, seed in candidates:
            findings = CRITIQUE_RULES.run_all(plan, spec_v2)
            severity = _compute_weighted_severity(findings)
            scores.append(
                CandidateScore(
                    plan=plan,
                    provenance=prov,
                    seed=seed,
                    findings=tuple(findings),
                    weighted_severity=severity,
                )
            )

        scores.sort(key=lambda s: (s.weighted_severity, s.seed))
        return scores

    def producer_select(
        self,
        ranked: list[CandidateScore],
        provenance: ProvenanceLog | None = None,
    ) -> MusicalPlan:
        """Select the best candidate.

        Currently selects top-1 by lowest severity score.
        Future: _candidates_complementary check for merge.

        Args:
            ranked: Candidates sorted by weighted_severity.
            provenance: Optional provenance to record the selection.

        Returns:
            The selected MusicalPlan.

        Raises:
            ValueError: If no candidates available.
        """
        if not ranked:
            msg = "No candidates to select from"
            raise ValueError(msg)

        best = ranked[0]

        if provenance is not None:
            provenance.record(
                layer="conductor",
                operation="multi_candidate_select",
                parameters={
                    "n_candidates": len(ranked),
                    "selected_seed": best.seed,
                    "selected_severity": best.weighted_severity,
                    "all_seeds": [c.seed for c in ranked],
                    "all_severities": [c.weighted_severity for c in ranked],
                },
                source="MultiCandidateOrchestrator.producer_select",
                rationale=(
                    f"Selected candidate seed={best.seed} with severity "
                    f"{best.weighted_severity} from {len(ranked)} candidates."
                ),
            )

        return best.plan
