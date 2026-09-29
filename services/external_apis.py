"""
services/external_apis.py — All outbound HTTP calls for RAKSHA.

Functions here are pure data-fetchers:
  - No Flask request/session context.
  - No caching (cache_service wraps these in Phase 6).
  - Return plain Python dicts/lists.

Callers: blueprints/* and other services.
"""

import math
import re
import time
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import Config

# ── Shared headers ────────────────────────────────────────────
_NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_HDRS = {
    "User-Agent": "RAKSHA-DisasterAI/2.0 (Emergency Shelter Finder; contact@raksha.gov.in)",
    "Accept-Language": "en",
}
_OSM_API = "https://api.openstreetmap.org/api/0.6"
OSRM_BASE = "https://router.project-osrm.org"
ORS_BASE  = "https://api.openrouteservice.org"

_SHELTER_AMENITIES = [
    "school", "college", "university",
    "hospital", "clinic",
    "community_centre", "townhall",
    "place_of_worship",
    "fire_station", "police",
]

_OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# ════════════════════════════════════════════════════════════════
# OpenWeatherMap
# ════════════════════════════════════════════════════════════════

def _parse_weather(d: dict) -> dict:
    """Normalise a raw OWM /weather JSON response into RAKSHA's shape."""
    return {
        "city":       d.get("name", "Unknown"),
        "country":    d.get("sys", {}).get("country", ""),
        "temp":       round(d["main"]["temp"], 1),
        "feels_like": round(d["main"]["feels_like"], 1),
        "temp_min":   round(d["main"].get("temp_min", 0), 1),
        "temp_max":   round(d["main"].get("temp_max", 0), 1),
        "humidity":   d["main"]["humidity"],
        "pressure":   d["main"]["pressure"],
        "wind_speed": d.get("wind", {}).get("speed", 0),
        "wind_deg":   d.get("wind", {}).get("deg", 0),
        "desc":       d["weather"][0]["description"],
        "icon_code":  d["weather"][0]["icon"],
        "icon":       d["weather"][0]["main"],
        "visibility": d.get("visibility", 10000),
        "clouds":     d.get("clouds", {}).get("all", 0),
        "rain_1h":    d.get("rain", {}).get("1h", 0),
        "uv":         0,
        "lat":        d.get("coord", {}).get("lat", 20.5937),
        "lon":        d.get("coord", {}).get("lon", 78.9629),
        "sunrise":    d.get("sys", {}).get("sunrise", 0),
        "sunset":     d.get("sys", {}).get("sunset", 0),
    }


