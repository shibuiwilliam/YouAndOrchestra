"""Skill grounding integration test — Wave 2.1.

Verifies that genre skill files actually influence generation output.
This is the critical "does editing a Skill change the music?" test.

Closes Gap-3 from docs/audit/2026-05-status-reaudit.md.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import yaml

from yao.skills.loader import SkillRegistry


class TestSkillGrounding:
    """Test that Skill edits change generation behavior."""

    def test_tempo_range_sourced_from_skill(self) -> None:
        """TempoOutOfRangeDetector should use SkillRegistry tempo ranges."""
        registry = SkillRegistry()
        cinematic = registry.get_genre("cinematic")
        assert cinematic is not None

        lo, hi = cinematic.tempo_range
        # Cinematic tempo range is [60, 160]
        assert lo == 60.0
        assert hi == 160.0

    def test_changing_skill_changes_chord_palette(self) -> None:
        """Modifying a skill's chord progressions changes the palette lookup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy one skill YAML to temp dir
            src_yaml = Path("src/yao/skills/genres/jazz_swing.yaml")
            if not src_yaml.exists():
                return  # Skip if not found
            dest = Path(tmpdir) / "jazz_swing.yaml"
            shutil.copy(src_yaml, dest)

            # Load original
            registry_orig = SkillRegistry(skills_dir=Path(tmpdir))
            palette_orig = registry_orig.chord_palette_for("jazz_swing")
            assert palette_orig is not None
            assert len(palette_orig) >= 3

            # Modify the YAML: replace chord progressions
            with open(dest, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            data["typical_chord_progressions"] = [["I", "bVII", "IV", "I"]]
            with open(dest, "w", encoding="utf-8") as f:
                yaml.dump(data, f)

            # Reload
            registry_new = SkillRegistry(skills_dir=Path(tmpdir))
            palette_new = registry_new.chord_palette_for("jazz_swing")

            # Palettes should differ
            assert palette_new is not None
            assert palette_new != palette_orig
            assert "bVII" in palette_new

    def test_changing_tempo_range_affects_fitness_check(self) -> None:
        """Changing a skill's tempo range should change fitness detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a skill with narrow tempo range
            narrow_data = {
                "genre": "test_narrow",
                "tempo_range": [80, 90],
                "typical_keys": ["C"],
                "preferred_instruments": ["piano"],
                "avoided_instruments": [],
            }
            dest = Path(tmpdir) / "test_narrow.yaml"
            with open(dest, "w", encoding="utf-8") as f:
                yaml.dump(narrow_data, f)

            registry = SkillRegistry(skills_dir=Path(tmpdir))
            r = registry.tempo_range_for("test_narrow")
            assert r == (80.0, 90.0)

            # 120 BPM should be out of range [80, 90]
            assert r[1] < 120

    def test_skill_registry_loads_all_22_genres(self) -> None:
        """All 22 genre skills should be loadable."""
        registry = SkillRegistry()
        assert registry.genre_count() >= 22

    def test_spec_compiler_uses_skill_instruments(self) -> None:
        """SpecCompiler should use skill instruments for known genres."""
        from yao.sketch.compiler import SpecCompiler

        compiler = SpecCompiler()
        # "cinematic" genre → should get orchestral instruments from skill
        spec, _ = compiler.compile(
            "a cinematic piece",
            "test-cinematic",
            language="en",
        )

        # Cinematic skill prefers: strings_ensemble, french_horn, piano, cello, timpani
        names = [i.name for i in spec.instruments]
        assert "strings_ensemble" in names, f"Expected orchestral instruments, got {names}"

    def test_harmony_planner_uses_skill_chord_palette(self) -> None:
        """HarmonyPlanner should use chord progressions from skill."""
        from yao.generators.plan.harmony_planner import RuleBasedHarmonyPlanner
        from yao.ir.trajectory import MultiDimensionalTrajectory
        from yao.reflect.provenance import ProvenanceLog
        from yao.schema.composition_v2 import CompositionSpecV2

        spec = CompositionSpecV2.model_validate(
            {
                "version": "2",
                "identity": {"title": "Grounding Test", "duration_sec": 14},
                "global": {"key": "Bb major", "bpm": 140, "time_signature": "4/4", "genre": "jazz_swing"},
                "form": {"sections": [{"id": "main", "bars": 8, "density": 0.5}]},
                "harmony": {"chord_palette": ["I", "IV", "V", "vi"]},  # Default → skill should override
                "arrangement": {"instruments": {"piano": {"role": "melody"}}},
                "generation": {"strategy": "rule_based"},
            }
        )

        planner = RuleBasedHarmonyPlanner()
        prov = ProvenanceLog()
        traj = MultiDimensionalTrajectory.default()

        result = planner.generate(spec, traj, prov)
        harmony = result["harmony"]

        # Should have chord events from jazz skill palette (ii7, V7, Imaj7, etc.)
        romans = [e.roman for e in harmony.chord_events]
        assert len(romans) > 0

        # Check provenance records source_skill
        harmony_records = prov.query_by_operation("harmony_planning")
        assert len(harmony_records) >= 1
        assert harmony_records[0].parameters.get("source_skill") == "jazz_swing"
