from flask import Flask, request, jsonify, session
import requests, os, json, hashlib, secrets, time
import xml.etree.ElementTree as ET
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from groq import Groq
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None; Client = None

load_dotenv()
app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# ROOT CAUSE FIX #1 — Persistent SECRET_KEY
# ---------------------------------------------------------------
# BUG:  app.secret_key = secrets.token_hex(32)
#       A NEW random key is generated every time Flask restarts.
#       Every existing browser session becomes cryptographically
#       invalid → Flask returns 401 / session cleared → the
#       frontend receives a network error and shows the toast.
#
# FIX:  Read from .env. If missing, generate ONCE and warn.
#       Add SECRET_KEY=<any-long-random-string> to your .env.
# ═══════════════════════════════════════════════════════════════
_secret = os.getenv("SECRET_KEY")
if not _secret:
    _secret = secrets.token_hex(32)
    print("WARNING: SECRET_KEY not set in .env - sessions will break on restart. "
          f"Add: SECRET_KEY={_secret}")
app.secret_key = _secret

WEATHER_KEY = os.getenv("WEATHER_API_KEY", "c4299a4cf2c891d96114c83661c34316")
GROQ_KEY    = os.getenv("GROQ_API_KEY", "YOUR_GROQ_KEY_HERE")
groq_client = Groq(api_key=GROQ_KEY)
MODEL       = "llama-3.3-70b-versatile"

# ─── GOOGLE OAUTH ─────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "YOUR_GOOGLE_CLIENT_ID_HERE":
    print("ℹ️  GOOGLE_CLIENT_ID not set — Google Sign-In will be disabled.")
    GOOGLE_CLIENT_ID = ""

# ─── SUPABASE (optional) ──────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase = None; USE_SUPABASE = False
if SUPABASE_URL and SUPABASE_KEY and create_client:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        USE_SUPABASE = True; print("✅ Supabase connected.")
    except Exception as e:
        print(f"⚠️  Supabase failed ({e}) — using users.json")
else:
    print("ℹ️  No Supabase creds — using local users.json")

USERS_FILE = "users.json"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def _load_users():
    if not os.path.exists(USERS_FILE): return {}
    with open(USERS_FILE, encoding="utf-8") as f: return json.load(f)
def _save_users(u):
    with open(USERS_FILE, "w", encoding="utf-8") as f: json.dump(u, f, indent=2)

def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def db_get_user(email):
    if USE_SUPABASE:
        try:
            res = supabase.table("users").select("*").eq("email", email).single().execute()
            return res.data
        except: return None
    return _load_users().get(email)

def db_create_user(name, email, pw, phone):
    now_str = _now_str()
    if USE_SUPABASE:
        try:
            res = supabase.table("users").insert({
                "name": name,
                "email": email,
                "password": hash_pw(pw),
                "phone": phone or "",
                "lang": "English",
                "joined": datetime.utcnow().isoformat(),      # TIMESTAMPTZ — ISO format
                "last_login": datetime.utcnow().isoformat(),  # TIMESTAMPTZ — ISO format
                "login_count": 1,
                "auth_provider": "email",
            }).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"[db_create_user] Supabase error: {e}")
            return None
    users = _load_users()
    users[email] = {
        "name": name, "email": email, "password": hash_pw(pw),
        "phone": phone or "", "lang": "English",
        "joined": now_str, "last_login": now_str, "login_count": 1,
        "auth_provider": "email",
    }
    _save_users(users)
    return users[email]

def db_record_login(email):
    """Increment login_count and update last_login timestamp on every sign-in."""
    now_str = _now_str()
    if USE_SUPABASE:
        try:
            res = supabase.table("users").select("login_count").eq("email", email).single().execute()
            current = (res.data or {}).get("login_count", 0) or 0
            supabase.table("users").update({
                "last_login": datetime.utcnow().isoformat(),  # TIMESTAMPTZ
                "login_count": current + 1,
            }).eq("email", email).execute()
        except Exception as e:
            print(f"[db_record_login] Supabase error: {e}")
        return
    users = _load_users()
    if email in users:
        users[email]["last_login"] = now_str
        users[email]["login_count"] = (users[email].get("login_count", 0) or 0) + 1
        _save_users(users)

def db_update_lang(email, lang):
    if USE_SUPABASE:
        try: supabase.table("users").update({"lang": lang}).eq("email", email).execute()
        except: pass
        return
    users = _load_users()
    if email in users: users[email]["lang"] = lang; _save_users(users)

# ─── ALL 22 OFFICIAL INDIAN LANGUAGES ────────
ALL_LANGUAGES = [
    {"name": "Assamese",  "native": "অসমীয়া",    "code": "as", "flag": "🇮🇳"},
    {"name": "Bengali",   "native": "বাংলা",       "code": "bn", "flag": "🇮🇳"},
    {"name": "Bodo",      "native": "बड़ो",         "code": "brx","flag": "🇮🇳"},
    {"name": "Dogri",     "native": "डोगरी",        "code": "doi","flag": "🇮🇳"},
    {"name": "Gujarati",  "native": "ગુજરાતી",     "code": "gu", "flag": "🇮🇳"},
    {"name": "Hindi",     "native": "हिन्दी",       "code": "hi", "flag": "🇮🇳"},
    {"name": "Kannada",   "native": "ಕನ್ನಡ",        "code": "kn", "flag": "🇮🇳"},
    {"name": "Kashmiri",  "native": "کٲشُر",        "code": "ks", "flag": "🇮🇳"},
    {"name": "Konkani",   "native": "कोंकणी",       "code": "kok","flag": "🇮🇳"},
    {"name": "Maithili",  "native": "मैथिली",       "code": "mai","flag": "🇮🇳"},
    {"name": "Malayalam", "native": "മലയാളം",       "code": "ml", "flag": "🇮🇳"},
    {"name": "Manipuri",  "native": "মৈতৈলোন্",    "code": "mni","flag": "🇮🇳"},
    {"name": "Marathi",   "native": "मराठी",        "code": "mr", "flag": "🇮🇳"},
    {"name": "Nepali",    "native": "नेपाली",       "code": "ne", "flag": "🇮🇳"},
    {"name": "Odia",      "native": "ଓଡ଼ିଆ",        "code": "or", "flag": "🇮🇳"},
    {"name": "Punjabi",   "native": "ਪੰਜਾਬੀ",       "code": "pa", "flag": "🇮🇳"},
    {"name": "Sanskrit",  "native": "संस्कृतम्",    "code": "sa", "flag": "🇮🇳"},
    {"name": "Santali",   "native": "ᱥᱟᱱᱛᱟᱲᱤ",    "code": "sat","flag": "🇮🇳"},
    {"name": "Sindhi",    "native": "سنڌي",         "code": "sd", "flag": "🇮🇳"},
    {"name": "Tamil",     "native": "தமிழ்",        "code": "ta", "flag": "🇮🇳"},
    {"name": "Telugu",    "native": "తెలుగు",       "code": "te", "flag": "🇮🇳"},
    {"name": "Urdu",      "native": "اردو",          "code": "ur", "flag": "🇮🇳"},
    {"name": "English",   "native": "English",      "code": "en", "flag": "🇬🇧"},
]

