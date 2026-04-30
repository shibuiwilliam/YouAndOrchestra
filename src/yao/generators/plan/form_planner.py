"""Rule-based form planner — Step 1 of the generation pipeline.

Converts CompositionSpecV2 form sections into a SongFormPlan with
structural annotations (role, density, tension, climax).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from typing import Any, cast

from yao.generators.plan.base import PlanGeneratorBase, register_plan_generator
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2

# Map common section id patterns to roles
_ROLE_MAP: dict[str, str] = {
    "intro": "intro",
    "verse": "verse",
    "pre_chorus": "pre_chorus",
    "prechorus": "pre_chorus",
    "chorus": "chorus",
    "bridge": "bridge",
    "solo": "solo",
    "interlude": "interlude",
    "breakdown": "breakdown",
    "build": "build",
    "drop": "drop",
    "outro": "outro",
    "coda": "coda",
}


def _infer_role(section_id: str) -> str:
    """Infer structural role from section id.

    Args:
        section_id: Section identifier (e.g., "verse_a", "chorus").

    Returns:
        A valid role string.
    """
    lower = section_id.lower().replace("-", "_")
    # Try exact match first
    if lower in _ROLE_MAP:
        return _ROLE_MAP[lower]
    # Try prefix match (e.g., "verse_a" → "verse")
    for prefix, role in _ROLE_MAP.items():
        if lower.startswith(prefix):
            return role
    # Default: if contains common keywords
    for keyword in ("loop", "main", "theme"):
        if keyword in lower:
            return "verse"
    return "verse"  # safe default


@register_plan_generator("rule_based_form")
class RuleBasedFormPlanner(PlanGeneratorBase):
    """Deterministic form planner that maps spec sections to SongFormPlan."""

    def generate(
        self,
        spec: CompositionSpecV2,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> dict[str, Any]:
        """Generate a SongFormPlan from the spec's form sections.

        Args:
            spec: The v2 composition specification.
            trajectory: Multi-dimensional trajectory.
            provenance: Provenance log.

        Returns:
            Dict with "form" key containing a SongFormPlan.
        """
        sections: list[SectionPlan] = []
        current_bar = 0

        for s in spec.form.sections:
            role = _infer_role(s.id)
            tension_at_start = trajectory.value_at("tension", float(current_bar))
            sections.append(
                SectionPlan(
                    id=s.id,
                    start_bar=current_bar,
                    bars=s.bars,
                    role=cast(Any, role),
                    target_density=s.density,
                    target_tension=tension_at_start,
                    is_climax=s.climax,
                )
            )
            current_bar += s.bars

        climax_id = next(
            (s.id for s in sections if s.is_climax),
            sections[-1].id if sections else "",
        )

        form_plan = SongFormPlan(sections=sections, climax_section_id=climax_id)

        provenance.record(
            layer="generator",
            operation="form_planning",
            parameters={
                "generator": "rule_based_form",
                "climax_section": climax_id,
                "n_sections": len(sections),
                "total_bars": form_plan.total_bars(),
            },
            source="RuleBasedFormPlanner.generate",
            rationale=f"Form plan: {len(sections)} sections, climax at '{climax_id}'.",
        )

        return {"form": form_plan}
