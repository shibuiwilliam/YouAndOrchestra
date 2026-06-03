"""Validate that all instrument names in genre profile YAMLs exist in INSTRUMENT_RANGES.

Run with: python tools/validate_genre_instruments.py
Part of `make all-checks`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from yao.constants.instruments import INSTRUMENT_RANGES  # noqa: E402


def main() -> int:
    """Check all genre profile YAMLs for unknown instrument names."""
    errors: list[str] = []
    project_root = Path(__file__).resolve().parent.parent

    for yaml_dir in [project_root / "genre_profiles"]:
        if not yaml_dir.exists():
            continue
        for p in sorted(yaml_dir.glob("*.yaml")):
            data = yaml.safe_load(p.read_text())
            if not data:
                continue
            pi = data.get("preferred_instruments") or []
            for name in pi:
                if name and name not in INSTRUMENT_RANGES:
                    errors.append(f"{p.name}: unknown instrument '{name}' in preferred_instruments")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", flush=True)
        return 1
    print(f"OK: All instruments in {len(list((project_root / 'genre_profiles').glob('*.yaml')))} profiles are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
