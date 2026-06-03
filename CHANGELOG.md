# Changelog

## [Unreleased] - v2.1: Genre & Variation Refinement

### Added
- **Genre normalization module** (`src/yao/genre/normalization.py`): 60+ English + 17 Japanese aliases mapping short user-facing genre names to registered profile IDs
- **15 GM instruments** to `INSTRUMENT_RANGES`: electric guitar variants (muted/overdrive/distorted/harmonics), electric piano (Rhodes/Wurlitzer), clavinet, Hammond organ, rock organ, upright bass, fretless bass, slap bass, synth bass sub/acid, pluck synth
- **11 musical motif transforms**: ornament_add, ornament_remove, rhythm_displace, interval_fill, interval_leap, octave_displace, expand, contract, fragment, extend, question_answer
- **Motif schedule system**: sections now receive 2-8 motif placements with role-specific transformation distributions (verse=ornament/displace, chorus=expand, bridge=inversion/fragment)
- **Per-genre motif transformation weights** on GenreProfile (jazz=ornament-heavy, ambient=identity-heavy, classical=development-oriented)
- **Genre-aware trajectory shapes**: 30 genre-specific tension curves (EDM=build-drop, hiphop=loop-flat, rock=gradual build, classical=arch, ambient=flat)
- **Drum auto-attach from SpecCompiler**: genres with `requires_drums=True` automatically get DrumsSpec
- **Conductor drum safety net**: fallback drum pattern when genre resolution fails
- **10 seed motifs** in `references/motifs/catalog.yaml` covering pop, jazz, rock, hiphop, latin, ambient, cinematic, funk, blues
- **Genre fidelity regression test** (12 parametrized cases)
- **Motif recurrence regression test** (3 cases)
- **Instrument validation script** (`tools/validate_genre_instruments.py`)

### Fixed
- Genre ID mismatch: SpecCompiler returned "rock"/"jazz" while GenreRegistry uses "rock_classic"/"jazz_ballad" -- all 30 genres now resolve correctly
- Instrument names in 30 genre profile YAMLs aligned with INSTRUMENT_RANGES (removed phantom instruments like drum_kit, drums_808)
- `saxophone_alto` -> `alto_sax` namespace mismatch in Japanese keyword map
- "acoustic" alias ambiguity (now requires "acoustic folk")
- Cinematic profile preferred instruments reordered (strings_ensemble first)
- Genre-specific instrument overrides: metal->distorted guitar, funk->muted guitar + slap bass, hiphop->Rhodes + sub bass

### Changed
- `_infer_genre` now uses `_GENRE_ALIASES` from normalization module (always returns registered ID)
- `_infer_instruments` is now genre-driven (uses profile.preferred_instruments, adds user-mentioned instruments on top)
- `_enrich_from_skill` narrowed to key/tempo enrichment only (instruments handled by `_infer_instruments`)
- Default genre fallback changed from "general" to "pop_mainstream" (avoids classical bias)
- MotivicPlanner uses weighted transform selection per section role instead of uniform random
