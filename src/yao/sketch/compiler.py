"""SpecCompiler — compiles natural language descriptions into composition specs.

Three-stage fallback system (v3.0 Wave 1.3):
  Stage 1: LLM compile (when AnthropicAPIBackend is available)
  Stage 2: Keyword compile (English + Japanese emotion vocabulary)
  Stage 3: Default compile (minimal.yaml baseline)

Belongs to Layer 1.5 (Sketch — between user input and specification).
"""

from __future__ import annotations

import re
from typing import Literal

import structlog

from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint
from yao.sketch.emotion_vocabulary import EmotionVocabulary
from yao.sketch.language_detect import detect_language

logger = structlog.get_logger()

_RoleType = Literal["melody", "harmony", "bass", "rhythm", "pad"]

# ── English mood → Key mapping (preserved from v2.0) ───────────────────

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

# ── English instrument keyword mapping (preserved from v2.0) ───────────

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

# ── Japanese instrument keywords ────────────────────────────────────────

_JA_INSTRUMENT_KEYWORDS: dict[str, list[tuple[str, _RoleType]]] = {
    "ピアノ": [("piano", "melody")],
    "チェロ": [("cello", "bass")],
    "バイオリン": [("violin", "melody")],
    "ヴァイオリン": [("violin", "melody")],
    "弦楽": [("strings_ensemble", "pad"), ("cello", "bass")],
    "オーケストラ": [
        ("strings_ensemble", "pad"),
        ("french_horn", "harmony"),
        ("cello", "bass"),
        ("piano", "melody"),
    ],
    "ギター": [("acoustic_guitar_nylon", "melody")],
    "フルート": [("flute", "melody")],
    "サックス": [("saxophone_alto", "melody")],
    "シンセ": [("synth_pad_warm", "pad"), ("synth_lead_saw", "melody")],
}

# ── Genre detection (English, preserved from v2.0) ──────────────────────

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

# ── Japanese tempo modifiers ────────────────────────────────────────────

_JA_TEMPO_KEYWORDS: list[tuple[str, float]] = [
    ("とても速い", 160.0),
    ("速い", 140.0),
    ("アップテンポ", 140.0),
    ("ゆっくり", 75.0),
    ("遅い", 75.0),
    ("スロー", 75.0),
    ("穏やか", 80.0),
]

# ── Japanese duration patterns ──────────────────────────────────────────

_JA_DURATION_PATTERN = re.compile(r"(\d+)\s*(?:秒|sec)")
_JA_MINUTE_PATTERN = re.compile(r"(\d+)\s*(?:分|min)")