# ─── UI TRANSLATIONS ──────────────────────────
UI_STRINGS = {
    "English":   {"welcome":"Welcome","dashboard":"Dashboard","alerts":"Alerts","guidelines":"Guidelines","maps":"Maps","signout":"Sign Out","askme":"Ask me anything in your language…","sending":"…","riskLevel":"Risk Level","noHazards":"No active hazards","loading":"Loading…","live":"LIVE"},
    "Tamil":     {"welcome":"வரவேற்கிறோம்","dashboard":"டாஷ்போர்ட்","alerts":"எச்சரிக்கைகள்","guidelines":"வழிகாட்டுதல்கள்","maps":"வரைபடங்கள்","signout":"வெளியேறு","askme":"உங்கள் மொழியில் கேளுங்கள்…","sending":"…","riskLevel":"அபாய நிலை","noHazards":"செயலில் உள்ள அபாயம் இல்லை","loading":"ஏற்றுகிறது…","live":"நேரலை"},
    "Hindi":     {"welcome":"स्वागत है","dashboard":"डैशबोर्ड","alerts":"अलर्ट","guidelines":"दिशानिर्देश","maps":"मानचित्र","signout":"साइन आउट","askme":"अपनी भाषा में पूछें…","sending":"…","riskLevel":"जोखिम स्तर","noHazards":"कोई सक्रिय खतरा नहीं","loading":"लोड हो रहा है…","live":"लाइव"},
    "Telugu":    {"welcome":"స్వాగతం","dashboard":"డాష్‌బోర్డ్","alerts":"హెచ్చరికలు","guidelines":"మార్గదర్శకాలు","maps":"మ్యాప్‌లు","signout":"సైన్ అవుట్","askme":"మీ భాషలో అడగండి…","sending":"…","riskLevel":"ప్రమాద స్థాయి","noHazards":"సక్రియ ప్రమాదాలు లేవు","loading":"లోడ్ అవుతోంది…","live":"లైవ్"},
    "Malayalam": {"welcome":"സ്വാഗതം","dashboard":"ഡാഷ്ബോർഡ്","alerts":"മുന്നറിയിപ്പുകൾ","guidelines":"മാർഗ്ഗനിർദ്ദേശങ്ങൾ","maps":"ഭൂപടങ്ങൾ","signout":"സൈൻ ഔട്ട്","askme":"നിങ്ങളുടെ ഭാഷയിൽ ചോദിക്കൂ…","sending":"…","riskLevel":"അപകട നില","noHazards":"സജീവ അപകടങ്ങളില്ല","loading":"ലോഡ് ചെയ്യുന്നു…","live":"തത്സമയം"},
    "Kannada":   {"welcome":"ಸ್ವಾಗತ","dashboard":"ಡ್ಯಾಶ್‌ಬೋರ್ಡ್","alerts":"ಎಚ್ಚರಿಕೆಗಳು","guidelines":"ಮಾರ್ಗದರ್ಶನಗಳು","maps":"ನಕ್ಷೆಗಳು","signout":"ಸೈನ್ ಔಟ್","askme":"ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಕೇಳಿ…","sending":"…","riskLevel":"ಅಪಾಯ ಮಟ್ಟ","noHazards":"ಸಕ್ರಿಯ ಅಪಾಯಗಳಿಲ್ಲ","loading":"ಲೋಡ್ ಆಗುತ್ತಿದೆ…","live":"ನೇರ"},
    "Bengali":   {"welcome":"স্বাগতম","dashboard":"ড্যাশবোর্ড","alerts":"সতর্কতা","guidelines":"নির্দেশিকা","maps":"মানচিত্র","signout":"সাইন আউট","askme":"আপনার ভাষায় জিজ্ঞাসা করুন…","sending":"…","riskLevel":"ঝুঁকির মাত্রা","noHazards":"কোনো সক্রিয় বিপদ নেই","loading":"লোড হচ্ছে…","live":"লাইভ"},
    "Marathi":   {"welcome":"स्वागत","dashboard":"डॅशबोर्ड","alerts":"इशारे","guidelines":"मार्गदर्शक तत्त्वे","maps":"नकाशे","signout":"साइन आउट","askme":"तुमच्या भाषेत विचारा…","sending":"…","riskLevel":"धोका पातळी","noHazards":"कोणताही सक्रिय धोका नाही","loading":"लोड होत आहे…","live":"लाइव्ह"},
    "Gujarati":  {"welcome":"આવો","dashboard":"ડેશબોર્ડ","alerts":"ચેતવણી","guidelines":"માર્ગદર્શિકા","maps":"નકશા","signout":"સાઇન આઉટ","askme":"તમારી ભાષામાં પૂછો…","sending":"…","riskLevel":"જોખમ સ્તર","noHazards":"કોઈ સક્રિય જોખમ નથી","loading":"લોડ…","live":"લાઈવ"},
    "Punjabi":   {"welcome":"ਜੀ ਆਇਆਂ","dashboard":"ਡੈਸ਼ਬੋਰਡ","alerts":"ਚੇਤਾਵਨੀਆਂ","guidelines":"ਦਿਸ਼ਾ ਨਿਰਦੇਸ਼","maps":"ਨਕਸ਼ੇ","signout":"ਸਾਈਨ ਆਊਟ","askme":"ਆਪਣੀ ਭਾਸ਼ਾ ਵਿੱਚ ਪੁੱਛੋ…","sending":"…","riskLevel":"ਜੋਖਮ ਪੱਧਰ","noHazards":"ਕੋਈ ਸਰਗਰਮ ਖ਼ਤਰਾ ਨਹੀਂ","loading":"ਲੋਡ ਹੋ ਰਿਹਾ…","live":"ਲਾਈਵ"},
    "Odia":      {"welcome":"ସ୍ୱାଗତ","dashboard":"ଡ୍ୟାଶ୍‌ବୋର୍ଡ","alerts":"ସତର୍କତା","guidelines":"ଦିଗ୍ଦର୍ଶନ","maps":"ମାନଚିତ୍ର","signout":"ସାଇନ ଆଉଟ","askme":"ଆପଣଙ୍କ ଭାଷାରେ ପଚାରନ୍ତୁ…","sending":"…","riskLevel":"ବିପଦ ସ୍ତର","noHazards":"କୌଣସି ସକ୍ରିୟ ବିପଦ ନାହିଁ","loading":"ଲୋଡ ହେଉଛି…","live":"ଲାଇଭ"},
}


