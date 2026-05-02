"""Mix Engineer Subagent — designs production manifest from spec and score.

Mirrors .claude/agents/mix-engineer.md.
Uses pyloudnorm for LUFS targets, never RMS approximation.
"""

from __future__ import annotations

from yao.reflect.provenance import ProvenanceLog
from yao.schema.production import (
    CompressionSpec,
    EQBand,
    MasterSpec,
    ProductionManifest,
    ReverbSpec,
    TrackMixSpec,
)
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)


@register_subagent(AgentRole.MIX_ENGINEER)
class MixEngineerSubagent(SubagentBase):
    """Generates a ProductionManifest from spec and score.

    Responsibility boundary:
    - Owns: ProductionManifest (EQ, compression, reverb, pan, LUFS target)
    - Does NOT own: generation, critique, arrangement
    """

    role = AgentRole.MIX_ENGINEER

    def process(self, context: AgentContext) -> AgentOutput:
        """Design a production manifest.

        Auto-assigns sensible defaults based on instrument roles,
        genre conventions, and frequency ranges.

        Args:
            context: Pipeline state with spec and optionally score.

        Returns:
            AgentOutput with production_manifest.
        """
        prov = ProvenanceLog()

        per_track: dict[str, TrackMixSpec] = {}
        for instr in context.spec.instruments:
            per_track[instr.name] = self._design_track(instr.name, instr.role)

        manifest = ProductionManifest(
            master=MasterSpec(
                target_lufs=-14.0,
                true_peak_max_dbfs=-1.0,
                stereo_width=0.7,
            ),
            per_track=per_track,
        )

        prov.record(
            layer="subagent",
            operation="mix_engineer_complete",
            parameters={
                "track_count": len(per_track),
                "target_lufs": -14.0,
            },
            source="MixEngineerSubagent.process",
            rationale="Mix Engineer designed production manifest from spec.",
        )

        return AgentOutput(
            provenance=prov,
            production_manifest=manifest,
        )

    def _design_track(self, instrument: str, role: str) -> TrackMixSpec:
        """Design mix settings for a single track.

        Args:
            instrument: Instrument name.
            role: Instrument role (melody, bass, harmony, etc.).

        Returns:
            TrackMixSpec with sensible defaults.
        """
        eq_bands: list[EQBand] = []
        compression: CompressionSpec | None = None
        reverb: ReverbSpec | None = None
        pan = 0.0
        gain_db = 0.0

        # Role-based defaults
        if role == "bass":
            eq_bands.append(EQBand(freq=80.0, type="high_pass"))
            compression = CompressionSpec(threshold_db=-15.0, ratio=3.0)
            pan = 0.0
            gain_db = 1.0
        elif role == "melody":
            eq_bands.append(EQBand(freq=120.0, type="high_pass"))
            reverb = ReverbSpec(type="room", wet=0.15)
            gain_db = 2.0
        elif role == "harmony":
            eq_bands.append(EQBand(freq=150.0, type="high_pass"))
            reverb = ReverbSpec(type="hall", wet=0.2)
            pan = -0.2
            gain_db = -2.0
        elif role == "pad":
            reverb = ReverbSpec(type="hall", wet=0.3)
            pan = 0.1
            gain_db = -4.0
        elif role == "rhythm":
            compression = CompressionSpec(threshold_db=-12.0, ratio=4.0)
            pan = 0.3

        return TrackMixSpec(
            eq=eq_bands,
            compression=compression,
            reverb=reverb,
            pan=pan,
            gain_db=gain_db,
        )
