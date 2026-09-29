"""
blueprints/alerts/routes.py

Routes:
  GET /api/news
  GET /api/alerts
  GET /api/gdacs-events
  GET /api/guidelines
  GET /api/guidelines/<disaster>
"""

from flask import Blueprint, jsonify

from services.external_apis import classify_alert_level, fetch_gdacs_events, fetch_verified_news
from blueprints.alerts.guidelines import GUIDELINES

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/api/news")
def news():
    items = fetch_verified_news()
    return jsonify({
        "news": items,
        "source_note": (
            "All news from verified official sources: "
            "GDACS, ReliefWeb, EMSC, WHO, UN OCHA only."
        ),
    })


@alerts_bp.route("/api/alerts")
def alerts():
    items      = fetch_verified_news()
    alerts_out = []
    counts     = {"CRITICAL": 0, "HIGH": 0}

    for it in items:
        level = classify_alert_level(it["title"], it.get("desc", ""))
        if level is None:
            continue
        counts[level] += 1
        alerts_out.append({
            "state":   "India",
            "type":    "Disaster Alert",
            "level":   level,
            "message": it["title"],
            "issued":  it["source"],
            "link":    it.get("link", ""),
            "date":    it.get("date", ""),
        })

    return jsonify({
        "alerts":      alerts_out[:15],
        "verified":    True,
        "counts":      counts,
        "filter_note": (
            "Only HIGH and CRITICAL severity alerts are returned. "
            "LOW and MODERATE alerts are excluded at the server level."
        ),
    })


@alerts_bp.route("/api/gdacs-events")
def gdacs_events():
    events = fetch_gdacs_events()
    return jsonify({
        "events":  events,
        "total":   len(events),
        "source":  "GDACS — UN/EU Global Disaster Alert and Coordination System",
        "cached":  True,
    })


@alerts_bp.route("/api/guidelines")
def guidelines_all():
    return jsonify({"guidelines": GUIDELINES})


@alerts_bp.route("/api/guidelines/<disaster>")
def guideline(disaster):
    g = GUIDELINES.get(disaster.lower())
    if not g:
        return jsonify({"error": "Not found"}), 404
    return jsonify(g)