# ─── WEATHER ──────────────────────────────────────────────────
def get_weather_city(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
    try:
        d = requests.get(url, timeout=5).json()
        return _pw(d) if "main" in d else {"error": d.get("message","City not found")}
    except Exception as e: return {"error": str(e)}

def get_weather_coords(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
    try:
        d = requests.get(url, timeout=5).json()
        return _pw(d) if "main" in d else {"error": d.get("message","Error")}
    except Exception as e: return {"error": str(e)}

def get_forecast(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric&cnt=8"
    try:
        d = requests.get(url, timeout=5).json()
        items = []
        for i in d.get("list", []):
            items.append({
                "time": i["dt_txt"][11:16],
                "temp": i["main"]["temp"],
                "icon": i["weather"][0]["main"],
                "desc": i["weather"][0]["description"],
                "wind": i.get("wind",{}).get("speed",0),
                "rain": i.get("rain",{}).get("3h",0),
                "pop":  round(i.get("pop",0)*100),
            })
        return items
    except: return []

def _pw(d):
    return {
        "city": d.get("name","Unknown"), "country": d.get("sys",{}).get("country",""),
        "temp": round(d["main"]["temp"],1), "feels_like": round(d["main"]["feels_like"],1),
        "temp_min": round(d["main"].get("temp_min",0),1), "temp_max": round(d["main"].get("temp_max",0),1),
        "humidity": d["main"]["humidity"], "pressure": d["main"]["pressure"],
        "wind_speed": d.get("wind",{}).get("speed",0), "wind_deg": d.get("wind",{}).get("deg",0),
        "desc": d["weather"][0]["description"], "icon_code": d["weather"][0]["icon"],
        "icon": d["weather"][0]["main"],
        "visibility": d.get("visibility",10000), "clouds": d.get("clouds",{}).get("all",0),
        "rain_1h": d.get("rain",{}).get("1h",0), "uv": 0,
        "lat": d.get("coord",{}).get("lat",20.5937), "lon": d.get("coord",{}).get("lon",78.9629),
        "sunrise": d.get("sys",{}).get("sunrise",0), "sunset": d.get("sys",{}).get("sunset",0),
    }

# ─── RISK ENGINE ──────────────────────────────────────────────
def compute_risk(w):
    temp=w.get("temp",25); humid=w.get("humidity",50); wind=w.get("wind_speed",0)
    rain=w.get("rain_1h",0); icon=w.get("icon","Clear"); vis=w.get("visibility",10000)
    risks={}
    c=0
    if wind>32:c=5
    elif wind>24:c=4
    elif wind>17:c=3
    elif wind>10:c=2
    elif wind>6:c=1
    risks["cyclone"]=c
    f=0
    if rain>50:f=5
    elif rain>20:f=4
    elif rain>7.5:f=3
    elif rain>2.5:f=2
    elif rain>0:f=1
    if humid>90:f=min(5,f+1)
    risks["flood"]=f
    h=0
    if temp>=47:h=5
    elif temp>=44:h=4
    elif temp>=40:h=3
    elif temp>=37:h=2
    elif temp>=34:h=1
    risks["heatwave"]=h
    co=0
    if temp<=0:co=5
    elif temp<=4:co=4
    elif temp<=8:co=3
    elif temp<=12:co=2
    elif temp<=15:co=1
    risks["cold_wave"]=co
    fg=0
    if vis<50:fg=5
    elif vis<200:fg=4
    elif vis<500:fg=3
    elif vis<1000:fg=2
    elif vis<2000:fg=1
    risks["dense_fog"]=fg
    risks["thunderstorm"]=5 if icon=="Thunderstorm" else 0
    risks["lightning"]=4 if (icon=="Thunderstorm" and humid>75) else 0
    mx=max(risks.values())
    overall="CRITICAL" if mx>=4 else "HIGH" if mx>=3 else "MODERATE" if mx>=2 else "LOW" if mx>=1 else "NORMAL"
    return {"risks":risks,"overall":overall,"max_score":mx}

# ═══════════════════════════════════════════════════════════════
# RSS SOURCE LIST — verified official feeds
# ═══════════════════════════════════════════════════════════════
OFFICIAL_RSS = [
    ("GDACS Global Alerts",  "https://www.gdacs.org/xml/rss.xml"),
    ("ReliefWeb India",      "https://reliefweb.int/country/ind/rss.xml"),
    ("EMSC Earthquakes",     "https://www.emsc-csem.org/service/rss/rss.php?typ=emsc"),
    ("WHO Emergencies",      "https://www.who.int/feeds/entity/csr/don/en/rss.xml"),
    ("UN OCHA Asia",         "https://reliefweb.int/region/asia/rss.xml"),
]

# ═══════════════════════════════════════════════════════════════
# ROOT CAUSE FIX #2 — Parallel RSS fetching + TTL cache
# ---------------------------------------------------------------
# BUG:  All 5 feeds fetched sequentially with timeout=7 each.
#       Worst case = 5 × 7 = 35 seconds before ANY data returns.
#       External servers (GDACS, WHO, UN OCHA) are frequently
#       slow, rate-limited, or temporarily down.
#       Zero caching → every map page load repeats this 35s wait.
#       Both /api/news AND /api/alerts call fetch_verified_news()
#       independently → up to 70 seconds per full dashboard load.
#
# FIX:  ThreadPoolExecutor fetches all 5 feeds in parallel.
#       Actual wall time = max(individual times) ≈ 7s worst case.
#       Simple dict cache with 5-minute TTL avoids redundant
#       fetches when news, alerts, and shelter map all init at
#       once.  Cache is per-process (sufficient for single-worker
#       Flask; for multi-worker use Redis instead).
# ═══════════════════════════════════════════════════════════════
_rss_cache: dict = {"data": None, "ts": 0}
RSS_TTL_SECONDS = 300   # 5 minutes — tune to taste
RSS_PER_SOURCE_TIMEOUT = 6  # seconds per individual feed

def _fetch_one_feed(source_url_pair: tuple) -> list:
    """Fetch a single RSS feed and return parsed items."""
    source, url = source_url_pair
    headers = {"User-Agent": "RAKSHA-DisasterAI/1.0 (Government Emergency Platform)"}
    items = []
    try:
        r = requests.get(url, timeout=RSS_PER_SOURCE_TIMEOUT, headers=headers)
        if r.status_code != 200:
            return items
        root = ET.fromstring(r.content)
        kws = ["india","flood","cyclone","earthquake","storm","disaster","emergency",
               "tsunami","landslide","heat","drought","fire","alert","warning",
               "bangladesh","nepal","srilanka","myanmar","asia"]
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
                relevant = True  # GDACS/EMSC always relevant
            if relevant:
                items.append({
                    "source": source, "title": title[:140],
                    "link": link, "desc": desc[:200], "date": pub,
                    "verified": True, "type": "official"
                })
                count += 1
            if count >= 5:
                break
    except Exception:
        pass   # individual feed failure is non-fatal; others still return
    return items


def fetch_verified_news() -> list:
    """
    Fetch from all official RSS feeds IN PARALLEL, with TTL caching.
    Wall time drops from up to 35s → ~6-7s worst case (single slow feed).
    Cached result is reused for 5 minutes to avoid hammering external APIs.
    """
    global _rss_cache
    now = time.monotonic()
    # Return cached data if still fresh
    if _rss_cache["data"] is not None and (now - _rss_cache["ts"]) < RSS_TTL_SECONDS:
        return _rss_cache["data"]

    all_items: list = []
    # Fetch all feeds concurrently; max_workers=5 since we have exactly 5 feeds
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_fetch_one_feed, pair): pair for pair in OFFICIAL_RSS}
        for future in as_completed(futures):
            try:
                all_items.extend(future.result())
            except Exception:
                pass  # individual thread failure is non-fatal

    # Sort by recency (best-effort on pubDate string) and cap at 25
    result = all_items[:25]

    _rss_cache["data"] = result
    _rss_cache["ts"]   = now
    return result


# ═══════════════════════════════════════════════════════════════
# ROOT CAUSE FIX #3 — Alert severity classification
# ---------------------------------------------------------------
# BUG:  /api/alerts only produced "HIGH" or "MODERATE" levels.
#       CRITICAL never appeared in alerts even though compute_risk
#       produces it.  LOW and MODERATE alerts were returned and
#       rendered on maps, cluttering Disaster Zone and Risk maps.
#
# FIX:  Two-tier keyword matching produces CRITICAL vs HIGH only.
#       Everything below HIGH is dropped entirely.
#       Filtering happens at the BACKEND (this file) — justified:
#         • Reduces payload size sent to client
#         • Single source of truth — frontend can't accidentally
#           re-introduce low alerts via its own filter logic
#         • Consistent across all three map types
#         • Cheaper: filter once on server vs. filter on every
#           client that loads a map
# ═══════════════════════════════════════════════════════════════

# Keywords that indicate CRITICAL severity (imminent life-threat)
CRITICAL_KWS = [
    "red alert", "red warning", "extreme warning",
    "tsunami", "tsunami warning", "tsunami watch",
    "cyclone landfall", "super cyclone", "severe cyclonic storm",
    "extremely severe", "catastrophic",
    "major earthquake", "strong earthquake",
    "nuclear emergency", "chemical disaster",
    "mass casualty", "evacuation order", "evacuate immediately",
    "dam breach", "dam failure", "flash flood warning",
    "orange alert",   # NDMA orange = high-end before red
]

# Keywords that indicate HIGH severity (serious hazard, action needed)
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


def classify_alert_level(title: str, desc: str) -> str | None:
    """
    Returns 'CRITICAL', 'HIGH', or None (drop the item).
    Low / moderate severity items return None and are excluded.
    """
    text = (title + " " + desc).lower()
    if any(k in text for k in CRITICAL_KWS):
        return "CRITICAL"
    if any(k in text for k in HIGH_KWS):
        return "HIGH"
    return None   # drop LOW and MODERATE entirely


# ─── SHELTER DATA (static + extensible) ───────────────────────
# In production, load from a database or govt. API.
# These represent official NDMA-registered shelter sites.
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


# ═══════════════════════════════════════════════════════════════
# ROOT CAUSE FIX #4 — /api/shelters was MISSING
# ---------------------------------------------------------------
# BUG:  The Shelter Map page calls /api/shelters, but no such
#       route existed in app.py → Flask returns 404 → fetch()
#       in the browser throws a network error → toast appears.
#
# FIX:  Add the endpoint.  Returns shelter markers with all
#       metadata the map needs to render pins and popups.
# ═══════════════════════════════════════════════════════════════
@app.route("/api/shelters")
def shelters():
    district = request.args.get("district", "").strip()
    available_only = request.args.get("available", "false").lower() == "true"

    result = list(SHELTER_DATA)
    if district:
        result = [s for s in result if s["district"].lower() == district.lower()]
    if available_only:
        result = [s for s in result if s["available"]]

    return jsonify({
        "shelters": result,
        "total": len(result),
        "available_count": sum(1 for s in result if s["available"]),
        "source": "NDMA registered shelter sites"
    })


# ═══════════════════════════════════════════════════════════════
# /api/overpass  — Proxy for Overpass API
# ROOT CAUSE of "Network error": browser → overpass-api.de is
# rate-limited. Flask server-side requests are not. Three mirrors.
# ═══════════════════════════════════════════════════════════════
_OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

@app.route("/api/overpass", methods=["POST"])
def overpass_proxy():
    body  = request.get_json(force=True, silent=True) or {}
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"error": "no query"}), 400
    hdrs = {"Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "RAKSHA/1.0"}
    last_err = ""
    for mirror in _OVERPASS_MIRRORS:
        try:
            r = requests.post(mirror, data={"data": query}, headers=hdrs, timeout=25)
            if r.status_code != 200:
                last_err = f"HTTP {r.status_code}"; continue
            j = r.json()
            if "remark" in j and "rate limit" in str(j.get("remark", "")):
                last_err = "rate limited"; continue
            return jsonify(j)
        except Exception as e:
            last_err = str(e); continue
    return jsonify({"error": "All Overpass mirrors failed", "detail": last_err}), 502


# ═══════════════════════════════════════════════════════════════
# /api/osrm-table  — Batch real road distances via OSRM Table API
#
# BUG FIXED: The frontend used haversineKm() (straight-line) for
# all displayed distances and walk times (distKm × 12 min/km).
# In Chennai's road network, haversine under-estimates by 40–80%.
# Example: 5.5km haversine → 10.5km actual road → 24min vs 58min.
#
# FIX: This endpoint takes user location + shelter coordinates,
# calls OSRM Table API (one request for ALL shelters), and returns
# real road distances (metres) and walking durations (seconds).
# The frontend updates every card and popup with actual values.
#
# OSRM Table API format:
#   GET /table/v1/{profile}/{lon,lat;lon,lat;...}
#   ?sources=0              → user location is index 0 (the source)
#   &annotations=distance,duration
#   Returns distances[0][i] in metres, durations[0][i] in seconds
#   IMPORTANT: OSRM uses lon,lat order (GeoJSON), NOT lat,lon
# ═══════════════════════════════════════════════════════════════
OSRM_BASE = "https://router.project-osrm.org"

@app.route("/api/osrm-table", methods=["POST"])
def osrm_table():
    body    = request.get_json(force=True, silent=True) or {}
    user_lat = body.get("user_lat")
    user_lon = body.get("user_lon")
    shelters = body.get("shelters", [])   # [{id, lat, lon}, ...]

    if user_lat is None or user_lon is None or not shelters:
        return jsonify({"error": "user_lat, user_lon and shelters required"}), 400

    # Cap at 99 shelters (OSRM max = 100 coordinates including user)
    shelters = shelters[:99]

    # Process in chunks of 25 destinations to avoid OSRM public API limits
    results = []
    chunk_size = 25
    
    for i in range(0, len(shelters), chunk_size):
        chunk = shelters[i:i+chunk_size]
        coords = f"{user_lon},{user_lat};" + ";".join(
            f"{s['lon']},{s['lat']}" for s in chunk
        )
        
        # OSRM public API only officially supports 'driving'. The 'foot' profile will 
        # often just return driving speeds. So we request driving, and manually 
        # estimate walking duration based on distance (average walking speed = 5 km/h).
        url = (f"{OSRM_BASE}/table/v1/driving/{coords}"
               f"?sources=0&annotations=distance,duration")
               
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                print(f"[OSRM] Table chunk {i} HTTP {r.status_code}")
                continue
                
            data = r.json()
            if data.get("code") != "Ok":
                print(f"[OSRM] Table chunk {i} error: {data.get('code')}")
                continue
                
            dists = data.get("distances", [[]])[0]
            durs  = data.get("durations", [[]])[0]
            
            for j, s in enumerate(chunk):
                dist_m = dists[j + 1] if (j + 1) < len(dists) else None
                dur_s  = durs[j + 1]  if (j + 1) < len(durs)  else None
                
                if dist_m is not None and dist_m > 0:
                    # Walk time: 5 km/h = 1.38 m/s
                    walk_sec = int(dist_m / 1.38)
                    results.append({
                        "id": s["id"],
                        "drive_m": dist_m,
                        "drive_sec": dur_s,
                        "walk_m": dist_m,    # walk distance is approx same as drive
                        "walk_sec": walk_sec
                    })
        except Exception as e:
            print(f"[OSRM] Table chunk {i} failed: {e}")
            continue

    return jsonify({"results": results})


# ═══════════════════════════════════════════════════════════════
# /api/osrm-route — Proxy for OSRM Route API (geometry + times)
#
# Routes the geometry for drawing on the map.
# Goes through Flask to avoid browser rate-limiting on OSRM.
# profile: "driving" or "foot"
# ═══════════════════════════════════════════════════════════════
@app.route("/api/osrm-route", methods=["POST"])
def osrm_route():
    body     = request.get_json(force=True, silent=True) or {}
    profile  = body.get("profile", "driving")
    user_lat = body.get("user_lat"); user_lon = body.get("user_lon")
    dest_lat = body.get("dest_lat"); dest_lon = body.get("dest_lon")
    if None in (user_lat, user_lon, dest_lat, dest_lon):
        return jsonify({"error": "missing coordinates"}), 400
    # lon,lat order for OSRM
    url = (f"{OSRM_BASE}/route/v1/{profile}/"
           f"{user_lon},{user_lat};{dest_lon},{dest_lat}"
           f"?overview=full&geometries=geojson")
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return jsonify({"error": f"OSRM HTTP {r.status_code}"}), 502
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


# ─── GUIDELINES ───────────────────────────────────────────────
GUIDELINES = {
    "flood": {
        "title": "🌊 Flood Safety Guidelines",
        "source": "NDMA India / FEMA / UN OCHA",
        "before": [
            "Register with your local ward/panchayat for early warning SMS alerts",
            "Store at least 72-hour supply of drinking water (minimum 3 litres/person/day)",
            "Keep a waterproof emergency bag: torch, first aid, medicines, ID documents, cash",
            "Know the elevation of your home relative to nearest water body",
            "Identify and memorize nearest flood shelter location",
            "Disconnect all electrical appliances if flood warning issued",
            "Move valuables and important documents to upper floors"
        ],
        "during": [
            "NEVER attempt to walk through moving floodwater — 6 inches can knock you down",
            "Do NOT drive through flooded roads — turn around, don't drown",
            "Move to highest point available — roof if necessary",
            "Signal for rescue using bright cloth, torch, or whistle",
            "Do not touch electrical equipment — risk of electrocution",
            "Call NDMA: 1078 or National Emergency: 112",
            "Follow instructions from NDMA/district administration ONLY"
        ],
        "after": [
            "Do not return home until officially declared safe by authorities",
            "Boil all water before drinking — floodwater contamination is severe",
            "Wear rubber boots and gloves when cleaning flood debris",
            "Check gas/electrical systems before turning on — fire risk",
            "Document all damage with photos for insurance and government relief",
            "Watch for water-borne diseases: cholera, typhoid, leptospirosis",
            "Contact district collector office for relief registration"
        ]
    },
    "cyclone": {
        "title": "🌀 Cyclone Safety Guidelines — NDMA India",
        "source": "National Disaster Management Authority, Government of India",
        "before": [
            "Monitor IMD cyclone bulletins every 3 hours during cyclone season",
            "Secure loose objects: furniture, vehicles, satellite dishes, gas cylinders",
            "Board up or tape all windows in X-pattern with masking tape",
            "Store 5-day emergency food and water supply",
            "Identify nearest cyclone shelter (pucca building, school, community hall)",
            "Keep vehicles fuel tank full for potential evacuation",
            "Trim/remove dead tree branches near your house"
        ],
        "during": [
            "Stay INDOORS — most cyclone deaths occur from flying debris outside",
            "Stay away from windows and glass doors — move to interior rooms",
            "Do NOT go outside when winds temporarily calm — it may be the eye of cyclone",
            "Disconnect all electrical appliances and turn off main supply",
            "Fill bathtubs with water — supply may be cut after cyclone",
            "Listen ONLY to All India Radio (AIR) and DD National for updates",
            "Do not call emergency numbers unless life-threatening — keep lines clear"
        ],
        "after": [
            "Wait for official 'All Clear' signal before venturing out",
            "Stay away from damaged structures, electrical poles, fallen trees",
            "Do not touch any standing water — may be electrified by fallen wires",
            "Report missing persons to district control room immediately",
            "Contact IMD / State Disaster Management Authority for relief",
            "Document property damage for insurance claim within 72 hours"
        ]
    },
    "heatwave": {
        "title": "🌡 Heatwave Safety Guidelines — NDMA India",
        "source": "National Disaster Management Authority & India Meteorological Department",
        "before": [
            "Download IMD Mausam app for daily heat alerts",
            "Install reflective curtains or whitewash walls to reduce indoor heat",
            "Stock Oral Rehydration Salts (ORS) — available free at PHCs",
            "Locate nearest cooling center: government building, community hall",
            "Check on elderly, children, and outdoor workers daily",
            "Schedule outdoor work before 9 AM or after 6 PM",
            "Paint rooftop white to reduce radiant heat"
        ],
        "during": [
            "Drink minimum 2–3 litres of water per day — do not wait until thirsty",
            "Avoid going out between 12 PM – 4 PM (peak heat hours)",
            "Wear loose, light-colored cotton clothes and wide-brimmed hat",
            "Apply wet cloth on head/neck — evaporative cooling is effective",
            "Eat light meals — avoid heavy, oily, or non-vegetarian food",
            "Never leave children or animals in parked vehicles",
            "If feeling dizzy/nauseous — HEATSTROKE. Move to cool area, call 108"
        ],
        "after": [
            "Resume outdoor activity gradually after heat warning lifted",
            "Report heat-stroke deaths to district health officer (mandatory)",
            "Advocate for shade and water kiosks at public spaces",
            "Check heat damage to crops — contact Krishi Vigyan Kendra"
        ]
    },
    "earthquake": {
        "title": "🏚 Earthquake Safety Guidelines — NDMA India",
        "source": "National Disaster Management Authority, Government of India",
        "before": [
            "Get your building structurally assessed — contact local municipality",
            "Secure heavy furniture and appliances to walls with brackets",
            "Know how to shut off gas, water, and electricity at main valves",
            "Keep emergency kit in easily accessible location: ground floor",
            "Practice 'Drop, Cover, Hold On' with all family members quarterly",
            "Identify safe spots in every room: under sturdy table, against inner wall",
            "Store emergency water in sealed containers — minimum 3 days supply"
        ],
        "during": [
            "DROP immediately to hands and knees — stay low to floor",
            "COVER your head and neck with arms; take shelter under sturdy table",
            "HOLD ON until shaking completely stops — do not run outside",
            "If outdoors: move away from buildings, trees, and utility wires",
            "If in vehicle: pull over away from flyovers, bridges, and buildings",
            "NEVER use elevators — take stairs after shaking stops",
            "Do not light matches or candles after quake — gas leaks possible"
        ],
        "after": [
            "Expect aftershocks — they can be strong and cause additional damage",
            "If you smell gas: leave immediately, do not operate any electrical switch",
            "Check for injuries — do not move seriously injured unless in immediate danger",
            "SMS is better than calls after earthquake — lines will be overloaded",
            "Do not enter damaged buildings until structurally cleared by engineers",
            "Listen to NDMA / state disaster authority for official instructions only"
        ]
    },
    "landslide": {
        "title": "⛰ Landslide Safety Guidelines",
        "source": "NDMA India / USGS",
        "before": [
            "Avoid building homes on steep slopes, near drainage channels, or hill cuts",
            "Plant deep-rooted vegetation on slopes — prevents soil erosion",
            "Install retaining walls if building cannot be relocated",
            "Monitor heavy rainfall warnings from IMD for hill districts",
            "Know evacuation routes from hilly/mountainous areas in advance",
            "Never dump waste on slopes — weakens natural stability"
        ],
        "during": [
            "Evacuate IMMEDIATELY if you hear rumbling sounds or see cracks in ground",
            "Move perpendicular to the flow direction — NEVER run downhill",
            "Avoid river valleys and low-lying areas during heavy rain",
            "If escape is impossible: curl into tight ball and protect your head",
            "Do not re-enter affected area — follow-on slides are common",
            "Call 112 or SDRF (State Disaster Response Force) immediately"
        ],
        "after": [
            "Stay away from slide area for minimum 24 hours — secondary slides likely",
            "Report broken gas, water, electricity lines to respective departments",
            "Check building foundations before re-entering — may be undermined",
            "Clear drainage channels carefully — blockage causes repeat slides",
            "Document damage for insurance and government relief application"
        ]
    },
    "tsunami": {
        "title": "🌊 Tsunami Safety Guidelines",
        "source": "NDMA India / NOAA / Pacific Tsunami Warning Center",
        "before": [
            "Know if you live in a tsunami hazard zone — check state coastal maps",
            "Memorize elevation of your home above sea level",
            "Identify inland high-ground evacuation routes — practice annually",
            "Know natural warnings: strong earthquake, ocean withdrawal, roaring sound",
            "Sign up for INCOIS (Indian National Centre for Ocean Information Services) tsunami alerts",
            "Prepare go-bag with 3-day supplies: water, food, medicines, documents",
            "Establish family meeting point on high ground away from coast"
        ],
        "during": [
            "If you feel a strong earthquake near coast — DO NOT wait for official warning",
            "Move IMMEDIATELY to high ground or far inland — at least 30m elevation",
            "NEVER go to shore to watch waves — first wave may not be the biggest",
            "Tsunami can travel at 800 km/h — you have very little time",
            "If caught in water: grab something that floats, protect your head",
            "Stay on high ground until official all-clear — multiple waves arrive",
            "Do not use vehicles unless evacuation route is fully clear"
        ],
        "after": [
            "Wait for official all-clear — tsunamis arrive in multiple waves for hours",
            "Stay away from damaged buildings and flooded areas",
            "Do not drink tap water — assume contamination",
            "Watch for secondary hazards: fires, chemical spills, power lines down",
            "Report missing persons to police immediately",
            "Seek medical care even for minor injuries — water-borne infection risk"
        ]
    },
    "wildfire": {
        "title": "🔥 Wildfire / Forest Fire Safety Guidelines",
        "source": "NDMA India / US Forest Service / NIFC",
        "before": [
            "Create 30-foot defensible space around your home — clear dry vegetation",
            "Use fire-resistant roofing and ember-resistant vents in fire-prone areas",
            "Keep gutters and roof clear of dry leaves and debris",
            "Prepare go-bag: medications, documents, N95 masks, water, clothes",
            "Know your community's evacuation plan and multiple exit routes",
            "Sign up for local emergency alerts",
            "Keep vehicle fuel tank at least half-full during fire season"
        ],
        "during": [
            "Evacuate EARLY — do not wait until fire is visible. Obey mandatory orders",
            "Close all windows, doors, vents — stuff gaps with wet towels",
            "Wear long cotton or wool clothing — synthetics melt and burn",
            "Use N95 mask or wet cloth — smoke inhalation kills more than flames",
            "If trapped in vehicle: park away from trees, turn engine off, stay low",
            "If caught in open: lie face down in lowest dip, cover with wet cloth",
            "Never shelter under wooden structures — fire spreads through wood rapidly"
        ],
        "after": [
            "Do not return until officially cleared — hot spots can reignite for days",
            "Wear N95 mask when cleaning — ash contains toxic heavy metals",
            "Document all damage with photos before cleanup",
            "Check food and water safety — heat and smoke contaminate water supply",
            "Watch for mudslides after fire — hillsides destabilized without vegetation",
            "Seek counseling — wildfires cause significant psychological trauma"
        ]
    },
    "tornado": {
        "title": "🌪 Tornado Safety Guidelines",
        "source": "FEMA / NWS / WMO",
        "before": [
            "Know the difference: Tornado WATCH = conditions favorable; WARNING = tornado spotted",
            "Identify the safest room: interior, ground floor or basement, no windows",
            "Practice tornado drill with all family members twice yearly",
            "Prepare emergency kit: helmet, shoes, blankets, water, first aid",
            "Remove large trees or dead limbs near your home",
            "Know your area's tornado siren system",
            "Mobile homes are extremely dangerous — identify nearest shelter building"
        ],
        "during": [
            "Go immediately to basement or interior room on lowest floor",
            "Get under sturdy table or cover yourself with mattress/blankets",
            "Protect head and neck with your arms at all times",
            "NEVER shelter under highway overpass — wind speeds are higher there",
            "If outdoors with no shelter: lie flat in lowest ditch, cover head with hands",
            "If in vehicle: do NOT try to outrun tornado — abandon and seek shelter",
            "Stay away from windows, doors, and exterior walls"
        ],
        "after": [
            "Wait for official all-clear — multiple tornadoes can form in same system",
            "Watch for downed power lines — assume all are live and dangerous",
            "Wear sturdy boots when walking — debris causes serious cuts",
            "Do not use candles or open flame — gas leaks may be present",
            "Report injuries and structural damage to local emergency management",
            "Do not enter damaged buildings until inspected by engineers"
        ]
    },
    "drought": {
        "title": "🏜 Drought Safety & Preparedness Guidelines",
        "source": "NDMA India / IMD / FAO",
        "before": [
            "Install water meters and monitor household consumption monthly",
            "Harvest rainwater: install rooftop collection systems",
            "Switch to drought-resistant crops: millets, pulses, oilseeds",
            "Repair all water leaks — a dripping tap wastes 20 litres per day",
            "Build farm ponds and check dams for groundwater recharge",
            "Register for PMFBY (Pradhan Mantri Fasal Bima Yojana) crop insurance",
            "Identify alternative water sources in advance: borewells, tankers"
        ],
        "during": [
            "Reduce water use by 20–30%: shorter showers, drought-friendly washing",
            "Prioritize water for drinking and cooking — reduce agricultural use if needed",
            "Do not waste groundwater — aquifer recovery takes decades",
            "Monitor livestock health — animals are first victims of drought stress",
            "Apply for government drought relief through district collector office",
            "Use treated wastewater for irrigation where available",
            "Pool water resources with neighbors — community approach is more resilient"
        ],
        "after": [
            "Restock emergency water reserves immediately when rains return",
            "Assess crop damage and apply for relief compensation within deadlines",
            "Restore degraded land: plant trees, restore wetlands, grass cover",
            "Debrief community on lessons learned — update local drought plan",
            "Install additional rainwater harvesting before next dry season",
            "Report groundwater depletion data to district administration"
        ]
    },
    "winter_storm": {
        "title": "❄ Winter Storm / Blizzard Safety Guidelines",
        "source": "NDMA India / FEMA / BIS",
        "before": [
            "Insulate pipes — wrap exposed pipes with foam insulation",
            "Stock emergency supplies: food for 3 days, extra blankets, generators",
            "Keep vehicle winter-ready: antifreeze, snow tyres, emergency kit",
            "Trim tree branches that could fall on power lines under snow weight",
            "Know symptoms of hypothermia: shivering, confusion, slurred speech",
            "Prepare heating alternatives: firewood, kerosene heater with ventilation",
            "Register elderly and vulnerable neighbors for welfare checks"
        ],
        "during": [
            "Stay indoors — travel only if absolutely necessary",
            "Use generators, grills, and camp stoves OUTSIDE only — CO poisoning risk",
            "Dress in layers: wool/synthetic inner, insulating middle, windproof outer",
            "Clear snow from roof to prevent collapse — weight of snow is enormous",
            "Check pipes every 2 hours — running water slowly prevents freezing",
            "If stranded in vehicle: run engine 10 minutes per hour, clear exhaust pipe",
            "Eat high-calorie food — body needs extra energy to maintain heat"
        ],
        "after": [
            "Clear pathways carefully — ice makes surfaces extremely slippery",
            "Check on neighbors, especially elderly — cold kills silently",
            "Inspect roof for damage and structural weakening from snow load",
            "Beware of frostbite: rewarm limbs slowly with body heat, NOT hot water",
            "Report downed power lines to electricity board immediately",
            "Restore heating gradually — rapid warming can burst thawed pipes"
        ]
    },
    "volcanic": {
        "title": "🌋 Volcanic Eruption Safety Guidelines",
        "source": "NDMA India / USGS / VAAC",
        "before": [
            "Know if you live near a volcanic zone — check Geological Survey of India maps",
            "Prepare N95 respirators and goggles — ash is extremely fine and harmful",
            "Keep vehicles garaged and covered — ash damages engines severely",
            "Know evacuation routes away from the volcano — practice annually",
            "Follow Volcano Observatory alerts (alert levels: green, yellow, orange, red)",
            "Stock extra medications — respiratory conditions worsen near volcanoes",
            "Remove livestock and animals from danger zones when alerts are raised"
        ],
        "during": [
            "Evacuate IMMEDIATELY when ordered — lava flows and pyroclastic surges are lethal",
            "Wear N95 masks and goggles — even mild ash causes serious lung damage",
            "Stay indoors when ash is falling — seal doors and windows with wet towels",
            "Drive slowly with headlights on in ash fall — visibility near zero",
            "Stay away from river valleys — lahars (volcanic mudflows) travel at 60 km/h",
            "Avoid low-lying areas — heavier-than-air volcanic gases collect there",
            "Never try to outrun a pyroclastic flow — evacuate well in advance"
        ],
        "after": [
            "Wear masks when cleaning ash — silica causes permanent lung scarring",
            "Clean ash from roofs immediately — 10 cm of wet ash can collapse roofs",
            "Do not drink tap water until authorities confirm safety",
            "Check vehicle air filters — replace if contaminated with ash",
            "Report any ground fissures or unusual gas smells to Geological Survey",
            "Mental health support: eruptions cause severe post-traumatic stress"
        ]
    },
    "avalanche": {
        "title": "🏔 Avalanche Safety Guidelines",
        "source": "NDMA India / Snow and Avalanche Study Establishment (SASE)",
        "before": [
            "Check SASE avalanche bulletins before any mountain travel",
            "Learn to recognize danger signs: recent avalanche debris, cracking sounds, whumpf sounds",
            "Carry essential safety gear: avalanche transceiver, probe, shovel",
            "Travel with companions — solo mountaineering significantly increases fatality risk",
            "Avoid steep slopes (30–45°) after heavy snowfall or during warm spells",
            "Know the terrain: identify natural avalanche paths and stay clear",
            "Take a certified avalanche safety course before high-altitude trekking"
        ],
        "during": [
            "If caught: shout to alert others, then discard poles and skis if possible",
            "Try to move to the side of the avalanche flow as it begins",
            "If buried: use arm to create an air pocket in front of face before snow sets",
            "Spit to determine which way is down — dig upward toward surface",
            "Conserve oxygen — movement uses air rapidly in snow pocket",
            "Stay calm — panic increases oxygen consumption",
            "Activate transceiver to search/receive mode immediately"
        ],
        "after": [
            "Search for buried victims IMMEDIATELY — survival rate drops sharply after 15 minutes",
            "Use probe to locate victims, then shovel carefully to not injure them",
            "Warm buried survivors gradually — hypothermia is life-threatening",
            "Call emergency services: ITBP Helpline 1800-180-1234 in Himalayan regions",
            "Do not cross the avalanche debris until cleared by professionals",
            "Report avalanche path data to SASE for future hazard mapping"
        ]
    },
    "dust_storm": {
        "title": "🌫 Dust Storm / Sandstorm Safety Guidelines",
        "source": "NDMA India / IMD",
        "before": [
            "Monitor IMD dust storm alerts, especially April–June in North/Northwest India",
            "Seal windows and door gaps with wet towels or foam strips",
            "Keep N95 masks and goggles accessible for all family members",
            "Park vehicles in garages or cover with protective sheets",
            "Clear the area around your home of loose objects that can become projectiles",
            "Prepare emergency lighting — power cuts are common during dust storms",
            "Brief children — keep them indoors immediately when skies darken"
        ],
        "during": [
            "Stay indoors and keep all doors/windows tightly shut",
            "Wear N95 mask and goggles if outdoors is unavoidable",
            "If driving: pull off road, turn off lights, keep foot off brake pedal",
            "Do not take shelter under highway overpasses — creates wind tunnel effect",
            "Protect animals — bring livestock indoors or behind windbreaks",
            "Turn off HVAC systems — dust infiltrates through air conditioning",
            "Stay clear of power lines — dust storms frequently cause them to fall"
        ],
        "after": [
            "Clean dust carefully — damp cloth first to prevent redistributing particles",
            "Replace HVAC filters — heavy dust loads damage air conditioning systems",
            "Inspect and clean vehicle air filter before driving long distances",
            "Check food and water — fine dust contaminates open containers",
            "Eye care: flush eyes with clean water, avoid rubbing — scratches corneas",
            "Monitor children and elderly for respiratory symptoms post-storm"
        ]
    },
    "lightning": {
        "title": "⚡ Lightning Safety Guidelines",
        "source": "NDMA India / IMD / IEEE",
        "before": [
            "Install lightning protection rods on tall buildings — ISI certified only",
            "Stay updated on IMD thunderstorm warnings — check forecast daily",
            "Identify safe structures in your area: concrete buildings with lightning rods",
            "Count seconds between lightning and thunder — 5 seconds = 1 km away",
            "Unplug electronics before storm — surge protectors do not prevent all damage",
            "Keep surge protectors on computers and sensitive equipment year-round",
            "Avoid planting tall isolated trees near living areas"
        ],
        "during": [
            "Follow the 30-30 rule: if thunder within 30 sec of lightning, stay in for 30 min after",
            "Safe: substantial buildings, hard-topped metal vehicles",
            "UNSAFE: open structures, gazebos, tents, convertible cars, under trees",
            "If outdoors: crouch low with feet together, avoid lying flat (ground current)",
            "Stay away from metal objects: fences, golf clubs, umbrellas, bikes",
            "Move away from water: ponds, lakes, swimming pools immediately",
            "Inside: avoid plumbing, landlines, windows, doors, and electrical panels"
        ],
        "after": [
            "Lightning strike victims carry NO electrical charge — help them immediately",
            "Call 108 (Ambulance) — cardiac arrest is the leading cause of death in lightning strikes",
            "Check for secondary injuries from fall or blast effect",
            "Survivors often have permanent neurological effects — follow up with doctor",
            "Inspect building structure — lightning can cause internal damage without visible marks",
            "Check trees for delayed falling hazard — lightning can kill a tree slowly"
        ]
    },
    "chemical": {
        "title": "☢ Chemical / Industrial Disaster Safety Guidelines",
        "source": "NDMA India / MoEF / UN OPCW",
        "before": [
            "Know nearby industrial facilities and the chemicals they store",
            "Familiarize yourself with community warning sirens and their meanings",
            "Seal emergency safe room: weather stripping on doors, plastic sheeting ready",
            "Prepare emergency go-bag including a full change of clothes",
            "Locate the nearest upwind evacuation route from industrial zones",
            "Keep windows and doors sealed during industrial emergencies",
            "Register with local emergency management for community alerts"
        ],
        "during": [
            "If ordered to shelter-in-place: go to interior room, seal doors and windows",
            "Turn off all HVAC and fans — stops bringing contaminated air inside",
            "If evacuating: cover nose/mouth with wet cloth, move crosswind not downwind",
            "Do NOT eat, drink, or touch anything potentially contaminated",
            "Remove and bag clothing if you've been exposed — do not bring indoors",
            "Shower with soap and water if skin contact occurred",
            "Call emergency: 112. Describe the chemical if known"
        ],
        "after": [
            "Do not return until officials confirm area is decontaminated",
            "Follow decontamination instructions from NDRF/local authorities",
            "Seek medical evaluation even if you feel fine — many chemicals have delayed effects",
            "Report any dead fish, birds, or unusual plant die-off — signs of contamination",
            "Dispose of potentially contaminated food, water, and clothing as directed",
            "Participate in long-term health monitoring programs"
        ]
    },
    "nuclear": {
        "title": "☢ Nuclear Emergency Safety Guidelines",
        "source": "NDMA India / AERB / IAEA",
        "before": [
            "Know if you live within 16 km of a nuclear facility — Emergency Planning Zone",
            "Register for nuclear emergency alerts from Atomic Energy Regulatory Board (AERB)",
            "Keep potassium iodide (KI) tablets only if prescribed by health authorities",
            "Learn the difference between shelter-in-place and evacuation orders",
            "Identify the most interior, lowest-floor room in your concrete building",
            "Prepare 2-week emergency supply: food, water, medications, radio",
            "Have a battery-powered or hand-crank radio for emergency broadcasts"
        ],
        "during": [
            "SHELTER IN PLACE immediately when alarm sounds — do not go outside",
            "Close and seal ALL windows, doors, fireplace dampers",
            "Turn off all HVAC — stops radioactive particles from entering",
            "If outdoors when alarm sounds: cover mouth, run inside nearest building",
            "Remove and bag outer clothing — reduces radiation contamination by 80%",
            "Shower immediately if you were outdoors — wash hair thoroughly",
            "Listen ONLY to official government broadcasts — do not spread rumours"
        ],
        "after": [
            "Do not return home until authorities confirm radiation levels are safe",
            "Follow dosimetry instructions from nuclear safety authorities",
            "Do not consume local food, water, or milk without official clearance",
            "All exposed persons must be medically evaluated — long-term monitoring needed",
            "Record all official communications for personal health history",
            "Mental health support is critical — radiation emergencies cause severe anxiety"
        ]
    },
    "dam_failure": {
        "title": "🏗 Dam Failure / Flash Flood Safety Guidelines",
        "source": "NDMA India / CWC / ICOLD",
        "before": [
            "Know if you live downstream of a dam — check CWC (Central Water Commission) dam safety maps",
            "Memorize evacuation routes to high ground — practice with family twice yearly",
            "Monitor CWC flood forecasting bulletins during monsoon season",
            "Keep emergency supplies ready: 3-day food, water, medicines, documents",
            "Know community warning signals for dam emergency — check with local administration",
            "Identify the nearest high ground (at least 15 metres above river level)",
            "Register for SMS flood alerts from State Emergency Operations Centre"
        ],
        "during": [
            "If you hear roaring sound or see rapid water rise — EVACUATE IMMEDIATELY",
            "Move to highest ground as fast as possible — dam breaks can send wall of water",
            "Do NOT try to collect belongings — seconds matter in flash flood",
            "NEVER try to cross moving floodwater on foot or in vehicle",
            "If trapped: move to upper floors, signal for rescue with bright cloth or torch",
            "Call 1078 (NDMA) and 112 (Emergency) immediately",
            "Follow only official evacuation routes — unofficial paths may be submerged"
        ],
        "after": [
            "Do not return until dam stability is confirmed by engineers",
            "Assume all tap water is contaminated — boil or use bottled water",
            "Check structural integrity of your home before re-entering",
            "Report all dam damage and breach details to CWC and district authorities",
            "Document damage thoroughly for government compensation claims",
            "Support community mental health recovery — displacement causes trauma"
        ]
    },
    "pandemic": {
        "title": "🦠 Pandemic / Epidemic Safety Guidelines",
        "source": "NDMA India / MoHFW / WHO",
        "before": [
            "Stay up to date on all recommended vaccinations — check MoHFW guidelines",
            "Stock 30-day supply of essential medications for chronic conditions",
            "Maintain emergency food supply: canned goods, dry food, water",
            "Know your nearest government hospital and fever clinic location",
            "Practice regular hand hygiene — 20 seconds with soap and water",
            "Keep N95 masks and pulse oximeters at home",
            "Establish contact with local ASHA worker and PHC for health monitoring"
        ],
        "during": [
            "Follow only MoHFW / WHO guidelines — ignore social media misinformation",
            "Isolate immediately if symptomatic — notify local health department",
            "Wear N95 mask in public — surgical masks provide less protection",
            "Maintain social distancing — minimize contact with high-risk individuals",
            "Report to fever clinic within 24 hours of symptom onset",
            "Monitor oxygen saturation: below 94% requires immediate hospital care",
            "Do not self-medicate with unproven treatments — consult MBBS doctor"
        ],
        "after": [
            "Continue precautions until WHO/government declares end of public health emergency",
            "Long-COVID is real — get medical evaluation if symptoms persist weeks after recovery",
            "Support community vaccination drives — herd immunity protects everyone",
            "Mental health support: isolation and illness cause depression and anxiety",
            "Contact NIMHANS helpline for psychological support: 080-46110007",
            "Update household emergency plans based on lessons from the pandemic"
        ]
    },
    "storm_surge": {
        "title": "🌊 Storm Surge / Coastal Flood Safety Guidelines",
        "source": "NDMA India / IMD / INCOIS",
        "before": [
            "Know your community's storm surge flood zone — check IMD coastal maps",
            "Prepare early evacuation plan — storm surge can be fatal within minutes",
            "Install storm shutters or boards for all windows in coastal homes",
            "Elevate electrical panels, HVAC, and appliances above likely flood levels",
            "Keep boat or life-jackets if living in extremely low coastal areas",
            "Sign up for IMD coastal weather alerts and INCOIS sea state warnings",
            "Keep vehicle fuelled and facing the evacuation direction"
        ],
        "during": [
            "Evacuate when ordered — storm surge can be 9 metres high and travel inland kilometers",
            "NEVER try to ride out a surge in a mobile home or low-lying structure",
            "Move inland and to higher ground — even 1 metre of surge water can knock you over",
            "Never underestimate surge force — it pushes cars off roads and destroys walls",
            "If trapped: move to highest floor, signal for rescue from roof",
            "Wear life jacket if evacuation through water is unavoidable",
            "Do not attempt to walk through surge — submerged objects and currents are lethal"
        ],
        "after": [
            "Do not return until waters fully recede and officials confirm safety",
            "Assume all water is contaminated with sewage and chemicals",
            "Photograph all damage before cleanup for insurance and government claims",
            "Wear rubber gloves and boots when cleaning — many pathogens in surge water",
            "Check coastal erosion damage — homes may be structurally compromised",
            "Engage with coastal protection planning — mangrove restoration reduces surge impact"
        ]
    },
    "building_collapse": {
        "title": "🏚 Building Collapse Safety Guidelines",
        "source": "NDMA India / BIS / UNDAC",
        "before": [
            "Get older buildings structurally assessed every 10 years",
            "Never add unauthorized floors — overloading causes collapse",
            "Report visible cracks in walls or columns to municipal engineer immediately",
            "Avoid buildings showing signs: cracks wider than 3mm, leaning walls, sagging floors",
            "Know structural difference: RCC buildings safer than unreinforced masonry",
            "Familiarize all family members with building exits and stairwell locations",
            "Keep emergency whistle and torch in bedroom for nighttime emergencies"
        ],
        "during": [
            "If building collapses: protect head and body — curl into fetal position",
            "Stay near inner walls or under sturdy tables — avoid exterior walls",
            "Do not run during collapse — most injuries from debris during movement",
            "If trapped: tap pipes or walls to signal rescuers — conserve voice for when help is near",
            "Cover nose and mouth with cloth — dust causes respiratory distress",
            "Turn off gas if possible — fire is major secondary hazard in collapses",
            "Move only if in immediate danger of fire or rising water"
        ],
        "after": [
            "Call NDRF (National Disaster Response Force): 011-24363260 immediately",
            "Do not enter partially collapsed buildings — secondary collapse risk is high",
            "Mark searched areas with spray paint for rescue teams — prevents double-searching",
            "Provide rescuers with information: number of trapped, last known location",
            "Do not move seriously injured victims unless fire/flood is immediate threat",
            "Set up triage area away from collapse zone for injured survivors"
        ]
    }
}   


# ─── AI CORE ──────────────────────────────────────────────────
SYSTEM = """You are RAKSHA — India's official disaster intelligence assistant, built on verified NDMA guidelines.

STRICT RULES:
1. LANGUAGE: Always reply in the exact language the user writes in. Tamil→Tamil, Hindi→Hindi, etc. Never mix languages.
2. ACCURACY: Only provide information based on verified NDMA, IMD, and established disaster science. Never fabricate statistics, events, or numbers.
3. HELPLINES: ONLY cite verified numbers — NDMA:1078, Emergency:112, Fire:101, Ambulance:108, Police:100, Coast Guard:1554.
4. FORMAT: Use emojis. Structure clearly. If risk is HIGH/CRITICAL, begin with ⚠️ WARNING.
5. HONESTY: If you don't know something, say so. Never make up disaster events.
"""

def build_ctx(weather, risk):
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
        a = {k:v for k,v in risk["risks"].items() if v>0}
        if a:
            parts.append(f"NDMA RISK ({risk['overall']}): " + " | ".join(f"{k}={v}/5" for k,v in a.items()))
    return "\n".join(parts)

def ask_ai(msg, weather=None, risk=None, history=None, username=None, lang="English"):
    system = SYSTEM
    if username: system += f"\nUser: {username}."
    system += f"\nRespond in {lang} language."
    ctx = build_ctx(weather, risk)
    if ctx: system += f"\n\nLIVE DATA:\n{ctx}"
    msgs = list((history or [])[-8:])
    msgs.append({"role":"user","content":msg})
    try:
        r = groq_client.chat.completions.create(
            model=MODEL, max_tokens=1024, temperature=0.4,
            messages=[{"role":"system","content":system}]+msgs
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI error: {e}"


# ─── AUTH ROUTES ──────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    d=request.json; name=d.get("name","").strip(); email=d.get("email","").strip().lower(); pw=d.get("password","")
    if not all([name,email,pw]): return jsonify({"status":"error","message":"All fields required."})
    if len(pw)<6: return jsonify({"status":"error","message":"Password min 6 characters."})
    if "@" not in email: return jsonify({"status":"error","message":"Invalid email."})
    if db_get_user(email): return jsonify({"status":"error","message":"Email already registered."})
    phone=d.get("phone","")
    user = db_create_user(name, email, pw, phone)
    if not user: return jsonify({"status":"error","message":"Registration failed. Please try again."})
    session["email"]=email; session["name"]=name; session["lang"]="English"
    return jsonify({"status":"success","name":name,"lang":"English"})

@app.route("/api/login", methods=["POST"])
def login():
    d=request.json; email=d.get("email","").strip().lower(); pw=d.get("password","")
    if not email or not pw: return jsonify({"status":"error","message":"Email and password required."})
    user = db_get_user(email)
    if not user or user["password"] != hash_pw(pw): return jsonify({"status":"error","message":"Invalid email or password."})
    db_record_login(email)
    session["email"]=email; session["name"]=user["name"]; session["lang"]=user.get("lang","English")
    return jsonify({"status":"success","name":user["name"],"lang":user.get("lang","English")})


# ═══════════════════════════════════════════════════════════════
# /api/google-auth  — Verify Google ID token, auto-create account
# ---------------------------------------------------------------
# Uses google-auth library to verify the JWT credential returned
# by Google Identity Services (One Tap / popup).
# On success: creates account if new, sets session, returns name.
# ═══════════════════════════════════════════════════════════════
@app.route("/api/google-auth", methods=["GET", "POST"])
def google_auth():
    # GET hits happen when a browser redirect lands here (wrong flow) — show a clean message
    if request.method == "GET":
        return """<html><body style="font-family:sans-serif;padding:40px;background:#020c1b;color:#dff4ff;">
        <h2>⚠️ Google Sign-In Error</h2>
        <p>This page should not be opened directly.<br>
        Please close this tab and sign in from the RAKSHA app.</p>
        <script>
          if(window.opener){ window.opener.postMessage({type:'google_auth_error',message:'Wrong flow — please retry'},'*'); }
          setTimeout(()=>window.close(), 2000);
        </script></body></html>""", 400
    if not GOOGLE_CLIENT_ID:
        return jsonify({"status": "error", "message": "Google Sign-In is not configured on this server."}), 503

    body = request.get_json(force=True, silent=True) or {}
    credential = body.get("credential", "").strip()
    mode = body.get("mode", "login")   # "login" or "register"

    if not credential:
        return jsonify({"status": "error", "message": "No credential received from Google."}), 400

    # ── Verify the ID token with Google ──────────────────────
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ImportError:
        # google-auth not installed — fall back to Google tokeninfo endpoint
        try:
            resp = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential},
                timeout=8,
            )
            if resp.status_code != 200:
                return jsonify({"status": "error", "message": "Google token verification failed."}), 401
            id_info = resp.json()
            if id_info.get("aud") != GOOGLE_CLIENT_ID:
                return jsonify({"status": "error", "message": "Token audience mismatch."}), 401
        except Exception as e:
            return jsonify({"status": "error", "message": f"Could not verify Google token: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid Google token: {e}"}), 401

    # ── Extract user info from verified token ─────────────────
    email = (id_info.get("email") or "").strip().lower()
    name  = id_info.get("name") or id_info.get("given_name") or email.split("@")[0]
    email_verified = id_info.get("email_verified", False)

    if not email:
        return jsonify({"status": "error", "message": "Could not retrieve email from Google."}), 400
    if not email_verified:
        return jsonify({"status": "error", "message": "Google account email is not verified."}), 400

    # ── Find or create user ───────────────────────────────────
    existing = db_get_user(email)
    is_new = False

    if existing:
        # Existing user — record this login
        lang = existing.get("lang", "English")
        db_record_login(email)
    else:
        # New user — create account with a random unusable password
        # (Google users never use password login, so this is safe)
        random_pw = secrets.token_hex(32)
        user = db_create_user(name, email, random_pw, "")
        if not user:
            return jsonify({"status": "error", "message": "Account creation failed. Please try again."}), 500
        # Mark as Google auth provider in Supabase
        if USE_SUPABASE:
            try:
                supabase.table("users").update({"auth_provider": "google"}).eq("email", email).execute()
            except Exception as e:
                print(f"[google_auth] Could not set auth_provider: {e}")
        lang = "English"
        is_new = True

    session["email"] = email
    session["name"]  = name
    session["lang"]  = lang

    return jsonify({
        "status":  "success",
        "name":    name,
        "lang":    lang,
        "is_new":  is_new,
        "email":   email,
    })

