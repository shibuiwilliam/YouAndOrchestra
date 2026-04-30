"""Rule-based note realizer — realizes MusicalPlan into ScoreIR.

This wraps the legacy RuleBasedGenerator, converting the MusicalPlan
back to a v1-compatible spec for the existing generation logic.
The legacy generator remains the workhorse; this adapter ensures it
participates in the v2 pipeline.

Phase β will rewrite this to read MusicalPlan directly.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from yao.generators.note.base import NoteRealizerBase, register_note_realizer
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec
    from yao.schema.trajectory import TrajectorySpec


@register_note_realizer("rule_based")
class RuleBasedNoteRealizer(NoteRealizerBase):
    """Note realizer backed by the legacy rule-based generator."""

    def realize(
        self,
        plan: MusicalPlan,
        seed: int,
        temperature: float,
        provenance: ProvenanceLog,
        original_spec: CompositionSpec | None = None,
    ) -> ScoreIR:
        """Realize a MusicalPlan into ScoreIR.

        Args:
            plan: The musical plan.
            seed: Random seed (unused in rule_based, deterministic).
            temperature: Variation control (unused in rule_based).
            provenance: Provenance log.
            original_spec: Optional original v1 spec to preserve metadata
                (key, tempo, time_signature, instruments) during Phase α.

        Returns:
            ScoreIR with concrete notes.
        """
        from yao.generators.rule_based import RuleBasedGenerator

        v1_spec = original_spec if original_spec is not None else _plan_to_v1_spec(plan)
        traj_spec = _plan_to_traj_spec(plan)

        provenance.record(
            layer="generator",
            operation="note_realization",
            parameters={"realizer": "rule_based", "seed": seed},
            source="RuleBasedNoteRealizer.realize",
            rationale="Realizing MusicalPlan via legacy rule-based generator.",
        )

        gen = RuleBasedGenerator()
        score, gen_prov = gen.generate(v1_spec, trajectory=traj_spec)

        for rec in gen_prov.records:
            provenance.add(rec)
        for dec in gen_prov.recoverables:
            provenance.record_recoverable(dec)

        return score


def _plan_to_v1_spec(plan: MusicalPlan) -> CompositionSpec:
    """Convert a MusicalPlan to a v1 CompositionSpec for legacy generators.

    Uses GlobalContext from the plan to preserve key, tempo, time signature,
    and instruments. Falls back to defaults if GlobalContext is empty.
    """
    from yao.schema.composition import (
        CompositionSpec,
        GenerationConfig,
        InstrumentSpec,
        SectionSpec,
    )

    ctx = plan.global_context

    sections = [
        SectionSpec(
            name=s.id,
            bars=s.bars,
            dynamics=_tension_to_dynamics(s.target_tension),
        )
        for s in plan.form.sections
    ]

    # Use instruments from GlobalContext, falling back to piano
    if ctx.instruments:
        instruments = [
            InstrumentSpec(name=name, role=role)  # type: ignore[arg-type]
            for name, role in ctx.instruments
        ]
    else:
        instruments = [InstrumentSpec(name="piano", role="melody")]

    return CompositionSpec(
        title=plan.intent.text[:50] if plan.intent.text else "Untitled",
        key=ctx.key,
        tempo_bpm=ctx.tempo_bpm,
        time_signature=ctx.time_signature,
        genre=ctx.genre,
        instruments=instruments,
        sections=sections,
        generation=GenerationConfig(strategy="rule_based"),
    )


def _plan_to_traj_spec(plan: MusicalPlan) -> TrajectorySpec | None:
    """Convert plan trajectory to a v1 TrajectorySpec."""
    from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint

    waypoints = []
    for section in plan.form.sections:
        waypoints.append(Waypoint(bar=section.start_bar, value=section.target_tension))
    if not waypoints:
        return None
    return TrajectorySpec(
        tension=TrajectoryDimension(type="bezier", waypoints=waypoints),
    )


def _tension_to_dynamics(tension: float) -> str:
    """Map tension [0,1] to a dynamics marking.

    Delegates to the canonical mapping in constants/music.py.
    """
    from yao.constants.music import tension_to_dynamics

    return tension_to_dynamics(tension)
