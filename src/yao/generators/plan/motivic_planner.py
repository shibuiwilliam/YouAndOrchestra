"""Motivic planner — generates MotifPlan from form and spec.

Creates seed motifs and plans their development across sections.
The primary motif appears in every section with appropriate transformations.
Bridge/development sections receive more aggressive transformations.
The final section returns to the primary motif for closure.

Heuristics (from IMPROVEMENT.md Proposal 3):
- Primary motif: 2-4 bars, chord-tone-dominated
- Each section gets at least one treatment of the primary motif
- Bridge/development: inverted, retrograde, augmented, fragmented
- Final section: original or closely related form (closure)

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random

from yao.generators.plan.base import PlanGeneratorBase, register_plan_generator
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed, MotifTransform
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2

# Contour patterns for different emotional intents
_ASCENDING_INTERVALS = (0, 2, 4, 5, 7)
_DESCENDING_INTERVALS = (7, 5, 4, 2, 0)
_ARCH_INTERVALS = (0, 2, 4, 5, 4, 2)
_VALLEY_INTERVALS = (5, 4, 2, 0, 2, 4)

# Rhythm templates for seed motifs (2-4 bars worth of beats)
_RHYTHM_TEMPLATES: list[tuple[float, ...]] = [
    (1.0, 1.0, 0.5, 0.5, 1.0),  # 4 beats: quarter-quarter-eighth-eighth-quarter
    (1.5, 0.5, 1.0, 1.0),  # 4 beats: dotted quarter-eighth-quarter-quarter
    (1.0, 1.0, 1.0, 1.0),  # 4 beats: straight quarters
    (0.5, 0.5, 1.0, 0.5, 0.5, 1.0),  # 4 beats: syncopated
    (2.0, 1.0, 0.5, 0.5),  # 4 beats: half-quarter-eighths
    (1.0, 0.5, 0.5, 1.0, 1.0),  # 4 beats: varied
]

# Section role → transformation strategy
_ROLE_TRANSFORMS: dict[str, list[MotifTransform]] = {
    "intro": [MotifTransform.IDENTITY, MotifTransform.AUGMENTATION],
    "verse": [MotifTransform.IDENTITY, MotifTransform.SEQUENCE_UP],
    "chorus": [MotifTransform.IDENTITY, MotifTransform.SEQUENCE_UP],
    "bridge": [MotifTransform.INVERSION, MotifTransform.RETROGRADE, MotifTransform.VARIED_INTERVALS],
    "development": [MotifTransform.INVERSION, MotifTransform.RETROGRADE, MotifTransform.DIMINUTION],
    "outro": [MotifTransform.IDENTITY, MotifTransform.AUGMENTATION],
}


@register_plan_generator("rule_based_motif")
class MotivicPlanner(PlanGeneratorBase):
    """Generates a MotifPlan with seed motifs and section placements.

    The planner creates 1-2 seed motifs and distributes them across
    all sections with role-appropriate transformations.
    """

    def generate(
        self,
        spec: CompositionSpecV2,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> dict[str, MotifPlan]:
        """Generate a motivic development plan.

        Args:
            spec: The v2 composition specification.
            trajectory: Multi-dimensional trajectory.
            provenance: Provenance log.

        Returns:
            Dict with "motif" key containing a MotifPlan.
        """
        seed_val = spec.generation.seed if spec.generation.seed is not None else 42
        rng = random.Random(seed_val)

        form_sections = spec.form.sections
        if not form_sections:
            return {"motif": MotifPlan(seeds=[], placements=[])}

        # Generate primary seed motif
        primary_seed = self._generate_seed(
            motif_id="M1",
            origin_section=form_sections[0].id,
            rng=rng,
            character="primary theme",
        )

        seeds = [primary_seed]
        placements: list[MotifPlacement] = []

        # Optionally generate secondary motif for longer pieces
        total_bars = sum(s.bars for s in form_sections)
        if total_bars >= 24 and len(form_sections) >= 3:  # noqa: PLR2004
            secondary_seed = self._generate_seed(
                motif_id="M2",
                origin_section=form_sections[1].id if len(form_sections) > 1 else form_sections[0].id,
                rng=rng,
                character="secondary theme",
            )
            seeds.append(secondary_seed)

        # Place motifs across sections
        beats_per_bar = 4.0  # Default; ideally from spec
        current_beat = 0.0

        for i, section in enumerate(form_sections):
            section_start_beat = current_beat
            section_beats = section.bars * beats_per_bar
            role = section.id.lower()

            # Determine transformation for this section
            available_transforms = _ROLE_TRANSFORMS.get(role, _ROLE_TRANSFORMS.get("verse", [MotifTransform.IDENTITY]))
            transform = rng.choice(available_transforms)

            # Final section: return to identity for closure
            is_final = i == len(form_sections) - 1
            if is_final:
                transform = MotifTransform.IDENTITY

            # Primary motif placement
            placements.append(
                MotifPlacement(
                    motif_id="M1",
                    section_id=section.id,
                    start_beat=section_start_beat,
                    transform=transform,
                    transposition=self._section_transposition(i, len(form_sections), rng),
                    intensity=0.0 if transform == MotifTransform.IDENTITY else 0.3,
                )
            )

            # Additional placement midway through longer sections
            if section.bars >= 8:  # noqa: PLR2004
                mid_beat = section_start_beat + section_beats / 2
                second_transform = rng.choice(available_transforms)
                placements.append(
                    MotifPlacement(
                        motif_id="M1",
                        section_id=section.id,
                        start_beat=mid_beat,
                        transform=second_transform,
                        transposition=self._section_transposition(i, len(form_sections), rng) + rng.choice([0, 2, -2]),
                        intensity=0.2,
                    )
                )

            # Secondary motif in non-primary sections
            if len(seeds) > 1 and role in ("bridge", "verse", "development"):
                secondary_beat = section_start_beat + section_beats * 0.25
                placements.append(
                    MotifPlacement(
                        motif_id="M2",
                        section_id=section.id,
                        start_beat=secondary_beat,
                        transform=MotifTransform.IDENTITY,
                        transposition=0,
                        intensity=0.0,
                    )
                )

            current_beat += section_beats

        motif_plan = MotifPlan(seeds=seeds, placements=placements)

        provenance.record(
            layer="generator",
            operation="motivic_planning",
            parameters={
                "seed_count": len(seeds),
                "placement_count": len(placements),
                "total_bars": total_bars,
                "sections": [s.id for s in form_sections],
            },
            source="MotivicPlanner.generate",
            rationale=(
                f"Generated {len(seeds)} seed motifs with {len(placements)} placements "
                f"across {len(form_sections)} sections."
            ),
        )

        return {"motif": motif_plan}

    def _generate_seed(
        self,
        motif_id: str,
        origin_section: str,
        rng: random.Random,
        character: str,
    ) -> MotifSeed:
        """Generate a seed motif with appropriate contour and rhythm.

        Args:
            motif_id: Unique identifier.
            origin_section: Section where motif first appears.
            rng: Random generator.
            character: Description of the motif.

        Returns:
            A MotifSeed instance.
        """
        rhythm = rng.choice(_RHYTHM_TEMPLATES)

        # Choose interval pattern based on character
        contour_options = [_ASCENDING_INTERVALS, _DESCENDING_INTERVALS, _ARCH_INTERVALS, _VALLEY_INTERVALS]
        base_intervals = rng.choice(contour_options)

        # Trim or extend to match rhythm length
        intervals = base_intervals[: len(rhythm)]
        if len(intervals) < len(rhythm):
            # Extend by cycling
            extended = list(intervals)
            while len(extended) < len(rhythm):
                extended.append(intervals[len(extended) % len(intervals)])
            intervals = tuple(extended)

        return MotifSeed(
            id=motif_id,
            rhythm_shape=rhythm,
            interval_shape=intervals,
            origin_section=origin_section,
            character=character,
        )

    def _section_transposition(self, section_idx: int, total_sections: int, rng: random.Random) -> int:
        """Determine transposition for a section's motif placement.

        Middle sections may transpose up; final section returns to 0.

        Args:
            section_idx: Index of the current section.
            total_sections: Total number of sections.
            rng: Random generator.

        Returns:
            Transposition in semitones.
        """
        if section_idx == 0 or section_idx == total_sections - 1:
            return 0
        return rng.choice([0, 0, 2, 3, 5, -2])
