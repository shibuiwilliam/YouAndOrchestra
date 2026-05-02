"""Arrangement Diff Writer — markdown comparison of source vs target.

Outputs a structured diff following PROJECT.md §13.4 format:
- Preserved: what was kept and how similar
- Changed: what was transformed and how
- Risks: preservation contract violations

Belongs to arrange/ package.
"""

from __future__ import annotations

from pathlib import Path

from yao.arrange.style_vector_ops import PreservationResult
from yao.errors import RenderError
from yao.ir.plan.musical_plan import MusicalPlan


class ArrangementDiffWriter:
    """Writes a markdown diff comparing source and target plans."""

    def write(
        self,
        source_plan: MusicalPlan,
        target_plan: MusicalPlan,
        preservation: PreservationResult,
        output_path: Path,
    ) -> Path:
        """Write an arrangement diff to markdown.

        Args:
            source_plan: The original MusicalPlan.
            target_plan: The transformed MusicalPlan.
            preservation: Preservation contract results.
            output_path: Path for the output markdown.

        Returns:
            Path to the written file.

        Raises:
            RenderError: If writing fails.
        """
        try:
            md = self._generate_markdown(source_plan, target_plan, preservation)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(md, encoding="utf-8")
        except Exception as e:
            raise RenderError(f"Failed to write arrangement diff: {e}") from e

        return output_path

    def _generate_markdown(
        self,
        source: MusicalPlan,
        target: MusicalPlan,
        preservation: PreservationResult,
    ) -> str:
        """Generate the diff markdown content."""
        lines: list[str] = []

        lines.append("# Arrangement Diff")
        lines.append("")

        # Preserved
        lines.append("## Preserved")
        lines.append(
            f"- Melody similarity: {preservation.melody_similarity:.2f} "
            f"{'OK' if preservation.melody_similarity >= 0.85 else 'BELOW THRESHOLD'}"
        )
        lines.append(
            f"- Hook rhythm similarity: {preservation.hook_similarity:.2f} "
            f"{'OK' if preservation.hook_similarity >= 0.80 else 'BELOW THRESHOLD'}"
        )
        lines.append(
            f"- Chord function similarity: {preservation.chord_similarity:.2f} "
            f"{'OK' if preservation.chord_similarity >= 0.75 else 'BELOW THRESHOLD'}"
        )
        lines.append(f"- Form structure: {'preserved' if preservation.form_preserved else 'CHANGED'}")
        lines.append("")

        # Changed
        lines.append("## Changed")
        src_ctx = source.global_context
        tgt_ctx = target.global_context
        if src_ctx.tempo_bpm != tgt_ctx.tempo_bpm:
            lines.append(f"- BPM: {src_ctx.tempo_bpm} -> {tgt_ctx.tempo_bpm}")
        if src_ctx.genre != tgt_ctx.genre:
            lines.append(f"- Genre: {src_ctx.genre} -> {tgt_ctx.genre}")
        if src_ctx.key != tgt_ctx.key:
            lines.append(f"- Key: {src_ctx.key} -> {tgt_ctx.key}")

        # Chord changes
        src_chords = [e.roman for e in source.harmony.chord_events]
        tgt_chords = [e.roman for e in target.harmony.chord_events]
        changed_chords = sum(1 for a, b in zip(src_chords, tgt_chords, strict=False) if a != b)
        if changed_chords > 0:
            total = max(len(src_chords), 1)
            pct = changed_chords / total * 100
            lines.append(f"- Chords: {changed_chords}/{total} bars reharmonized ({pct:.0f}%)")
        lines.append("")

        # Risks
        lines.append("## Risks")
        if preservation.violations:
            for v in preservation.violations:
                lines.append(f"- WARNING: {v}")
        else:
            lines.append("- No preservation contract violations detected.")
        lines.append("")

        return "\n".join(lines)
