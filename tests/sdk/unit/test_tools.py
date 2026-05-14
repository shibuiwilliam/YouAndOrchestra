"""Tests for yao.sdk.tools — Pydantic input model validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from yao.sdk.tools import (
    ArchLintInput,
    ComposeInput,
    ConductInput,
    CritiqueInput,
    DiffInput,
    EvaluateInput,
    ExplainInput,
    ListIterationsInput,
    LoadSpecInput,
    NewProjectInput,
    ReadIterationInput,
    RegenerateSectionInput,
    RenderAudioInput,
    RunTestsInput,
    ValidateSpecInput,
)


class TestComposeInput:
    def test_valid(self) -> None:
        inp = ComposeInput(spec_path="specs/projects/test/composition.yaml")
        assert inp.spec_path == "specs/projects/test/composition.yaml"

    def test_missing_required(self) -> None:
        with pytest.raises(ValidationError):
            ComposeInput()  # type: ignore[call-arg]


class TestConductInput:
    def test_defaults(self) -> None:
        inp = ConductInput(spec_or_desc="a calm piano piece")
        assert inp.max_iterations == 3
        assert inp.is_description is False

    def test_max_iterations_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ConductInput(spec_or_desc="test", max_iterations=0)
        with pytest.raises(ValidationError):
            ConductInput(spec_or_desc="test", max_iterations=21)

    def test_valid_description(self) -> None:
        inp = ConductInput(
            spec_or_desc="a calm piano piece",
            max_iterations=5,
            is_description=True,
        )
        assert inp.is_description is True
        assert inp.max_iterations == 5


class TestCritiqueInput:
    def test_valid(self) -> None:
        inp = CritiqueInput(iteration_path="outputs/projects/test/iterations/v001")
        assert inp.iteration_path == "outputs/projects/test/iterations/v001"


class TestRegenerateSectionInput:
    def test_valid(self) -> None:
        inp = RegenerateSectionInput(project="test", section="bridge")
        assert inp.project == "test"
        assert inp.section == "bridge"
        assert inp.seed is None

    def test_with_seed(self) -> None:
        inp = RegenerateSectionInput(project="test", section="chorus", seed=42)
        assert inp.seed == 42


class TestRenderAudioInput:
    def test_valid(self) -> None:
        inp = RenderAudioInput(midi_path="test.mid")
        assert inp.soundfont is None


class TestEvaluateInput:
    def test_valid(self) -> None:
        inp = EvaluateInput(iteration_path="outputs/projects/test/iterations/v001")
        assert inp.iteration_path.endswith("v001")


class TestDiffInput:
    def test_valid(self) -> None:
        inp = DiffInput(iter_a="v001", iter_b="v002")
        assert inp.iter_a == "v001"


class TestExplainInput:
    def test_valid(self) -> None:
        inp = ExplainInput(query="why was the key changed?")
        assert inp.iteration_path is None


class TestValidateSpecInput:
    def test_valid(self) -> None:
        inp = ValidateSpecInput(spec_path="specs/projects/test/composition.yaml")
        assert inp.spec_path.endswith(".yaml")


class TestLoadSpecInput:
    def test_valid(self) -> None:
        inp = LoadSpecInput(spec_path="test.yaml")
        assert inp.spec_path == "test.yaml"


class TestNewProjectInput:
    def test_valid(self) -> None:
        inp = NewProjectInput(name="my-song")
        assert inp.from_template is None

    def test_with_template(self) -> None:
        inp = NewProjectInput(name="my-song", from_template="ambient")
        assert inp.from_template == "ambient"


class TestListIterationsInput:
    def test_valid(self) -> None:
        inp = ListIterationsInput(project="test")
        assert inp.project == "test"


class TestReadIterationInput:
    def test_valid(self) -> None:
        inp = ReadIterationInput(project="test", iteration="v001")
        assert inp.iteration == "v001"


class TestArchLintInput:
    def test_valid(self) -> None:
        inp = ArchLintInput()
        assert inp is not None


class TestRunTestsInput:
    def test_defaults(self) -> None:
        inp = RunTestsInput()
        assert inp.target is None

    def test_with_target(self) -> None:
        inp = RunTestsInput(target="tests/unit/")
        assert inp.target == "tests/unit/"
