"""
tests/test_routes.py — Route registry snapshot + blueprint smoke tests.

Route snapshot: ensures app.url_map never silently loses or gains routes.
Smoke tests: hit every endpoint with mocked external APIs to confirm
             they return the right HTTP status code and JSON shape.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dotenv import load_dotenv
    load_dotenv()
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    application.config["SECRET_KEY"] = "test-secret-key-for-pytest"
    return application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def authed_client(app):
    """Client with a fake logged-in session."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["email"] = "test@example.com"
        sess["name"]  = "Test User"
        sess["lang"]  = "English"
    return c


# ── Route snapshot ────────────────────────────────────────────

EXPECTED_ROUTES = {
    "/",
    "/api/alerts",
    "/api/disaster-zones",
    "/api/gdacs-events",
    "/api/google-auth",
    "/api/guidelines",
    "/api/guidelines/<disaster>",
    "/api/india-weather-risk",
    "/api/languages",
    "/api/login",
    "/api/logout",
    "/api/me",
    "/api/nearby-shelters",
    "/api/news",
    "/api/ors-matrix",
    "/api/ors-route",
    "/api/osrm-route",
    "/api/osrm-table",
    "/api/overpass",
    "/api/register",
    "/api/risk-analysis",
    "/api/set-lang",
    "/api/shelters",
    "/chat",
    "/static/<path:filename>",
    "/weather",
}


def test_route_snapshot(app):
    """Fail if any route is added or removed without updating this snapshot."""
    actual = {str(rule) for rule in app.url_map.iter_rules()}
    missing = EXPECTED_ROUTES - actual
    extra   = actual - EXPECTED_ROUTES
    assert not missing, f"Routes removed: {missing}"
    assert not extra,   f"Routes added (update snapshot): {extra}"


# ── Auth smoke tests ──────────────────────────────────────────

class TestAuthRoutes:
    def test_register_missing_fields(self, client):
        r = client.post("/api/register", json={})
        assert r.status_code == 200
        assert r.get_json()["status"] == "error"

    def test_register_short_password(self, client):
        r = client.post("/api/register", json={
            "name": "Test", "email": "t@t.com", "password": "abc"
        })
        assert r.get_json()["status"] == "error"
        assert "8" in r.get_json()["message"]

    def test_login_missing_fields(self, client):
        r = client.post("/api/login", json={})
        assert r.status_code == 200
        assert r.get_json()["status"] == "error"

    def test_login_generic_error(self, client):
        r = client.post("/api/login", json={"email": "no@exist.com", "password": "whatever1"})
        assert r.get_json()["message"] == "Invalid credentials."

    def test_me_not_logged_in(self, client):
        r = client.get("/api/me")
        assert r.status_code == 200
        assert r.get_json()["logged_in"] is False

    def test_logout(self, client):
        r = client.post("/api/logout")
        assert r.status_code == 200

    def test_languages(self, client):
        r = client.get("/api/languages")
        data = r.get_json()
        assert "languages" in data
        assert "ui_strings" in data
        assert len(data["languages"]) >= 23   # 22 Indian + English


# ── Public data routes ────────────────────────────────────────

class TestPublicDataRoutes:
    def test_shelters(self, client):
        r = client.get("/api/shelters")
        assert r.status_code == 200
        data = r.get_json()
        assert "shelters" in data
        assert data["total"] > 0

    def test_guidelines_all(self, client):
        r = client.get("/api/guidelines")
        assert r.status_code == 200
        assert "guidelines" in r.get_json()

    def test_guidelines_flood(self, client):
        r = client.get("/api/guidelines/flood")
        assert r.status_code == 200
        data = r.get_json()
        assert "before" in data and "during" in data and "after" in data

    def test_guidelines_not_found(self, client):
        r = client.get("/api/guidelines/nonexistent")
        assert r.status_code == 404

    @patch("services.external_apis.fetch_verified_news", return_value=[])
    def test_news_returns_list(self, mock_news, client):
        r = client.get("/api/news")
        assert r.status_code == 200
        assert "news" in r.get_json()

    @patch("services.external_apis.fetch_verified_news", return_value=[])
    def test_alerts_returns_list(self, mock_news, client):
        r = client.get("/api/alerts")
        assert r.status_code == 200
        assert "alerts" in r.get_json()

    @patch("services.external_apis.fetch_gdacs_events", return_value=[])
    def test_gdacs_events(self, mock_gdacs, client):
        r = client.get("/api/gdacs-events")
        assert r.status_code == 200
        assert "events" in r.get_json()

    @patch("services.external_apis.fetch_verified_news", return_value=[])
    def test_disaster_zones(self, mock_news, client):
        r = client.get("/api/disaster-zones")
        assert r.status_code == 200
        assert "zones" in r.get_json()


# ── Weather routes ────────────────────────────────────────────

class TestWeatherRoutes:
    _MOCK_WEATHER = {
        "city": "Chennai", "country": "IN", "temp": 32.0, "feels_like": 35.0,
        "temp_min": 29.0, "temp_max": 34.0, "humidity": 80, "pressure": 1010,
        "wind_speed": 5.0, "wind_deg": 180, "desc": "clear sky",
        "icon_code": "01d", "icon": "Clear", "visibility": 10000,
        "clouds": 5, "rain_1h": 0, "uv": 0,
        "lat": 13.08, "lon": 80.27, "sunrise": 0, "sunset": 0,
    }

    @patch("services.external_apis.get_weather_city")
    def test_weather_by_city(self, mock_w, client):
        mock_w.return_value = self._MOCK_WEATHER
        r = client.post("/weather", json={"city": "Chennai"})
        assert r.status_code == 200
        data = r.get_json()
        assert "weather" in data
        assert "risk" in data

    @patch("services.external_apis.get_weather_coords")
    @patch("services.external_apis.fetch_verified_news", return_value=[])
    def test_risk_analysis(self, mock_news, mock_w, client):
        mock_w.return_value = self._MOCK_WEATHER
        r = client.post("/api/risk-analysis", json={"lat": 13.08, "lon": 80.27})
        assert r.status_code == 200
        assert "risk" in r.get_json()


# ── Chat route (requires auth) ────────────────────────────────

class TestChatRoute:
    def test_chat_unauthenticated(self, client):
        r = client.post("/chat", json={"message": "hello"})
        assert r.status_code == 401

    def test_chat_empty_message(self, authed_client):
        r = authed_client.post("/chat", json={"message": ""})
        assert r.status_code in (200, 401)
