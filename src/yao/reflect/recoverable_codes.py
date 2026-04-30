"""Registry of known RecoverableDecision codes.

Every compromise code must be registered here before use. This prevents
ad-hoc codes from proliferating without documentation.

To add a new code: add it to KNOWN_CODES with a description, then use it
in the RecoverableDecision constructor.
"""

from __future__ import annotations

from yao.errors import VerificationError

KNOWN_CODES: dict[str, str] = {
    # Pitch range issues
    "MELODY_NOTE_OUT_OF_RANGE": "Melody note outside instrument range, bounced back",
    "MELODY_NOTE_SKIPPED": "Melody note could not fit instrument range, skipped",
    "BASS_NOTE_OUT_OF_RANGE": "Bass note outside instrument range, fell back to root",
    "CHORD_NOTE_OUT_OF_RANGE": "Chord note outside instrument range, skipped",
    "RHYTHM_PITCH_OUT_OF_RANGE": "Rhythm pitch outside range, fell back to root only",
    "MOTIF_NOTE_OUT_OF_RANGE": "Transformed motif note outside range, octave-adjusted or skipped",
    # Velocity issues
    "VELOCITY_CLAMPED": "Computed velocity outside MIDI range [1, 127], clamped",
    # Chord/harmony issues
    "CHORD_QUALITY_UNDEFINED": "Chord quality not in palette, defaulted to major",
    # Structural issues
    "REST_INSERTED": "Stochastic rest inserted, bar has fewer notes than expected",
}


def validate_code(code: str) -> None:
    """Ensure a code is registered.

    Args:
        code: The RecoverableDecision code to validate.

    Raises:
        VerificationError: If the code is not in KNOWN_CODES.
    """
    if code not in KNOWN_CODES:
        raise VerificationError(
            f"Unknown recoverable code: '{code}'. Add it to src/yao/verify/recoverable_codes.py before use."
        )
