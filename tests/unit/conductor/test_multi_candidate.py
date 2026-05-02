"""Tests for Multi-Candidate Orchestrator."""

from __future__ import annotations

from yao.conductor.multi_candidate import (
    CandidateScore,
    MultiCandidateOrchestrator,
    _compute_weighted_severity,
)
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.verify.critique.types import Finding, Severity


def _make_spec(seed: int = 42) -> CompositionSpec:
    return CompositionSpec(
        title="Multi-Candidate Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="acoustic_bass", role="bass"),
        ],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="rule_based", seed=seed),
    )


class TestGenerateCandidates:
    def test_generates_n_candidates(self) -> None:
        mco = MultiCandidateOrchestrator()
        candidates = mco.generate_candidates(_make_spec(), n=5)
        assert len(candidates) == 5

    def test_each_candidate_has_different_seed(self) -> None:
        mco = MultiCandidateOrchestrator()
        candidates = mco.generate_candidates(_make_spec(), n=5, base_seed=100)
        seeds = [c[2] for c in candidates]
        assert seeds == [100, 101, 102, 103, 104]

    def test_single_candidate(self) -> None:
        mco = MultiCandidateOrchestrator()
        candidates = mco.generate_candidates(_make_spec(), n=1)
        assert len(candidates) == 1

    def test_capped_at_10(self) -> None:
        mco = MultiCandidateOrchestrator()
        candidates = mco.generate_candidates(_make_spec(), n=15)
        assert len(candidates) <= 10


class TestCriticRank:
    def test_deterministic_ranking(self) -> None:
        mco = MultiCandidateOrchestrator()
        spec = _make_spec()
        c1 = mco.generate_candidates(spec, n=3)
        c2 = mco.generate_candidates(spec, n=3)
        r1 = mco.critic_rank(c1, spec)
        r2 = mco.critic_rank(c2, spec)
        assert [c.seed for c in r1] == [c.seed for c in r2]

    def test_returns_candidate_scores(self) -> None:
        mco = MultiCandidateOrchestrator()
        spec = _make_spec()
        candidates = mco.generate_candidates(spec, n=3)
        ranked = mco.critic_rank(candidates, spec)
        assert len(ranked) == 3
        for cs in ranked:
            assert isinstance(cs, CandidateScore)
            assert cs.weighted_severity >= 0

    def test_sorted_by_severity(self) -> None:
        mco = MultiCandidateOrchestrator()
        spec = _make_spec()
        candidates = mco.generate_candidates(spec, n=5)
        ranked = mco.critic_rank(candidates, spec)
        severities = [c.weighted_severity for c in ranked]
        assert severities == sorted(severities)


class TestSeverityWeighting:
    def test_severity_weights(self) -> None:
        findings = [
            Finding(
                rule_id="test_crit",
                severity=Severity.CRITICAL,
                role="structural",
                issue="critical issue",
            ),
            Finding(
                rule_id="test_maj",
                severity=Severity.MAJOR,
                role="structural",
                issue="major issue",
            ),
            Finding(
                rule_id="test_min",
                severity=Severity.MINOR,
                role="structural",
                issue="minor issue",
            ),
        ]
        score = _compute_weighted_severity(findings)
        # critical=10 + major=3 + minor=1 = 14
        assert score == 14.0

    def test_empty_findings_zero(self) -> None:
        assert _compute_weighted_severity([]) == 0.0


class TestProducerSelect:
    def test_selects_lowest_severity(self) -> None:
        mco = MultiCandidateOrchestrator()
        spec = _make_spec()
        candidates = mco.generate_candidates(spec, n=5)
        ranked = mco.critic_rank(candidates, spec)
        best = mco.producer_select(ranked)
        assert best is ranked[0].plan

    def test_records_provenance(self) -> None:
        mco = MultiCandidateOrchestrator()
        spec = _make_spec()
        candidates = mco.generate_candidates(spec, n=3)
        ranked = mco.critic_rank(candidates, spec)
        prov = ProvenanceLog()
        mco.producer_select(ranked, provenance=prov)
        assert len(prov) > 0
        last = prov.records[-1]
        assert "multi_candidate_select" in last.operation
        params = last.parameters or {}
        assert "all_seeds" in params
        assert len(params["all_seeds"]) == 3