def get_weather_city(city: str) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={Config.OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        d = requests.get(url, timeout=5).json()
        return _parse_weather(d) if "main" in d else {"error": d.get("message", "City not found")}
    except Exception as e:
        return {"error": str(e)}


def get_weather_coords(lat: float, lon: float) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={Config.OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        d = requests.get(url, timeout=5).json()
        return _parse_weather(d) if "main" in d else {"error": d.get("message", "Error")}
    except Exception as e:
        return {"error": str(e)}


def get_forecast(lat: float, lon: float) -> list:
    url = (
        f"http://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={Config.OPENWEATHER_API_KEY}&units=metric&cnt=8"
    )
    try:
        d = requests.get(url, timeout=5).json()
        return [
            {
                "time": i["dt_txt"][11:16],
                "temp": i["main"]["temp"],
                "icon": i["weather"][0]["main"],
                "desc": i["weather"][0]["description"],
                "wind": i.get("wind", {}).get("speed", 0),
                "rain": i.get("rain", {}).get("3h", 0),
                "pop":  round(i.get("pop", 0) * 100),
            }
            for i in d.get("list", [])
        ]
    except Exception:
        return []


# ════════════════════════════════════════════════════════════════
# RSS / News
# ════════════════════════════════════════════════════════════════

OFFICIAL_RSS = [
    ("GDACS Global Alerts", "https://www.gdacs.org/xml/rss.xml"),
    ("ReliefWeb India",     "https://reliefweb.int/country/ind/rss.xml"),
    ("EMSC Earthquakes",    "https://www.emsc-csem.org/service/rss/rss.php?typ=emsc"),
    ("WHO Emergencies",     "https://www.who.int/feeds/entity/csr/don/en/rss.xml"),
    ("UN OCHA Asia",        "https://reliefweb.int/region/asia/rss.xml"),
]

RSS_PER_SOURCE_TIMEOUT = 4

_rss_cache: dict = {"data": None, "ts": 0, "refreshing": False}
RSS_TTL_SECONDS = Config.RSS_TTL_SECONDS  # 300


def _fetch_one_feed(source_url_pair: tuple) -> list:
    source, url = source_url_pair
    headers = {"User-Agent": "RAKSHA-DisasterAI/1.0 (Government Emergency Platform)"}
    items = []
    kws = [
        "india", "flood", "cyclone", "earthquake", "storm", "disaster", "emergency",
        "tsunami", "landslide", "heat", "drought", "fire", "alert", "warning",
        "bangladesh", "nepal", "srilanka", "myanmar", "asia",
    ]
    try:
        r = requests.get(url, timeout=RSS_PER_SOURCE_TIMEOUT, headers=headers)
        if r.status_code != 200:
            return items
        root = ET.fromstring(r.content)
        count = 0
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link")  or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = (item.findtext("pubDate") or "")[:22].strip()
            if not title or len(title) < 5:
                continue
            relevant = any(k in (title + desc).lower() for k in kws)
            if not relevant and "reliefweb" not in url:
                relevant = True
            if relevant:
                items.append({
                    "source":   source,
                    "title":    title[:140],
                    "link":     link,
                    "desc":     desc[:200],
                    "date":     pub,
                    "verified": True,
                    "type":     "official",
                })
                count += 1
            if count >= 5:
                break
    except Exception:
        pass
    return items


def _do_rss_refresh() -> None:
    global _rss_cache
    if _rss_cache.get("refreshing"):
        return
    _rss_cache["refreshing"] = True
    try:
        all_items: list = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(_fetch_one_feed, pair): pair for pair in OFFICIAL_RSS}
            for future in as_completed(futures):
                try:
                    all_items.extend(future.result())
                except Exception:
                    pass
        if all_items:
            _rss_cache["data"] = all_items[:25]
            _rss_cache["ts"]   = time.monotonic()
    except Exception:
        pass
    finally:
        _rss_cache["refreshing"] = False


def fetch_verified_news() -> list:
    """
    Return cached RSS data. Refreshes in background when TTL expires.
    Blocks only on cold start (first ever call).
    """
    global _rss_cache
    now  = time.monotonic()
    data = _rss_cache["data"]

    if data is None:
        _do_rss_refresh()
        return _rss_cache["data"] or []

    if (now - _rss_cache["ts"]) > RSS_TTL_SECONDS and not _rss_cache.get("refreshing"):
        threading.Thread(target=_do_rss_refresh, daemon=True).start()

    return data


# ════════════════════════════════════════════════════════════════
# GDACS
# ════════════════════════════════════════════════════════════════

GDACS_EVENT_ICONS = {
    "EQ": "🏚", "TC": "🌀", "FL": "🌊", "VO": "🌋",
    "DR": "🏜", "WF": "🔥", "TS": "🌊", "SS": "🌊",
}
GDACS_ALERT_MAP = {"Red": "CRITICAL", "Orange": "HIGH", "Green": "LOW"}

_gdacs_cache: dict = {"data": None, "ts": 0}
GDACS_TTL = Config.GDACS_TTL_SECONDS  # 600


def fetch_gdacs_events() -> list:
    global _gdacs_cache
    now = time.monotonic()
    if _gdacs_cache["data"] is not None and (now - _gdacs_cache["ts"]) < GDACS_TTL:
        return _gdacs_cache["data"]

    results = []
    seen_ids: set = set()
    try:
        url = (
            "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
            "?eventlist=EQ;TC;FL;VO;DR;WF"
            "&alertlevel=Green;Orange;Red"
            "&pagesize=50"
        )
        r = requests.get(url, timeout=15, headers={"User-Agent": "RAKSHA-DisasterAI/2.0"})
        if r.status_code == 200:
            for f in r.json().get("features", []):
                p      = f.get("properties", {})
                geo    = f.get("geometry", {})
                coords = geo.get("coordinates", [None, None])
                if not coords or coords[0] is None:
                    continue
                eid = p.get("eventid", 0)
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                alert_level  = p.get("alertlevel", "Green")
                raksha_level = GDACS_ALERT_MAP.get(alert_level, "LOW")
                etype        = p.get("eventtype", "EQ")
                color = (
                    "#DC2626" if alert_level == "Red" else
                    "#EA580C" if alert_level == "Orange" else "#22d3ee"
                )
                results.append({
                    "id":          eid,
                    "name":        p.get("name", "Unknown Event"),
                    "type":        etype,
                    "icon":        GDACS_EVENT_ICONS.get(etype, "⚠️"),
                    "alert":       alert_level,
                    "level":       raksha_level,
                    "country":     p.get("country", ""),
                    "lat":         coords[1],
                    "lon":         coords[0],
                    "date":        (p.get("fromdate") or "")[:10],
                    "description": p.get("description") or p.get("name", ""),
                    "url": (
                        p.get("url", {}).get("report", "")
                        if isinstance(p.get("url"), dict) else ""
                    ),
                    "color": color,
                })
    except Exception as e:
        print(f"[GDACS] fetch error: {e}")

    _gdacs_cache["data"] = results
    _gdacs_cache["ts"]   = now
    return results


# ════════════════════════════════════════════════════════════════
# Alert severity classification (shared by alerts + maps blueprints)
# ════════════════════════════════════════════════════════════════

CRITICAL_KWS = [
    "red alert", "red warning", "extreme warning",
    "tsunami", "tsunami warning", "tsunami watch",
    "cyclone landfall", "super cyclone", "severe cyclonic storm",
    "extremely severe", "catastrophic",
    "major earthquake", "strong earthquake",
    "nuclear emergency", "chemical disaster",
    "mass casualty", "evacuation order", "evacuate immediately",
    "dam breach", "dam failure", "flash flood warning",
    "orange alert",
]
HIGH_KWS = [
    "warning", "alert", "emergency", "severe",
    "cyclone", "flood", "earthquake", "storm",
    "landslide", "wildfire", "forest fire",
    "heat wave", "heatwave", "cold wave",
    "heavy rain", "very heavy rain",
    "thunderstorm", "lightning",
    "drought", "water scarcity",
    "pandemic", "outbreak", "epidemic",
    "yellow alert",
]


def classify_alert_level(title: str, desc: str):
    """Returns 'CRITICAL', 'HIGH', or None (drop the item)."""
    text = (title + " " + desc).lower()
    if any(k in text for k in CRITICAL_KWS):
        return "CRITICAL"
    if any(k in text for k in HIGH_KWS):
        return "HIGH"
    return None


# ════════════════════════════════════════════════════════════════
# Nominatim / OSM shelter search
# ════════════════════════════════════════════════════════════════

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nominatim_search(amenity: str, lat: float, lon: float, radius_m: int) -> list:
    lat_delta = (radius_m * 1.3) / 111320.0
    lon_delta = (radius_m * 1.3) / (111320.0 * math.cos(math.radians(lat)))
    quadrants = [
        (lon,             lat + lat_delta, lon + lon_delta, lat),
        (lon - lon_delta, lat + lat_delta, lon,             lat),
        (lon,             lat,             lon + lon_delta, lat - lat_delta),
        (lon - lon_delta, lat,             lon,             lat - lat_delta),
    ]
    all_results, seen = [], set()
    for (min_lon, max_lat, max_lon, min_lat) in quadrants:
        params = {
            "amenity": amenity, "format": "jsonv2", "addressdetails": 1,
            "limit": 50, "viewbox": f"{min_lon},{max_lat},{max_lon},{min_lat}", "bounded": 1,
        }
        try:
            r = requests.get(_NOMINATIM_BASE, params=params, headers=_NOMINATIM_HDRS, timeout=10)
            if r.status_code == 200:
                for item in (r.json() or []):
                    oid = item.get("osm_id")
                    if oid and oid not in seen:
                        seen.add(oid)
                        all_results.append(item)
        except Exception:
            pass
    return all_results


def _fetch_osm_tags(r: dict) -> tuple:
    osm_type = r["osm_type"]
    osm_id   = r["osm_id"]
    try:
        resp = requests.get(
            f"{_OSM_API}/{osm_type}/{osm_id}.json",
            headers=_NOMINATIM_HDRS, timeout=8,
        )
        if resp.status_code == 200:
            elements = resp.json().get("elements", [])
            if elements:
                return osm_id, elements[0].get("tags", {})
    except Exception:
        pass
    return osm_id, {}


def find_nearby_shelters(lat: float, lon: float, radius: int) -> list:
    """
    Find nearby shelter candidates via Nominatim + OSM tag enrichment.
    Returns a list of element dicts matching the /api/nearby-shelters shape.
    """
    radius = min(radius, 25000)
    raw_results = []
    seen_ids: set = set()

    with ThreadPoolExecutor(max_workers=len(_SHELTER_AMENITIES)) as pool:
        futures = {
            pool.submit(nominatim_search, am, lat, lon, radius): am
            for am in _SHELTER_AMENITIES
        }
        for future in as_completed(futures):
            amenity_type = futures[future]
            try:
                for item in future.result():
                    osm_id   = item.get("osm_id")
                    item_lat = float(item.get("lat", 0))
                    item_lon = float(item.get("lon", 0))
                    if not osm_id or osm_id in seen_ids or not item_lat or not item_lon:
                        continue
                    if _haversine_km(lat, lon, item_lat, item_lon) > (radius / 1000) + 0.2:
                        continue
                    name = item.get("display_name", "").split(",")[0].strip()
                    if not name or len(name) < 3:
                        continue
                    seen_ids.add(osm_id)
                    addr = item.get("address", {})
                    raw_results.append({
                        "osm_id":   osm_id,
                        "osm_type": item.get("osm_type", "node"),
                        "lat":      item_lat,
                        "lon":      item_lon,
                        "name":     name,
                        "amenity":  amenity_type,
                        "road":     addr.get("road", ""),
                        "city":     addr.get("city") or addr.get("town") or addr.get("village") or "",
                        "suburb":   addr.get("suburb", ""),
                        "postcode": addr.get("postcode", ""),
                    })
            except Exception:
                pass

    if not raw_results:
        return []

    # Enrich with full OSM tags (phone, hours, operator …)
    osm_tags_map: dict = {}
    with ThreadPoolExecutor(max_workers=20) as pool:
        for osm_id, tags_data in pool.map(_fetch_osm_tags, raw_results):
            if tags_data:
                osm_tags_map[osm_id] = tags_data

    results = []
    for r in raw_results:
        et     = osm_tags_map.get(r["osm_id"], {})
        phone  = (
            et.get("phone") or et.get("contact:phone") or et.get("telephone") or
            et.get("contact:mobile") or et.get("mobile") or et.get("phone_1") or ""
        )
        if phone:
            phone = phone.strip().replace(";", " / ").replace(",", " / ")
        address = (
            et.get("addr:full") or et.get("address") or
            ", ".join(p for p in [r["road"], r["suburb"], r["city"]] if p)
        )
        tags = {
            "name":           r["name"],
            "amenity":        r["amenity"],
            "addr:street":    r["road"],
            "addr:city":      r["city"],
            "phone":          phone,
            "contact:phone":  phone,
            "opening_hours":  et.get("opening_hours", "24/7 during emergencies"),
            "operator":       et.get("operator", "Local Authority / NDMA"),
            "website":        et.get("website") or et.get("contact:website") or et.get("url") or "",
            "email":          et.get("email") or et.get("contact:email") or "",
            "full_address":   address,
            "capacity":       et.get("capacity") or et.get("capacity:persons") or "",
        }
        results.append({
            "id":     r["osm_id"],
            "type":   r["osm_type"],
            "lat":    r["lat"],
            "lon":    r["lon"],
            "tags":   tags,
            "center": {"lat": r["lat"], "lon": r["lon"]},
        })
    return results


def overpass_query(query: str) -> dict:
    """
    Try Overpass mirrors; fall back to Nominatim if all fail.
    Returns a dict matching Overpass JSON format ({"elements": [...]}).
    """
    hdrs = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "RAKSHA/1.0"}
    last_err = ""
    for mirror in _OVERPASS_MIRRORS:
        try:
            r = requests.post(mirror, data={"data": query}, headers=hdrs, timeout=12)
            if r.status_code != 200:
                last_err = f"HTTP {r.status_code}"
                continue
            j = r.json()
            if "remark" in j and "rate limit" in str(j.get("remark", "")):
                last_err = "rate limited"
                continue
            return j
        except Exception as e:
            last_err = str(e)
            continue

    # Fallback: parse lat/lon/radius from Overpass QL and use Nominatim
    m = re.search(r'around:(\d+),([\d.\-]+),([\d.\-]+)', query)
    if m:
        radius = int(m.group(1))
        lat    = float(m.group(2))
        lon    = float(m.group(3))
        raw = []
        seen_ids: set = set()
        with ThreadPoolExecutor(max_workers=len(_SHELTER_AMENITIES)) as pool:
            futures = {
                pool.submit(nominatim_search, am, lat, lon, radius): am
                for am in _SHELTER_AMENITIES
            }
            for future in as_completed(futures):
                amenity_type = futures[future]
                try:
                    for item in future.result():
                        osm_id   = item.get("osm_id")
                        item_lat = float(item.get("lat", 0))
                        item_lon = float(item.get("lon", 0))
                        if not osm_id or osm_id in seen_ids or not item_lat or not item_lon:
                            continue
                        seen_ids.add(osm_id)
                        name = item.get("display_name", "").split(",")[0].strip()
                        if not name or len(name) < 3:
                            continue
                        addr = item.get("address", {})
                        raw.append({
                            "id": osm_id, "type": item.get("osm_type", "node"),
                            "lat": item_lat, "lon": item_lon,
                            "tags": {
                                "name": name, "amenity": amenity_type,
                                "addr:street": addr.get("road", ""),
                                "addr:city": addr.get("city") or addr.get("town") or addr.get("village") or "",
                                "phone": "",
                                "opening_hours": "24/7 during emergencies",
                                "operator": "Local Authority / NDMA",
                            },
                            "center": {"lat": item_lat, "lon": item_lon},
                        })
                except Exception:
                    pass
        return {"elements": raw, "source": "nominatim_fallback"}

    return {"error": "All Overpass mirrors failed", "detail": last_err}


