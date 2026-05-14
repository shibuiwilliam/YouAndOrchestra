# YaO Agent SDK — API Reference

## Lane A: `YaoAgent`

### Constructor

```python
YaoAgent(
    project: str,
    *,
    cwd: str | Path | None = None,
    model: str | None = None,
    permission_mode: PermissionMode = "acceptEdits",
    extra_options: ClaudeAgentOptions | None = None,
)
```

### Methods

All methods are async generators yielding `YaoEvent` subclasses.

| Method | Slash Command | Description |
|---|---|---|
| `sketch(description)` | `/sketch` | Interactive spec creation |
| `compose(spec_or_desc)` | `/compose` | Single iteration |
| `conduct(spec_or_desc, max_iterations=3)` | `/conduct` | Full loop |
| `critique(iteration=None)` | `/critique` | Adversarial review |
| `regenerate_section(section, seed=None)` | `/regenerate-section` | Replace one section |
| `render(iteration=None)` | `/render` | MIDI to WAV |
| `diff(iter_a, iter_b)` | `/diff` | Compare iterations |
| `evaluate(iteration=None)` | `/evaluate` | Quality scoring |
| `explain(query)` | `/explain` | Provenance query |
| `chat(prompt)` | (free-form) | Any instruction |

## Lane B: Building Blocks

### `create_yao_mcp_server()`

Returns an `McpSdkServerConfig` with 15 in-process tools.

### `default_yao_options(project, *, cwd=None, extra_options=None)`

Returns a `ClaudeAgentOptions` pre-configured for music production.

### `yao_agent_definitions(*, agents_dir=None)`

Returns `dict[str, AgentDefinition]` parsed from `.claude/agents/*.md`.

### `default_yao_hooks()`

Returns hook configuration for auto-render, auto-critique, auto-provenance.

### `default_yao_permission(tool_name, input_data, context)`

Permission callback that protects iterations, references, and agent definitions.

## Events

| Event | When |
|---|---|
| `PhaseStartedEvent` | Cognitive phase begins |
| `PhaseCompletedEvent` | Cognitive phase ends |
| `SubagentStartedEvent` | Subagent begins work |
| `IterationCompletedEvent` | Conductor iteration done |
| `EvaluationReportEvent` | evaluation.json written |
| `CritiqueAvailableEvent` | critique.md written |
| `AudioReadyEvent` | WAV rendering done |
| `ProvenanceUpdatedEvent` | Provenance appended |
| `ConductorFinishedEvent` | conduct() run complete |

## MCP Tools

15 tools exposed via the in-process server:

`yao_compose`, `yao_conduct`, `yao_critique`, `yao_regenerate_section`,
`yao_render_audio`, `yao_evaluate`, `yao_diff`, `yao_explain`,
`yao_validate_spec`, `yao_load_spec`, `yao_new_project`,
`yao_list_iterations`, `yao_read_iteration`, `yao_arch_lint`, `yao_run_tests`
