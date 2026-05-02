"""Language detection — determine input language from text characteristics.

Uses ascii character ratio as a simple heuristic. For YaO's purposes,
we only need to distinguish Japanese from English.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations


def detect_language(text: str) -> str:
    """Detect the primary language of a text string.

    Uses the ratio of ASCII characters to total characters.
    Japanese text has many multi-byte characters (hiragana, katakana, kanji),
    resulting in a low ASCII ratio.

    Args:
        text: Input text to analyze.

    Returns:
        Language code: "ja" for Japanese, "en" for English.
    """
    if not text.strip():
        return "en"

    # Count ASCII printable characters (excluding whitespace for ratio)
    non_space = [c for c in text if not c.isspace()]
    if not non_space:
        return "en"

    ascii_count = sum(1 for c in non_space if ord(c) < 128)
    ascii_ratio = ascii_count / len(non_space)

    # Japanese text typically has < 50% ASCII characters
    # Mixed text with Japanese emotion words also falls below this threshold
    if ascii_ratio < 0.5:  # noqa: PLR2004
        return "ja"

    # Check for Japanese punctuation even in mostly-ASCII text
    jp_punct = any(c in text for c in "\u3001\u3002\u300c\u300d\u3010\u3011\uff01\uff1f")
    if jp_punct:
        return "ja"

    return "en"
