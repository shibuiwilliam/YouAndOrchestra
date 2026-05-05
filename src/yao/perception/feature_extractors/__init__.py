"""Feature Extractor Registry — discovers and manages symbolic feature extractors.

Provides a protocol-based registry for feature extractors that operate on ScoreIR.
All extractors produce numpy arrays and are registered via the ``register_extractor``
decorator.

Belongs to Layer 4 (Perception).
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from yao.ir.score_ir import ScoreIR


class FeatureExtractor(Protocol):
    """Protocol for symbolic feature extractors.

    Each extractor takes a ScoreIR and returns a fixed-size numpy array.
    """

    name: str
    feature_dim: int

    def extract(self, score: ScoreIR) -> np.ndarray:
        """Extract feature vector from a ScoreIR.

        Args:
            score: The symbolic score to analyze.

        Returns:
            Numpy array of shape (feature_dim,).
        """
        ...


# Global registry of extractors
_REGISTRY: dict[str, FeatureExtractor] = {}


def register_extractor(extractor: FeatureExtractor) -> FeatureExtractor:
    """Register a feature extractor in the global registry.

    Args:
        extractor: An instance implementing FeatureExtractor protocol.

    Returns:
        The same extractor (allows use as post-instantiation registration).
    """
    _REGISTRY[extractor.name] = extractor
    return extractor


def get_extractor(name: str) -> FeatureExtractor:
    """Retrieve a registered extractor by name.

    Args:
        name: The extractor's registered name.

    Returns:
        The extractor instance.

    Raises:
        KeyError: If no extractor with that name is registered.
    """
    if name not in _REGISTRY:
        msg = f"No feature extractor registered with name '{name}'. Available: {sorted(_REGISTRY.keys())}"
        raise KeyError(msg)
    return _REGISTRY[name]


def list_extractors() -> list[str]:
    """Return sorted list of registered extractor names.

    Returns:
        List of extractor names.
    """
    return sorted(_REGISTRY.keys())


def extract_all(score: ScoreIR) -> dict[str, np.ndarray]:
    """Run all registered extractors on a score.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Dict mapping extractor name to its feature vector.
    """
    return {name: ext.extract(score) for name, ext in sorted(_REGISTRY.items())}


def extract_concatenated(score: ScoreIR) -> np.ndarray:
    """Run all extractors and concatenate into a single feature vector.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Single concatenated numpy array of all features.
    """
    vectors = [ext.extract(score) for _, ext in sorted(_REGISTRY.items())]
    if not vectors:
        return np.array([], dtype=np.float64)
    return np.concatenate(vectors)


# Auto-register symbolic extractors on import
from yao.perception.feature_extractors import symbolic as _symbolic  # noqa: E402, F401
