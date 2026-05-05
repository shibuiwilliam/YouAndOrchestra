"""Tests for B3 TonalSystem Protocol and implementations."""

from __future__ import annotations

import pytest

from yao.ir.tonal_system import (
    CommonPracticeTonality,
    MaqamSystem,
    ModalSystem,
    TonalSystem,
)


class TestTonalSystemProtocol:
    """All implementations must satisfy the TonalSystem Protocol."""

    def test_common_practice_is_tonal_system(self) -> None:
        assert isinstance(CommonPracticeTonality(), TonalSystem)

    def test_modal_is_tonal_system(self) -> None:
        assert isinstance(ModalSystem("dorian"), TonalSystem)

    def test_maqam_is_tonal_system(self) -> None:
        assert isinstance(MaqamSystem("rast"), TonalSystem)


class TestCommonPracticeTonality:
    """Tests for the default Western tonal system."""

    def test_name(self) -> None:
        sys = CommonPracticeTonality()
        assert sys.name == "common_practice"

    def test_major_scale_has_7_degrees(self) -> None:
        sys = CommonPracticeTonality()
        scale = sys.realize_scale(60)  # C4
        assert len(scale) == 7

    def test_major_scale_intervals_correct(self) -> None:
        sys = CommonPracticeTonality()
        scale = sys.realize_scale(60)
        # Check relative intervals in cents (100 cents = 1 semitone in 12-TET)
        diffs = [scale[i + 1] - scale[i] for i in range(len(scale) - 1)]
        # Major scale: W W H W W W (200, 200, 100, 200, 200, 200)
        expected = [200.0, 200.0, 100.0, 200.0, 200.0, 200.0]
        for d, e in zip(diffs, expected, strict=True):
            assert d == pytest.approx(e)

    def test_authentic_cadence_strongest(self) -> None:
        sys = CommonPracticeTonality()
        # V→I should be 1.0
        assert sys.cadence_strength(4, 0) == 1.0

    def test_plagal_cadence(self) -> None:
        sys = CommonPracticeTonality()
        assert sys.cadence_strength(3, 0) == 0.8

    def test_deceptive_cadence(self) -> None:
        sys = CommonPracticeTonality()
        # V→vi
        assert sys.cadence_strength(4, 5) == 0.6


class TestModalSystem:
    """Tests for the modal tonal system."""

    def test_name_includes_mode(self) -> None:
        sys = ModalSystem("dorian")
        assert "dorian" in sys.name

    def test_dorian_scale_7_degrees(self) -> None:
        sys = ModalSystem("dorian")
        scale = sys.realize_scale(62)  # D
        assert len(scale) == 7

    def test_dorian_has_minor_third_major_sixth(self) -> None:
        sys = ModalSystem("dorian")
        scale = sys.realize_scale(60)  # C dorian
        diffs = [scale[i] - scale[0] for i in range(len(scale))]
        # Dorian: 0, 200, 300, 500, 700, 900, 1000
        assert diffs[2] == pytest.approx(300.0)  # minor third
        assert diffs[5] == pytest.approx(900.0)  # major sixth (characteristic)

    def test_all_modes_valid(self) -> None:
        for mode in ["ionian", "dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"]:
            sys = ModalSystem(mode)
            assert len(sys.realize_scale(60)) == 7

    def test_unknown_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown mode"):
            ModalSystem("invented")

    def test_tonic_resolution_strong(self) -> None:
        sys = ModalSystem("dorian")
        assert sys.cadence_strength(4, 0) >= 0.5


class TestMaqamSystem:
    """Tests for the maqam tonal system."""

    def test_name_includes_maqam(self) -> None:
        sys = MaqamSystem("rast")
        assert "rast" in sys.name

    def test_rast_has_7_degrees(self) -> None:
        sys = MaqamSystem("rast")
        scale = sys.realize_scale(60)
        assert len(scale) == 7

    def test_rast_has_quarter_tones(self) -> None:
        """Rast maqam contains 350-cent and 1050-cent intervals (quarter tones)."""
        sys = MaqamSystem("rast")
        scale = sys.realize_scale(60)
        diffs = [scale[i] - scale[0] for i in range(len(scale))]
        # Rast: 0, 200, 350, 500, 700, 900, 1050
        assert diffs[2] == pytest.approx(350.0)  # three-quarter tone
        assert diffs[6] == pytest.approx(1050.0)  # neutral seventh

    def test_hijaz_has_augmented_second(self) -> None:
        """Hijaz maqam has a 300-cent gap (augmented second) between degrees 1-2."""
        sys = MaqamSystem("hijaz")
        scale = sys.realize_scale(60)
        diffs = [scale[i] - scale[0] for i in range(len(scale))]
        # Hijaz: 0, 100, 400, 500, 700, 800, 1100
        assert diffs[2] - diffs[1] == pytest.approx(300.0)  # augmented second

    def test_all_maqamat_valid(self) -> None:
        for maqam in ["rast", "bayati", "hijaz", "saba", "nahawand"]:
            sys = MaqamSystem(maqam)
            assert len(sys.realize_scale(60)) == 7

    def test_unknown_maqam_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown maqam"):
            MaqamSystem("invented")

    def test_qarar_resolution_strong(self) -> None:
        """Resolution to tonic (qarar) should be strong."""
        sys = MaqamSystem("rast")
        assert sys.cadence_strength(4, 0) >= 0.8

    def test_maqam_not_12tet(self) -> None:
        """Maqam scales should contain non-12-TET intervals."""
        sys = MaqamSystem("rast")
        scale = sys.realize_scale(60)
        diffs = [scale[i] - scale[0] for i in range(len(scale))]
        # At least one interval should not be a multiple of 100
        non_12tet = [d for d in diffs if d % 100 != 0]
        assert len(non_12tet) > 0, "Rast maqam should contain quarter-tone intervals"
