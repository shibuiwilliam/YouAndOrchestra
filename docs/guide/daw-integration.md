# DAW Integration

YaO can integrate with Digital Audio Workstations via the MCP bridge
and direct file export.

## Reaper Integration

### RPP Export

YaO can export compositions directly to Reaper RPP format:

```python
from yao.render.daw.reaper_writer import write_rpp
write_rpp(score_ir, Path("output.rpp"))
```

### TCP Control

When Reaper is running with its ReaScript TCP server enabled, YaO can
push and pull MIDI in real-time:

```python
from yao.render.daw.mcp_bridge import DAWMCPBridge

bridge = DAWMCPBridge()
status = bridge.connect("reaper")

if status.connected:
    bridge.push_score(score_ir)
    # ... edit in Reaper ...
    midi_path = bridge.pull_changes()
```

### Setting Up Reaper TCP

1. Open Reaper
2. Actions > Show Action List
3. Search for "ReaScript" > Enable TCP server
4. Default: `127.0.0.1:8800`

## MCP Server

YaO also exposes 15 tools via an MCP server for Claude Agent SDK integration:

```bash
yao serve --host 0.0.0.0 --port 8765
```

Tools include: compose, conduct, critique, evaluate, diff, explain,
validate, render, regenerate-section, and more.

## Workflow

1. Compose in YaO: `yao compose spec.yaml`
2. Push to DAW: use the bridge or export MIDI/RPP
3. Edit in DAW (mix, add effects, record vocals)
4. Pull back to YaO for evaluation: `yao evaluate`
5. Iterate with the Conductor: `yao conduct`

## Supported DAWs

| DAW | Status | Method |
|-----|--------|--------|
| Reaper | Supported | RPP export + TCP control |
| Others | File exchange | Export MIDI, import in DAW |
