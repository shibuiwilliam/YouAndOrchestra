"""Conversation Director — Step 5.5 of the generation pipeline.

Produces a ConversationPlan from an ArrangementPlan and SongFormPlan.
Determines voice focus, conversation events, and fill opportunities.

The Conversation Director does NOT modify notes — it only produces
a structural plan that the Note Realizer respects.

Belongs to Layer 2 (Generation Strategy).
"""

from __future__ import annotations

from yao.ir.conversation import BarRange, ConversationEvent, ConversationPlan
from yao.ir.plan.arrangement import InstrumentRole
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SongFormPlan
from yao.reflect.provenance import ProvenanceLog
from yao.schema.conversation import ConversationSpec


def generate_conversation_plan(
    plan: MusicalPlan,
    conversation_spec: ConversationSpec | None = None,
    seed: int = 42,
) -> tuple[ConversationPlan, ProvenanceLog]:
    """Generate a ConversationPlan from the existing MusicalPlan.

    If a ConversationSpec is provided, it is used directly.
    Otherwise, a default plan is inferred from the ArrangementPlan.

    Args:
        plan: The current MusicalPlan (must have form at minimum).
        conversation_spec: Optional explicit conversation specification.
        seed: Random seed for deterministic generation.

    Returns:
        Tuple of (ConversationPlan, ProvenanceLog).
    """
    provenance = ProvenanceLog()

    if conversation_spec is not None:
        result = _plan_from_spec(plan, conversation_spec, provenance)
    else:
        result = _plan_from_arrangement(plan, provenance)

    provenance.record(
        layer="generator",
        operation="conversation_director",
        parameters={"seed": seed, "n_events": len(result.events)},
        source="generate_conversation_plan",
        rationale="Produced ConversationPlan for inter-instrument dialogue.",
    )

    return result, provenance


def _plan_from_spec(
    plan: MusicalPlan,
    spec: ConversationSpec,
    provenance: ProvenanceLog,
) -> ConversationPlan:
    """Build ConversationPlan from an explicit ConversationSpec."""
    events: list[ConversationEvent] = []

    # Convert spec events to IR events
    for ev_spec in spec.events:
        # Compute absolute bar positions from section offset
        section_offset = _section_start_bar(plan.form, ev_spec.section_id)
        abs_start = section_offset + ev_spec.start_bar
        abs_end = section_offset + ev_spec.end_bar
        beats_per_bar = _beats_per_bar(plan.global_context.time_signature)

        events.append(
            ConversationEvent(
                type=ev_spec.type,
                initiator=ev_spec.initiator,
                responder=ev_spec.responder,
                location=BarRange(start=abs_start, end=abs_end),
                duration_beats=(abs_end - abs_start) * beats_per_bar,
            )
        )

    # Build voice focus maps from spec
    primary_map: dict[str, str] = {}
    accompaniment_map: dict[str, tuple[str, ...]] = {}
    for vf in spec.voice_focus:
        primary_map[vf.section_id] = vf.primary
        accompaniment_map[vf.section_id] = tuple(vf.accompaniment)

    provenance.record(
        layer="generator",
        operation="conversation_from_spec",
        parameters={
            "n_voice_focus": len(spec.voice_focus),
            "n_events": len(spec.events),
        },
        source="_plan_from_spec",
        rationale="Built ConversationPlan from explicit conversation.yaml.",
    )

    return ConversationPlan(
        events=tuple(events),
        primary_voice_per_section=primary_map,
        accompaniment_role_per_section=accompaniment_map,
    )


def _plan_from_arrangement(
    plan: MusicalPlan,
    provenance: ProvenanceLog,
) -> ConversationPlan:
    """Infer a default ConversationPlan from the ArrangementPlan.

    Uses arrangement roles to determine primary voice:
    - MELODY role → primary voice
    - All others → accompaniment
    """
    primary_map: dict[str, str] = {}
    accompaniment_map: dict[str, tuple[str, ...]] = {}

    if plan.arrangement is not None:
        for assignment in plan.arrangement.assignments:
            section_id = assignment.section_id
            if assignment.role == InstrumentRole.MELODY:
                primary_map[section_id] = assignment.instrument
            else:
                existing = list(accompaniment_map.get(section_id, ()))
                existing.append(assignment.instrument)
                accompaniment_map[section_id] = tuple(existing)
    elif plan.form is not None:
        # Fallback: use first instrument as primary for all sections
        instruments = plan.global_context.instruments
        if instruments:
            first_instrument = instruments[0][0]
            for section in plan.form.sections:
                primary_map[section.id] = first_instrument

    provenance.record(
        layer="generator",
        operation="conversation_from_arrangement",
        parameters={"n_sections": len(primary_map)},
        source="_plan_from_arrangement",
        rationale="Inferred ConversationPlan from ArrangementPlan roles.",
    )

    return ConversationPlan(
        events=(),
        primary_voice_per_section=primary_map,
        accompaniment_role_per_section=accompaniment_map,
    )


def _section_start_bar(form: SongFormPlan, section_id: str) -> int:
    """Get the absolute start bar of a section."""
    for section in form.sections:
        if section.id == section_id:
            return section.start_bar
    return 0


def _beats_per_bar(time_sig: str) -> float:
    """Parse time signature string to get beats per bar."""
    parts = time_sig.split("/")
    if len(parts) == 2:
        return float(parts[0])
    return 4.0
