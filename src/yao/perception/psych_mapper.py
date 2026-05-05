"""PSL-Psychology: empirical emotion-to-feature mapping.

Maps emotion keywords (from intent.md and v2 emotion spec fields)
to concrete musical feature targets. Drawn from empirical music
psychology research:

- Juslin & Sloboda (2010): "Handbook of Music and Emotion"
- Krumhansl (1990): "Cognitive Foundations of Musical Pitch"
- Huron (2006): "Sweet Anticipation: Music and the Psychology of Expectation"
- Gabrielsson & Lindström (2001): "The Influence of Musical Structure on
  Emotional Expression"

This module enables the Conductor's spec compiler to set generator parameters
from emotion fields, making v2 emotion specifications functional (Bottleneck D).

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yao.ir.score_ir import ScoreIR


class Articulation(StrEnum):
    """Articulation style affecting note duration and attack."""

    LEGATO = "legato"
    STACCATO = "staccato"
    MARCATO = "marcato"
    TENUTO = "tenuto"
    NORMAL = "normal"


class Dynamics(StrEnum):
    """Dynamic level identifiers."""

    PPP = "ppp"
    PP = "pp"
    P = "p"
    MP = "mp"
    MF = "mf"
    F = "f"
    FF = "ff"
    FFF = "fff"


@dataclass(frozen=True)
class FeatureProfile:
    """Empirically-derived musical feature targets for an emotion.

    Each field represents a measurable musical parameter that correlates
    with the perceived emotion, based on music psychology literature.

    Attributes:
        tempo_bpm_range: Expected tempo range (min, max) BPM.
            Source: Gabrielsson & Lindström (2001) — tempo–arousal correlation.
        major_minor_bias: 0.0 = pure minor, 1.0 = pure major.
            Source: Juslin (2001) — mode strongly predicts valence.
        consonance_target: Target consonance ratio (0.0–1.0).
            Source: Krumhansl (1990) — tonal hierarchy and stability.
        spectral_centroid_target: Brightness target (0.0=dark, 1.0=bright).
            Source: Juslin & Laukka (2004) — timbre cues in emotional expression.
        articulation: Dominant articulation style.
            Source: Gabrielsson & Lindström (2001) — articulation–emotion mapping.
        typical_dynamics: (low, high) dynamic range for this emotion.
            Source: Juslin (2001) — dynamics variation as emotion cue.
        density_target: Note density (0.0=sparse, 1.0=dense).
            Source: Huron (2006) — event density and arousal.
        register_height: Target register (0.0=low, 1.0=high).
            Source: Huron (2006) — pitch height and arousal/valence.
    """

    tempo_bpm_range: tuple[int, int]
    major_minor_bias: float
    consonance_target: float
    spectral_centroid_target: float
    articulation: Articulation
    typical_dynamics: tuple[Dynamics, Dynamics]
    density_target: float = 0.5
    register_height: float = 0.5


# ── Emotion → Feature mapping ─────────────────────────────────────────
# Each entry is backed by empirical findings from the cited sources.
# Emotions are organized by valence × arousal quadrant:
#   High valence, high arousal: triumphant, joyful, playful, energetic
#   High valence, low arousal:  tender, serene, peaceful, nostalgic
#   Low valence, high arousal:  aggressive, anxious, intense, dramatic
#   Low valence, low arousal:   melancholic, somber, mysterious, lonely

EMOTION_TO_FEATURES: dict[str, FeatureProfile] = {
    # ── High valence, high arousal ──
    "triumphant": FeatureProfile(
        tempo_bpm_range=(110, 140),
        major_minor_bias=0.95,
        consonance_target=0.70,
        spectral_centroid_target=0.65,
        articulation=Articulation.MARCATO,
        typical_dynamics=(Dynamics.MF, Dynamics.FFF),
        density_target=0.7,
        register_height=0.7,
    ),
    "joyful": FeatureProfile(
        tempo_bpm_range=(100, 135),
        major_minor_bias=0.90,
        consonance_target=0.80,
        spectral_centroid_target=0.60,
        articulation=Articulation.STACCATO,
        typical_dynamics=(Dynamics.MF, Dynamics.FF),
        density_target=0.65,
        register_height=0.6,
    ),
    "playful": FeatureProfile(
        tempo_bpm_range=(100, 130),
        major_minor_bias=0.85,
        consonance_target=0.75,
        spectral_centroid_target=0.55,
        articulation=Articulation.STACCATO,
        typical_dynamics=(Dynamics.MP, Dynamics.F),
        density_target=0.6,
        register_height=0.6,
    ),
    "energetic": FeatureProfile(
        tempo_bpm_range=(120, 160),
        major_minor_bias=0.70,
        consonance_target=0.65,
        spectral_centroid_target=0.70,
        articulation=Articulation.MARCATO,
        typical_dynamics=(Dynamics.F, Dynamics.FFF),
        density_target=0.8,
        register_height=0.6,
    ),
    # ── High valence, low arousal ──
    "tender": FeatureProfile(
        tempo_bpm_range=(60, 90),
        major_minor_bias=0.30,
        consonance_target=0.85,
        spectral_centroid_target=0.30,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PP, Dynamics.MP),
        density_target=0.3,
        register_height=0.5,
    ),
    "serene": FeatureProfile(
        tempo_bpm_range=(55, 80),
        major_minor_bias=0.60,
        consonance_target=0.90,
        spectral_centroid_target=0.25,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PP, Dynamics.P),
        density_target=0.2,
        register_height=0.5,
    ),
    "peaceful": FeatureProfile(
        tempo_bpm_range=(50, 75),
        major_minor_bias=0.65,
        consonance_target=0.90,
        spectral_centroid_target=0.25,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PPP, Dynamics.P),
        density_target=0.2,
        register_height=0.4,
    ),
    "nostalgic": FeatureProfile(
        tempo_bpm_range=(60, 90),
        major_minor_bias=0.40,
        consonance_target=0.80,
        spectral_centroid_target=0.35,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PP, Dynamics.MP),
        density_target=0.35,
        register_height=0.5,
    ),
    # ── Low valence, high arousal ──
    "aggressive": FeatureProfile(
        tempo_bpm_range=(130, 180),
        major_minor_bias=0.10,
        consonance_target=0.40,
        spectral_centroid_target=0.80,
        articulation=Articulation.MARCATO,
        typical_dynamics=(Dynamics.FF, Dynamics.FFF),
        density_target=0.85,
        register_height=0.4,
    ),
    "anxious": FeatureProfile(
        tempo_bpm_range=(100, 140),
        major_minor_bias=0.15,
        consonance_target=0.50,
        spectral_centroid_target=0.60,
        articulation=Articulation.STACCATO,
        typical_dynamics=(Dynamics.MP, Dynamics.FF),
        density_target=0.7,
        register_height=0.6,
    ),
    "intense": FeatureProfile(
        tempo_bpm_range=(110, 150),
        major_minor_bias=0.20,
        consonance_target=0.50,
        spectral_centroid_target=0.65,
        articulation=Articulation.MARCATO,
        typical_dynamics=(Dynamics.F, Dynamics.FFF),
        density_target=0.75,
        register_height=0.5,
    ),
    "dramatic": FeatureProfile(
        tempo_bpm_range=(70, 130),
        major_minor_bias=0.25,
        consonance_target=0.55,
        spectral_centroid_target=0.55,
        articulation=Articulation.TENUTO,
        typical_dynamics=(Dynamics.PP, Dynamics.FFF),
        density_target=0.6,
        register_height=0.5,
    ),
    # ── Low valence, low arousal ──
    "melancholic": FeatureProfile(
        tempo_bpm_range=(55, 85),
        major_minor_bias=0.15,
        consonance_target=0.80,
        spectral_centroid_target=0.35,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PP, Dynamics.MP),
        density_target=0.3,
        register_height=0.4,
    ),
    "somber": FeatureProfile(
        tempo_bpm_range=(50, 75),
        major_minor_bias=0.10,
        consonance_target=0.75,
        spectral_centroid_target=0.30,
        articulation=Articulation.TENUTO,
        typical_dynamics=(Dynamics.PP, Dynamics.P),
        density_target=0.25,
        register_height=0.3,
    ),
    "mysterious": FeatureProfile(
        tempo_bpm_range=(60, 100),
        major_minor_bias=0.25,
        consonance_target=0.55,
        spectral_centroid_target=0.35,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PP, Dynamics.MF),
        density_target=0.35,
        register_height=0.5,
    ),
    "lonely": FeatureProfile(
        tempo_bpm_range=(50, 80),
        major_minor_bias=0.20,
        consonance_target=0.75,
        spectral_centroid_target=0.30,
        articulation=Articulation.LEGATO,
        typical_dynamics=(Dynamics.PPP, Dynamics.MP),
        density_target=0.2,
        register_height=0.4,
    ),
}


def get_feature_profile(emotion: str) -> FeatureProfile | None:
    """Look up a feature profile for an emotion keyword.

    Performs case-insensitive matching with common synonyms.

    Args:
        emotion: Emotion keyword (e.g., "melancholic", "happy").

    Returns:
        FeatureProfile if found, None otherwise.
    """
    key = emotion.lower().strip()

    # Direct match
    if key in EMOTION_TO_FEATURES:
        return EMOTION_TO_FEATURES[key]

    # Common synonyms
    synonyms: dict[str, str] = {
        "happy": "joyful",
        "sad": "melancholic",
        "calm": "serene",
        "exciting": "energetic",
        "dark": "somber",
        "bright": "joyful",
        "angry": "aggressive",
        "relaxed": "peaceful",
        "epic": "triumphant",
        "contemplative": "nostalgic",
        "bittersweet": "nostalgic",
        "uplifting": "triumphant",
        "tense": "anxious",
        "suspenseful": "anxious",
        "ethereal": "serene",
        "warm": "tender",
        "cool": "mysterious",
        "haunting": "mysterious",
        "driving": "energetic",
        "gentle": "tender",
        "dreamy": "serene",
        "powerful": "intense",
        "fierce": "aggressive",
        "wistful": "nostalgic",
        "hopeful": "joyful",
        "melancholy": "melancholic",
    }

    if key in synonyms:
        return EMOTION_TO_FEATURES[synonyms[key]]

    return None


def all_emotions() -> list[str]:
    """Return all supported emotion keywords.

    Returns:
        Sorted list of primary emotion keywords.
    """
    return sorted(EMOTION_TO_FEATURES.keys())


def emotion_to_generator_params(emotion: str) -> dict[str, float | str | tuple[int, int]] | None:
    """Convert an emotion to generator-consumable parameters.

    This is the primary interface for the Conductor's spec compiler.
    It returns a dict that can be applied to CompositionSpec fields.

    Args:
        emotion: Emotion keyword.

    Returns:
        Dict with generator parameters, or None if emotion not recognized.
        Keys: tempo_bpm_range, dynamics_low, dynamics_high, temperature_bias,
              articulation, register_height, density_target.
    """
    profile = get_feature_profile(emotion)
    if profile is None:
        return None

    # Temperature bias: higher arousal → higher temperature (more variation)
    # Derived from density_target as proxy for arousal
    temp_bias = profile.density_target * 0.4

    return {
        "tempo_bpm_range": profile.tempo_bpm_range,
        "dynamics_low": profile.typical_dynamics[0].value,
        "dynamics_high": profile.typical_dynamics[1].value,
        "temperature_bias": temp_bias,
        "articulation": profile.articulation.value,
        "register_height": profile.register_height,
        "density_target": profile.density_target,
        "consonance_target": profile.consonance_target,
        "spectral_centroid_target": profile.spectral_centroid_target,
        "major_minor_bias": profile.major_minor_bias,
    }


# ── Score → Perception estimators (C3 reverse direction) ─────────────


def estimate_arousal(score: ScoreIR) -> float:
    """Estimate arousal (calm 0.0 → excited 1.0) from a generated score.

    Based on tempo, note density, dynamics, and register.

    References:
        Russell (1980): Circumplex model of affect.
        Schubert (1999): Measurement of continuous emotion in music.
        Gabrielsson & Lindström (2001): tempo–arousal correlation.

    Goodhart defense: can be gamed by spamming fast high-velocity notes.
    Cross-check with motif coherence and structural quality metrics.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Estimated arousal in [0.0, 1.0].
    """
    notes = score.all_notes()
    if not notes:
        return 0.0

    # Note density: notes per beat
    max_beat = max(n.start_beat + n.duration_beats for n in notes)
    density = len(notes) / max(max_beat, 1.0)
    density_score = min(density / 8.0, 1.0)  # 8 notes/beat = max

    # Velocity (dynamics proxy)
    avg_vel = sum(n.velocity for n in notes) / len(notes)
    vel_score = avg_vel / 127.0

    # Register height
    avg_pitch = sum(n.pitch for n in notes) / len(notes)
    register_score = max(0.0, min((avg_pitch - 36) / (96 - 36), 1.0))

    # Weighted combination
    return min(1.0, 0.4 * density_score + 0.35 * vel_score + 0.25 * register_score)


def estimate_valence(score: ScoreIR) -> float:
    """Estimate valence (negative 0.0 → positive 1.0) from a generated score.

    Based on mode (major/minor bias), consonance, and register.

    References:
        Juslin & Laukka (2003): Communication of emotions in vocal and
        musical expression.
        Krumhansl (1990): Cognitive Foundations of Musical Pitch.

    Goodhart defense: can be gamed by using only major triads. Cross-check
    with harmonic complexity and melodic contour variety.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Estimated valence in [0.0, 1.0].
    """
    notes = score.all_notes()
    if not notes:
        return 0.5

    # Major/minor bias from interval class distribution
    # Major 3rd (4 semitones) vs minor 3rd (3 semitones) prevalence
    sorted_notes = sorted(notes, key=lambda n: n.start_beat)
    major_thirds = 0
    minor_thirds = 0
    for i in range(1, len(sorted_notes)):
        interval = abs(sorted_notes[i].pitch - sorted_notes[i - 1].pitch) % 12
        if interval == 4:
            major_thirds += 1
        elif interval == 3:
            minor_thirds += 1
    total_thirds = major_thirds + minor_thirds
    mode_score = major_thirds / total_thirds if total_thirds > 0 else 0.5

    # Consonance: ratio of consonant intervals (unison, 3rd, 4th, 5th, 6th, octave)
    consonant_classes = {0, 3, 4, 5, 7, 8, 9}  # interval classes
    consonant_count = 0
    total_intervals = 0
    for i in range(1, len(sorted_notes)):
        interval = abs(sorted_notes[i].pitch - sorted_notes[i - 1].pitch) % 12
        if interval in consonant_classes:
            consonant_count += 1
        total_intervals += 1
    consonance = consonant_count / total_intervals if total_intervals > 0 else 0.5

    # Register contributes slightly (higher = slightly more positive)
    avg_pitch = sum(n.pitch for n in notes) / len(notes)
    register_score = max(0.0, min((avg_pitch - 48) / (84 - 48), 1.0))

    return min(1.0, 0.45 * mode_score + 0.35 * consonance + 0.20 * register_score)


def estimate_tension(score: ScoreIR, bar: int, beats_per_bar: float = 4.0) -> float:
    """Estimate tension at a specific bar from a generated score.

    Based on dissonance, register extremes, note density, and dynamics
    at the given bar position.

    References:
        Lerdahl & Jackendoff (1983): A Generative Theory of Tonal Music.
        Lerdahl (2001): Tonal Pitch Space — distance-based tension model.

    Goodhart defense: can be gamed by inserting dissonant clusters.
    Cross-check with structural coherence and harmonic function analysis.

    Args:
        score: The ScoreIR to analyze.
        bar: The bar number (0-indexed) to estimate tension for.
        beats_per_bar: Beats per bar (default 4.0 for 4/4 time).

    Returns:
        Estimated tension in [0.0, 1.0].
    """
    bar_start = bar * beats_per_bar
    bar_end = bar_start + beats_per_bar

    bar_notes = [n for n in score.all_notes() if bar_start <= n.start_beat < bar_end]
    if not bar_notes:
        return 0.0

    # Dissonance: proportion of dissonant intervals
    dissonant_classes = {1, 2, 6, 10, 11}  # semitone, whole tone, tritone
    pitches = sorted(set(n.pitch for n in bar_notes))
    dissonant_count = 0
    total_pairs = 0
    for i in range(len(pitches)):
        for j in range(i + 1, len(pitches)):
            interval = (pitches[j] - pitches[i]) % 12
            if interval in dissonant_classes:
                dissonant_count += 1
            total_pairs += 1
    dissonance = dissonant_count / total_pairs if total_pairs > 0 else 0.0

    # Density
    density = min(len(bar_notes) / 16.0, 1.0)

    # Dynamics
    avg_vel = sum(n.velocity for n in bar_notes) / len(bar_notes)
    dynamics = avg_vel / 127.0

    # Register extremes (spread)
    pitch_range = max(n.pitch for n in bar_notes) - min(n.pitch for n in bar_notes)
    register_spread = min(pitch_range / 48.0, 1.0)

    return min(1.0, 0.35 * dissonance + 0.25 * dynamics + 0.20 * density + 0.20 * register_spread)
