"""Tests for ConversationSpec schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.errors import SpecValidationError
from yao.schema.conversation import ConversationEventSpec, ConversationSpec, VoiceFocusSpec


class TestVoiceFocusSpec:
    def test_valid(self) -> None:
        vf = VoiceFocusSpec(
            section_id="verse",
            primary="piano",
            accompaniment=["strings", "bass"],
            fill_capable=["drums"],
        )
        assert vf.primary == "piano"
        assert len(vf.accompaniment) == 2


class TestConversationEventSpec:
    def test_valid(self) -> None:
        ev = ConversationEventSpec(
            type="call_response",
            initiator="piano",
            responder="strings",
            section_id="verse",
            start_bar=0,
            end_bar=4,
        )
        assert ev.type == "call_response"

    def test_negative_start_bar_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            ConversationEventSpec(
                type="call_response",
                initiator="piano",
                section_id="verse",
                start_bar=-1,
                end_bar=4,
            )

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            ConversationEventSpec(
                type="call_response",
                initiator="piano",
                section_id="verse",
                start_bar=4,
                end_bar=2,
            )


class TestConversationSpec:
    def test_empty(self) -> None:
        spec = ConversationSpec()
        assert len(spec.voice_focus) == 0
        assert len(spec.events) == 0

    def test_duplicate_section_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            ConversationSpec(
                voice_focus=[
                    VoiceFocusSpec(section_id="verse", primary="piano"),
                    VoiceFocusSpec(section_id="verse", primary="strings"),
                ]
            )

    def test_primary_for_section(self) -> None:
        spec = ConversationSpec(
            voice_focus=[
                VoiceFocusSpec(section_id="verse", primary="piano"),
                VoiceFocusSpec(section_id="chorus", primary="strings"),
            ]
        )
        assert spec.primary_for_section("verse") == "piano"
        assert spec.primary_for_section("chorus") == "strings"
        assert spec.primary_for_section("bridge") is None

    def test_fill_capable_for_section(self) -> None:
        spec = ConversationSpec(
            voice_focus=[
                VoiceFocusSpec(
                    section_id="verse",
                    primary="piano",
                    fill_capable=["drums", "bass"],
                ),
            ]
        )
        assert spec.fill_capable_for_section("verse") == ["drums", "bass"]
        assert spec.fill_capable_for_section("unknown") == []

    def test_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = """
voice_focus:
  - section_id: verse
    primary: piano
    accompaniment: [strings, bass]
    fill_capable: [drums]
  - section_id: chorus
    primary: strings
    accompaniment: [piano, bass]
    fill_capable: [drums, percussion]

events:
  - type: call_response
    initiator: piano
    responder: strings
    section_id: verse
    start_bar: 0
    end_bar: 4
  - type: fill_in_response
    initiator: bass
    responder: drums
    section_id: verse
    start_bar: 4
    end_bar: 8
    minimum_silence_beats: 1.0
"""
        path = tmp_path / "conversation.yaml"
        path.write_text(yaml_content)
        spec = ConversationSpec.from_yaml(path)
        assert len(spec.voice_focus) == 2
        assert len(spec.events) == 2
        assert spec.events[0].type == "call_response"

    def test_from_yaml_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SpecValidationError):
            ConversationSpec.from_yaml(tmp_path / "missing.yaml")

    def test_from_yaml_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "conversation.yaml"
        path.write_text("")
        spec = ConversationSpec.from_yaml(path)
        assert len(spec.voice_focus) == 0
