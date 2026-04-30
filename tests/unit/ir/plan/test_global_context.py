"""Tests for GlobalContext in MusicalPlan."""

from __future__ import annotations

from yao.ir.plan.musical_plan import GlobalContext


class TestGlobalContext:
    """Test GlobalContext creation and serialization."""

    def test_create_with_instruments(self) -> None:
        ctx = GlobalContext(
            key="G major",
            tempo_bpm=132.0,
            time_signature="3/4",
            genre="classical",
            instruments=(("piano", "melody"), ("violin", "melody"), ("cello", "bass")),
        )
        assert ctx.key == "G major"
        assert ctx.tempo_bpm == 132.0
        assert ctx.time_signature == "3/4"
        assert len(ctx.instruments) == 3

    def test_defaults(self) -> None:
        ctx = GlobalContext()
        assert ctx.key == "C major"
        assert ctx.tempo_bpm == 120.0
        assert ctx.time_signature == "4/4"
        assert ctx.instruments == ()

    def test_roundtrip_dict(self) -> None:
        ctx = GlobalContext(
            key="D minor",
            tempo_bpm=80.0,
            time_signature="6/8",
            genre="cinematic",
            instruments=(("piano", "melody"), ("cello", "bass")),
        )
        data = ctx.to_dict()
        restored = GlobalContext.from_dict(data)
        assert restored.key == ctx.key
        assert restored.tempo_bpm == ctx.tempo_bpm
        assert restored.time_signature == ctx.time_signature
        assert len(restored.instruments) == 2
