"""Stochastic note realizer — realizes MusicalPlan into ScoreIR.

This wraps the legacy StochasticGenerator, converting the MusicalPlan
back to a v1-compatible spec for the existing generation logic.

Phase β will rewrite this to read MusicalPlan directly.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from yao.generators.note.base import NoteRealizerBase, register_note_realizer
from yao.generators.note.rule_based import _plan_to_traj_spec, _plan_to_v1_spec
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec


@register_note_realizer("stochastic")
class StochasticNoteRealizer(NoteRealizerBase):
    """Note realizer backed by the legacy stochastic generator."""

    def realize(
        self,
        plan: MusicalPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
        original_spec: CompositionSpec | None = None,
    ) -> ScoreIR:
        """Realize a MusicalPlan into ScoreIR via the stochastic generator.

        Args:
            plan: The musical plan.
            seed: Random seed for reproducibility.
            temperature: Variation control (0.0–1.0).
            provenance: Provenance log.
            original_spec: Optional original v1 spec to preserve metadata.

        Returns:
            ScoreIR with concrete notes.
        """
        from yao.generators.stochastic import StochasticGenerator
        from yao.schema.composition import GenerationConfig

        v1_spec = original_spec if original_spec is not None else _plan_to_v1_spec(plan)
        # Override generation config with realizer parameters
        v1_spec = v1_spec.model_copy(
            update={
                "generation": GenerationConfig(
                    strategy="stochastic",
                    seed=seed,
                    temperature=temperature,
                ),
            }
        )
        traj_spec = _plan_to_traj_spec(plan)

        provenance.record(
            layer="generator",
            operation="note_realization",
            parameters={
                "realizer": "stochastic",
                "seed": seed,
                "temperature": temperature,
            },
            source="StochasticNoteRealizer.realize",
            rationale=f"Realizing MusicalPlan via legacy stochastic generator (seed={seed}).",
        )

        gen = StochasticGenerator()
        score, gen_prov = gen.generate(v1_spec, trajectory=traj_spec)

        for rec in gen_prov.records:
            provenance.add(rec)
        for dec in gen_prov.recoverables:
            provenance.record_recoverable(dec)

        return score
