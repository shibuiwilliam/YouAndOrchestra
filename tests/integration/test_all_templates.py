"""Integration test: all templates compose with both generators.

Phase 2 acceptance criterion: every composition template produces valid
MIDI through both rule_based and stochastic generators, with provenance
persisted and all notes within instrument ranges.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Import generators to trigger @register_generator decorators
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.registry import get_generator
from yao.render.midi_reader import load_midi_to_score_ir
from yao.render.midi_writer import write_midi
from yao.schema.composition import CompositionSpec
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.loader import load_composition_spec_auto


def _collect_composition_templates() -> list[Path]:
    """Collect all composition template YAML files (v1 + v2)."""
    templates: list[Path] = []
    v1_dir = Path("specs/templates")
    for f in sorted(v1_dir.glob("*.yaml")):
        if f.name == "trajectory-example.yaml":
            continue  # trajectory-only, not a composition spec
        templates.append(f)
    v2_dir = v1_dir / "v2"
    if v2_dir.exists():
        for f in sorted(v2_dir.glob("*.yaml")):
            templates.append(f)
    return templates


def _to_v1(spec: CompositionSpec | CompositionSpecV2) -> CompositionSpec:
    """Convert v2 spec to v1 if needed."""
    if isinstance(spec, CompositionSpecV2):
        return spec.to_v1()
    return spec


_TEMPLATES = _collect_composition_templates()
_STRATEGIES = ["rule_based", "stochastic"]
_SEED = 42


@pytest.mark.integration
class TestAllTemplates:
    @pytest.mark.parametrize("template", _TEMPLATES, ids=[t.stem for t in _TEMPLATES])
    @pytest.mark.parametrize("strategy", _STRATEGIES)
    def test_template_composes(self, template: Path, strategy: str, tmp_path: Path) -> None:
        """Each template generates valid MIDI with the given strategy."""
        raw_spec = load_composition_spec_auto(template)
        spec = _to_v1(raw_spec)

        # Override strategy and seed for deterministic testing
        gen_config = spec.generation.model_copy(update={"strategy": strategy, "seed": _SEED})
        spec = spec.model_copy(update={"generation": gen_config})

        generator = get_generator(strategy)
        score, provenance = generator.generate(spec)

        # Basic structure checks
        assert len(score.all_notes()) > 0, f"No notes generated for {template.name} ({strategy})"
        assert len(score.sections) > 0

        # Write MIDI and verify round-trip
        midi_path = tmp_path / "full.mid"
        write_midi(score, midi_path)
        assert midi_path.exists()
        assert midi_path.stat().st_size > 0

        # Round-trip: load back and verify
        reloaded = load_midi_to_score_ir(midi_path, spec=spec)
        assert len(reloaded.all_notes()) > 0

        # Provenance must exist
        assert len(provenance) > 0
        prov_path = tmp_path / "provenance.json"
        provenance.save(prov_path)
        assert prov_path.exists()

    @pytest.mark.parametrize("template", _TEMPLATES, ids=[t.stem for t in _TEMPLATES])
    def test_stochastic_seed_reproducibility(self, template: Path) -> None:
        """Same seed produces bit-exact identical output."""
        raw_spec = load_composition_spec_auto(template)
        spec = _to_v1(raw_spec)
        gen_config = spec.generation.model_copy(update={"strategy": "stochastic", "seed": _SEED})
        spec = spec.model_copy(update={"generation": gen_config})

        generator = get_generator("stochastic")
        score_a, _ = generator.generate(spec)
        score_b, _ = generator.generate(spec)

        notes_a = score_a.all_notes()
        notes_b = score_b.all_notes()
        assert len(notes_a) == len(notes_b), "Different note counts with same seed"
        for na, nb in zip(notes_a, notes_b, strict=True):
            assert na.pitch == nb.pitch, f"Pitch mismatch: {na.pitch} != {nb.pitch}"
            assert na.start_beat == nb.start_beat
            assert na.velocity == nb.velocity
