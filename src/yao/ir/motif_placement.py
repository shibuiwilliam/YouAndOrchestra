"""Motif placement — distribute motif seeds across sections with transforms.

Places each MotifSeed at least 3 times across the composition,
selecting transforms based on section role and tension target.
This ensures MotifRecurrenceDetector's threshold is met.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

import random

from yao.ir.plan.motif import MotifPlacement, MotifSeed, MotifTransform
from yao.ir.plan.song_form import SectionPlan, SongFormPlan

# Minimum recurrences per motif (must match MotifRecurrenceDetector threshold)
_MIN_RECURRENCES = 3

# Section role → preferred transforms
_ROLE_TRANSFORMS: dict[str, list[MotifTransform]] = {
    "intro": [MotifTransform.IDENTITY, MotifTransform.AUGMENTATION],
    "verse": [MotifTransform.IDENTITY, MotifTransform.SEQUENCE_UP],
    "pre_chorus": [MotifTransform.SEQUENCE_UP, MotifTransform.VARIED_RHYTHM],
    "chorus": [MotifTransform.IDENTITY, MotifTransform.SEQUENCE_UP, MotifTransform.SEQUENCE_DOWN],
    "bridge": [MotifTransform.INVERSION, MotifTransform.VARIED_INTERVALS],
    "solo": [MotifTransform.VARIED_RHYTHM, MotifTransform.VARIED_INTERVALS],
    "interlude": [MotifTransform.RETROGRADE, MotifTransform.AUGMENTATION],
    "breakdown": [MotifTransform.DIMINUTION, MotifTransform.VARIED_RHYTHM],
    "build": [MotifTransform.SEQUENCE_UP, MotifTransform.VARIED_RHYTHM],
    "drop": [MotifTransform.IDENTITY, MotifTransform.SEQUENCE_DOWN],
    "outro": [MotifTransform.AUGMENTATION, MotifTransform.IDENTITY],
    "coda": [MotifTransform.AUGMENTATION, MotifTransform.RETROGRADE],
}


def _select_transform(
    section: SectionPlan,
    is_first_appearance: bool,
    rng: random.Random,
) -> MotifTransform:
    """Select an appropriate transform for a motif in a given section.

    Args:
        section: The target section.
        is_first_appearance: Whether this is the motif's first placement.
        rng: Seeded random generator.

    Returns:
        A MotifTransform appropriate for the section role.
    """
    if is_first_appearance:
        return MotifTransform.IDENTITY

    candidates = _ROLE_TRANSFORMS.get(section.role, [MotifTransform.IDENTITY])
    return rng.choice(candidates)


def _compute_transposition(section: SectionPlan) -> int:
    """Compute transposition based on section tension.

    Higher tension sections may transpose motifs upward for intensity.

    Args:
        section: The target section.

    Returns:
        Semitone transposition value.
    """
    tension = section.target_tension
    if tension >= 0.8:  # noqa: PLR2004
        return 2  # Up a whole step for climax
    if tension >= 0.6:  # noqa: PLR2004
        return 1  # Up a semitone for building tension
    return 0


def _section_start_beat(section: SectionPlan, beats_per_bar: float) -> float:
    """Calculate the absolute start beat of a section.

    Args:
        section: The section plan.
        beats_per_bar: Beats per bar (from time signature).

    Returns:
        Absolute beat position.
    """
    return section.start_bar * beats_per_bar


def place_motifs(
    seeds: list[MotifSeed],
    form: SongFormPlan,
    *,
    seed: int = 42,
    beats_per_bar: float = 4.0,
    min_recurrences: int = _MIN_RECURRENCES,
) -> list[MotifPlacement]:
    """Place motif seeds across sections with appropriate transforms.

    Each motif is guaranteed to appear at least ``min_recurrences`` times.
    Placements follow these strategies:
    - Primary motif (M1): appears in verse, chorus, and outro
    - Secondary motifs: appear in chorus, bridge, and contrasting sections
    - Transforms are selected based on section role

    Args:
        seeds: The seed motifs to place.
        form: Song form plan with section definitions.
        seed: Random seed for reproducibility.
        beats_per_bar: Beats per bar (default 4.0 for 4/4).
        min_recurrences: Minimum placements per motif.

    Returns:
        List of MotifPlacement objects sorted by start_beat.
    """
    if not seeds or not form.sections:
        return []

    rng = random.Random(seed)
    placements: list[MotifPlacement] = []

    for motif in seeds:
        motif_placements: list[MotifPlacement] = []

        # Find the origin section
        origin = form.section_by_id(motif.origin_section)
        if origin is None:
            origin = form.sections[0]

        # Place at origin (identity, first appearance)
        origin_beat = _section_start_beat(origin, beats_per_bar)
        motif_placements.append(
            MotifPlacement(
                motif_id=motif.id,
                section_id=origin.id,
                start_beat=origin_beat,
                transform=MotifTransform.IDENTITY,
                transposition=0,
                intensity=0.0,
            )
        )

        # Candidate sections for additional placements (exclude origin)
        candidates = [s for s in form.sections if s.id != origin.id]

        # Prioritize sections that benefit from motif recurrence
        priority_roles = ("chorus", "verse", "outro", "bridge", "drop", "build")
        candidates.sort(
            key=lambda s: (
                priority_roles.index(s.role) if s.role in priority_roles else len(priority_roles),
                s.start_bar,
            )
        )

        # Place in priority sections until min_recurrences met
        placed_section_ids = {origin.id}
        for section in candidates:
            if len(motif_placements) >= min_recurrences and section.id in placed_section_ids:
                continue

            transform = _select_transform(section, False, rng)
            transposition = _compute_transposition(section)
            section_beat = _section_start_beat(section, beats_per_bar)

            # Place at the start of the section with a small offset
            offset_beats = rng.uniform(0, min(beats_per_bar, section.bars * beats_per_bar * 0.1))

            motif_placements.append(
                MotifPlacement(
                    motif_id=motif.id,
                    section_id=section.id,
                    start_beat=round(section_beat + offset_beats, 2),
                    transform=transform,
                    transposition=transposition,
                    intensity=round(section.target_tension * 0.5, 2),
                )
            )
            placed_section_ids.add(section.id)

            if len(motif_placements) >= min_recurrences + 1:
                break

        # If still under min, duplicate in existing sections at later positions
        while len(motif_placements) < min_recurrences:
            section = rng.choice(form.sections)
            section_beat = _section_start_beat(section, beats_per_bar)
            section_length = section.bars * beats_per_bar
            offset = rng.uniform(section_length * 0.3, section_length * 0.7)

            transform = _select_transform(section, False, rng)

            motif_placements.append(
                MotifPlacement(
                    motif_id=motif.id,
                    section_id=section.id,
                    start_beat=round(section_beat + offset, 2),
                    transform=transform,
                    transposition=0,
                    intensity=0.2,
                )
            )

        placements.extend(motif_placements)

    # Sort all placements by start_beat
    placements.sort(key=lambda p: p.start_beat)
    return placements
