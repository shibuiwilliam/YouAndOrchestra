"""Integration tests for SpecCompiler Japanese input — Wave 1.3.

20 Japanese description samples testing that the keyword compiler
produces musically reasonable specs (key, tempo, instruments, duration).
"""

from __future__ import annotations

import pytest

from yao.sketch.compiler import SpecCompiler


@pytest.fixture
def compiler() -> SpecCompiler:
    return SpecCompiler()


# ── Test data: 20 Japanese samples ──────────────────────────────────────

_JA_SAMPLES = [
    {
        "desc": "雨の夜のカフェで聴きたい少し切ないピアノ曲、90秒",
        "project": "rain-cafe",
        "expect_mode": "minor",
        "expect_tempo_range": (60, 110),
        "expect_instruments": ["piano"],
        "expect_duration": 90,
    },
    {
        "desc": "梅雨明けの朝の喜び、明るく爽やか、3分",
        "project": "summer-morning",
        "expect_mode": "major",
        "expect_tempo_range": (90, 130),
        "expect_instruments": None,
        "expect_duration": 180,
    },
    {
        "desc": "夕暮れの公園、ノスタルジー、控えめなピアノとチェロ",
        "project": "sunset-park",
        "expect_mode": "minor",
        "expect_tempo_range": (70, 110),
        "expect_instruments": ["piano", "cello"],
        "expect_duration": None,
    },
    {
        "desc": "壮大なオーケストラ、映画のクライマックスシーン",
        "project": "epic-climax",
        "expect_mode": "minor",
        "expect_tempo_range": (80, 145),
        "expect_instruments": ["strings_ensemble"],
        "expect_duration": None,
    },
    {
        "desc": "穏やかで温かいギターの曲",
        "project": "warm-guitar",
        "expect_mode": "major",
        "expect_tempo_range": (60, 95),
        "expect_instruments": ["acoustic_guitar_nylon"],
        "expect_duration": None,
    },
    {
        "desc": "激しいピアノソロ、怒りと情熱",
        "project": "angry-piano",
        "expect_mode": "minor",
        "expect_tempo_range": (120, 180),
        "expect_instruments": ["piano"],
        "expect_duration": None,
    },
    {
        "desc": "神秘的な雰囲気のシンセとピアノ、60秒",
        "project": "mysterious-synth",
        "expect_mode": "minor",
        "expect_tempo_range": (60, 100),
        "expect_instruments": ["piano"],
        "expect_duration": 60,
    },
    {
        "desc": "幸福感あふれる明るい曲、120 BPM",
        "project": "happy-bright",
        "expect_mode": "major",
        "expect_tempo_range": (118, 122),
        "expect_instruments": None,
        "expect_duration": None,
    },
    {
        "desc": "悲しいバイオリンとチェロのデュエット、ゆっくり",
        "project": "sad-duet",
        "expect_mode": "minor",
        "expect_tempo_range": (55, 85),
        "expect_instruments": ["violin", "cello"],
        "expect_duration": None,
    },
    {
        "desc": "癒しのアンビエント、静かで清らかな",
        "project": "healing-ambient",
        "expect_mode": "major",
        "expect_tempo_range": (55, 90),
        "expect_instruments": None,
        "expect_duration": None,
    },
    {
        "desc": "勇壮な行進曲、力強く華やか",
        "project": "march",
        "expect_mode": "major",
        "expect_tempo_range": (110, 150),
        "expect_instruments": None,
        "expect_duration": None,
    },
    {
        "desc": "儚い記憶、哀愁漂うピアノ独奏",
        "project": "fleeting-memory",
        "expect_mode": "minor",
        "expect_tempo_range": (60, 100),
        "expect_instruments": ["piano"],
        "expect_duration": None,
    },
    {
        "desc": "ドラマチックなオーケストラ、緊張から解放へ",
        "project": "dramatic-release",
        "expect_mode": "minor",
        "expect_tempo_range": (80, 145),
        "expect_instruments": ["strings_ensemble"],
        "expect_duration": None,
    },
    {
        "desc": "のどかな田園風景、フルートとギター、2分",
        "project": "pastoral",
        "expect_mode": "major",
        "expect_tempo_range": (65, 95),
        "expect_instruments": ["flute", "acoustic_guitar_nylon"],
        "expect_duration": 120,
    },
    {
        "desc": "夢幻的なピアノ曲、幻想的で甘美",
        "project": "dreamscape",
        "expect_mode": "major",
        "expect_tempo_range": (60, 100),
        "expect_instruments": ["piano"],
        "expect_duration": None,
    },
    {
        "desc": "情熱的なサックスとピアノのジャズ",
        "project": "passionate-jazz",
        "expect_mode": "minor",
        "expect_tempo_range": (100, 150),
        "expect_instruments": ["saxophone_alto", "piano"],
        "expect_duration": None,
    },
    {
        "desc": "不安と恐怖の弦楽四重奏、スロー",
        "project": "horror-strings",
        "expect_mode": "minor",
        "expect_tempo_range": (55, 85),
        "expect_instruments": ["strings_ensemble"],
        "expect_duration": None,
    },
    {
        "desc": "希望に満ちた朝、元気で楽しいピアノ",
        "project": "hopeful-morning",
        "expect_mode": "major",
        "expect_tempo_range": (100, 150),
        "expect_instruments": ["piano"],
        "expect_duration": None,
    },
    {
        "desc": "懐かしい夏の日の思い出、ギター弾き語り",
        "project": "summer-memory",
        "expect_mode": "major",
        "expect_tempo_range": (80, 120),
        "expect_instruments": ["acoustic_guitar_nylon"],
        "expect_duration": None,
    },
    {
        "desc": "厳かで壮厳な教会音楽",
        "project": "church-solemn",
        "expect_mode": "minor",
        "expect_tempo_range": (55, 90),
        "expect_instruments": None,
        "expect_duration": None,
    },
]


