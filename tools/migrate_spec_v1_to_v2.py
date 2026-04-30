#!/usr/bin/env python3
"""Migrate a composition.yaml v1 spec to a v2 draft.

This produces a DRAFT v2 spec that requires human review. Fields that
cannot be automatically determined are marked with TODO comments.

Usage:
    python tools/migrate_spec_v1_to_v2.py specs/projects/my-song/composition.yaml

Output:
    specs/projects/my-song/composition.yaml.v2-draft.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from yao.schema.composition import CompositionSpec  # noqa: E402


_V2_DRAFT_HEADER = """\
# ============================================================================
# YaO composition.yaml v2 DRAFT
#
# This file was auto-generated from a v1 spec by migrate_spec_v1_to_v2.py.
# It requires HUMAN REVIEW before use. Look for TODO comments.
#
# Fields marked TODO need manual values — the migration tool cannot infer them.
# ============================================================================

"""


def migrate_v1_to_v2(v1_spec: CompositionSpec) -> dict:
    """Convert a v1 CompositionSpec to a v2 dict (for YAML output).

    Args:
        v1_spec: Validated v1 spec.

    Returns:
        Dict representing the v2 spec structure.
    """
    v2: dict = {"version": "2"}

    # Identity
    v2["identity"] = {
        "title": v1_spec.title,
        "purpose": "TODO: describe the purpose of this piece",
        "duration_sec": _estimate_duration(v1_spec),
        "loopable": False,  # v1 has no loopable concept
    }

    # Global
    v2["global"] = {
        "key": v1_spec.key,
        "bpm": v1_spec.tempo_bpm,
        "time_signature": v1_spec.time_signature,
        "genre": v1_spec.genre,
    }

    # Emotion — cannot be inferred from v1
    v2["emotion"] = {
        "valence": "TODO: 0.0-1.0 (bright=1.0, dark=0.0)",
        "energy": "TODO: 0.0-1.0",
        "tension": "TODO: 0.0-1.0",
        "warmth": "TODO: 0.0-1.0",
        "nostalgia": "TODO: 0.0-1.0",
    }

    # Form
    sections = []
    for s in v1_spec.sections:
        section = {"id": s.name, "bars": s.bars, "density": "TODO: 0.0-1.0"}
        if s.dynamics:
            section["dynamics"] = s.dynamics
        sections.append(section)
    v2["form"] = {"sections": sections}

    # Melody — minimal defaults, needs human input
    v2["melody"] = {
        "range": {"min": "TODO: e.g. A3", "max": "TODO: e.g. E5"},
        "contour": "arch",
        "motif": {
            "length_beats": 2,
            "repetition_rate": 0.5,
            "variation_rate": 0.3,
        },
        "intervals": {"stepwise_ratio": 0.7, "max_leap": "P5"},
        "phrase": {"bars_per_phrase": 4, "call_response": False},
    }

    # Harmony — minimal defaults
    v2["harmony"] = {
        "complexity": "TODO: 0.0-1.0",
        "chord_palette": ["I", "IV", "V", "vi"],
        "cadence": {},
        "harmonic_rhythm": {},
    }

    # Rhythm
    v2["rhythm"] = {
        "groove": "straight",
        "swing": 0.0,
        "syncopation": "TODO: 0.0-1.0",
    }

    # Drums
    v2["drums"] = {
        "pattern_family": "basic",
        "swing": 0.0,
        "ghost_notes_density": 0.0,
        "fills_at": [],
    }

    # Arrangement — map from v1 instruments
    instruments = {}
    for inst in v1_spec.instruments:
        instruments[inst.name] = {"role": inst.role}
    v2["arrangement"] = {
        "instruments": instruments,
        "counter_melody": {"enabled_sections": []},
    }

    # Production
    v2["production"] = {
        "use_case": "general",
        "target_lufs": -14,
        "stereo_width": 0.8,
        "vocal_space_reserved": False,
    }

    # Constraints
    v2["constraints"] = []

    # Generation — carry over from v1
    v2["generation"] = {
        "strategy": v1_spec.generation.strategy,
    }
    if v1_spec.generation.seed is not None:
        v2["generation"]["seed"] = v1_spec.generation.seed
    v2["generation"]["temperature"] = v1_spec.generation.temperature

    return v2


def _estimate_duration(spec: CompositionSpec) -> float:
    """Estimate duration in seconds from v1 spec."""
    total_bars = spec.computed_total_bars()
    ts_parts = spec.time_signature.split("/")
    beats_per_bar = int(ts_parts[0]) if len(ts_parts) == 2 else 4  # noqa: PLR2004
    return (total_bars * beats_per_bar * 60.0) / spec.tempo_bpm


def main() -> int:
    """Main entry point."""
    if len(sys.argv) != 2:  # noqa: PLR2004
        print(f"Usage: {sys.argv[0]} <v1-spec.yaml>")
        return 1

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        return 1

    output_path = input_path.with_suffix(".yaml.v2-draft.yaml")

    try:
        v1_spec = CompositionSpec.from_yaml(input_path)
    except Exception as e:
        print(f"ERROR: Failed to load v1 spec: {e}")
        return 1

    v2_dict = migrate_v1_to_v2(v1_spec)

    yaml_str = yaml.dump(v2_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)

    with open(output_path, "w") as f:
        f.write(_V2_DRAFT_HEADER)
        f.write(yaml_str)

    print(f"V2 draft written to: {output_path}")
    print("Review TODO comments before using this spec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
