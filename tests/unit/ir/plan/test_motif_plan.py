"""Tests for MotifPlan IR type."""

from __future__ import annotations

from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed, MotifTransform


class TestMotifSeed:
    """Test MotifSeed creation and serialization."""

    def test_create_seed(self) -> None:
        seed = MotifSeed(
            id="M1",
            rhythm_shape=(1.0, 0.5, 0.5, 1.0),
            interval_shape=(0, 2, 4, 5),
            origin_section="verse",
            character="lyrical ascending",
        )
        assert seed.id == "M1"
        assert seed.length_beats() == 3.0

    def test_roundtrip_dict(self) -> None:
        seed = MotifSeed(
            id="M1",
            rhythm_shape=(1.0, 0.5, 0.5),
            interval_shape=(0, 2, -1),
            origin_section="chorus",
        )
        data = seed.to_dict()
        restored = MotifSeed.from_dict(data)
        assert restored.id == seed.id
        assert restored.rhythm_shape == seed.rhythm_shape
        assert restored.interval_shape == seed.interval_shape
        assert restored.origin_section == seed.origin_section


class TestMotifPlacement:
    """Test MotifPlacement creation and serialization."""

    def test_create_placement(self) -> None:
        placement = MotifPlacement(
            motif_id="M1",
            section_id="chorus",
            start_beat=32.0,
            transform=MotifTransform.INVERSION,
            transposition=5,
            intensity=0.3,
        )
        assert placement.motif_id == "M1"
        assert placement.transform == MotifTransform.INVERSION

    def test_roundtrip_dict(self) -> None:
        placement = MotifPlacement(
            motif_id="M2",
            section_id="bridge",
            start_beat=48.0,
            transform=MotifTransform.RETROGRADE,
        )
        data = placement.to_dict()
        restored = MotifPlacement.from_dict(data)
        assert restored.motif_id == placement.motif_id
        assert restored.transform == MotifTransform.RETROGRADE


class TestMotifPlan:
    """Test MotifPlan queries and serialization."""

    def _make_plan(self) -> MotifPlan:
        return MotifPlan(
            seeds=[
                MotifSeed("M1", (1.0, 1.0), (0, 2), "verse", "main theme"),
                MotifSeed("M2", (0.5, 0.5, 1.0), (0, 4, 2), "chorus", "hook"),
            ],
            placements=[
                MotifPlacement("M1", "verse", 0.0),
                MotifPlacement("M1", "chorus", 16.0, MotifTransform.SEQUENCE_UP),
                MotifPlacement("M1", "verse", 32.0, MotifTransform.INVERSION),
                MotifPlacement("M2", "chorus", 20.0),
                MotifPlacement("M2", "bridge", 48.0, MotifTransform.RETROGRADE),
            ],
        )

    def test_seed_by_id(self) -> None:
        plan = self._make_plan()
        assert plan.seed_by_id("M1") is not None
        assert plan.seed_by_id("M1").character == "main theme"
        assert plan.seed_by_id("M99") is None

    def test_placements_in_section(self) -> None:
        plan = self._make_plan()
        verse_placements = plan.placements_in_section("verse")
        assert len(verse_placements) == 2
        chorus_placements = plan.placements_in_section("chorus")
        assert len(chorus_placements) == 2

    def test_recurrence_count(self) -> None:
        plan = self._make_plan()
        assert plan.recurrence_count("M1") == 3
        assert plan.recurrence_count("M2") == 2

    def test_roundtrip_dict(self) -> None:
        plan = self._make_plan()
        data = plan.to_dict()
        restored = MotifPlan.from_dict(data)
        assert len(restored.seeds) == 2
        assert len(restored.placements) == 5
        assert restored.recurrence_count("M1") == 3
