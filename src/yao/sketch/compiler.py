"""SpecCompiler — compiles natural language descriptions into composition specs.

This module extracts musical knowledge (mood→key, pace→tempo, keyword→instruments)
from the Conductor, where it violated CLAUDE.md anti-pattern #7. The Conductor
should orchestrate pipelines, not make music theory decisions.

The SpecCompiler is the single place where NL descriptions are parsed into
structured musical parameters.

Belongs to Layer 1.5 (Sketch — between user input and specification).
"""

from __future__ import annotations

import re
from typing import Literal

from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint

_RoleType = Literal["melody", "harmony", "bass", "rhythm", "pad"]

# ── Mood → Key mapping ──────────────────────────────────────────────────

_MOOD_TO_KEY: dict[str, str] = {
    "happy": "C major",
    "joyful": "D major",
    "bright": "G major",
    "triumphant": "D major",
    "energetic": "A major",
    "calm": "F major",
    "peaceful": "F major",
    "gentle": "G major",
    "sad": "D minor",
    "melancholic": "D minor",
    "melancholy": "D minor",
    "dark": "C minor",
    "mysterious": "A minor",
    "suspenseful": "E minor",
    "dramatic": "C minor",
    "epic": "D minor",
    "romantic": "E major",
    "nostalgic": "A minor",
    "dreamy": "F major",
    "contemplative": "E minor",
    "introspective": "F# minor",
    "tense": "B minor",
    "heroic": "Bb major",
}

# ── Instrument keyword mapping ───────────────────────────────────────────

_INSTRUMENT_KEYWORDS: dict[str, list[tuple[str, _RoleType]]] = {
    "piano": [("piano", "melody")],
    "strings": [("strings_ensemble", "pad"), ("cello", "bass")],
    "orchestra": [
        ("strings_ensemble", "pad"),
        ("french_horn", "harmony"),
        ("cello", "bass"),
        ("piano", "melody"),
    ],
    "guitar": [("acoustic_guitar_nylon", "melody")],
    "synth": [("synth_pad_warm", "pad"), ("synth_lead_saw", "melody")],
    "minimal": [("piano", "melody")],
    "ambient": [("synth_pad_warm", "pad"), ("piano", "melody")],
    "cinematic": [
        ("strings_ensemble", "pad"),
        ("piano", "melody"),
        ("cello", "bass"),
        ("french_horn", "harmony"),
    ],
    "jazz": [("piano", "melody"), ("acoustic_bass", "bass")],
    "classical": [("piano", "melody"), ("violin", "melody"), ("cello", "bass")],
}

# ── Genre detection ──────────────────────────────────────────────────────

_GENRE_KEYWORDS: dict[str, str] = {
    "cinematic": "cinematic",
    "film": "cinematic",
    "movie": "cinematic",
    "jazz": "jazz",
    "classical": "classical",
    "ambient": "ambient",
    "electronic": "electronic",
    "rock": "rock",
    "pop": "pop",
    "game": "game",
    "lofi": "lofi",
    "lo-fi": "lofi",
}


