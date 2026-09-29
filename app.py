"""
app.py — RAKSHA application factory.

Registers all blueprints and sets up shared config.
All business logic lives in blueprints/ and services/.

Run locally:
    flask --app app run --debug

Run with Gunicorn (production):
    gunicorn "app:create_app()" --workers 3 --timeout 60
"""

import logging
import threading

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from config import Config

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Suppress noisy third-party loggers
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

_log = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory — called by Gunicorn and tests."""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    # ── Session cookie hardening ──────────────────────────────
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Secure flag only in production — dev uses plain HTTP
        SESSION_COOKIE_SECURE=Config.IS_PRODUCTION,
    )

    # ── Rate limiting (flask-limiter) ─────────────────────────
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    # Use Redis as storage backend when available; fall back to in-memory
    _limiter_storage = Config.REDIS_URL or "memory://"
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[],          # no global default — set per route
        storage_uri=_limiter_storage,
        strategy="fixed-window",
    )
    # Expose limiter for blueprints to import
    app.extensions["limiter"] = limiter

    # ── Register blueprints ────────────────────────────────────
    # url_prefix="" keeps all existing URL paths identical.
    from blueprints.auth.routes    import auth_bp
    from blueprints.chat.routes    import chat_bp
    from blueprints.weather.routes import weather_bp
    from blueprints.alerts.routes  import alerts_bp
    from blueprints.shelters.routes import shelters_bp
    from blueprints.maps.routes    import maps_bp

    for bp in (auth_bp, chat_bp, weather_bp, alerts_bp, shelters_bp, maps_bp):
        app.register_blueprint(bp)

    # ── Root route ────────────────────────────────────────────
    @app.route("/")
    def home():
        from flask import render_template
        return render_template(
            "index.html",
            google_client_id=Config.GOOGLE_CLIENT_ID or "",
            google_maps_key=Config.GOOGLE_MAPS_KEY or "",
            owm_key=Config.OPENWEATHER_API_KEY or "",
        )

    # ── Centralised JSON error handlers ───────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Too many requests — please try again later."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        _log.exception("Internal server error")
        # Never expose exception details in production
        return jsonify({"error": "Internal server error"}), 500

    # ── Pre-warm RSS cache on startup ─────────────────────────
    from services.external_apis import _do_rss_refresh
    threading.Thread(target=_do_rss_refresh, daemon=True).start()

    _log.info("RAKSHA app created — %d routes registered",
              len(list(app.url_map.iter_rules())))
    return app


# ── Direct run (development only) ────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(debug=not Config.IS_PRODUCTION, port=5000)
