# Lane A vs Lane B

YaO's SDK offers two access lanes. Choose based on your needs.

## Lane A — `YaoAgent` (90% of users)

```python
async with YaoAgent(project="my-song") as agent:
    async for event in agent.conduct("a calm piano piece"):
        print(event)
```

**Use when:**
- You want music in 5 lines
- You don't need custom hooks or permissions
- You want typed events and results
- You're building a web app, bot, or notebook

## Lane B — Raw SDK + `default_yao_options` (10% of users)

```python
from claude_agent_sdk import query
from yao.sdk import default_yao_options

opts = default_yao_options(project="my-song")
# Override anything:
opts.permission_mode = "default"
opts.hooks = None

async for msg in query(prompt="/compose my-song", options=opts):
    print(msg)
```

**Use when:**
- You need custom hooks or permissions
- You're building a multi-tenant server
- You need to override the system prompt
- You want to control which subagents load
- You need direct access to SDK messages

## Comparison

| Feature | Lane A | Lane B |
|---|:---:|:---:|
| Lines to compose | 5 | 10-15 |
| Typed events | Yes | Raw messages |
| Custom hooks | Via extra_options | Direct |
| Custom permissions | Via extra_options | Direct |
| Session management | Automatic | Manual |
| Subagent control | All loaded | Pick and choose |

Both lanes use the same Conductor, the same MCP server, and produce
the same musical output.
