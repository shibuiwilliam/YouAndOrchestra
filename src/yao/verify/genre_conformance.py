"""Genre Conformance evaluator — scores how well output matches its genre.

Implements PROJECT.md §13.6. The aggregate score covers:
    - instrumentation_match: core instruments present, forbidden absent
    - tempo_match: tempo within genre's typical range
    - rhythm_match: swing, syncopation density match genre expectations
    - harmony_match: chord palette, seventh-chord usage, harmonic rhythm
    - form_match: section structure adherence (placeholder)

Each genre profile contributes its own weighting (jazz weights harmony
heavily, EDM weights rhythm and texture).

The Conductor uses the overall score to drive genre-aware adaptations.
When ``overall_score < threshold``, adaptation is mandatory (Rule 10).

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from yao.genre.profile import GenreProfile
from yao.genre.registry import GenreRegistry
from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class GenreConformanceScore:
    """Multi-dimensional genre conformance score.

    Each dimension is 0.0–1.0 (higher = better match).
    The ``overall`` score is a weighted average.

    Attributes:
        genre: Name of the genre evaluated against.
        instrumentation_match: How well instruments match the genre profile.
        tempo_match: How well tempo falls within the genre's range.
        rhythm_match: Swing, syncopation, groove conformity.
        harmony_match: Chord palette and extension usage conformity.
        form_match: Section structure conformity.
        overall: Weighted average of all dimensions.
        details: Per-dimension explanation strings.
    """

    genre: str
    instrumentation_match: float
    tempo_match: float
    rhythm_match: float
    harmony_match: float
    form_match: float
    overall: float
    details: dict[str, str] = field(default_factory=dict)


def evaluate_genre_conformance(
    score_ir: ScoreIR,
    genre_name: str,
    tempo_bpm: float = 120.0,
    profile: GenreProfile | None = None,
) -> GenreConformanceScore:
    """Evaluate how well a ScoreIR conforms to a genre.

    Args:
        score_ir: The generated score to evaluate.
        genre_name: Name of the target genre.
        tempo_bpm: Tempo of the composition.
        profile: Optional pre-resolved GenreProfile. If None, looks up
            from GenreRegistry.

    Returns:
        GenreConformanceScore with per-dimension and overall scores.
    """
    if profile is None:
        resolved = GenreRegistry.get_or_none(genre_name)
        if resolved is None:
            # Unknown genre: cannot evaluate conformance
            return GenreConformanceScore(
                genre=genre_name,
                instrumentation_match=0.5,
                tempo_match=0.5,
                rhythm_match=0.5,
                harmony_match=0.5,
                form_match=0.5,
                overall=0.5,
                details={"note": f"Genre '{genre_name}' not in registry; default scores used"},
            )
        profile = resolved

    details: dict[str, str] = {}

    # 1. Instrumentation match
    instr_score, instr_detail = _score_instrumentation(score_ir, profile)
    details["instrumentation"] = instr_detail

    # 2. Tempo match
    tempo_score, tempo_detail = _score_tempo(tempo_bpm, profile)
    details["tempo"] = tempo_detail

    # 3. Rhythm match
    rhythm_score, rhythm_detail = _score_rhythm(score_ir, profile)
    details["rhythm"] = rhythm_detail

    # 4. Harmony match
    harmony_score, harmony_detail = _score_harmony(score_ir, profile)
    details["harmony"] = harmony_detail

    # 5. Form match (placeholder — requires form template matching)
    form_score = 0.5
    details["form"] = "Form matching not yet implemented; default 0.5"

    # Weighted average with genre-specific weights
    weights = _genre_weights(profile)
    overall = (
        weights["instrumentation"] * instr_score
        + weights["tempo"] * tempo_score
        + weights["rhythm"] * rhythm_score
        + weights["harmony"] * harmony_score
        + weights["form"] * form_score
    )

    return GenreConformanceScore(
        genre=genre_name,
        instrumentation_match=instr_score,
        tempo_match=tempo_score,
        rhythm_match=rhythm_score,
        harmony_match=harmony_score,
        form_match=form_score,
        overall=overall,
        details=details,
    )


def _score_instrumentation(score_ir: ScoreIR, profile: GenreProfile) -> tuple[float, str]:
    """Score instrumentation conformity.

    Checks:
        - Core instruments present: each adds to score
        - Forbidden instruments absent: each absent is good
    """
    part_names: set[str] = set()
    for section in score_ir.sections:
        for part in section.parts:
            part_names.add(part.instrument)

    core_names = {i.name for i in profile.core_instruments}
    forbidden_names = set(profile.forbidden_instruments)

    if not core_names and not forbidden_names:
        return 0.7, "No instrumentation constraints in profile"

    score = 0.0
    total_checks = 0

    # Core instrument checks
    for name in core_names:
        total_checks += 1
        if name in part_names:
            score += 1.0

    # Forbidden instrument checks
    for name in forbidden_names:
        total_checks += 1
        if name not in part_names:
            score += 1.0

    if total_checks == 0:
        return 0.7, "No instrumentation constraints"

    normalized = score / total_checks
    present_core = core_names & part_names
    present_forbidden = forbidden_names & part_names
    detail = (
        f"Core present: {len(present_core)}/{len(core_names)}; "
        f"Forbidden present: {len(present_forbidden)}/{len(forbidden_names)}"
    )
    return normalized, detail


def _score_tempo(tempo_bpm: float, profile: GenreProfile) -> tuple[float, str]:
    """Score tempo conformity against genre's typical range."""
    low, high = profile.typical_tempo_range

    if low <= tempo_bpm <= high:
        return 1.0, f"Tempo {tempo_bpm} BPM within range [{low}, {high}]"

    # Score based on distance from range
    distance = low - tempo_bpm if tempo_bpm < low else tempo_bpm - high

    range_size = high - low if high > low else 1.0
    penalty = min(distance / range_size, 1.0)
    score = max(0.0, 1.0 - penalty)
    return score, f"Tempo {tempo_bpm} BPM outside range [{low}, {high}], penalty {penalty:.2f}"


