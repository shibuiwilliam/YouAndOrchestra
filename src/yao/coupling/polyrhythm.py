"""Polyrhythm Engine — multi-layer rhythmic textures.

Generates polyrhythmic textures where multiple rhythmic cycles
run simultaneously at different ratios.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §3.2, PROJECT.md §3.4.5, CLAUDE.md Phase 5.0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PolyrhythmLayer:
    """A single rhythmic layer in a polyrhythmic texture.

    Attributes:
        cycle_length_beats: Length of one cycle in beats.
        pattern: Onset positions within the cycle (as fractions of cycle length).
        instrument: Instrument this layer is assigned to.
        accent_pattern: Velocity multipliers for each onset (0.0-1.0).
    """

    cycle_length_beats: float
    pattern: tuple[float, ...]
    instrument: str
    accent_pattern: tuple[float, ...] = ()


@dataclass(frozen=True)
class PolyrhythmTexture:
    """Multiple PolyrhythmLayers running simultaneously.

    Attributes:
        layers: The constituent rhythmic layers.
        base_meter: Time signature string (e.g., "4/4").
        duration_bars: Number of bars this texture covers.
    """

    layers: tuple[PolyrhythmLayer, ...]
    base_meter: str
    duration_bars: int

    @property
    def layer_count(self) -> int:
        """Number of layers in the texture."""
        return len(self.layers)

    def all_onsets(self, beats_per_bar: int = 4) -> list[tuple[float, str]]:
        """Return all onset positions across all layers.

        Returns:
            List of (beat_position, instrument) tuples, sorted by beat.
        """
        total_beats = self.duration_bars * beats_per_bar
        onsets: list[tuple[float, str]] = []

        for layer in self.layers:
            if layer.cycle_length_beats <= 0:
                continue
            cycles = int(math.ceil(total_beats / layer.cycle_length_beats))
            for cycle in range(cycles):
                cycle_start = cycle * layer.cycle_length_beats
                for onset_frac in layer.pattern:
                    beat = cycle_start + onset_frac * layer.cycle_length_beats
                    if beat < total_beats:
                        onsets.append((beat, layer.instrument))

        onsets.sort(key=lambda x: x[0])
        return onsets


def are_coprime(a: int, b: int) -> bool:
    """Check if two integers are coprime."""
    return math.gcd(a, b) == 1


def compose_polyrhythm(
    ratio: tuple[int, int],
    duration_bars: int,
    instruments: tuple[str, str] = ("percussion_1", "percussion_2"),
    beats_per_bar: int = 4,
) -> PolyrhythmTexture:
    """Compose a two-layer polyrhythm at the given ratio.

    Args:
        ratio: e.g., (3, 4) for 3-against-4.
        instruments: Instrument names for each layer.
        duration_bars: Number of bars.
        beats_per_bar: Beats per bar.

    Returns:
        PolyrhythmTexture with two layers.
    """
    a, b = ratio

    # Layer A: a evenly-spaced onsets per bar
    layer_a_cycle = float(beats_per_bar)
    layer_a_pattern = tuple(i / a for i in range(a))

    # Layer B: b evenly-spaced onsets per bar
    layer_b_cycle = float(beats_per_bar)
    layer_b_pattern = tuple(i / b for i in range(b))

    return PolyrhythmTexture(
        layers=(
            PolyrhythmLayer(
                cycle_length_beats=layer_a_cycle,
                pattern=layer_a_pattern,
                instrument=instruments[0],
            ),
            PolyrhythmLayer(
                cycle_length_beats=layer_b_cycle,
                pattern=layer_b_pattern,
                instrument=instruments[1],
            ),
        ),
        base_meter=f"{beats_per_bar}/4",
        duration_bars=duration_bars,
    )


def phase_shift(
    layer: PolyrhythmLayer,
    offset_beats: float,
) -> PolyrhythmLayer:
    """Apply a phase shift to a polyrhythm layer.

    Shifts all onset positions by offset_beats within the cycle.

    Args:
        layer: Original layer.
        offset_beats: Shift amount in beats.

    Returns:
        New PolyrhythmLayer with shifted pattern.
    """
    if layer.cycle_length_beats <= 0:
        return layer

    offset_frac = offset_beats / layer.cycle_length_beats
    shifted = tuple((p + offset_frac) % 1.0 for p in layer.pattern)

    return PolyrhythmLayer(
        cycle_length_beats=layer.cycle_length_beats,
        pattern=tuple(sorted(shifted)),
        instrument=layer.instrument,
        accent_pattern=layer.accent_pattern,
    )
