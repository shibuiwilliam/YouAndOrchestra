"""Golden MIDI tests — detect unintended musical regression.

Each test generates a MIDI file from a fixed spec + seed + realizer
combination and compares it bit-exactly against a committed golden file.

See tests/golden/README.md for when and how to update goldens.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.golden.comparison import assert_midi_match
from tests.golden.tools.regenerate_goldens import GOLDEN_MATRIX, golden_filename
from yao.generators.note.base import NOTE_REALIZERS
from yao.generators.plan.orchestrator import PlanOrchestrator
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.render.midi_writer import write_midi
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec

INPUTS_DIR = Path(__file__).resolve().parent / "inputs"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def _generate_midi(spec_name: str, seed: int, realizer: str, output_path: Path) -> None:
    """Generate a MIDI file via the v2 pipeline."""
    spec = CompositionSpecV2.from_yaml(INPUTS_DIR / spec_name)
    traj = MultiDimensionalTrajectory.default()
    intent = IntentSpec(text="golden test", keywords=[])
    prov = ProvenanceLog()

    plan = PlanOrchestrator(plan_strategy="rule_based").build_plan(
        spec, traj, intent, prov,
    )
    note_realizer = NOTE_REALIZERS[realizer]()
    score = note_realizer.realize(plan, seed=seed, temperature=0.5, provenance=prov)
    write_midi(score, output_path)


@pytest.mark.golden
class TestGoldenMidi:
    """Golden MIDI regression tests."""

    @pytest.mark.parametrize(
        "spec_name,seed,realizer",
        GOLDEN_MATRIX,
        ids=[
            f"{s.replace('.yaml','')}_seed{sd}_{r}"
            for s, sd, r in GOLDEN_MATRIX
        ],
    )
    def test_golden(
        self,
        spec_name: str,
        seed: int,
        realizer: str,
        tmp_path: Path,
    ) -> None:
        """Verify generated MIDI matches the committed golden."""
        expected_name = golden_filename(spec_name, seed, realizer)
        expected_path = EXPECTED_DIR / expected_name
        actual_path = tmp_path / "actual.mid"

        _generate_midi(spec_name, seed, realizer, actual_path)
        assert_midi_match(actual_path, expected_path, tolerance=0.0)
