"""Shared test fixtures for YaO tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


@pytest.fixture
def minimal_spec() -> CompositionSpec:
    """A minimal 8-bar, single-piano composition spec."""
    return CompositionSpec(
        title="Test Composition",
        genre="general",
        key="C major",
        tempo_bpm=120.0,
        time_signature="4/4",
        total_bars=8,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
    )


@pytest.fixture
def multi_instrument_spec() -> CompositionSpec:
    """A spec with multiple instruments and sections."""
    return CompositionSpec(
        title="Multi Instrument Test",
        genre="general",
        key="G major",
        tempo_bpm=100.0,
        time_signature="4/4",
        total_bars=16,
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="acoustic_bass", role="bass"),
        ],
        sections=[
            SectionSpec(name="intro", bars=4, dynamics="mp"),
            SectionSpec(name="verse", bars=8, dynamics="mf"),
            SectionSpec(name="outro", bars=4, dynamics="mp"),
        ],
    )


@pytest.fixture
def sample_score_ir() -> ScoreIR:
    """A pre-built ScoreIR with known notes for testing."""
    notes = tuple(
        Note(
            pitch=60 + i,
            start_beat=float(i),
            duration_beats=0.9,
            velocity=80,
            instrument="piano",
        )
        for i in range(8)
    )
    part = Part(instrument="piano", notes=notes)
    section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
    return ScoreIR(
        title="Test Score",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """A temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def spec_template_dir() -> Path:
    """Path to the spec templates directory."""
    return Path("specs/templates")
