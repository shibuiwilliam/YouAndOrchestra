"""Rhythm Markov Generator — n-gram onset pattern generation.

Generates rhythmic onset patterns via Markov chains over beat-grid
positions, replacing static rhythm pools with genre-conditioned
probabilistic patterns.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §3.1, PROJECT.md §3.4.5, CLAUDE.md Phase 4.0.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import yaml

from yao.types import Beat

_RHYTHM_MODELS_DIR = Path(__file__).resolve().parent.parent / "generators" / "markov_models" / "rhythm"
_RHYTHM_MODEL_CACHE: dict[str, RhythmMarkovModel] = {}


@dataclass(frozen=True)
class RhythmMarkovModel:
    """A loaded rhythm transition table.

    Attributes:
        name: Model identifier.
        description: Human-readable description.
        source: Provenance of the model.
        license: License string.
        n_gram_order: Order of the n-gram.
        resolution: Grid resolution (e.g., "beat", "16th").
        transitions: Mapping from beat position to next-position probabilities.
    """

    name: str
    description: str
    source: str
    license: str
    n_gram_order: int
    resolution: str
    transitions: dict[int, dict[int, float]]

    @property
    def num_positions(self) -> int:
        """Number of positions in the model."""
        return len(self.transitions)


def load_rhythm_model(model_name: str) -> RhythmMarkovModel:
    """Load a rhythm Markov model from YAML.

    Args:
        model_name: Model filename without .yaml extension.

    Returns:
        Parsed RhythmMarkovModel.

    Raises:
        FileNotFoundError: If model file doesn't exist.
    """
    if model_name in _RHYTHM_MODEL_CACHE:
        return _RHYTHM_MODEL_CACHE[model_name]

    path = _RHYTHM_MODELS_DIR / f"{model_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Rhythm Markov model not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    meta = data.get("metadata", {})
    transitions_raw = data.get("transitions", {})
    transitions: dict[int, dict[int, float]] = {}
    for key, val in transitions_raw.items():
        transitions[int(key)] = {int(k): float(v) for k, v in val.items()}

    model = RhythmMarkovModel(
        name=meta.get("name", model_name),
        description=meta.get("description", ""),
        source=meta.get("source", ""),
        license=meta.get("license", ""),
        n_gram_order=meta.get("n_gram_order", 2),
        resolution=meta.get("resolution", "beat"),
        transitions=transitions,
    )
    _RHYTHM_MODEL_CACHE[model_name] = model
    return model


def generate_rhythm_pattern(
    model: RhythmMarkovModel,
    bars: int,
    beats_per_bar: int = 4,
    rng: random.Random | None = None,
) -> list[Beat]:
    """Generate onset positions using a rhythm Markov model.

    Args:
        model: The rhythm Markov model.
        bars: Number of bars to generate.
        beats_per_bar: Beats per bar (default 4 for 4/4).
        rng: Random number generator.

    Returns:
        List of beat positions (absolute, from beat 0.0) where onsets occur.
    """
    if rng is None:
        rng = random.Random()

    positions = model.num_positions
    onsets: list[Beat] = []

    for bar in range(bars):
        for beat_in_bar in range(beats_per_bar):
            model_pos = beat_in_bar % positions
            trans = model.transitions.get(model_pos, {})

            if not trans:
                continue

            # Onset probability from the model's self-transition weight
            onset_prob = trans.get(model_pos, 0.5)
            abs_beat = float(bar * beats_per_bar + beat_in_bar)
            if rng.random() < onset_prob:
                onsets.append(abs_beat)

    return onsets


def list_available_rhythm_models() -> list[str]:
    """List available rhythm Markov model names.

    Returns:
        Sorted list of model names (without .yaml extension).
    """
    if not _RHYTHM_MODELS_DIR.exists():
        return []
    return sorted(p.stem for p in _RHYTHM_MODELS_DIR.glob("*.yaml"))


def clear_rhythm_cache() -> None:
    """Clear the rhythm model cache."""
    _RHYTHM_MODEL_CACHE.clear()