class SpecCompiler:
    """Compiles natural language descriptions into CompositionSpec + TrajectorySpec.

    All musical knowledge (mood→key, pace→tempo, keyword→instruments) lives here.
    The Conductor delegates to this class instead of containing music theory logic.
    """

    def compile(
        self,
        description: str,
        project_name: str,
    ) -> tuple[CompositionSpec, TrajectorySpec]:
        """Compile a description into a spec and trajectory.

        Args:
            description: Natural language description of desired music.
            project_name: Project name (used as title).

        Returns:
            Tuple of (CompositionSpec, TrajectorySpec).
        """
        desc_lower = description.lower()

        key = self._infer_key(desc_lower)
        tempo = self._infer_tempo(desc_lower)
        instruments = self._infer_instruments(desc_lower)
        duration_seconds = self._infer_duration(desc_lower)
        genre = self._infer_genre(desc_lower)

        beats = duration_seconds * tempo / 60.0
        total_bars = max(8, round(beats / 4))  # 4/4 time

        sections = self._build_sections(total_bars, desc_lower)
        trajectory = self._build_trajectory(total_bars, desc_lower)

        spec = CompositionSpec(
            title=project_name.replace("-", " ").title(),
            genre=genre,
            key=key,
            tempo_bpm=tempo,
            time_signature="4/4",
            total_bars=total_bars,
            instruments=instruments,
            sections=sections,
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        return spec, trajectory

    def _infer_key(self, desc_lower: str) -> str:
        """Infer key signature from mood keywords."""
        for mood, mood_key in _MOOD_TO_KEY.items():
            if mood in desc_lower:
                return mood_key
        return "C major"

    def _infer_tempo(self, desc_lower: str) -> float:
        """Infer tempo from pace keywords.

        Uses longest-match-first ordering to avoid 'very fast' matching 'fast'.
        """
        # Sorted by length descending for longest match first
        tempo_terms: list[tuple[str, float]] = [
            ("very fast", 160.0),
            ("frantic", 160.0),
            ("intense", 160.0),
            ("energetic", 140.0),
            ("upbeat", 140.0),
            ("driving", 140.0),
            ("fast", 140.0),
            ("moderate", 100.0),
            ("walking", 100.0),
            ("peaceful", 80.0),
            ("ambient", 80.0),
            ("gentle", 80.0),
            ("calm", 80.0),
            ("slow", 80.0),
        ]
        for term, bpm in tempo_terms:
            if term in desc_lower:
                return bpm
        return 120.0

    def _infer_instruments(self, desc_lower: str) -> list[InstrumentSpec]:
        """Infer instruments from keyword matching."""
        instruments: list[InstrumentSpec] = []
        matched = False
        for keyword, instr_list in _INSTRUMENT_KEYWORDS.items():
            if keyword in desc_lower:
                for name, role in instr_list:
                    if not any(i.name == name for i in instruments):
                        instruments.append(InstrumentSpec(name=name, role=role))
                matched = True
        if not matched:
            instruments = [
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ]
        return instruments

    def _infer_duration(self, desc_lower: str) -> float:
        """Extract duration from description text."""
        duration_seconds = 90.0
        duration_match = re.search(r"(\d+)\s*(?:second|sec|s\b)", desc_lower)
        if duration_match:
            duration_seconds = float(duration_match.group(1))
        minute_match = re.search(r"(\d+)\s*(?:minute|min|m\b)", desc_lower)
        if minute_match:
            duration_seconds = float(minute_match.group(1)) * 60
        return duration_seconds

    def _infer_genre(self, desc_lower: str) -> str:
        """Detect genre from description keywords."""
        for keyword, genre in _GENRE_KEYWORDS.items():
            if keyword in desc_lower:
                return genre
        return "general"

    def _build_sections(self, total_bars: int, desc_lower: str) -> list[SectionSpec]:
        """Build section structure from total bars."""
        if total_bars <= 8:  # noqa: PLR2004
            return [SectionSpec(name="verse", bars=total_bars, dynamics="mf")]

        if total_bars <= 16:  # noqa: PLR2004
            half = total_bars // 2
            return [
                SectionSpec(name="verse", bars=half, dynamics="mp"),
                SectionSpec(name="chorus", bars=total_bars - half, dynamics="f"),
            ]

        intro_bars = max(2, total_bars // 8)
        outro_bars = max(2, total_bars // 8)
        body_bars = total_bars - intro_bars - outro_bars
        verse_bars = body_bars // 2
        chorus_bars = body_bars - verse_bars

        sections = [
            SectionSpec(name="intro", bars=intro_bars, dynamics="pp"),
            SectionSpec(name="verse", bars=verse_bars, dynamics="mp"),
            SectionSpec(name="chorus", bars=chorus_bars, dynamics="f"),
            SectionSpec(name="outro", bars=outro_bars, dynamics="pp"),
        ]

        if total_bars >= 32:  # noqa: PLR2004
            bridge_bars = max(4, total_bars // 8)
            chorus_bars_adj = chorus_bars - bridge_bars
            if chorus_bars_adj >= 4:  # noqa: PLR2004
                sections = [
                    SectionSpec(name="intro", bars=intro_bars, dynamics="pp"),
                    SectionSpec(name="verse", bars=verse_bars, dynamics="mp"),
                    SectionSpec(name="chorus", bars=chorus_bars_adj, dynamics="f"),
                    SectionSpec(name="bridge", bars=bridge_bars, dynamics="mf"),
                    SectionSpec(name="outro", bars=outro_bars, dynamics="pp"),
                ]

        return sections

    def _build_trajectory(self, total_bars: int, desc_lower: str) -> TrajectorySpec:
        """Build a trajectory from the description."""
        peak_bar = total_bars * 2 // 3

        if any(w in desc_lower for w in ("build", "crescendo", "rising")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=total_bars, value=0.9),
            ]
        elif any(w in desc_lower for w in ("calm", "peaceful", "ambient", "gentle")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=total_bars // 2, value=0.35),
                Waypoint(bar=total_bars, value=0.2),
            ]
        elif any(w in desc_lower for w in ("dramatic", "epic", "intense", "climax")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=peak_bar, value=0.95),
                Waypoint(bar=total_bars, value=0.15),
            ]
        else:
            waypoints = [
                Waypoint(bar=0, value=0.3),
                Waypoint(bar=peak_bar, value=0.7),
                Waypoint(bar=total_bars, value=0.25),
            ]

        return TrajectorySpec(
            tension=TrajectoryDimension(type="linear", waypoints=waypoints),
        )
