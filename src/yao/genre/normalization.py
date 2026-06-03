"""Normalize user-facing genre strings to registered profile IDs.

This is the single entry point for genre ID resolution across all paths:
NL → spec, explicit YAML, and SDK API.

Belongs to Layer 1 (Genre).
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger()

# Short user-facing genre names → registered profile IDs.
# Registered IDs themselves don't need to be here (direct match catches them).
_GENRE_ALIASES: dict[str, str] = {
    # Rock family
    "rock": "rock_classic",
    "hard rock": "rock_classic",
    "classic rock": "rock_classic",
    "alternative rock": "rock_classic",
    "punk": "rock_classic",
    "indie rock": "rock_classic",
    "metal": "metal",
    "heavy metal": "metal",
    "death metal": "metal",
    "thrash": "metal",
    "progressive": "progressive_rock",
    "prog": "progressive_rock",
    "prog rock": "progressive_rock",
    # Hip-hop family
    "hip hop": "hiphop_boom_bap",
    "hip-hop": "hiphop_boom_bap",
    "hiphop": "hiphop_boom_bap",
    "rap": "hiphop_boom_bap",
    "boom bap": "hiphop_boom_bap",
    "trap": "hiphop_trap",
    "drill": "hiphop_trap",
    "lofi": "lofi_hiphop",
    "lo-fi": "lofi_hiphop",
    "lo fi": "lofi_hiphop",
    "chillhop": "lofi_hiphop",
    "study beats": "lofi_hiphop",
    # Electronic family
    "edm": "electronic_house",
    "electronic": "electronic_house",
    "dance": "electronic_house",
    "house": "electronic_house",
    "deep house": "electronic_house",
    "techno": "electronic_techno",
    "minimal techno": "electronic_techno",
    "trance": "electronic_trance",
    "psytrance": "electronic_trance",
    "synthwave": "electronic_synthwave",
    "retrowave": "electronic_synthwave",
    "vaporwave": "electronic_synthwave",
    "dnb": "electronic_techno",
    "drum and bass": "electronic_techno",
    "drum'n'bass": "electronic_techno",
    "dubstep": "electronic_techno",
    # Pop family
    "pop": "pop_mainstream",
    "radio pop": "pop_mainstream",
    "j-pop": "j_pop",
    "jpop": "j_pop",
    "japanese pop": "j_pop",
    "j pop": "j_pop",
    "anime": "j_pop",
    # Jazz family
    "jazz": "jazz_ballad",
    "swing": "jazz_ballad",
    "ballad": "jazz_ballad",
    "smooth jazz": "jazz_ballad",
    "bebop": "jazz_bebop",
    "bop": "jazz_bebop",
    "modal jazz": "jazz_modal",
    "modal": "jazz_modal",
    "cool jazz": "jazz_modal",
    # Classical family
    "classical": "classical_romantic",
    "romantic": "classical_romantic",
    "symphony": "classical_romantic",
    "concerto": "classical_romantic",
    "baroque": "classical_baroque",
    "bach": "classical_baroque",
    "neoclassical": "neoclassical",
    "minimalist": "neoclassical",
    # Cinematic
    "cinematic": "cinematic",
    "film": "cinematic",
    "movie": "cinematic",
    "score": "cinematic",
    "soundtrack": "cinematic",
    "trailer": "cinematic",
    "epic": "cinematic",
    # Ambient
    "ambient": "ambient",
    "drone": "ambient",
    "atmospheric": "ambient",
    "soundscape": "ambient",
    "dark ambient": "ambient_dark",
    "horror": "ambient_dark",
    # Blues
    "blues": "blues_chicago",
    "delta blues": "blues_chicago",
    "chicago blues": "blues_chicago",
    # Country/Folk
    "country": "country_traditional",
    "honky tonk": "country_traditional",
    "americana": "country_traditional",
    "folk": "acoustic_folk",
    "singer-songwriter": "acoustic_folk",
    "acoustic": "acoustic_folk",
    "celtic": "world_celtic",
    "irish": "world_celtic",
    "scottish": "world_celtic",
    # Latin
    "bossa": "latin_bossa_nova",
    "bossa nova": "latin_bossa_nova",
    "samba": "latin_bossa_nova",
    "latin": "latin_bossa_nova",
    "salsa": "latin_bossa_nova",
    # R&B / Soul / Funk
    "rnb": "rnb_neo_soul",
    "r&b": "rnb_neo_soul",
    "r and b": "rnb_neo_soul",
    "neo soul": "rnb_neo_soul",
    "neo-soul": "rnb_neo_soul",
    "soul": "rnb_neo_soul",
    "motown": "rnb_neo_soul",
    "funk": "funk_classic",
    "funky": "funk_classic",
    "disco": "funk_classic",
    # Reggae
    "reggae": "reggae",
    "ska": "reggae",
    "dub": "reggae",
    "island": "reggae",
    # Game / Chiptune
    "chiptune": "game_8bit_chiptune",
    "8bit": "game_8bit_chiptune",
    "8-bit": "game_8bit_chiptune",
    "game": "game_8bit_chiptune",
    "video game": "game_8bit_chiptune",
}

# Japanese genre keywords → registered profile IDs
_JA_GENRE_ALIASES: dict[str, str] = {
    "ロック": "rock_classic",
    "メタル": "metal",
    "ヒップホップ": "hiphop_boom_bap",
    "ラップ": "hiphop_boom_bap",
    "トラップ": "hiphop_trap",
    "ローファイ": "lofi_hiphop",
    "ジャズ": "jazz_ballad",
    "ビバップ": "jazz_bebop",
    "クラシック": "classical_romantic",
    "バロック": "classical_baroque",
    "アンビエント": "ambient",
    "シネマティック": "cinematic",
    "映画音楽": "cinematic",
    "ポップ": "pop_mainstream",
    "ポップス": "pop_mainstream",
    "ファンク": "funk_classic",
    "テクノ": "electronic_techno",
    "ハウス": "electronic_house",
    "トランス": "electronic_trance",
    "シンセウェイブ": "electronic_synthwave",
    "ボサノバ": "latin_bossa_nova",
    "レゲエ": "reggae",
    "ブルース": "blues_chicago",
    "カントリー": "country_traditional",
    "フォーク": "acoustic_folk",
    "ケルト": "world_celtic",
    "ソウル": "rnb_neo_soul",
    "チップチューン": "game_8bit_chiptune",
    "ゲーム音楽": "game_8bit_chiptune",
}


def normalize_genre(user_genre: str) -> str | None:
    """Normalize a user-facing genre string to a registered profile ID.

    Args:
        user_genre: User input (e.g., "rock", "hip hop", "j-pop").

    Returns:
        Registered profile ID (e.g., "rock_classic"), or None if unresolvable.
    """
    from yao.constants.genre_profile import all_genre_profiles

    if not user_genre:
        return None

    normalized_input = user_genre.lower().strip().replace("_", " ")
    registered = set(all_genre_profiles().keys())

    # 1. Direct match
    if normalized_input in registered:
        return normalized_input
    # 2. Underscore form direct match
    underscore_form = normalized_input.replace(" ", "_")
    if underscore_form in registered:
        return underscore_form
    # 3. Alias map (English)
    aliased = _GENRE_ALIASES.get(normalized_input)
    if aliased and aliased in registered:
        return aliased
    # 4. Alias map with underscore→space conversion
    aliased2 = _GENRE_ALIASES.get(underscore_form.replace("_", " "))
    if aliased2 and aliased2 in registered:
        return aliased2
    # 5. Japanese aliases
    for ja_key, profile_id in _JA_GENRE_ALIASES.items():
        if ja_key in user_genre and profile_id in registered:
            return profile_id

    logger.warning(
        "genre_normalize_failed",
        user_input=user_genre,
        normalized_input=normalized_input,
        registered_count=len(registered),
    )
    return None


def normalize_genre_with_fallback(
    user_genre: str,
    fallback: str = "pop_mainstream",
) -> str:
    """Normalize with a decisive non-classical fallback.

    Uses pop_mainstream as fallback to avoid classical/cinematic bias.
    """
    result = normalize_genre(user_genre)
    return result if result is not None else fallback
