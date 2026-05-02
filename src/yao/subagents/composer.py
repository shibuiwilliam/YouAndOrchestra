"""Composer Subagent — generates motifs, phrases, and thematic material.

Mirrors .claude/agents/composer.md.
Does NOT choose instruments (Orchestrator's job).
Does NOT evaluate quality (Critic's job).

v3.0 Wave 1.1: Full implementation using motif_generation and motif_placement
modules. Guarantees MotifPlan.seeds is never empty.

Belongs to Layer 7 (Reflection — Subagent system).
"""

from __future__ import annotations

from yao.ir.motif_generation import generate_motif_seeds
from yao.ir.motif_placement import place_motifs
from yao.ir.plan.motif import MotifPlan
from yao.ir.plan.phrase import (
    Phrase,
    PhraseCadence,
    PhraseContour,
    PhrasePlan,
    PhraseRole,
)
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)


def _build_phrase_plan(
    context: AgentContext,
    bars_per_phrase: float = 4.0,
) -> PhrasePlan:
    """Build a PhrasePlan from the form plan.

    Creates antecedent-consequent phrase pairs within each section,
    with contours derived from section tension targets.

    Args:
        context: Pipeline state with form_plan and trajectory.
        bars_per_phrase: Default phrase length in bars.

    Returns:
        PhrasePlan with phrases covering all sections.
    """
    form = context.form_plan
    if form is None:
        return PhrasePlan(phrases=[], bars_per_phrase=bars_per_phrase, pattern="")

    phrases: list[Phrase] = []
    pattern_chars: list[str] = []
    phrase_idx = 0
    beats_per_bar = 4.0  # Default for 4/4

    # Map section roles to phrase pattern letters
    role_to_letter = {"verse": "A", "chorus": "B", "bridge": "C", "solo": "D"}

    for section in form.sections:
        section_beats = section.bars * beats_per_bar
        section_start = section.start_bar * beats_per_bar
        n_phrases = max(1, round(section.bars / bars_per_phrase))
        phrase_length = section_beats / n_phrases

        # Assign pattern letter
        letter = role_to_letter.get(section.role, "X")
        pattern_chars.append(letter)

        # Select contour based on tension
        if section.target_tension >= 0.7:  # noqa: PLR2004
            contour = PhraseContour.ARCH
        elif section.target_tension <= 0.3:  # noqa: PLR2004
            contour = PhraseContour.FALL if section.role == "outro" else PhraseContour.FLAT
        else:
            contour = PhraseContour.WAVE

        for j in range(n_phrases):
            phrase_idx += 1
            start = section_start + j * phrase_length

            # Alternate antecedent/consequent pairs
            if n_phrases >= 2:  # noqa: PLR2004
                role = PhraseRole.ANTECEDENT if j % 2 == 0 else PhraseRole.CONSEQUENT
            else:
                role = PhraseRole.STAND_ALONE

            # Last phrase in section gets a cadence
            if j == n_phrases - 1:
                if section.role in ("chorus", "outro", "coda"):
                    cadence = PhraseCadence.AUTHENTIC
                elif section.role == "bridge":
                    cadence = PhraseCadence.HALF
                else:
                    cadence = PhraseCadence.HALF if role == PhraseRole.ANTECEDENT else PhraseCadence.AUTHENTIC
            else:
                cadence = PhraseCadence.NONE

            phrases.append(
                Phrase(
                    id=f"P{phrase_idx}",
                    section_id=section.id,
                    start_beat=round(start, 2),
                    length_beats=round(phrase_length, 2),
                    role=role,
                    contour=contour,
                    cadence=cadence,
                    peak_position=0.7 if section.is_climax else 0.6,
                )
            )

    return PhrasePlan(
        phrases=phrases,
        bars_per_phrase=bars_per_phrase,
        pattern="".join(pattern_chars),
    )


@register_subagent(AgentRole.COMPOSER)
class ComposerSubagent(SubagentBase):
    """Generates motif and phrase plans from spec, intent, and trajectory.

    Responsibility boundary:
    - Owns: MotifPlan, PhrasePlan
    - Does NOT own: instruments, voicings, evaluation

    v3.0 guarantee: MotifPlan.seeds is never empty (len >= 1).
    """

    role = AgentRole.COMPOSER

    def process(self, context: AgentContext) -> AgentOutput:
        """Generate motif and phrase plans.

        Uses motif_generation for seed creation (Markov bigram + intent)
        and motif_placement for section distribution (>= 3 per motif).

        Args:
            context: Pipeline state with spec, intent, trajectory, form_plan.

        Returns:
            AgentOutput with non-empty motif_plan and phrase_plan.
        """
        prov = ProvenanceLog()

        # Get form plan (must exist — Producer runs before Composer)
        form = context.form_plan
        if form is None:
            from yao.ir.plan.song_form import SectionPlan, SongFormPlan

            # Fallback: single section from spec
            form = SongFormPlan(
                sections=[
                    SectionPlan(
                        id="verse",
                        start_bar=0,
                        bars=context.spec.total_bars,
                        role="verse",
                        target_density=0.5,
                        target_tension=0.5,
                    )
                ],
                climax_section_id="verse",
            )

        # Extract seed from spec generation config
        gen_seed = getattr(context.spec.generation, "seed", 42) or 42

        # Stage A: Generate motif seeds
        seeds = generate_motif_seeds(
            intent=context.intent,
            form=form,
            seed=gen_seed,
        )

        prov.record(
            layer="subagent",
            operation="motif_generation",
            parameters={
                "seed_count": len(seeds),
                "seed_ids": [s.id for s in seeds],
                "characters": [s.character for s in seeds],
                "intent_keywords": context.intent.keywords[:5],
            },
            source="ComposerSubagent.process",
            rationale=(f"Generated {len(seeds)} motif seed(s) from intent keywords and Markov bigram model."),
        )

        # Stage B: Place motifs across sections
        placements = place_motifs(
            seeds=seeds,
            form=form,
            seed=gen_seed,
        )

        motif_plan = MotifPlan(seeds=seeds, placements=placements)

        # Record placement provenance with identity strength breakdown
        for s in seeds:
            from yao.ir.motif_generation import _compute_identity_strength

            identity = _compute_identity_strength(s.rhythm_shape, s.interval_shape)
            recurrence = motif_plan.recurrence_count(s.id)
            prov.record(
                layer="subagent",
                operation="motif_placement",
                parameters={
                    "motif_id": s.id,
                    "recurrence_count": recurrence,
                    "identity_strength": identity,
                    "origin_section": s.origin_section,
                },
                source="ComposerSubagent.process",
                rationale=(
                    f"Motif {s.id} placed {recurrence} times. "
                    f"Identity strength {identity:.3f} "
                    f"(rhythm + interval specificity)."
                ),
            )

        # Build phrase plan
        phrase_plan = _build_phrase_plan(context)

        prov.record(
            layer="subagent",
            operation="composer_complete",
            parameters={
                "motif_count": len(motif_plan.seeds),
                "placement_count": len(motif_plan.placements),
                "phrase_count": len(phrase_plan.phrases),
                "phrase_pattern": phrase_plan.pattern,
            },
            source="ComposerSubagent.process",
            rationale=(
                f"Composer generated {len(motif_plan.seeds)} motifs with "
                f"{len(motif_plan.placements)} placements and "
                f"{len(phrase_plan.phrases)} phrases (pattern: {phrase_plan.pattern})."
            ),
        )

        return AgentOutput(
            provenance=prov,
            motif_plan=motif_plan,
            phrase_plan=phrase_plan,
        )
