"""Song form definitions — structural templates for compositions.

Each form defines a section sequence with bar counts, roles, and
typical use cases. Forms are reference data, not aesthetic judgments.

YAML overrides in forms/ directory are optional and extend this library.

Belongs to Layer 0 (Constants).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FormSection:
    """A section within a form template.

    Attributes:
        id: Section identifier (e.g., "verse_a", "chorus").
        bars: Default number of bars.
        role: Structural role.
        density: Default target density [0, 1].
        tension: Default target tension [0, 1].
    """

    id: str
    bars: int
    role: str
    density: float = 0.5
    tension: float = 0.5


@dataclass(frozen=True)
class SongForm:
    """A complete song form template.

    Attributes:
        id: Unique form identifier (e.g., "aaba_32bar").
        name: Human-readable name.
        sections: Ordered sequence of sections.
        typical_genres: Genres commonly using this form.
        total_bars: Computed total bar count.
        description: Brief description of the form.
    """

    id: str
    name: str
    sections: tuple[FormSection, ...]
    typical_genres: tuple[str, ...] = ()
    description: str = ""

    @property
    def total_bars(self) -> int:
        """Total number of bars in the form."""
        return sum(s.bars for s in self.sections)

    @property
    def section_ids(self) -> list[str]:
        """Ordered list of section IDs."""
        return [s.id for s in self.sections]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "name": self.name,
            "sections": [
                {"id": s.id, "bars": s.bars, "role": s.role, "density": s.density, "tension": s.tension}
                for s in self.sections
            ],
            "typical_genres": list(self.typical_genres),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SongForm:
        """Deserialize from dict."""
        sections = tuple(
            FormSection(
                id=s["id"],
                bars=s["bars"],
                role=s["role"],
                density=s.get("density", 0.5),
                tension=s.get("tension", 0.5),
            )
            for s in data["sections"]
        )
        return cls(
            id=data["id"],
            name=data["name"],
            sections=sections,
            typical_genres=tuple(data.get("typical_genres", [])),
            description=data.get("description", ""),
        )


# ---------------------------------------------------------------------------
# Form Library — 20 forms
# ---------------------------------------------------------------------------

FORM_LIBRARY: dict[str, SongForm] = {}


def _register(form: SongForm) -> SongForm:
    """Register a form in the library."""
    FORM_LIBRARY[form.id] = form
    return form


_register(
    SongForm(
        id="aaba_32bar",
        name="AABA 32-Bar",
        sections=(
            FormSection(id="a1", bars=8, role="verse", density=0.5, tension=0.4),
            FormSection(id="a2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="b", bars=8, role="bridge", density=0.6, tension=0.7),
            FormSection(id="a3", bars=8, role="verse", density=0.5, tension=0.5),
        ),
        typical_genres=("jazz_ballad", "tin_pan_alley", "standards"),
        description="Classic 32-bar AABA with bridge as contrasting middle section.",
    )
)

_register(
    SongForm(
        id="verse_chorus_bridge",
        name="Verse-Chorus-Bridge",
        sections=(
            FormSection(id="intro", bars=4, role="intro", density=0.3, tension=0.2),
            FormSection(id="verse_1", bars=8, role="verse", density=0.5, tension=0.4),
            FormSection(id="chorus_1", bars=8, role="chorus", density=0.8, tension=0.8),
            FormSection(id="verse_2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="chorus_2", bars=8, role="chorus", density=0.8, tension=0.85),
            FormSection(id="bridge", bars=8, role="bridge", density=0.6, tension=0.7),
            FormSection(id="chorus_3", bars=8, role="chorus", density=0.9, tension=0.95),
            FormSection(id="outro", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("pop", "rock", "j_pop"),
        description="Standard pop form with verse-chorus alternation and bridge for contrast.",
    )
)

_register(
    SongForm(
        id="rondo_abacaba",
        name="Rondo ABACABA",
        sections=(
            FormSection(id="a1", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="b", bars=8, role="bridge", density=0.6, tension=0.6),
            FormSection(id="a2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="c", bars=8, role="solo", density=0.7, tension=0.7),
            FormSection(id="a3", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="b2", bars=8, role="bridge", density=0.6, tension=0.6),
            FormSection(id="a4", bars=8, role="verse", density=0.5, tension=0.4),
        ),
        typical_genres=("classical", "neoclassical"),
        description="Rondo form with recurring A section and contrasting episodes.",
    )
)

_register(
    SongForm(
        id="through_composed",
        name="Through-Composed",
        sections=(
            FormSection(id="section_1", bars=8, role="verse", density=0.4, tension=0.3),
            FormSection(id="section_2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="section_3", bars=8, role="bridge", density=0.6, tension=0.7),
            FormSection(id="section_4", bars=8, role="verse", density=0.7, tension=0.8),
            FormSection(id="section_5", bars=8, role="outro", density=0.4, tension=0.3),
        ),
        typical_genres=("cinematic", "ambient", "art_song"),
        description="No repeating sections; continuous development throughout.",
    )
)

_register(
    SongForm(
        id="intro_loop_outro",
        name="Intro-Loop-Outro",
        sections=(
            FormSection(id="intro", bars=4, role="intro", density=0.3, tension=0.2),
            FormSection(id="loop_a", bars=8, role="verse", density=0.6, tension=0.5),
            FormSection(id="loop_b", bars=8, role="verse", density=0.6, tension=0.6),
            FormSection(id="outro", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("game_bgm", "lofi_hiphop", "ambient"),
        description="Loopable BGM with brief intro/outro bookends.",
    )
)

_register(
    SongForm(
        id="arch_form_abcba",
        name="Arch Form ABCBA",
        sections=(
            FormSection(id="a1", bars=8, role="intro", density=0.3, tension=0.3),
            FormSection(id="b1", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="c", bars=8, role="chorus", density=0.8, tension=0.9),
            FormSection(id="b2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="a2", bars=8, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("cinematic", "orchestral", "neoclassical"),
        description="Symmetrical arch with climax at center.",
    )
)

_register(
    SongForm(
        id="binary_ab",
        name="Binary AB",
        sections=(
            FormSection(id="a", bars=16, role="verse", density=0.5, tension=0.5),
            FormSection(id="b", bars=16, role="chorus", density=0.7, tension=0.7),
        ),
        typical_genres=("baroque", "folk"),
        description="Two contrasting sections.",
    )
)

_register(
    SongForm(
        id="ternary_aba",
        name="Ternary ABA",
        sections=(
            FormSection(id="a1", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="b", bars=8, role="bridge", density=0.6, tension=0.7),
            FormSection(id="a2", bars=8, role="verse", density=0.5, tension=0.4),
        ),
        typical_genres=("classical", "jazz_ballad"),
        description="Statement-contrast-return.",
    )
)

_register(
    SongForm(
        id="theme_and_variations",
        name="Theme and Variations",
        sections=(
            FormSection(id="theme", bars=8, role="verse", density=0.4, tension=0.4),
            FormSection(id="var_1", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="var_2", bars=8, role="verse", density=0.6, tension=0.6),
            FormSection(id="var_3", bars=8, role="chorus", density=0.7, tension=0.8),
            FormSection(id="coda", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("classical", "neoclassical", "jazz_ballad"),
        description="Theme stated then varied with increasing complexity.",
    )
)

_register(
    SongForm(
        id="verse_prechorus_chorus",
        name="Verse-PreChorus-Chorus",
        sections=(
            FormSection(id="intro", bars=4, role="intro", density=0.3, tension=0.2),
            FormSection(id="verse_1", bars=8, role="verse", density=0.5, tension=0.4),
            FormSection(id="prechorus_1", bars=4, role="pre_chorus", density=0.6, tension=0.6),
            FormSection(id="chorus_1", bars=8, role="chorus", density=0.8, tension=0.8),
            FormSection(id="verse_2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="prechorus_2", bars=4, role="pre_chorus", density=0.7, tension=0.7),
            FormSection(id="chorus_2", bars=8, role="chorus", density=0.9, tension=0.9),
            FormSection(id="outro", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("pop", "j_pop", "rock"),
        description="Pop form with pre-chorus buildup.",
    )
)

_register(
    SongForm(
        id="intro_verse_chorus_outro",
        name="Intro-Verse-Chorus-Outro",
        sections=(
            FormSection(id="intro", bars=4, role="intro", density=0.3, tension=0.2),
            FormSection(id="verse", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="chorus", bars=8, role="chorus", density=0.8, tension=0.8),
            FormSection(id="outro", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("pop", "lofi_hiphop"),
        description="Minimal pop form for short pieces.",
    )
)

_register(
    SongForm(
        id="fugue_exposition_episodes",
        name="Fugue (Exposition + Episodes)",
        sections=(
            FormSection(id="exposition", bars=8, role="intro", density=0.4, tension=0.4),
            FormSection(id="episode_1", bars=8, role="verse", density=0.6, tension=0.5),
            FormSection(id="middle_entry", bars=8, role="chorus", density=0.7, tension=0.7),
            FormSection(id="episode_2", bars=8, role="bridge", density=0.6, tension=0.6),
            FormSection(id="final_entry", bars=8, role="chorus", density=0.8, tension=0.9),
        ),
        typical_genres=("classical", "neoclassical"),
        description="Fugal structure with subject entries and episodes.",
    )
)

_register(
    SongForm(
        id="minimalist_phasing",
        name="Minimalist Phasing",
        sections=(
            FormSection(id="pattern_a", bars=8, role="verse", density=0.4, tension=0.3),
            FormSection(id="phase_1", bars=8, role="verse", density=0.5, tension=0.4),
            FormSection(id="phase_2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="phase_3", bars=8, role="verse", density=0.6, tension=0.6),
            FormSection(id="resolution", bars=8, role="outro", density=0.4, tension=0.3),
        ),
        typical_genres=("ambient", "process_music"),
        description="Gradual phase shifting through repetition.",
    )
)

_register(
    SongForm(
        id="sonatina_form",
        name="Sonatina Form",
        sections=(
            FormSection(id="exposition_1", bars=8, role="verse", density=0.5, tension=0.4),
            FormSection(id="exposition_2", bars=8, role="verse", density=0.6, tension=0.6),
            FormSection(id="development", bars=12, role="bridge", density=0.7, tension=0.8),
            FormSection(id="recapitulation", bars=8, role="chorus", density=0.6, tension=0.6),
            FormSection(id="coda", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("classical", "neoclassical", "cinematic"),
        description="Compressed sonata with exposition, development, recap.",
    )
)

_register(
    SongForm(
        id="blues_12bar",
        name="12-Bar Blues",
        sections=(
            FormSection(id="phrase_1", bars=4, role="verse", density=0.5, tension=0.4),
            FormSection(id="phrase_2", bars=4, role="verse", density=0.6, tension=0.6),
            FormSection(id="phrase_3", bars=4, role="verse", density=0.7, tension=0.7),
        ),
        typical_genres=("jazz_ballad", "rock", "blues"),
        description="Standard 12-bar blues progression structure.",
    )
)

_register(
    SongForm(
        id="blues_16bar",
        name="16-Bar Blues",
        sections=(
            FormSection(id="phrase_1", bars=4, role="verse", density=0.5, tension=0.4),
            FormSection(id="phrase_2", bars=4, role="verse", density=0.5, tension=0.5),
            FormSection(id="phrase_3", bars=4, role="verse", density=0.6, tension=0.6),
            FormSection(id="phrase_4", bars=4, role="verse", density=0.7, tension=0.7),
        ),
        typical_genres=("jazz_ballad", "blues"),
        description="Extended 16-bar blues.",
    )
)

_register(
    SongForm(
        id="jazz_aaba_64bar",
        name="Jazz AABA 64-Bar",
        sections=(
            FormSection(id="a1", bars=16, role="verse", density=0.5, tension=0.4),
            FormSection(id="a2", bars=16, role="verse", density=0.5, tension=0.5),
            FormSection(id="b", bars=16, role="bridge", density=0.6, tension=0.7),
            FormSection(id="a3", bars=16, role="verse", density=0.5, tension=0.5),
        ),
        typical_genres=("jazz_ballad",),
        description="Extended AABA for jazz standards with longer sections.",
    )
)

_register(
    SongForm(
        id="j_pop_intro_a_b_chorus",
        name="J-Pop Intro-A-B-Chorus",
        sections=(
            FormSection(id="intro", bars=4, role="intro", density=0.3, tension=0.2),
            FormSection(id="a_melo", bars=8, role="verse", density=0.5, tension=0.4),
            FormSection(id="b_melo", bars=8, role="pre_chorus", density=0.6, tension=0.6),
            FormSection(id="sabi", bars=8, role="chorus", density=0.8, tension=0.9),
            FormSection(id="interlude", bars=4, role="interlude", density=0.4, tension=0.4),
            FormSection(id="a_melo_2", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="b_melo_2", bars=8, role="pre_chorus", density=0.7, tension=0.7),
            FormSection(id="sabi_2", bars=8, role="chorus", density=0.9, tension=0.95),
            FormSection(id="outro", bars=4, role="outro", density=0.3, tension=0.2),
        ),
        typical_genres=("j_pop", "anime_bgm"),
        description="J-Pop A-melo/B-melo/Sabi structure.",
    )
)

_register(
    SongForm(
        id="game_intro_loop_a_loop_b",
        name="Game Intro-LoopA-LoopB",
        sections=(
            FormSection(id="intro", bars=4, role="intro", density=0.3, tension=0.2),
            FormSection(id="loop_a", bars=8, role="verse", density=0.5, tension=0.5),
            FormSection(id="transition", bars=2, role="build", density=0.6, tension=0.6),
            FormSection(id="loop_b", bars=8, role="chorus", density=0.7, tension=0.7),
        ),
        typical_genres=("game_8bit_chiptune", "game_bgm"),
        description="Game BGM with two loopable sections.",
    )
)

_register(
    SongForm(
        id="ambient_throughflow",
        name="Ambient Throughflow",
        sections=(
            FormSection(id="emergence", bars=8, role="intro", density=0.2, tension=0.1),
            FormSection(id="flow_1", bars=16, role="verse", density=0.3, tension=0.3),
            FormSection(id="flow_2", bars=16, role="verse", density=0.4, tension=0.4),
            FormSection(id="dissolution", bars=8, role="outro", density=0.2, tension=0.1),
        ),
        typical_genres=("ambient", "meditation"),
        description="Ambient piece with gradual emergence and dissolution.",
    )
)


def get_form(form_id: str) -> SongForm | None:
    """Look up a form by ID.

    Args:
        form_id: Form identifier.

    Returns:
        The SongForm, or None if not found.
    """
    return FORM_LIBRARY.get(form_id)


def list_forms() -> list[str]:
    """Return all registered form IDs."""
    return list(FORM_LIBRARY.keys())
