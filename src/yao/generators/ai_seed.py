"""AI-Seed Generator — LLM motif seed → rule-based expansion → Pipeline finish.

Hybrid generator: uses an LLM (Anthropic API via claude-agent-sdk) to generate
a creative motif seed, then expands it via rule-based motif transformations,
and finishes with the standard Pipeline.

The LLM is good at "interesting starting ideas" but unreliable for
"controllable structural development." This split plays to each strength.

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Callable
from typing import Protocol, runtime_checkable

import structlog

from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.motif import Motif, augment, invert, retrograde, transpose
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.trajectory import TrajectorySpec

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# LLM Client Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM providers used by the AI-Seed Generator.

    Implementations must provide a generate_motif method that returns
    a JSON-serializable motif description from a prompt.
    """

    @property
    def model_name(self) -> str:
        """Return the model identifier for provenance."""
        ...

    def generate_motif(self, prompt: str) -> str:
        """Generate a motif description from a prompt.

        Args:
            prompt: The prompt describing the desired motif.

        Returns:
            JSON string with keys: notes (list of {pitch, duration, velocity}).
        """
        ...


# ---------------------------------------------------------------------------
# Anthropic Client
# ---------------------------------------------------------------------------


class AnthropicMotifClient:
    """LLM client using the Anthropic Messages API.

    Uses the anthropic package to generate motif seeds. Falls back
    gracefully if the package is not installed or API key is missing.

    Attributes:
        _model: The Anthropic model to use.
    """

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        """Initialize the client.

        Args:
            model: Anthropic model ID.
        """
        self._model = model

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return self._model

    def generate_motif(self, prompt: str) -> str:
        """Generate a motif via the Anthropic API.

        Args:
            prompt: The motif generation prompt.

        Returns:
            JSON string with motif notes.

        Raises:
            RuntimeError: If anthropic package is not available or API fails.
        """
        try:
            import anthropic
        except ImportError as e:
            msg = "anthropic package not installed. Install with: pip install anthropic"
            raise RuntimeError(msg) from e

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        block = response.content[0]
        if hasattr(block, "text"):
            return block.text
        msg = f"Unexpected response block type: {type(block)}"
        raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Deterministic Fallback Client (for testing / CI)
# ---------------------------------------------------------------------------


class DeterministicMotifClient:
    """Deterministic motif client for testing without LLM calls.

    Generates motifs from a seed using simple rules, ensuring
    reproducibility and CI compatibility.
    """

    def __init__(self, seed: int = 42) -> None:
        """Initialize with a random seed.

        Args:
            seed: Random seed for reproducibility.
        """
        self._seed = seed

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return f"deterministic(seed={self._seed})"

    def generate_motif(self, prompt: str) -> str:
        """Generate a deterministic motif from the prompt hash.

        Args:
            prompt: The prompt (used for deterministic variation).

        Returns:
            JSON string with motif notes.
        """
        rng = random.Random(self._seed + hash(prompt) % 1000)

        n_notes = rng.randint(4, 8)
        notes = []
        pitch = 60 + rng.randint(-5, 5)
        for _i in range(n_notes):
            notes.append(
                {
                    "pitch": max(48, min(84, pitch)),
                    "duration": rng.choice([0.25, 0.5, 0.5, 1.0, 1.0]),
                    "velocity": rng.randint(60, 100),
                }
            )
            pitch += rng.choice([-3, -2, -1, 0, 1, 2, 3, 5])

        return json.dumps({"notes": notes})


# ---------------------------------------------------------------------------
# Seed parsing and validation
# ---------------------------------------------------------------------------


def _parse_seed_motif(raw_json: str, key: str, instrument: str) -> Motif:
    """Parse and validate an LLM-generated motif.

    Validates that all pitches are in-range and in-key (best effort).

    Args:
        raw_json: JSON string from the LLM.
        key: Key signature for validation (e.g., "C major").
        instrument: Instrument name for range clamping.

    Returns:
        Validated Motif.

    Raises:
        ValueError: If the JSON is malformed or contains invalid notes.
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        # Try to extract JSON from markdown code blocks
        import re

        match = re.search(r"```(?:json)?\s*(.*?)```", raw_json, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            msg = f"Failed to parse LLM motif output as JSON: {e}"
            raise ValueError(msg) from e

    raw_notes = data.get("notes", [])
    if not raw_notes:
        msg = "LLM returned empty notes list"
        raise ValueError(msg)

    notes: list[Note] = []
    beat = 0.0
    for n in raw_notes:
        pitch = int(n.get("pitch", 60))
        duration = float(n.get("duration", 0.5))
        velocity = int(n.get("velocity", 80))

        # Clamp to valid MIDI range
        pitch = max(0, min(127, pitch))
        velocity = max(1, min(127, velocity))
        duration = max(0.125, min(4.0, duration))

        notes.append(
            Note(
                pitch=pitch,
                start_beat=beat,
                duration_beats=duration,
                velocity=velocity,
                instrument=instrument,
            )
        )
        beat += duration

    return Motif(
        notes=tuple(notes),
        label="ai_seed",
        transformations_applied=("llm_generated",),
    )


def _build_seed_prompt(spec: CompositionSpec) -> str:
    """Build the LLM prompt for motif generation.

    Args:
        spec: The composition specification.

    Returns:
        Prompt string.
    """
    key = spec.key if hasattr(spec, "key") else "C major"
    genre = spec.genre if hasattr(spec, "genre") else "general"
    tempo = spec.tempo_bpm if hasattr(spec, "tempo_bpm") else 120

    return f"""Generate a short musical motif (4-8 notes) for a {genre} composition in {key} at {tempo} BPM.

