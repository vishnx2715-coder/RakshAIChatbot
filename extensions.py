"""
extensions.py — Shared client singletons for RAKSHA.

Initialised once at startup; imported by services and blueprints.
Services never import blueprints to avoid circular imports.
"""

import os
from config import Config

# ── Supabase ──────────────────────────────────────────────────
supabase = None
USE_SUPABASE = False

try:
    from supabase import create_client
    if Config.SUPABASE_URL and Config.SUPABASE_KEY:
        if Config.SUPABASE_KEY.startswith("sb_secret_"):
            print(
                "⚠️  SUPABASE_KEY looks like a Management API key (sb_secret_...). "
                "Use the project 'anon' or 'service_role' key from Supabase → Settings → API."
            )
        else:
            try:
                supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                USE_SUPABASE = True
                print("✅ Supabase connected.")
            except Exception as e:
                print(f"⚠️  Supabase failed ({e}) — using users.json")
    else:
        print("ℹ️  No Supabase creds — using local users.json")
except ImportError:
    print("ℹ️  supabase package not installed — using local users.json")

# ── Redis (Phase 6) ───────────────────────────────────────────
# Imported lazily in cache_service.py so missing redis package
# does not break startup.
