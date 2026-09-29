"""
blueprints/auth/data.py — Static language and UI string data for RAKSHA.

ALL_LANGUAGES : list of all 22 official Indian languages + English
UI_STRINGS    : per-language UI label translations
"""

ALL_LANGUAGES = [
    {"name": "Assamese",  "native": "অসমীয়া",    "code": "as",  "flag": "🇮🇳"},
    {"name": "Bengali",   "native": "বাংলা",       "code": "bn",  "flag": "🇮🇳"},
    {"name": "Bodo",      "native": "बड़ो",         "code": "brx", "flag": "🇮🇳"},
    {"name": "Dogri",     "native": "डोगरी",        "code": "doi", "flag": "🇮🇳"},
    {"name": "Gujarati",  "native": "ગુજરાતી",     "code": "gu",  "flag": "🇮🇳"},
    {"name": "Hindi",     "native": "हिन्दी",       "code": "hi",  "flag": "🇮🇳"},
    {"name": "Kannada",   "native": "ಕನ್ನಡ",        "code": "kn",  "flag": "🇮🇳"},
    {"name": "Kashmiri",  "native": "کٲشُر",        "code": "ks",  "flag": "🇮🇳"},
    {"name": "Konkani",   "native": "कोंकणी",       "code": "kok", "flag": "🇮🇳"},
    {"name": "Maithili",  "native": "मैथिली",       "code": "mai", "flag": "🇮🇳"},
    {"name": "Malayalam", "native": "മലയാളം",       "code": "ml",  "flag": "🇮🇳"},
    {"name": "Manipuri",  "native": "মৈতৈলোন্",    "code": "mni", "flag": "🇮🇳"},
    {"name": "Marathi",   "native": "मराठी",        "code": "mr",  "flag": "🇮🇳"},
    {"name": "Nepali",    "native": "नेपाली",       "code": "ne",  "flag": "🇮🇳"},
    {"name": "Odia",      "native": "ଓଡ଼ିଆ",        "code": "or",  "flag": "🇮🇳"},
    {"name": "Punjabi",   "native": "ਪੰਜਾਬੀ",       "code": "pa",  "flag": "🇮🇳"},
    {"name": "Sanskrit",  "native": "संस्कृतम्",    "code": "sa",  "flag": "🇮🇳"},
    {"name": "Santali",   "native": "ᱥᱟᱱᱛᱟᱲᱤ",    "code": "sat", "flag": "🇮🇳"},
    {"name": "Sindhi",    "native": "سنڌي",         "code": "sd",  "flag": "🇮🇳"},
    {"name": "Tamil",     "native": "தமிழ்",        "code": "ta",  "flag": "🇮🇳"},
    {"name": "Telugu",    "native": "తెలుగు",       "code": "te",  "flag": "🇮🇳"},
    {"name": "Urdu",      "native": "اردو",          "code": "ur",  "flag": "🇮🇳"},
    {"name": "English",   "native": "English",      "code": "en",  "flag": "🇬🇧"},
]

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
