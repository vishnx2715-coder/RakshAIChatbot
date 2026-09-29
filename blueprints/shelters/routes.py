"""
blueprints/shelters/routes.py

Routes:
  GET  /api/shelters
  POST /api/nearby-shelters
  POST /api/overpass
  POST /api/osrm-table
  POST /api/osrm-route
  POST /api/ors-matrix
  POST /api/ors-route
"""

from flask import Blueprint, jsonify, request

from config import Config
from services.external_apis import (
    find_nearby_shelters,
    ors_matrix,
    ors_route,
    osrm_route,
    osrm_table,
    overpass_query,
)

shelters_bp = Blueprint("shelters", __name__)

# ── Static NDMA-registered shelter data ──────────────────────
SHELTER_DATA = [
    {"id": 1, "name": "Chennai Corporation Shelter — Chepauk",   "lat": 13.0628, "lon": 80.2797, "capacity": 2500, "available": True,  "facilities": ["water","food","medical","toilets"], "contact": "044-25384520", "district": "Chennai"},
    {"id": 2, "name": "Koyambedu Bus Terminus Shelter",           "lat": 13.0700, "lon": 80.1951, "capacity": 5000, "available": True,  "facilities": ["water","food","toilets"],            "contact": "044-24793500", "district": "Chennai"},
    {"id": 3, "name": "YMCA Nandanam Relief Camp",                "lat": 13.0250, "lon": 80.2415, "capacity": 1500, "available": True,  "facilities": ["water","food","medical"],            "contact": "044-24330624", "district": "Chennai"},
    {"id": 4, "name": "Nehru Indoor Stadium Shelter",             "lat": 13.0668, "lon": 80.2776, "capacity": 3000, "available": False, "facilities": ["water","toilets"],                  "contact": "044-28444571", "district": "Chennai"},
    {"id": 5, "name": "Perambur Government School Relief Camp",   "lat": 13.1167, "lon": 80.2333, "capacity": 2000, "available": True,  "facilities": ["water","food","medical","toilets"], "contact": "044-26621234", "district": "Chennai"},
    {"id": 6, "name": "Ambattur Relief Centre",                   "lat": 13.0982, "lon": 80.1551, "capacity": 3000, "available": True,  "facilities": ["water","food","toilets"],            "contact": "044-26583322", "district": "Chennai"},
    {"id": 7, "name": "Tambaram District Shelter",                "lat": 12.9249, "lon": 80.1000, "capacity": 1800, "available": True,  "facilities": ["water","medical"],                  "contact": "044-22262100", "district": "Chengalpattu"},
    {"id": 8, "name": "Tiruvallur District Collectorate Shelter", "lat": 13.1427, "lon": 79.9080, "capacity": 2500, "available": True,  "facilities": ["water","food","medical","toilets"], "contact": "044-27662200", "district": "Tiruvallur"},
]


@shelters_bp.route("/api/shelters")
def shelters():
    district       = request.args.get("district", "").strip()
    available_only = request.args.get("available", "false").lower() == "true"
    result = list(SHELTER_DATA)
    if district:
        result = [s for s in result if s["district"].lower() == district.lower()]
    if available_only:
        result = [s for s in result if s["available"]]
    return jsonify({
        "shelters":        result,
        "total":           len(result),
        "available_count": sum(1 for s in result if s["available"]),
        "source":          "NDMA registered shelter sites",
    })


@shelters_bp.route("/api/nearby-shelters", methods=["POST"])
def nearby_shelters():
    body   = request.get_json(force=True, silent=True) or {}
    lat    = body.get("lat")
    lon    = body.get("lon")
    radius = int(body.get("radius", 5000))
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    results = find_nearby_shelters(lat, lon, radius)
    return jsonify({"elements": results, "source": "nominatim", "total": len(results)})


@shelters_bp.route("/api/overpass", methods=["POST"])
def overpass_proxy():
    body  = request.get_json(force=True, silent=True) or {}
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"error": "no query"}), 400
    result = overpass_query(query)
    if "error" in result and "elements" not in result:
        return jsonify(result), 502
    return jsonify(result)


@shelters_bp.route("/api/osrm-table", methods=["POST"])
def osrm_table_route():
    body      = request.get_json(force=True, silent=True) or {}
    user_lat  = body.get("user_lat")
    user_lon  = body.get("user_lon")
    shelters  = body.get("shelters", [])
    if user_lat is None or user_lon is None or not shelters:
        return jsonify({"error": "user_lat, user_lon and shelters required"}), 400
    results = osrm_table(user_lat, user_lon, shelters)
    return jsonify({"results": results})


@shelters_bp.route("/api/osrm-route", methods=["POST"])
def osrm_route_endpoint():
    body     = request.get_json(force=True, silent=True) or {}
    profile  = body.get("profile", "driving")
    user_lat = body.get("user_lat")
    user_lon = body.get("user_lon")
    dest_lat = body.get("dest_lat")
    dest_lon = body.get("dest_lon")
    if None in (user_lat, user_lon, dest_lat, dest_lon):
        return jsonify({"error": "missing coordinates"}), 400
    try:
        data = osrm_route(profile, user_lat, user_lon, dest_lat, dest_lon)
        if "error" in data:
            return jsonify(data), 502
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@shelters_bp.route("/api/ors-matrix", methods=["POST"])
def ors_matrix_route():
    if not Config.ORS_API_KEY:
        return jsonify({"error": "ORS_API_KEY not configured"}), 503
    body     = request.get_json(force=True, silent=True) or {}
    user_lat = body.get("user_lat")
    user_lon = body.get("user_lon")
    shelters = body.get("shelters", [])
    profile  = body.get("profile", "driving-car")
    if user_lat is None or user_lon is None or not shelters:
        return jsonify({"error": "user_lat, user_lon and shelters required"}), 400
    results = ors_matrix(user_lat, user_lon, shelters, profile)
    return jsonify({"results": results})


@shelters_bp.route("/api/ors-route", methods=["POST"])
def ors_route_endpoint():
    if not Config.ORS_API_KEY:
        return jsonify({"error": "ORS_API_KEY not configured"}), 503
    body     = request.get_json(force=True, silent=True) or {}
    profile  = body.get("profile", "driving-car")
    user_lat = body.get("user_lat")
    user_lon = body.get("user_lon")
    dest_lat = body.get("dest_lat")
    dest_lon = body.get("dest_lon")
    if None in (user_lat, user_lon, dest_lat, dest_lon):
        return jsonify({"error": "missing coordinates"}), 400
    try:
        data = ors_route(profile, user_lat, user_lon, dest_lat, dest_lon)
        if "error" in data:
            return jsonify(data), 502
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
