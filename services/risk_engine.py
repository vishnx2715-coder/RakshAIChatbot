"""
services/risk_engine.py — Weather-based disaster risk scoring for RAKSHA.

compute_risk(weather_dict) → {"risks": {...}, "overall": str, "max_score": int}

Hazard scores are 0–5:
  0 = no hazard
  1–2 = LOW / MODERATE
  3 = HIGH
  4–5 = CRITICAL

Overall status:
  max_score >= 4 → CRITICAL
  max_score >= 3 → HIGH
  max_score >= 2 → MODERATE
  max_score >= 1 → LOW
  else           → NORMAL
"""


def compute_risk(w: dict) -> dict:
    """
    Compute multi-hazard risk from an OpenWeatherMap weather dict.

    Parameters
    ----------
    w : dict
        Parsed weather response (output of external_apis._parse_weather).

    Returns
    -------
    dict with keys:
        risks     : {hazard_name: score_0_to_5}
        overall   : "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | "NORMAL"
        max_score : int (0–5)
    """
    temp  = w.get("temp", 25)
    humid = w.get("humidity", 50)
    wind  = w.get("wind_speed", 0)
    rain  = w.get("rain_1h", 0)
    icon  = w.get("icon", "Clear")
    vis   = w.get("visibility", 10000)

    risks: dict[str, int] = {}

    # ── Cyclone (wind speed m/s) ──────────────────────────────
    if wind > 32:    c = 5
    elif wind > 24:  c = 4
    elif wind > 17:  c = 3
    elif wind > 10:  c = 2
    elif wind > 6:   c = 1
    else:            c = 0
    risks["cyclone"] = c

    # ── Flood (rain mm/h + humidity modifier) ─────────────────
    if rain > 50:    f = 5
    elif rain > 20:  f = 4
    elif rain > 7.5: f = 3
    elif rain > 2.5: f = 2
    elif rain > 0:   f = 1
    else:            f = 0
    if humid > 90:
        f = min(5, f + 1)
    risks["flood"] = f

    # ── Heatwave (°C) ─────────────────────────────────────────
    if temp >= 47:   h = 5
    elif temp >= 44: h = 4
    elif temp >= 40: h = 3
    elif temp >= 37: h = 2
    elif temp >= 34: h = 1
    else:            h = 0
    risks["heatwave"] = h

    # ── Cold wave (°C) ────────────────────────────────────────
    if temp <= 0:    co = 5
    elif temp <= 4:  co = 4
    elif temp <= 8:  co = 3
    elif temp <= 12: co = 2
    elif temp <= 15: co = 1
    else:            co = 0
    risks["cold_wave"] = co

    # ── Dense fog (visibility metres) ────────────────────────
    if vis < 50:     fg = 5
    elif vis < 200:  fg = 4
    elif vis < 500:  fg = 3
    elif vis < 1000: fg = 2
    elif vis < 2000: fg = 1
    else:            fg = 0
    risks["dense_fog"] = fg

    # ── Thunderstorm / lightning ──────────────────────────────
    risks["thunderstorm"] = 5 if icon == "Thunderstorm" else 0
    risks["lightning"]    = 4 if (icon == "Thunderstorm" and humid > 75) else 0

    mx = max(risks.values())
    if mx >= 4:      overall = "CRITICAL"
    elif mx >= 3:    overall = "HIGH"
    elif mx >= 2:    overall = "MODERATE"
    elif mx >= 1:    overall = "LOW"
    else:            overall = "NORMAL"

    return {"risks": risks, "overall": overall, "max_score": mx}


# ── Risk metadata (icon + display label) used by blueprints ──
RISK_META: dict[str, dict] = {
    "cyclone":     {"icon": "🌀", "l": "Cyclone"},
    "flood":       {"icon": "🌊", "l": "Flood"},
    "heatwave":    {"icon": "🌡", "l": "Heatwave"},
    "cold_wave":   {"icon": "❄️",  "l": "Cold Wave"},
    "dense_fog":   {"icon": "🌫", "l": "Dense Fog"},
    "thunderstorm":{"icon": "⛈", "l": "Thunderstorm"},
    "lightning":   {"icon": "⚡", "l": "Lightning"},
}
