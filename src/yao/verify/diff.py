"""Score diff — compare two ScoreIR iterations.

Belongs to Layer 6 (Verification). Supports the /diff command
(PROJECT.md §8) which compares two iterations of the same composition.

Tracks added, removed, AND modified notes (PROJECT_IMPROVEMENT §5.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from yao.ir.notation import midi_to_note_name
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class NoteDiff:
    """A single note-level difference between two scores.

    Attributes:
        change_type: 'added', 'removed', or 'modified'.
        note: The note in question (the "after" note for modifications).
        section: Section name where the change occurred.
        instrument: Instrument name.
    """

    change_type: str
    note: Note
    section: str
    instrument: str


@dataclass(frozen=True)
class NoteModification:
    """A note that was modified between two iterations.

    Attributes:
        note_before: The note in the earlier score.
        note_after: The note in the later score.
        section: Section name.
        instrument: Instrument name.
        changes: Human-readable description of what changed.
    """

    note_before: Note
    note_after: Note
    section: str
    instrument: str
    changes: str


@dataclass
class ScoreDiff:
    """Complete diff between two ScoreIR objects.

    Attributes:
        title_a: Title of the first score.
        title_b: Title of the second score.
        added_notes: Notes present in B but not A.
        removed_notes: Notes present in A but not B.
        modified_notes: Notes at the same position with changed properties.
        section_changes: Sections that were added/removed/renamed.
        instrument_changes: Instruments that were added/removed.
        tempo_changed: Whether tempo changed.
        key_changed: Whether key changed.
    """

    title_a: str
    title_b: str
    added_notes: list[NoteDiff] = field(default_factory=list)
    removed_notes: list[NoteDiff] = field(default_factory=list)
    modified_notes: list[NoteModification] = field(default_factory=list)
    section_changes: list[str] = field(default_factory=list)
    instrument_changes: list[str] = field(default_factory=list)
    tempo_changed: bool = False
    key_changed: bool = False

    @property
    def total_changes(self) -> int:
        """Total number of note-level changes."""
        return len(self.added_notes) + len(self.removed_notes) + len(self.modified_notes)

    @property
    def has_changes(self) -> bool:
        """Whether any changes were detected."""
        return (
            self.total_changes > 0
            or len(self.section_changes) > 0
            or len(self.instrument_changes) > 0
            or self.tempo_changed
            or self.key_changed
        )


def _note_key(note: Note) -> tuple[int, float, float, int, str]:
    """Create a hashable key for exact note comparison."""
    return (note.pitch, note.start_beat, note.duration_beats, note.velocity, note.instrument)


def _position_key(note: Note) -> tuple[float, str]:
    """Create a key based on time position and instrument for modification matching."""
    return (round(note.start_beat, 3), note.instrument)


def _describe_changes(before: Note, after: Note) -> str:
    """Describe what changed between two notes at the same position."""
    changes: list[str] = []
    if before.pitch != after.pitch:
        before_name = midi_to_note_name(before.pitch)
        after_name = midi_to_note_name(after.pitch)
        diff = after.pitch - before.pitch
        direction = "up" if diff > 0 else "down"
        changes.append(f"pitch {before_name}→{after_name} ({direction} {abs(diff)} semitones)")
    if abs(before.duration_beats - after.duration_beats) > 0.01:
        changes.append(f"duration {before.duration_beats:.2f}→{after.duration_beats:.2f}")
    if before.velocity != after.velocity:
        changes.append(f"velocity {before.velocity}→{after.velocity}")
    return "; ".join(changes) if changes else "no change"


def diff_scores(score_a: ScoreIR, score_b: ScoreIR) -> ScoreDiff:
    """Compare two ScoreIR objects and identify differences.

    Detects added, removed, AND modified notes. A note is considered
    "modified" if a note at the same time position and instrument exists
    in both scores but with different pitch, duration, or velocity.

    Args:
        score_a: The first (earlier) score.
        score_b: The second (later) score.

    Returns:
        ScoreDiff describing all changes from A to B.
    """
    result = ScoreDiff(title_a=score_a.title, title_b=score_b.title)

    # Global changes
    result.tempo_changed = score_a.tempo_bpm != score_b.tempo_bpm
    result.key_changed = score_a.key != score_b.key

    # Section changes
    sections_a = {s.name for s in score_a.sections}
    sections_b = {s.name for s in score_b.sections}
    for name in sorted(sections_b - sections_a):
        result.section_changes.append(f"+ section '{name}'")
    for name in sorted(sections_a - sections_b):
        result.section_changes.append(f"- section '{name}'")

    # Instrument changes
    instr_a = set(score_a.instruments())
    instr_b = set(score_b.instruments())
    for name in sorted(instr_b - instr_a):
        result.instrument_changes.append(f"+ instrument '{name}'")
    for name in sorted(instr_a - instr_b):
        result.instrument_changes.append(f"- instrument '{name}'")

    # Build note maps
    # Exact key → (note, section_name) for precise add/remove detection
    exact_a: dict[tuple[int, float, float, int, str], tuple[Note, str]] = {}
    for section in score_a.sections:
        for part in section.parts:
            for note in part.notes:
                exact_a[_note_key(note)] = (note, section.name)

    exact_b: dict[tuple[int, float, float, int, str], tuple[Note, str]] = {}
    for section in score_b.sections:
        for part in section.parts:
            for note in part.notes:
                exact_b[_note_key(note)] = (note, section.name)

    exact_a_keys = set(exact_a.keys())
    exact_b_keys = set(exact_b.keys())

    # Position key → list of (note, section) for modification detection
    pos_a: dict[tuple[float, str], list[tuple[Note, str]]] = {}
    for section in score_a.sections:
        for part in section.parts:
            for note in part.notes:
                pk = _position_key(note)
                pos_a.setdefault(pk, []).append((note, section.name))

    pos_b: dict[tuple[float, str], list[tuple[Note, str]]] = {}
    for section in score_b.sections:
        for part in section.parts:
            for note in part.notes:
                pk = _position_key(note)
                pos_b.setdefault(pk, []).append((note, section.name))

    # Find modifications: notes at same position+instrument that changed
    modified_positions: set[tuple[float, str]] = set()
    for pk in pos_a:
        if pk not in pos_b:
            continue
        notes_at_a = pos_a[pk]
        notes_at_b = pos_b[pk]
        # Match by index (simplest: first note at position A matches first at B)
        for i in range(min(len(notes_at_a), len(notes_at_b))):
            na, sec_a = notes_at_a[i]
            nb, sec_b = notes_at_b[i]
            key_a = _note_key(na)
            key_b = _note_key(nb)
            if key_a != key_b:
                # Same position, different content = modification
                result.modified_notes.append(
                    NoteModification(
                        note_before=na,
                        note_after=nb,
                        section=sec_b,
                        instrument=nb.instrument,
                        changes=_describe_changes(na, nb),
                    )
                )
                modified_positions.add(pk)
                # Remove from exact sets so they don't appear as add+remove
                exact_a_keys.discard(key_a)
                exact_b_keys.discard(key_b)

    # Pure additions (in B but not A, and not a modification)
    for key in exact_b_keys - exact_a_keys:
        diff_note, section_name = exact_b[key]
        result.added_notes.append(
            NoteDiff(
                change_type="added",
                note=diff_note,
                section=section_name,
                instrument=diff_note.instrument,
            )
        )

    # Pure removals (in A but not B, and not a modification)
    for key in exact_a_keys - exact_b_keys:
        diff_note, section_name = exact_a[key]
        result.removed_notes.append(
            NoteDiff(
                change_type="removed",
                note=diff_note,
                section=section_name,
                instrument=diff_note.instrument,
            )
        )

    return result


def format_diff(diff: ScoreDiff) -> str:
    """Format a ScoreDiff as human-readable text.

    Args:
        diff: The diff to format.

    Returns:
        Multi-line formatted string.
    """
    if not diff.has_changes:
        return f"No changes between '{diff.title_a}' and '{diff.title_b}'."

    lines = [f"=== Diff: {diff.title_a} → {diff.title_b} ==="]

    if diff.tempo_changed:
        lines.append("  Tempo changed")
    if diff.key_changed:
        lines.append("  Key changed")

    for change in diff.section_changes:
        lines.append(f"  {change}")
    for change in diff.instrument_changes:
        lines.append(f"  {change}")

    if diff.modified_notes:
        lines.append(f"\n  Modified: {len(diff.modified_notes)} notes")
        for nm in diff.modified_notes[:10]:
            name = midi_to_note_name(nm.note_after.pitch)
            lines.append(
                f"    ~ {name} at beat {nm.note_after.start_beat:.1f} "
                f"({nm.instrument}, {nm.section}): {nm.changes}"
            )
        if len(diff.modified_notes) > 10:
            lines.append(f"    ... and {len(diff.modified_notes) - 10} more")

    if diff.added_notes:
        lines.append(f"\n  Added: {len(diff.added_notes)} notes")
        for nd in diff.added_notes[:10]:
            name = midi_to_note_name(nd.note.pitch)
            lines.append(
                f"    + {name} at beat {nd.note.start_beat:.1f} ({nd.instrument}, {nd.section})"
            )
        if len(diff.added_notes) > 10:
            lines.append(f"    ... and {len(diff.added_notes) - 10} more")

    if diff.removed_notes:
        lines.append(f"\n  Removed: {len(diff.removed_notes)} notes")
        for nd in diff.removed_notes[:10]:
            name = midi_to_note_name(nd.note.pitch)
            lines.append(
                f"    - {name} at beat {nd.note.start_beat:.1f} ({nd.instrument}, {nd.section})"
            )
        if len(diff.removed_notes) > 10:
            lines.append(f"    ... and {len(diff.removed_notes) - 10} more")

    counts = f"+{len(diff.added_notes)} / -{len(diff.removed_notes)} / ~{len(diff.modified_notes)}"
    lines.append(f"\n  Total: {counts} notes")
    return "\n".join(lines)
