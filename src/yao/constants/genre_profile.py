"""Genre profile data structure — structured genre parameters for generators.

Each genre profile encodes the harmonic, melodic, rhythmic, and voicing
preferences that make a genre *acoustically distinguishable*. Generators
consult these profiles to bias their output toward genre-specific signatures.

This resolves Bottleneck B from IMPROVEMENT.md: genre diversity is no longer
cosmetic (drum patterns only) but flows through chord palettes, voicing,
swing, contour, and dynamics.

Belongs to Layer 0 (Constants).
"""

from __future__ import annotations

import contextlib
import random
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class ContourType(StrEnum):
    """Melodic contour shapes."""

    ASCENDING = "ascending"
    DESCENDING = "descending"
    ARCH = "arch"
    VALLEY = "valley"
    FLAT = "flat"


class BassStyle(StrEnum):
    """Bass motion style."""

    WALKING = "walking"
    ROOT_FIFTH = "root_fifth"
    PEDAL = "pedal"
    ARPEGGIATED = "arpeggiated"
    SYNCOPATED = "syncopated"


@dataclass(frozen=True)
class GenreProfile:
    """A genre's complete musical fingerprint for generator consumption.

    All generators should consult this profile when the composition
    specifies a genre. The profile biases stochastic choices toward
    genre-appropriate output.

    Attributes:
        name: Genre identifier (e.g., "lofi_hiphop").
        chord_palette: Roman numerals of typical chords.
        progression_n_grams: Transition probabilities between chord pairs.
        seventh_chord_probability: How often to use 7th chords (0.0-1.0).
        secondary_dominant_probability: Probability of V/x chords.
        modal_interchange_probability: Probability of borrowed chords.
        melodic_contour_weights: Weight per contour type for melody generation.
        leap_probability: Probability of melodic leaps vs steps.
        blue_note_probability: Probability of blue notes (b3, b5, b7).
        swing_ratio: Swing amount (0.5=straight, 0.67=triplet swing).
        syncopation_density: How much syncopation (0.0-1.0).
        rhythm_template_weights: Weights for different rhythm templates.
        preferred_instruments: Instruments typical of this genre.
        voicing_density_target: Target number of voices in chords.
        bass_motion_style: How the bass moves.
        typical_dynamics_range: (soft, loud) dynamics range.
        target_spectral_centroid: Brightness target (0.0=dark, 1.0=bright).
        tempo_range: (min_bpm, max_bpm).
    """

    name: str

    # Harmonic preferences
    chord_palette: tuple[str, ...] = ()
    progression_n_grams: dict[tuple[str, str], float] = field(default_factory=dict)
    seventh_chord_probability: float = 0.3
    secondary_dominant_probability: float = 0.1
    modal_interchange_probability: float = 0.1

    # Melodic preferences
    melodic_contour_weights: dict[ContourType, float] = field(default_factory=dict)
    leap_probability: float = 0.3
    blue_note_probability: float = 0.0

    # Rhythmic preferences
    swing_ratio: float = 0.5
    syncopation_density: float = 0.3
    rhythm_template_weights: dict[str, float] = field(default_factory=dict)

    # Voicing & instrumentation
    preferred_instruments: tuple[str, ...] = ()
    voicing_density_target: int = 4
    bass_motion_style: BassStyle = BassStyle.ROOT_FIFTH

    # Dynamics & acoustics
    typical_dynamics_range: tuple[str, str] = ("mp", "f")
    target_spectral_centroid: float = 0.5
    tempo_range: tuple[float, float] = (80.0, 140.0)

    @classmethod
    def from_yaml(cls, data: dict[str, Any]) -> GenreProfile:
        """Construct a GenreProfile from a parsed YAML dict.

        Args:
            data: Parsed YAML data.

        Returns:
            GenreProfile instance.

        Raises:
            KeyError: If required 'name' field is missing.
        """
        name = data["name"]

        # Parse n-grams: YAML stores as {"I,IV": 0.3, ...}
        raw_ngrams = data.get("progression_n_grams", {})
        ngrams: dict[tuple[str, str], float] = {}
        for key_str, weight in raw_ngrams.items():
            parts = str(key_str).split(",")
            if len(parts) == 2:  # noqa: PLR2004
                ngrams[(parts[0].strip(), parts[1].strip())] = float(weight)

        # Parse contour weights
        raw_contours = data.get("melodic_contour_weights", {})
        contour_weights: dict[ContourType, float] = {}
        for cname, w in raw_contours.items():
            with contextlib.suppress(ValueError):
                contour_weights[ContourType(cname)] = float(w)

        # Parse dynamics range
        dyn_range = data.get("typical_dynamics_range", ["mp", "f"])
        if isinstance(dyn_range, list) and len(dyn_range) == 2:  # noqa: PLR2004
            dynamics_tuple = (str(dyn_range[0]), str(dyn_range[1]))
        else:
            dynamics_tuple = ("mp", "f")

        # Parse tempo range
        tempo_raw = data.get("tempo_range", [80, 140])
        if isinstance(tempo_raw, list) and len(tempo_raw) == 2:  # noqa: PLR2004
            tempo_tuple = (float(tempo_raw[0]), float(tempo_raw[1]))
        else:
            tempo_tuple = (80.0, 140.0)

        # Parse bass style
        bass_str = data.get("bass_motion_style", "root_fifth")
        try:
            bass_style = BassStyle(bass_str)
        except ValueError:
            bass_style = BassStyle.ROOT_FIFTH

        return cls(
            name=name,
            chord_palette=tuple(data.get("chord_palette", [])),
            progression_n_grams=ngrams,
            seventh_chord_probability=float(data.get("seventh_chord_probability", 0.3)),
            secondary_dominant_probability=float(data.get("secondary_dominant_probability", 0.1)),
            modal_interchange_probability=float(data.get("modal_interchange_probability", 0.1)),
            melodic_contour_weights=contour_weights,
            leap_probability=float(data.get("leap_probability", 0.3)),
            blue_note_probability=float(data.get("blue_note_probability", 0.0)),
            swing_ratio=float(data.get("swing_ratio", 0.5)),
            syncopation_density=float(data.get("syncopation_density", 0.3)),
            rhythm_template_weights=data.get("rhythm_template_weights", {}),
            preferred_instruments=tuple(data.get("preferred_instruments", [])),
            voicing_density_target=int(data.get("voicing_density_target", 4)),
            bass_motion_style=bass_style,
            typical_dynamics_range=dynamics_tuple,
            target_spectral_centroid=float(data.get("target_spectral_centroid", 0.5)),
            tempo_range=tempo_tuple,
        )


