"""Sketch dialogue state — persistence for multi-turn /sketch sessions.

Saves and restores the 6-turn dialogue state so that users can
interrupt and resume sketch sessions.

Belongs to Layer 1.5 (Sketch).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SketchState:
    """Persistent state for a multi-turn /sketch dialogue.

    Attributes:
        turn: Current turn number (1-6).
        project_name: Name of the project being sketched.
        emotion: Core emotion identified in Turn 1.
        purpose: Musical purpose (study, game, film, etc.).
        context: Listening context (headphones, speakers, etc.).
        like_references: Styles/genres to draw from.
        avoid_references: Styles/genres to avoid.
        instruments: Chosen instruments with roles.
        duration_seconds: Target duration.
        key: Musical key.
        tempo_bpm: Tempo.
        time_signature: Time signature.
        sections: Section structure.
        trajectory_waypoints: Tension curve waypoints.
        climax_section: Which section is the climax.
        loopable: Whether the piece should loop.
        generator_strategy: Which realizer to use.
        temperature: Generation temperature.
        seed: Random seed.
    """

    turn: int = 1
    project_name: str = ""
    emotion: str = ""
    purpose: str = ""
    context: str = ""
    like_references: list[str] = field(default_factory=list)
    avoid_references: list[str] = field(default_factory=list)
    instruments: list[dict[str, str]] = field(default_factory=list)
    duration_seconds: float = 90.0
    key: str = ""
    tempo_bpm: float = 120.0
    time_signature: str = "4/4"
    sections: list[dict[str, Any]] = field(default_factory=list)
    trajectory_waypoints: list[list[float]] = field(default_factory=list)
    climax_section: str = ""
    loopable: bool = False
    generator_strategy: str = "stochastic_v2"
    temperature: float = 0.4
    seed: int = 42

    def save(self, project_dir: Path) -> Path:
        """Save state to sketch_state.json in the project directory.

        Args:
            project_dir: Project directory (specs/projects/<name>/).

        Returns:
            Path to the saved file.
        """
        project_dir.mkdir(parents=True, exist_ok=True)
        path = project_dir / "sketch_state.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        return path

    @classmethod
    def load(cls, project_dir: Path) -> SketchState:
        """Load state from sketch_state.json.

        Args:
            project_dir: Project directory containing sketch_state.json.

        Returns:
            Restored SketchState.

        Raises:
            FileNotFoundError: If sketch_state.json doesn't exist.
        """
        path = project_dir / "sketch_state.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def exists(cls, project_dir: Path) -> bool:
        """Check if a sketch state exists for a project."""
        return (project_dir / "sketch_state.json").exists()

    def advance_turn(self) -> None:
        """Move to the next turn."""
        self.turn = min(self.turn + 1, 6)

    def is_complete(self) -> bool:
        """Whether all 6 turns have been completed."""
        return self.turn >= 6

    def summary(self) -> str:
        """Human-readable summary of current state."""
        lines = [f"Sketch: {self.project_name} (Turn {self.turn}/6)"]
        if self.emotion:
            lines.append(f"  Emotion: {self.emotion}")
        if self.purpose:
            lines.append(f"  Purpose: {self.purpose}")
        if self.key:
            lines.append(f"  Key: {self.key}, Tempo: {self.tempo_bpm} BPM")
        if self.instruments:
            instr_str = ", ".join(f"{i['name']}({i.get('role', '?')})" for i in self.instruments)
            lines.append(f"  Instruments: {instr_str}")
        if self.sections:
            sec_str = " → ".join(s.get("name", "?") for s in self.sections)
            lines.append(f"  Sections: {sec_str}")
        return "\n".join(lines)
