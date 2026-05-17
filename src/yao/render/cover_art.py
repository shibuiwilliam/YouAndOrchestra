"""Cover Art Generator — AI-powered album artwork using Gemini image generation.

Generates cover art for compositions based on their musical characteristics
(genre, mood, instrumentation, tempo, key) using Google's Gemini image
generation API (Nano Banana).

Requires: pip install -e ".[cover-art]" (google-genai package)
Requires: GEMINI_API_KEY environment variable set

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class CoverArtRequest:
    """Request for cover art generation.

    Attributes:
        title: Composition title.
        genre: Primary genre.
        mood: Mood description (e.g., "melancholic", "energetic").
        instruments: Key instruments in the piece.
        tempo_bpm: Tempo for energy inference.
        key: Musical key.
        style_hint: Optional visual style hint from the user.
    """

    title: str
    genre: str = "general"
    mood: str = ""
    instruments: tuple[str, ...] = ()
    tempo_bpm: float = 120.0
    key: str = "C major"
    style_hint: str = ""


@dataclass(frozen=True)
class CoverArtResult:
    """Result of cover art generation.

    Attributes:
        image_path: Path to the saved image file.
        prompt_used: The prompt sent to the image generation model.
        model: Model used for generation.
        success: Whether generation succeeded.
        error_message: Error message if generation failed.
    """

    image_path: Path | None = None
    prompt_used: str = ""
    model: str = ""
    success: bool = False
    error_message: str = ""


def _build_prompt(request: CoverArtRequest) -> str:
    """Build an image generation prompt from composition metadata.

    Translates musical characteristics into visual language for the
    image generation model.

    Args:
        request: The cover art request.

    Returns:
        A descriptive prompt for image generation.
    """
    parts: list[str] = []

    parts.append(f'Album cover art for a piece titled "{request.title}".')

    # Genre → visual style mapping
    genre_visuals: dict[str, str] = {
        "jazz": "smoky nightclub atmosphere, warm golden lighting, abstract shapes",
        "rock": "bold graphic design, high contrast, electric energy",
        "pop": "vibrant colors, clean modern design, playful",
        "electronic": "neon lights, futuristic geometric patterns, digital aesthetic",
        "classical": "elegant, oil painting style, ornate golden frames",
        "ambient": "ethereal misty landscape, soft gradients, dreamlike",
        "metal": "dark dramatic, sharp angles, intense imagery",
        "hiphop": "urban street art style, bold typography, graffiti elements",
        "blues": "weathered textures, deep blues and warm browns, vintage feel",
        "funk": "psychedelic colors, retro 70s design, groovy patterns",
        "reggae": "tropical colors, sun and nature, Rastafarian-inspired palette",
        "latin": "warm sunset colors, tropical flowers, passionate movement",
        "country": "rustic landscapes, warm earth tones, open sky",
        "cinematic": "dramatic wide panorama, cinematic color grading, epic scale",
    }

    # Find matching genre visual
    genre_key = request.genre.split("_")[0] if "_" in request.genre else request.genre
    if genre_key in genre_visuals:
        parts.append(f"Visual style: {genre_visuals[genre_key]}.")
    elif request.genre != "general":
        parts.append(f"Visual style inspired by {request.genre} music.")

    # Mood → atmosphere
    if request.mood:
        parts.append(f"Mood: {request.mood}.")

    # Tempo → energy
    if request.tempo_bpm < 80:
        parts.append("Calm, slow, contemplative energy.")
    elif request.tempo_bpm > 150:
        parts.append("High energy, dynamic, intense movement.")

    # Key → color temperature hint
    if "minor" in request.key.lower():
        parts.append("Cool color palette, darker tones.")
    elif "major" in request.key.lower():
        parts.append("Warm color palette, brighter tones.")

    # User style hint takes priority
    if request.style_hint:
        parts.append(f"Additional direction: {request.style_hint}.")

    # Quality instructions
    parts.append("Professional album cover quality. No text or letters in the image.")
    parts.append("Square aspect ratio (1:1). High detail, visually striking.")

    return " ".join(parts)


def generate_cover_art(
    request: CoverArtRequest,
    output_path: Path,
    model: str = "gemini-2.5-flash-image",
) -> CoverArtResult:
    """Generate cover art for a composition using Gemini image generation.

    Requires the GEMINI_API_KEY environment variable to be set.
    Install the dependency: pip install -e ".[cover-art]"

    Args:
        request: Cover art request with composition metadata.
        output_path: Where to save the generated image (PNG).
        model: Gemini model to use for image generation.

    Returns:
        CoverArtResult with the path to the generated image.
    """
    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return CoverArtResult(
            success=False,
            error_message="GEMINI_API_KEY environment variable is not set. "
            "Get a key at https://aistudio.google.com/apikey",
        )

    # Check dependency
    try:
        from google import genai
    except ImportError:
        return CoverArtResult(
            success=False,
            error_message='google-genai package not installed. Run: pip install -e ".[cover-art]"',
        )

    # Build prompt
    prompt = _build_prompt(request)
    logger.info(
        "cover_art_generating",
        title=request.title,
        genre=request.genre,
        model=model,
        prompt_length=len(prompt),
    )

    # Generate image
    try:
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        # Extract and save image
        if response.candidates:
            content = response.candidates[0].content
            if content is not None and content.parts is not None:
                for part in content.parts:
                    if hasattr(part, "inline_data") and part.inline_data is not None:
                        # Save image bytes
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        image_bytes = part.inline_data.data
                        if image_bytes is not None:
                            output_path.write_bytes(image_bytes)
                            logger.info("cover_art_saved", path=str(output_path))
                            return CoverArtResult(
                                image_path=output_path,
                                prompt_used=prompt,
                                model=model,
                                success=True,
                            )

        # No image in response — might be text-only
        text_parts: list[str] = []
        if response.candidates:
            content = response.candidates[0].content
            if content is not None and content.parts is not None:
                text_parts = [p.text for p in content.parts if hasattr(p, "text") and p.text]

        return CoverArtResult(
            prompt_used=prompt,
            model=model,
            success=False,
            error_message=f"No image generated. Model response: {' '.join(text_parts)[:200]}",
        )

    except Exception as e:
        logger.error("cover_art_failed", error=str(e))
        return CoverArtResult(
            prompt_used=prompt,
            model=model,
            success=False,
            error_message=f"Image generation failed: {e}",
        )