# ── Profile registry ──────────────────────────────────────────────────

_PROFILES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "genre_profiles"
_profiles: dict[str, GenreProfile] | None = None


def _load_all_profiles() -> dict[str, GenreProfile]:
    """Load all genre profiles from genre_profiles/ directory."""
    profiles: dict[str, GenreProfile] = {}
    if not _PROFILES_DIR.exists():
        return profiles

    for yaml_path in sorted(_PROFILES_DIR.glob("*.yaml")):
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "name" in data:
            profile = GenreProfile.from_yaml(data)
            profiles[profile.name] = profile

    return profiles


def get_genre_profile(genre_name: str) -> GenreProfile | None:
    """Load a genre profile by name.

    Args:
        genre_name: Genre identifier (e.g., "lofi_hiphop").

    Returns:
        GenreProfile if found, None otherwise.
    """
    global _profiles  # noqa: PLW0603
    if _profiles is None:
        _profiles = _load_all_profiles()
    return _profiles.get(genre_name)


def all_genre_profiles() -> dict[str, GenreProfile]:
    """Return all loaded genre profiles.

    Returns:
        Dict mapping genre name to GenreProfile.
    """
    global _profiles  # noqa: PLW0603
    if _profiles is None:
        _profiles = _load_all_profiles()
    return dict(_profiles)


def reload_profiles() -> None:
    """Reload all profiles from disk (for testing)."""
    global _profiles  # noqa: PLW0603
    _profiles = _load_all_profiles()


# ── Roman numeral → scale degree utilities ───────────────────────────

_ROMAN_TO_DEGREE: dict[str, int] = {
    "i": 0,
    "ii": 1,
    "iii": 2,
    "iv": 3,
    "v": 4,
    "vi": 5,
    "vii": 6,
}


def roman_to_degree(roman: str) -> int:
    """Convert a Roman numeral chord symbol to a 0-indexed scale degree.

    Handles accidentals (bVI → 5), quality suffixes (Imaj7 → 0, ii7 → 1),
    and case variations. Returns the base diatonic degree.

    Args:
        roman: Roman numeral string (e.g., "Imaj7", "bVII7", "vi", "IV").

    Returns:
        Scale degree 0-6.

    Example:
        >>> roman_to_degree("Imaj7")
        0
        >>> roman_to_degree("bVII7")
        6
        >>> roman_to_degree("vi")
        5
    """
    # Strip accidentals
    cleaned = roman.strip().lstrip("b").lstrip("#").lstrip("♭").lstrip("♯")
    # Strip quality suffixes: maj7, m7, 7, dim, aug, °, ø, +, M, etc.
    # Work from the right to find the core Roman numeral
    base = cleaned
    for suffix in ("maj7", "min7", "dim7", "aug7", "M7", "m7", "7", "maj", "min", "dim", "aug", "°", "ø", "+"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return _ROMAN_TO_DEGREE.get(base.lower(), 0)


def genre_chord_sequence(
    profile: GenreProfile,
    section_name: str,
    length: int,
    rng: random.Random,
) -> list[int]:
    """Generate a chord degree sequence biased by genre n-gram probabilities.

    Uses the profile's ``progression_n_grams`` as a first-order Markov chain.
    Falls back to uniform random selection from ``chord_palette`` when no
    matching n-gram transition exists.

    Args:
        profile: Genre profile with chord_palette and progression_n_grams.
        section_name: Section name (unused currently, reserved for future
            section-aware biasing).
        length: Number of chords to generate.
        rng: Random instance for reproducibility.

    Returns:
        List of scale degree integers (0-6), length ``length``.
    """
    palette_degrees = [roman_to_degree(r) for r in profile.chord_palette]
    if not palette_degrees:
        # Fallback: diatonic I-IV-V-vi
        palette_degrees = [0, 3, 4, 5]

    # Build n-gram transition table: degree → [(degree, weight), ...]
    transitions: dict[int, list[tuple[int, float]]] = {}
    for (from_roman, to_roman), weight in profile.progression_n_grams.items():
        from_deg = roman_to_degree(from_roman)
        to_deg = roman_to_degree(to_roman)
        transitions.setdefault(from_deg, []).append((to_deg, weight))

    # Start from a random chord in the palette
    result: list[int] = [rng.choice(palette_degrees)]

    for _ in range(length - 1):
        current = result[-1]
        options = transitions.get(current)
        if options:
            degrees, weights = zip(*options, strict=True)
            result.append(rng.choices(list(degrees), weights=list(weights), k=1)[0])
        else:
            # No n-gram from this chord — pick uniformly from palette
            result.append(rng.choice(palette_degrees))

    return result
