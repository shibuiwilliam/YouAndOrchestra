"""Tests for Annotation and AnnotationFile models."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.reflect.annotation import Annotation, AnnotationFile


class TestAnnotationModel:
    def test_valid_annotation(self) -> None:
        a = Annotation(
            time_start_sec=12.4,
            time_end_sec=14.8,
            sentiment="positive",
            tags=["memorable_motif", "good_dynamics"],
        )
        assert a.sentiment == "positive"
        assert len(a.tags) == 2

    def test_invalid_sentiment_raises(self) -> None:
        with pytest.raises(ValueError):
            Annotation(
                time_start_sec=0.0,
                time_end_sec=1.0,
                sentiment="amazing",  # type: ignore[arg-type]
                tags=[],
            )

    def test_empty_tags_ok(self) -> None:
        a = Annotation(
            time_start_sec=0.0,
            time_end_sec=5.0,
            sentiment="neutral",
            tags=[],
        )
        assert a.tags == []

    def test_with_comment(self) -> None:
        a = Annotation(
            time_start_sec=0.0,
            time_end_sec=2.0,
            sentiment="negative",
            tags=["too_busy"],
            comment="The strings are too loud here",
        )
        assert a.comment == "The strings are too loud here"


class TestAnnotationFile:
    def test_empty_file(self) -> None:
        af = AnnotationFile()
        assert af.annotations == []

    def test_round_trip(self, tmp_path: Path) -> None:
        af = AnnotationFile(
            iteration="v003",
            annotations=[
                Annotation(
                    time_start_sec=0.0,
                    time_end_sec=5.0,
                    sentiment="positive",
                    tags=["good"],
                ),
                Annotation(
                    time_start_sec=10.0,
                    time_end_sec=15.0,
                    sentiment="negative",
                    tags=["muddy"],
                ),
            ],
        )
        path = tmp_path / "annotations.json"
        af.save(path)
        assert path.exists()

        loaded = AnnotationFile.load(path)
        assert len(loaded.annotations) == 2
        assert loaded.iteration == "v003"
        assert loaded.annotations[0].sentiment == "positive"

    def test_load_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        loaded = AnnotationFile.load(tmp_path / "missing.json")
        assert loaded.annotations == []

    def test_save_sets_timestamp(self, tmp_path: Path) -> None:
        af = AnnotationFile(iteration="v001")
        path = tmp_path / "ts_test.json"
        af.save(path)
        loaded = AnnotationFile.load(path)
        assert loaded.timestamp_iso != ""
