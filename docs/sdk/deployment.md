# Deployment Guide

## Web App (FastAPI)

See `examples/sdk/web/app.py` for a complete example.

```bash
pip install -e ".[sdk]" fastapi uvicorn sse-starlette
uvicorn examples.sdk.web.app:app --host 0.0.0.0 --port 8000
```

Key considerations:
- Set `permission_mode="bypassPermissions"` in sandboxed environments
- Use `extra_options` to configure `max_budget_usd` per request
- Stream events via Server-Sent Events for real-time UI updates

## Discord/Slack Bot

See `examples/sdk/discord/bot.py`.

```bash
pip install -e ".[sdk]" discord.py
export DISCORD_TOKEN=...
python examples/sdk/discord/bot.py
```

Key considerations:
- Lock down permissions: no Bash, no Edit outside outputs/
- Set a low `max_budget_usd` to prevent abuse
- Reply with the WAV file and critique summary

## CI Pipeline

See `examples/sdk/ci/generate_music.py`.

```yaml
# .github/workflows/music.yml
- run: pip install -e ".[sdk]"
- run: python examples/sdk/ci/generate_music.py levels/
```

Key considerations:
- Use `permission_mode="bypassPermissions"` in sandboxed runners
- Pin seeds for reproducible builds
- Upload WAV artifacts to release

## Jupyter Notebook

```python
from yao.sdk import YaoAgent
from IPython.display import Audio, display

async with YaoAgent(project="notebook") as agent:
    async for event in agent.conduct("a calm piece"):
        if isinstance(event, AudioReadyEvent):
            display(Audio(event.wav_path))
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | API key for Claude |
| `DISCORD_TOKEN` | Discord only | Bot token |

## Resource Budgets

- Default `max_budget_usd`: None (unlimited)
- Recommended for bots: `max_budget_usd=0.50`
- Typical 3-iteration conduct: ~$0.05-0.10 on Sonnet
