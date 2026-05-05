# Design: Audio Perception Layer

## Problem

LLMs cannot listen. Symbolic evaluation alone can produce scores that rise while actual listening quality degrades.

## Solution

Audio feature extraction via librosa + pyloudnorm. A `PerceptualReport` frozen dataclass is produced after every audio render. Symbolic-acoustic divergence detection catches cases where the score looks correct but sounds wrong.

## Components

- `AudioPerceptionAnalyzer`: extracts LUFS, spectral features (centroid, rolloff, flatness), onset density, tempo stability, 7-band energy distribution, masking risk
- `PerceptualReport`: frozen dataclass with loudness, spectral, and temporal dimensions
- `ListeningSimulator`: orchestrates post-render perception, persists `perceptual.json`, mood divergence detection via intent keywords
- `UseCaseEvaluator`: 7 use cases (YouTube BGM, Game BGM, Advertisement, Study Focus, Meditation, Workout, Cinematic) with context-specific scoring
- 5 acoustic divergence critique rules: symbolic_acoustic_divergence, lufs_target_violation, spectral_imbalance, brightness_intent_mismatch, energy_trajectory_violation

## Pipeline Position

Step 7.5 — after audio render, before optional feedback loopback.

## Files

- `src/yao/perception/audio_features.py` — AudioPerceptionAnalyzer
- `src/yao/perception/listening_simulator.py` — ListeningSimulator
- `src/yao/perception/use_case_evaluator.py` — UseCaseEvaluator
- `src/yao/verify/acoustic/divergence_rules.py` — 5 critique rules
