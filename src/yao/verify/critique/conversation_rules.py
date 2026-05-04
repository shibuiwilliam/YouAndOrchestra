"""Conversation critique rules — detect ensemble dialogue issues.

Rules:
- ConversationSilenceDetector: no conversation events declared
- PrimaryVoiceAmbiguityDetector: section has no clear primary voice
- FillAbsenceDetector: phrase endings with no fills when fill_capable exists
- FrequencyCollisionUnresolvedDetector: high collision count remaining

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class ConversationSilenceDetector(CritiqueRule):
    """Detect ensembles with no inter-instrument dialogue.

    Fires when a multi-instrument piece has no ConversationPlan or
    an empty events list.
    """

    rule_id = "conversation.silence"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect missing conversation plan in multi-instrument pieces."""
        # Only relevant for multi-instrument pieces
        n_instruments = len(plan.global_context.instruments)
        if n_instruments < 2:
            return []

        # Check if conversation plan exists
        if not hasattr(plan, "conversation") or plan.conversation is None:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=(
                        f"Multi-instrument piece ({n_instruments} instruments) has no "
                        f"ConversationPlan. Instruments may not interact musically."
                    ),
                    evidence={"n_instruments": n_instruments},
                    recommendation={
                        "conversation_director": "Add a ConversationPlan with at least voice focus assignments.",
                    },
                )
            ]

        # Check if events are empty
        if len(plan.conversation.events) == 0 and n_instruments >= 3:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.SUGGESTION,
                    role=self.role,
                    issue=(
                        "ConversationPlan has no events. Consider adding "
                        "call-response or trade patterns for richer dialogue."
                    ),
                    evidence={
                        "n_instruments": n_instruments,
                        "n_events": 0,
                    },
                )
            ]

        return []


class PrimaryVoiceAmbiguityDetector(CritiqueRule):
    """Detect sections without a clear primary voice.

    When no instrument is designated as primary, the mix may
    sound unfocused and lack a clear lead.
    """

    rule_id = "conversation.primary_voice_ambiguity"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect sections missing a primary voice designation."""
        findings: list[Finding] = []

        if not hasattr(plan, "conversation") or plan.conversation is None:
            return []

        n_instruments = len(plan.global_context.instruments)
        if n_instruments < 2:
            return []

        for section in plan.form.sections:
            primary = plan.conversation.primary_voice_for_section(section.id)
            if primary is None:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=f"Section '{section.id}' has no designated primary voice.",
                        location=SongLocation(section=section.id),
                        recommendation={
                            "conversation_director": f"Assign a primary voice for section '{section.id}'.",
                        },
                    )
                )

        return findings


class FillAbsenceDetector(CritiqueRule):
    """Detect phrase endings without reactive fills.

    Only fires when fill_capable instruments are declared but no
    fill events exist in qualifying gaps.
    """

    rule_id = "conversation.fill_absence_at_phrase_ends"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect missing fills at phrase endings.

        Note: This is a plan-level check. For full detection,
        the ScoreIR would need to be analyzed (done at runtime).
        At plan level, we check if the conversation plan has
        any fill_in_response events when instruments are available.
        """
        if not hasattr(plan, "conversation") or plan.conversation is None:
            return []

        # Check if there are any fill_in_response events
        has_fills = any(e.type == "fill_in_response" for e in plan.conversation.events)
        if has_fills:
            return []

        # Check if the piece has enough sections to warrant fills
        if len(plan.form.sections) < 2:
            return []

        n_instruments = len(plan.global_context.instruments)
        if n_instruments < 2:
            return []

        return [
            Finding(
                rule_id=self.rule_id,
                severity=Severity.SUGGESTION,
                role=self.role,
                issue=(
                    "No fill_in_response events in ConversationPlan. "
                    "Phrase endings may feel abrupt without reactive fills."
                ),
                evidence={"n_sections": len(plan.form.sections)},
                recommendation={
                    "conversation_director": ("Add fill_in_response events at melodic phrase endings."),
                },
            )
        ]


class FrequencyCollisionUnresolvedDetector(CritiqueRule):
    """Detect unresolved frequency collisions.

    At plan level, checks if primary voice and accompaniment share
    the same register assignment without frequency clearance.
    """

    rule_id = "conversation.frequency_collision_unresolved"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect potential register collisions between primary and accompaniment."""
        findings: list[Finding] = []

        if plan.arrangement is None:
            return []

        if not hasattr(plan, "conversation") or plan.conversation is None:
            return []

        for section in plan.form.sections:
            primary = plan.conversation.primary_voice_for_section(section.id)
            if primary is None:
                continue

            # Find primary's register
            primary_low = 0
            primary_high = 127
            for a in plan.arrangement.assignments:
                if a.instrument == primary and a.section_id == section.id:
                    primary_low = a.register_low
                    primary_high = a.register_high
                    break

            # Check accompaniment registers for overlap
            accomp = plan.conversation.accompaniment_for_section(section.id)
            for a in plan.arrangement.assignments:
                if a.instrument in accomp and a.section_id == section.id:
                    # Check if registers overlap significantly
                    overlap_low = max(primary_low, a.register_low)
                    overlap_high = min(primary_high, a.register_high)
                    if overlap_high - overlap_low > 12:  # More than an octave overlap
                        findings.append(
                            Finding(
                                rule_id=self.rule_id,
                                severity=Severity.MINOR,
                                role=self.role,
                                issue=(
                                    f"'{a.instrument}' register overlaps significantly "
                                    f"with primary voice '{primary}' in section '{section.id}'. "
                                    f"Frequency clearance may be needed."
                                ),
                                location=SongLocation(section=section.id, instrument=a.instrument),
                                evidence={
                                    "overlap_semitones": overlap_high - overlap_low,
                                    "primary": primary,
                                    "accompaniment": a.instrument,
                                },
                            )
                        )

        return findings
