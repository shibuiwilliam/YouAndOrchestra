"""
YaO Jupyter Notebook example — run as a Python script or in Jupyter.

Shows how to use YaoAgent in a notebook context with inline progress.

Prerequisites:
    pip install -e ".[sdk]"
    export ANTHROPIC_API_KEY=sk-...

In Jupyter:
    %run examples/sdk/notebook/yao_in_jupyter.py
"""

from __future__ import annotations

import asyncio

from yao.sdk import YaoAgent
from yao.sdk.events import (
    AudioReadyEvent,
    ConductorFinishedEvent,
    IterationCompletedEvent,
    PhaseStartedEvent,
)


async def compose_in_notebook() -> None:
    """Run a composition and print progress inline."""
    print("Starting YaO composition...")

    async with YaoAgent(project="notebook-demo") as agent:
        async for event in agent.conduct(
            "a mysterious puzzle game BGM with piano and strings",
            max_iterations=2,
        ):
            if isinstance(event, PhaseStartedEvent):
                print(f"  Phase: {event.phase}")
            elif isinstance(event, IterationCompletedEvent):
                status = "PASS" if event.pass_status else "FAIL"
                print(f"  Iteration {event.iteration}: {status}")
            elif isinstance(event, AudioReadyEvent):
                print(f"  Audio ready: {event.wav_path}")
                # In Jupyter: from IPython.display import Audio, display
                # display(Audio(event.wav_path))
            elif isinstance(event, ConductorFinishedEvent):
                print(f"  Done: {event.final_iteration_path}")


if __name__ == "__main__":
    asyncio.run(compose_in_notebook())
