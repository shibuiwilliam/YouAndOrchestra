"""
Minimal end-to-end YaO Agent SDK example.

Prerequisites:
    pip install -e ".[sdk]"
    export ANTHROPIC_API_KEY=sk-...

Run:
    python examples/sdk/minimal.py
"""

from __future__ import annotations

import asyncio

from yao.sdk import YaoAgent
from yao.sdk.events import (
    AudioReadyEvent,
    ConductorFinishedEvent,
    CritiqueAvailableEvent,
    IterationCompletedEvent,
    PhaseStartedEvent,
)


async def main() -> None:
    project = "minimal-demo"

    async with YaoAgent(project=project) as agent:
        async for event in agent.conduct(
            "a calm piano piece in D minor for studying, 90 seconds",
            max_iterations=3,
        ):
            match event:
                case PhaseStartedEvent():
                    print(f"[phase] {event.phase} started")
                case IterationCompletedEvent():
                    pass_str = "PASS" if event.pass_status else "FAIL"
                    print(f"[iter {event.iteration}] {pass_str} -> {event.iteration_path}")
                case CritiqueAvailableEvent():
                    print(f"[critique] {event.severity_counts}")
                case AudioReadyEvent():
                    print(f"[audio]    {event.wav_path} ({event.duration_seconds:.1f}s)")
                case ConductorFinishedEvent():
                    print(f"[done]     {event.final_iteration_path}")


if __name__ == "__main__":
    asyncio.run(main())
