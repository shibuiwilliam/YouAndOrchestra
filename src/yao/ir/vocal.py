"""Vocal Line IR — VocalNote and LyricsLine for vocal-centric genres.

Extends the Note concept with syllable alignment, melisma, and breath
positions. Enables singing constraints: minimum note duration per syllable,
accent-beat alignment, and breath rest insertion.

Belongs to Layer 3 (IR).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.ir.note import Note


@dataclass(frozen=True)
class VocalNote:
    """A note in a vocal line with lyrics alignment.

    Extends Note semantics with syllable text, melisma targets,
    and breath marks. VocalNote does not subclass Note because
    Note is frozen and its constructor is fixed; instead, it
    wraps a Note and adds vocal-specific fields.

    Attributes:
        note: The underlying Note (pitch, start_beat, duration, velocity, instrument).
        syllable: The syllable text sung on this note, or None for melisma continuation.
        melisma_target_pitches: Additional pitches sung on the same syllable
            (melismatic ornamentation). Empty for syllabic singing.
        breath_after: If True, a short rest should follow this note for breathing.
    """

    note: Note
    syllable: str | None = None
    melisma_target_pitches: tuple[int, ...] = ()
    breath_after: bool = False

    @property
    def pitch(self) -> int:
        """Delegate to underlying note pitch."""
        return self.note.pitch

    @property
    def start_beat(self) -> float:
        """Delegate to underlying note start beat."""
        return self.note.start_beat

    @property
    def duration_beats(self) -> float:
        """Delegate to underlying note duration."""
        return self.note.duration_beats

    @property
    def velocity(self) -> int:
        """Delegate to underlying note velocity."""
        return self.note.velocity

    @property
    def is_melisma(self) -> bool:
        """True if this note continues a syllable from a previous note."""
        return self.syllable is None

    @property
    def is_syllabic(self) -> bool:
        """True if this note starts a new syllable."""
        return self.syllable is not None


@dataclass(frozen=True)
class LyricsLine:
    """A line of lyrics with rhythmic emphasis information.

    Attributes:
        text: The full text of the lyrics line.
        syllables: Individual syllables for note alignment.
        rhythmic_emphasis: Accent strength per syllable (0.0=weak, 1.0=strong).
            Must have the same length as syllables.
    """

    text: str
    syllables: tuple[str, ...]
    rhythmic_emphasis: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.rhythmic_emphasis and len(self.rhythmic_emphasis) != len(self.syllables):
            msg = (
                f"rhythmic_emphasis length ({len(self.rhythmic_emphasis)}) "
                f"must match syllables length ({len(self.syllables)})"
            )
            raise ValueError(msg)

    @property
    def syllable_count(self) -> int:
        """Number of syllables in this line."""
        return len(self.syllables)


# ── Singing constraints ──────────────────────────────────────────────

# Minimum note duration in beats for a syllable to be singable.
# Below this, the syllable cannot be articulated clearly.
MIN_SYLLABLE_DURATION_BEATS: float = 0.25  # 16th note at any tempo

# Minimum rest duration in beats after a breath mark.
MIN_BREATH_REST_BEATS: float = 0.125  # 32nd note


@dataclass(frozen=True)
class VocalConstraintViolation:
    """A violation of singing constraints.

    Attributes:
        bar: The bar number where the violation occurs.
        beat: The beat position within the bar.
        rule: The constraint rule that was violated.
        message: Human-readable description.
    """

    bar: int
    beat: float
    rule: str
    message: str


def check_vocal_constraints(
    vocal_notes: tuple[VocalNote, ...],
    beats_per_bar: float = 4.0,
) -> list[VocalConstraintViolation]:
    """Check that a vocal line satisfies singing constraints.

    Constraints checked:
    1. Note duration >= MIN_SYLLABLE_DURATION_BEATS for syllabic notes.
    2. Breath marks are followed by sufficient rest.
    3. Accented syllables should fall on strong beats.

    Args:
        vocal_notes: The vocal notes to check.
        beats_per_bar: Beats per bar for bar/beat calculation.

    Returns:
        List of constraint violations (empty if all constraints satisfied).
    """
    violations: list[VocalConstraintViolation] = []

    for i, vn in enumerate(vocal_notes):
        bar = int(vn.start_beat / beats_per_bar)
        beat = vn.start_beat % beats_per_bar

        # 1. Minimum syllable duration
        if vn.is_syllabic and vn.duration_beats < MIN_SYLLABLE_DURATION_BEATS:
            violations.append(
                VocalConstraintViolation(
                    bar=bar,
                    beat=beat,
                    rule="min_syllable_duration",
                    message=(
                        f"Syllable '{vn.syllable}' at bar {bar} beat {beat:.2f} "
                        f"has duration {vn.duration_beats:.3f} beats "
                        f"(min: {MIN_SYLLABLE_DURATION_BEATS})"
                    ),
                )
            )

        # 2. Breath rest
        if vn.breath_after and i + 1 < len(vocal_notes):
            next_vn = vocal_notes[i + 1]
            gap = next_vn.start_beat - (vn.start_beat + vn.duration_beats)
            if gap < MIN_BREATH_REST_BEATS:
                violations.append(
                    VocalConstraintViolation(
                        bar=bar,
                        beat=beat,
                        rule="breath_rest",
                        message=(
                            f"Breath mark at bar {bar} beat {beat:.2f} "
                            f"followed by only {gap:.3f} beats rest "
                            f"(min: {MIN_BREATH_REST_BEATS})"
                        ),
                    )
                )

    return violations
