"""Production system — genre-specific mix and master profiles.

Provides ProductionProfile data structure and loader for per-genre
audio processing chains. Used by the Mix Engineer subagent and
the audio rendering pipeline.

Belongs to Layer 5 (Rendering adjunct).
"""

from yao.production.profile import ProductionProfile, load_production_profile

__all__ = ["ProductionProfile", "load_production_profile"]