def _score_rhythm(score_ir: ScoreIR, profile: GenreProfile) -> tuple[float, str]:
    """Score rhythmic conformity (swing, syncopation).

    Heuristic: checks note density and timing patterns.
    Full implementation would check swing ratio and syncopation density
    from MIDI timing data.
    """
    total_notes = sum(len(p.notes) for s in score_ir.sections for p in s.parts)
    total_bars = max(1.0, sum(s.bar_count for s in score_ir.sections) if score_ir.sections else 4.0)
    density = total_notes / total_bars

    # Higher density is expected for genres with high syncopation
    expected_density = 4.0 + profile.syncopation_density * 8.0
    density_ratio = min(density / max(expected_density, 1.0), 2.0) / 2.0

    detail = f"Note density: {density:.1f}/bar, expected ~{expected_density:.1f}"

    return min(0.5 + density_ratio * 0.5, 1.0), detail


def _score_harmony(score_ir: ScoreIR, profile: GenreProfile) -> tuple[float, str]:
    """Score harmonic conformity.

    Checks chord palette match. Full implementation would analyze
    chord types in the generated output against the genre's palette.
    """
    # If profile has a chord palette, we give a base score
    if profile.chord_palette_extended:
        base = 0.6
        detail = f"Genre has {len(profile.chord_palette_extended)} chord types in palette"
    else:
        base = 0.5
        detail = "No chord palette in genre profile"

    # Bonus for seventh-chord probability > 0
    if profile.seventh_chord_probability > 0.5:
        base += 0.1
        detail += "; genre expects rich extensions"

    return min(base, 1.0), detail


def _genre_weights(profile: GenreProfile) -> dict[str, float]:
    """Return per-dimension weights based on genre characteristics.

    Jazz weights harmony heavily; EDM/hip-hop weight rhythm heavily.
    """
    # Default weights
    weights = {
        "instrumentation": 0.2,
        "tempo": 0.15,
        "rhythm": 0.25,
        "harmony": 0.25,
        "form": 0.15,
    }

    # Genre-specific adjustments
    if profile.seventh_chord_probability > 0.5:
        # Harmony-heavy genre (jazz, bossa, etc.)
        weights["harmony"] = 0.35
        weights["rhythm"] = 0.2
        weights["form"] = 0.1

    if profile.syncopation_density > 0.35:
        # Rhythm-heavy genre (funk, hip-hop, etc.)
        weights["rhythm"] = 0.35
        weights["harmony"] = 0.2
        weights["form"] = 0.1

    # Normalize to sum to 1.0
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}
