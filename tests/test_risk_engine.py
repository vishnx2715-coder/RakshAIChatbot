"""
tests/test_risk_engine.py — Unit tests for services/risk_engine.py

Covers compute_risk() for each hazard type, boundary severity values,
overall status levels 1–5, and edge cases.
"""

import pytest
from services.risk_engine import compute_risk


def _w(**kwargs):
    """Build a minimal weather dict with safe defaults."""
    base = {
        "temp": 25, "humidity": 50, "wind_speed": 0,
        "rain_1h": 0, "icon": "Clear", "visibility": 10000,
    }
    base.update(kwargs)
    return base


# ─────────────────────────────────────────────────────────────
# Cyclone (wind speed m/s)
# ─────────────────────────────────────────────────────────────
class TestCyclone:
    def test_no_wind(self):
        r = compute_risk(_w(wind_speed=0))
        assert r["risks"]["cyclone"] == 0

    def test_wind_score_1(self):
        assert compute_risk(_w(wind_speed=7))["risks"]["cyclone"] == 1

    def test_wind_score_3(self):
        assert compute_risk(_w(wind_speed=18))["risks"]["cyclone"] == 3

    def test_wind_score_5(self):
        assert compute_risk(_w(wind_speed=33))["risks"]["cyclone"] == 5


# ─────────────────────────────────────────────────────────────
# Flood (rain + humidity modifier)
# ─────────────────────────────────────────────────────────────
class TestFlood:
    def test_no_rain(self):
        assert compute_risk(_w(rain_1h=0))["risks"]["flood"] == 0

    def test_light_rain_score_1(self):
        assert compute_risk(_w(rain_1h=1))["risks"]["flood"] == 1

    def test_heavy_rain_score_4(self):
        assert compute_risk(_w(rain_1h=25))["risks"]["flood"] == 4

    def test_extreme_rain_score_5(self):
        assert compute_risk(_w(rain_1h=60))["risks"]["flood"] == 5

    def test_humidity_modifier_bumps_score(self):
        # rain=1 → base score 1; high humidity → 2
        r = compute_risk(_w(rain_1h=1, humidity=95))
        assert r["risks"]["flood"] == 2

    def test_humidity_modifier_caps_at_5(self):
        # rain=60 → 5; adding humidity can't exceed 5
        r = compute_risk(_w(rain_1h=60, humidity=95))
        assert r["risks"]["flood"] == 5


# ─────────────────────────────────────────────────────────────
# Heatwave (temperature °C)
# ─────────────────────────────────────────────────────────────
class TestHeatwave:
    def test_normal_temp_no_heat(self):
        assert compute_risk(_w(temp=30))["risks"]["heatwave"] == 0

    def test_heat_score_1(self):
        assert compute_risk(_w(temp=35))["risks"]["heatwave"] == 1

    def test_heat_score_3(self):
        assert compute_risk(_w(temp=41))["risks"]["heatwave"] == 3

    def test_heat_score_5(self):
        assert compute_risk(_w(temp=48))["risks"]["heatwave"] == 5


# ─────────────────────────────────────────────────────────────
# Cold wave
# ─────────────────────────────────────────────────────────────
class TestColdWave:
    def test_normal_temp_no_cold(self):
        assert compute_risk(_w(temp=20))["risks"]["cold_wave"] == 0

    def test_cold_score_1(self):
        assert compute_risk(_w(temp=14))["risks"]["cold_wave"] == 1

    def test_cold_score_5(self):
        assert compute_risk(_w(temp=-1))["risks"]["cold_wave"] == 5


# ─────────────────────────────────────────────────────────────
# Dense fog (visibility metres)
# ─────────────────────────────────────────────────────────────
class TestDenseFog:
    def test_clear_visibility(self):
        assert compute_risk(_w(visibility=10000))["risks"]["dense_fog"] == 0

    def test_fog_score_2(self):
        assert compute_risk(_w(visibility=800))["risks"]["dense_fog"] == 2

    def test_fog_score_5(self):
        assert compute_risk(_w(visibility=30))["risks"]["dense_fog"] == 5


# ─────────────────────────────────────────────────────────────
# Thunderstorm / lightning
# ─────────────────────────────────────────────────────────────
class TestThunderstorm:
    def test_no_thunderstorm(self):
        r = compute_risk(_w(icon="Clear"))
        assert r["risks"]["thunderstorm"] == 0
        assert r["risks"]["lightning"] == 0

    def test_thunderstorm_sets_score_5(self):
        r = compute_risk(_w(icon="Thunderstorm"))
        assert r["risks"]["thunderstorm"] == 5

    def test_lightning_needs_humidity(self):
        # Thunderstorm but low humidity → no lightning
        r = compute_risk(_w(icon="Thunderstorm", humidity=70))
        assert r["risks"]["lightning"] == 0

    def test_lightning_high_humidity(self):
        r = compute_risk(_w(icon="Thunderstorm", humidity=80))
        assert r["risks"]["lightning"] == 4


# ─────────────────────────────────────────────────────────────
# Overall status mapping (severity 1–5)
# ─────────────────────────────────────────────────────────────
class TestOverallStatus:
    def test_normal(self):
        r = compute_risk(_w())
        assert r["overall"] == "NORMAL"
        assert r["max_score"] == 0

    def test_low(self):
        r = compute_risk(_w(wind_speed=7))   # cyclone=1
        assert r["overall"] == "LOW"

    def test_moderate(self):
        r = compute_risk(_w(wind_speed=11))   # cyclone=2
        assert r["overall"] == "MODERATE"

    def test_high(self):
        r = compute_risk(_w(wind_speed=18))   # cyclone=3
        assert r["overall"] == "HIGH"

    def test_critical(self):
        r = compute_risk(_w(wind_speed=33))   # cyclone=5
        assert r["overall"] == "CRITICAL"

    def test_max_score_reflects_highest_hazard(self):
        r = compute_risk(_w(wind_speed=33, rain_1h=60))
        assert r["max_score"] == 5

    def test_risks_dict_has_all_keys(self):
        r = compute_risk(_w())
        expected = {"cyclone", "flood", "heatwave", "cold_wave", "dense_fog", "thunderstorm", "lightning"}
        assert set(r["risks"].keys()) == expected
