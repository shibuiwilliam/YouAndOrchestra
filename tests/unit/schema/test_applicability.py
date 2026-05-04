"""Tests for the spec field applicability registry."""

from __future__ import annotations

from yao.schema.applicability import (
    FieldStatus,
    format_applicability_report,
    get_field_status,
    get_registry,
    lint_spec_applicability,
)
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


def _minimal_spec() -> CompositionSpec:
    return CompositionSpec(
        title="Test",
        key="C major",
        tempo_bpm=120.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
    )


class TestRegistryContents:
    """Verify registry has comprehensive entries."""

    def test_registry_not_empty(self) -> None:
        """Registry has entries."""
        registry = get_registry()
        assert len(registry) > 20  # noqa: PLR2004

    def test_has_all_core_fields(self) -> None:
        """All core spec fields are registered."""
        registry = get_registry()
        for field in [
            "title",
            "key",
            "tempo_bpm",
            "time_signature",
            "genre",
            "generation.strategy",
            "generation.seed",
            "sections",
            "instruments",
        ]:
            assert field in registry, f"Missing field: {field}"

    def test_has_production_fields(self) -> None:
        """Production fields are registered."""
        registry = get_registry()
        for field in ["production.target_lufs", "production.stereo_width", "production.reverb_amount"]:
            assert field in registry, f"Missing field: {field}"

    def test_has_ignored_fields(self) -> None:
        """At least some fields are marked as ignored."""
        registry = get_registry()
        ignored = [k for k, v in registry.items() if v.status == FieldStatus.IGNORED]
        assert len(ignored) > 0, "No ignored fields found"

    def test_has_partial_fields(self) -> None:
        """At least some fields are marked as partial."""
        registry = get_registry()
        partial = [k for k, v in registry.items() if v.status == FieldStatus.PARTIAL]
        assert len(partial) > 0, "No partial fields found"

    def test_has_applied_fields(self) -> None:
        """Most fields are marked as applied."""
        registry = get_registry()
        applied = [k for k, v in registry.items() if v.status == FieldStatus.APPLIED]
        assert len(applied) > 10  # noqa: PLR2004


class TestGetFieldStatus:
    """Test field status lookup."""

    def test_known_field(self) -> None:
        """Known field returns applicability."""
        result = get_field_status("production.target_lufs")
        assert result is not None
        assert result.status == FieldStatus.APPLIED

    def test_unknown_field_returns_none(self) -> None:
        """Unknown field returns None."""
        assert get_field_status("nonexistent.field") is None

    def test_ignored_field(self) -> None:
        """Ignored field has correct status."""
        result = get_field_status("emotion.warmth")
        assert result is not None
        assert result.status == FieldStatus.IGNORED


class TestLintSpecApplicability:
    """Test the lint function that finds problematic fields."""

    def test_minimal_spec_no_warnings(self) -> None:
        """Minimal v1 spec has no ignored fields set."""
        spec = _minimal_spec()
        warnings = lint_spec_applicability(spec)
        ignored = [w for w in warnings if w.status == FieldStatus.IGNORED]
        assert len(ignored) == 0

    def test_v2_spec_has_warnings(self) -> None:
        """V2 spec with emotion.warmth set should warn."""
        from yao.schema.composition_v2 import (
            ArrangementSpecV2,
            CompositionSpecV2,
            EmotionSpec,
            FormSpec,
            GenerationSpecV2,
            GlobalSpec,
            IdentitySpec,
            InstrumentArrangementSpec,
            SectionFormSpec,
        )

        spec = CompositionSpecV2(
            version="2",
            identity=IdentitySpec(title="Test", duration_sec=16),
            global_=GlobalSpec(key="C major"),
            emotion=EmotionSpec(warmth=0.8),  # ignored field
            form=FormSpec(sections=[SectionFormSpec(id="verse", bars=8)]),
            arrangement=ArrangementSpecV2(
                instruments={"piano": InstrumentArrangementSpec(role="melody")},
            ),
            generation=GenerationSpecV2(),
        )
        warnings = lint_spec_applicability(spec)
        ignored_fields = {w.field for w in warnings if w.status == FieldStatus.IGNORED}
        assert "emotion.warmth" in ignored_fields


class TestFormatApplicabilityReport:
    """Test the human-readable report formatter."""

    def test_report_has_applied_section(self) -> None:
        """Report for any spec should have Applied section."""
        spec = _minimal_spec()
        report = format_applicability_report(spec)
        assert "Applied:" in report

    def test_report_contains_field_names(self) -> None:
        """Report should contain actual field names."""
        spec = _minimal_spec()
        report = format_applicability_report(spec)
        assert "generation.strategy" in report
