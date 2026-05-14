# Parity with Claude Code

The SDK surface produces identical musical output to Claude Code.
This is enforced by five testable parity guarantees.

## The Five Guarantees

### G1 — Same Files

Both surfaces load `.claude/` and `CLAUDE.md` identically.
The SDK uses `setting_sources=["project"]` to load the same files
Claude Code reads natively.

### G2 — Same Subagent Reasoning

The seven Markdown subagent definitions in `.claude/agents/` are
used by both surfaces. The SDK additionally exposes them as
programmatic `AgentDefinition` via `yao_agent_definitions()`.

The Markdown is authoritative. The Python mirror regenerates on import.

### G3 — Same Conductor Loop

Both surfaces call `yao.conductor.Conductor`. Neither reimplements
the generate → evaluate → adapt → regenerate loop.

### G4 — Same Provenance and Outputs

Both write to `outputs/projects/<name>/iterations/v<NNN>/` with
identical JSON schema. Provenance records use the same format.

### G5 — Same Constraint and Lint Guarantees

Both run music lint and constraint checks through the same
`verify/` modules. A constraint violation in Claude Code is a
constraint violation in the SDK.

## How Parity Is Tested

Tests in `tests/sdk/integration/test_compose_parity.py` (planned)
run the same prompt through CLI and SDK with pinned seeds and assert
bit-equal MIDI output.

For stochastic generators, scores must be within tolerance rather
than bit-equal, but the seed determines identical IR-level structure.

## What Is NOT the Same

- **Latency**: SDK has lower latency (no subprocess overhead)
- **Session persistence**: SDK supports session resume; CLI does not
- **Streaming**: SDK streams typed events; CLI prints text
- **Permission model**: SDK uses `can_use_tool` callback; CLI uses terminal