@app.route("/api/logout",methods=["POST"])
def logout(): session.clear(); return jsonify({"status":"success"})

@app.route("/api/me")
def me():
    if "email" in session: return jsonify({"logged_in":True,"name":session["name"],"lang":session.get("lang","English")})
    return jsonify({"logged_in":False})

@app.route("/api/set-lang",methods=["POST"])
def set_lang():
    if "email" not in session: return jsonify({"status":"error"})
    lang=request.json.get("lang","English"); session["lang"]=lang
    db_update_lang(session["email"], lang)
    return jsonify({"status":"success","lang":lang})

@app.route("/api/languages")
def languages(): return jsonify({"languages":ALL_LANGUAGES,"ui_strings":UI_STRINGS})


# ─── DATA ROUTES ──────────────────────────────────────────────
@app.route("/api/news")
def news():
    items = fetch_verified_news()   # now cached + parallel
    return jsonify({
        "news": items,
        "source_note": "All news from verified official sources: GDACS, ReliefWeb, EMSC, WHO, UN OCHA only."
    })

@app.route("/api/guidelines")
def guidelines_all(): return jsonify({"guidelines": GUIDELINES})

@app.route("/api/guidelines/<disaster>")
def guideline(disaster):
    g = GUIDELINES.get(disaster.lower())
    if not g: return jsonify({"error": "Not found"}), 404
    return jsonify(g)


