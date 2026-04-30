"""Schema for intent.md — the piece's soul in 1–3 sentences.

The intent is the final court of appeal: when automated metrics conflict,
intent.md decides which one matters (PROJECT.md §7.3).

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from yao.errors import SpecValidationError

_MAX_TEXT_LENGTH = 600

# Simple keyword extraction: words that are likely musically descriptive.
# Not NLP — just a reasonable heuristic for downstream use.
_STOP_WORDS = frozenset([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "can", "could", "may", "might", "must", "need", "dare",
    "and", "or", "but", "nor", "so", "yet", "for", "at", "by", "to",
    "in", "on", "of", "with", "from", "into", "through", "during",
    "before", "after", "above", "below", "between", "among", "this",
    "that", "these", "those", "it", "its", "i", "my", "we", "our",
    "you", "your", "they", "their", "not", "no", "very", "too", "also",
    "just", "only", "still", "even", "much", "more", "most", "about",
    "like", "than",
])


@dataclass(frozen=True)
class IntentSpec:
    """Parsed intent from intent.md.

    Attributes:
        text: The raw intent text (1–3 sentences, max 600 chars).
        keywords: Extracted descriptive words for downstream matching.
        valence_hint: Optional brightness hint [0,1] (filled by sketch dialogue).
        energy_hint: Optional energy hint [0,1] (filled by sketch dialogue).
        use_case_hint: Optional use-case tag (filled by sketch dialogue).
    """

    text: str
    keywords: list[str] = field(default_factory=list)
    valence_hint: float | None = None
    energy_hint: float | None = None
    use_case_hint: str | None = None

    @classmethod
    def from_markdown(cls, path: Path) -> IntentSpec:
        """Load an intent from a Markdown file.

        Expects a short Markdown file. The first ``#`` heading is stripped
        (it's the project title), and the remaining text is the intent body.

        Args:
            path: Path to intent.md.

        Returns:
            Validated IntentSpec.

        Raises:
            SpecValidationError: If the file is missing, empty, or too long.
        """
        if not path.exists():
            raise SpecValidationError(
                f"intent.md not found: {path}",
                field="intent",
            )

        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            raise SpecValidationError(
                "intent.md is empty",
                field="intent",
            )

        # Strip leading heading (e.g., "# my-song\n")
        lines = raw.split("\n")
        body_lines = [ln for ln in lines if not ln.strip().startswith("#")]
        text = "\n".join(body_lines).strip()

        if not text:
            raise SpecValidationError(
                "intent.md has a heading but no body text",
                field="intent",
            )

        if len(text) > _MAX_TEXT_LENGTH:
            raise SpecValidationError(
                f"intent.md body is {len(text)} chars; max is {_MAX_TEXT_LENGTH}",
                field="intent",
            )

        keywords = _extract_keywords(text)

        return cls(text=text, keywords=keywords)

    def crystallized(self) -> bool:
        """Return True if the intent has enough substance to proceed.

        An intent is considered crystallized if it has at least 2 keywords
        (indicating some specificity beyond a trivial statement).
        """
        return len(self.keywords) >= 2  # noqa: PLR2004


def _extract_keywords(text: str) -> list[str]:
    """Extract descriptive keywords from intent text.

    Simple heuristic: lowercase, split on non-alpha, remove stop words
    and short words. No NLP dependency.

    Args:
        text: Raw intent text.

    Returns:
        Deduplicated list of descriptive keywords.
    """
    words = re.findall(r"[a-zA-Z]+", text.lower())
    seen: set[str] = set()
    keywords: list[str] = []
    for w in words:
        if len(w) >= 3 and w not in _STOP_WORDS and w not in seen:  # noqa: PLR2004
            seen.add(w)
            keywords.append(w)
    return keywords
