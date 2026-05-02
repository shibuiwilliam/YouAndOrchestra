"""Tests for drum_patterner generator."""

from __future__ import annotations

import pytest

from yao.generators.drum_patterner import generate_drum_hits, load_pattern
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import (
    CompositionSpec,
    DrumsSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)

ALL_PATTERNS = [
    "pop_8beat",
    "four_on_the_floor",
    "lofi_laidback",
    "trap_half_time",
    "rock_backbeat",
    "jazz_swing_ride",
    "ballad_brushed",
    "game_drive_16bit",
]


def _make_spec(pattern: str = "pop_8beat", bars: int = 4) -> CompositionSpec:
    return CompositionSpec(
        title="Drum Test",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=bars, dynamics="mf")],
        drums=DrumsSpec(pattern_family=pattern),
        generation=GenerationConfig(strategy="rule_based", seed=42),
    )


class TestLoadPattern:
    """Test pattern loading from YAML files."""

    @pytest.mark.parametrize("name", ALL_PATTERNS)
    def test_all_patterns_load(self, name: str) -> None:
        pattern = load_pattern(name)
        assert pattern.id == name
        assert len(pattern.hits) > 0

    def test_nonexistent_pattern_raises(self) -> None:
        from yao.errors import SpecValidationError

        with pytest.raises(SpecValidationError, match="not found"):
            load_pattern("nonexistent_pattern_xyz")

    @pytest.mark.parametrize("name", ALL_PATTERNS)
    def test_patterns_have_valid_kit_pieces(self, name: str) -> None:
        from yao.ir.drum import GM_DRUM_MAP

        pattern = load_pattern(name)
        for hit in pattern.hits:
            assert hit.kit_piece in GM_DRUM_MAP


class TestGenerateDrumHits:
    """Test drum hit generation across sections."""

    def test_generates_hits_for_spec_with_drums(self) -> None:
        spec = _make_spec("pop_8beat", bars=4)
        hits, prov = generate_drum_hits(spec)
        assert len(hits) > 0
        assert len(prov.records) >= 2  # noqa: PLR2004 — loaded + section

    def test_no_hits_without_drums_spec(self) -> None:
        spec = CompositionSpec(
            title="No Drums",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
            generation=GenerationConfig(strategy="rule_based"),
        )
        hits, prov = generate_drum_hits(spec)
        assert len(hits) == 0

    def test_hit_count_scales_with_bars(self) -> None:
        short = _make_spec("pop_8beat", bars=2)
        long = _make_spec("pop_8beat", bars=8)
        hits_short, _ = generate_drum_hits(short)
        hits_long, _ = generate_drum_hits(long)
        assert len(hits_long) > len(hits_short)

    def test_swing_shifts_offbeat_positions(self) -> None:
        straight = _make_spec("pop_8beat", bars=1)
        straight.drums = DrumsSpec(pattern_family="pop_8beat", swing=0.0)  # type: ignore[assignment]
        swung = _make_spec("pop_8beat", bars=1)
        swung.drums = DrumsSpec(pattern_family="pop_8beat", swing=0.6)  # type: ignore[assignment]

        hits_straight, _ = generate_drum_hits(straight)
        hits_swung, _ = generate_drum_hits(swung)

        # Swung hits should have different time positions
        straight_times = sorted(h.time_beats for h in hits_straight)
        swung_times = sorted(h.time_beats for h in hits_swung)
        assert straight_times != swung_times

    def test_ghost_notes_add_soft_hits(self) -> None:
        spec_no_ghost = _make_spec("pop_8beat", bars=4)
        spec_no_ghost.drums = DrumsSpec(pattern_family="pop_8beat", ghost_notes_density=0.0)  # type: ignore[assignment]

        spec_with_ghost = _make_spec("pop_8beat", bars=4)
        spec_with_ghost.drums = DrumsSpec(pattern_family="pop_8beat", ghost_notes_density=0.8)  # type: ignore[assignment]

        hits_no, _ = generate_drum_hits(spec_no_ghost, seed=42)
        hits_yes, _ = generate_drum_hits(spec_with_ghost, seed=42)

        assert len(hits_yes) > len(hits_no)

        # Ghost notes should have low velocity
        ghost_velocities = [h.velocity for h in hits_yes if h.velocity < 50]  # noqa: PLR2004
        assert len(ghost_velocities) > 0

    def test_trajectory_density_thins_hits(self) -> None:
        spec = _make_spec("pop_8beat", bars=4)
        low_density = MultiDimensionalTrajectory.uniform(0.2)
        high_density = MultiDimensionalTrajectory.uniform(0.9)

        hits_sparse, _ = generate_drum_hits(spec, trajectory=low_density, seed=42)
        hits_dense, _ = generate_drum_hits(spec, trajectory=high_density, seed=42)

        # Low density should thin out non-essential hits
        assert len(hits_sparse) <= len(hits_dense)

    def test_deterministic_with_seed(self) -> None:
        spec = _make_spec("lofi_laidback", bars=4)
        hits_a, _ = generate_drum_hits(spec, seed=42)
        hits_b, _ = generate_drum_hits(spec, seed=42)
        assert len(hits_a) == len(hits_b)
        for a, b in zip(hits_a, hits_b, strict=True):
            assert a.time_beats == b.time_beats
            assert a.kit_piece == b.kit_piece