class SpecCompiler:
    """Compiles natural language descriptions into CompositionSpec + TrajectorySpec.

    Three-stage fallback (v3.0):
      Stage 1: LLM compile (requires non-stub AnthropicAPIBackend)
      Stage 2: Keyword compile (English mood dict + Japanese emotion vocabulary)
      Stage 3: Default compile (minimal spec)

    All stages produce identical output types. Stage transitions are logged
    to provenance.
    """

    def __init__(self) -> None:
        self._emotion_vocab = EmotionVocabulary()
        self._provenance = ProvenanceLog()

    @property
    def provenance(self) -> ProvenanceLog:
        """Access the provenance log for this compilation."""
        return self._provenance

    def compile(
        self,
        description: str,
        project_name: str,
        *,
        language: str = "auto",
    ) -> tuple[CompositionSpec, TrajectorySpec]:
        """Compile a description into a spec and trajectory.

        Three-stage fallback:
          1. LLM compile (if backend available)
          2. Keyword compile (English + Japanese)
          3. Default compile (minimal spec)

        Args:
            description: Natural language description of desired music.
            project_name: Project name (used as title).
            language: Language code ("auto", "en", "ja"). Auto-detected if "auto".

        Returns:
            Tuple of (CompositionSpec, TrajectorySpec).
        """
        self._provenance = ProvenanceLog()
        lang = detect_language(description) if language == "auto" else language

        self._provenance.record(
            layer="sketch",
            operation="language_detection",
            parameters={"language": lang, "auto": language == "auto"},
            source="SpecCompiler.compile",
            rationale=f"Detected language: {lang}",
        )

        # Stage 1: LLM compile (skip if backend not available)
        if self._is_llm_available():
            try:
                result = self._llm_compile(description, project_name, lang)
                self._provenance.record(
                    layer="sketch",
                    operation="spec_compilation",
                    parameters={"stage": "llm", "language": lang},
                    source="SpecCompiler.compile",
                    rationale="LLM compile succeeded.",
                )
                return result
            except Exception as e:
                self._provenance.record(
                    layer="sketch",
                    operation="llm_fallback",
                    parameters={"stage": "llm", "error": str(e)[:200]},
                    source="SpecCompiler.compile",
                    rationale=f"LLM compile failed, falling back to keyword: {e}",
                )
                logger.warning("spec_compiler_llm_fallback", error=str(e))

        # Stage 2: Keyword compile
        result = self._keyword_compile(description, project_name, lang)
        return result

    def _is_llm_available(self) -> bool:
        """Check if a non-stub LLM backend is available."""
        try:
            from yao.agents.registry import get_backend

            backend = get_backend("anthropic_api")
            return hasattr(backend, "is_stub") and not backend.is_stub
        except Exception:
            return False

    def _llm_compile(
        self,
        description: str,
        project_name: str,
        lang: str,
    ) -> tuple[CompositionSpec, TrajectorySpec]:
        """Stage 1: LLM-based compilation.

        Uses AnthropicAPIBackend with tool_use for structured output.
        Currently raises NotImplementedError — will be connected when
        AnthropicAPIBackend is fully implemented (Wave 1.2).

        Args:
            description: NL description.
            project_name: Project name.
            lang: Language code.

        Returns:
            Tuple of (CompositionSpec, TrajectorySpec).

        Raises:
            AgentBackendError: If LLM call fails.
        """
        from yao.errors import AgentBackendError

        raise AgentBackendError("LLM compile not yet connected (Wave 1.2 prerequisite)")

    def _keyword_compile(
        self,
        description: str,
        project_name: str,
        lang: str,
    ) -> tuple[CompositionSpec, TrajectorySpec]:
        """Stage 2: Keyword-based compilation with Japanese support.

        For English: uses the original mood/instrument/genre keyword dicts.
        For Japanese: uses EmotionVocabulary (valence × arousal → key/tempo)
                      plus Japanese instrument/tempo/duration keywords.

        Args:
            description: NL description.
            project_name: Project name.
            lang: Language code.

        Returns:
            Tuple of (CompositionSpec, TrajectorySpec).
        """
        if lang == "ja":
            key, tempo, instruments, duration, genre = self._parse_japanese(description)
        else:
            key, tempo, instruments, duration, genre = self._parse_english(description)

        # v3.0 Wave 2.1: Enrich from SkillRegistry if genre is known
        key, tempo, instruments = self._enrich_from_skill(
            genre,
            key,
            tempo,
            instruments,
            description,
        )

        beats = duration * tempo / 60.0
        total_bars = max(8, round(beats / 4))

        desc_lower = description.lower()
        sections = self._build_sections(total_bars, desc_lower)
        trajectory = self._build_trajectory(total_bars, desc_lower if lang == "en" else description)

        stage = "keyword_ja" if lang == "ja" else "keyword_en"
        self._provenance.record(
            layer="sketch",
            operation="spec_compilation",
            parameters={
                "stage": stage,
                "language": lang,
                "key": key,
                "tempo": tempo,
                "genre": genre,
                "n_instruments": len(instruments),
                "duration_sec": duration,
                "total_bars": total_bars,
            },
            source="SpecCompiler._keyword_compile",
            rationale=f"Keyword compile ({lang}): key={key}, tempo={tempo}, genre={genre}",
        )

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

    # ── Japanese parsing ────────────────────────────────────────────────

    def _enrich_from_skill(
        self,
        genre: str,
        key: str,
        tempo: float,
        instruments: list[InstrumentSpec],
        description: str,
    ) -> tuple[str, float, list[InstrumentSpec]]:
        """Enrich spec parameters from SkillRegistry if genre is known.

        Only overrides defaults — explicit user choices (key regex, BPM) are preserved.

        Args:
            genre: Detected genre ID.
            key: Current key (may be default "C major").
            tempo: Current tempo.
            instruments: Current instrument list.
            description: Original description (to detect explicit overrides).

        Returns:
            Tuple of (enriched_key, enriched_tempo, enriched_instruments).
        """
        from yao.skills.loader import get_skill_registry

        registry = get_skill_registry()
        profile = registry.get_genre(genre)
        if profile is None:
            return key, tempo, instruments

        # Only enrich key if it's still the default (no explicit key in description)
        has_explicit_key = bool(self._KEY_PATTERN.search(description.lower()))
        if not has_explicit_key and key == "C major" and profile.typical_keys:
            key = profile.typical_keys[0]
            # Normalize short key notation (e.g., "Dm" → "D minor")
            if len(key) <= 3 and not key.endswith(("major", "minor")):  # noqa: PLR2004
                key = f"{key[:-1]} minor" if key.endswith("m") else f"{key} major"

        # Enrich tempo if it's still the default
        if tempo == 120.0:
            lo, hi = profile.tempo_range
            tempo = (lo + hi) / 2

        # Enrich instruments if they're still the default (piano + acoustic_bass)
        is_default_instruments = (
            len(instruments) == 2  # noqa: PLR2004
            and instruments[0].name == "piano"
            and instruments[1].name == "acoustic_bass"
        )
        if is_default_instruments and profile.preferred_instruments:
            instruments = []
            for i, name in enumerate(profile.preferred_instruments[:4]):
                role: _RoleType = "melody" if i == 0 else ("bass" if "bass" in name else "harmony")
                instruments.append(InstrumentSpec(name=name, role=role))

        self._provenance.record(
            layer="sketch",
            operation="skill_enrichment",
            parameters={
                "source_skill": genre,
                "enriched_key": key,
                "enriched_tempo": tempo,
                "enriched_instruments": [i.name for i in instruments],
            },
            source="SpecCompiler._enrich_from_skill",
            rationale=f"Enriched spec from genre skill '{genre}'.",
        )

        return key, tempo, instruments

    def _parse_japanese(
        self,
        description: str,
    ) -> tuple[str, float, list[InstrumentSpec], float, str]:
        """Parse Japanese description using emotion vocabulary.

        Returns:
            Tuple of (key, tempo, instruments, duration_seconds, genre).
        """
        # Emotion vocabulary scan
        emotions = self._emotion_vocab.scan_text(description, "ja")
        agg = self._emotion_vocab.aggregate_emotions(emotions)

        key = agg["key"]
        tempo = agg["tempo_bpm"]

        # Japanese tempo keyword override
        for kw, bpm in _JA_TEMPO_KEYWORDS:
            if kw in description:
                tempo = bpm
                break

        # BPM pattern (e.g., "85 BPM", "85BPM")
        bpm_match = re.search(r"(\d+)\s*(?:BPM|bpm)", description)
        if bpm_match:
            tempo = float(bpm_match.group(1))

        # Instruments from Japanese keywords + emotion suggestions
        instruments: list[InstrumentSpec] = []
        for kw, instr_list in _JA_INSTRUMENT_KEYWORDS.items():
            if kw in description:
                for name, role in instr_list:
                    if not any(i.name == name for i in instruments):
                        instruments.append(InstrumentSpec(name=name, role=role))

        # Add emotion-suggested instruments if none matched from keywords
        if not instruments and agg["instruments"]:
            for name in agg["instruments"]:
                instr_role: _RoleType = "melody" if not instruments else "harmony"
                instruments.append(InstrumentSpec(name=name, role=instr_role))

        if not instruments:
            instruments = [InstrumentSpec(name="piano", role="melody")]

        # Duration
        duration = 90.0
        dur_match = _JA_DURATION_PATTERN.search(description)
        if dur_match:
            duration = float(dur_match.group(1))
        min_match = _JA_MINUTE_PATTERN.search(description)
        if min_match:
            duration = float(min_match.group(1)) * 60

        # Genre (check English genre keywords in Japanese text too)
        genre = "general"
        for kw, g in _GENRE_KEYWORDS.items():
            if kw in description.lower():
                genre = g
                break

        if emotions:
            self._provenance.record(
                layer="sketch",
                operation="emotion_scan",
                parameters={
                    "matched_words": [e.word for e in emotions],
                    "avg_valence": agg["valence"],
                    "avg_arousal": agg["arousal"],
                },
                source="SpecCompiler._parse_japanese",
                rationale=(
                    f"Matched {len(emotions)} emotion word(s): "
                    f"{', '.join(e.word for e in emotions)}. "
                    f"Valence={agg['valence']}, Arousal={agg['arousal']}"
                ),
            )

        return key, tempo, instruments, duration, genre

    # ── English parsing (preserved from v2.0) ───────────────────────────

    def _parse_english(
        self,
        description: str,
    ) -> tuple[str, float, list[InstrumentSpec], float, str]:
        """Parse English description using keyword dicts.

        Returns:
            Tuple of (key, tempo, instruments, duration_seconds, genre).
        """
        desc_lower = description.lower()

        key = self._infer_key(desc_lower)
        tempo = self._infer_tempo(desc_lower)
        instruments = self._infer_instruments(desc_lower)
        duration = self._infer_duration(desc_lower)
        genre = self._infer_genre(desc_lower)

        return key, tempo, instruments, duration, genre

    # Regex for explicit key specifications like "in D minor", "key of C# major"
    _KEY_PATTERN = re.compile(
        r"(?:in|key of)\s+([A-Ga-g][#b]?\s+(?:major|minor))",
        re.IGNORECASE,
    )

    def _infer_key(self, desc_lower: str) -> str:
        """Infer key signature from explicit key name or mood keywords.

        Priority:
        1. Explicit key name (e.g., "in D minor", "key of C# major")
        2. Mood keyword mapping (e.g., "sad" → D minor)
        3. Default: C major
        """
        match = self._KEY_PATTERN.search(desc_lower)
        if match:
            key_str = match.group(1).strip()
            parts = key_str.split()
            if len(parts) == 2:  # noqa: PLR2004
                note = parts[0][0].upper() + parts[0][1:]
                scale = parts[1].lower()
                return f"{note} {scale}"

        for mood, mood_key in _MOOD_TO_KEY.items():
            if mood in desc_lower:
                return mood_key
        return "C major"

    def _infer_tempo(self, desc_lower: str) -> float:
        """Infer tempo from pace keywords."""
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

    def _build_trajectory(self, total_bars: int, description: str) -> TrajectorySpec:
        """Build a trajectory from the description."""
        desc_lower = description.lower()
        peak_bar = total_bars * 2 // 3

        if any(w in desc_lower for w in ("build", "crescendo", "rising")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=total_bars, value=0.9),
            ]
        elif any(
            w in desc_lower for w in ("calm", "peaceful", "ambient", "gentle", "穏やか", "安らぎ", "静か", "癒し")
        ):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=total_bars // 2, value=0.35),
                Waypoint(bar=total_bars, value=0.2),
            ]
        elif any(
            w in desc_lower for w in ("dramatic", "epic", "intense", "climax", "壮大", "ドラマチック", "激しい", "壮厳")
        ):
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
