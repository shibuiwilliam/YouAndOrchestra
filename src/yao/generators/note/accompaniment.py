"""Accompaniment rendering for the v2 note realizers (P1.1 prerequisite).

The v2 realizers (``stochastic_v2``, ``rule_based_v2``) historically produced
only a single melody ``Part`` per section, ignoring harmony/bass/pad
instruments. That made them non-viable as a default (flipping to them would
drop all accompaniment). This module renders the missing non-melody parts
directly from the plan's ``ChordEvent`` stream so the v2 realizers produce
complete arrangements.

Voicings here are deliberately simple and correct (block chords for
harmony/pad, a per-bar root pulse for bass). Richer voice-leading and voicing
styles are a separate concern (PROJECT_IMPROVEMENT §P1.3).

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from yao.constants.music import SCALE_INTERVALS
from yao.ir.harmony import ChordFunction, diatonic_quality
from yao.ir.harmony import realize as realize_chord
from yao.ir.note import Note
from yao.ir.plan.harmony import ChordEvent
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.voicing import Voicing, check_parallel_fifths, check_parallel_octaves

if TYPE_CHECKING:
    from yao.schema.composition import CompositionSpec

# Accompaniment sits under the melody dynamically. These are structural
# balance factors (accompaniment softer than the lead), not hardcoded
# velocities — the base velocity is still derived from section tension.
_HARMONY_VELOCITY_FACTOR = 0.72
_BASS_VELOCITY_FACTOR = 0.85
# counter_melody is sparse but strong: fewer re-attacks, louder relative velocity
_COUNTER_MELODY_DENSITY_SCALE = 0.45  # forces "one voicing per chord" reattack rate
_COUNTER_MELODY_VELOCITY_FACTOR = 0.95  # sits just under melody level

# Register placement.
_BASS_OCTAVE_DROP = 24  # two octaves below the realized chord root
_MIN_BASS_PITCH = 28
_MAX_HARMONY_VOICES = 4

_ROMAN_DEGREE: dict[str, int] = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}


def instrument_roles(plan: MusicalPlan) -> list[tuple[str, str]]:
    """Return ordered (instrument, role) pairs for a plan.

    Prefers ``GlobalContext.instruments`` (which carries roles); falls back to
    the arrangement plan's assignments (first role seen per instrument), then
    to a single piano melody. Shared by both v2 realizers so melody and
    accompaniment agree on the instrument roster.

    Args:
        plan: The musical plan.

    Returns:
        Ordered list of (instrument_name, role) pairs (never empty).
    """
    ctx = plan.global_context
    if ctx.instruments:
        return [(name, role) for name, role in ctx.instruments]
    if plan.arrangement and plan.arrangement.assignments:
        seen: dict[str, str] = {}
        for assignment in plan.arrangement.assignments:
            role = assignment.role.value if hasattr(assignment.role, "value") else str(assignment.role)
            seen.setdefault(assignment.instrument, role)
        return list(seen.items())
    return [("piano", "melody")]


def chord_pitches(chord_event: ChordEvent, key_root: str, scale_type: str) -> list[int]:
    """Realize a ``ChordEvent``'s roman numeral to MIDI pitches (octave 4).

    Mirrors the realizers' internal chord realization so accompaniment and
    melody agree on harmony.

    Args:
        chord_event: The chord to realize.
        key_root: Key root note name (e.g. "F").
        scale_type: Scale/mode name (e.g. "major").

    Returns:
        Ascending MIDI pitches for the chord (empty only on total failure).
    """
    cleaned = chord_event.roman.strip().replace("b", "").replace("#", "")
    base = cleaned.rstrip("7").rstrip("maj").rstrip("dim").rstrip("aug")
    degree = _ROMAN_DEGREE.get(base.lower(), 0)
    quality = diatonic_quality(degree, scale_type)
    if "7" in chord_event.roman:
        quality = "dom7" if quality == "maj" else "min7"
    # Harmonic-minor dominant: render the V as a major/dominant chord (raised
    # leading tone) in minor keys so the dominant actually pulls to the tonic
    # — natural-minor v has no leading tone and makes a weak cadence.
    if degree == 4 and "minor" in scale_type:  # noqa: PLR2004
        quality = "dom7" if "7" in chord_event.roman else "maj"
    try:
        return realize_chord(ChordFunction(degree=degree, quality=quality), key_root, scale_type, octave=4)
    except Exception:
        from yao.ir.notation import note_name_to_midi

        root = note_name_to_midi(f"{key_root}4")
        return [root, root + 4, root + 7]


def _clamp(pitch: int, lo: int = 0, hi: int = 127) -> int:
    return max(lo, min(hi, pitch))


def _nearest_pitch_with_pc(target: int, pitch_class: int) -> int:
    """Return the pitch of the given pitch-class nearest to ``target``."""
    base = target - (target % 12) + pitch_class
    return min((base - 12, base, base + 12), key=lambda q: abs(q - target))


def _lead_voice(prev_pitch: int, next_pcs: list[int]) -> int:
    """Move one voice to its nearest chord tone in the next chord."""
    best_pc = min(next_pcs, key=lambda pc: abs(_nearest_pitch_with_pc(prev_pitch, pc) - prev_pitch))
    return _nearest_pitch_with_pc(prev_pitch, best_pc)


def voice_lead_sequence(
    chord_pitch_lists: list[list[int]],
    num_voices: int = 3,
) -> list[list[int]]:
    """Voice-lead a sequence of chords for smooth, connected motion.

    Each chord after the first is voiced by moving every voice to its nearest
    chord tone (nearest-tone voice leading), then a light repair pass nudges a
    voice off any parallel fifth/octave it introduced against the previous
    chord. This replaces block root-position chords (which lurch to root each
    time) with connected inner-voice motion.

    Args:
        chord_pitch_lists: Per-chord ascending MIDI pitches (root position).
        num_voices: Number of voices to keep (bounded by the first chord).

    Returns:
        One ascending voicing per input chord (same length).
    """
    voicings: list[list[int]] = []
    prev: list[int] | None = None
    for pitches in chord_pitch_lists:
        if not pitches:
            voicings.append([])
            continue
        pcs = sorted({p % 12 for p in pitches})
        if prev is None:
            voicing = sorted(pitches[:num_voices])
        else:
            voicing = sorted(_lead_voice(p, pcs) for p in prev)
            voicing = _repair_parallels(prev, voicing, pcs)
        voicings.append(voicing)
        prev = voicing
    return voicings


def _repair_parallels(prev: list[int], voicing: list[int], next_pcs: list[int]) -> list[int]:
    """Best-effort single-pass removal of parallel fifths/octaves.

    Reassigns the highest offending voice to its second-nearest chord tone.
    """
    va = Voicing(pitches=tuple(prev))
    vb = Voicing(pitches=tuple(voicing))
    offenders = check_parallel_fifths(va, vb) + check_parallel_octaves(va, vb)
    if not offenders:
        return voicing
    # Move the upper voice of the first offending pair to an alternative tone.
    voice_idx = max(offenders[0])
    if voice_idx >= len(voicing):
        return voicing
    target = prev[voice_idx] if voice_idx < len(prev) else voicing[voice_idx]
    alternatives = sorted(
        (_nearest_pitch_with_pc(target, pc) for pc in next_pcs),
        key=lambda q: abs(q - target),
    )
    for alt in alternatives:
        if alt != voicing[voice_idx]:
            repaired = list(voicing)
            repaired[voice_idx] = alt
            return sorted(repaired)
    return voicing


# Density bands that shape how busy the accompaniment is per section, so
# sparse and dense sections contrast instead of every section sounding alike.
_DENSITY_SPARSE = 0.4
_DENSITY_BUSY = 0.7


def _bass_pulse(density: float, beats_per_bar: float) -> float:
    """Bass pulse interval (beats) from section density: sparser → longer."""
    if density < _DENSITY_SPARSE:
        return max(beats_per_bar, 1.0)  # root once per bar
    if density < _DENSITY_BUSY:
        return max(beats_per_bar / 2.0, 1.0)  # twice per bar
    return 1.0  # once per beat


def _harmony_reattack(density: float, chord_duration: float) -> float:
    """Chord re-attack interval (beats): sustained when sparse, rhythmic when busy."""
    if density < _DENSITY_SPARSE:
        return chord_duration  # one sustained voicing per chord
    if density < _DENSITY_BUSY:
        return 2.0  # re-attack every half-bar
    return 1.0  # comp on every beat


def realize_harmony_part(
    instrument: str,
    section_chords: list[ChordEvent],
    key_root: str,
    scale_type: str,
    base_velocity: int,
    density: float = 0.5,
) -> list[Note]:
    """Render a voice-led block-chord part (harmony/pad/rhythm), density-aware.

    Voicings are voice-led across the section for smooth motion. Sparse
    sections hold one voicing per chord; busier sections re-attack the voicing
    rhythmically (every half-bar, then every beat), so section density
    contrasts.

    Args:
        instrument: Instrument name for the emitted notes.
        section_chords: Chord events belonging to the section.
        key_root: Key root note name.
        scale_type: Scale/mode name.
        base_velocity: Section base velocity (derived from tension).
        density: Section target density [0, 1] controlling re-attack rate.

    Returns:
        The chord-comping notes for the section.
    """
    velocity = _clamp(int(base_velocity * _HARMONY_VELOCITY_FACTOR), 1, 127)
    root_position = [chord_pitches(chord, key_root, scale_type)[:_MAX_HARMONY_VOICES] for chord in section_chords]
    voicings = voice_lead_sequence(root_position, num_voices=_MAX_HARMONY_VOICES)

    notes: list[Note] = []
    for chord, voicing in zip(section_chords, voicings, strict=True):
        interval = _harmony_reattack(density, chord.duration_beats)
        beat = chord.start_beat
        end = chord.end_beat()
        while beat < end - 1e-6:
            dur = min(interval, end - beat)
            for pitch in voicing:
                notes.append(
                    Note(
                        pitch=_clamp(pitch),
                        start_beat=beat,
                        duration_beats=dur,
                        velocity=velocity,
                        instrument=instrument,
                    )
                )
            beat += interval
    return notes


def realize_bass_part(
    instrument: str,
    section_chords: list[ChordEvent],
    key_root: str,
    scale_type: str,
    base_velocity: int,
    beats_per_bar: float,
    density: float = 0.5,
) -> list[Note]:
    """Render a bass part: the chord root pulsed, density-aware.

    Sparse sections pulse once per bar; busier sections pulse twice per bar,
    then once per beat — giving low- vs high-energy sections a different feel.

    Args:
        instrument: Instrument name for the emitted notes.
        section_chords: Chord events belonging to the section.
        key_root: Key root note name.
        scale_type: Scale/mode name.
        base_velocity: Section base velocity (derived from tension).
        beats_per_bar: Beats per bar.
        density: Section target density [0, 1] controlling pulse rate.

    Returns:
        The bass notes for the section.
    """
    velocity = _clamp(int(base_velocity * _BASS_VELOCITY_FACTOR), 1, 127)
    pulse = _bass_pulse(density, beats_per_bar)
    notes: list[Note] = []
    for chord in section_chords:
        pitches = chord_pitches(chord, key_root, scale_type)
        if not pitches:
            continue
        root = _clamp(pitches[0] - _BASS_OCTAVE_DROP, _MIN_BASS_PITCH, 127)
        beat = chord.start_beat
        end = chord.end_beat()
        while beat < end - 1e-6:
            dur = min(pulse, end - beat)
            notes.append(
                Note(
                    pitch=root,
                    start_beat=beat,
                    duration_beats=dur,
                    velocity=velocity,
                    instrument=instrument,
                )
            )
            beat += pulse
    return notes


def realize_walking_bass(
    instrument: str,
    section_chords: list[ChordEvent],
    key_root: str,
    scale_type: str,
    base_velocity: int,
) -> list[Note]:
    """Render a walking bass: a quarter-note line connecting the chords.

    The classic jazz/blues idiom — root on the downbeat, chord tones through
    the middle of the bar, and a chromatic approach tone leading into the next
    chord's root. Gives the bass forward motion instead of a static pulse.

    Args:
        instrument: Instrument name for the emitted notes.
        section_chords: Chord events belonging to the section.
        key_root: Key root note name.
        scale_type: Scale/mode name.
        base_velocity: Section base velocity (derived from tension).

    Returns:
        Quarter-note walking-bass notes for the section.
    """
    velocity = _clamp(int(base_velocity * _BASS_VELOCITY_FACTOR), 1, 127)
    chords = sorted(section_chords, key=lambda c: c.start_beat)
    notes: list[Note] = []
    for i, chord in enumerate(chords):
        pitches = chord_pitches(chord, key_root, scale_type)
        if not pitches:
            continue
        tones = [_clamp(p - _BASS_OCTAVE_DROP, _MIN_BASS_PITCH, 127) for p in pitches]
        root = tones[0]
        next_root: int | None = None
        if i + 1 < len(chords):
            nxt = chord_pitches(chords[i + 1], key_root, scale_type)
            if nxt:
                next_root = _clamp(nxt[0] - _BASS_OCTAVE_DROP, _MIN_BASS_PITCH, 127)

        beat = chord.start_beat
        end = chord.end_beat()
        n_beats = max(1, int(round(end - beat)))
        for b in range(n_beats):
            if b == 0:
                pitch = root  # downbeat: the root
            elif b == n_beats - 1 and next_root is not None and next_root != root:
                # Approach the next root chromatically from a half-step away.
                pitch = _clamp(next_root - 1 if next_root >= root else next_root + 1, _MIN_BASS_PITCH, 127)
            else:
                pitch = tones[b % len(tones)]  # chord tones through the middle
            notes.append(
                Note(
                    pitch=pitch,
                    start_beat=beat + b,
                    duration_beats=1.0,
                    velocity=velocity,
                    instrument=instrument,
                )
            )
    return notes


def realize_accompaniment_for_role(
    role: str,
    instrument: str,
    section_chords: list[ChordEvent],
    key_root: str,
    scale_type: str,
    base_velocity: int,
    beats_per_bar: float,
    density: float = 0.5,
    walking_bass: bool = False,
    velocity_boost: int = 0,
) -> list[Note]:
    """Dispatch a non-melody instrument to the appropriate renderer.

    ``bass`` → walking line (when ``walking_bass``) or density-aware root
    pulse; ``counter_melody`` → sparse sustained voicings at near-melody
    velocity; everything else (harmony/pad/rhythm) → block-chord comping.
    ``density`` shapes how busy the part is, so sections contrast.

    Args:
        role: The instrument's musical role.
        instrument: Instrument name for the emitted notes.
        section_chords: Chord events belonging to the section.
        key_root: Key root note name.
        scale_type: Scale/mode name.
        base_velocity: Section base velocity (derived from tension).
        beats_per_bar: Beats per bar.
        density: Section target density [0, 1].
        walking_bass: When True and role is bass, render a walking line
            (jazz/blues idiom) instead of a root pulse.
        velocity_boost: Per-instrument velocity offset from InstrumentSpec
            (applied after role-based velocity scaling).

    Returns:
        The rendered accompaniment notes (empty if no chords).
    """
    if not section_chords:
        return []
    if role == "bass":
        if walking_bass:
            notes = realize_walking_bass(instrument, section_chords, key_root, scale_type, base_velocity)
        else:
            notes = realize_bass_part(
                instrument, section_chords, key_root, scale_type, base_velocity, beats_per_bar, density
            )
    elif role == "counter_melody":
        # Counter-melody: one sustained voicing per chord (below sparse threshold),
        # at near-melody velocity so it cuts through as a strong secondary voice.
        counter_velocity = _clamp(int(base_velocity * _COUNTER_MELODY_VELOCITY_FACTOR), 1, 127)
        notes = realize_harmony_part(
            instrument,
            section_chords,
            key_root,
            scale_type,
            counter_velocity,
            density * _COUNTER_MELODY_DENSITY_SCALE,
        )
    else:
        notes = realize_harmony_part(instrument, section_chords, key_root, scale_type, base_velocity, density)
    if velocity_boost != 0:
        notes = [
            Note(
                pitch=n.pitch,
                start_beat=n.start_beat,
                duration_beats=n.duration_beats,
                velocity=_clamp(n.velocity + velocity_boost, 1, 127),
                instrument=n.instrument,
            )
            for n in notes
        ]
    return notes


def build_recall_map(original_spec: CompositionSpec | None) -> dict[str, str]:
    """Map each section that recalls a theme to its source section name.

    Reads ``recall_melody_from`` from the v1 spec (which the v2 realizers
    receive as ``original_spec``). This is how the ``thematic_development``
    feature reaches the plan-consuming realizers so return sections restate
    the theme — matching the legacy generator's behavior.

    Args:
        original_spec: The v1 composition spec, or None.

    Returns:
        ``{section_name: source_section_name}`` (empty if none / no spec).
    """
    if original_spec is None:
        return {}
    return {s.name: s.recall_melody_from for s in original_spec.sections if s.recall_melody_from}


def restate_melody(
    source_notes: list[Note],
    source_start_beat: float,
    target_start_beat: float,
    instrument: str,
) -> list[Note]:
    """Restate a theme in a return section by time-shifting the source melody.

    Preserves pitch, duration, and velocity; only the onset is offset to the
    target section. This yields a faithful thematic restatement (A → A′).

    Args:
        source_notes: The source section's melody notes.
        source_start_beat: Beat at which the source section starts.
        target_start_beat: Beat at which the return section starts.
        instrument: Instrument name for the restated notes.

    Returns:
        The restated notes positioned in the target section.
    """
    offset = target_start_beat - source_start_beat
    return [
        Note(
            pitch=n.pitch,
            start_beat=max(0.0, n.start_beat + offset),
            duration_beats=n.duration_beats,
            velocity=n.velocity,
            instrument=instrument,
        )
        for n in source_notes
    ]


# Blue notes relative to the key root pitch-class: b3, b5, b7.
_BLUE_NOTE_OFFSETS: tuple[int, ...] = (3, 6, 10)


def _scale_pitch_classes(key_root: str, scale_type: str) -> set[int]:
    """Pitch classes belonging to ``scale_type`` rooted at ``key_root``."""
    from yao.ir.notation import note_name_to_midi

    root_pc = note_name_to_midi(f"{key_root}4") % 12
    intervals = SCALE_INTERVALS.get(scale_type) or SCALE_INTERVALS.get("major", (0, 2, 4, 5, 7, 9, 11))
    return {(root_pc + i) % 12 for i in intervals}


def _nearest_scale_pitch(pitch: int, scale_pcs: set[int], direction: int) -> int:
    """Nearest pitch in ``direction`` (+1 up / -1 down) whose pc is in scale."""
    probe = pitch + direction
    for _ in range(4):
        if probe % 12 in scale_pcs:
            return probe
        probe += direction
    return pitch


def _chord_containing(chords: list[ChordEvent], beat: float) -> ChordEvent | None:
    """The chord active at ``beat`` (absolute), or None."""
    for chord in chords:
        if chord.start_beat <= beat < chord.end_beat():
            return chord
    return None


def develop_melody(
    source_notes: list[Note],
    source_start_beat: float,
    target_start_beat: float,
    instrument: str,
    *,
    key_root: str,
    scale_type: str,
    section_chords: list[ChordEvent],
    variation: float,
    rng: random.Random,
    allow_blue: bool = False,
) -> list[Note]:
    """Restate a theme with genre-appropriate variation (development, not copy).

    Unlike :func:`restate_melody` (which copies the theme note-for-note), this
    produces a *developed* restatement: the opening and closing notes are held
    as phrase anchors so the theme stays recognizable, while a ``variation``
    fraction of interior notes are re-voiced to nearby chord tones, scale
    neighbours, blue notes, or an octave displacement. Note count, rhythm, and
    velocities are preserved (so aligned thematic similarity degrades smoothly
    from 1.0 toward ``1 - variation`` rather than collapsing), keeping the
    ``motif_development_index`` metric meaningful while removing the mechanical
    "same melody every return" monotony.

    Args:
        source_notes: The source section's melody notes.
        source_start_beat: Beat at which the source section starts.
        target_start_beat: Beat at which the return section starts.
        instrument: Instrument name for the restated notes.
        key_root: Key root note name (e.g. "D").
        scale_type: Scale/mode name (e.g. "minor").
        section_chords: The *target* section's chord events (absolute beats).
        variation: Fraction of interior notes to vary (0.0 = exact copy).
        rng: A ``random.Random``-compatible source.
        allow_blue: Whether blue notes (b3/b5/b7) are idiomatic for the genre.

    Returns:
        The developed restatement positioned in the target section.
    """
    if not source_notes or variation <= 0.0:
        return restate_melody(source_notes, source_start_beat, target_start_beat, instrument)

    from yao.ir.notation import note_name_to_midi

    offset = target_start_beat - source_start_beat
    scale_pcs = _scale_pitch_classes(key_root, scale_type)
    root_pc = note_name_to_midi(f"{key_root}4") % 12
    blue_pcs = {(root_pc + o) % 12 for o in _BLUE_NOTE_OFFSETS}
    n_notes = len(source_notes)

    result: list[Note] = []
    for idx, note in enumerate(source_notes):
        pitch = note.pitch
        target_beat = note.start_beat + offset
        is_anchor = idx == 0 or idx == n_notes - 1
        if not is_anchor and rng.random() < variation:
            roll = rng.random()
            chord = _chord_containing(section_chords, target_beat)
            chord_pcs = {p % 12 for p in chord_pitches(chord, key_root, scale_type)} if chord else set()
            if allow_blue and roll < 0.20:  # noqa: PLR2004
                target_pc = min(blue_pcs, key=lambda pc: abs(_nearest_pitch_with_pc(pitch, pc) - pitch))
                pitch = _nearest_pitch_with_pc(pitch, target_pc)
            elif chord_pcs and roll < 0.55:  # noqa: PLR2004
                cands = [_nearest_pitch_with_pc(pitch, pc) for pc in chord_pcs]
                distinct = [c for c in cands if c != pitch] or cands
                pitch = min(distinct, key=lambda c: abs(c - pitch))
            elif roll < 0.85:  # noqa: PLR2004
                pitch = _nearest_scale_pitch(pitch, scale_pcs, rng.choice((-1, 1)))
            else:
                pitch += rng.choice((-12, 12))
            pitch = _clamp(pitch, 36, 88)
        result.append(
            Note(
                pitch=pitch,
                start_beat=max(0.0, target_beat),
                duration_beats=note.duration_beats,
                velocity=note.velocity,
                instrument=instrument,
            )
        )
    return result


def genre_melodic_variation(genre_profile: object | None, recall_index: int) -> float:
    """Derive a theme-development variation amount from the genre profile.

    Genres with wider leaps / more blue notes / more syncopation develop their
    themes more freely on return; conservative genres (ambient, mainstream pop)
    keep the hook nearly intact. Each successive return develops a little
    further (A′ < A″ < …), matching how real variations intensify.

    Args:
        genre_profile: The resolved :class:`GenreProfile`, or None.
        recall_index: 1-based count of how many times this theme has returned.

    Returns:
        A variation fraction in ``[0.0, 0.6]``.
    """
    if genre_profile is None:
        base = 0.22
    else:
        leap = float(getattr(genre_profile, "leap_probability", 0.3))
        blue = float(getattr(genre_profile, "blue_note_probability", 0.0))
        sync = float(getattr(genre_profile, "syncopation_density", 0.3))
        base = 0.5 * leap + 0.5 * blue + 0.2 * sync
    scaled = base * (1.0 + 0.4 * max(0, recall_index - 1))
    return max(0.0, min(0.6, scaled))
