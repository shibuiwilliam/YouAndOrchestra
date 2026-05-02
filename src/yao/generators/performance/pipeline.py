"""Performance Realizer Pipeline — runs all 4 realizers and merges results.

Order: Articulation → Dynamics Curve → Microtiming → CC Curves.
Each realizer is independent and idempotent.

The merge strategy: for each NoteId, fields from earlier realizers are
preserved; later realizers only fill fields that are still at defaults.
"""

from __future__ import annotations

from yao.generators.performance.articulation_realizer import ArticulationRealizer
from yao.generators.performance.cc_curve_generator import CCCurveGenerator
from yao.generators.performance.dynamics_curve_renderer import DynamicsCurveRenderer
from yao.generators.performance.microtiming_injector import MicrotimingInjector
from yao.ir.expression import NoteExpression, NoteId, PerformanceLayer
from yao.ir.score_ir import ScoreIR
from yao.schema.trajectory import TrajectorySpec


def realize_performance(
    score: ScoreIR,
    trajectory: TrajectorySpec | None = None,
    genre: str = "default",
) -> PerformanceLayer:
    """Run the full performance realizer pipeline.

    Args:
        score: The ScoreIR to express.
        trajectory: Optional trajectory for dynamics shaping.
        genre: Genre name for microtiming profile.

    Returns:
        Merged PerformanceLayer with all expression data.
    """
    layers = [
        ArticulationRealizer().realize(score),
        DynamicsCurveRenderer().render(score, trajectory),
        MicrotimingInjector().inject(score, genre),
        CCCurveGenerator().generate(score),
    ]
    return _merge_layers(layers)


def _merge_layers(layers: list[PerformanceLayer]) -> PerformanceLayer:
    """Merge multiple PerformanceLayers into one.

    For each NoteId, fields from earlier layers take priority.
    Non-default fields are preserved; default fields are overwritten.

    Args:
        layers: Ordered list of PerformanceLayers.

    Returns:
        A single merged PerformanceLayer.
    """
    merged_expressions: dict[NoteId, NoteExpression] = {}
    merged_rubato: dict[str, object] = {}
    all_breaths: list[object] = []
    all_pedals: list[object] = []

    for layer in layers:
        for nid, expr in layer.note_expressions.items():
            if nid in merged_expressions:
                merged_expressions[nid] = _merge_expressions(merged_expressions[nid], expr)
            else:
                merged_expressions[nid] = expr

        for name, rubato in layer.section_rubato.items():
            if name not in merged_rubato:
                merged_rubato[name] = rubato

        all_breaths.extend(layer.breath_marks)
        all_pedals.extend(layer.pedal_curves)

    return PerformanceLayer(
        note_expressions=merged_expressions,
        section_rubato=merged_rubato,  # type: ignore[arg-type]
        breath_marks=tuple(all_breaths),  # type: ignore[arg-type]
        pedal_curves=tuple(all_pedals),  # type: ignore[arg-type]
    )


def _merge_expressions(base: NoteExpression, overlay: NoteExpression) -> NoteExpression:
    """Merge two NoteExpressions, preferring non-default values from base.

    Args:
        base: The earlier expression (higher priority).
        overlay: The later expression (fills gaps).

    Returns:
        Merged NoteExpression.
    """
    return NoteExpression(
        legato_overlap=base.legato_overlap if base.legato_overlap != 0.0 else overlay.legato_overlap,
        accent_strength=base.accent_strength if base.accent_strength != 0.0 else overlay.accent_strength,
        glissando_to=base.glissando_to if base.glissando_to is not None else overlay.glissando_to,
        pitch_bend_curve=base.pitch_bend_curve if base.pitch_bend_curve is not None else overlay.pitch_bend_curve,
        cc_curves=_merge_cc(base.cc_curves, overlay.cc_curves),
        micro_timing_ms=base.micro_timing_ms if base.micro_timing_ms != 0.0 else overlay.micro_timing_ms,
        micro_dynamics=base.micro_dynamics if base.micro_dynamics != 0.0 else overlay.micro_dynamics,
    )


def _merge_cc(
    base: dict[int, tuple[tuple[float, float], ...]] | None,
    overlay: dict[int, tuple[tuple[float, float], ...]] | None,
) -> dict[int, tuple[tuple[float, float], ...]] | None:
    """Merge CC curve dictionaries (union of CC numbers)."""
    if base is None and overlay is None:
        return None
    result: dict[int, tuple[tuple[float, float], ...]] = {}
    if base is not None:
        result.update(base)
    if overlay is not None:
        for cc, points in overlay.items():
            if cc not in result:
                result[cc] = points
    return result if result else None
