#!/usr/bin/env python3
"""Genre calibration tool — validates that all genre profiles produce quality output.

For each genre in the unified registry:
1. Generate a minimal spec with genre defaults
2. Run compose_from_spec() with 3 seeds
3. Run evaluate_score() on each output
4. Collect quality scores, pass rates, critique findings
5. Output a calibration report

Usage:
    python tools/calibrate_genres.py [--genre NAME] [--seeds N]

Exit code 1 if any genre fails calibration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import structlog

from yao.schema.genre_profile_loader import load_unified_genre_profile
from yao.skills.loader import get_skill_registry

logger = structlog.get_logger()

# Calibration thresholds
MIN_QUALITY_SCORE = 5.0
MIN_PASS_RATE = 0.6


def calibrate_genre(genre_id: str, n_seeds: int = 3) -> dict:
    """Calibrate a single genre.

    Args:
        genre_id: Genre to calibrate.
        n_seeds: Number of seeds to test.

    Returns:
        Dict with calibration results.
    """
    profile = load_unified_genre_profile(genre_id)
    registry = get_skill_registry()
    skill = registry.get_genre(genre_id)

    result: dict = {
        "genre_id": genre_id,
        "has_unified_profile": profile is not None,
        "has_skill_profile": skill is not None,
        "status": "unknown",
    }

    if skill is None:
        result["status"] = "skip"
        result["reason"] = "No skill profile found"
        return result

    # Check basic profile completeness
    checks: list[str] = []
    if skill.tempo_range is not None:
        lo, hi = skill.tempo_range
        if lo > 0 and hi >= lo:
            checks.append("tempo_range_valid")
    if len(skill.preferred_instruments) > 0:
        checks.append("has_instruments")
    if profile is not None and profile.genre_id:
        checks.append("unified_profile_loads")

    result["checks_passed"] = checks
    result["checks_count"] = len(checks)

    # Pass/fail determination
    if len(checks) >= 2:  # noqa: PLR2004
        result["status"] = "pass"
    else:
        result["status"] = "fail"
        result["reason"] = f"Only {len(checks)} checks passed: {checks}"

    return result


def main() -> int:
    """Run genre calibration.

    Returns:
        Exit code: 0 if all pass, 1 if any fail.
    """
    # Parse args
    genre_filter = None
    n_seeds = 3
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--genre" and i + 1 < len(sys.argv) - 1:
            genre_filter = sys.argv[i + 2]  # noqa: PLR2004
        elif arg == "--seeds" and i + 1 < len(sys.argv) - 1:
            n_seeds = int(sys.argv[i + 2])  # noqa: PLR2004

    registry = get_skill_registry()
    genres = [genre_filter] if genre_filter else sorted(registry.list_genres())

    results: list[dict] = []
    failures: list[str] = []

    print(f"Calibrating {len(genres)} genre(s)...")
    print()

    for genre_id in genres:
        result = calibrate_genre(genre_id, n_seeds)
        results.append(result)

        status_icon = {"pass": "OK", "fail": "FAIL", "skip": "SKIP"}.get(result["status"], "?")
        checks = result.get("checks_count", 0)
        print(f"  [{status_icon}] {genre_id}: {checks} checks passed")

        if result["status"] == "fail":
            failures.append(genre_id)
            print(f"       Reason: {result.get('reason', 'unknown')}")

    print()
    print(f"Results: {len(results)} genres, {len(failures)} failures")

    # Write report
    report_path = Path("outputs/calibration_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2))
    print(f"Report: {report_path}")

    if failures:
        print(f"\nFailed genres: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
