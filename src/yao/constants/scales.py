"""Scale definitions with cents-based intervals.

All scales are defined as ``ScaleDefinition`` with intervals in cents.
12-EDO scales have intervals that are exact multiples of 100.
Microtonal scales have non-100-multiple intervals.

Each non-Western scale MUST have a ``cultural_context`` description.

Belongs to Layer 0 (Constants).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScaleDefinition:
    """A scale defined in cents from the root.

    For 12-EDO scales, ``intervals_cents`` equals semitones * 100.
    For microtonal scales, cents values may not be multiples of 100.

    Attributes:
        name: Scale identifier.
        intervals_cents: Intervals in cents from the root pitch.
        octave_cents: Size of one octave in cents (1200 for most tunings).
        cultural_context: Required cultural note. Empty for Western scales.
    """

    name: str
    intervals_cents: tuple[int, ...]
    octave_cents: int = 1200
    cultural_context: str = ""

    @property
    def is_12edo(self) -> bool:
        """Return True if all intervals are multiples of 100 cents."""
        return all(c % 100 == 0 for c in self.intervals_cents)

    @property
    def degree_count(self) -> int:
        """Number of scale degrees."""
        return len(self.intervals_cents)


# ---------------------------------------------------------------------------
# 12-EDO Western scales (backward compatible with SCALE_INTERVALS)
# ---------------------------------------------------------------------------

MAJOR = ScaleDefinition(
    name="major",
    intervals_cents=(0, 200, 400, 500, 700, 900, 1100),
)

MINOR = ScaleDefinition(
    name="minor",
    intervals_cents=(0, 200, 300, 500, 700, 800, 1000),
)

HARMONIC_MINOR = ScaleDefinition(
    name="harmonic_minor",
    intervals_cents=(0, 200, 300, 500, 700, 800, 1100),
)

DORIAN = ScaleDefinition(
    name="dorian",
    intervals_cents=(0, 200, 300, 500, 700, 900, 1000),
)

MIXOLYDIAN = ScaleDefinition(
    name="mixolydian",
    intervals_cents=(0, 200, 400, 500, 700, 900, 1000),
)

PENTATONIC_MAJOR = ScaleDefinition(
    name="pentatonic_major",
    intervals_cents=(0, 200, 400, 700, 900),
)

PENTATONIC_MINOR = ScaleDefinition(
    name="pentatonic_minor",
    intervals_cents=(0, 300, 500, 700, 1000),
)

BLUES = ScaleDefinition(
    name="blues",
    intervals_cents=(0, 300, 500, 600, 700, 1000),
)

CHROMATIC = ScaleDefinition(
    name="chromatic",
    intervals_cents=tuple(i * 100 for i in range(12)),
)

# ---------------------------------------------------------------------------
# North Indian classical (Hindustani raga)
# ---------------------------------------------------------------------------

RAGA_YAMAN = ScaleDefinition(
    name="raga_yaman",
    intervals_cents=(0, 200, 400, 600, 700, 900, 1100),
    cultural_context=(
        "Hindustani evening raga. Equivalent to Lydian mode. "
        "Traditionally performed after sunset. Ascent emphasizes "
        "the sharp fourth (tivra Ma). No chord progressions in pure form."
    ),
)

RAGA_BHAIRAV = ScaleDefinition(
    name="raga_bhairav",
    intervals_cents=(0, 100, 400, 500, 700, 800, 1100),
    cultural_context=(
        "Hindustani morning raga. Solemn and devotional character. "
        "Komal Re (flat 2nd) and komal Dha (flat 6th) are characteristic. "
        "Traditionally performed at dawn."
    ),
)

RAGA_DARBARI = ScaleDefinition(
    name="raga_darbari",
    intervals_cents=(0, 200, 280, 500, 700, 800, 980),
    cultural_context=(
        "Hindustani late-night raga. The komal Ga (slightly flattened 3rd, "
        "~280 cents) and komal Ni (~980 cents) are microtonal — they sit "
        "between standard 12-EDO pitches. Majestic and contemplative mood. "
        "Requires microtonal rendering for authenticity."
    ),
)

# ---------------------------------------------------------------------------
# Arab/Turkish maqam (quarter-tone system)
# ---------------------------------------------------------------------------

MAQAM_RAST = ScaleDefinition(
    name="maqam_rast",
    intervals_cents=(0, 200, 350, 500, 700, 900, 1050),
    cultural_context=(
        "Fundamental Arabic maqam. The 3rd degree (Sikah, ~350 cents) and "
        "7th degree (~1050 cents) are quarter-tones — halfway between "
        "Western semitones. Joyful, open character. Foundation of the "
        "Arabic maqam system."
    ),
)

MAQAM_BAYATI = ScaleDefinition(
    name="maqam_bayati",
    intervals_cents=(0, 150, 300, 500, 700, 800, 1000),
    cultural_context=(
        "Common Arabic maqam with a characteristic quarter-flat 2nd "
        "degree (~150 cents). Warm, earthy, melancholic character. "
        "One of the most frequently used maqamat in Arabic music."
    ),
)

# ---------------------------------------------------------------------------
# Gamelan (Javanese/Balinese)
# ---------------------------------------------------------------------------

PELOG = ScaleDefinition(
    name="pelog",
    intervals_cents=(0, 120, 270, 540, 675, 800, 1020),
    octave_cents=1200,
    cultural_context=(
        "Javanese/Balinese gamelan 7-tone scale. Intervals are "
        "non-equal and vary between ensembles. This is a representative "
        "tuning. Pelog has a distinctive sound with large and small "
        "intervals alternating. Used in sacred and ceremonial contexts."
    ),
)

SLENDRO = ScaleDefinition(
    name="slendro",
    intervals_cents=(0, 240, 480, 720, 960),
    octave_cents=1200,
    cultural_context=(
        "Javanese/Balinese gamelan 5-tone near-equidistant scale. "
        "Each interval is approximately 240 cents (vs 200 for 12-EDO "
        "whole tone). Intervals vary between ensembles. Bright, "
        "lively character. Used in dance and narrative performance."
    ),
)

# ---------------------------------------------------------------------------
# Just Intonation
# ---------------------------------------------------------------------------

JUST_INTONATION_MAJOR = ScaleDefinition(
    name="just_intonation_major",
    intervals_cents=(0, 204, 386, 498, 702, 884, 1088),
    cultural_context=(
        "Major scale tuned to pure harmonic ratios. "
        "3rd is 386 cents (pure major third 5/4) vs 400 in 12-EDO. "
        "5th is 702 cents (pure fifth 3/2) vs 700 in 12-EDO. "
        "Produces beatless consonances but limits modulation."
    ),
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_SCALE_DEFINITIONS: dict[str, ScaleDefinition] = {
    # 12-EDO Western
    "major": MAJOR,
    "minor": MINOR,
    "harmonic_minor": HARMONIC_MINOR,
    "dorian": DORIAN,
    "mixolydian": MIXOLYDIAN,
    "pentatonic_major": PENTATONIC_MAJOR,
    "pentatonic_minor": PENTATONIC_MINOR,
    "blues": BLUES,
    "chromatic": CHROMATIC,
    # Hindustani
    "raga_yaman": RAGA_YAMAN,
    "raga_bhairav": RAGA_BHAIRAV,
    "raga_darbari": RAGA_DARBARI,
    # Maqam
    "maqam_rast": MAQAM_RAST,
    "maqam_bayati": MAQAM_BAYATI,
    # Gamelan
    "pelog": PELOG,
    "slendro": SLENDRO,
    # Just Intonation
    "just_intonation_major": JUST_INTONATION_MAJOR,
}
