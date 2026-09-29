"""
config.py — Central configuration for RAKSHA.

Loads all required secrets from environment variables.
- In production (FLASK_ENV=production): missing required var → startup error.
- In development: missing var → warning, app continues with empty value.

Never commit real values here. Use .env locally, Render dashboard in production.
"""

import os

# ── Environment detection ──────────────────────────────────────
_ENV = os.getenv("FLASK_ENV", "development").lower()
IS_PRODUCTION = _ENV == "production"

# Required vars in production; warned in dev
_REQUIRED = [
    "SECRET_KEY",
    "GROQ_API_KEY",
    "OPENWEATHER_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
]

# Optional in both envs (feature degrades gracefully when absent)
_OPTIONAL = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_MAPS_KEY",
    "ORS_API_KEY",
    "REDIS_URL",
]


def _require(var: str) -> str:
    """Return env var value. Fail fast in production if missing."""
    value = os.getenv(var, "")
    if not value:
        if IS_PRODUCTION:
            raise RuntimeError(
                f"[RAKSHA] STARTUP ERROR: Required environment variable '{var}' is not set. "
                f"Set it in the Render dashboard (or .env locally) and redeploy."
            )
        else:
            print(
                f"[RAKSHA] WARNING: Environment variable '{var}' is not set. "
                f"Some features will not work. Add it to your .env file."
            )
    return value


def _optional(var: str, default: str = "") -> str:
    """Return env var value, or default. Never fails."""
    value = os.getenv(var, default)
    if not value and not default:
        pass  # silence — optional vars are expected to be absent sometimes
    return value


class Config:
    # ── Core Flask ─────────────────────────────────────────────
    SECRET_KEY: str = _require("SECRET_KEY")
    FLASK_ENV: str = _ENV

    # ── External APIs (required) ───────────────────────────────
    GROQ_API_KEY: str = _require("GROQ_API_KEY")
    # Support both OPENWEATHER_API_KEY (new canonical name) and legacy WEATHER_API_KEY
    OPENWEATHER_API_KEY: str = (
        os.getenv("OPENWEATHER_API_KEY")
        or os.getenv("WEATHER_API_KEY")
        or _require("OPENWEATHER_API_KEY")  # triggers fail/warn if both absent
    )

    # ── Supabase (required) ────────────────────────────────────
    SUPABASE_URL: str = _require("SUPABASE_URL")
    SUPABASE_KEY: str = _require("SUPABASE_KEY")

    # ── Optional / feature-flagged ─────────────────────────────
    GOOGLE_CLIENT_ID: str = _optional("GOOGLE_CLIENT_ID")
    GOOGLE_MAPS_KEY: str = _optional("GOOGLE_MAPS_KEY")
    ORS_API_KEY: str = _optional("ORS_API_KEY")
    REDIS_URL: str = _optional("REDIS_URL")

    # ── Model constants (not secrets) ─────────────────────────
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Rate-limit / cache tuning (not secrets) ───────────────
    RSS_TTL_SECONDS: int = 300
    GDACS_TTL_SECONDS: int = 600
    WEATHER_TTL_SECONDS: int = 600
    INDIA_RISK_TTL_SECONDS: int = 300
    SHELTERS_TTL_SECONDS: int = 3600