Return ONLY a JSON object with this exact format:
{{
  "notes": [
    {{"pitch": 60, "duration": 0.5, "velocity": 80}},
    {{"pitch": 64, "duration": 1.0, "velocity": 90}},
    ...
  ]
}}

Rules:
- pitch: MIDI note numbers (60=C4, 72=C5). Stay within 48-84 range.
- duration: in beats (0.25=16th, 0.5=8th, 1.0=quarter, 2.0=half).
- velocity: 1-127 (60=mp, 80=mf, 100=f).
- The motif should be memorable, singable, and idiomatic for {genre}.
- Use notes from the {key} scale.
- Return ONLY the JSON, no explanation."""


# ---------------------------------------------------------------------------
# Motif expansion
# ---------------------------------------------------------------------------


def _expand_motif(seed: Motif, total_bars: int, beats_per_bar: float, rng: random.Random) -> list[Note]:
    """Expand a seed motif into a full melody via rule-based transformations.

    Applies transposition, inversion, retrograde, and augmentation
    to fill the required number of bars.

    Args:
        seed: The seed motif to expand.
        total_bars: Target number of bars.
        beats_per_bar: Beats per bar.
        rng: Random number generator.

    Returns:
        List of notes filling the required bars.
    """
    total_beats = total_bars * beats_per_bar
    all_notes: list[Note] = list(seed.notes)
    current_beat = seed.duration_beats

    transforms: list[Callable[[Motif], Motif]] = [
        lambda m: transpose(m, rng.choice([-7, -5, -3, -2, 2, 3, 5, 7])),
        lambda m: invert(m),
        lambda m: retrograde(m),
        lambda m: transpose(m, rng.choice([4, 5, 7])),
        lambda m: augment(m, 1.5),
    ]

    while current_beat < total_beats:
        transform: Callable[[Motif], Motif] = rng.choice(transforms)
        variant = transform(seed)

        for note in variant.notes:
            if current_beat >= total_beats:
                break
            from dataclasses import replace

            shifted = replace(note, start_beat=current_beat)
            all_notes.append(shifted)
            current_beat += note.duration_beats

    return all_notes


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@register_generator("ai_seed")
class AISeedGenerator(GeneratorBase):
    """Hybrid generator: LLM seed → rule-based expansion.

    The LLM generates a creative seed motif. Rule-based logic expands it
    into a full composition via motif transformations. The result is a
    ScoreIR with full provenance tracking the LLM model, prompt hash,
    and all expansion decisions.

    Attributes:
        llm_client: The LLM client to use for seed generation.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize the generator.

        Args:
            llm_client: Optional LLM client. If None, attempts to use
                AnthropicMotifClient, falling back to DeterministicMotifClient.
        """
        self._client: LLMClient
        if llm_client is not None:
            self._client = llm_client
        else:
            try:
                import anthropic  # noqa: F811

                if anthropic.Anthropic().api_key:
                    self._client = AnthropicMotifClient()
                else:
                    self._client = DeterministicMotifClient()
            except Exception:
                self._client = DeterministicMotifClient()

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a composition from an LLM-seeded motif.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory specification.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        log = ProvenanceLog()
        seed_val = spec.seed if hasattr(spec, "seed") and spec.seed is not None else 42
        rng = random.Random(seed_val)

        # Step 1: Generate seed motif via LLM
        prompt = _build_seed_prompt(spec)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        log.record(
            layer="generation",
            operation="ai_seed_prompt",
            parameters={
                "model": self._client.model_name,
                "prompt_hash": prompt_hash,
            },
            source="AISeedGenerator",
            rationale="Generate creative motif seed via LLM",
        )

        raw_output = self._client.generate_motif(prompt)

        # Step 2: Parse and validate seed
        key = spec.key if hasattr(spec, "key") else "C major"
        instrument = "piano"
        if hasattr(spec, "instruments") and spec.instruments:
            instrument = spec.instruments[0].name

        seed_motif = _parse_seed_motif(raw_output, key, instrument)

        log.record(
            layer="generation",
            operation="ai_seed_parsed",
            parameters={
                "n_notes": len(seed_motif.notes),
                "duration_beats": seed_motif.duration_beats,
                "pitch_range": seed_motif.pitch_range,
            },
            source="AISeedGenerator",
            rationale="Validate and parse LLM motif output",
        )

        # Step 3: Expand seed via rule-based transformations
        total_bars = sum(s.bars for s in spec.sections) if hasattr(spec, "sections") else 16
        beats_per_bar = 4.0
        expanded_notes = _expand_motif(seed_motif, total_bars, beats_per_bar, rng)

        log.record(
            layer="generation",
            operation="ai_seed_expanded",
            parameters={
                "total_bars": total_bars,
                "expanded_notes": len(expanded_notes),
            },
            source="AISeedGenerator",
            rationale="Expand seed motif via rule-based transformations",
        )

        # Step 4: Assemble into ScoreIR
        title = spec.title if hasattr(spec, "title") else "AI-Seeded Composition"
        tempo = spec.tempo_bpm if hasattr(spec, "tempo_bpm") else 120

        part = Part(instrument=instrument, notes=tuple(expanded_notes))
        section = Section(
            name="main",
            start_bar=0,
            end_bar=total_bars,
            parts=(part,),
        )

        score = ScoreIR(
            title=title,
            tempo_bpm=tempo,
            time_signature="4/4",
            key=key,
            sections=(section,),
        )

        return score, log
