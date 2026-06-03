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

from yao.genre.normalization import (
    _GENRE_ALIASES,
    _JA_GENRE_ALIASES,
    normalize_genre_with_fallback,
)
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    DrumsSpec,
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
    "サックス": [("alto_sax", "melody")],
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
        trajectory = self._build_trajectory(
            total_bars,
            desc_lower if lang == "en" else description,
            genre=genre,
        )

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

        drums = self._infer_drums_from_genre(genre, tempo)

        spec = CompositionSpec(
            title=project_name.replace("-", " ").title(),
            genre=genre,
            key=key,
            tempo_bpm=tempo,
            time_signature="4/4",
            total_bars=total_bars,
            instruments=instruments,
            sections=sections,
            drums=drums,
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        if drums is not None:
            self._provenance.record(
                layer="sketch",
                operation="drums_auto_attached",
                parameters={
                    "genre": genre,
                    "pattern_family": drums.pattern_family,
                },
                source="SpecCompiler._keyword_compile",
                rationale=f"Auto-attached drums '{drums.pattern_family}' from genre '{genre}'.",
            )

        return spec, trajectory

    def _infer_drums_from_genre(self, genre: str, tempo: float) -> DrumsSpec | None:
        """Derive DrumsSpec from genre profile if drums are required."""
        from yao.constants.genre_profile import get_genre_profile

        profile = get_genre_profile(genre)
        if profile is None or not profile.requires_drums:
            return None
        pattern = profile.default_drum_pattern or "pop_8beat"
        swing = max(0.0, (profile.swing_ratio - 0.5) * 2.0)
        return DrumsSpec(
            pattern_family=pattern,
            swing=swing,
            humanize_ms=5.0,
            ghost_notes_density=0.0,
        )

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

        # Instrument enrichment is now handled by _infer_instruments (genre-driven).
        # _enrich_from_skill only touches key and tempo.

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

        # Genre: check Japanese aliases first, then English aliases
        genre = "pop_mainstream"
        for ja_kw, profile_id in _JA_GENRE_ALIASES.items():
            if ja_kw in description:
                genre = profile_id
                break
        else:
            # Fall back to English keyword detection
            genre = self._infer_genre(description.lower())

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
        genre = self._infer_genre(desc_lower)
        instruments = self._infer_instruments(desc_lower, detected_genre=genre)
        duration = self._infer_duration(desc_lower)

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

    def _infer_instruments(
        self,
        desc_lower: str,
        detected_genre: str = "",
    ) -> list[InstrumentSpec]:
        """Infer instruments from genre profile + explicit keyword mentions.

        Priority:
        1. Genre profile's preferred_instruments (up to 4)
        2. User-mentioned instruments added on top
        3. Fallback to piano + bass if nothing else
        """
        from yao.constants.genre_profile import get_genre_profile
        from yao.constants.instruments import INSTRUMENT_RANGES

        instruments: list[InstrumentSpec] = []
        seen_names: set[str] = set()

        # Phase 1: Genre profile instruments
        profile = get_genre_profile(detected_genre) if detected_genre else None
        if profile and profile.preferred_instruments:
            for i, name in enumerate(profile.preferred_instruments[:4]):
                if name not in INSTRUMENT_RANGES:
                    continue
                role = self._infer_role_for_instrument(name, position=i)
                instruments.append(InstrumentSpec(name=name, role=role))
                seen_names.add(name)

        # Phase 2: Explicit user mentions
        mention_map: dict[str, list[str]] = {
            "electric piano": ["electric_piano_rhodes"],
            "rhodes": ["electric_piano_rhodes"],
            "wurli": ["electric_piano_wurli"],
            "distorted guitar": ["electric_guitar_distorted"],
            "electric guitar": ["electric_guitar_overdrive"],
            "acoustic guitar": ["acoustic_guitar_steel"],
            "nylon guitar": ["acoustic_guitar_nylon"],
            "upright bass": ["upright_bass"],
            "synth bass": ["synth_bass"],
            "alto sax": ["alto_sax"],
            "tenor sax": ["tenor_sax"],
            "saxophone": ["alto_sax"],
            "piano": ["piano"],
            "organ": ["hammond_organ"],
            "guitar": [],
            "bass": ["electric_bass_finger"],
            "808": ["synth_bass_sub"],
            "violin": ["violin"],
            "viola": ["viola"],
            "cello": ["cello"],
            "contrabass": ["contrabass"],
            "strings": ["strings_ensemble"],
            "orchestra": ["strings_ensemble", "french_horn"],
            "horn": ["french_horn"],
            "trumpet": ["trumpet"],
            "trombone": ["trombone"],
            "flute": ["flute"],
            "clarinet": ["clarinet"],
            "oboe": ["oboe"],
            "synth": ["synth_lead_saw", "synth_pad_warm"],
            "pad": ["synth_pad_warm"],
            "lead": ["synth_lead_saw"],
            "vibraphone": ["vibraphone"],
            "marimba": ["marimba"],
        }

        # Disambiguate "guitar" by context
        if "guitar" in desc_lower:
            if any(w in desc_lower for w in ("rock", "metal", "punk", "distorted", "heavy")):
                mention_map["guitar"] = ["electric_guitar_distorted"]
            elif any(w in desc_lower for w in ("jazz", "clean", "blues")):
                mention_map["guitar"] = ["electric_guitar_clean"]
            elif any(w in desc_lower for w in ("country", "folk", "acoustic")):
                mention_map["guitar"] = ["acoustic_guitar_steel"]
            else:
                mention_map["guitar"] = ["acoustic_guitar_steel"]

        # Longest keywords first
        for kw in sorted(mention_map.keys(), key=len, reverse=True):
            if kw in desc_lower:
                for name in mention_map[kw]:
                    if name in INSTRUMENT_RANGES and name not in seen_names:
                        role = self._infer_role_for_instrument(name, position=len(instruments))
                        instruments.append(InstrumentSpec(name=name, role=role))
                        seen_names.add(name)

        # Phase 3: Fallback
        if not instruments:
            instruments = [
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="electric_bass_finger", role="bass"),
            ]

        return instruments[:6]

    def _infer_role_for_instrument(self, name: str, position: int) -> _RoleType:
        """Infer a role for an instrument based on name and position."""
        from yao.constants.instruments import INSTRUMENT_RANGES

        if name not in INSTRUMENT_RANGES:
            return "melody"
        family = INSTRUMENT_RANGES[name].family
        if family == "bass":
            return "bass"
        if name.startswith("synth_pad"):
            return "pad"
        if name in ("strings_ensemble",) and position > 0:
            return "harmony"
        return "melody" if position == 0 else "harmony"

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
        """Detect genre from description keywords and normalize to registry ID.

        Uses _GENRE_ALIASES for keyword detection (longest match first to
        avoid partial match issues like "lo-fi" vs "fi"), then falls back
        to direct registered ID matching.
        """
        from yao.constants.genre_profile import all_genre_profiles

        # Longest keywords first to avoid partial-match issues
        sorted_aliases = sorted(_GENRE_ALIASES.keys(), key=len, reverse=True)
        for kw in sorted_aliases:
            if f" {kw} " in f" {desc_lower} " or desc_lower == kw:
                registered_id = _GENRE_ALIASES[kw]
                if registered_id in all_genre_profiles():
                    return registered_id

        # Direct registered ID match
        for genre_id in all_genre_profiles():
            if genre_id in desc_lower:
                return genre_id

        return normalize_genre_with_fallback("", fallback="pop_mainstream")

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

    # Genre-aware trajectory shapes: (relative_position [0..1], tension [0..1])
    _GENRE_TRAJECTORY_SHAPES: dict[str, list[tuple[float, float]]] = {
        # Ambient: flat
        "ambient": [(0.0, 0.25), (0.5, 0.40), (1.0, 0.30)],
        "ambient_dark": [(0.0, 0.30), (0.5, 0.45), (1.0, 0.35)],
        # Cinematic: arch
        "cinematic": [(0.0, 0.20), (0.66, 0.95), (1.0, 0.20)],
        # Classical
        "neoclassical": [(0.0, 0.30), (0.50, 0.70), (1.0, 0.35)],
        "classical_baroque": [(0.0, 0.50), (0.50, 0.65), (1.0, 0.50)],
        "classical_romantic": [(0.0, 0.25), (0.66, 0.85), (1.0, 0.30)],
        # EDM: build-drop
        "electronic_house": [
            (0.0, 0.40),
            (0.30, 0.60),
            (0.45, 0.90),
            (0.50, 0.30),
            (0.75, 0.95),
            (1.0, 0.55),
        ],
        "electronic_techno": [(0.0, 0.50), (0.50, 0.75), (1.0, 0.60)],
        "electronic_trance": [(0.0, 0.30), (0.40, 0.60), (0.50, 0.85), (0.70, 0.95), (1.0, 0.50)],
        "electronic_synthwave": [(0.0, 0.40), (0.50, 0.70), (1.0, 0.50)],
        # Hip-hop: loop-flat
        "hiphop_boom_bap": [(0.0, 0.50), (0.50, 0.55), (1.0, 0.50)],
        "hiphop_trap": [(0.0, 0.50), (0.50, 0.65), (1.0, 0.55)],
        "lofi_hiphop": [(0.0, 0.30), (0.50, 0.40), (1.0, 0.30)],
        # Rock: gradual build
        "rock_classic": [(0.0, 0.45), (0.40, 0.65), (0.70, 0.90), (1.0, 0.75)],
        "metal": [(0.0, 0.55), (0.30, 0.75), (0.70, 0.95), (1.0, 0.80)],
        "progressive_rock": [(0.0, 0.30), (0.40, 0.70), (0.70, 0.85), (1.0, 0.60)],
        # Jazz: undulation
        "jazz_ballad": [(0.0, 0.35), (0.40, 0.65), (0.70, 0.45), (1.0, 0.40)],
        "jazz_bebop": [(0.0, 0.55), (0.50, 0.80), (1.0, 0.60)],
        "jazz_modal": [(0.0, 0.40), (0.50, 0.60), (1.0, 0.40)],
        # Pop
        "pop_mainstream": [(0.0, 0.40), (0.50, 0.80), (0.80, 0.95), (1.0, 0.60)],
        "j_pop": [(0.0, 0.35), (0.50, 0.80), (0.80, 0.90), (1.0, 0.55)],
        # Other
        "funk_classic": [(0.0, 0.55), (0.50, 0.75), (1.0, 0.65)],
        "blues_chicago": [(0.0, 0.40), (0.50, 0.65), (1.0, 0.50)],
        "country_traditional": [(0.0, 0.40), (0.50, 0.65), (1.0, 0.50)],
        "acoustic_folk": [(0.0, 0.35), (0.50, 0.55), (1.0, 0.40)],
        "world_celtic": [(0.0, 0.40), (0.50, 0.65), (1.0, 0.45)],
        "latin_bossa_nova": [(0.0, 0.45), (0.50, 0.55), (1.0, 0.45)],
        "reggae": [(0.0, 0.50), (0.50, 0.55), (1.0, 0.50)],
        "rnb_neo_soul": [(0.0, 0.40), (0.50, 0.65), (1.0, 0.50)],
        "game_8bit_chiptune": [(0.0, 0.50), (0.50, 0.75), (1.0, 0.55)],
    }

    def _build_trajectory(
        self,
        total_bars: int,
        description: str,
        genre: str = "",
    ) -> TrajectorySpec:
        """Build a trajectory from the description, with genre-aware defaults."""
        desc_lower = description.lower()
        peak_bar = total_bars * 2 // 3

        # Explicit user intent overrides genre defaults
        if any(w in desc_lower for w in ("build", "crescendo", "rising")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=total_bars, value=0.9),
            ]
        elif any(w in desc_lower for w in ("calm", "peaceful", "gentle", "穏やか", "安らぎ", "静か", "癒し")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=total_bars // 2, value=0.35),
                Waypoint(bar=total_bars, value=0.2),
            ]
        elif any(w in desc_lower for w in ("dramatic", "intense", "climax", "壮大", "ドラマチック", "激しい", "壮厳")):
            waypoints = [
                Waypoint(bar=0, value=0.2),
                Waypoint(bar=peak_bar, value=0.95),
                Waypoint(bar=total_bars, value=0.15),
            ]
        else:
            # Genre-aware default
            shape = self._GENRE_TRAJECTORY_SHAPES.get(genre)
            if shape:
                waypoints = [Waypoint(bar=int(rel * total_bars), value=val) for rel, val in shape]
            else:
                waypoints = [
                    Waypoint(bar=0, value=0.3),
                    Waypoint(bar=peak_bar, value=0.7),
                    Waypoint(bar=total_bars, value=0.25),
                ]

        return TrajectorySpec(
            tension=TrajectoryDimension(type="linear", waypoints=waypoints),
        )
