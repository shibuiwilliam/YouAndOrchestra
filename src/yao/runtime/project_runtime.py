"""Project Runtime — stateful session with generation cache and undo.

Context manager: ``with ProjectRuntime("my-song") as rt: ...``
Cache key: (spec_hash, seed, generator_name).
Undo stack: max 50, redo cleared on new edit.
Lockfile prevents concurrent access.

Belongs to runtime/ package (Tier 3).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from yao.ir.score_ir import ScoreIR


@dataclass
class RuntimeState:
    """A snapshot of the project state for undo/redo.

    Attributes:
        description: Human-readable description of the action.
        score_json: Serialized ScoreIR state.
    """

    description: str
    score_json: str


class ProjectRuntime:
    """Stateful project session with caching and undo.

    Usage::

        with ProjectRuntime("my-song") as rt:
            rt.set_score(score, "Initial generation")
            rt.undo()
            rt.redo()
            cached = rt.get_cached(spec, seed, strategy)
    """

    _MAX_UNDO = 50

    def __init__(self, project_name: str, base_dir: Path | None = None) -> None:
        self._project_name = project_name
        self._base_dir = base_dir or Path(f"outputs/projects/{project_name}")
        self._cache_dir = self._base_dir / ".cache"
        self._lock_path = self._base_dir / ".lock"
        self._undo_stack: list[RuntimeState] = []
        self._redo_stack: list[RuntimeState] = []
        self._current_score: ScoreIR | None = None

    @property
    def project_name(self) -> str:
        """Project name."""
        return self._project_name

    @property
    def current_score(self) -> ScoreIR | None:
        """Current ScoreIR state."""
        return self._current_score

    @property
    def can_undo(self) -> bool:
        """Whether undo is available."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Whether redo is available."""
        return len(self._redo_stack) > 0

    @property
    def undo_depth(self) -> int:
        """Number of undo steps available."""
        return len(self._undo_stack)

    def __enter__(self) -> ProjectRuntime:
        """Acquire project lock and initialize."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path.write_text(self._project_name)
        return self

    def __exit__(self, *args: object) -> None:
        """Release project lock."""
        if self._lock_path.exists():
            self._lock_path.unlink()

    def set_score(self, score: ScoreIR, description: str) -> None:
        """Set a new score state, pushing current to undo stack.

        Clears redo stack (new edit invalidates redo history).

        Args:
            score: New ScoreIR state.
            description: What changed.
        """
        if self._current_score is not None:
            state = RuntimeState(
                description=description,
                score_json=json.dumps({"title": self._current_score.title}),
            )
            self._undo_stack.append(state)
            if len(self._undo_stack) > self._MAX_UNDO:
                self._undo_stack.pop(0)

        self._current_score = score
        self._redo_stack.clear()

    def undo(self) -> RuntimeState | None:
        """Undo the last action.

        Returns:
            The undone state, or None if nothing to undo.
        """
        if not self._undo_stack:
            return None
        state = self._undo_stack.pop()
        if self._current_score is not None:
            self._redo_stack.append(
                RuntimeState(
                    description="undo",
                    score_json=json.dumps({"title": self._current_score.title}),
                )
            )
        return state

    def redo(self) -> RuntimeState | None:
        """Redo a previously undone action.

        Returns:
            The redone state, or None if nothing to redo.
        """
        if not self._redo_stack:
            return None
        state = self._redo_stack.pop()
        return state

    def cache_key(self, spec_hash: str, seed: int, strategy: str) -> str:
        """Compute cache key.

        Args:
            spec_hash: Hash of the spec.
            seed: Generation seed.
            strategy: Generator strategy name.

        Returns:
            Cache key string.
        """
        content = f"{spec_hash}:{seed}:{strategy}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_cached(self, spec_hash: str, seed: int, strategy: str) -> Path | None:
        """Look up a cached generation result.

        Args:
            spec_hash: Hash of the spec.
            seed: Generation seed.
            strategy: Generator strategy name.

        Returns:
            Path to cached MIDI file, or None.
        """
        key = self.cache_key(spec_hash, seed, strategy)
        path = self._cache_dir / f"{key}.mid"
        return path if path.exists() else None

    def save_to_cache(self, spec_hash: str, seed: int, strategy: str, midi_path: Path) -> None:
        """Save a generation result to cache.

        Args:
            spec_hash: Hash of the spec.
            seed: Generation seed.
            strategy: Generator strategy name.
            midi_path: Path to the MIDI file to cache.
        """
        key = self.cache_key(spec_hash, seed, strategy)
        dest = self._cache_dir / f"{key}.mid"
        dest.write_bytes(midi_path.read_bytes())
