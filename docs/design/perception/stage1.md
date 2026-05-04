# Design: Acoustic Truth — Perception Layer Stage 1 (Phase γ.2)

## Problem
LLMs cannot listen. v1.0 evaluated music only symbolically. Symbolic scores can rise while listening quality degrades.

## Solution
Audio feature extraction via librosa + pyloudnorm. PerceptualReport frozen dataclass produced after every audio render. Symbolic-acoustic divergence detection.

## Components
- `AudioPerceptionAnalyzer`: extracts LUFS, spectral features, onset density, tempo stability
- `PerceptualReport`: frozen dataclass with loudness, spectral, temporal dimensions
- `ListeningSimulator`: orchestrates post-render perception, persists perceptual.json
- `UseCaseEvaluator`: 7 use cases with context-specific scoring
- Acoustic divergence critique rules (3): symbolic_acoustic_divergence, lufs_target_violation, spectral_imbalance

## Pipeline Position
Step 7.5 — after audio render, before optional loopback.
