"""Tests for the motif IR module."""

from __future__ import annotations

from yao.ir.motif import Motif, MotifNetwork, MotifNode, augment, diminish, invert, retrograde, transpose
from yao.ir.note import Note


def _make_simple_motif() -> Motif:
    """Create a simple C-D-E motif for testing."""
    return Motif(
        notes=(
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
            Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="piano"),
            Note(pitch=64, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="piano"),
        ),
        label="test_motif",
    )


class TestMotif:
    def test_duration_beats(self) -> None:
        m = _make_simple_motif()
        assert m.duration_beats == 3.0

    def test_pitch_range(self) -> None:
        m = _make_simple_motif()
        assert m.pitch_range == (60, 64)

    def test_empty_motif(self) -> None:
        m = Motif(notes=())
        assert m.duration_beats == 0.0
        assert m.pitch_range == (0, 0)

    def test_frozen(self) -> None:
        m = _make_simple_motif()
        import pytest

        with pytest.raises(AttributeError):
            m.label = "changed"  # type: ignore[misc]


class TestTranspose:
    def test_transpose_up(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, 5)
        assert [n.pitch for n in result.notes] == [65, 67, 69]

    def test_transpose_down(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, -2)
        assert [n.pitch for n in result.notes] == [58, 60, 62]

    def test_transpose_records_transformation(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, 3)
        assert "transpose(3)" in result.transformations_applied

    def test_transpose_preserves_rhythm(self) -> None:
        m = _make_simple_motif()
        result = transpose(m, 5)
        for orig, trans in zip(m.notes, result.notes, strict=True):
            assert orig.start_beat == trans.start_beat
            assert orig.duration_beats == trans.duration_beats


class TestInvert:
    def test_invert_around_first_note(self) -> None:
        m = _make_simple_motif()
        result = invert(m)
        # C(60) stays, D(62) → Bb(58), E(64) → Ab(56)
        assert [n.pitch for n in result.notes] == [60, 58, 56]

    def test_invert_around_axis(self) -> None:
        m = _make_simple_motif()
        result = invert(m, axis=62)
        # C(60) → D(64), D(62) stays, E(64) → C(60)
        assert [n.pitch for n in result.notes] == [64, 62, 60]


class TestRetrograde:
    def test_retrograde_reverses_order(self) -> None:
        m = _make_simple_motif()
        result = retrograde(m)
        # E plays first (at beat 0), then D, then C
        assert result.notes[0].pitch == 64
        assert result.notes[1].pitch == 62
        assert result.notes[2].pitch == 60

    def test_retrograde_records_transformation(self) -> None:
        m = _make_simple_motif()
        result = retrograde(m)
        assert "retrograde" in result.transformations_applied


class TestAugment:
    def test_augment_doubles_duration(self) -> None:
        m = _make_simple_motif()
        result = augment(m, 2.0)
        for note in result.notes:
            assert note.duration_beats == 2.0

    def test_augment_stretches_positions(self) -> None:
        m = _make_simple_motif()
        result = augment(m, 2.0)
        assert result.notes[0].start_beat == 0.0
        assert result.notes[1].start_beat == 2.0
        assert result.notes[2].start_beat == 4.0


class TestDiminish:
    def test_diminish_halves_duration(self) -> None:
        m = _make_simple_motif()
        result = diminish(m, 2.0)
        for note in result.notes:
            assert note.duration_beats == 0.5


class TestMotifNode:
    """Tests for A2 MotifNode."""

    def test_node_creation(self) -> None:
        m = _make_simple_motif()
        node = MotifNode(motif=m, parent_id=None, transformation="identity", bar_locations=(0, 1))
        assert node.motif.label == "test_motif"
        assert node.parent_id is None
        assert node.bar_locations == (0, 1)

    def test_derived_node(self) -> None:
        m = _make_simple_motif()
        t = transpose(m, 5)
        node = MotifNode(motif=t, parent_id="test_motif", transformation="transpose", bar_locations=(4, 5))
        assert node.parent_id == "test_motif"
        assert node.transformation == "transpose"


class TestMotifNetwork:
    """Tests for A2 MotifNetwork."""

    def _build_network(self) -> MotifNetwork:
        """Build a test network: seed + 3 derived motifs across 16 bars."""
        m = _make_simple_motif()
        net = MotifNetwork(total_bars=16)
        seed_key = net.add_node(MotifNode(motif=m, bar_locations=(0, 1, 2, 3)))
        net.add_node(
            MotifNode(
                motif=transpose(m, 5),
                parent_id=seed_key,
                transformation="transpose",
                bar_locations=(4, 5, 6, 7),
            )
        )
        net.add_node(
            MotifNode(
                motif=invert(m),
                parent_id=seed_key,
                transformation="invert",
                bar_locations=(8, 9),
            )
        )
        net.add_node(
            MotifNode(
                motif=retrograde(m),
                parent_id=seed_key,
                transformation="retrograde",
                bar_locations=(12, 13),
            )
        )
        return net

    def test_coverage_ratio_full(self) -> None:
        net = self._build_network()
        # Bars covered: 0-9, 12-13 = 12 out of 16
        assert net.coverage_ratio() == 12 / 16

    def test_coverage_ratio_empty(self) -> None:
        net = MotifNetwork(total_bars=8)
        assert net.coverage_ratio() == 0.0

    def test_coverage_ratio_complete(self) -> None:
        m = _make_simple_motif()
        net = MotifNetwork(total_bars=4)
        net.add_node(MotifNode(motif=m, bar_locations=(0, 1, 2, 3)))
        assert net.coverage_ratio() == 1.0

    def test_variation_diversity_multiple_transforms(self) -> None:
        net = self._build_network()
        # Has identity, transpose, invert, retrograde = 4 types
        diversity = net.variation_diversity()
        assert diversity > 0.5  # fairly diverse

    def test_variation_diversity_single_transform(self) -> None:
        m = _make_simple_motif()
        net = MotifNetwork(total_bars=8)
        # All nodes use same transformation
        for i in range(4):
            net.add_node(
                MotifNode(
                    motif=transpose(m, i),
                    transformation="transpose",
                    bar_locations=(i * 2,),
                )
            )
        assert net.variation_diversity() == 0.0  # no diversity

    def test_variation_diversity_empty(self) -> None:
        net = MotifNetwork(total_bars=8)
        assert net.variation_diversity() == 0.0

    def test_trace_lineage(self) -> None:
        net = self._build_network()
        # The transposed motif should trace back to the seed
        # Find the key for the transposed motif
        keys = list(net.nodes.keys())
        transposed_key = keys[1]  # second added
        lineage = net.trace_lineage(transposed_key)
        assert len(lineage) == 2  # seed + derived
        assert lineage[0].transformation == "identity"  # seed
        assert lineage[1].transformation == "transpose"

    def test_trace_lineage_seed(self) -> None:
        net = self._build_network()
        keys = list(net.nodes.keys())
        lineage = net.trace_lineage(keys[0])
        assert len(lineage) == 1  # just the seed

    def test_trace_lineage_nonexistent(self) -> None:
        net = self._build_network()
        lineage = net.trace_lineage("nonexistent")
        assert len(lineage) == 0

    def test_add_node_auto_key(self) -> None:
        net = MotifNetwork(total_bars=4)
        m = Motif(notes=(), label="")  # empty label
        key = net.add_node(MotifNode(motif=m, bar_locations=(0,)))
        assert key == "motif"
        # Adding another with same empty label gets a suffix
        key2 = net.add_node(MotifNode(motif=m, bar_locations=(1,)))
        assert key2 == "motif_1"
