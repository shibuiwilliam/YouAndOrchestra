"""Motif generation — create seed motifs from intent, trajectory, and genre.

Generates MotifSeed objects by combining:
- Markov bigram model for interval sequences (reuses diatonic_bigram.yaml)
- Intent keywords for character derivation
- Trajectory tension peaks for climax-ready motifs
- Rhythm shape templates scaled by tempo

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml

from yao.ir.plan.motif import MotifSeed
from yao.ir.plan.song_form import SongFormPlan
from yao.schema.intent import IntentSpec

_MARKOV_DIR = Path(__file__).resolve().parent.parent / "generators" / "markov_models"


# ── Rhythm templates ────────────────────────────────────────────────────
# Beats per note. Templates are normalized to 4-beat bars; scale by time_sig.

_RHYTHM_TEMPLATES: dict[str, tuple[float, ...]] = {
    "even_quarter": (1.0, 1.0, 1.0, 1.0),
    "dotted_drive": (1.5, 0.5, 1.0, 1.0),
    "syncopated": (0.5, 1.0, 0.5, 1.0, 1.0),
    "lyrical_long": (2.0, 1.0, 1.0),
    "hook_short": (0.5, 0.5, 0.5, 0.5, 1.0, 1.0),
    "triplet_feel": (2 / 3, 2 / 3, 2 / 3, 1.0, 1.0),
    "slow_ballad": (2.0, 2.0),
    "punchy": (0.5, 0.5, 1.0, 0.5, 0.5, 1.0),
}

# ── Intent → motif character heuristics ─────────────────────────────────

_KEYWORD_CHARACTER: dict[str, dict[str, Any]] = {
    # keyword → preferred direction, rhythm style, description fragment
    "uplifting": {"direction": "ascending", "rhythm": "even_quarter", "desc": "ascending major"},
    "bright": {"direction": "ascending", "rhythm": "dotted_drive", "desc": "bright rising"},
    "triumphant": {"direction": "ascending", "rhythm": "punchy", "desc": "heroic fanfare"},
    "heroic": {"direction": "ascending", "rhythm": "punchy", "desc": "heroic fanfare"},
    "energetic": {"direction": "ascending", "rhythm": "syncopated", "desc": "driving syncopated"},
    "calm": {"direction": "stepwise", "rhythm": "lyrical_long", "desc": "gentle stepwise"},
    "peaceful": {"direction": "stepwise", "rhythm": "slow_ballad", "desc": "serene sustained"},
    "gentle": {"direction": "stepwise", "rhythm": "lyrical_long", "desc": "soft lyrical"},
    "sad": {"direction": "descending", "rhythm": "lyrical_long", "desc": "descending minor"},
    "melancholic": {"direction": "descending", "rhythm": "slow_ballad", "desc": "melancholic sighing"},
    "dark": {"direction": "descending", "rhythm": "syncopated", "desc": "dark chromatic"},
    "mysterious": {"direction": "mixed", "rhythm": "triplet_feel", "desc": "enigmatic angular"},
    "dramatic": {"direction": "wide", "rhythm": "dotted_drive", "desc": "dramatic leaping"},
    "epic": {"direction": "wide", "rhythm": "punchy", "desc": "epic sweeping"},
    "romantic": {"direction": "stepwise", "rhythm": "lyrical_long", "desc": "romantic lyrical"},
    "dreamy": {"direction": "stepwise", "rhythm": "slow_ballad", "desc": "dreamy floating"},
    "tense": {"direction": "chromatic", "rhythm": "syncopated", "desc": "tense chromatic"},
    "nostalgic": {"direction": "descending", "rhythm": "lyrical_long", "desc": "wistful descending"},
}

_DEFAULT_CHARACTER = {"direction": "mixed", "rhythm": "even_quarter", "desc": "neutral melodic"}


def _load_bigram_model(model_name: str = "diatonic_bigram") -> dict[int, dict[int, float]]:
    """Load a Markov bigram transition model from YAML.

    Args:
        model_name: Name of the model file (without .yaml).

    Returns:
        Dict mapping current_degree → {next_degree: probability}.
    """
    path = _MARKOV_DIR / f"{model_name}.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    transitions: dict[int, dict[int, float]] = {}
    for degree_str, next_probs in data["transitions"].items():
        degree = int(degree_str)
        transitions[degree] = {int(k): float(v) for k, v in next_probs.items()}
    return transitions


def _derive_character(intent: IntentSpec) -> dict[str, Any]:
    """Derive motif character from intent keywords.

    Args:
        intent: The piece's intent specification.

    Returns:
        Character dict with direction, rhythm template name, and description.
    """
    for keyword in intent.keywords:
        kw_lower = keyword.lower()
        if kw_lower in _KEYWORD_CHARACTER:
            return _KEYWORD_CHARACTER[kw_lower]
    # Fall back to text scanning
    text_lower = intent.text.lower()
    for kw, char in _KEYWORD_CHARACTER.items():
        if kw in text_lower:
            return char
    return _DEFAULT_CHARACTER


def _generate_interval_sequence(
    length: int,
    direction: str,
    bigram: dict[int, dict[int, float]],
    rng: random.Random,
) -> tuple[int, ...]:
    """Generate an interval sequence using the Markov bigram model.

    Args:
        length: Number of intervals to generate.
        direction: Preferred direction ("ascending", "descending", "stepwise",
                   "wide", "chromatic", "mixed").
        bigram: Transition probability table (degree → {degree: prob}).
        rng: Seeded random generator.

    Returns:
        Tuple of semitone intervals from the first note.
    """
    # Start on tonic (degree 0)
    current_degree = 0
    degrees = [0]

    for _ in range(length - 1):
        probs = bigram.get(current_degree, bigram[0]).copy()

        # Apply directional bias
        if direction == "ascending":
            for d in probs:
                if d > current_degree or (d == 0 and current_degree >= 5):  # noqa: PLR2004
                    probs[d] *= 1.5
        elif direction == "descending":
            for d in probs:
                if d < current_degree or (d >= 5 and current_degree <= 1):  # noqa: PLR2004
                    probs[d] *= 1.5
        elif direction == "stepwise":
            for d in probs:
                if abs(d - current_degree) <= 1 or abs(d - current_degree) == 6:  # noqa: PLR2004
                    probs[d] *= 2.0
        elif direction == "wide":
            for d in probs:
                if abs(d - current_degree) >= 3:  # noqa: PLR2004
                    probs[d] *= 1.8

        # Normalize
        total = sum(probs.values())
        if total == 0:
            current_degree = rng.randint(0, 6)  # noqa: S311
        else:
            normalized = {d: p / total for d, p in probs.items()}
            choices = list(normalized.keys())
            weights = [normalized[c] for c in choices]
            current_degree = rng.choices(choices, weights=weights, k=1)[0]

        degrees.append(current_degree)

    # Convert scale degrees to semitone intervals from first note
    # Major scale intervals: [0, 2, 4, 5, 7, 9, 11]
    major_semitones = [0, 2, 4, 5, 7, 9, 11]
    base_semitone = major_semitones[degrees[0]]
    intervals = tuple(major_semitones[d] - base_semitone for d in degrees)

    return intervals


def _compute_identity_strength(
    rhythm_shape: tuple[float, ...],
    interval_shape: tuple[int, ...],
) -> float:
    """Compute how distinctive a motif is (0.0–1.0).

    Identity strength is based on:
    - Rhythm specificity: how varied the durations are (vs uniform)
    - Interval specificity: how varied the intervals are (vs stepwise)

    Args:
        rhythm_shape: Duration pattern in beats.
        interval_shape: Interval pattern in semitones.

    Returns:
        Identity strength score [0.0, 1.0].
    """
    # Rhythm specificity: coefficient of variation of durations
    if len(rhythm_shape) <= 1:
        rhythm_spec = 0.0
    else:
        mean_dur = sum(rhythm_shape) / len(rhythm_shape)
        if mean_dur == 0:
            rhythm_spec = 0.0
        else:
            variance = sum((d - mean_dur) ** 2 for d in rhythm_shape) / len(rhythm_shape)
            rhythm_spec = min((variance**0.5) / mean_dur, 1.0)

    # Interval specificity: range and variety of intervals
    if len(interval_shape) <= 1:
        interval_spec = 0.0
    else:
        unique_intervals = len(set(interval_shape))
        interval_range = max(interval_shape) - min(interval_shape) if interval_shape else 0
        interval_spec = min(
            (unique_intervals / len(interval_shape)) * 0.5 + min(interval_range / 12.0, 1.0) * 0.5,
            1.0,
        )

    return round(rhythm_spec * 0.4 + interval_spec * 0.6, 3)


def generate_motif_seeds(
    intent: IntentSpec,
    form: SongFormPlan,
    *,
    seed: int = 42,
    count: int | None = None,
    bigram_model: str = "diatonic_bigram",
) -> list[MotifSeed]:
    """Generate seed motifs from intent, form structure, and Markov model.

    Guarantees at least 1 motif seed. Typically produces 1-3 depending
    on form complexity.

    Args:
        intent: The piece's intent specification.
        form: Song form plan (sections with tension/density targets).
        seed: Random seed for reproducibility.
        count: Override number of motifs (default: auto from form complexity).
        bigram_model: Name of the Markov bigram model to use.

    Returns:
        List of MotifSeed objects (len >= 1).
    """
    rng = random.Random(seed)
    bigram = _load_bigram_model(bigram_model)
    character = _derive_character(intent)

    # Determine motif count from form complexity
    if count is None:
        n_sections = len(form.sections)
        if n_sections <= 2:  # noqa: PLR2004
            count = 1
        elif n_sections <= 4:  # noqa: PLR2004
            count = 2
        else:
            count = min(3, max(1, n_sections // 2))

    # Select rhythm template
    rhythm_key = character["rhythm"]
    base_rhythm = _RHYTHM_TEMPLATES.get(rhythm_key, _RHYTHM_TEMPLATES["even_quarter"])

    seeds: list[MotifSeed] = []

    for i in range(count):
        motif_id = f"M{i + 1}"

        # Vary rhythm slightly for secondary motifs
        if i == 0:
            rhythm_shape = base_rhythm
        else:
            # Pick a contrasting rhythm for variety
            alt_keys = [k for k in _RHYTHM_TEMPLATES if k != rhythm_key]
            alt_key = rng.choice(alt_keys)
            rhythm_shape = _RHYTHM_TEMPLATES[alt_key]

        # Generate interval sequence
        n_notes = len(rhythm_shape)
        direction = character["direction"]
        if i > 0 and direction in ("ascending", "descending"):
            # Contrast: secondary motifs go opposite
            direction = "descending" if direction == "ascending" else "ascending"

        interval_shape = _generate_interval_sequence(n_notes, direction, bigram, rng)

        # Determine origin section
        if i == 0:
            # Primary motif: first melodic section (verse or chorus)
            melodic_sections = [s for s in form.sections if s.role in ("verse", "chorus")]
            origin = melodic_sections[0].id if melodic_sections else form.sections[0].id
        else:
            # Secondary motifs: bridge/chorus for contrast
            contrast_sections = [s for s in form.sections if s.role in ("chorus", "bridge", "solo")]
            if contrast_sections:
                origin = contrast_sections[min(i - 1, len(contrast_sections) - 1)].id
            else:
                origin = form.sections[min(i, len(form.sections) - 1)].id

        # Build character description
        desc_base = character["desc"]
        identity = _compute_identity_strength(rhythm_shape, interval_shape)
        desc = f"{desc_base} (identity={identity:.2f})"

        seeds.append(
            MotifSeed(
                id=motif_id,
                rhythm_shape=rhythm_shape,
                interval_shape=interval_shape,
                origin_section=origin,
                character=desc,
            )
        )

    return seeds
