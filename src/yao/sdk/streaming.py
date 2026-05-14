"""Message-to-YaoEvent translator.

Converts the raw message stream from ``query()`` / ``ClaudeSDKClient``
into typed ``YaoEvent`` subclasses that UIs can subscribe to.
"""

from __future__ import annotations

import json
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    RateLimitEvent,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    ToolUseBlock,
    UserMessage,
)

from yao.sdk.events import (
    AudioReadyEvent,
    CritiqueAvailableEvent,
    EvaluationReportEvent,
    IterationCompletedEvent,
    PhaseStartedEvent,
    SubagentStartedEvent,
    YaoEvent,
)

# Phase names from PROJECT.md §6
_PHASE_NAMES = [
    "intent_crystallization",
    "architectural_sketch",
    "skeletal_generation",
    "critic_composer_dialogue",
    "detailed_filling",
    "listening_simulation",
]

Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent | RateLimitEvent


def translate_message(msg: Message, iteration: int = 0) -> list[YaoEvent]:
    """Translate a single SDK message into zero or more YaoEvents.

    Args:
        msg: A message from the SDK stream.
        iteration: Current iteration number for context.

    Returns:
        List of YaoEvent subclasses extracted from the message.
    """
    events: list[YaoEvent] = []

    if isinstance(msg, AssistantMessage):
        events.extend(_extract_from_assistant(msg, iteration))
    elif isinstance(msg, ResultMessage):
        events.extend(_extract_from_result(msg, iteration))

    return events


def _extract_from_assistant(msg: AssistantMessage, iteration: int) -> list[YaoEvent]:
    """Extract events from an AssistantMessage."""
    events: list[YaoEvent] = []

    for block in msg.content:
        if isinstance(block, ToolUseBlock):
            events.extend(_extract_from_tool_use(block, iteration))

    return events


def _extract_from_tool_use(block: ToolUseBlock, iteration: int) -> list[YaoEvent]:
    """Extract events from a tool use block."""
    events: list[YaoEvent] = []
    tool_name = block.name

    # Detect YaO tool calls
    if tool_name == "mcp__yao__yao_compose":
        events.append(PhaseStartedEvent(iteration=iteration, phase="skeletal_generation"))
    elif tool_name == "mcp__yao__yao_conduct":
        events.append(PhaseStartedEvent(iteration=iteration, phase="intent_crystallization"))
    elif tool_name == "mcp__yao__yao_critique":
        events.append(SubagentStartedEvent(iteration=iteration, subagent_name="adversarial_critic"))
    elif tool_name == "mcp__yao__yao_render_audio":
        events.append(SubagentStartedEvent(iteration=iteration, subagent_name="mix_engineer"))
    elif tool_name == "mcp__yao__yao_evaluate":
        events.append(PhaseStartedEvent(iteration=iteration, phase="listening_simulation"))

    # Detect subagent invocations
    if tool_name == "Agent":
        input_data = block.input if isinstance(block.input, dict) else {}
        agent_name = input_data.get("name", "")
        if agent_name:
            events.append(SubagentStartedEvent(iteration=iteration, subagent_name=agent_name))

    return events


def _extract_from_result(msg: ResultMessage, iteration: int) -> list[YaoEvent]:
    """Extract events from a ResultMessage (final response)."""
    events: list[YaoEvent] = []

    # ResultMessage has a 'result' text field, not 'content'
    text = msg.result or ""

    # Try to parse structured results from the text
    if text:
        try:
            data = json.loads(text)
            events.extend(_extract_from_structured(data, iteration))
        except (json.JSONDecodeError, TypeError):
            pass

    return events


def _extract_from_structured(data: dict[str, Any], iteration: int) -> list[YaoEvent]:
    """Extract events from structured JSON data in tool results."""
    events: list[YaoEvent] = []

    if "iteration_path" in data and "evaluation" in data:
        eval_data = data.get("evaluation", {})
        events.append(
            IterationCompletedEvent(
                iteration=iteration,
                iteration_path=data["iteration_path"],
                evaluation=eval_data,
                pass_status=eval_data.get("passed", False),
            )
        )

    if "critique_md_path" in data:
        events.append(
            CritiqueAvailableEvent(
                iteration=iteration,
                critique_md_path=data["critique_md_path"],
                severity_counts=data.get("severity_counts", {}),
            )
        )

    if "wav_path" in data:
        events.append(
            AudioReadyEvent(
                iteration=iteration,
                wav_path=data["wav_path"],
                duration_seconds=data.get("duration_seconds", 0.0),
            )
        )

    if "evaluation_json_path" in data:
        events.append(
            EvaluationReportEvent(
                iteration=iteration,
                evaluation_json_path=data["evaluation_json_path"],
                scores=data.get("scores", {}),
            )
        )

    return events
