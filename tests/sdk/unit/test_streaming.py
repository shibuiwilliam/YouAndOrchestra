"""Tests for yao.sdk.streaming — message-to-event translation."""

from __future__ import annotations

from unittest.mock import MagicMock

from claude_agent_sdk import AssistantMessage, ToolUseBlock

from yao.sdk.events import (
    PhaseStartedEvent,
    SubagentStartedEvent,
)
from yao.sdk.streaming import translate_message

_MODEL = "claude-sonnet-4-6"


class TestTranslateMessage:
    def test_unknown_message_returns_empty(self) -> None:
        msg = MagicMock()
        events = translate_message(msg)
        assert events == []

    def test_assistant_with_compose_tool_use(self) -> None:
        block = ToolUseBlock(id="test", name="mcp__yao__yao_compose", input={})
        msg = AssistantMessage(content=[block], model=_MODEL)

        events = translate_message(msg)
        assert len(events) == 1
        assert isinstance(events[0], PhaseStartedEvent)
        assert events[0].phase == "skeletal_generation"

    def test_assistant_with_critique_tool_use(self) -> None:
        block = ToolUseBlock(id="test", name="mcp__yao__yao_critique", input={})
        msg = AssistantMessage(content=[block], model=_MODEL)

        events = translate_message(msg)
        assert len(events) == 1
        assert isinstance(events[0], SubagentStartedEvent)
        assert events[0].subagent_name == "adversarial_critic"

    def test_assistant_with_agent_tool_use(self) -> None:
        block = ToolUseBlock(
            id="test",
            name="Agent",
            input={"name": "composer"},
        )
        msg = AssistantMessage(content=[block], model=_MODEL)

        events = translate_message(msg)
        assert any(isinstance(e, SubagentStartedEvent) and e.subagent_name == "composer" for e in events)

    def test_assistant_with_conduct_tool_use(self) -> None:
        block = ToolUseBlock(id="test", name="mcp__yao__yao_conduct", input={})
        msg = AssistantMessage(content=[block], model=_MODEL)

        events = translate_message(msg)
        assert len(events) == 1
        assert isinstance(events[0], PhaseStartedEvent)
        assert events[0].phase == "intent_crystallization"

    def test_assistant_with_evaluate_tool_use(self) -> None:
        block = ToolUseBlock(id="test", name="mcp__yao__yao_evaluate", input={})
        msg = AssistantMessage(content=[block], model=_MODEL)

        events = translate_message(msg)
        assert len(events) == 1
        assert isinstance(events[0], PhaseStartedEvent)
        assert events[0].phase == "listening_simulation"

    def test_assistant_with_render_tool_use(self) -> None:
        block = ToolUseBlock(id="test", name="mcp__yao__yao_render_audio", input={})
        msg = AssistantMessage(content=[block], model=_MODEL)

        events = translate_message(msg)
        assert len(events) == 1
        assert isinstance(events[0], SubagentStartedEvent)
        assert events[0].subagent_name == "mix_engineer"
