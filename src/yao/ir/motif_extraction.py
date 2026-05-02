"""Motif extraction — extract motif seeds from existing ScoreIR.

Analyzes a realized ScoreIR to find recurring melodic-rhythmic patterns
that could serve as motif seeds. Used by the Arrangement Engine and
for post-hoc analysis of compositions.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.ir.note import Note
from yao.ir.plan.motif import MotifSeed
from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class ExtractedFragment:
    """A candidate melodic fragment before promotion to MotifSeed.

    Attributes:
        notes: The sequence of notes.
        section_id: Section where this fragment was found.
        start_beat: Beat position of the first note.
        occurrences: Number of similar fragments found.
        similarity_avg: Average similarity to other occurrences (0-1).
    """

    notes: tuple[Note, ...]
    section_id: str
    start_beat: float
    occurrences: int
    similarity_avg: float


def _notes_to_rhythm_shape(notes: tuple[Note, ...]) -> tuple[float, ...]:
    """Convert a note sequence to a rhythm shape (duration pattern).

    Args:
        notes: Sequence of notes.

    Returns:
        Tuple of durations in beats.
    """
    return tuple(n.duration_beats for n in notes)


def _notes_to_interval_shape(notes: tuple[Note, ...]) -> tuple[int, ...]:
    """Convert a note sequence to an interval shape (semitone offsets from first).

    Args:
        notes: Sequence of notes.

    Returns:
        Tuple of semitone intervals from the first note's pitch.
    """
    if not notes:
        return ()
    base_pitch = notes[0].pitch
    return tuple(n.pitch - base_pitch for n in notes)


def _rhythm_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Compute rhythm similarity between two duration patterns (0-1).

    Uses normalized absolute difference. 1.0 = identical.

    Args:
        a: First rhythm shape.
        b: Second rhythm shape.

    Returns:
        Similarity score [0.0, 1.0].
    """
    if len(a) != len(b):
        return 0.0
    if not a:
        return 1.0
    max_dur = max(max(a), max(b), 0.001)
    diffs = [abs(x - y) / max_dur for x, y in zip(a, b, strict=True)]
    return max(0.0, 1.0 - sum(diffs) / len(diffs))


def _interval_similarity(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    """Compute interval pattern similarity (0-1).

    Compares semitone intervals. Allows transposition (offsets the second).

    Args:
        a: First interval shape.
        b: Second interval shape.

    Returns:
        Similarity score [0.0, 1.0].
    """
    if len(a) != len(b):
        return 0.0
    if not a:
        return 1.0
    # Normalize by removing offset (allow transposition)
    a_norm = tuple(v - a[0] for v in a)
    b_norm = tuple(v - b[0] for v in b)
    matches = sum(1 for x, y in zip(a_norm, b_norm, strict=True) if x == y)
    return matches / len(a_norm)


def extract_fragments(
    score: ScoreIR,
    *,
    min_notes: int = 3,
    max_notes: int = 8,
    similarity_threshold: float = 0.7,
) -> list[ExtractedFragment]:
    """Extract recurring melodic fragments from a ScoreIR.

    Scans melody parts for note subsequences that recur with high
    rhythm and interval similarity. Returns fragments sorted by
    occurrence count (descending).

    Args:
        score: The ScoreIR to analyze.
        min_notes: Minimum fragment length.
        max_notes: Maximum fragment length.
        similarity_threshold: Minimum combined similarity to count as recurrence.

    Returns:
        List of ExtractedFragment candidates, sorted by occurrences descending.
    """
    # Collect melody notes from all parts, grouped by section
    all_melody_notes: list[tuple[str, tuple[Note, ...]]] = []
    for section in score.sections:
        for part in section.parts:
            # Filter melody parts by checking instrument name heuristic
            notes = part.notes
            if len(notes) >= min_notes:
                all_melody_notes.append((section.name, notes))

    if not all_melody_notes:
        return []

    # Generate candidate fragments of varying lengths
    candidates: list[tuple[str, tuple[Note, ...]]] = []
    for section_id, notes in all_melody_notes:
        for length in range(min_notes, min(max_notes + 1, len(notes) + 1)):
            for start in range(len(notes) - length + 1):
                fragment = notes[start : start + length]
                candidates.append((section_id, fragment))

    if not candidates:
        return []

    # Compare fragments pairwise and group by similarity
    fragments: list[ExtractedFragment] = []
    used: set[int] = set()

    for i, (sec_i, frag_i) in enumerate(candidates):
        if i in used:
            continue
        rhythm_i = _notes_to_rhythm_shape(frag_i)
        interval_i = _notes_to_interval_shape(frag_i)

        similar_count = 1
        similarity_sum = 1.0

        for j, (_, frag_j) in enumerate(candidates):
            if j <= i or j in used:
                continue
            rhythm_j = _notes_to_rhythm_shape(frag_j)
            interval_j = _notes_to_interval_shape(frag_j)

            r_sim = _rhythm_similarity(rhythm_i, rhythm_j)
            i_sim = _interval_similarity(interval_i, interval_j)
            combined = r_sim * 0.4 + i_sim * 0.6

            if combined >= similarity_threshold:
                similar_count += 1
                similarity_sum += combined
                used.add(j)

        if similar_count >= 2:  # noqa: PLR2004
            fragments.append(
                ExtractedFragment(
                    notes=frag_i,
                    section_id=sec_i,
                    start_beat=frag_i[0].start_beat,
                    occurrences=similar_count,
                    similarity_avg=round(similarity_sum / similar_count, 3),
                )
            )
        used.add(i)

    # Sort by occurrences descending
    fragments.sort(key=lambda f: (-f.occurrences, -f.similarity_avg))
    return fragments


def fragments_to_seeds(
    fragments: list[ExtractedFragment],
    *,
    max_seeds: int = 3,
) -> list[MotifSeed]:
    """Promote the best extracted fragments to MotifSeed objects.

    Args:
        fragments: Candidate fragments from extract_fragments().
        max_seeds: Maximum number of seeds to return.

    Returns:
        List of MotifSeed objects.
    """
    seeds: list[MotifSeed] = []

    for i, frag in enumerate(fragments[:max_seeds]):
        rhythm_shape = _notes_to_rhythm_shape(frag.notes)
        interval_shape = _notes_to_interval_shape(frag.notes)

        seeds.append(
            MotifSeed(
                id=f"EX{i + 1}",
                rhythm_shape=rhythm_shape,
                interval_shape=interval_shape,
                origin_section=frag.section_id,
                character=f"extracted (occurrences={frag.occurrences}, sim={frag.similarity_avg:.2f})",
            )
        )

    return seeds
