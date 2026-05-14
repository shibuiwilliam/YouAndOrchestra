"""
YaO Web App — FastAPI + SSE streaming example.

A browser-based music composition interface backed by YaoAgent.
Shows one progress card per cognitive phase, plus a play button
when audio is ready.

Prerequisites:
    pip install -e ".[sdk]" fastapi uvicorn sse-starlette

Run:
    uvicorn examples.sdk.web.app:app --reload
"""

from __future__ import annotations

import json

from yao.sdk import YaoAgent
from yao.sdk.events import (
    AudioReadyEvent,
    ConductorFinishedEvent,
    IterationCompletedEvent,
    PhaseStartedEvent,
    YaoEvent,
)

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from sse_starlette.sse import EventSourceResponse
except ImportError as _exc:
    raise ImportError("Install fastapi, uvicorn, sse-starlette for the web example") from _exc

app = FastAPI(title="YaO Web Composer")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """<!DOCTYPE html>
<html>
<head><title>YaO Web Composer</title></head>
<body>
<h1>YaO Web Composer</h1>
<input id="desc" placeholder="Describe your music..." style="width:400px"/>
<button onclick="compose()">Compose</button>
<div id="events"></div>
<script>
function compose() {
  const desc = document.getElementById('desc').value;
  const es = new EventSource('/compose?desc=' + encodeURIComponent(desc));
  const div = document.getElementById('events');
  div.innerHTML = '';
  es.onmessage = (e) => {
    const p = document.createElement('p');
    p.textContent = e.data;
    div.appendChild(p);
  };
  es.onerror = () => es.close();
}
</script>
</body>
</html>"""


@app.get("/compose")
async def compose(desc: str = "a calm piano piece") -> EventSourceResponse:
    async def event_stream() -> None:
        async with YaoAgent(project="web-demo") as agent:
            async for event in agent.conduct(desc, max_iterations=2):
                data = _event_to_json(event)
                yield {"data": data}  # type: ignore[misc]

    return EventSourceResponse(event_stream())


def _event_to_json(event: YaoEvent) -> str:
    info: dict[str, object] = {"type": type(event).__name__}
    if isinstance(event, PhaseStartedEvent):
        info["phase"] = event.phase
    elif isinstance(event, IterationCompletedEvent):
        info["iteration"] = event.iteration
        info["passed"] = event.pass_status
    elif isinstance(event, AudioReadyEvent):
        info["wav_path"] = event.wav_path
    elif isinstance(event, ConductorFinishedEvent):
        info["final"] = event.final_iteration_path
    return json.dumps(info)
