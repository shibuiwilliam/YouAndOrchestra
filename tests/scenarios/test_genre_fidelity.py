"""Genre normalization and instrumentation fidelity regression test.

Verifies that user prompts like "rock song" correctly resolve to
registered genre IDs with appropriate instrumentation and drums.
Prevents regression to classical-biased default generation.
"""

from __future__ import annotations

import pytest

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.sketch.compiler import SpecCompiler


@pytest.mark.parametrize(
    "prompt,expected_genre,checks",
    [
        (
            "a rock song with electric guitar, energetic",
            "rock_classic",
            {
                "must_have_drums": True,
                "must_contain_inst_family": {"guitar"},
                "tempo_range": (100, 170),
            },
        ),
        (
            "a hip-hop track with a strong beat",
            "hiphop_boom_bap",
            {
                "must_have_drums": True,
                "tempo_range": (70, 120),
            },
        ),
        (
            "a chill lo-fi study beat",
            "lofi_hiphop",
            {
                "must_have_drums": True,
                "tempo_range": (60, 100),
            },
        ),
        (
            "an EDM dance track",
            "electronic_house",
            {
                "must_have_drums": True,
                "tempo_range": (115, 145),
            },
        ),
        (
            "a smooth jazz ballad with saxophone",
            "jazz_ballad",
            {
                "must_contain_inst": {"alto_sax"},
                "tempo_range": (55, 110),
            },
        ),
        (
            "a country song with acoustic guitar",
            "country_traditional",
            {
                "must_contain_inst": {"acoustic_guitar_steel"},
            },
        ),
        (
            "a calm ambient drone",
            "ambient",
            {
                "must_have_drums": False,
            },
        ),
        (
            "a cinematic orchestral piece",
            "cinematic",
            {
                "must_contain_inst": {"strings_ensemble"},
            },
        ),
        (
            "a bossa nova piece",
            "latin_bossa_nova",
            {
                "must_have_drums": True,
            },
        ),
        (
            "a heavy metal track",
            "metal",
            {
                "must_have_drums": True,
                "must_contain_inst_family": {"guitar"},
            },
        ),
        (
            "a funk groove with slap bass",
            "funk_classic",
            {
                "must_have_drums": True,
            },
        ),
        (
            "a reggae song",
            "reggae",
            {
                "must_have_drums": True,
            },
        ),
    ],
)
def test_genre_fidelity(prompt: str, expected_genre: str, checks: dict) -> None:
    """Each genre prompt resolves to correct ID with proper instrumentation."""
    compiler = SpecCompiler()
    spec, trajectory = compiler.compile(prompt, "test-fidelity", language="en")

    # 1. Genre normalization succeeded
    assert spec.genre == expected_genre, (
        f"Genre normalization failed for '{prompt}': got '{spec.genre}', expected '{expected_genre}'"
    )

    # 2. Tempo in range
    if "tempo_range" in checks:
        lo, hi = checks["tempo_range"]
        assert lo <= spec.tempo_bpm <= hi, f"Tempo {spec.tempo_bpm} out of range [{lo}, {hi}] for '{prompt}'"

    # 3. Drums
    has_drums = spec.drums is not None
    if "must_have_drums" in checks:
        if checks["must_have_drums"]:
            assert has_drums, f"'{prompt}' should have drums (genre={expected_genre})"
        else:
            assert not has_drums, f"'{prompt}' should NOT have drums (genre={expected_genre})"

    # 4. Required instruments
    instrument_names = {i.name for i in spec.instruments}
    if "must_contain_inst" in checks:
        for inst in checks["must_contain_inst"]:
            assert inst in instrument_names, f"'{prompt}' missing required instrument '{inst}'. Got: {instrument_names}"

    # 5. Required instrument families
    instrument_families = {INSTRUMENT_RANGES[i.name].family for i in spec.instruments if i.name in INSTRUMENT_RANGES}
    if "must_contain_inst_family" in checks:
        for family in checks["must_contain_inst_family"]:
            assert family in instrument_families, (
                f"'{prompt}' missing required family '{family}'. Got: {instrument_families}"
            )

    # 6. Provenance has genre-related operation
    prov_ops = [r.operation for r in compiler.provenance.records]
    assert any("genre" in op or "drums" in op or "skill" in op for op in prov_ops), (
        f"No genre/drum operation in provenance for '{prompt}'. Got: {prov_ops}"
    )
