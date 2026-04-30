#!/usr/bin/env python3
"""Regenerate golden MIDI files.

Use ONLY when intentionally changing musical output. Every regeneration
must include a --reason explaining why the goldens changed, and the PR
must include an audio comparison of old vs new.

Usage:
    python tests/golden/tools/regenerate_goldens.py --reason "Brief description" --confirm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))

# Trigger registrations
import yao.generators.note.rule_based as _nrb  # noqa: F401, E402
import yao.generators.note.stochastic as _nst  # noqa: F401, E402
import yao.generators.rule_based as _rb  # noqa: F401, E402
import yao.generators.stochastic as _st  # noqa: F401, E402
from yao.generators.note.base import NOTE_REALIZERS  # noqa: E402
from yao.generators.plan.orchestrator import PlanOrchestrator  # noqa: E402
from yao.ir.trajectory import MultiDimensionalTrajectory  # noqa: E402
from yao.reflect.provenance import ProvenanceLog  # noqa: E402
from yao.render.midi_writer import write_midi  # noqa: E402
from yao.schema.composition_v2 import CompositionSpecV2  # noqa: E402
from yao.schema.intent import IntentSpec  # noqa: E402

INPUTS_DIR = Path(__file__).resolve().parent.parent / "inputs"
EXPECTED_DIR = Path(__file__).resolve().parent.parent / "expected"

# The golden test matrix. Each entry: (spec_filename, seed, realizer_name).
# Adding or removing entries requires PR review.
GOLDEN_MATRIX: list[tuple[str, int, str]] = [
    ("minimal_v2.yaml", 42, "rule_based"),
    ("minimal_v2.yaml", 42, "stochastic"),
    ("pop_basic.yaml", 42, "rule_based"),
    ("pop_basic.yaml", 42, "stochastic"),
    ("cinematic_basic.yaml", 42, "rule_based"),
    ("cinematic_basic.yaml", 42, "stochastic"),
]


def golden_filename(spec_name: str, seed: int, realizer: str) -> str:
    """Compute the expected golden filename."""
    base = spec_name.replace(".yaml", "")
    return f"{base}_seed{seed}_{realizer}.mid"


def generate_one(spec_name: str, seed: int, realizer: str) -> Path:
    """Generate a single golden MIDI file.

    Args:
        spec_name: Spec filename in inputs/.
        seed: Random seed.
        realizer: Note realizer name.

    Returns:
        Path to the generated MIDI file.
    """
    spec_path = INPUTS_DIR / spec_name
    spec = CompositionSpecV2.from_yaml(spec_path)
    traj = MultiDimensionalTrajectory.default()
    intent = IntentSpec(text="golden test", keywords=[])
    prov = ProvenanceLog()

    plan = PlanOrchestrator(plan_strategy="rule_based").build_plan(
        spec, traj, intent, prov,
    )

    note_realizer = NOTE_REALIZERS[realizer]()
    score = note_realizer.realize(plan, seed=seed, temperature=0.5, provenance=prov)

    out_path = EXPECTED_DIR / golden_filename(spec_name, seed, realizer)
    write_midi(score, out_path)
    return out_path


def regenerate(reason: str) -> None:
    """Regenerate ALL golden MIDI files.

    Args:
        reason: Why the goldens are being regenerated.
    """
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Regenerating {len(GOLDEN_MATRIX)} goldens...")
    print(f"Reason: {reason}")
    print()

    for spec_name, seed, realizer in GOLDEN_MATRIX:
        out_path = generate_one(spec_name, seed, realizer)
        print(f"  OK: {out_path.name}")

    print()
    print(f"Regenerated {len(GOLDEN_MATRIX)} goldens.")
    print("REMINDER: Attach audio sample comparing old vs new to PR.")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Regenerate golden MIDI files")
    parser.add_argument(
        "--reason",
        required=True,
        help="Why are you regenerating? (appears in commit message)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        required=True,
        help="Confirm intentional regeneration",
    )
    args = parser.parse_args()

    if not args.confirm:
        print("ERROR: --confirm flag is required")
        return 1

    regenerate(args.reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
