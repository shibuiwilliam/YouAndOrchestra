"""Tests for yao.sdk.schemas — JSON Schema output models."""

from __future__ import annotations

from yao.sdk.schemas import (
    ConductorIteration,
    ConductReport,
    CritiqueIssue,
    CritiqueReport,
    EvaluationReport,
    EvaluationScoreSchema,
)


class TestCritiqueIssue:
    def test_valid(self) -> None:
        issue = CritiqueIssue(
            severity="major",
            category="harmony",
            location="bar 12, soprano",
            description="parallel fifths",
            suggestion="use contrary motion",
        )
        assert issue.severity == "major"
        assert issue.suggestion == "use contrary motion"

    def test_json_schema(self) -> None:
        schema = CritiqueIssue.model_json_schema()
        assert "properties" in schema
        assert "severity" in schema["properties"]


class TestCritiqueReport:
    def test_valid(self) -> None:
        report = CritiqueReport(
            iteration_path="v001",
            overall_summary="Good but needs work",
            issues=[
                CritiqueIssue(
                    severity="minor",
                    category="melody",
                    location="bar 1",
                    description="monotonic",
                ),
            ],
        )
        assert len(report.issues) == 1

    def test_json_schema_generation(self) -> None:
        schema = CritiqueReport.model_json_schema()
        assert schema["type"] == "object"
        assert "issues" in schema["properties"]


class TestConductReport:
    def test_valid(self) -> None:
        report = ConductReport(
            project="test",
            iterations=[
                ConductorIteration(
                    iteration_id="v001",
                    evaluation_scores={"melody": 0.8},
                    pass_status=True,
                    adaptation_applied=None,
                    timestamp_ms=1000,
                ),
            ],
            final_iteration_path="v001",
            pass_rate=1.0,
            total_duration_ms=5000,
        )
        assert report.pass_rate == 1.0


class TestEvaluationReport:
    def test_valid(self) -> None:
        report = EvaluationReport(
            title="test",
            scores=[
                EvaluationScoreSchema(
                    dimension="melody",
                    metric="range_fit",
                    score=0.9,
                    target=0.8,
                    tolerance=0.1,
                    passed=True,
                ),
            ],
            pass_rate=1.0,
            quality_score=8.5,
        )
        assert report.quality_score == 8.5
