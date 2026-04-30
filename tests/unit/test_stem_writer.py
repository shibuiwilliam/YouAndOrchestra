"""Tests for the stem writer."""

from __future__ import annotations

from pathlib import Path

from yao.ir.score_ir import ScoreIR
from yao.render.stem_writer import write_stems
from yao.schema.composition import CompositionSpec


class TestStemWriter:
    def test_writes_stems(self, multi_instrument_spec: CompositionSpec, tmp_output_dir: Path) -> None:
        from yao.generators.rule_based import RuleBasedGenerator

        gen = RuleBasedGenerator()
        score, _ = gen.generate(multi_instrument_spec)

        stems = write_stems(score, tmp_output_dir)
        assert "piano" in stems
        assert "acoustic_bass" in stems

        for path in stems.values():
            assert path.exists()
            assert path.stat().st_size > 0

    def test_stem_directory_created(
        self,
        sample_score_ir: ScoreIR,
        tmp_output_dir: Path,  # noqa: F821
    ) -> None:
        write_stems(sample_score_ir, tmp_output_dir)
        stems_dir = tmp_output_dir / "stems"
        assert stems_dir.exists()
        assert stems_dir.is_dir()
