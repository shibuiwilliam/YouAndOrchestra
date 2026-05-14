"""
YaO Discord Bot — compose music via Discord commands.

Listens for !compose <description> and replies with the WAV file
and critique markdown.

Prerequisites:
    pip install -e ".[sdk]" discord.py
    export DISCORD_TOKEN=...
    export ANTHROPIC_API_KEY=sk-...

Run:
    python examples/sdk/discord/bot.py
"""

from __future__ import annotations

import os
from pathlib import Path

from yao.sdk import YaoAgent
from yao.sdk.events import AudioReadyEvent, ConductorFinishedEvent

try:
    import discord
except ImportError as _exc:
    raise ImportError("Install discord.py: pip install discord.py") from _exc

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user:
        return

    if not message.content.startswith("!compose "):
        return

    description = message.content[len("!compose ") :]
    await message.channel.send(f"Composing: {description}...")

    wav_path = None
    async with YaoAgent(
        project="discord-bot",
        permission_mode="bypassPermissions",
    ) as agent:
        async for event in agent.conduct(description, max_iterations=2):
            if isinstance(event, AudioReadyEvent):
                wav_path = event.wav_path
            elif isinstance(event, ConductorFinishedEvent):
                await message.channel.send(f"Done! {event.status}")

    if wav_path and Path(wav_path).exists():
        await message.channel.send(file=discord.File(wav_path))
    else:
        await message.channel.send("Composition complete (no audio rendered).")


if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN", "")
    if not token:
        print("Set DISCORD_TOKEN environment variable")
    else:
        client.run(token)
