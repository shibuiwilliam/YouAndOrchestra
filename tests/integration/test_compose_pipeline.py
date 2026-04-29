"""Integration test: full composition pipeline from spec to outputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.generators.rule_based import RuleBasedGenerator
from yao.render.midi_writer import write_midi
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec
from yao.verify.analyzer import analyze_score


@pytest.mark.integration
class TestComposePipeline:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Spec -> Generate -> MIDI -> Lint -> Analysis -> Provenance."""
        # 1. Create spec
        spec = CompositionSpec(
            title="Pipeline Test",
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            instruments=[
                InstrumentSpec(name="piano", role="melody"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
            sections=[
                SectionSpec(name="intro", bars=4, dynamics="mp"),
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="outro", bars=4, dynamics="p"),
            ],
        )

        # 2. Generate
        gen = RuleBasedGenerator()
        score, provenance = gen.generate(spec)
        assert len(score.all_notes()) > 0
        assert len(score.sections) == 3

        # 3. Write MIDI
        midi_path = tmp_path / "full.mid"
        write_midi(score, midi_path)
        assert midi_path.exists()
        assert midi_path.stat().st_size > 0

        # 4. Analyze (includes lint)
        report = analyze_score(score)
        assert report.total_notes > 0
        assert "piano" in report.instruments_used
        assert "acoustic_bass" in report.instruments_used

        # 5. No lint errors
        errors = [r for r in report.lint_results if r.severity == "error"]
        assert len(errors) == 0, f"Lint errors: {[r.message for r in errors]}"

        # 6. Save analysis and provenance
        analysis_path = tmp_path / "analysis.json"
        report.save(analysis_path)
        assert analysis_path.exists()

        prov_path = tmp_path / "provenance.json"
        provenance.save(prov_path)
        assert prov_path.exists()
        assert len(provenance) > 0

    def test_pipeline_with_yaml_spec(self, tmp_path: Path) -> None:
        """Load from YAML file, generate, write MIDI."""
        import yaml

        # Write spec to YAML
        data = {
            "title": "YAML Pipeline Test",
            "key": "G major",
            "tempo_bpm": 100,
            "time_signature": "3/4",
            "instruments": [{"name": "piano", "role": "melody"}],
            "sections": [{"name": "waltz", "bars": 8, "dynamics": "mf"}],
        }
        yaml_path = tmp_path / "composition.yaml"
        yaml_path.write_text(yaml.dump(data))

        # Load and generate
        spec = CompositionSpec.from_yaml(yaml_path)
        gen = RuleBasedGenerator()
        score, _ = gen.generate(spec)

        # Write MIDI
        midi_path = tmp_path / "waltz.mid"
        write_midi(score, midi_path)
        assert midi_path.exists()

        # Verify
        report = analyze_score(score)
        assert report.key == "G major"
        assert report.time_signature == "3/4"
