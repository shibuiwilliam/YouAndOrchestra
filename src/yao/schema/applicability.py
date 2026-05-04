"""Spec field applicability registry.

Maps every user-settable spec field to its implementation status:
Applied, Partial, or Ignored. This powers the three-part report in
``yao validate`` and the pre-flight warnings in ``yao compose`` /
``yao conduct``.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from yao.schema.composition import CompositionSpec
from yao.schema.composition_v2 import CompositionSpecV2


class FieldStatus(StrEnum):
    """Implementation status of a spec field."""

    APPLIED = "applied"
    PARTIAL = "partial"
    IGNORED = "ignored"


@dataclass(frozen=True)
class FieldApplicability:
    """Applicability record for a single spec field.

    Attributes:
        field: Dotted field path (e.g. "production.target_lufs").
        status: Whether the field is applied, partial, or ignored.
        description: Human-readable explanation.
        consumers: Which modules consume this field.
    """

    field: str
    status: FieldStatus
    description: str
    consumers: str = ""


# ── Registry ──────────────────────────────────────────────────────────────

_REGISTRY: dict[str, FieldApplicability] = {}


def _reg(field: str, status: FieldStatus, desc: str, consumers: str = "") -> None:
    """Register a field applicability entry."""
    _REGISTRY[field] = FieldApplicability(
        field=field,
        status=status,
        description=desc,
        consumers=consumers,
    )


# ── v1 + v2 shared fields ────────────────────────────────────────────────

# Identity / top-level
_reg("title", FieldStatus.APPLIED, "Used in output filenames and reports", "all")
_reg("genre", FieldStatus.APPLIED, "Drives GenreProfile selection for generators", "generators, drum_patterner")
_reg("key", FieldStatus.APPLIED, "Sets scale for all note generation", "all generators")
_reg("tempo_bpm", FieldStatus.APPLIED, "Sets MIDI tempo and beat timing", "MIDI writer, all generators")
_reg("time_signature", FieldStatus.APPLIED, "Sets beats per bar", "all generators, MIDI writer")

# Generation
_reg("generation.strategy", FieldStatus.APPLIED, "Selects generator (rule_based, stochastic, etc.)", "registry")
_reg("generation.seed", FieldStatus.APPLIED, "Deterministic seed for reproducibility", "stochastic generators")
_reg("generation.temperature", FieldStatus.APPLIED, "Controls stochastic variation", "stochastic generators")

# Sections
_reg("sections", FieldStatus.APPLIED, "Section structure (name, bars, dynamics)", "plan orchestrator, all generators")

# Instruments
_reg("instruments", FieldStatus.APPLIED, "Instrument list with roles", "note realizers, MIDI writer")

# Drums
_reg("drums.pattern_family", FieldStatus.APPLIED, "Selects drum pattern YAML", "drum_patterner")
_reg("drums.swing", FieldStatus.APPLIED, "Drum swing amount", "drum_patterner")
_reg("drums.ghost_notes_density", FieldStatus.APPLIED, "Ghost note probability", "drum_patterner")
_reg("drums.fills_at", FieldStatus.PARTIAL, "Fill placement points", "drum_patterner (section names matched)")

# ── v2-only fields ────────────────────────────────────────────────────────

# Emotion
_reg("emotion.valence", FieldStatus.PARTIAL, "Mapped to key mode heuristic", "spec compiler")
_reg("emotion.energy", FieldStatus.PARTIAL, "Mapped to tempo/density heuristic", "spec compiler")
_reg("emotion.tension", FieldStatus.PARTIAL, "Mapped to trajectory tension curve", "spec compiler")
_reg("emotion.warmth", FieldStatus.IGNORED, "No warmth-specific feature yet", "")
_reg("emotion.nostalgia", FieldStatus.IGNORED, "Mapped to valence heuristic only", "")

# Melody
_reg("melody.range", FieldStatus.APPLIED, "Constrains note pitch range", "note realizers")
_reg("melody.contour", FieldStatus.APPLIED, "Selects contour algorithm", "stochastic generator")
_reg("melody.motif.length_beats", FieldStatus.APPLIED, "Motif seed length", "motif extraction")
_reg("melody.motif.repetition_rate", FieldStatus.APPLIED, "Motif recurrence frequency", "motif placement")
_reg(
    "melody.motif.variation_rate",
    FieldStatus.PARTIAL,
    "Controls motif transforms",
    "motif placement (limited)",
)
_reg("melody.intervals.stepwise_ratio", FieldStatus.APPLIED, "Target stepwise motion ratio", "stochastic generator")
_reg("melody.intervals.max_leap", FieldStatus.PARTIAL, "Maximum melodic leap", "stochastic generator (soft constraint)")
_reg("melody.phrase.bars_per_phrase", FieldStatus.APPLIED, "Phrase structure length", "plan orchestrator")
_reg("melody.phrase.call_response", FieldStatus.IGNORED, "Call-response pattern not yet implemented", "")

# Harmony
_reg("harmony.complexity", FieldStatus.APPLIED, "Chord palette richness", "harmony planner")
_reg("harmony.chord_palette", FieldStatus.APPLIED, "Allowed chord functions", "harmony planner")
_reg("harmony.cadence", FieldStatus.APPLIED, "Section-end cadence types", "harmony planner")
_reg("harmony.harmonic_rhythm", FieldStatus.PARTIAL, "Chords-per-bar pacing", "harmony planner (section-level only)")

# Rhythm
_reg("rhythm.groove", FieldStatus.APPLIED, "Groove type (straight, swing)", "groove applicator")
_reg("rhythm.swing", FieldStatus.APPLIED, "Swing amount for all instruments", "groove applicator, drum_patterner")
_reg("rhythm.syncopation", FieldStatus.PARTIAL, "Target syncopation ratio", "stochastic generator (approximate)")

# Arrangement
_reg("arrangement.instruments", FieldStatus.APPLIED, "Per-instrument role and voicing", "note realizers")
_reg("arrangement.counter_melody", FieldStatus.APPLIED, "Counter-melody configuration", "counter_melody generator")

# Production
_reg("production.target_lufs", FieldStatus.APPLIED, "Loudness normalization target", "mix chain, playback")
_reg("production.stereo_width", FieldStatus.APPLIED, "Stereo width processing", "mix chain")
_reg("production.reverb_amount", FieldStatus.APPLIED, "Global reverb send level", "mix chain")
_reg("production.vocal_space_reserved", FieldStatus.IGNORED, "No vocal space carving yet", "")
_reg("production.use_case", FieldStatus.PARTIAL, "Used for evaluation thresholds", "evaluator (limited)")
_reg("production.tape_saturation", FieldStatus.IGNORED, "Saturation effect not implemented", "")
_reg("production.master_eq", FieldStatus.IGNORED, "Master EQ not implemented in mix chain MVP", "")

# Constraints
_reg(
    "constraints",
    FieldStatus.PARTIAL,
    "Declarative constraint rules",
    "constraint checker (must/must_not; prefer/avoid advisory)",
)


# ── Public API ────────────────────────────────────────────────────────────


def get_registry() -> dict[str, FieldApplicability]:
    """Return the full applicability registry.

    Returns:
        Dict mapping field paths to FieldApplicability records.
    """
    return dict(_REGISTRY)


def get_field_status(field: str) -> FieldApplicability | None:
    """Look up the applicability of a single field.

    Args:
        field: Dotted field path.

    Returns:
        FieldApplicability or None if not registered.
    """
    return _REGISTRY.get(field)


def lint_spec_applicability(
    spec: CompositionSpec | CompositionSpecV2,
) -> list[FieldApplicability]:
    """Check a spec for fields that are ignored or partial.

    Returns only fields that are set to non-default values AND are
    marked as Ignored or Partial — these are the ones users should
    be warned about.

    Args:
        spec: A v1 or v2 composition spec.

    Returns:
        List of FieldApplicability records for problematic fields.
    """
    warnings: list[FieldApplicability] = []

    for entry in _REGISTRY.values():
        if entry.status == FieldStatus.APPLIED:
            continue
        # Check if this field is actually set in the spec
        if _field_is_set(spec, entry.field):
            warnings.append(entry)

    return warnings


def format_applicability_report(
    spec: CompositionSpec | CompositionSpecV2,
) -> str:
    """Format a three-part applicability report for display.

    Args:
        spec: A v1 or v2 composition spec.

    Returns:
        Formatted multi-line report string.
    """
    applied: list[str] = []
    partial: list[str] = []
    ignored: list[str] = []

    for entry in _REGISTRY.values():
        if not _field_is_set(spec, entry.field):
            continue

        line = f"  {entry.field}: {entry.description}"
        if entry.consumers:
            line += f" [{entry.consumers}]"

        if entry.status == FieldStatus.APPLIED:
            applied.append(line)
        elif entry.status == FieldStatus.PARTIAL:
            partial.append(line)
        else:
            ignored.append(line)

    parts: list[str] = []
    if applied:
        parts.append("Applied:")
        parts.extend(applied)
    if partial:
        parts.append("\nPartially applied:")
        parts.extend(partial)
    if ignored:
        parts.append("\nNot yet honored (will be ignored):")
        parts.extend(ignored)

    return "\n".join(parts) if parts else "No fields set."


def _field_is_set(spec: CompositionSpec | CompositionSpecV2, field: str) -> bool:
    """Check if a dotted field path has a non-None value in the spec.

    Args:
        spec: The spec to check.
        field: Dotted path like "production.target_lufs".

    Returns:
        True if the field exists and is not None.
    """
    parts = field.split(".")
    obj: object = spec

    for part in parts:
        # Handle v2 field aliases
        attr = "global_" if part == "global" else part
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
        elif isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return False

        if obj is None:
            return False

    return True
