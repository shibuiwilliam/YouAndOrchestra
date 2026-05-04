"""A/B Audition server — local FastAPI app for side-by-side comparison.

Endpoints:
- GET /          : A/B comparison UI (HTML)
- GET /audio/a   : Stream iteration A audio
- GET /audio/b   : Stream iteration B audio
- GET /preferences : Load existing preferences
- POST /preferences : Save preference for a section

All data is local. No external services. Preferences feed the Reflection Layer.

Belongs to audition/ package.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse, HTMLResponse

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


@dataclass(frozen=True)
class SectionPreference:
    """User preference for a specific section.

    Attributes:
        section: Section name (e.g. "chorus").
        preferred: Which iteration was preferred ("a" or "b").
        reason: Optional free-text reason.
    """

    section: str
    preferred: str  # "a" or "b"
    reason: str = ""


@dataclass
class AuditionResult:
    """Collection of section-level A/B preferences.

    Attributes:
        project: Project name.
        iteration_a: Version ID of iteration A.
        iteration_b: Version ID of iteration B.
        preferences: List of section preferences.
    """

    project: str
    iteration_a: str
    iteration_b: str
    preferences: list[SectionPreference] = field(default_factory=list)

    def add_preference(self, section: str, preferred: str, reason: str = "") -> None:
        """Record a preference for a section.

        Args:
            section: Section name.
            preferred: "a" or "b".
            reason: Optional reason.
        """
        self.preferences.append(SectionPreference(section=section, preferred=preferred, reason=reason))

    def preferred_count(self) -> dict[str, int]:
        """Count how many sections preferred each iteration.

        Returns:
            Dict with keys "a" and "b" and integer counts.
        """
        counts = {"a": 0, "b": 0}
        for p in self.preferences:
            if p.preferred in counts:
                counts[p.preferred] += 1
        return counts

    def winner(self) -> str | None:
        """Return which iteration was preferred overall.

        Returns:
            "a", "b", or None if tied.
        """
        counts = self.preferred_count()
        if counts["a"] > counts["b"]:
            return "a"
        if counts["b"] > counts["a"]:
            return "b"
        return None

    def save(self, path: Path) -> None:
        """Save preferences to JSON.

        Args:
            path: Output file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "project": self.project,
            "iteration_a": self.iteration_a,
            "iteration_b": self.iteration_b,
            "preferences": [asdict(p) for p in self.preferences],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> AuditionResult:
        """Load preferences from JSON.

        Args:
            path: Input file path.

        Returns:
            AuditionResult instance.
        """
        data = json.loads(path.read_text())
        result = cls(
            project=data["project"],
            iteration_a=data["iteration_a"],
            iteration_b=data["iteration_b"],
        )
        for p in data.get("preferences", []):
            result.preferences.append(SectionPreference(**p))
        return result


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YaO A/B Audition — {project}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }}
        h1 {{ color: #333; }}
        .comparison {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0; }}
        .iteration {{ padding: 1rem; border: 2px solid #ddd; border-radius: 8px; }}
        .iteration h2 {{ margin-top: 0; }}
        .iteration.selected {{ border-color: #4CAF50; background: #f0fff0; }}
        audio {{ width: 100%; margin: 1rem 0; }}
        .section-vote {{ margin: 1rem 0; padding: 0.8rem; background: #f5f5f5; border-radius: 4px; }}
        .vote-buttons {{ display: flex; gap: 1rem; margin-top: 0.5rem; }}
        .vote-btn {{ padding: 0.5rem 1.5rem; border: 1px solid #ccc; border-radius: 4px;
                    cursor: pointer; background: white; }}
        .vote-btn.active {{ background: #4CAF50; color: white; border-color: #4CAF50; }}
        .summary {{ margin-top: 2rem; padding: 1rem; background: #e8f5e9; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>A/B Audition: {project}</h1>
    <p>Comparing <strong>{iter_a}</strong> vs <strong>{iter_b}</strong></p>

    <div class="comparison">
        <div class="iteration" id="iter-a">
            <h2>Iteration A ({iter_a})</h2>
            <audio controls src="/audio/a"></audio>
        </div>
        <div class="iteration" id="iter-b">
            <h2>Iteration B ({iter_b})</h2>
            <audio controls src="/audio/b"></audio>
        </div>
    </div>

    <h2>Section Preferences</h2>
    <div id="sections">
        <p>Listen to both iterations, then choose your preference for each section.</p>
        <div class="section-vote">
            <strong>Overall</strong>
            <div class="vote-buttons">
                <button class="vote-btn" onclick="vote('overall','a',this)">Prefer A</button>
                <button class="vote-btn" onclick="vote('overall','b',this)">Prefer B</button>
            </div>
        </div>
    </div>

    <button onclick="submitAll()" style="margin-top: 1rem; padding: 0.8rem 2rem;
        background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Submit Preferences
    </button>

    <div class="summary" id="result" style="display:none">
        <h3>Preferences saved!</h3>
    </div>

    <script>
        const votes = {{}};
        function vote(section, choice, btn) {{
            votes[section] = choice;
            const siblings = btn.parentElement.querySelectorAll('.vote-btn');
            siblings.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }}
        async function submitAll() {{
            const prefs = Object.entries(votes).map(([section, preferred]) => ({{
                section, preferred, reason: ''
            }}));
            await fetch('/preferences', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(prefs)
            }});
            document.getElementById('result').style.display = 'block';
        }}
    </script>
</body>
</html>"""


def create_audition_app(
    project: str,
    iter_a_path: Path,
    iter_b_path: Path,
    output_path: Path,
) -> Any:
    """Create a FastAPI app for A/B audition.

    Args:
        project: Project name.
        iter_a_path: Path to iteration A audio file.
        iter_b_path: Path to iteration B audio file.
        output_path: Path to save preference results.

    Returns:
        FastAPI app instance.

    Raises:
        ImportError: If FastAPI is not installed.
    """
    if not _HAS_FASTAPI:
        msg = "FastAPI required for audition UI. Install with: pip install yao[annotate]"
        raise ImportError(msg)

    app = FastAPI(title=f"YaO Audition — {project}")
    iter_a = iter_a_path.parent.name
    iter_b = iter_b_path.parent.name

    result = AuditionResult(project=project, iteration_a=iter_a, iteration_b=iter_b)

    @app.get("/", response_class=HTMLResponse)
    def ui() -> str:
        return _HTML_TEMPLATE.format(project=project, iter_a=iter_a, iter_b=iter_b)

    @app.get("/audio/a")
    def audio_a() -> FileResponse:
        if not iter_a_path.exists():
            raise HTTPException(status_code=404, detail="Iteration A audio not found")
        return FileResponse(iter_a_path, media_type="audio/midi")

    @app.get("/audio/b")
    def audio_b() -> FileResponse:
        if not iter_b_path.exists():
            raise HTTPException(status_code=404, detail="Iteration B audio not found")
        return FileResponse(iter_b_path, media_type="audio/midi")

    @app.get("/preferences")
    def get_preferences() -> dict[str, Any]:
        return {
            "project": result.project,
            "iteration_a": result.iteration_a,
            "iteration_b": result.iteration_b,
            "preferences": [asdict(p) for p in result.preferences],
        }

    @app.post("/preferences")
    def save_preferences(prefs: list[dict[str, str]]) -> dict[str, str]:
        for p in prefs:
            result.add_preference(
                section=p.get("section", "overall"),
                preferred=p.get("preferred", "a"),
                reason=p.get("reason", ""),
            )
        result.save(output_path)
        return {"status": "saved", "winner": result.winner() or "tied"}

    return app
