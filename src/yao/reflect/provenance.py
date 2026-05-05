"""Provenance tracking — append-only recording of all generation decisions.

Every creative decision in YaO must be recorded with a rationale (Principle 2).
The ProvenanceLog is append-only: existing entries MUST NOT be deleted or
modified (CLAUDE.md §3).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yao.errors import ProvenanceError


@dataclass(frozen=True)
class ProvenanceRecord:
    """A single recorded decision in the generation process.

    Attributes:
        timestamp: ISO 8601 timestamp of when the decision was made.
        layer: Which architectural layer made the decision.
        operation: The specific operation performed.
        parameters: Input parameters that influenced the decision.
        source: What triggered this operation.
        rationale: Why this particular decision was made.
        record_id: Unique identifier for causal graph edges.
        caused_by: IDs of records that influenced this decision.
        agent: Subagent identifier (v2.0). Required for subagent decisions.
        phase: Cognitive phase name (v2.0). E.g., "SKELETAL_GENERATION".
        confidence: Decision confidence in [0.0, 1.0] (v2.0).
        alternatives_rejected: Other options considered but not chosen (v2.0).
        skill_referenced: Genre Skill that informed this decision (v2.0).
    """

    timestamp: str
    layer: str
    operation: str
    parameters: dict[str, Any]
    source: str
    rationale: str
    record_id: str = ""
    caused_by: tuple[str, ...] = ()
    agent: str | None = None
    phase: str | None = None
    confidence: float | None = None
    alternatives_rejected: tuple[str, ...] = ()
    skill_referenced: str | None = None

    @classmethod
    def create(
        cls,
        *,
        layer: str,
        operation: str,
        parameters: dict[str, Any],
        source: str,
        rationale: str,
        caused_by: tuple[str, ...] = (),
        agent: str | None = None,
        phase: str | None = None,
        confidence: float | None = None,
        alternatives_rejected: tuple[str, ...] = (),
        skill_referenced: str | None = None,
    ) -> ProvenanceRecord:
        """Create a new provenance record with the current timestamp.

        Args:
            layer: Architectural layer name (e.g., "generator", "render").
            operation: Operation name (e.g., "generate_melody").
            parameters: Dictionary of input parameters.
            source: What triggered this operation.
            rationale: Why this decision was made.
            caused_by: IDs of records that influenced this decision.
            agent: Subagent identifier (v2.0, optional).
            phase: Cognitive phase name (v2.0, optional).
            confidence: Decision confidence in [0.0, 1.0] (v2.0, optional).
            alternatives_rejected: Alternatives considered (v2.0, optional).
            skill_referenced: Genre Skill that informed this decision (v2.0, optional).

        Returns:
            A new ProvenanceRecord with current UTC timestamp and auto-generated ID.
        """
        import hashlib

        ts = datetime.now(tz=UTC).isoformat()
        # Generate deterministic ID from content
        content = f"{ts}:{layer}:{operation}:{source}"
        record_id = hashlib.sha256(content.encode()).hexdigest()[:12]

        return cls(
            timestamp=ts,
            layer=layer,
            operation=operation,
            parameters=parameters,
            source=source,
            rationale=rationale,
            record_id=record_id,
            caused_by=caused_by,
            agent=agent,
            phase=phase,
            confidence=confidence,
            alternatives_rejected=alternatives_rejected,
            skill_referenced=skill_referenced,
        )


@dataclass
class ProvenanceLog:
    """Append-only log of provenance records and recoverable decisions.

    Records can only be added, never removed or modified.
    This ensures complete traceability of all generation decisions.
    """

    _records: list[ProvenanceRecord] = field(default_factory=list)
    _recoverables: list[Any] = field(default_factory=list)  # RecoverableDecision objects

    def add(self, record: ProvenanceRecord) -> None:
        """Append a provenance record.

        Args:
            record: The provenance record to add.
        """
        self._records.append(record)

    def record(
        self,
        *,
        layer: str,
        operation: str,
        parameters: dict[str, Any],
        source: str,
        rationale: str,
        caused_by: tuple[str, ...] = (),
        agent: str | None = None,
        phase: str | None = None,
        confidence: float | None = None,
        alternatives_rejected: tuple[str, ...] = (),
        skill_referenced: str | None = None,
    ) -> ProvenanceRecord:
        """Create and append a provenance record in one step.

        Args:
            layer: Architectural layer name.
            operation: Operation name.
            parameters: Input parameters.
            source: What triggered this operation.
            rationale: Why this decision was made.
            caused_by: IDs of records that influenced this decision.
            agent: Subagent identifier (v2.0, optional).
            phase: Cognitive phase name (v2.0, optional).
            confidence: Decision confidence in [0.0, 1.0] (v2.0, optional).
            alternatives_rejected: Alternatives considered (v2.0, optional).
            skill_referenced: Genre Skill that informed this decision (v2.0, optional).

        Returns:
            The newly created record (for chaining causal references).
        """
        rec = ProvenanceRecord.create(
            layer=layer,
            operation=operation,
            parameters=parameters,
            source=source,
            rationale=rationale,
            caused_by=caused_by,
            agent=agent,
            phase=phase,
            confidence=confidence,
            alternatives_rejected=alternatives_rejected,
            skill_referenced=skill_referenced,
        )
        self.add(rec)
        return rec

    @property
    def records(self) -> list[ProvenanceRecord]:
        """Return a copy of all records (prevents external mutation)."""
        return list(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def query_by_operation(self, operation: str) -> list[ProvenanceRecord]:
        """Find all records matching an operation name.

        Args:
            operation: Operation name to search for (exact or substring).

        Returns:
            Matching records in chronological order.
        """
        return [r for r in self._records if operation in r.operation]

    def query_by_layer(self, layer: str) -> list[ProvenanceRecord]:
        """Find all records from a specific architectural layer.

        Args:
            layer: Layer name (e.g., "generator", "render").

        Returns:
            Matching records in chronological order.
        """
        return [r for r in self._records if r.layer == layer]

    def record_recoverable(self, decision: Any) -> None:
        """Record a recoverable decision.

        Also creates a provenance record for the decision so the full
        chain is visible in the explain output.

        Args:
            decision: A RecoverableDecision instance.
        """
        self._recoverables.append(decision)
        self.record(
            layer="recoverable",
            operation="compromise",
            parameters={
                "code": decision.code,
                "severity": decision.severity,
                "original": str(decision.original_value),
                "recovered": str(decision.recovered_value),
            },
            source=decision.code,
            rationale=f"{decision.reason} | Impact: {decision.musical_impact}",
        )

    @property
    def recoverables(self) -> list[Any]:
        """Return a copy of all recoverable decisions."""
        return list(self._recoverables)

    def recoverables_by_severity(self, severity: str) -> list[Any]:
        """Filter recoverable decisions by severity.

        Args:
            severity: "info", "warning", or "error".

        Returns:
            Matching decisions.
        """
        return [d for d in self._recoverables if d.severity == severity]

    def recoverables_by_code(self, code: str) -> list[Any]:
        """Filter recoverable decisions by code.

        Args:
            code: The decision code (e.g., "BASS_NOTE_OUT_OF_RANGE").

        Returns:
            Matching decisions.
        """
        return [d for d in self._recoverables if d.code == code]

    def has_blocking_decisions(self) -> bool:
        """Return True if any recoverable decision has severity 'error'."""
        return any(d.is_blocking for d in self._recoverables)

    def get_by_id(self, record_id: str) -> ProvenanceRecord | None:
        """Find a record by its unique ID.

        Args:
            record_id: The record_id to look up.

        Returns:
            The matching record, or None.
        """
        for r in self._records:
            if r.record_id == record_id:
                return r
        return None

    def get_causes(self, record: ProvenanceRecord) -> list[ProvenanceRecord]:
        """Return all records that causally influenced a given record.

        Args:
            record: The record whose causes to find.

        Returns:
            List of causing records (may be empty).
        """
        return [r for r in self._records if r.record_id in record.caused_by]

    def get_effects(self, record: ProvenanceRecord) -> list[ProvenanceRecord]:
        """Return all records that were caused by a given record.

        Args:
            record: The record whose effects to find.

        Returns:
            List of effect records.
        """
        return [r for r in self._records if record.record_id in r.caused_by]

    def trace_ancestry(self, record: ProvenanceRecord) -> list[ProvenanceRecord]:
        """Trace the full causal ancestry of a record (BFS).

        Returns all records that directly or indirectly caused this record,
        in breadth-first order.

        Args:
            record: The record to trace.

        Returns:
            Ancestry chain, nearest causes first.
        """
        visited: set[str] = set()
        queue: list[ProvenanceRecord] = list(self.get_causes(record))
        result: list[ProvenanceRecord] = []

        while queue:
            current = queue.pop(0)
            if current.record_id in visited:
                continue
            visited.add(current.record_id)
            result.append(current)
            queue.extend(self.get_causes(current))

        return result

    def explain_chain(self) -> str:
        """Generate a human-readable explanation of the full decision chain.

        Returns:
            Multi-line narrative of all decisions and their rationales,
            including causal edges.
        """
        if not self._records:
            return "No decisions recorded."

        lines: list[str] = ["=== Provenance Chain ==="]
        for i, r in enumerate(self._records, 1):
            lines.append(f"\n{i}. [{r.layer}] {r.operation}")
            lines.append(f"   Why: {r.rationale}")
            if r.parameters:
                params = ", ".join(f"{k}={v}" for k, v in r.parameters.items())
                lines.append(f"   With: {params}")
            if r.caused_by:
                causes = ", ".join(r.caused_by)
                lines.append(f"   Caused by: {causes}")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize the full log to a JSON string.

        Returns:
            JSON string with all provenance records.
        """
        return json.dumps(
            [asdict(r) for r in self._records],
            indent=2,
            ensure_ascii=False,
        )

    def save(self, path: Path) -> None:
        """Save the provenance log to a JSON file.

        If the file already exists, existing records are preserved and new
        records are appended (append-only guarantee).

        Args:
            path: Output file path.

        Raises:
            ProvenanceError: If saving fails.
        """
        existing: list[dict[str, Any]] = []
        if path.exists():
            try:
                with open(path) as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                raise ProvenanceError(f"Failed to read existing provenance file: {e}") from e

        new_records = [asdict(r) for r in self._records]
        all_records = existing + new_records

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(all_records, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise ProvenanceError(f"Failed to save provenance: {e}") from e
