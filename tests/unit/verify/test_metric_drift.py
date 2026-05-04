"""Tests for MetricDriftDetector critique rule."""

from __future__ import annotations

from yao.verify.critique.metric_drift import MetricDriftDetector


class TestMetricDriftDetector:
    """Test the metric drift detection rule."""

    def test_rule_id(self) -> None:
        rule = MetricDriftDetector()
        assert rule.rule_id == "metric_drift"

    def test_role_is_rhythm(self) -> None:
        rule = MetricDriftDetector()
        assert rule.role.value == "rhythm"

    def test_rule_is_registered(self) -> None:
        from yao.verify.critique import CRITIQUE_RULES

        rule_ids = [r.rule_id for r in CRITIQUE_RULES.all_rules()]
        assert "metric_drift" in rule_ids
