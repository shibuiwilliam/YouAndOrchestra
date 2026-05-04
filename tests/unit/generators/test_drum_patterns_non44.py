"""Tests for non-4/4 drum patterns."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yao.ir.timing import beats_per_bar_from_sig, parse_time_signature

DRUM_PATTERNS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "drum_patterns"

NON_44_PATTERNS = [
    "waltz_3_4",
    "compound_6_8",
    "take_five_5_4",
    "bulgarian_7_8",
    "bartok_7_8",
]


@pytest.fixture(params=NON_44_PATTERNS)
def pattern_data(request: pytest.FixtureRequest) -> dict:
    """Load a non-4/4 drum pattern YAML."""
    yaml_path = DRUM_PATTERNS_DIR / f"{request.param}.yaml"
    assert yaml_path.exists(), f"Pattern file not found: {yaml_path}"
    data = yaml.safe_load(yaml_path.read_text())
    data["_name"] = request.param
    return data


class TestNon44DrumPatterns:
    """Verify non-4/4 drum patterns are well-formed."""

    def test_pattern_loads(self, pattern_data: dict) -> None:
        assert "id" in pattern_data
        assert "time_signature" in pattern_data
        assert "hits" in pattern_data

    def test_time_signature_is_not_4_4(self, pattern_data: dict) -> None:
        ts = pattern_data["time_signature"]
        assert ts != "4/4", f"Pattern {pattern_data['_name']} is 4/4"

    def test_hits_within_bar_duration(self, pattern_data: dict) -> None:
        ts = pattern_data["time_signature"]
        num, den = parse_time_signature(ts)
        bpb = beats_per_bar_from_sig(num, den)
        bars = pattern_data.get("bars_per_pattern", 1)
        max_beat = bpb * bars

        for hit in pattern_data["hits"]:
            assert hit["time_beats"] < max_beat, (
                f"Hit at beat {hit['time_beats']} exceeds bar duration {max_beat} "
                f"for {ts} in pattern {pattern_data['_name']}"
            )
            assert hit["time_beats"] >= 0.0

    def test_has_kick_on_downbeat(self, pattern_data: dict) -> None:
        """Every pattern should have a kick or strong hit on beat 0."""
        downbeat_hits = [h for h in pattern_data["hits"] if h["time_beats"] == 0.0]
        assert len(downbeat_hits) > 0, f"No hits on downbeat in {pattern_data['_name']}"

    def test_velocity_in_range(self, pattern_data: dict) -> None:
        for hit in pattern_data["hits"]:
            assert 1 <= hit["velocity"] <= 127, f"Velocity {hit['velocity']} out of range in {pattern_data['_name']}"


class TestSpecificMeters:
    """Verify specific meter expectations."""

    def test_waltz_is_3_4(self) -> None:
        data = yaml.safe_load((DRUM_PATTERNS_DIR / "waltz_3_4.yaml").read_text())
        assert data["time_signature"] == "3/4"

    def test_compound_is_6_8(self) -> None:
        data = yaml.safe_load((DRUM_PATTERNS_DIR / "compound_6_8.yaml").read_text())
        assert data["time_signature"] == "6/8"

    def test_take_five_is_5_4(self) -> None:
        data = yaml.safe_load((DRUM_PATTERNS_DIR / "take_five_5_4.yaml").read_text())
        assert data["time_signature"] == "5/4"

    def test_bulgarian_is_7_8(self) -> None:
        data = yaml.safe_load((DRUM_PATTERNS_DIR / "bulgarian_7_8.yaml").read_text())
        assert data["time_signature"] == "7/8"

    def test_bartok_is_7_8(self) -> None:
        data = yaml.safe_load((DRUM_PATTERNS_DIR / "bartok_7_8.yaml").read_text())
        assert data["time_signature"] == "7/8"

    def test_total_drum_patterns_at_least_15(self) -> None:
        yaml_files = list(DRUM_PATTERNS_DIR.glob("*.yaml"))
        assert len(yaml_files) >= 15, f"Expected >=15 drum patterns, got {len(yaml_files)}"