class TestJapaneseSpecCompiler:
    """Integration tests for Japanese input."""

    @pytest.mark.parametrize(
        "sample",
        _JA_SAMPLES,
        ids=[s["project"] for s in _JA_SAMPLES],
    )
    def test_japanese_sample(self, compiler: SpecCompiler, sample: dict) -> None:
        """Each Japanese sample produces a musically reasonable spec."""
        spec, traj = compiler.compile(sample["desc"], sample["project"], language="ja")

        # Key mode check
        expected_mode = sample["expect_mode"]
        assert expected_mode in spec.key.lower(), f"{sample['project']}: expected {expected_mode} key, got {spec.key}"

        # Tempo range check
        lo, hi = sample["expect_tempo_range"]
        assert lo <= spec.tempo_bpm <= hi, f"{sample['project']}: tempo {spec.tempo_bpm} not in [{lo}, {hi}]"

        # Instrument check (if specified)
        if sample["expect_instruments"] is not None:
            actual_names = [i.name for i in spec.instruments]
            for expected_instr in sample["expect_instruments"]:
                assert expected_instr in actual_names, (
                    f"{sample['project']}: expected {expected_instr} in {actual_names}"
                )

        # Duration check (if specified, with tolerance)
        if sample["expect_duration"] is not None:
            expected_dur = sample["expect_duration"]
            actual_dur = spec.total_bars * 4 * 60.0 / spec.tempo_bpm
            assert abs(actual_dur - expected_dur) < expected_dur * 0.5, (
                f"{sample['project']}: duration ~{actual_dur:.0f}s, expected ~{expected_dur}s"
            )

        # Basic validity
        assert len(spec.instruments) >= 1
        assert len(spec.sections) >= 1
        assert spec.total_bars >= 8
        assert traj.tension is not None

    def test_provenance_records_emotion_scan(self, compiler: SpecCompiler) -> None:
        """Japanese compile should record emotion scan in provenance."""
        compiler.compile("切ないピアノ曲", "test", language="ja")
        emotion_records = compiler.provenance.query_by_operation("emotion_scan")
        assert len(emotion_records) >= 1
        assert "切ない" in str(emotion_records[0].parameters["matched_words"])

    def test_auto_language_detection(self, compiler: SpecCompiler) -> None:
        """Auto language detection should route Japanese to ja compile."""
        spec_ja, _ = compiler.compile("切ないピアノ曲", "test")
        spec_en, _ = compiler.compile("A sad piano piece", "test")
        # Both should produce minor keys
        assert "minor" in spec_ja.key.lower()
        assert "minor" in spec_en.key.lower()
