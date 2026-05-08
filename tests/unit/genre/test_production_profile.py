"""Tests for ProductionProfile loading and validation."""

from __future__ import annotations

from yao.production.profile import (
    ProductionProfile,
    all_production_profiles,
    load_production_profile,
)


class TestProductionProfileLoading:
    """Test production profile YAML loading."""

    def test_load_lofi_hip_hop(self) -> None:
        """Lo-fi profile should load with vinyl simulation."""
        profile = load_production_profile("lofi_hip_hop")
        assert profile is not None
        assert profile.name == "lofi_hip_hop"
        assert profile.vinyl_simulation is True
        assert profile.target_lufs == -16.0
        assert profile.lo_pass_hz == 8000

    def test_load_modern_edm(self) -> None:
        """EDM profile should have sidechain enabled."""
        profile = load_production_profile("modern_edm")
        assert profile is not None
        assert profile.sidechain_enabled is True
        assert profile.target_lufs == -8.0

    def test_load_jazz_intimate(self) -> None:
        """Jazz profile should have narrow stereo and gentle compression."""
        profile = load_production_profile("jazz_intimate")
        assert profile is not None
        assert profile.stereo_width < 0.5
        assert profile.master_compressor is not None
        assert profile.master_compressor.ratio < 2.0

    def test_load_cinematic(self) -> None:
        """Cinematic profile should have wide dynamic range."""
        profile = load_production_profile("cinematic")
        assert profile is not None
        assert profile.target_lufs <= -18.0
        assert profile.reverb_type == "hall"
        assert profile.reverb_amount >= 0.4

    def test_load_nonexistent_returns_none(self) -> None:
        """Missing profile should return None, not raise."""
        result = load_production_profile("nonexistent_xyz_profile")
        assert result is None

    def test_all_profiles_load(self) -> None:
        """All production profile YAMLs should load successfully."""
        profiles = all_production_profiles()
        assert len(profiles) >= 7
        for name, profile in profiles.items():
            assert isinstance(profile, ProductionProfile)
            assert profile.name == name

    def test_all_profiles_have_valid_lufs(self) -> None:
        """All profiles should have reasonable LUFS targets."""
        for name, profile in all_production_profiles().items():
            assert -30.0 <= profile.target_lufs <= -5.0, f"{name} has unreasonable target_lufs={profile.target_lufs}"

    def test_from_yaml_data(self) -> None:
        """from_yaml_data should construct a valid profile."""
        data = {
            "name": "test_profile",
            "genre_tags": ["test"],
            "target_lufs": -12.0,
            "stereo_width": 0.5,
        }
        profile = ProductionProfile.from_yaml_data(data)
        assert profile.name == "test_profile"
        assert profile.target_lufs == -12.0

    def test_saturation_clamped(self) -> None:
        """Saturation should be clamped to [0, 1]."""
        profile = ProductionProfile(name="test", tape_saturation=1.5)
        assert profile.tape_saturation == 1.0
        profile2 = ProductionProfile(name="test2", tape_saturation=-0.5)
        assert profile2.tape_saturation == 0.0
