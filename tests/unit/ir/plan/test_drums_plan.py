"""Tests for DrumPattern IR type."""

from __future__ import annotations

from yao.ir.plan.drums import DrumHit, DrumPattern, FillLocation, KitPiece


class TestDrumHit:
    """Test DrumHit creation and serialization."""

    def test_create_hit(self) -> None:
        hit = DrumHit(
            time=0.0,
            duration=0.25,
            kit_piece=KitPiece.KICK,
            velocity=100,
            microtiming_ms=-5.0,
        )
        assert hit.kit_piece == KitPiece.KICK
        assert hit.microtiming_ms == -5.0
        assert not hit.is_ghost

    def test_ghost_note(self) -> None:
        hit = DrumHit(
            time=1.5,
            duration=0.125,
            kit_piece=KitPiece.SNARE,
            velocity=30,
            is_ghost=True,
        )
        assert hit.is_ghost

    def test_roundtrip_dict(self) -> None:
        hit = DrumHit(0.0, 0.25, KitPiece.CLOSED_HAT, 80, 2.0, False)
        data = hit.to_dict()
        restored = DrumHit.from_dict(data)
        assert restored.kit_piece == KitPiece.CLOSED_HAT
        assert restored.velocity == 80
        assert restored.microtiming_ms == 2.0


class TestDrumPattern:
    """Test DrumPattern creation and queries."""

    def _make_pattern(self) -> DrumPattern:
        return DrumPattern(
            id="pop_8beat",
            genre="pop",
            time_signature="4/4",
            bars=1,
            hits=[
                DrumHit(0.0, 0.25, KitPiece.KICK, 100),
                DrumHit(1.0, 0.25, KitPiece.SNARE, 90),
                DrumHit(2.0, 0.25, KitPiece.KICK, 95),
                DrumHit(3.0, 0.25, KitPiece.SNARE, 90),
                DrumHit(0.0, 0.125, KitPiece.CLOSED_HAT, 70),
                DrumHit(0.5, 0.125, KitPiece.CLOSED_HAT, 60),
                DrumHit(1.0, 0.125, KitPiece.CLOSED_HAT, 70),
                DrumHit(1.5, 0.125, KitPiece.CLOSED_HAT, 60),
            ],
            swing=0.1,
            fills=[FillLocation("chorus", 7, "tom_cascade")],
        )

    def test_hits_for_piece(self) -> None:
        pattern = self._make_pattern()
        kicks = pattern.hits_for_piece(KitPiece.KICK)
        assert len(kicks) == 2
        hats = pattern.hits_for_piece(KitPiece.CLOSED_HAT)
        assert len(hats) == 4

    def test_roundtrip_dict(self) -> None:
        pattern = self._make_pattern()
        data = pattern.to_dict()
        restored = DrumPattern.from_dict(data)
        assert restored.id == "pop_8beat"
        assert len(restored.hits) == 8
        assert restored.swing == 0.1
        assert len(restored.fills) == 1
        assert restored.fills[0].fill_type == "tom_cascade"
