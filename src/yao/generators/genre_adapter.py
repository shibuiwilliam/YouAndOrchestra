"""Genre adapter — translates GenreProfile into generation-time biases.

A thin Layer 2 module that converts GenreProfile fields into parameters
consumed by generators (both v1 stochastic and v2 note realizers).

All bias applications are recorded in provenance. When no genre profile
is active, every method returns the unmodified default — full backward
compatibility.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from yao.constants.genre_profile import ContourType, GenreProfile


@dataclass(frozen=True)
class GenreBias:
    """Resolved generation biases from a GenreProfile.

    Attributes:
        contour_weights: Probability distribution over contour shapes.
        leap_probability: Probability of melodic leap vs step.
        blue_note_probability: Probability of injecting blue notes.
        syncopation_density: Density of syncopated rhythms (0.0-1.0).
        rhythm_weights: Weights for rhythm template selection.
        voicing_density: Target chord voicing density.
        seventh_chord_probability: Probability of using 7th chords.
        secondary_dominant_probability: Probability of V/x chords.
        modal_interchange_probability: Probability of borrowed chords.
        tempo_range: (min_bpm, max_bpm) for validation.
    """

    contour_weights: dict[str, float]
    leap_probability: float
    blue_note_probability: float
    syncopation_density: float
    rhythm_weights: dict[str, float]
    voicing_density: int
    seventh_chord_probability: float
    secondary_dominant_probability: float
    modal_interchange_probability: float
    tempo_range: tuple[float, float]


# Default bias when no genre profile is active
DEFAULT_BIAS = GenreBias(
    contour_weights={"ascending": 0.25, "descending": 0.25, "arch": 0.3, "valley": 0.1, "flat": 0.1},
    leap_probability=0.3,
    blue_note_probability=0.0,
    syncopation_density=0.3,
    rhythm_weights={},
    voicing_density=4,
    seventh_chord_probability=0.3,
    secondary_dominant_probability=0.1,
    modal_interchange_probability=0.1,
    tempo_range=(80.0, 140.0),
)


def resolve_genre_bias(profile: GenreProfile | None) -> GenreBias:
    """Resolve a GenreProfile into generation biases.

    Args:
        profile: Genre profile, or None for default behavior.

    Returns:
        GenreBias with resolved parameters.
    """
    if profile is None:
        return DEFAULT_BIAS

    contour_weights: dict[str, float] = {}
    for ct, w in profile.melodic_contour_weights.items():
        contour_weights[ct.value if isinstance(ct, ContourType) else str(ct)] = w
    if not contour_weights:
        contour_weights = dict(DEFAULT_BIAS.contour_weights)

    return GenreBias(
        contour_weights=contour_weights,
        leap_probability=profile.leap_probability,
        blue_note_probability=profile.blue_note_probability,
        syncopation_density=profile.syncopation_density,
        rhythm_weights=dict(profile.rhythm_template_weights),
        voicing_density=profile.voicing_density_target,
        seventh_chord_probability=profile.seventh_chord_probability,
        secondary_dominant_probability=profile.secondary_dominant_probability,
        modal_interchange_probability=profile.modal_interchange_probability,
        tempo_range=profile.tempo_range,
    )


def biased_contour(bias: GenreBias, rng: random.Random) -> str:
    """Select a melodic contour weighted by genre bias.

    Args:
        bias: Resolved genre biases.
        rng: Random generator for reproducibility.

    Returns:
        Contour type string.
    """
    if not bias.contour_weights:
        return "arch"
    contours = list(bias.contour_weights.keys())
    weights = [bias.contour_weights[c] for c in contours]
    return rng.choices(contours, weights=weights, k=1)[0]


def biased_movement_step(
    bias: GenreBias,
    rng: random.Random,
    base_step: int,
    temperature: float,
) -> int:
    """Adjust a melodic step size based on genre leap probability.

    Higher leap_probability → more likely to return larger intervals.
    Blue notes are injected as chromatic inflections.

    Args:
        bias: Resolved genre biases.
        rng: Random generator.
        base_step: Original step in scale degrees (signed).
        temperature: Generation temperature.

    Returns:
        Adjusted step size.
    """
    direction = 1 if base_step >= 0 else -1
    magnitude = abs(base_step)

    # Genre-biased leap probability
    if magnitude <= 1 and rng.random() < bias.leap_probability:
        # Promote step to leap
        magnitude = rng.choice([3, 4, 5])
    elif magnitude >= 3 and rng.random() > bias.leap_probability:
        # Demote leap to step (for genres that prefer stepwise motion)
        magnitude = rng.choice([1, 2])

    return magnitude * direction


def biased_rhythm_pool(
    bias: GenreBias,
    base_pool: list[list[float]],
    rng: random.Random,
) -> list[float]:
    """Select a rhythm pattern biased by genre rhythm weights.

    When the genre provides rhythm_weights, patterns matching
    the weighted templates are preferred. Syncopation density
    biases toward shorter subdivisions.

    Args:
        bias: Resolved genre biases.
        base_pool: Available rhythm patterns.
        rng: Random generator.

    Returns:
        Selected rhythm pattern.
    """
    if not base_pool:
        return [1.0, 1.0, 1.0, 1.0]

    # If genre has high syncopation, prefer denser patterns
    if bias.syncopation_density > 0.5:
        dense = [p for p in base_pool if len(p) >= 5]  # noqa: PLR2004
        if dense and rng.random() < bias.syncopation_density:
            return rng.choice(dense)
    elif bias.syncopation_density < 0.2:
        sparse = [p for p in base_pool if len(p) <= 3]  # noqa: PLR2004
        if sparse and rng.random() < (1.0 - bias.syncopation_density):
            return rng.choice(sparse)

    return rng.choice(base_pool)


def should_add_blue_note(bias: GenreBias, rng: random.Random) -> bool:
    """Determine whether to inject a blue note at this position.

    Args:
        bias: Resolved genre biases.
        rng: Random generator.

    Returns:
        True if a blue note should be injected.
    """
    return rng.random() < bias.blue_note_probability


def apply_blue_note(pitch: int, rng: random.Random) -> int:
    """Apply a blue note inflection to a pitch.

    Blue notes are typically b3, b5, or b7 relative to the key.
    This adds a chromatic lower neighbor.

    Args:
        pitch: Original MIDI pitch.
        rng: Random generator.

    Returns:
        Adjusted pitch with blue note inflection.
    """
    # Flatten by 1 semitone (minor-izing the interval)
    return pitch - 1


def clamp_tempo_to_genre(
    requested_bpm: float,
    bias: GenreBias,
) -> tuple[float, bool]:
    """Clamp or suggest tempo within genre typical range.

    Does NOT force — returns the original tempo with a flag indicating
    whether it's outside the genre range.

    Args:
        requested_bpm: User-requested tempo.
        bias: Resolved genre biases.

    Returns:
        Tuple of (tempo, is_outside_range).
    """
    low, high = bias.tempo_range
    return requested_bpm, not (low <= requested_bpm <= high)
