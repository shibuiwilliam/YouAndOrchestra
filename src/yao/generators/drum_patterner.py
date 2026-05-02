"""Drum pattern generator — produces drum hits across the song timeline.

Takes a DrumsSpec from composition.yaml and produces a list of DrumHit
objects placed across all sections. Applies swing, humanization, ghost
notes, and trajectory-driven intensity.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml

from yao.errors import SpecValidationError
from yao.ir.drum import DrumHit, DrumPattern
from yao.ir.timing import bars_to_beats
from yao.ir.trajectory import MultiDimensionalTrajectory, derive_generation_params
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec, DrumsSpec, SectionSpec

PATTERNS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "drum_patterns"


def load_pattern(family: str) -> DrumPattern:
    """Load a drum pattern from the YAML library.

    Args:
        family: Pattern family name (e.g., "pop_8beat").

    Returns:
        DrumPattern loaded from drum_patterns/<family>.yaml.

    Raises:
        SpecValidationError: If the pattern file is not found.
    """
    path = PATTERNS_DIR / f"{family}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in PATTERNS_DIR.glob("*.yaml"))
        raise SpecValidationError(
            f"Drum pattern '{family}' not found. Available: {available}",
            field="drums.pattern_family",
        )
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return DrumPattern(
        id=data["id"],
        genre=data["genre"],
        time_signature=data.get("time_signature", "4/4"),
        hits=tuple(
            DrumHit(
                time_beats=h["time_beats"],
                duration_beats=h["duration_beats"],
                kit_piece=h["kit_piece"],
                velocity=h["velocity"],
            )
            for h in data.get("hits", [])
        ),
        swing=data.get("swing", 0.0),
        humanize_ms=data.get("humanize_ms", 0.0),
        bars_per_pattern=data.get("bars_per_pattern", 1),
    )


def generate_drum_hits(
    spec: CompositionSpec,
    trajectory: MultiDimensionalTrajectory | None = None,
    seed: int = 42,
) -> tuple[list[DrumHit], ProvenanceLog]:
    """Generate drum hits for an entire composition.

    Args:
        spec: The composition specification (must have drums field).
        trajectory: Optional trajectory for dynamic shaping.
        seed: Random seed for humanization and ghost notes.

    Returns:
        Tuple of (drum hits list, ProvenanceLog).
    """
    provenance = ProvenanceLog()

    if spec.drums is None:
        return [], provenance

    drums_spec = spec.drums
    pattern = load_pattern(drums_spec.pattern_family)

    provenance.record(
        layer="generator",
        operation="drum_pattern_loaded",
        parameters={
            "pattern_id": pattern.id,
            "genre": pattern.genre,
            "swing": drums_spec.swing,
            "ghost_density": drums_spec.ghost_notes_density,
        },
        source="drum_patterner.generate_drum_hits",
        rationale=f"Loaded drum pattern '{pattern.id}' ({pattern.genre}).",
    )

    rng = random.Random(seed)
    traj = trajectory if trajectory is not None else MultiDimensionalTrajectory.default()
    all_hits: list[DrumHit] = []
    current_bar = 0

    for section in spec.sections:
        section_hits = _generate_section_hits(
            pattern=pattern,
            section=section,
            drums_spec=drums_spec,
            start_bar=current_bar,
            tempo_bpm=spec.tempo_bpm,
            time_signature=spec.time_signature,
            trajectory=traj,
            rng=rng,
        )
        all_hits.extend(section_hits)

        provenance.record(
            layer="generator",
            operation="drum_section_generated",
            parameters={
                "section": section.name,
                "hits": len(section_hits),
                "bars": section.bars,
            },
            source="drum_patterner._generate_section_hits",
            rationale=f"Generated {len(section_hits)} drum hits for section '{section.name}'.",
        )

        current_bar += section.bars

    return all_hits, provenance


def _generate_section_hits(
    *,
    pattern: DrumPattern,
    section: SectionSpec,
    drums_spec: DrumsSpec,
    start_bar: int,
    tempo_bpm: float,
    time_signature: str,
    trajectory: MultiDimensionalTrajectory,
    rng: random.Random,
) -> list[DrumHit]:
    """Generate drum hits for a single section by repeating the pattern.

    Applies swing, humanization, ghost notes, and trajectory density.
    """
    beats_per_bar = bars_to_beats(1, time_signature)
    hits: list[DrumHit] = []

    for bar_offset in range(section.bars):
        absolute_bar = start_bar + bar_offset
        bar_start_beat = bars_to_beats(absolute_bar, time_signature)

        # Trajectory: use density to thin out hits at low density
        params = derive_generation_params(trajectory, absolute_bar)
        density_factor = params.note_density_factor

        # Pattern cycle: which bar of the multi-bar pattern are we in?
        pattern_bar = bar_offset % pattern.bars_per_pattern

        for hit in pattern.hits:
            # Only place hits that belong to this pattern bar
            hit_bar = int(hit.time_beats / beats_per_bar) if beats_per_bar > 0 else 0
            if hit_bar != pattern_bar:
                continue

            # Position within the current bar
            hit_time_in_bar = hit.time_beats - (hit_bar * beats_per_bar)

            # Apply swing: offset off-beat 8th notes
            swung_time = _apply_swing(hit_time_in_bar, drums_spec.swing, beats_per_bar)

            # Apply humanization
            micro_ms = 0.0
            if drums_spec.humanize_ms > 0:
                micro_ms = rng.uniform(-drums_spec.humanize_ms, drums_spec.humanize_ms)

            # Density thinning: at low density, randomly drop non-essential hits
            if (
                density_factor < 0.8  # noqa: PLR2004
                and hit.kit_piece not in ("kick", "snare")
                and rng.random() > density_factor
            ):
                continue

            absolute_time = bar_start_beat + swung_time

            hits.append(
                DrumHit(
                    time_beats=absolute_time,
                    duration_beats=hit.duration_beats,
                    kit_piece=hit.kit_piece,
                    velocity=hit.velocity,
                    microtiming_ms=micro_ms,
                )
            )

        # Ghost notes: add soft snare/hat hits between main hits
        if drums_spec.ghost_notes_density > 0:
            ghost_hits = _generate_ghost_notes(
                bar_start_beat,
                beats_per_bar,
                drums_spec.ghost_notes_density,
                rng,
            )
            hits.extend(ghost_hits)

    return hits


def _apply_swing(time_in_bar: float, swing: float, beats_per_bar: float) -> float:
    """Apply swing to an off-beat position.

    Swing shifts off-beat 8th notes later. A swing of 0.67 makes the
    off-beat 2/3 of the way to the next beat (triplet feel).

    Args:
        time_in_bar: Original position in beats within the bar.
        swing: Swing amount (0.0=straight, 0.67=hard swing).
        beats_per_bar: Beats per bar.

    Returns:
        Swung time position.
    """
    if swing == 0.0:
        return time_in_bar

    # Check if this is an off-beat 8th (0.5, 1.5, 2.5, 3.5)
    fractional = time_in_bar % 1.0
    if abs(fractional - 0.5) < 0.01:
        # Shift the off-beat: 0.5 → 0.5 + swing * 0.5
        shift = swing * 0.25
        return time_in_bar + shift

    return time_in_bar


def _generate_ghost_notes(
    bar_start: float,
    beats_per_bar: float,
    density: float,
    rng: random.Random,
) -> list[DrumHit]:
    """Generate ghost notes (very soft snare/hat fills).

    Args:
        bar_start: Beat position of bar start.
        beats_per_bar: Beats per bar.
        density: Ghost note density (0.0–1.0).
        rng: Random generator.

    Returns:
        List of ghost DrumHit objects.
    """
    ghosts: list[DrumHit] = []
    # Check 16th note positions for ghost placement
    for sixteenth in range(int(beats_per_bar * 4)):
        pos = sixteenth * 0.25
        if rng.random() < density * 0.3:
            ghosts.append(
                DrumHit(
                    time_beats=bar_start + pos,
                    duration_beats=0.125,
                    kit_piece="snare",
                    velocity=rng.randint(25, 45),
                    microtiming_ms=rng.uniform(-3, 3),
                )
            )
    return ghosts