# ════════════════════════════════════════════════════════════════
# OSRM
# ════════════════════════════════════════════════════════════════

def osrm_table(user_lat: float, user_lon: float, shelters: list) -> list:
    """
    Batch road distances via OSRM Table API.
    Returns list of {id, drive_m, drive_sec, walk_m, walk_sec}.
    """
    shelters = shelters[:99]
    results  = []
    chunk_size = 25
    for i in range(0, len(shelters), chunk_size):
        chunk  = shelters[i: i + chunk_size]
        coords = f"{user_lon},{user_lat};" + ";".join(f"{s['lon']},{s['lat']}" for s in chunk)
        url    = f"{OSRM_BASE}/table/v1/driving/{coords}?sources=0&annotations=distance,duration"
        try:
            r    = requests.get(url, timeout=10)
            data = r.json()
            if r.status_code != 200 or data.get("code") != "Ok":
                continue
            dists = data.get("distances", [[]])[0]
            durs  = data.get("durations", [[]])[0]
            for j, s in enumerate(chunk):
                dist_m = dists[j + 1] if (j + 1) < len(dists) else None
                dur_s  = durs[j + 1]  if (j + 1) < len(durs)  else None
                if dist_m is not None and dist_m > 0:
                    results.append({
                        "id":       s["id"],
                        "drive_m":  dist_m,
                        "drive_sec": dur_s,
                        "walk_m":   dist_m,
                        "walk_sec": int(dist_m / 1.38),
                    })
        except Exception as e:
            print(f"[OSRM] Table chunk {i} failed: {e}")
    return results