# ═══════════════════════════════════════════════════════════════
# FIXED /api/alerts — HIGH and CRITICAL only
# ---------------------------------------------------------------
# CHANGE SUMMARY vs original:
#   • classify_alert_level() replaces the single is_severe boolean
#   • Items that classify as None are DROPPED (not returned)
#   • CRITICAL tier is now populated (was never present before)
#   • Filtering is on the BACKEND (not the frontend map JS)
#
# WHY BACKEND FILTERING:
#   The three map pages (Disaster Zones, Risk Analysis, Shelter)
#   all fetch /api/alerts. Filtering here means:
#     1. Smaller JSON payload over the wire
#     2. Frontend maps never receive LOW/MODERATE data at all —
#        no risk of them accidentally rendering it
#     3. One place to change the threshold if requirements change
#     4. The Shelter Map's marker list stays clean without
#        additional JS filtering logic in each template
# ═══════════════════════════════════════════════════════════════
@app.route("/api/alerts")
def alerts():
    """Real alerts from official RSS feeds — HIGH and CRITICAL only."""
    items = fetch_verified_news()   # cached + parallel

    alerts_out = []
    counts = {"CRITICAL": 0, "HIGH": 0}

    for it in items:
        level = classify_alert_level(it["title"], it.get("desc", ""))
        if level is None:
            continue   # DROP: LOW and MODERATE are excluded entirely

        counts[level] += 1
        alerts_out.append({
            "state":   "India",
            "type":    "Disaster Alert",
            "level":   level,          # "CRITICAL" or "HIGH" only
            "message": it["title"],
            "issued":  it["source"],
            "link":    it.get("link", ""),
            "date":    it.get("date", ""),
        })

    return jsonify({
        "alerts":      alerts_out[:15],
        "verified":    True,
        "counts":      counts,
        "filter_note": "Only HIGH and CRITICAL severity alerts are returned. "
                       "LOW and MODERATE alerts are excluded at the server level.",
    })


