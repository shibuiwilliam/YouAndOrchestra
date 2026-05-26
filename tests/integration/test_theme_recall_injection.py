"""Integration test: automatic theme recall injection.

Verifies that compositions with 3+ sections automatically get
theme recall on the last section, producing a recognizable A→...→A′ form.
"""

from __future__ import annotations

from yao.generators.genre_resolver import inject_theme_recall
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


class TestThemeRecallInjection:
    """Verify automatic theme recall injection."""

    def test_three_section_spec_gets_recall(self) -> None:
        """A 3-section spec should auto-inject recall on the last section."""
        spec = CompositionSpec(
            title="Theme Recall Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="f"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42),
        )
        prov = ProvenanceLog()
        enriched = inject_theme_recall(spec, prov)

        assert enriched.sections[-1].recall_melody_from == "verse"
        # Original sections unchanged
        assert enriched.sections[0].recall_melody_from is None
        assert enriched.sections[1].recall_melody_from is None
        # Provenance records the injection
        ops = [r.operation for r in prov.records]
        assert "theme_recall_injected" in ops

    def test_two_section_spec_unchanged(self) -> None:
        """A 2-section spec should NOT get recall (too short)."""
        spec = CompositionSpec(
            title="Short Piece",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
        )
        prov = ProvenanceLog()
        enriched = inject_theme_recall(spec, prov)

        assert enriched.sections[-1].recall_melody_from is None

    def test_existing_recall_not_overwritten(self) -> None:
        """If any section already has recall, don't interfere."""
        spec = CompositionSpec(
            title="Manual Recall",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="f", recall_melody_from="verse"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
        )
        prov = ProvenanceLog()
        enriched = inject_theme_recall(spec, prov)

        # Should not change anything
        assert enriched.sections[-1].recall_melody_from is None
        assert enriched.sections[1].recall_melody_from == "verse"
