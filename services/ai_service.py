"""
services/ai_service.py — Groq/LLM integration for RAKSHA.

ask_ai() is the single entry point for all AI responses.
build_ctx() assembles the live weather context string.
"""

from groq import Groq
from config import Config

_client = Groq(api_key=Config.GROQ_API_KEY)

SYSTEM = """You are RAKSHA — India's official AI disaster and weather assistant.

RULES (follow strictly):
1. LANGUAGE: Reply in the exact same language as the user. Tamil input → Tamil reply. Hindi input → Hindi reply. English → English. Never switch languages.

2. WEATHER (most important): When LIVE DATA is in this prompt, you MUST use it directly. Format weather replies like:
   🌤 [City] Weather Right Now:
   • Temperature: [temp]°C (feels like [feels]°C)
   • Humidity: [humidity]%
   • Wind: [wind] m/s
   • Condition: [desc]
   • Risk: [risk level]
   NEVER say "I don't have real-time data" or "I can't check" when LIVE DATA is present.

3. GENERAL: Answer all disaster safety, first aid, emergency, and general questions helpfully and directly.

4. HELPLINES: NDMA:1078 | Emergency:112 | Fire:101 | Ambulance:108 | Police:100

5. VOICE-FRIENDLY: Keep answers clear and direct. Avoid very long replies unless detailed info is needed.

6. No live data present → answer from knowledge, note it's not real-time.
"""


def build_ctx(weather: dict | None, risk: dict | None) -> str:
    """Assemble the live data context block injected into the system prompt."""
    parts = []
    if weather and "error" not in weather:
        parts.append(
            f"LIVE WEATHER: {weather['city']}, {weather['country']} | "
            f"{weather['temp']}°C (feels {weather['feels_like']}°C) | "
            f"Humidity:{weather['humidity']}% | Wind:{weather['wind_speed']}m/s | "
            f"Rain(1h):{weather['rain_1h']}mm | Visibility:{weather['visibility']/1000:.1f}km | "
            f"Condition:{weather['desc']}"
        )
    if risk:
        active = {k: v for k, v in risk["risks"].items() if v > 0}
        if active:
            parts.append(
                f"NDMA RISK ({risk['overall']}): "
                + " | ".join(f"{k}={v}/5" for k, v in active.items())
            )
    return "\n".join(parts)


def ask_ai(
    msg: str,
    weather: dict | None = None,
    risk: dict | None = None,
    history: list | None = None,
    username: str | None = None,
    lang: str = "English",
) -> str:
    """
    Call the Groq LLM with live weather context.

    Parameters
    ----------
    msg      : user message text
    weather  : parsed OWM weather dict (or None)
    risk     : compute_risk() output (or None)
    history  : last N chat turns [{role, content}, ...]
    username : display name for personalisation (never logged)
    lang     : language name (e.g. "Tamil")

    Returns
    -------
    str — the assistant reply
    """
    system = SYSTEM
    if username:
        system += f"\nUser's name: {username}."
    system += f"\nAlways respond in: {lang}."
    ctx = build_ctx(weather, risk)
    if ctx:
        system += f"\n\n--- LIVE DATA (use this to answer) ---\n{ctx}\n--- END LIVE DATA ---"

    msgs = list((history or [])[-6:])
    msgs.append({"role": "user", "content": msg})

    try:
        r = _client.chat.completions.create(
            model=Config.GROQ_MODEL,
            max_tokens=800,
            temperature=0.3,
            messages=[{"role": "system", "content": system}] + msgs,
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"[Groq ERROR] {e}")
        return f"⚠️ AI error: {str(e)}"