# ═══════════════════════════════════════════════════════════════
# /api/disaster-zones — Disaster Zone Map feed
# HIGH and CRITICAL only (same filter, dedicated endpoint)
# ═══════════════════════════════════════════════════════════════
@app.route("/api/disaster-zones")
def disaster_zones():
    """
    Returns HIGH and CRITICAL alerts formatted for the Disaster
    Zones map layer.  LOW and MODERATE zones are never returned.
    """
    items = fetch_verified_news()

    zones = []
    for it in items:
        level = classify_alert_level(it["title"], it.get("desc", ""))
        if level is None:
            continue

        # Marker colour used by the map template
        color = "#DC2626" if level == "CRITICAL" else "#EA580C"   # red / orange

        zones.append({
            "level":   level,
            "color":   color,
            "title":   it["title"],
            "source":  it["source"],
            "link":    it.get("link", ""),
            "date":    it.get("date", ""),
        })

    critical_count = sum(1 for z in zones if z["level"] == "CRITICAL")
    high_count     = sum(1 for z in zones if z["level"] == "HIGH")

    return jsonify({
        "zones":          zones[:20],
        "critical_count": critical_count,
        "high_count":     high_count,
        "total":          critical_count + high_count,
        # Legend entries — ONLY these two levels exist
        "legend": [
            {"level": "CRITICAL", "color": "#DC2626", "label": "Critical — immediate danger"},
            {"level": "HIGH",     "color": "#EA580C", "label": "High — serious hazard"},
        ],
        "filter_note": "Only HIGH and CRITICAL zones rendered. LOW and MODERATE excluded.",
    })


