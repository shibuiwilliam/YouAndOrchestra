"""Annotation server — local FastAPI app for time-tagged feedback.

Endpoints:
- GET /          : Annotation UI (HTML)
- GET /audio     : Stream the iteration's WAV file
- GET /annotations : Load existing annotations
- POST /annotations : Save annotations

All data is local. No external services.

Belongs to annotate/ package.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from yao.reflect.annotation import Annotation, AnnotationFile

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse, HTMLResponse

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YaO Annotation — {iteration}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
        h1 {{ color: #333; }}
        .controls {{ margin: 1rem 0; padding: 1rem; background: #f5f5f5; border-radius: 8px; }}
        label {{ display: block; margin: 0.5rem 0 0.2rem; font-weight: bold; }}
        input, select, textarea {{ width: 100%; padding: 0.4rem; box-sizing: border-box; }}
        button {{ padding: 0.6rem 1.5rem; background: #2563eb; color: white; border: none;
                  border-radius: 4px; cursor: pointer; margin-top: 0.5rem; }}
        button:hover {{ background: #1d4ed8; }}
        .annotation-list {{ margin-top: 1rem; }}
        .annotation-item {{ padding: 0.5rem; margin: 0.3rem 0; background: #eef; border-radius: 4px; }}
        .positive {{ border-left: 4px solid #22c55e; }}
        .negative {{ border-left: 4px solid #ef4444; }}
        .neutral {{ border-left: 4px solid #94a3b8; }}
        audio {{ width: 100%; margin: 1rem 0; }}
        #status {{ color: #666; margin-top: 0.5rem; }}
    </style>
</head>
<body>
    <h1>YaO Annotation: {iteration}</h1>
    <audio id="player" controls src="/audio"></audio>

    <div class="controls">
        <label>Start (sec): <input type="number" id="start" step="0.1" value="0"></label>
        <label>End (sec): <input type="number" id="end" step="0.1" value="5"></label>
        <label>Sentiment:
            <select id="sentiment">
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="neutral">Neutral</option>
            </select>
        </label>
        <label>Tags (comma-separated):
            <input type="text" id="tags" placeholder="memorable_motif, good_dynamics, too_busy">
        </label>
        <label>Comment: <textarea id="comment" rows="2"></textarea></label>
        <button onclick="saveAnnotation()">Save Annotation</button>
        <div id="status"></div>
    </div>

    <div class="annotation-list" id="annotations"></div>

    <script>
    async function loadAnnotations() {{
        const resp = await fetch('/annotations');
        const data = await resp.json();
        const list = document.getElementById('annotations');
        list.innerHTML = '<h3>Annotations (' + data.annotations.length + ')</h3>';
        data.annotations.forEach(a => {{
            const div = document.createElement('div');
            div.className = 'annotation-item ' + a.sentiment;
            div.textContent = a.time_start_sec.toFixed(1) + 's-' + a.time_end_sec.toFixed(1)
                + 's [' + a.sentiment + '] ' + a.tags.join(', ')
                + (a.comment ? ' — ' + a.comment : '');
            list.appendChild(div);
        }});
    }}
    async function saveAnnotation() {{
        const body = {{
            time_start_sec: parseFloat(document.getElementById('start').value),
            time_end_sec: parseFloat(document.getElementById('end').value),
            sentiment: document.getElementById('sentiment').value,
            tags: document.getElementById('tags').value.split(',').map(s => s.trim()).filter(s => s),
            comment: document.getElementById('comment').value,
        }};
        const resp = await fetch('/annotations', {{
            method: 'POST', headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(body),
        }});
        if (resp.ok) {{
            document.getElementById('status').textContent = 'Saved!';
            loadAnnotations();
        }} else {{
            document.getElementById('status').textContent = 'Error: ' + resp.statusText;
        }}
    }}
    loadAnnotations();
    </script>
</body>
</html>"""


def create_app(iteration_dir: Path) -> Any:
    """Create a FastAPI annotation app for an iteration directory.

    Args:
        iteration_dir: Path to the iteration directory (e.g., outputs/.../v001).

    Returns:
        FastAPI application instance.

    Raises:
        ImportError: If fastapi is not installed.
    """
    if not _HAS_FASTAPI:
        msg = "FastAPI not installed. Install with: pip install yao[annotate]"
        raise ImportError(msg)

    app = FastAPI(title="YaO Annotation")
    annotations_path = iteration_dir / "annotations.json"
    iteration_name = iteration_dir.name

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        """Serve the annotation UI."""
        return _HTML_TEMPLATE.format(iteration=iteration_name)

    @app.get("/audio")
    async def audio() -> FileResponse:
        """Serve the iteration's audio file."""
        # Look for WAV or MIDI
        for ext in ("*.wav", "*.mid"):
            files = sorted(iteration_dir.glob(ext))
            if files:
                return FileResponse(files[0], media_type="audio/wav")
        raise HTTPException(status_code=404, detail="No audio file found")

    @app.get("/annotations")
    async def get_annotations() -> dict[str, Any]:
        """Load existing annotations."""
        af = AnnotationFile.load(annotations_path)
        return af.model_dump()

    @app.post("/annotations")
    async def post_annotation(annotation: Annotation) -> dict[str, str]:
        """Save a new annotation."""
        af = AnnotationFile.load(annotations_path)
        af.annotations.append(annotation)
        af.iteration = iteration_name
        af.save(annotations_path)
        return {"status": "saved", "count": str(len(af.annotations))}

    return app
