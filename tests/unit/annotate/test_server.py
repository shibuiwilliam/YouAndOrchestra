"""Tests for Annotation server endpoints."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from yao.annotate.server import create_app  # noqa: E402


@pytest.fixture()
def iteration_dir(tmp_path: Path) -> Path:
    """Create a mock iteration directory with a WAV file."""
    d = tmp_path / "v001"
    d.mkdir()
    # Create a short WAV
    sr = 44100
    audio = np.zeros(sr, dtype=np.float32)
    sf.write(str(d / "full.wav"), audio, sr)
    return d


@pytest.fixture()
def client(iteration_dir: Path) -> TestClient:
    """Create a test client for the annotation app."""
    app = create_app(iteration_dir)
    return TestClient(app)


class TestServerEndpoints:
    def test_index_returns_html(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "YaO Annotation" in resp.text

    def test_post_annotation_saves(self, client: TestClient, iteration_dir: Path) -> None:
        resp = client.post(
            "/annotations",
            json={
                "time_start_sec": 1.0,
                "time_end_sec": 3.0,
                "sentiment": "positive",
                "tags": ["good_melody"],
                "comment": "Nice!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "saved"

        # Verify file was written
        ann_path = iteration_dir / "annotations.json"
        assert ann_path.exists()

    def test_get_annotations_returns_saved(self, client: TestClient) -> None:
        # Save one first
        client.post(
            "/annotations",
            json={
                "time_start_sec": 0.0,
                "time_end_sec": 2.0,
                "sentiment": "negative",
                "tags": ["too_loud"],
            },
        )
        resp = client.get("/annotations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["annotations"]) >= 1

    def test_post_invalid_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/annotations",
            json={
                "time_start_sec": 0.0,
                # Missing required fields
            },
        )
        assert resp.status_code == 422
