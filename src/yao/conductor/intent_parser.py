"""IntentParser — multi-dimensional intent parsing from natural language.

Converts natural-language descriptions into a StructuredIntent with
emotional dimensions, genre candidates, and compositional hints.
Uses a rule-based keyword extraction approach.

See PROJECT.md §11.3 and IMPROVEMENT.md §4.6.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredIntent:
    """Multi-dimensional emotional and stylistic vector from text.

    All emotional dimensions are populated by the parser. The Conductor
    uses this to build a CompositionSpec via IntentToSpec.

    Attributes:
        valence: Emotional brightness (-1.0=sad to +1.0=joyful).
        arousal: Energy level (0.0=calm to 1.0=excited).
        tension: Harmonic/structural tension (0.0=relaxed to 1.0=tense).
        warmth: Timbral warmth (-1.0=cold to +1.0=warm).
        nostalgia: Nostalgic quality (0.0=none to 1.0=strong).
        genre_candidates: Ranked (genre, confidence) pairs.
        use_case: Primary use case tag.
        duration_seconds: Target duration.
        loopable: Whether the piece should loop.
        instruments_mentioned: Instruments explicitly named.
        tempo_hint: Tempo descriptor or None.
        mood_keywords: Extracted mood-related keywords.
        raw_description: Original text.
    """

    valence: float
    arousal: float
    tension: float
    warmth: float
    nostalgia: float
    genre_candidates: list[tuple[str, float]]
    use_case: str
    duration_seconds: float
    loopable: bool
    instruments_mentioned: list[str]
    tempo_hint: str | None
    mood_keywords: list[str]
    raw_description: str


# ---------------------------------------------------------------------------
# Keyword → dimension mappings
# ---------------------------------------------------------------------------

_VALENCE_POSITIVE = {
    "happy",
    "joyful",
    "bright",
    "uplifting",
    "cheerful",
    "optimistic",
    "hopeful",
    "playful",
    "celebratory",
    "triumphant",
    "warm",
    "light",
    "sunny",
    "lively",
    "exuberant",
    "radiant",
}
_VALENCE_NEGATIVE = {
    "sad",
    "melancholy",
    "dark",
    "gloomy",
    "somber",
    "tragic",
    "mournful",
    "sorrowful",
    "bleak",
    "desolate",
    "lonely",
    "grief",
    "depressing",
    "pensive",
    "bittersweet",
    "wistful",
}

_AROUSAL_HIGH = {
    "energetic",
    "fast",
    "intense",
    "driving",
    "aggressive",
    "powerful",
    "furious",
    "explosive",
    "frantic",
    "wild",
    "epic",
    "fierce",
    "upbeat",
    "exciting",
    "dynamic",
    "lively",
}
_AROUSAL_LOW = {
    "calm",
    "peaceful",
    "gentle",
    "soft",
    "quiet",
    "relaxing",
    "serene",
    "tranquil",
    "meditative",
    "ambient",
    "floating",
    "dreamy",
    "still",
    "slow",
    "languid",
    "hushed",
}

_TENSION_HIGH = {
    "tense",
    "suspenseful",
    "dramatic",
    "ominous",
    "foreboding",
    "anxious",
    "unsettling",
    "dissonant",
    "chaotic",
    "menacing",
    "eerie",
    "mysterious",
    "dark",
    "intense",
    "brooding",
}
_TENSION_LOW = {
    "relaxed",
    "peaceful",
    "resolved",
    "comforting",
    "soothing",
    "simple",
    "clear",
    "consonant",
    "stable",
    "grounded",
}

_WARMTH_POSITIVE = {
    "warm",
    "cozy",
    "intimate",
    "soft",
    "gentle",
    "tender",
    "acoustic",
    "organic",
    "earthy",
    "woody",
    "rich",
    "full",
}
_WARMTH_NEGATIVE = {
    "cold",
    "icy",
    "sterile",
    "metallic",
    "digital",
    "synthetic",
    "harsh",
    "clinical",
    "mechanical",
    "crystalline",
}

_NOSTALGIA = {
    "nostalgic",
    "retro",
    "vintage",
    "old",
    "classic",
    "reminiscent",
    "memory",
    "childhood",
    "past",
    "bittersweet",
    "longing",
    "wistful",
}

# Genre keyword mapping
_GENRE_KEYWORDS: dict[str, list[str]] = {
    "bebop_jazz": ["jazz", "bebop", "bop", "swing", "improvisation"],
    "j_pop_ballad": ["jpop", "j-pop", "japanese", "ballad", "anime"],
    "classical_romantic": ["classical", "romantic", "orchestral", "symphony", "concerto"],
    "lofi_hiphop": ["lofi", "lo-fi", "chillhop", "study", "chill", "beats"],
    "rock_classic": ["rock", "guitar", "riff", "classic rock"],
    "blues": ["blues", "bluesy", "12-bar"],
    "electronic_ambient": ["ambient", "atmospheric", "drone", "soundscape"],
    "electronic_house": ["house", "dance", "edm", "club", "techno"],
    "folk_traditional": ["folk", "acoustic", "traditional", "singer-songwriter"],
    "country": ["country", "nashville", "twang", "honky-tonk"],
    "funk": ["funk", "funky", "groove", "slap"],
    "reggae": ["reggae", "ska", "dub", "island"],
    "latin_bossa": ["bossa", "bossa nova", "brazilian"],
    "latin_salsa": ["salsa", "latin", "mambo", "son"],
    "soul_rnb": ["soul", "r&b", "rnb", "motown"],
    "gospel": ["gospel", "spiritual", "church"],
    "cinematic": ["cinematic", "film", "movie", "soundtrack", "score", "epic"],
    "metal_traditional": ["metal", "heavy", "shred"],
    "celtic": ["celtic", "irish", "scottish"],
    "jazz_modal": ["modal", "miles davis", "kind of blue"],
}

# Use-case keywords
_USE_CASE_KEYWORDS: dict[str, list[str]] = {
    "bgm": ["background", "bgm", "studying", "study", "working", "reading", "focus"],
    "foreground": ["performance", "concert", "live", "main", "feature"],
    "meditation": ["meditation", "yoga", "mindfulness", "breathing", "zen"],
    "workout": ["workout", "exercise", "gym", "running", "training"],
    "game": ["game", "gaming", "video game", "puzzle", "rpg", "boss"],
    "film": ["film", "movie", "scene", "trailer", "cinematic"],
    "sleep": ["sleep", "lullaby", "bedtime", "dreaming"],
    "party": ["party", "celebration", "dance", "club"],
}

# Tempo keywords
_TEMPO_KEYWORDS: dict[str, list[str]] = {
    "very_slow": ["very slow", "adagio", "largo", "grave"],
    "slow": ["slow", "andante", "walking"],
    "medium": ["medium", "moderate", "moderato"],
    "fast": ["fast", "allegro", "upbeat", "quick"],
    "very_fast": ["very fast", "presto", "vivace", "frantic"],
}

# Instrument keywords
_INSTRUMENT_KEYWORDS: dict[str, list[str]] = {
    "piano": ["piano", "keys", "keyboard"],
    "guitar": ["guitar", "acoustic guitar", "electric guitar"],
    "drums": ["drums", "percussion", "beat"],
    "bass": ["bass", "bass guitar", "upright bass"],
    "strings": ["strings", "violin", "viola", "cello", "orchestra"],
    "synthesizer": ["synth", "synthesizer", "electronic"],
    "saxophone": ["sax", "saxophone"],
    "trumpet": ["trumpet", "brass", "horn"],
    "flute": ["flute", "woodwind"],
    "voice": ["voice", "vocal", "singing", "choir"],
}

# Mode mapping: emotional vector → recommended mode
_MODE_MAP: list[tuple[str, float, float, float]] = [
    # (mode_name, valence_center, warmth_center, nostalgia_center)
    ("major", 0.6, 0.3, 0.0),
    ("natural_minor", -0.3, 0.0, 0.3),
    ("dorian", -0.1, 0.4, 0.5),
    ("mixolydian", 0.4, 0.5, 0.2),
    ("pentatonic_major", 0.5, 0.6, 0.3),
    ("pentatonic_minor", -0.2, 0.2, 0.4),
    ("blues", -0.1, 0.3, 0.4),
    ("harmonic_minor", -0.4, -0.2, 0.2),
    ("melodic_minor", -0.2, 0.1, 0.1),
    ("phrygian", -0.5, -0.3, 0.1),
    ("lydian", 0.7, 0.2, 0.0),
    ("locrian", -0.8, -0.5, 0.0),
    ("whole_tone", 0.0, -0.2, 0.0),
    ("chromatic", 0.0, -0.4, 0.0),
]


class IntentParser:
    """Parses natural-language descriptions into StructuredIntent.

    Uses rule-based keyword extraction for all dimensions.
    The parser populates all 5 emotional dimensions, genre candidates,
    use case, duration, instruments, tempo, and mood keywords.
    """

    def parse(self, description: str) -> StructuredIntent:
        """Parse a natural-language description into a StructuredIntent.

        Args:
            description: Free-form text describing the desired music.

        Returns:
            A fully-populated StructuredIntent.
        """
        lower = description.lower()
        words = set(re.findall(r"[a-z]+", lower))

        valence = self._score_dimension(words, _VALENCE_POSITIVE, _VALENCE_NEGATIVE)
        arousal = self._score_unipolar(words, _AROUSAL_HIGH, _AROUSAL_LOW)
        tension = self._score_unipolar(words, _TENSION_HIGH, _TENSION_LOW)
        warmth = self._score_dimension(words, _WARMTH_POSITIVE, _WARMTH_NEGATIVE)
        nostalgia = self._score_unipolar(words, _NOSTALGIA, set())

        genre_candidates = self._detect_genres(lower)
        use_case = self._detect_use_case(lower)
        duration = self._detect_duration(lower)
        loopable = self._detect_loopable(lower)
        instruments = self._detect_instruments(lower)
        tempo = self._detect_tempo(lower)
        mood_keywords = self._extract_mood_keywords(words)

        return StructuredIntent(
            valence=valence,
            arousal=arousal,
            tension=tension,
            warmth=warmth,
            nostalgia=nostalgia,
            genre_candidates=genre_candidates,
            use_case=use_case,
            duration_seconds=duration,
            loopable=loopable,
            instruments_mentioned=instruments,
            tempo_hint=tempo,
            mood_keywords=mood_keywords,
            raw_description=description,
        )

    def select_mode(self, intent: StructuredIntent) -> str:
        """Select the best musical mode for an intent.

        Maps the emotional vector to the closest mode using
        Euclidean distance in (valence, warmth, nostalgia) space.

        Args:
            intent: The parsed StructuredIntent.

        Returns:
            Mode name (e.g., "dorian", "major", "pentatonic_minor").
        """
        best_mode = "major"
        best_dist = float("inf")

        for mode_name, v_center, w_center, n_center in _MODE_MAP:
            dist = (
                (intent.valence - v_center) ** 2 + (intent.warmth - w_center) ** 2 + (intent.nostalgia - n_center) ** 2
            )
            if dist < best_dist:
                best_dist = dist
                best_mode = mode_name

        return best_mode

    def _score_dimension(
        self,
        words: set[str],
        positive: set[str],
        negative: set[str],
    ) -> float:
        """Score a bipolar dimension (-1 to +1)."""
        pos = len(words & positive)
        neg = len(words & negative)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def _score_unipolar(
        self,
        words: set[str],
        high: set[str],
        low: set[str],
    ) -> float:
        """Score a unipolar dimension (0 to 1)."""
        hi = len(words & high)
        lo = len(words & low)
        total = hi + lo
        if total == 0:
            return 0.5
        return hi / total

    def _detect_genres(self, text: str) -> list[tuple[str, float]]:
        """Detect genre candidates from text."""
        scores: dict[str, float] = {}
        for genre, keywords in _GENRE_KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw in text)
            if match_count > 0:
                scores[genre] = min(1.0, match_count * 0.4)

        if not scores:
            scores["lofi_hiphop"] = 0.3  # default fallback

        sorted_genres = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_genres[:3]

    def _detect_use_case(self, text: str) -> str:
        """Detect use case from text."""
        for use_case, keywords in _USE_CASE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return use_case
        return "bgm"

    def _detect_duration(self, text: str) -> float:
        """Extract duration hints from text."""
        # Look for explicit duration mentions
        match = re.search(r"(\d+)\s*(?:second|sec|s)\b", text)
        if match:
            return float(match.group(1))
        match = re.search(r"(\d+)\s*(?:minute|min|m)\b", text)
        if match:
            return float(match.group(1)) * 60
        # Default durations by use case
        if "short" in text or "brief" in text:
            return 30.0
        if "long" in text or "extended" in text:
            return 180.0
        return 90.0

    def _detect_loopable(self, text: str) -> bool:
        """Detect if the piece should loop."""
        loop_keywords = {"loop", "looping", "loopable", "repeat", "seamless", "bgm", "background"}
        return any(kw in text.lower() for kw in loop_keywords)

    def _detect_instruments(self, text: str) -> list[str]:
        """Detect mentioned instruments."""
        instruments: list[str] = []
        for inst, keywords in _INSTRUMENT_KEYWORDS.items():
            if any(kw in text.lower() for kw in keywords):
                instruments.append(inst)
        return instruments

    def _detect_tempo(self, text: str) -> str | None:
        """Detect tempo hints."""
        # Check for BPM
        match = re.search(r"(\d+)\s*bpm", text.lower())
        if match:
            bpm = int(match.group(1))
            if bpm < 70:  # noqa: PLR2004
                return "slow"
            if bpm < 110:  # noqa: PLR2004
                return "medium"
            if bpm < 140:  # noqa: PLR2004
                return "fast"
            return "very_fast"

        for tempo, keywords in _TEMPO_KEYWORDS.items():
            if any(kw in text.lower() for kw in keywords):
                return tempo
        return None

    def _extract_mood_keywords(self, words: set[str]) -> list[str]:
        """Extract mood-related keywords."""
        all_mood = (
            _VALENCE_POSITIVE
            | _VALENCE_NEGATIVE
            | _AROUSAL_HIGH
            | _AROUSAL_LOW
            | _TENSION_HIGH
            | _TENSION_LOW
            | _WARMTH_POSITIVE
            | _WARMTH_NEGATIVE
            | _NOSTALGIA
        )
        return sorted(words & all_mood)