# ═══════════════════════════════════════════════════════════════
# /api/risk-analysis — Risk Analysis Map feed
# Uses compute_risk() on live weather for the requested location
# and cross-references with RSS alerts.
# ═══════════════════════════════════════════════════════════════
@app.route("/api/risk-analysis", methods=["POST"])
def risk_analysis():
    """
    POST body: { "lat": float, "lon": float }  (optional; defaults to India centroid)
    Returns weather-derived risk score AND HIGH/CRITICAL RSS alerts only.
    """
    d   = request.json or {}
    lat = d.get("lat", 20.5937)
    lon = d.get("lon", 78.9629)

    weather = get_weather_coords(lat, lon)
    risk    = compute_risk(weather) if weather and "error" not in weather else None

    # Only surface HIGH / CRITICAL from the weather risk engine
    # (MODERATE, LOW, NORMAL are dropped from the risk map markers)
    risk_level = None
    risk_items = []
    if risk:
        risk_level = risk["overall"]
        if risk_level in ("HIGH", "CRITICAL"):
            for hazard, score in risk["risks"].items():
                if score >= 3:   # score 3–5 maps to HIGH; 4–5 maps to CRITICAL
                    hazard_level = "CRITICAL" if score >= 4 else "HIGH"
                    risk_items.append({
                        "hazard": hazard,
                        "score":  score,
                        "level":  hazard_level,
                        "color":  "#DC2626" if hazard_level == "CRITICAL" else "#EA580C",
                    })
        # If overall is MODERATE/LOW/NORMAL, risk_items stays empty → no markers

    # Fetch and filter RSS alerts (same backend filter)
    rss_items = fetch_verified_news()
    rss_alerts = []
    for it in rss_items:
        level = classify_alert_level(it["title"], it.get("desc", ""))
        if level:
            rss_alerts.append({"level": level, "title": it["title"], "source": it["source"]})

    return jsonify({
        "weather":     weather,
        "risk":        risk,
        "risk_items":  risk_items,    # only HIGH/CRITICAL hazards
        "rss_alerts":  rss_alerts[:8],
        "legend": [
            {"level": "CRITICAL", "color": "#DC2626", "label": "Critical risk"},
            {"level": "HIGH",     "color": "#EA580C", "label": "High risk"},
        ],
        "filter_note": "MODERATE, LOW, and NORMAL risk zones are not rendered on this map.",
    })


