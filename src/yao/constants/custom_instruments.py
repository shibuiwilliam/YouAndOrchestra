"""Custom instrument profile definitions.

Non-Western and specialized instrument profiles. Each profile describes range,
GM mapping, idiomatic techniques, and cultural origin.

Belongs to Layer 0 (Constants).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomInstrument:
    """A custom instrument profile for non-GM or non-Western instruments.

    Attributes:
        name: Instrument name (e.g., "shakuhachi", "oud").
        midi_low: Lowest playable MIDI note.
        midi_high: Highest playable MIDI note.
        gm_program: GM program number for approximation (0-indexed).
        custom_sf2_path: Optional path to a dedicated SoundFont.
        cultural_origin: Cultural tradition (e.g., "japanese", "indian").
        idiomatic_techniques: List of characteristic playing techniques.
        typical_velocity_range: Tuple of (min, max) typical velocities.
        typical_scales: List of scale names this instrument commonly uses.
        notes: Additional notes about the instrument.

    Example:
        >>> shaku = load_custom_instrument("shakuhachi")
        >>> shaku.cultural_origin
        'japanese'
    """

    name: str
    midi_low: int
    midi_high: int
    gm_program: int | None = None
    custom_sf2_path: str | None = None
    cultural_origin: str = ""
    idiomatic_techniques: tuple[str, ...] = ()
    typical_velocity_range: tuple[int, int] = (40, 100)
    typical_scales: tuple[str, ...] = ()
    notes: str = ""


# ---------------------------------------------------------------------------
# All custom instrument profiles (inline, no external YAML dependency)
# ---------------------------------------------------------------------------

_CUSTOM_INSTRUMENTS: dict[str, CustomInstrument] = {
    "shakuhachi": CustomInstrument(
        name="shakuhachi",
        midi_low=55,
        midi_high=84,
        gm_program=77,
        cultural_origin="japanese",
        idiomatic_techniques=(
            "meri (pitch bending down by partially closing finger holes)",
            "kari (pitch bending up)",
            "muraiki (breathy, overblown tone for expressive effect)",
            "yuri (vibrato achieved by head movement)",
            "nayashi (slow glissando between notes)",
        ),
        typical_velocity_range=(40, 100),
        typical_scales=("japanese_in", "japanese_ritsu", "hirajoshi"),
        notes=(
            "The shakuhachi is a 5-hole bamboo flute central to Japanese music. "
            "Its breathy tone and pitch flexibility make it ideal for meditative "
            'and expressive contexts. Source: Riley Lee, "The Shakuhachi" (2021).'
        ),
    ),
    "koto": CustomInstrument(
        name="koto",
        midi_low=40,
        midi_high=84,
        gm_program=107,
        cultural_origin="japanese",
        idiomatic_techniques=(
            "oshi (pitch bend by pressing string behind bridge)",
            "chirashi (rapid tremolo)",
            "sukui-zume (upward pluck)",
            "shan (sharp accented pluck with pick)",
            "glissando (sweeping across strings)",
        ),
        typical_velocity_range=(30, 110),
        typical_scales=("hirajoshi", "japanese_in", "japanese_yo"),
        notes=(
            "The koto is a 13-string zither and Japan's national instrument. "
            "Tunings vary; hirajoshi is the most common. Multiple tuning systems "
            'exist for different genres. Source: Fumio Koizumi, "Japanese Music" (1974).'
        ),
    ),
    "shamisen": CustomInstrument(
        name="shamisen",
        midi_low=50,
        midi_high=79,
        gm_program=106,
        cultural_origin="japanese",
        idiomatic_techniques=(
            "bachi strike (percussive plectrum technique)",
            "hajiki (left-hand pizzicato)",
            "suri (slide between notes)",
            "uchi (hammering the string)",
            "sawari (intentional buzzing tone from bridge)",
        ),
        typical_velocity_range=(50, 120),
        typical_scales=("japanese_in", "japanese_minyo", "japanese_yo"),
        notes=(
            "The shamisen has three types (hosozao, chuuzao, futozao) with different "
            "neck widths for different genres. The sawari buzz is a defining timbre "
            'feature. Source: Henry Johnson, "The Shamisen" (2010).'
        ),
    ),
    "taiko": CustomInstrument(
        name="taiko",
        midi_low=36,
        midi_high=60,
        gm_program=116,
        cultural_origin="japanese",
        idiomatic_techniques=(
            "don (center strike, deep tone)",
            "ka (edge strike, higher tone)",
            "su-don (light then heavy stroke)",
            "oroshi (accelerating roll)",
            "katsu (sharp rim shot)",
        ),
        typical_velocity_range=(40, 127),
        typical_scales=(),
        notes=(
            "Taiko encompasses many drum sizes from small shime-daiko to large "
            "o-daiko. Traditionally used in matsuri festivals, theatre, and "
            'Buddhist ceremonies. Source: Rolling Thunder, "The Art of Taiko" (2012).'
        ),
    ),
    "sitar": CustomInstrument(
        name="sitar",
        midi_low=48,
        midi_high=84,
        gm_program=104,
        cultural_origin="indian",
        idiomatic_techniques=(
            "meend (pitch bend/glide between notes, fundamental to raga)",
            "gamak (oscillation around a note)",
            "murki (rapid ornamental turn)",
            "krintan (pull-off similar to guitar)",
            "jhala (rhythmic strumming on drone strings)",
        ),
        typical_velocity_range=(40, 110),
        typical_scales=("raga_yaman", "raga_bhairav", "raga_darbari", "raga_todi"),
        notes=(
            "The sitar has 18-21 strings including sympathetic strings (taraf) "
            "that resonate with the played melody. Meend (pitch bending) is "
            'essential to raga performance. Source: Ravi Shankar, "My Music, My Life" (1968).'
        ),
    ),
    "tabla": CustomInstrument(
        name="tabla",
        midi_low=36,
        midi_high=72,
        gm_program=115,
        cultural_origin="indian",
        idiomatic_techniques=(
            "na/ta (right drum open stroke)",
            "tin (right drum edge stroke)",
            "ge/ghe (left drum open stroke)",
            "dha (combined both-drum stroke)",
            "tirakita (fast ornamental pattern)",
        ),
        typical_velocity_range=(30, 120),
        typical_scales=(),
        notes=(
            "The tabla is a pair of drums (dayan right, bayan left) with "
            "tunable heads. Over 20 distinct stroke types are named using "
            "onomatopoeic syllables (bols). Source: David Courtney, "
            '"Fundamentals of Tabla" (2006).'
        ),
    ),
    "oud": CustomInstrument(
        name="oud",
        midi_low=43,
        midi_high=79,
        gm_program=25,
        cultural_origin="middle_eastern",
        idiomatic_techniques=(
            "risha (plectrum technique with feather-like strokes)",
            "trill (rapid alternation between adjacent notes)",
            "glissando (smooth slide, enabled by fretless neck)",
            "qarar (drone on lowest string)",
            "ajnas (tetrachord-based melodic development)",
        ),
        typical_velocity_range=(35, 105),
        typical_scales=("maqam_rast", "maqam_bayati", "maqam_hijaz", "maqam_nahawand"),
        notes=(
            "The oud is the ancestor of the European lute. Its fretless neck "
            "allows microtonal inflections essential to maqam performance. "
            "Standard tuning uses 11 or 13 strings. Source: Ali Jihad Racy, "
            '"Making Music in the Arab World" (2003).'
        ),
    ),
    "ney": CustomInstrument(
        name="ney",
        midi_low=55,
        midi_high=86,
        gm_program=72,
        cultural_origin="middle_eastern",
        idiomatic_techniques=(
            "nefes (breath control for dynamics and tone color)",
            "vibrato (achieved by jaw movement or finger shading)",
            "trill (rapid finger movement between adjacent holes)",
            "glissando (half-holing for microtonal slides)",
            "karar (settling on the tonic with ornamental approach)",
        ),
        typical_velocity_range=(30, 95),
        typical_scales=("maqam_rast", "maqam_bayati", "maqam_hijaz", "maqam_kurd"),
        notes=(
            "The ney is one of the oldest wind instruments (5000+ years). Its "
            "breathy, haunting tone is central to Sufi music and Arabic/Turkish "
            "classical traditions. Microtonal capability through half-holing. "
            'Source: Kudsi Erguner, "Journeys of a Sufi Musician" (2005).'
        ),
    ),
    # Chinese traditional
    "guzheng": CustomInstrument(
        name="guzheng",
        midi_low=48,
        midi_high=96,
        gm_program=107,
        cultural_origin="chinese",
        idiomatic_techniques=(
            "yao-zhi (tremolo by rapidly plucking with right hand)",
            "hua-zhi (glissando sweeping across strings)",
            "an (pitch bend by pressing string left of bridge)",
            "dian (staccato pluck with fingertip)",
            "gou-tuo (alternating inward/outward pluck for melodic runs)",
        ),
        typical_velocity_range=(30, 110),
        typical_scales=("pentatonic_gong", "pentatonic_shang", "pentatonic_yu"),
        notes=(
            "The guzheng is a 21-string Chinese zither with movable bridges. "
            "It is one of the oldest Chinese instruments, central to both solo "
            "and ensemble music. Tuned to pentatonic scales with pitch bending "
            "enabling chromatic and microtonal inflections. The Japanese koto "
            "is historically derived from the guzheng."
        ),
    ),
    "erhu": CustomInstrument(
        name="erhu",
        midi_low=55,
        midi_high=86,
        gm_program=40,
        cultural_origin="chinese",
        idiomatic_techniques=(
            "rou-xian (vibrato by oscillating left-hand finger pressure)",
            "hua-yin (portamento slide between notes)",
            "dun-gong (staccato bowing)",
            "lian-gong (legato connected bowing)",
            "pao-yin (thrown bow for accented attack)",
        ),
        typical_velocity_range=(35, 100),
        typical_scales=("pentatonic_gong", "pentatonic_shang", "pentatonic_yu"),
        notes=(
            "The erhu is a two-string bowed instrument with no fingerboard; "
            "the player presses strings without touching the neck. Its vocal, "
            "expressive tone is often compared to the human voice. Central to "
            "Chinese opera, folk, and classical ensemble music. Range spans "
            "approximately three octaves with skilled players."
        ),
    ),
    "dizi": CustomInstrument(
        name="dizi",
        midi_low=62,
        midi_high=86,
        gm_program=73,
        cultural_origin="chinese",
        idiomatic_techniques=(
            "li-yin (grace note ornament)",
            "da-yin (tongued articulation)",
            "hua-she (tongue flutter/tremolo)",
            "die-yin (rapid finger trill)",
            "mo-yin (membrane vibrato from the di-mo buzzing membrane)",
        ),
        typical_velocity_range=(35, 95),
        typical_scales=("pentatonic_gong", "pentatonic_shang", "pentatonic_yu"),
        notes=(
            "The dizi is a transverse bamboo flute distinguished by its di-mo, "
            "a thin membrane covering one hole that produces a characteristic "
            "bright, buzzing timbre. Two main types: qudi (longer, for kunqu "
            "opera) and bangdi (shorter, brighter, for northern folk music). "
            "One of the earliest Chinese instruments, dating back 8000+ years."
        ),
    ),
    "pipa": CustomInstrument(
        name="pipa",
        midi_low=45,
        midi_high=76,
        gm_program=104,
        cultural_origin="chinese",
        idiomatic_techniques=(
            "lun-zhi (tremolo by rolling all five fingers in rapid succession)",
            "tan-tiao (alternating outward/inward single plucks)",
            "sao (rapid downward sweep across strings)",
            "ban (percussive slap on strings against frets)",
            "tui-la (pitch bend by pushing/pulling string laterally)",
        ),
        typical_velocity_range=(30, 120),
        typical_scales=("pentatonic_gong", "pentatonic_shang", "pentatonic_yu"),
        notes=(
            "The pipa is a four-string pear-shaped lute with 12-26 frets. "
            "Known for both lyrical sustained passages and dramatic percussive "
            "techniques. A cornerstone of Chinese classical and court music "
            "since the Han dynasty. Its wide dynamic range spans from delicate "
            "single notes to powerful strummed chords."
        ),
    ),
    "bianzhong": CustomInstrument(
        name="bianzhong",
        midi_low=48,
        midi_high=84,
        gm_program=14,
        cultural_origin="chinese",
        idiomatic_techniques=(
            "zheng-gu (center strike for fundamental tone)",
            "ce-gu (side strike for a note a third higher)",
            "dan-ji (single ceremonial strike with wooden mallet)",
            "lian-ji (successive strikes across bells for melodic passage)",
            "yu-yin (letting bell ring to full natural decay)",
        ),
        typical_velocity_range=(40, 95),
        typical_scales=("pentatonic_gong", "pentatonic_shang"),
        notes=(
            "Bianzhong are ancient Chinese bronze bell chimes, typically 65 "
            "bells arranged in a frame spanning five octaves. Each bell produces "
            "two pitches depending on strike location. Central to yayue court "
            "ritual music. The most famous set is from the tomb of Marquis Yi "
            "of Zeng (433 BCE), demonstrating sophisticated tuning systems."
        ),
    ),
}


def load_custom_instrument(name: str) -> CustomInstrument:
    """Load a named custom instrument profile.

    Args:
        name: Instrument name (e.g., "shakuhachi"). Must be a known profile.

    Returns:
        The CustomInstrument.

    Raises:
        FileNotFoundError: If the instrument name is not known.
    """
    if name not in _CUSTOM_INSTRUMENTS:
        msg = f"Custom instrument '{name}' not found"
        raise FileNotFoundError(msg)
    return _CUSTOM_INSTRUMENTS[name]


def available_custom_instruments() -> list[str]:
    """Return names of all available custom instrument profiles.

    Returns:
        Sorted list of instrument names.
    """
    return sorted(_CUSTOM_INSTRUMENTS)
