"""
blueprints/chat/routes.py

Routes:
  POST /chat
"""

from flask import Blueprint, jsonify, request, session

from services.ai_service import ask_ai
from services.external_apis import get_weather_city, get_weather_coords
from services.risk_engine import compute_risk

chat_bp = Blueprint("chat", __name__)

# ── City name lookup lists ────────────────────────────────────
_INDIA_CITIES = [
    "chennai","mumbai","delhi","kolkata","hyderabad","bengaluru","bangalore",
    "ahmedabad","pune","jaipur","lucknow","kanpur","nagpur","indore","thane",
    "bhopal","visakhapatnam","vizag","patna","vadodara","ghaziabad","ludhiana",
    "agra","nashik","faridabad","meerut","rajkot","varanasi","srinagar","aurangabad",
    "amritsar","navi mumbai","allahabad","prayagraj","ranchi","howrah","coimbatore",
    "jabalpur","gwalior","vijayawada","jodhpur","madurai","raipur","kota","guwahati",
    "chandigarh","solapur","hubli","dharwad","bareilly","moradabad","mysuru","mysore",
    "gurgaon","gurugram","noida","thiruvananthapuram","trivandrum","kochi","cochin",
    "bhubaneswar","dehradun","shimla","manali","ooty","darjeeling","gangtok",
    "pondicherry","puducherry","mangalore","mangaluru","tiruchirappalli","trichy",
    "salem","tirunelveli","vellore","erode","tiruppur","dhanbad","bokaro",
    "jammu","leh","imphal","shillong","aizawl","kohima","itanagar","agartala",
    "port blair","daman","silvassa","panaji","goa",
]

_WEATHER_KWS = [
    "weather","rain","flood","cyclone","storm","temp","humid","wind","disaster","alert","risk",
    "safe","forecast","heat","fog","lightning","thunder","earthquake","landslide","drought",
    "cold","snow","hail","tsunami","fire","smoke","air","pollution","uv","sunrise","sunset",
    "climate","season","monsoon","cloud","pressure","visibility","feels like","dew",
    # Indian languages
    "வானிலை","மழை","வெள்ளம்","புயல்","வெப்பம்","காற்று","மேகம்",
    "मौसम","बारिश","बाढ़","तूफान","गर्मी","ठंड","धुंध","भूकंप",
    "వాతావరణం","వరద","కాలావస్థ","వర్షం","గాలి","వేడి",
    "ಹವಾಮಾನ","ಮಳೆ","ಪ್ರವಾಹ","ಗಾಳಿ","ಬಿಸಿಲು",
    "കാലാവസ്ഥ","മഴ","വെള്ളപ്പൊക്കം","കാറ്റ്","ചൂട്",
    "আবহাওয়া","বন্যা","বৃষ্টি","ঝড়",
    "ਹੜ੍ਹ","ਹਨੇਰੀ","ਮੌਸਮ","ਮੀਂਹ",
]

_PREPS = {
    "in","at","for","of","near","around","about",
    "இல்","இல","la","le","में","के","लिए","లో","కి","ൽ","ಲ್ಲಿ","এ","ਵਿੱਚ",
}

_NON_CITIES = {
    "me","my","us","here","there","now","today","tomorrow","this","that","the",
}


def _extract_city(lower_msg: str) -> str | None:
    """Try to extract a city name from the user message text."""
    words = lower_msg.split()
    # Preposition + next word heuristic
    for i, w in enumerate(words):
        if w in _PREPS and i + 1 < len(words):
            candidate = " ".join(words[i + 1:]).strip("?.,!").title()
            if candidate.lower() not in _NON_CITIES and len(candidate) > 1:
                return candidate
    # Known Indian city list
    for c in _INDIA_CITIES:
        if c in lower_msg:
            return c.title()
    return None


@chat_bp.route("/chat", methods=["POST"])
def chat():
    if "email" not in session:
        return jsonify({"reply": "⚠️ Please log in."}), 401

    d         = request.json or {}
    msg       = d.get("message", "").strip()
    lat       = d.get("lat")
    lon       = d.get("lon")
    history   = d.get("history", [])
    sent_city = d.get("city", "").strip()

    if not msg:
        return jsonify({"reply": "⚠️ Empty."})
    if len(msg) > 800:
        return jsonify({"reply": "⚠️ Too long."})

    lower = msg.lower()
    needs_w = any(k in lower for k in _WEATHER_KWS) or bool(lat) or bool(sent_city)

    weather, risk = None, None
    if needs_w:
        if lat and lon:
            weather = get_weather_coords(lat, lon)
        elif sent_city:
            weather = get_weather_city(sent_city)
        else:
            city = _extract_city(lower) or "Chennai"
            weather = get_weather_city(city)

        if weather and "error" not in weather:
            risk = compute_risk(weather)

    lang  = session.get("lang", "English")
    reply = ask_ai(
        msg,
        weather=weather,
        risk=risk,
        history=history,
        username=session.get("name"),
        lang=lang,
    )
    return jsonify({"reply": reply, "weather": weather, "risk": risk})
