"""
YaO CI Music Generation — generate music in CI/CD pipelines.

Reads level metadata YAML files and generates music for each level.
Designed for game build pipelines.

Prerequisites:
    pip install -e ".[sdk]"
    export ANTHROPIC_API_KEY=sk-...

Run:
    python examples/sdk/ci/generate_music.py levels/
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import yaml

from yao.sdk import YaoAgent
from yao.sdk.events import AudioReadyEvent, ConductorFinishedEvent


async def generate_for_level(level_path: Path) -> str | None:
    """Generate music for a single level description.

    Args:
        level_path: Path to a YAML file with mood/length fields.

    Returns:
        Path to generated WAV, or None.
    """
    with open(level_path) as f:
        level = yaml.safe_load(f)

    mood = level.get("mood", "calm")
    length = level.get("length_seconds", 60)
    name = level_path.stem

    description = f"a {mood} BGM, {length} seconds long"
    wav = None

    async with YaoAgent(
        project=f"ci-{name}",
        permission_mode="bypassPermissions",
    ) as agent:
        async for event in agent.conduct(description, max_iterations=1):
            if isinstance(event, AudioReadyEvent):
                wav = event.wav_path
            elif isinstance(event, ConductorFinishedEvent):
                print(f"  [{name}] {event.status}")

    return wav


async def main(levels_dir: str) -> None:
    levels = sorted(Path(levels_dir).glob("*.yaml"))
    print(f"Found {len(levels)} level(s)")

    for level in levels:
        print(f"Generating music for {level.name}...")
        wav = await generate_for_level(level)
        if wav:
            print(f"  -> {wav}")
        else:
            print("  -> (no audio)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_music.py <levels_dir>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