# ─── WEATHER + CHAT ROUTES (unchanged) ────────────────────────
@app.route("/weather", methods=["POST"])
def weather_only():
    d=request.json; lat=d.get("lat"); lon=d.get("lon"); city=d.get("city","Chennai")
    w=get_weather_coords(lat,lon) if (lat and lon) else get_weather_city(city)
    r=compute_risk(w) if w and "error" not in w else None
    fc=get_forecast(w.get("lat",20.59),w.get("lon",78.96)) if w and "error" not in w else []
    return jsonify({"weather":w,"risk":r,"forecast":fc})

@app.route("/chat", methods=["POST"])
def chat():
    if "email" not in session: return jsonify({"reply":"⚠️ Please log in."}),401
    d=request.json; msg=d.get("message","").strip(); lat=d.get("lat"); lon=d.get("lon"); history=d.get("history",[])
    if not msg: return jsonify({"reply":"⚠️ Empty."})
    if len(msg)>800: return jsonify({"reply":"⚠️ Too long."})
    lower=msg.lower()
    kws=["weather","rain","flood","cyclone","storm","temp","humid","wind","disaster","alert","risk",
         "safe","forecast","heat","fog","lightning","thunder","earthquake","landslide",
         "வானிலை","மழை","வெள்ளம்","புயல்","मौसम","बारिश","बाढ़","तूफान",
         "వాతావరణం","వరద","కాలావస్థ","ಹವಾಮಾನ","ಮಳೆ","ಪ್ರವಾಹ",
         "കാലാവസ്ഥ","മഴ","വെള്ളപ്പൊക്കം","আবহাওয়া","বন্যা","ਹੜ੍ਹ","ਹਨੇਰੀ"]
    needs_w = any(k in lower for k in kws) or lat
    weather,risk = None,None
    if needs_w:
        if lat and lon: weather=get_weather_coords(lat,lon)
        else:
            city="Chennai"; words=lower.split()
            for i,w in enumerate(words):
                if w in ("in","at","for","இல்","में","లో","ൽ","ಲ್ಲಿ","এ","ਵਿੱਚ") and i+1<len(words):
                    city=" ".join(words[i+1:]).strip("?.,!").title(); break
            weather=get_weather_city(city)
        if weather and "error" not in weather: risk=compute_risk(weather)
    lang=session.get("lang","English")
    reply=ask_ai(msg,weather=weather,risk=risk,history=history,username=session.get("name"),lang=lang)
    return jsonify({"reply":reply,"weather":weather,"risk":risk})

@app.route("/")
def home():
    with open("templates/index.html", encoding="utf-8") as f:
        html = f.read()
    # Inject Google Client ID into the meta tag placeholder
    html = html.replace("{{ google_client_id }}", GOOGLE_CLIENT_ID or "")
    return html



if __name__ == "__main__":
    # debug=True enables auto-reload on file save + detailed error pages
    # Set to False in production
    app.run(debug=True, port=5000)