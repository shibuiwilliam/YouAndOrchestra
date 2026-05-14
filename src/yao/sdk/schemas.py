"""JSON Schema definitions for structured SDK outputs.

These Pydantic models are converted to JSON Schema for use with the
``output_format`` parameter of the Claude Agent SDK, guaranteeing
well-typed results that front-ends consume directly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CritiqueIssue(BaseModel):
    """A single issue found by the Adversarial Critic."""

    severity: Literal["critical", "major", "minor", "suggestion"]
    category: Literal["structure", "melody", "harmony", "rhythm", "emotion", "analysis"]
    location: str = Field(..., description="e.g., 'bar 12, soprano'")
    description: str
    suggestion: str | None = None


class CritiqueReport(BaseModel):
    """Structured output of the /critique command."""

    iteration_path: str
    overall_summary: str
    issues: list[CritiqueIssue]


class ConductorIteration(BaseModel):
    """Summary of one iteration within a conduct loop."""

    iteration_id: str
    evaluation_scores: dict[str, float]
    pass_status: bool
    adaptation_applied: str | None
    timestamp_ms: int


class ConductReport(BaseModel):
    """Structured output of the /conduct command."""

    project: str
    iterations: list[ConductorIteration]
    final_iteration_path: str
    pass_rate: float
    total_duration_ms: int


class EvaluationScoreSchema(BaseModel):
    """One evaluation metric in a structured evaluation report."""

    dimension: str
    metric: str
    score: float
    target: float
    tolerance: float
    passed: bool


class EvaluationReport(BaseModel):
    """Structured output of the /evaluate command."""

    title: str
    scores: list[EvaluationScoreSchema]
    pass_rate: float
    quality_score: float
