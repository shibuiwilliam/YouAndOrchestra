"""Tests for yao.sdk.results — typed result objects."""

from __future__ import annotations

from yao.sdk.results import (
    ComposeResult,
    ConductResult,
    CritiqueResult,
    DiffResult,
    EvaluateResult,
    ExplainResult,
    RegenerateSectionResult,
    RenderResult,
)


class TestResults:
    def test_compose_result(self) -> None:
        r = ComposeResult(
            iteration_path="v001",
            midi_path="full.mid",
            evaluation={"pass_rate": 0.8},
            provenance_entries=5,
        )
        assert r.provenance_entries == 5

    def test_conduct_result(self) -> None:
        r = ConductResult(
            final_iteration_path="v003",
            iterations=3,
            pass_rate=0.9,
            quality_score=7.5,
        )
        assert r.iterations == 3

    def test_critique_result(self) -> None:
        r = CritiqueResult(
            severity_counts={"critical": 0, "major": 2},
        )
        assert r.severity_counts["major"] == 2

    def test_regenerate_section_result(self) -> None:
        r = RegenerateSectionResult(section_regenerated="bridge")
        assert r.section_regenerated == "bridge"

    def test_render_result(self) -> None:
        r = RenderResult(wav_path="audio.wav", duration_seconds=90.0)
        assert r.duration_seconds == 90.0

    def test_diff_result(self) -> None:
        r = DiffResult(summary="5 changes", added=3, removed=1, modified=1)
        assert r.added + r.removed + r.modified == 5

    def test_evaluate_result(self) -> None:
        r = EvaluateResult(pass_rate=0.85, passed=True)
        assert r.passed is True

    def test_explain_result(self) -> None:
        r = ExplainResult(query="why key change?", chain=[{"op": "modulate"}])
        assert len(r.chain) == 1
