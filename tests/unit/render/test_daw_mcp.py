"""Tests for DAW MCP Bridge."""

from __future__ import annotations

from yao.render.daw.mcp_bridge import DAWMCPBridge, MCPStatus


class TestDAWMCPBridge:
    def test_default_disconnected(self) -> None:
        bridge = DAWMCPBridge()
        assert not bridge.status.connected

    def test_connect_stub_returns_disconnected(self) -> None:
        bridge = DAWMCPBridge()
        status = bridge.connect("reaper")
        assert isinstance(status, MCPStatus)
        assert not status.connected
        assert status.daw_name == "reaper"

    def test_push_without_connection_fails(self) -> None:
        from yao.ir.note import Note
        from yao.ir.score_ir import Part, ScoreIR, Section

        bridge = DAWMCPBridge()
        score = ScoreIR(
            title="Test",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="v",
                    start_bar=0,
                    end_bar=1,
                    parts=(
                        Part(
                            instrument="piano",
                            notes=(
                                Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
                            ),
                        ),
                    ),
                ),
            ),
        )
        assert not bridge.push_score(score)

    def test_pull_without_connection_returns_none(self) -> None:
        bridge = DAWMCPBridge()
        assert bridge.pull_changes() is None
