# YaO Agent SDK — Quickstart

## Installation

```bash
pip install -e ".[sdk]"
export ANTHROPIC_API_KEY=sk-...
```

## Minimal Example

```python
import asyncio
from yao.sdk import YaoAgent
from yao.sdk.events import IterationCompletedEvent, AudioReadyEvent

async def main():
    async with YaoAgent(project="my-first-song") as agent:
        async for event in agent.conduct(
            "a calm piano piece in D minor for studying",
            max_iterations=3,
        ):
            if isinstance(event, IterationCompletedEvent):
                print(f"Iteration {event.iteration}: {'PASS' if event.pass_status else 'FAIL'}")
            elif isinstance(event, AudioReadyEvent):
                print(f"Audio: {event.wav_path}")

asyncio.run(main())
```

## Using a YAML Spec

```python
async with YaoAgent(project="rainy-cafe") as agent:
    async for event in agent.compose("specs/projects/rainy-cafe/composition.yaml"):
        print(event)
```

## Critique an Iteration

```python
async with YaoAgent(project="rainy-cafe") as agent:
    async for event in agent.critique("outputs/projects/rainy-cafe/iterations/v001"):
        print(event)
```

## Lane B (Raw SDK)

```python
from claude_agent_sdk import query
from yao.sdk import default_yao_options

opts = default_yao_options(project="my-song")
async for msg in query(prompt="/compose my-song", options=opts):
    print(msg)
```
