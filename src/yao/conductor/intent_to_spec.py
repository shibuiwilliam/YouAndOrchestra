"""IntentToSpec — build a CompositionSpec from a StructuredIntent.

Converts the multi-dimensional emotional/stylistic vector from
IntentParser into a complete, valid CompositionSpec with appropriate
key, mode, tempo, instruments, sections, and genre selection.

See PROJECT.md §11.3 and IMPROVEMENT.md §4.6.
"""

from __future__ import annotations

from yao.conductor.intent_parser import IntentParser, StructuredIntent
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)

# Tempo mapping from arousal + tempo_hint
_TEMPO_MAP: dict[str, tuple[float, float]] = {
    "very_slow": (50.0, 65.0),
    "slow": (60.0, 80.0),
    "medium": (85.0, 115.0),
    "fast": (120.0, 150.0),
    "very_fast": (155.0, 200.0),
}

# Default instruments by use case
_USE_CASE_INSTRUMENTS: dict[str, list[tuple[str, str]]] = {
    "bgm": [("piano", "melody"), ("bass", "bass"), ("drums", "rhythm")],
    "meditation": [("piano", "melody"), ("strings", "pad")],
    "workout": [("synthesizer", "melody"), ("bass", "bass"), ("drums", "rhythm")],
    "game": [("piano", "melody"), ("strings", "harmony"), ("drums", "rhythm")],
    "film": [("strings", "melody"), ("piano", "harmony"), ("cello", "bass")],
    "sleep": [("piano", "melody")],
    "party": [("synthesizer", "melody"), ("bass", "bass"), ("drums", "rhythm")],
    "foreground": [("piano", "melody"), ("bass", "bass"), ("drums", "rhythm")],
}

# Key selection: major keys for positive valence, minor for negative
_MAJOR_KEYS = ["C", "D", "Eb", "F", "G", "A", "Bb"]
_MINOR_KEYS = ["A", "D", "E", "B", "C", "F#", "G"]


class IntentToSpec:
    """Builds a complete CompositionSpec from a StructuredIntent.

    Every field of the spec is derived from the intent's emotional
    dimensions, genre candidates, and contextual hints. The spec
    is always complete — never partial.
    """

    def __init__(self) -> None:
        """Initialize with an IntentParser for mode selection."""
        self._parser = IntentParser()

    def build_spec(self, intent: StructuredIntent) -> CompositionSpec:
        """Build a complete CompositionSpec from a StructuredIntent.

        Args:
            intent: The parsed intent with all dimensions populated.

        Returns:
            A valid CompositionSpec ready for generation.
        """
        genre = self._select_genre(intent)
        key = self._select_key(intent)
        mode = self._parser.select_mode(intent)
        tempo = self._select_tempo(intent)
        instruments = self._select_instruments(intent)
        sections = self._design_sections(intent)
        strategy = self._select_strategy(genre)

        return CompositionSpec(
            title=intent.raw_description[:50].strip(),
            genre=genre,
            key=f"{key} {mode}",
            tempo_bpm=tempo,
            instruments=instruments,
            sections=sections,
            generation=GenerationConfig(
                strategy=strategy,
                seed=42,
                temperature=self._select_temperature(intent),
                # Freshly-authored specs get thematic recurrence by default so
                # the primary melody states and restates a theme across the
                # form. Existing spec files (flag absent) are unaffected.
                thematic_development=True,
            ),
        )

    def _select_genre(self, intent: StructuredIntent) -> str:
        """Select primary genre from candidates."""
        if intent.genre_candidates:
            return intent.genre_candidates[0][0]
        return "lofi_hiphop"

    def _select_key(self, intent: StructuredIntent) -> str:
        """Select key based on valence."""
        if intent.valence >= 0:
            # Positive → major key, pick based on warmth
            idx = int((intent.warmth + 1.0) / 2.0 * (len(_MAJOR_KEYS) - 1))
            idx = max(0, min(idx, len(_MAJOR_KEYS) - 1))
            return _MAJOR_KEYS[idx]
        else:
            # Negative → minor key
            idx = int((abs(intent.valence)) * (len(_MINOR_KEYS) - 1))
            idx = max(0, min(idx, len(_MINOR_KEYS) - 1))
            return _MINOR_KEYS[idx]

    def _select_tempo(self, intent: StructuredIntent) -> float:
        """Select tempo from arousal and tempo hint."""
        if intent.tempo_hint and intent.tempo_hint in _TEMPO_MAP:
            low, high = _TEMPO_MAP[intent.tempo_hint]
            return low + (high - low) * intent.arousal
        # Derive from arousal alone
        return 70.0 + intent.arousal * 80.0  # 70–150 BPM

    def _select_instruments(self, intent: StructuredIntent) -> list[InstrumentSpec]:
        """Select instruments from intent and use case."""
        if intent.instruments_mentioned:
            specs: list[InstrumentSpec] = []
            for i, inst in enumerate(intent.instruments_mentioned[:4]):
                if i == 0:
                    specs.append(InstrumentSpec(name=inst, role="melody"))
                elif "bass" in inst:
                    specs.append(InstrumentSpec(name=inst, role="bass"))
                else:
                    specs.append(InstrumentSpec(name=inst, role="harmony"))
            return specs

        # Default by use case
        defaults = _USE_CASE_INSTRUMENTS.get(intent.use_case, _USE_CASE_INSTRUMENTS["bgm"])
        return [InstrumentSpec(name=name, role=role) for name, role in defaults]  # type: ignore[arg-type]

    def _design_sections(self, intent: StructuredIntent) -> list[SectionSpec]:
        """Design form (sections) from duration and use case."""
        total_seconds = intent.duration_seconds
        # Estimate tempo (we don't have the final tempo yet, use arousal proxy)
        est_tempo = 70.0 + intent.arousal * 80.0
        beats_per_bar = 4.0
        seconds_per_bar = beats_per_bar * 60.0 / est_tempo
        total_bars = max(4, int(total_seconds / seconds_per_bar))

        if total_bars <= 8:  # noqa: PLR2004
            return [SectionSpec(name="main", bars=total_bars)]

        if total_bars <= 16:  # noqa: PLR2004
            intro = max(2, total_bars // 4)
            main = total_bars - intro
            return [
                SectionSpec(name="intro", bars=intro, dynamics="pp"),
                SectionSpec(name="main", bars=main, dynamics="mf"),
            ]

        # Standard form for longer pieces
        intro = max(2, total_bars // 8)
        verse = max(4, total_bars // 4)
        chorus = max(4, total_bars // 4)
        remaining = total_bars - intro - verse - chorus
        outro = min(4, max(2, remaining))
        verse2 = remaining - outro

        sections = [
            SectionSpec(name="intro", bars=intro, dynamics="pp"),
            SectionSpec(name="verse", bars=verse, dynamics="mp"),
            SectionSpec(name="chorus", bars=chorus, dynamics="f"),
        ]
        if verse2 > 0:
            sections.append(SectionSpec(name="verse2", bars=verse2, dynamics="mp"))
        sections.append(SectionSpec(name="outro", bars=outro, dynamics="pp"))

        return sections

    def _select_strategy(self, genre: str) -> str:
        """Select generation strategy based on genre."""
        # phrase_aware for genres with melodic profiles
        return "phrase_aware"

    def _select_temperature(self, intent: StructuredIntent) -> float:
        """Select temperature from arousal and tension."""
        # Higher tension/arousal → more variation
        return min(1.0, 0.3 + intent.arousal * 0.3 + intent.tension * 0.2)
