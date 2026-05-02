"""Style Vector Operations — transfer formula and preservation contracts.

Implements: target = source - source_genre + target_genre ⊕ preservation

MVP: operates on MusicalPlan metadata (tempo, key, form) rather than
full StyleVector extraction (which requires audio).

Belongs to arrange/ package.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.ir.plan.harmony import ChordEvent, HarmonyPlan
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SongFormPlan
from yao.reflect.provenance import ProvenanceLog
from yao.schema.arrangement import ArrangementSpec
from yao.schema.intent import IntentSpec


@dataclass(frozen=True)
class PreservationResult:
    """Result of preservation contract checking.

    Attributes:
        melody_similarity: Similarity of melody contour (0.0-1.0).
        hook_similarity: Similarity of rhythmic hook (0.0-1.0).
        chord_similarity: Similarity of chord function (0.0-1.0).
        form_preserved: Whether form structure was kept.
        all_passed: Whether all enabled contracts were satisfied.
        violations: List of violated contract descriptions.
    """

    melody_similarity: float
    hook_similarity: float
    chord_similarity: float
    form_preserved: bool
    all_passed: bool
    violations: tuple[str, ...]


def transfer(
    source_plan: MusicalPlan,
    arrangement_spec: ArrangementSpec,
    provenance: ProvenanceLog | None = None,
) -> tuple[MusicalPlan, PreservationResult]:
    """Apply style transfer to a source plan.

    Formula: target = source - source_genre + target_genre ⊕ preservation

    MVP: adjusts global context (tempo, genre) and reharmonizes at
    the specified level. Does not modify melody (preserved by default).

    Args:
        source_plan: The extracted source MusicalPlan.
        arrangement_spec: The arrangement specification.
        provenance: Optional provenance log.

    Returns:
        Tuple of (transformed MusicalPlan, PreservationResult).
    """
    if provenance is None:
        provenance = ProvenanceLog()

    transform = arrangement_spec.transform
    preserve = arrangement_spec.preserve

    # Transform global context
    new_tempo = transform.bpm if transform.bpm is not None else source_plan.global_context.tempo_bpm
    new_ctx = GlobalContext(
        key=source_plan.global_context.key,
        tempo_bpm=new_tempo,
        time_signature=source_plan.global_context.time_signature,
        genre=transform.target_genre,
        instruments=source_plan.global_context.instruments,
    )

    # Transform harmony (MVP: scale reharmonization_level)
    new_harmony = _reharmonize(
        source_plan.harmony,
        transform.reharmonization_level,
    )

    # Preserve form
    new_form = source_plan.form  # always preserved in MVP

    # Check preservation contracts
    pres_result = _check_preservation(
        source_plan,
        new_harmony,
        new_form,
        preserve,
    )

    provenance.record(
        layer="arrange",
        operation="style_transfer",
        parameters={
            "source_genre": source_plan.global_context.genre,
            "target_genre": transform.target_genre,
            "reharmonization_level": transform.reharmonization_level,
            "tempo_change": f"{source_plan.global_context.tempo_bpm} → {new_tempo}",
            "preservation_passed": pres_result.all_passed,
            "violations": list(pres_result.violations),
        },
        source="style_vector_ops.transfer",
        rationale=(
            f"Style transfer from '{source_plan.global_context.genre}' to "
            f"'{transform.target_genre}' with reharmonization={transform.reharmonization_level}."
        ),
    )

    target_plan = MusicalPlan(
        form=new_form,
        harmony=new_harmony,
        trajectory=source_plan.trajectory,
        intent=IntentSpec(
            text=f"Arrangement: {source_plan.global_context.genre} → {transform.target_genre}",
            keywords=["arrangement", transform.target_genre],
        ),
        provenance=provenance,
        global_context=new_ctx,
        motif=source_plan.motif,
        phrase=source_plan.phrase,
        arrangement=source_plan.arrangement,
        drums=source_plan.drums,
    )

    return target_plan, pres_result


def _reharmonize(
    harmony: HarmonyPlan,
    level: float,
) -> HarmonyPlan:
    """Apply reharmonization at the given level.

    MVP: substitutes chords at random positions proportional to level.
    level 0.0 = no change, level 1.0 = all chords substituted.
    """
    if level <= 0.0:
        return harmony

    substitutions = {"I": "vi", "IV": "ii", "V": "iii", "vi": "IV"}
    new_events: list[ChordEvent] = []

    for i, event in enumerate(harmony.chord_events):
        if i / max(len(harmony.chord_events), 1) < level:
            new_roman = substitutions.get(event.roman, event.roman)
            new_events.append(
                ChordEvent(
                    section_id=event.section_id,
                    start_beat=event.start_beat,
                    duration_beats=event.duration_beats,
                    roman=new_roman,
                    function=event.function,
                    tension_level=event.tension_level,
                    cadence_role=event.cadence_role,
                )
            )
        else:
            new_events.append(event)

    return HarmonyPlan(chord_events=new_events)


def _check_preservation(
    source: MusicalPlan,
    new_harmony: HarmonyPlan,
    new_form: SongFormPlan,
    preserve: object,
) -> PreservationResult:
    """Check preservation contracts against transformed plan."""
    melody_sim = 1.0  # MVP: melody always preserved (not transformed)
    hook_sim = 1.0  # MVP: hook always preserved

    # Chord function similarity
    source_chords = [e.roman for e in source.harmony.chord_events]
    new_chords = [e.roman for e in new_harmony.chord_events]
    if source_chords:
        matching = sum(1 for a, b in zip(source_chords, new_chords, strict=False) if a == b)
        chord_sim = matching / len(source_chords)
    else:
        chord_sim = 1.0

    form_preserved = len(new_form.sections) == len(source.form.sections)

    violations: list[str] = []
    melody_min = getattr(preserve, "melody_similarity_min", 0.85)
    hook_min = getattr(preserve, "hook_similarity_min", 0.80)
    chord_min = getattr(preserve, "chord_similarity_min", 0.75)

    if getattr(preserve, "melody", True) and melody_sim < melody_min:
        violations.append(f"melody_similarity {melody_sim:.2f} < {melody_min}")
    if getattr(preserve, "hook_rhythm", True) and hook_sim < hook_min:
        violations.append(f"hook_similarity {hook_sim:.2f} < {hook_min}")
    if getattr(preserve, "chord_function", True) and chord_sim < chord_min:
        violations.append(f"chord_similarity {chord_sim:.2f} < {chord_min}")
    if getattr(preserve, "form", True) and not form_preserved:
        violations.append("form structure changed")

    return PreservationResult(
        melody_similarity=melody_sim,
        hook_similarity=hook_sim,
        chord_similarity=chord_sim,
        form_preserved=form_preserved,
        all_passed=len(violations) == 0,
        violations=tuple(violations),
    )
