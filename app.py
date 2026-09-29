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

from flask import Flask
from config import Config

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Suppress noisy third-party loggers
logging.getLogger("supabase").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def create_app() -> Flask:
    """Application factory — called by Gunicorn and tests."""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

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
        return {"error": "Bad request", "detail": str(e)}, 400

    @app.errorhandler(401)
    def unauthorized(e):
        return {"error": "Unauthorized"}, 401

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(e):
        logging.getLogger(__name__).exception("Internal server error")
        return {"error": "Internal server error"}, 500

    # ── Pre-warm RSS cache on startup ─────────────────────────
    from services.external_apis import _do_rss_refresh
    threading.Thread(target=_do_rss_refresh, daemon=True).start()

    logging.getLogger(__name__).info("RAKSHA app created — %d routes registered",
                                     len(list(app.url_map.iter_rules())))
    return app


# ── Direct run (development only) ────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
