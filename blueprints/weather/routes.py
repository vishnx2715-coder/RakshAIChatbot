"""
blueprints/weather/routes.py

Routes:
  POST /weather
  GET  /api/india-weather-risk
  POST /api/risk-analysis
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, jsonify, request

from config import Config
from services.external_apis import (
    classify_alert_level,
    fetch_verified_news,
    get_forecast,
    get_weather_city,
    get_weather_coords,
)
from services.risk_engine import RISK_META, compute_risk

weather_bp = Blueprint("weather", __name__)

# ── Indian cities for /api/india-weather-risk ─────────────────
INDIA_RISK_CITIES = [
    {"name": "Delhi",              "lat": 28.61, "lon": 77.21},
    {"name": "Mumbai",             "lat": 19.07, "lon": 72.87},
    {"name": "Chennai",            "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata",            "lat": 22.57, "lon": 88.36},
    {"name": "Hyderabad",          "lat": 17.38, "lon": 78.48},
    {"name": "Bengaluru",          "lat": 12.97, "lon": 77.59},
    {"name": "Ahmedabad",          "lat": 23.02, "lon": 72.57},
    {"name": "Pune",               "lat": 18.52, "lon": 73.85},
    {"name": "Jaipur",             "lat": 26.91, "lon": 75.78},
    {"name": "Guwahati",           "lat": 26.18, "lon": 91.73},
    {"name": "Bhubaneswar",        "lat": 20.29, "lon": 85.82},
    {"name": "Patna",              "lat": 25.59, "lon": 85.13},
    {"name": "Lucknow",            "lat": 26.85, "lon": 80.91},
    {"name": "Thiruvananthapuram", "lat":  8.52, "lon": 76.93},
    {"name": "Srinagar",           "lat": 34.08, "lon": 74.79},
    {"name": "Visakhapatnam",      "lat": 17.68, "lon": 83.21},
]

_india_risk_cache: dict = {"data": None, "ts": 0}
INDIA_RISK_TTL = Config.INDIA_RISK_TTL_SECONDS


@weather_bp.route("/weather", methods=["POST"])
def weather_only():
    d    = request.json or {}
    lat  = d.get("lat")
    lon  = d.get("lon")
    city = d.get("city", "Chennai")
    w    = get_weather_coords(lat, lon) if (lat and lon) else get_weather_city(city)
    r    = compute_risk(w) if w and "error" not in w else None
    fc   = get_forecast(w.get("lat", 20.59), w.get("lon", 78.96)) if w and "error" not in w else []
    return jsonify({"weather": w, "risk": r, "forecast": fc})


@weather_bp.route("/api/india-weather-risk")
def india_weather_risk():
    global _india_risk_cache
    now = time.monotonic()
    if _india_risk_cache["data"] is not None and (now - _india_risk_cache["ts"]) < INDIA_RISK_TTL:
        return jsonify(_india_risk_cache["data"])

    results = []

    def _fetch_city(city):
        w = get_weather_coords(city["lat"], city["lon"])
        if not w or "error" in w:
            return None
        r = compute_risk(w)
        if not r or r["overall"] in ("NORMAL", "LOW", "MODERATE"):
            return None
        top_hazards = sorted(
            [(k, v) for k, v in r["risks"].items() if v >= 3],
            key=lambda x: -x[1],
        )[:3]
        return {
            "name":     city["name"],
            "lat":      city["lat"],
            "lon":      city["lon"],
            "level":    r["overall"],
            "temp":     w.get("temp"),
            "humidity": w.get("humidity"),
            "wind":     w.get("wind_speed"),
            "rain":     w.get("rain_1h", 0),
            "desc":     w.get("desc", ""),
            "hazards":  [
                {
                    "key": k, "score": v,
                    "icon": RISK_META.get(k, {}).get("icon", "⚠️"),
                    "label": RISK_META.get(k, {}).get("l", k),
                }
                for k, v in top_hazards
            ],
            "color": "#DC2626" if r["overall"] == "CRITICAL" else "#EA580C",
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(_fetch_city, INDIA_RISK_CITIES):
            if result:
                results.append(result)

    payload = {
        "cities": results,
        "total": len(results),
        "source": "OpenWeatherMap live data",
        "note": "Only HIGH and CRITICAL risk cities shown",
    }
    _india_risk_cache["data"] = payload
    _india_risk_cache["ts"]   = now
    return jsonify(payload)


@weather_bp.route("/api/risk-analysis", methods=["POST"])
def risk_analysis():
    d   = request.json or {}
    lat = d.get("lat", 20.5937)
    lon = d.get("lon", 78.9629)

    weather = get_weather_coords(lat, lon)
    risk    = compute_risk(weather) if weather and "error" not in weather else None

    risk_items = []
    if risk and risk["overall"] in ("HIGH", "CRITICAL"):
        for hazard, score in risk["risks"].items():
            if score >= 3:
                hazard_level = "CRITICAL" if score >= 4 else "HIGH"
                risk_items.append({
                    "hazard": hazard,
                    "score":  score,
                    "level":  hazard_level,
                    "color":  "#DC2626" if hazard_level == "CRITICAL" else "#EA580C",
                })

    rss_items  = fetch_verified_news()
    rss_alerts = []
    for it in rss_items:
        level = classify_alert_level(it["title"], it.get("desc", ""))
        if level:
            rss_alerts.append({"level": level, "title": it["title"], "source": it["source"]})

    return jsonify({
        "weather":    weather,
        "risk":       risk,
        "risk_items": risk_items,
        "rss_alerts": rss_alerts[:8],
        "legend": [
            {"level": "CRITICAL", "color": "#DC2626", "label": "Critical risk"},
            {"level": "HIGH",     "color": "#EA580C", "label": "High risk"},
        ],
        "filter_note": "MODERATE, LOW, and NORMAL risk zones are not rendered on this map.",
    })