def osrm_route(profile: str, user_lat: float, user_lon: float,
               dest_lat: float, dest_lon: float) -> dict:
    """Full route geometry from OSRM."""
    osrm_profile = "driving" if profile in ("foot", "walking", "foot-walking") else profile
    url = (
        f"{OSRM_BASE}/route/v1/{osrm_profile}/"
        f"{user_lon},{user_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=geojson"
    )
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return {"error": f"OSRM HTTP {r.status_code}"}
    data = r.json()
    data["_profile_used"]      = osrm_profile
    data["_profile_requested"] = profile
    return data


# ════════════════════════════════════════════════════════════════
# OpenRouteService
# ════════════════════════════════════════════════════════════════

def ors_matrix(user_lat: float, user_lon: float, shelters: list, profile: str) -> list:
    """ORS Matrix API — real road distances + durations."""
    if not Config.ORS_API_KEY:
        return []
    headers = {
        "Authorization": Config.ORS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    shelters = shelters[:49]
    results  = []
    chunk_size = 49
    for i in range(0, len(shelters), chunk_size):
        chunk     = shelters[i: i + chunk_size]
        locations = [[user_lon, user_lat]] + [[s["lon"], s["lat"]] for s in chunk]
        payload   = {
            "locations":    locations,
            "sources":      [0],
            "destinations": list(range(1, len(locations))),
            "metrics":      ["distance", "duration"],
            "units":        "m",
        }
        try:
            r = requests.post(
                f"{ORS_BASE}/v2/matrix/{profile}",
                json=payload, headers=headers, timeout=15,
            )
            if r.status_code != 200:
                continue
            data      = r.json()
            distances = (data.get("distances") or [[]])[0]
            durations = (data.get("durations") or [[]])[0]
            for j, s in enumerate(chunk):
                dist_m = distances[j] if j < len(distances) else None
                dur_s  = durations[j]  if j < len(durations)  else None
                if dist_m is not None:
                    results.append({
                        "id":         s["id"],
                        "distance_m": round(dist_m),
                        "duration_s": round(dur_s) if dur_s is not None else None,
                    })
        except Exception as e:
            print(f"[ORS Matrix] chunk {i} error: {e}")
    return results


def ors_route(profile: str, user_lat: float, user_lon: float,
              dest_lat: float, dest_lon: float) -> dict:
    """ORS Directions API — full route geometry."""
    if not Config.ORS_API_KEY:
        return {"error": "ORS_API_KEY not configured"}
    headers = {
        "Authorization": Config.ORS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json, application/geo+json",
    }
    payload = {"coordinates": [[user_lon, user_lat], [dest_lon, dest_lat]], "format": "geojson"}
    r = requests.post(
        f"{ORS_BASE}/v2/directions/{profile}/geojson",
        json=payload, headers=headers, timeout=15,
    )
    if r.status_code != 200:
        return {"error": f"ORS HTTP {r.status_code}", "detail": r.text[:200]}
    data     = r.json()
    feature  = data["features"][0]
    props    = feature["properties"]["summary"]
    return {
        "geometry":   feature["geometry"],
        "distance_m": round(props.get("distance", 0)),
        "duration_s": round(props.get("duration", 0)),
    }
