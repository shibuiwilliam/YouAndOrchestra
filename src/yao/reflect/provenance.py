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
    """

    timestamp: str
    layer: str
    operation: str
    parameters: dict[str, Any]
    source: str
    rationale: str

    @classmethod
    def create(
        cls,
        *,
        layer: str,
        operation: str,
        parameters: dict[str, Any],
        source: str,
        rationale: str,
    ) -> ProvenanceRecord:
        """Create a new provenance record with the current timestamp.

        Args:
            layer: Architectural layer name (e.g., "generator", "render").
            operation: Operation name (e.g., "generate_melody").
            parameters: Dictionary of input parameters.
            source: What triggered this operation.
            rationale: Why this decision was made.

        Returns:
            A new ProvenanceRecord with current UTC timestamp.
        """
        return cls(
            timestamp=datetime.now(tz=UTC).isoformat(),
            layer=layer,
            operation=operation,
            parameters=parameters,
            source=source,
            rationale=rationale,
        )


@dataclass
class ProvenanceLog:
    """Append-only log of provenance records.

    Records can only be added, never removed or modified.
    This ensures complete traceability of all generation decisions.
    """

    _records: list[ProvenanceRecord] = field(default_factory=list)

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
    ) -> None:
        """Create and append a provenance record in one step.

        Args:
            layer: Architectural layer name.
            operation: Operation name.
            parameters: Input parameters.
            source: What triggered this operation.
            rationale: Why this decision was made.
        """
        self.add(
            ProvenanceRecord.create(
                layer=layer,
                operation=operation,
                parameters=parameters,
                source=source,
                rationale=rationale,
            )
        )

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

    def explain_chain(self) -> str:
        """Generate a human-readable explanation of the full decision chain.

        Returns:
            Multi-line narrative of all decisions and their rationales.
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
