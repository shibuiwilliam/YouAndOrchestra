"""Pydantic input models for YaO MCP tools.

Each model validates the arguments a tool receives from the agent.
These models are used as ``input_schema`` for the ``@tool`` decorator.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComposeInput(BaseModel):
    """Input for yao_compose — single-pass composition from a YAML spec."""

    spec_path: str = Field(..., description="Path to composition.yaml")


class ConductInput(BaseModel):
    """Input for yao_conduct — full generate-evaluate-adapt loop."""

    spec_or_desc: str = Field(
        ...,
        description="Path to composition.yaml or a natural-language description",
    )
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of generation rounds",
    )
    is_description: bool = Field(
        default=False,
        description="True if spec_or_desc is a natural-language description",
    )


class CritiqueInput(BaseModel):
    """Input for yao_critique — adversarial review of an iteration."""

    iteration_path: str = Field(
        ...,
        description="Path to the iteration directory to critique",
    )


class RegenerateSectionInput(BaseModel):
    """Input for yao_regenerate_section — replace one section of a composition."""

    project: str = Field(..., description="Project name")
    section: str = Field(..., description="Section name to regenerate")
    seed: int | None = Field(
        default=None,
        description="Optional random seed for reproducibility",
    )


class RenderAudioInput(BaseModel):
    """Input for yao_render_audio — MIDI to WAV rendering."""

    midi_path: str = Field(..., description="Path to the input MIDI file")
    soundfont: str | None = Field(
        default=None,
        description="Path to a SoundFont file (auto-detected if not provided)",
    )


class EvaluateInput(BaseModel):
    """Input for yao_evaluate — quality evaluation of an iteration."""

    iteration_path: str = Field(
        ...,
        description="Path to the iteration directory to evaluate",
    )


class DiffInput(BaseModel):
    """Input for yao_diff — compare two iterations."""

    iter_a: str = Field(..., description="Path to the first iteration directory")
    iter_b: str = Field(..., description="Path to the second iteration directory")


class ExplainInput(BaseModel):
    """Input for yao_explain — provenance query."""

    query: str = Field(..., description="Natural-language query about a decision")
    iteration_path: str | None = Field(
        default=None,
        description="Optional path to scope the query to a specific iteration",
    )


class ValidateSpecInput(BaseModel):
    """Input for yao_validate_spec — spec validation."""

    spec_path: str = Field(..., description="Path to the spec file to validate")


class LoadSpecInput(BaseModel):
    """Input for yao_load_spec — load and parse a spec."""

    spec_path: str = Field(..., description="Path to the spec file to load")


class NewProjectInput(BaseModel):
    """Input for yao_new_project — create a new project."""

    name: str = Field(..., description="Project name (used as directory name)")
    from_template: str | None = Field(
        default=None,
        description="Template name to copy from specs/templates/",
    )


class ListIterationsInput(BaseModel):
    """Input for yao_list_iterations — list all iterations for a project."""

    project: str = Field(..., description="Project name")


class ReadIterationInput(BaseModel):
    """Input for yao_read_iteration — read iteration details."""

    project: str = Field(..., description="Project name")
    iteration: str = Field(
        ...,
        description="Iteration name (e.g., 'v001')",
    )


class ArchLintInput(BaseModel):
    """Input for yao_arch_lint — run architecture lint."""


class RunTestsInput(BaseModel):
    """Input for yao_run_tests — run test suite."""

    target: str | None = Field(
        default=None,
        description="Test target (e.g., 'tests/unit/' or a specific test file)",
    )
