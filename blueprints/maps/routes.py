"""
blueprints/maps/routes.py

Routes:
  GET /api/disaster-zones
"""

from flask import Blueprint, jsonify

from services.external_apis import classify_alert_level, fetch_verified_news

maps_bp = Blueprint("maps", __name__)


@maps_bp.route("/api/disaster-zones")
def disaster_zones():
    """HIGH and CRITICAL alerts formatted for the Disaster Zones map layer."""
    items = fetch_verified_news()
    zones = []
    for it in items:
        level = classify_alert_level(it["title"], it.get("desc", ""))
        if level is None:
            continue
        color = "#DC2626" if level == "CRITICAL" else "#EA580C"
        zones.append({
            "level":  level,
            "color":  color,
            "title":  it["title"],
            "source": it["source"],
            "link":   it.get("link", ""),
            "date":   it.get("date", ""),
        })

    critical_count = sum(1 for z in zones if z["level"] == "CRITICAL")
    high_count     = sum(1 for z in zones if z["level"] == "HIGH")

    return jsonify({
        "zones":          zones[:20],
        "critical_count": critical_count,
        "high_count":     high_count,
        "total":          critical_count + high_count,
        "legend": [
            {"level": "CRITICAL", "color": "#DC2626", "label": "Critical — immediate danger"},
            {"level": "HIGH",     "color": "#EA580C", "label": "High — serious hazard"},
        ],
        "filter_note": "Only HIGH and CRITICAL zones rendered. LOW and MODERATE excluded.",
    })
