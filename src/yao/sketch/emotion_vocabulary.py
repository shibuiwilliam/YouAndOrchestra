"""Emotion vocabulary — load and query emotion-to-music mappings from Skill files.

Parses the YAML frontmatter from .claude/skills/psychology/emotion-mapping.md
and provides lookup functions for mapping emotional words to musical parameters.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _find_skill_path() -> Path:
    """Locate the emotion-mapping.md skill file relative to repo root."""
    # Walk up from this file to find .claude/ at the repo root
    candidate = Path(__file__).resolve().parent
    for _ in range(10):
        skill = candidate / ".claude" / "skills" / "psychology" / "emotion-mapping.md"
        if skill.exists():
            return skill
        candidate = candidate.parent
    # Fallback: assume repo root is 4 levels up from src/yao/sketch/
    root = Path(__file__).resolve().parent.parent.parent.parent
    return root / ".claude" / "skills" / "psychology" / "emotion-mapping.md"


_SKILL_PATH = _find_skill_path()

# Tempo hint → BPM mapping (center of range)
_TEMPO_MAP: dict[str, float] = {
    "very_slow": 57.0,
    "slow": 75.0,
    "moderate": 100.0,
    "fast": 132.0,
    "very_fast": 165.0,
}


@dataclass(frozen=True)
class EmotionEntry:
    """A single emotion-to-music mapping entry.

    Attributes:
        word: The emotion word (in original language).
        language: Language code ("ja" or "en").
        valence: Emotional valence [-1.0, 1.0] (negative=sad, positive=happy).
        arousal: Emotional arousal [-1.0, 1.0] (negative=calm, positive=excited).
        key: Suggested musical key (e.g., "D minor").
        mode: Suggested mode ("major" or "minor").
        tempo_hint: Tempo category ("slow", "moderate", "fast", etc.).
        tempo_bpm: Resolved BPM value from tempo_hint.
        instruments: Suggested instruments (may be empty).
    """

    word: str
    language: str
    valence: float
    arousal: float
    key: str
    mode: str
    tempo_hint: str
    tempo_bpm: float
    instruments: list[str]


class EmotionVocabulary:
    """Loads and queries emotion-to-music mappings from the Skill file.

    Thread-safe after initialization (immutable data).
    """

    def __init__(self, skill_path: Path | None = None) -> None:
        self._entries: dict[str, dict[str, EmotionEntry]] = {"ja": {}, "en": {}}
        path = skill_path or _SKILL_PATH
        if path.exists():
            self._load(path)

    def _load(self, path: Path) -> None:
        """Parse YAML frontmatter from the emotion-mapping.md Skill file."""
        text = path.read_text(encoding="utf-8")

        # Extract YAML block from markdown code fence
        yaml_match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
        if not yaml_match:
            return

        data = yaml.safe_load(yaml_match.group(1))
        if not data or "emotions" not in data:
            return

        for lang, entries in data["emotions"].items():
            if lang not in self._entries:
                self._entries[lang] = {}
            for word, props in entries.items():
                tempo_hint = props.get("tempo", "moderate")
                self._entries[lang][word] = EmotionEntry(
                    word=word,
                    language=lang,
                    valence=float(props.get("valence", 0.0)),
                    arousal=float(props.get("arousal", 0.0)),
                    key=props.get("key", "C major"),
                    mode=props.get("mode", "major"),
                    tempo_hint=tempo_hint,
                    tempo_bpm=_TEMPO_MAP.get(tempo_hint, 100.0),
                    instruments=props.get("instruments", []),
                )

    def lookup(self, word: str, language: str = "ja") -> EmotionEntry | None:
        """Look up an emotion word.

        Args:
            word: The emotion word to look up.
            language: Language code ("ja" or "en").

        Returns:
            EmotionEntry if found, None otherwise.
        """
        return self._entries.get(language, {}).get(word)

    def scan_text(self, text: str, language: str = "ja") -> list[EmotionEntry]:
        """Scan text for all matching emotion words.

        Args:
            text: Input text to scan.
            language: Language code.

        Returns:
            List of matched EmotionEntry objects (may be empty).
        """
        entries = self._entries.get(language, {})
        matches: list[EmotionEntry] = []
        for word, entry in entries.items():
            if word in text:
                matches.append(entry)
        return matches

    def aggregate_emotions(self, entries: list[EmotionEntry]) -> dict[str, Any]:
        """Aggregate multiple emotion entries into musical parameters.

        Averages valence and arousal, then derives key, tempo, mode.

        Args:
            entries: List of matched emotion entries.

        Returns:
            Dict with aggregated musical parameters:
            - key: str
            - mode: str ("major" or "minor")
            - tempo_bpm: float
            - valence: float (average)
            - arousal: float (average)
            - instruments: list[str] (union of all suggestions)
        """
        if not entries:
            return {
                "key": "C major",
                "mode": "major",
                "tempo_bpm": 120.0,
                "valence": 0.0,
                "arousal": 0.0,
                "instruments": [],
            }

        avg_valence = sum(e.valence for e in entries) / len(entries)
        avg_arousal = sum(e.arousal for e in entries) / len(entries)

        # Use the entry closest to the average as the primary
        best = min(
            entries,
            key=lambda e: (e.valence - avg_valence) ** 2 + (e.arousal - avg_arousal) ** 2,
        )

        # Derive tempo from arousal
        if avg_arousal >= 0.5:  # noqa: PLR2004
            tempo = 140.0
        elif avg_arousal >= 0.2:  # noqa: PLR2004
            tempo = 120.0
        elif avg_arousal >= -0.2:  # noqa: PLR2004
            tempo = 100.0
        else:
            tempo = 80.0

        # Override with best entry's tempo if more specific
        if best.tempo_bpm != 100.0:
            tempo = best.tempo_bpm

        # Collect unique instruments
        all_instruments: list[str] = []
        seen: set[str] = set()
        for e in entries:
            for instr in e.instruments:
                if instr not in seen:
                    all_instruments.append(instr)
                    seen.add(instr)

        return {
            "key": best.key,
            "mode": best.mode,
            "tempo_bpm": tempo,
            "valence": round(avg_valence, 2),
            "arousal": round(avg_arousal, 2),
            "instruments": all_instruments,
        }

    def languages(self) -> list[str]:
        """Return available language codes."""
        return [lang for lang, entries in self._entries.items() if entries]

    def word_count(self, language: str = "ja") -> int:
        """Return number of emotion words for a language."""
        return len(self._entries.get(language, {}))
