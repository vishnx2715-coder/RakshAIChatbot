/* ═══ CONSTANTS ═══ */
const WICO={Clear:'☀️',Clouds:'☁️',Rain:'🌧',Drizzle:'🌦',Thunderstorm:'⛈',Snow:'❄️',Mist:'🌫',Fog:'🌫',Haze:'🌁',Smoke:'🌫',Dust:'🌪',Sand:'🌪',Tornado:'🌪'};
const RISK_META={cyclone:{icon:'🌀',l:'Cyclone'},flood:{icon:'🌊',l:'Flood'},heatwave:{icon:'🌡',l:'Heatwave'},cold_wave:{icon:'❄️',l:'Cold Wave'},dense_fog:{icon:'🌫',l:'Dense Fog'},thunderstorm:{icon:'⛈',l:'Thunderstorm'},lightning:{icon:'⚡',l:'Lightning'}};
// OWM_KEY is injected by Flask via window.RAKSHA_CONFIG in base.html (never hardcoded in static files)
const OWM_KEY=(window.RAKSHA_CONFIG||{}).owmKey||'';
const RCOLORS={CRITICAL:'#ef4444',HIGH:'#f97316',MODERATE:'#eab308',LOW:'#22d3ee',NORMAL:'#4ade80'};
const RISK_COL_RGB={NORMAL:'74,222,128',LOW:'56,189,248',MODERATE:'252,211,77',HIGH:'249,115,22',CRITICAL:'239,68,68'};

/* ═══ DISASTER QUESTIONS — TOP 5 PRIORITY EACH ═══ */
const DISASTER_QUESTIONS={
  flood:{icon:'🌊',title:'Flood Safety',priority:[
    {ico:'🚨',text:'What are immediate steps if flood water enters my home right now?'},
    {ico:'🗺',text:'How do I find the nearest flood evacuation shelter near me?'},
    {ico:'🚗',text:'Is it safe to drive through flooded roads — what depth is dangerous?'},
    {ico:'💧',text:'How do I purify flood-contaminated water for drinking?'},
    {ico:'📞',text:'Which helpline should I call for flood rescue in India?'},
  ]},
  cyclone:{icon:'🌀',title:'Cyclone Emergency',priority:[
    {ico:'🏠',text:'How do I secure my home before a cyclone hits — step by step?'},
    {ico:'👁',text:'Why is the eye of the cyclone dangerous — what to do when winds temporarily calm?'},
    {ico:'🏃',text:'When exactly should I evacuate vs shelter in place during a cyclone?'},
    {ico:'📻',text:'Which radio stations broadcast official cyclone updates in India?'},
    {ico:'⏱',text:'How long should I wait before going outside after the cyclone passes?'},
  ]},
  heatwave:{icon:'🌡',title:'Heatwave Safety',priority:[
    {ico:'⚠️',text:'What are the warning signs of heat exhaustion vs heat stroke?'},
    {ico:'💧',text:'How much water should I drink per day during a severe heatwave?'},
    {ico:'🚨',text:'Someone collapsed in the heat — what are the immediate first aid steps?'},
    {ico:'⏰',text:'What are the safest times to go outside during a heatwave in India?'},
    {ico:'👴',text:'How do I protect elderly family members during an extreme heatwave?'},
  ]},
  earthquake:{icon:'🏚',title:'Earthquake Safety',priority:[
    {ico:'🛡',text:'Explain Drop Cover Hold On technique with full details for India'},
    {ico:'🔥',text:'Gas leak after earthquake — step by step emergency response'},
    {ico:'🏚',text:'How do I check if my building is safe to re-enter after an earthquake?'},
    {ico:'📱',text:'SMS vs calling after earthquake — what is the best communication plan?'},
    {ico:'⚠️',text:'How long do aftershocks last and how dangerous are they?'},
  ]},
  landslide:{icon:'⛰',title:'Landslide Safety',priority:[
    {ico:'👁',text:'What are the early warning signs of a landslide about to happen?'},
    {ico:'🏃',text:'What are the immediate steps if I hear rumbling sounds indicating a landslide?'},
    {ico:'🧭',text:'How do I evacuate safely from a mountain road during a landslide?'},
    {ico:'⏱',text:'How long is it dangerous after a landslide — when is secondary slide risk over?'},
    {ico:'📞',text:'SDRF and NDRF landslide rescue contacts for Uttarakhand, HP, NE India'},
  ]},
  tsunami:{icon:'🌊',title:'Tsunami Warning',priority:[
    {ico:'🌏',text:'What are the natural warning signs of an incoming tsunami?'},
    {ico:'🏃',text:'I am at the beach when an earthquake strikes — exactly what should I do?'},
    {ico:'📏',text:'How high and how far inland must I go to be safe from a tsunami?'},
    {ico:'⏱',text:'Is it safe after the first tsunami wave — how many waves arrive in total?'},
    {ico:'📡',text:'How does the INCOIS tsunami early warning system work in India?'},
  ]},
  wildfire:{icon:'🔥',title:'Wildfire Safety',priority:[
    {ico:'🏃',text:'When should I evacuate for wildfire — mandatory vs advisory evacuation order?'},
    {ico:'😷',text:'How dangerous is wildfire smoke and how do I protect myself from it?'},
    {ico:'🏠',text:'How do I protect my home from wildfire if evacuation is not possible?'},
    {ico:'⚠️',text:'I am trapped by wildfire with no escape route — survival steps?'},
    {ico:'📞',text:'Forest fire emergency contacts and SDRF numbers state-wise for India'},
  ]},
  tornado:{icon:'🌪',title:'Tornado Safety',priority:[
    {ico:'🏠',text:'What is the best room and position to shelter from a tornado in Indian homes?'},
    {ico:'🚗',text:'I am in a vehicle when a tornado approaches — what is the safest action?'},
    {ico:'🔊',text:'What does a tornado sound like and how much warning time do I get?'},
    {ico:'⚡',text:'Downed power lines after tornado — how to stay safe?'},
    {ico:'🌩',text:'Tornado watch vs tornado warning — what is the critical difference?'},
  ]},
  drought:{icon:'🏜',title:'Drought Preparedness',priority:[
    {ico:'💧',text:'How can I reduce household water use by 30% during a drought?'},
    {ico:'🌾',text:'What drought-resistant crops should Indian farmers grow during water scarcity?'},
    {ico:'💰',text:'How do I claim PM Fasal Bima Yojana crop insurance during drought?'},
    {ico:'🏠',text:'How do I set up a rainwater harvesting system for my Indian home?'},
    {ico:'🚰',text:'How do I apply for tanker water supply during severe drought in India?'},
  ]},
  winter_storm:{icon:'❄',title:'Winter Storm / Cold Wave',priority:[
    {ico:'🥶',text:'What are the symptoms of hypothermia and what is the emergency first aid?'},
    {ico:'🔥',text:'What are the safe heating methods in India — risks of coal and kerosene heaters?'},
    {ico:'🧥',text:'What clothing layers are best for surviving extreme cold in Indian winters?'},
    {ico:'💧',text:'How do I prevent water pipes from freezing in North India winters?'},
    {ico:'👴',text:'How do I protect elderly people from a cold wave — what are the warning signs?'},
  ]},
  volcanic:{icon:'🌋',title:'Volcanic Eruption',priority:[
    {ico:'🗺',text:'Where are the active volcanoes in India — Barren Island and Narcondam?'},
    {ico:'😷',text:'How dangerous is volcanic ash to health and how do I protect myself?'},
    {ico:'🏃',text:'When should I evacuate during a volcanic eruption and where should I go?'},
    {ico:'🌊',text:'What is a lahar volcanic mudflow and how dangerous is it?'},
    {ico:'🏠',text:'How do I protect my house from volcanic ash fall?'},
  ]},
  avalanche:{icon:'🏔',title:'Avalanche Safety',priority:[
    {ico:'❄',text:'What conditions trigger avalanches in the Himalayan regions of India?'},
    {ico:'🎿',text:'What essential avalanche safety gear is needed for trekking in the Himalayas?'},
    {ico:'🆘',text:'I am caught in an avalanche — exactly what should I do to survive?'},
    {ico:'❄',text:'How do I create an air pocket and breathe if buried under snow?'},
    {ico:'📞',text:'Avalanche rescue contacts — ITBP, BRO, SDRF, NDRF numbers for Himalayan regions'},
  ]},
  dust_storm:{icon:'🌫',title:'Dust Storm Safety',priority:[
    {ico:'🚗',text:'I am caught driving in a dust storm — what exact steps should I take?'},
    {ico:'😷',text:'What is the best mask for dust storm protection — N95 vs surgical vs cloth?'},
    {ico:'🏠',text:'How do I seal my home against a dust storm quickly and effectively?'},
    {ico:'👁',text:'Dust got in my eyes during a storm — what are the first aid steps?'},
    {ico:'📡',text:'How does IMD forecast dust storms and which apps give me alerts?'},
  ]},
  lightning:{icon:'⚡',title:'Lightning Safety',priority:[
    {ico:'🏠',text:'What buildings and shelters are safe during lightning — what qualifies?'},
    {ico:'📏',text:'How do I use the 30-30 rule to judge lightning distance and danger?'},
    {ico:'🏥',text:'Lightning strike victim first aid — CPR and exactly what to do?'},
    {ico:'🌳',text:'Why are trees so dangerous during lightning — the physics explained?'},
    {ico:'🔌',text:'How does a lightning surge travel through home wiring and how to protect electronics?'},
  ]},
  chemical:{icon:'☢',title:'Chemical Disaster',priority:[
    {ico:'🏠',text:'A chemical cloud is approaching — shelter-in-place procedure step by step?'},
    {ico:'🌬',text:'How do I seal my room from toxic chemical gas quickly?'},
    {ico:'🚿',text:'Chemical contamination on my skin — emergency decontamination steps?'},
    {ico:'👁',text:'Chemical splash in my eyes — what is the correct irrigation first aid?'},
    {ico:'📞',text:'Emergency number to call during a chemical industrial disaster in India?'},
  ]},
  nuclear:{icon:'☢',title:'Nuclear Emergency',priority:[
    {ico:'🏠',text:'Shelter-in-place procedure during a nuclear emergency — full step by step?'},
    {ico:'💊',text:'Potassium Iodide tablets for nuclear emergency — when and how to take them?'},
    {ico:'😷',text:'What type of mask protects against nuclear fallout particles?'},
    {ico:'🚗',text:'Nuclear evacuation procedure — what to take and where to go?'},
    {ico:'📞',text:'AERB nuclear emergency contacts and IAEA hotline numbers India?'},
  ]},
  dam_failure:{icon:'🏗',title:'Dam Failure Alert',priority:[
    {ico:'🚨',text:'I heard a roaring sound from the river — what is the exact dam break procedure?'},
    {ico:'🏃',text:'How fast does dam break flood water move — how much time do I have to escape?'},
    {ico:'📞',text:'Dam emergency helpline — CWC and state flood control room numbers?'},
    {ico:'🗺',text:'How do I find out if I live downstream of a dam in India?'},
    {ico:'📦',text:'What should be in the emergency kit for dam downstream zone residents?'},
  ]},
  pandemic:{icon:'🦠',title:'Pandemic Preparedness',priority:[
    {ico:'🏠',text:'Complete home isolation protocol for COVID and similar infectious diseases?'},
    {ico:'🫀',text:'Pulse oximeter reading — what number requires immediate hospital care?'},
    {ico:'🩺',text:'When should a home-isolated patient go to hospital — critical warning signs?'},
    {ico:'😷',text:'N95 vs surgical vs cloth mask — protection levels explained clearly?'},
    {ico:'🧠',text:'Mental health support during pandemic — NIMHANS helpline India?'},
  ]},
  storm_surge:{icon:'🌊',title:'Storm Surge Safety',priority:[
    {ico:'🚨',text:'Storm surge warning issued — when is mandatory evacuation required?'},
    {ico:'🌊',text:'How high can a storm surge get on the Indian coastline?'},
    {ico:'🚗',text:'How do I plan a coastal evacuation route before cyclone season?'},
    {ico:'🦠',text:'What waterborne diseases spread after a storm surge and how to prevent them?'},
    {ico:'📍',text:'Where do I find the storm surge elevation map for my coastal district?'},
  ]},
  building_collapse:{icon:'🏚',title:'Building Collapse',priority:[
    {ico:'🆘',text:'I am inside during a building collapse — body position and survival actions?'},
    {ico:'📞',text:'First call to make after a building collapse — NDRF number and procedure?'},
    {ico:'🔦',text:'I am trapped in rubble — how do I signal rescuers effectively?'},
    {ico:'⚠️',text:'What are the visible warning signs that my building may collapse?'},
    {ico:'🚒',text:'How do NDRF building collapse rescue operations work in India?'},
  ]},
  emergency_kit:{icon:'🎒',title:'Emergency Kit',priority:[
    {ico:'🎒',text:'What is the complete 72-hour emergency go-bag checklist for Indian families per NDMA?'},
    {ico:'💧',text:'How much water should I store per person per day in my emergency kit — NDMA guideline?'},
    {ico:'💊',text:'What essential medicines must be in a home emergency kit in India — chronic and first aid?'},
    {ico:'📄',text:'Which important documents must be in a waterproof emergency kit — Aadhaar, insurance, bank?'},
    {ico:'🔦',text:'What tools and equipment belong in an emergency kit — torch, radio, whistle, power bank?'},
  ]},
  helplines:{icon:'📞',title:'Emergency Helplines',priority:[
    {ico:'🆘',text:'What is the single national emergency number in India and when should I call 112?'},
    {ico:'🏥',text:'When should I call 108 ambulance vs go to hospital directly — EMRI guidelines India?'},
    {ico:'🌊',text:'What are the NDMA and NDRF helpline numbers for disaster rescue in India?'},
    {ico:'🌀',text:'State-wise cyclone and flood helpline numbers — which control room to contact?'},
    {ico:'🧠',text:'What are the mental health helplines available during and after disaster in India?'},
  ]},
  heavy_rain:{icon:'🌧',title:'Heavy Rain Safety',priority:[
    {ico:'🚨',text:'What are the immediate steps if heavy rain starts flooding my street right now?'},
    {ico:'🚗',text:'Is it safe to drive in heavy rain — what water depth is dangerous for vehicles?'},
    {ico:'⚡',text:'How do I stay safe from lightning during a heavy rain and thunderstorm?'},
    {ico:'🏠',text:'How do I protect my home from roof leaks and water seepage during heavy rain?'},
    {ico:'📞',text:'Which helpline should I call for flood rescue or rain emergency in India?'},
  ]},
};

/* ═══ DISASTER METADATA FOR QUICK GRID ═══ */
const QUICK_ACTIONS=[
  {ico:'🌧',lbl:'Heavy Rain',key:'heavy_rain'},
  {ico:'🌊',lbl:'Flood',key:'flood'},
  {ico:'🌀',lbl:'Cyclone',key:'cyclone'},
  {ico:'🌡',lbl:'Heatwave',key:'heatwave'},
  {ico:'🏚',lbl:'Earthquake',key:'earthquake'},
  {ico:'⛰',lbl:'Landslide',key:'landslide'},
  {ico:'🌊',lbl:'Tsunami',key:'tsunami'},
  {ico:'🔥',lbl:'Wildfire',key:'wildfire'},
  {ico:'🌪',lbl:'Tornado',key:'tornado'},
  {ico:'🏜',lbl:'Drought',key:'drought'},
  {ico:'❄',lbl:'Winter Storm',key:'winter_storm'},
  {ico:'🌋',lbl:'Volcanic',key:'volcanic'},
  {ico:'🏔',lbl:'Avalanche',key:'avalanche'},
  {ico:'🌫',lbl:'Dust Storm',key:'dust_storm'},
  {ico:'⚡',lbl:'Lightning',key:'lightning'},
  {ico:'☢',lbl:'Chemical',key:'chemical'},
  {ico:'☢',lbl:'Nuclear',key:'nuclear'},
  {ico:'🏗',lbl:'Dam Failure',key:'dam_failure'},
  {ico:'🦠',lbl:'Pandemic',key:'pandemic'},
  {ico:'🌊',lbl:'Storm Surge',key:'storm_surge'},
  {ico:'🏚',lbl:'Collapse',key:'building_collapse'},
  {ico:'🎒',lbl:'Emergency Kit',key:'emergency_kit'},
  {ico:'📞',lbl:'Helplines',key:'helplines'},
];

/* ═══ ZONES: INDIA + NEIGHBOURS + WORLD ═══ */
const INDIA_ZONES=[
  {lat:13.08,lon:80.27,name:"Chennai, Tamil Nadu",type:"Cyclone / Flood",risk:"HIGH",icon:"🌀",country:"India"},
  {lat:20.29,lon:85.82,name:"Odisha Coastline",type:"Cyclone",risk:"HIGH",icon:"🌀",country:"India"},
  {lat:22.57,lon:88.36,name:"Kolkata, West Bengal",type:"Flood / Storm",risk:"HIGH",icon:"🌊",country:"India"},
  {lat:30.73,lon:79.07,name:"Uttarakhand Hills",type:"Landslide / Flash Flood",risk:"HIGH",icon:"⛰",country:"India"},
  {lat:26.85,lon:80.91,name:"Uttar Pradesh",type:"Heatwave / Flood",risk:"MODERATE",icon:"🌡",country:"India"},
  {lat:26.18,lon:91.73,name:"Assam",type:"Flood",risk:"HIGH",icon:"🌊",country:"India"},
  {lat:8.52,lon:76.93,name:"Kerala",type:"Flood / Landslide",risk:"MODERATE",icon:"🌊",country:"India"},
  {lat:19.07,lon:72.87,name:"Mumbai",type:"Flood / Storm",risk:"MODERATE",icon:"🌊",country:"India"},
  {lat:25.37,lon:68.36,name:"Rajasthan Arid Zone",type:"Extreme Heatwave",risk:"CRITICAL",icon:"🌡",country:"India"},
  {lat:17.38,lon:78.48,name:"Hyderabad, Telangana",type:"Flood / Cyclone",risk:"MODERATE",icon:"🌀",country:"India"},
  {lat:25.09,lon:85.31,name:"Bihar Plains",type:"Flood",risk:"HIGH",icon:"🌊",country:"India"},
  {lat:32.08,lon:77.11,name:"Himachal Pradesh",type:"Landslide",risk:"MODERATE",icon:"⛰",country:"India"},
  {lat:27.35,lon:94.22,name:"Arunachal Pradesh",type:"Flood / Landslide",risk:"HIGH",icon:"🌊",country:"India"},
  {lat:12.27,lon:76.65,name:"Karnataka South",type:"Drought / Flood",risk:"LOW",icon:"🏜",country:"India"},
  {lat:15.49,lon:73.82,name:"Goa / Konkan",type:"Coastal Flood",risk:"MODERATE",icon:"🌊",country:"India"},
  {lat:23.25,lon:77.41,name:"Madhya Pradesh",type:"Heatwave / Flood",risk:"MODERATE",icon:"🌡",country:"India"},
];

const NEIGHBOUR_ZONES=[
  {lat:23.68,lon:90.35,name:"Dhaka, Bangladesh",type:"Cyclone / Flood",risk:"HIGH",icon:"🌊",country:"Bangladesh",flag:"🇧🇩"},
  {lat:21.78,lon:92.16,name:"Cox's Bazar, Bangladesh",type:"Cyclone Storm Surge",risk:"CRITICAL",icon:"🌀",country:"Bangladesh",flag:"🇧🇩"},
  {lat:33.72,lon:73.06,name:"Islamabad, Pakistan",type:"Flood / Earthquake",risk:"HIGH",icon:"🌊",country:"Pakistan",flag:"🇵🇰"},
  {lat:25.36,lon:68.37,name:"Sindh, Pakistan",type:"Heatwave / Flood",risk:"HIGH",icon:"🌡",country:"Pakistan",flag:"🇵🇰"},
  {lat:27.70,lon:85.31,name:"Kathmandu, Nepal",type:"Earthquake / Landslide",risk:"HIGH",icon:"🏚",country:"Nepal",flag:"🇳🇵"},
  {lat:7.87,lon:80.77,name:"Sri Lanka Central",type:"Flood / Landslide",risk:"MODERATE",icon:"🌊",country:"Sri Lanka",flag:"🇱🇰"},
  {lat:16.87,lon:96.19,name:"Yangon, Myanmar",type:"Cyclone / Flood",risk:"HIGH",icon:"🌀",country:"Myanmar",flag:"🇲🇲"},
  {lat:27.47,lon:89.64,name:"Thimphu, Bhutan",type:"Landslide / Flash Flood",risk:"MODERATE",icon:"⛰",country:"Bhutan",flag:"🇧🇹"},
];

const WORLD_ZONES=[
  {lat:35.68,lon:139.69,name:"Tokyo, Japan",type:"Earthquake / Tsunami",risk:"HIGH",icon:"🏚",country:"Japan",flag:"🇯🇵"},
  {lat:-8.34,lon:115.09,name:"Bali, Indonesia",type:"Volcanic / Earthquake",risk:"HIGH",icon:"🌋",country:"Indonesia",flag:"🇮🇩"},
  {lat:14.09,lon:-87.21,name:"Central America",type:"Hurricane / Landslide",risk:"HIGH",icon:"🌀",country:"Honduras",flag:"🌎"},
  {lat:38.74,lon:-77.47,name:"Eastern USA",type:"Hurricane / Tornado",risk:"MODERATE",icon:"🌪",country:"USA",flag:"🇺🇸"},
  {lat:-33.86,lon:151.21,name:"Sydney, Australia",type:"Wildfire / Drought",risk:"MODERATE",icon:"🔥",country:"Australia",flag:"🇦🇺"},
  {lat:4.17,lon:9.22,name:"West Africa",type:"Drought / Flood",risk:"HIGH",icon:"🏜",country:"Cameroon",flag:"🌍"},
  {lat:-18.14,lon:178.44,name:"Fiji Islands",type:"Cyclone / Tsunami",risk:"HIGH",icon:"🌀",country:"Fiji",flag:"🌊"},
  {lat:37.38,lon:36.86,name:"Turkey-Syria Region",type:"Earthquake",risk:"CRITICAL",icon:"🏚",country:"Turkey",flag:"🇹🇷"},
];

const CITY_STATIONS=[
  {lat:28.61,lon:77.21,name:"Delhi"},{lat:19.07,lon:72.87,name:"Mumbai"},
  {lat:13.08,lon:80.27,name:"Chennai"},{lat:22.57,lon:88.36,name:"Kolkata"},
  {lat:17.38,lon:78.48,name:"Hyderabad"},{lat:12.97,lon:77.59,name:"Bengaluru"},
  {lat:23.02,lon:72.57,name:"Ahmedabad"},{lat:18.52,lon:73.85,name:"Pune"},
  {lat:26.91,lon:75.78,name:"Jaipur"},{lat:26.18,lon:91.73,name:"Guwahati"},
  {lat:8.52,lon:76.93,name:"Thiruvananthapuram"},{lat:22.71,lon:75.86,name:"Indore"},
  // Neighbours
  {lat:23.68,lon:90.35,name:"Dhaka"},{lat:27.70,lon:85.31,name:"Kathmandu"},
  {lat:33.72,lon:73.06,name:"Islamabad"},{lat:6.93,lon:79.85,name:"Colombo"},
];

let chatHistory=[],userLat=null,userLon=null,loading=false,isRec=false;
let selectedLang="English",allLangs=[],uiStr={};
let currentWeather=null,currentForecast=[];
let mapInstance=null,baseLayer=null,overlayLayers=[],userMarkerRef=null,zoneMarkers=[];
let currentMapType="disaster",mapRefTimer=null,mapInitialized=false;

/* ═══ BOOT ═══ */
async function initLangs(){
  try{const r=await fetch('/api/languages');const d=await r.json();allLangs=d.languages||[];uiStr=d.ui_strings||{};}
  catch(e){allLangs=[{name:"English",native:"English",code:"en",flag:"🇬🇧"}];}
}

/* ═══ AUTH ═══ */
function switchTab(t){
  document.getElementById('panelLogin').classList.toggle('on',t==='login');
  document.getElementById('panelReg').classList.toggle('on',t==='register');
  document.getElementById('tabLogin').classList.toggle('on',t==='login');
  document.getElementById('tabReg').classList.toggle('on',t==='register');
  ['lErr','rErr'].forEach(id=>{const e=document.getElementById(id);if(e)e.classList.remove('show')});
}
function togglePw(id,btn){const e=document.getElementById(id);e.type=e.type==='password'?'text':'password';btn.textContent=e.type==='password'?'👁':'🙈'}
function showErr(id,m){const e=document.getElementById(id);if(e){e.textContent=m;e.classList.add('show')}}

/* ─── GOOGLE AUTH ─── */
let _googleAuthMode='login';

function startGoogleAuth(mode){
  _googleAuthMode=mode;
  const errId=mode==='login'?'lGoogleErr':'rGoogleErr';
  const btnId=mode==='login'?'lGoogleBtn':'rGoogleBtn';
  const btn=document.getElementById(btnId);
  const errEl=document.getElementById(errId);
  errEl.classList.remove('show');
  btn.disabled=true;
  btn.querySelector('.btn-google-text').textContent='Opening Google…';

  // Google Identity Services — One Tap / popup flow
  if(typeof google==='undefined'||!google.accounts){
    errEl.textContent='Google Sign-In failed to load. Check your internet connection.';
    errEl.classList.add('show');
    btn.disabled=false;
    btn.querySelector('.btn-google-text').textContent='Continue with Google';
    return;
  }

  google.accounts.id.initialize({
    client_id: document.querySelector('meta[name="google-signin-client_id"]').content,
    callback: _handleGoogleCredential,
    auto_select: false,
    cancel_on_tap_outside: true,
  });

  google.accounts.id.prompt(notification=>{
    // If One Tap is suppressed (e.g. user dismissed before), fall back to popup
    if(notification.isNotDisplayed()||notification.isSkippedMoment()){
      _openGooglePopup(mode);
    }
  });
}

function _openGooglePopup(mode){
  // Implicit flow is deprecated by Google since 2022 — use renderButton fallback instead
  const errId = mode==='login'?'lGoogleErr':'rGoogleErr';
  const btnId = mode==='login'?'lGoogleBtn':'rGoogleBtn';
  const btn   = document.getElementById(btnId);
  const errEl = document.getElementById(errId);

  // Render Google's official button in a temporary container and click it
  const tmp = document.createElement('div');
  tmp.style.cssText = 'position:absolute;opacity:0;pointer-events:none;';
  document.body.appendChild(tmp);

  try {
    google.accounts.id.renderButton(tmp, {
      type: 'standard', theme: 'outline', size: 'large',
      callback: _handleGoogleCredential
    });
    // Trigger the rendered button click
    const inner = tmp.querySelector('[role="button"], button, div[tabindex]');
    if (inner) { inner.click(); }
    else {
      // Last resort: show a message to use One Tap
      errEl.textContent = 'Please allow the Google sign-in popup. Check if it was blocked by your browser.';
      errEl.classList.add('show');
      btn.disabled = false;
      btn.querySelector('.btn-google-text').textContent = 'Continue with Google';
    }
  } catch(e) {
    errEl.textContent = 'Google Sign-In unavailable. Please try again.';
    errEl.classList.add('show');
    btn.disabled = false;
    btn.querySelector('.btn-google-text').textContent = 'Continue with Google';
  } finally {
    setTimeout(() => tmp.remove(), 3000);
  }
}

async function _handleGoogleCredential(response){
  const mode=_googleAuthMode;
  const errId=mode==='login'?'lGoogleErr':'rGoogleErr';
  const btnId=mode==='login'?'lGoogleBtn':'rGoogleBtn';
  const btn=document.getElementById(btnId);
  const errEl=document.getElementById(errId);

  btn.querySelector('.btn-google-text').textContent='Verifying…';

  try{
    const r=await fetch('/api/google-auth',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({credential:response.credential,mode})
    });
    const d=await r.json();
    if(d.status==='success'){
      selectedLang=d.lang||'English';
      enterApp(d.name, d.is_new||false);
    } else {
      errEl.textContent=d.message||'Google sign-in failed. Please try again.';
      errEl.classList.add('show');
      btn.disabled=false;
      btn.querySelector('.btn-google-text').textContent='Continue with Google';
    }
  }catch(e){
    errEl.textContent='Network error. Please try again.';
    errEl.classList.add('show');
    btn.disabled=false;
    btn.querySelector('.btn-google-text').textContent='Continue with Google';
  }
}

// Listen for postMessage from popup redirect (fallback flow)
window.addEventListener('message',e=>{
  if(e.data&&e.data.type==='google_auth_credential'){
    _handleGoogleCredential({credential:e.data.credential});
  }
  if(e.data&&e.data.type==='google_auth_error'){
    const errId=_googleAuthMode==='login'?'lGoogleErr':'rGoogleErr';
    const btnId=_googleAuthMode==='login'?'lGoogleBtn':'rGoogleBtn';
    const errEl=document.getElementById(errId);
    const btn=document.getElementById(btnId);
    if(errEl){errEl.textContent='Google Sign-In failed. Please try again.';errEl.classList.add('show');}
    if(btn){btn.disabled=false;btn.querySelector('.btn-google-text').textContent='Continue with Google';}
  }
});

async function doLogin(){
  const email=document.getElementById('lEmail').value.trim(),pass=document.getElementById('lPass').value;
  if(!email||!pass){showErr('lErr','Fill email and password.');return}
  const btn=document.getElementById('lBtn');btn.disabled=true;btn.textContent='Signing in…';
  try{
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pass})});
    const d=await r.json();
    if(d.status==='success'){selectedLang=d.lang||'English';enterApp(d.name,false);}
    else showErr('lErr',d.message);
  }catch(e){showErr('lErr','Connection error.')}
  btn.disabled=false;btn.textContent='Sign In';
}
async function doRegister(){
  const first=document.getElementById('rFirst').value.trim(),last=document.getElementById('rLast').value.trim();
  const email=document.getElementById('rEmail').value.trim(),pass=document.getElementById('rPass').value,pass2=document.getElementById('rPass2').value;
  const phoneCode=document.getElementById('rPhoneCode').value.trim(),phoneNum=document.getElementById('rPhoneNum').value.trim();
  if(!first||!last||!email||!pass||!pass2){showErr('rErr','All fields required.');return}
  if(pass!==pass2){showErr('rErr','Passwords do not match.');return}
  if(pass.length<6){showErr('rErr','Password min 6 chars.');return}
  const phone=phoneNum?(phoneCode+phoneNum):'';
  const btn=document.getElementById('rBtn');btn.disabled=true;btn.textContent='Creating…';
  try{
    const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:first+' '+last,email,password:pass,phone})});
    const d=await r.json();
    if(d.status==='success')enterApp(d.name,true);else showErr('rErr',d.message);
  }catch(e){showErr('rErr','Connection error.')}
  btn.disabled=false;btn.textContent='Create Account';
}
async function doLogout(){
  await fetch('/api/logout',{method:'POST'});
  resetChat();
  document.getElementById('app').classList.remove('on');
  document.getElementById('authScreen').classList.remove('gone');
}
function enterApp(name,showLang){
  document.getElementById('authScreen').classList.add('gone');
  document.getElementById('app').classList.add('on');
  document.getElementById('tName').textContent=name;
  document.getElementById('tAv').textContent=name[0].toUpperCase();
  buildQuickGrid();
  applyUILang();
  const wt=document.getElementById('welcomeTitle');
  if(wt)wt.textContent=(uiStr[selectedLang]?.welcome||'Welcome')+`, ${name.split(' ')[0]}! 👋`;
  if(showLang)openLangModal();else appInit();
}
function appInit(){
  useMyLocation();loadNews();loadAlerts();
  loadGuide('flood',document.querySelector('.gnbtn'));
  // Do NOT init map here — Maps page is hidden on load.
  // initMap() is called lazily when user clicks the Maps tab (goPage).
  startClock();initScrollReveal();
}
async function checkSession(){
  try{const r=await fetch('/api/me');const d=await r.json();if(d.logged_in){selectedLang=d.lang||'English';enterApp(d.name,false);}}catch(e){}
}

/* ═══ QUICK GRID ═══ */
let activeQACard=null;
function buildQuickGrid(){
  const g=document.getElementById('quickGrid');if(!g)return;g.innerHTML='';
  QUICK_ACTIONS.forEach(a=>{
    const d=document.createElement('div');d.className='q-card';
    d.setAttribute('data-key',a.key||'flood');
    d.innerHTML=`<div class="q-ico">${a.ico}</div><div class="q-lbl">${a.lbl}</div>`;
    d.onclick=()=>toggleQADropdown(a.key||'flood',d);
    g.appendChild(d);
  });
}

/* ═══ HIGHLIGHT QUICK ACTIONS BASED ON LIVE RISK ═══ */
// Maps risk engine keys → ONLY that disaster's quick action key
const RISK_TO_QUICK={
  flood:        ['flood'],
  cyclone:      ['cyclone'],
  heatwave:     ['heatwave'],
  cold_wave:    ['winter_storm'],
  dense_fog:    ['dust_storm'],
  thunderstorm: ['lightning'],
  lightning:    ['lightning'],
};

// Track whether popup was already shown this session for the same risk level
let _lastPopupRisk='';

function highlightQuickActions(risk, weather){
  // Clear all alert classes first
  document.querySelectorAll('.q-card').forEach(c=>{
    c.classList.remove('alert-HIGH','alert-CRITICAL');
    c.removeAttribute('title');
  });
  if(!risk)return;

  // Collect keys that need highlighting based on active hazards
  const toHighlight={};  // key → highest level

  Object.entries(risk.risks||{}).forEach(([hazard, score])=>{
    if(score<2)return; // only moderate and above
    const level=score>=4?'CRITICAL':'HIGH';
    const qaKeys=RISK_TO_QUICK[hazard]||[];
    qaKeys.forEach(k=>{
      // Keep the worst level
      if(!toHighlight[k]||level==='CRITICAL')toHighlight[k]=level;
    });
  });

  // Also check rain from weather directly
  if(weather){
    const rain=weather.rain_1h||0;
    const icon=weather.icon||'';
    if(rain>=7.5||icon==='Rain'||icon==='Drizzle'){
      const lv=rain>=20?'CRITICAL':'HIGH';
      if(!toHighlight['heavy_rain']||lv==='CRITICAL')toHighlight['heavy_rain']=lv;
    }
    if(icon==='Thunderstorm'){
      if(!toHighlight['lightning'])toHighlight['lightning']='HIGH';
    }
  }

  if(!Object.keys(toHighlight).length)return;

  // Apply highlight classes and move alert cards to front
  const grid=document.getElementById('quickGrid');
  if(!grid)return;
  const cards=[...grid.querySelectorAll('.q-card')];
  cards.forEach(card=>{
    const key=card.getAttribute('data-key');
    const level=toHighlight[key];
    if(level){
      card.classList.add('alert-'+level);
      const hazardName=DISASTER_QUESTIONS[key]?.title||key;
      card.title=`⚠️ ACTIVE: ${hazardName} — ${level} risk in your area`;
    }
  });

  // Re-order: alert cards first
  const alertCards=cards.filter(c=>c.classList.contains('alert-HIGH')||c.classList.contains('alert-CRITICAL'));
  const critCards=alertCards.filter(c=>c.classList.contains('alert-CRITICAL'));
  const highCards=alertCards.filter(c=>c.classList.contains('alert-HIGH'));
  const normalCards=cards.filter(c=>!c.classList.contains('alert-HIGH')&&!c.classList.contains('alert-CRITICAL'));
  [...critCards,...highCards,...normalCards].forEach(c=>grid.appendChild(c));

  // ── Show animated disaster alert popup ──
  const worstLevel=critCards.length>0?'CRITICAL':'HIGH';
  const popupKey=worstLevel+JSON.stringify(Object.keys(toHighlight).sort());
  if(_lastPopupRisk===popupKey)return; // don't re-show same alert
  _lastPopupRisk=popupKey;

  // Collect top highlighted hazard info for popup
  const alertKeys=Object.entries(toHighlight).sort((a,b)=>(b[1]==='CRITICAL'?1:-1));
  showDisasterAlertPopup(worstLevel, alertKeys, risk, weather);
}

function showDisasterAlertPopup(level, alertKeys, risk, weather){
  const isCrit=level==='CRITICAL';
  const col=isCrit?'#ef4444':'#f97316';
  const colBg=isCrit?'rgba(239,68,68,.15)':'rgba(249,115,22,.13)';
  const colBorder=isCrit?'rgba(239,68,68,.5)':'rgba(249,115,22,.4)';
  const topQ=alertKeys[0];
  const topKey=topQ?topQ[0]:'flood';
  const topData=DISASTER_QUESTIONS[topKey]||{icon:'⚠️',title:'Disaster Alert'};

  // Style the popup header
  const popup=document.getElementById('disasterAlertPopup');
  const top=document.getElementById('dapTop');
  top.style.background=`linear-gradient(160deg,${colBg},rgba(4,12,26,.0))`;
  top.style.borderBottom=`1px solid ${colBorder}`;

  // Scan line colour
  document.getElementById('dapScan').style.background=
    `linear-gradient(90deg,transparent,${col},transparent)`;

  // Ring colours
  ['dapRing1','dapRing2'].forEach(id=>{
    const el=document.getElementById(id);
    if(el)el.style.borderColor=col;
  });

  // Icon wrap
  const iconWrap=document.getElementById('dapIconWrap');
  iconWrap.style.background=colBg;
  iconWrap.style.boxShadow=`0 0 32px ${col}55,0 0 0 2px ${col}33`;
  iconWrap.style.animation=isCrit?'critFlash 1s ease infinite':'';
  document.getElementById('dapIcon').textContent=topData.icon||'⚠️';

  // Level badge
  const lvEl=document.getElementById('dapLevel');
  lvEl.textContent=isCrit?'🔴 CRITICAL RISK DETECTED':'🟠 HIGH RISK DETECTED';
  lvEl.style.color=col;

  // Title
  document.getElementById('dapTitle').textContent=topData.title||'Disaster Alert';
  document.getElementById('dapTitle').style.color=col;

  // Location
  const loc=weather?`📍 ${weather.city||'Your location'}, ${weather.country||''}`:'📍 Your current location';
  document.getElementById('dapLoc').textContent=loc;

  // Hazard chips
  const hazEl=document.getElementById('dapHazards');
  hazEl.innerHTML=alertKeys.slice(0,5).map(([k,lv])=>{
    const d=DISASTER_QUESTIONS[k]||{icon:'⚠️',title:k};
    const c2=lv==='CRITICAL'?'#ef4444':'#f97316';
    return `<div class="dap-hazard" style="background:${c2}18;border-color:${c2}44;color:${c2};">${d.icon} ${d.title||k}</div>`;
  }).join('');

  // Button
  const btn=document.getElementById('dapBtnAsk');
  btn.style.background=`linear-gradient(135deg,${isCrit?'#dc2626,#b91c1c':'#ea580c,#c2410c'})`;
  btn.style.color='#fff';
  btn.style.boxShadow=`0 4px 18px ${col}55`;
  btn.onclick=()=>{
    dismissDisasterPopup();
    goPage('Dash');
    // Pre-fill chat with the top disaster question
    const topQ=(topData.priority||[])[0];
    if(topQ){
      setTimeout(()=>{
        const inp=document.getElementById('msgInput');
        if(inp){inp.value=topQ.text;sendMessage();}
      },400);
    }
  };

  // Show overlay + popup
  const overlay=document.getElementById('dapOverlay');
  overlay.classList.remove('hide');overlay.classList.add('show');
  popup.classList.remove('hide');popup.classList.add('show');

  // Auto-dismiss after 12s
  setTimeout(()=>dismissDisasterPopup(),12000);
}

function dismissDisasterPopup(){
  const popup=document.getElementById('disasterAlertPopup');
  const overlay=document.getElementById('dapOverlay');
  popup.classList.remove('show');popup.classList.add('hide');
  overlay.classList.remove('show');overlay.classList.add('hide');
  setTimeout(()=>{
    popup.classList.remove('hide');popup.style.display='none';
    overlay.classList.remove('hide');overlay.style.display='none';
    // Reset for next time
    popup.classList.remove('show');overlay.classList.remove('show');
    popup.style.display='';overlay.style.display='';
  },300);
}

/* ═══ INLINE QA DROPDOWN ═══ */
function toggleQADropdown(key,cardEl){
  const drop=document.getElementById('qaDropdown');
  // If same card clicked again, close
  if(activeQACard===cardEl&&drop.classList.contains('open')){closeQADropdown();return;}
  // Mark active card
  document.querySelectorAll('.q-card').forEach(c=>c.classList.remove('active'));
  cardEl.classList.add('active');
  activeQACard=cardEl;
  const data=DISASTER_QUESTIONS[key];
  if(!data)return;
  document.getElementById('qaDropIco').textContent=data.icon;
  document.getElementById('qaDropTitle').textContent=data.title;
  // Build priority questions list — top 5 only
  const list=document.getElementById('qaOptsList');
  list.innerHTML='';
  const topQ=data.priority||[];
  topQ.forEach((q,i)=>{
    const opt=document.createElement('div');
    opt.className='qa-opt';
    opt.style.animation=`qaOptIn .28s cubic-bezier(.16,1,.3,1) ${i*0.055}s both`;
    opt.innerHTML=`<span class="qa-opt-ico">${q.ico}</span><span class="qa-opt-text">${q.text}</span><span class="qa-opt-arrow">→</span>`;
    opt.onclick=()=>{
      closeQADropdown();
      document.getElementById('msgInput').value=q.text;
      sendMessage();
    };
    list.appendChild(opt);
  });
  // Open with animation
  drop.classList.remove('closing');
  drop.classList.add('open');
  // Scroll so dropdown is visible
  setTimeout(()=>{drop.scrollIntoView({behavior:'smooth',block:'nearest'});},50);
}
function closeQADropdown(){
  const drop=document.getElementById('qaDropdown');
  drop.classList.add('closing');
  setTimeout(()=>{drop.classList.remove('open','closing');},220);
  document.querySelectorAll('.q-card').forEach(c=>c.classList.remove('active'));
  activeQACard=null;
}

/* ═══ LANGUAGE ═══ */
function buildLangGrid(filter=''){
  const g=document.getElementById('langGrid');g.innerHTML='';
  (filter?allLangs.filter(l=>l.name.toLowerCase().includes(filter.toLowerCase())||l.native.includes(filter)):allLangs).forEach(l=>{
    const btn=document.createElement('div');btn.className='lang-btn'+(l.name===selectedLang?' sel':'');
    btn.innerHTML=`<span class="lang-name">${l.flag} ${l.name}</span><span class="lang-native">${l.native}</span>`;
    btn.onclick=()=>{document.querySelectorAll('.lang-btn').forEach(b=>b.classList.remove('sel'));btn.classList.add('sel');selectedLang=l.name;};
    g.appendChild(btn);
  });
}
function filterLangs(v){buildLangGrid(v)}
function openLangModal(){buildLangGrid();document.getElementById('langSearch').value='';document.getElementById('langModal').classList.add('show');}
async function confirmLang(){
  document.getElementById('langModal').classList.remove('show');
  await fetch('/api/set-lang',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lang:selectedLang})});
  applyUILang();appInit();
}
function applyUILang(){
  const s=uiStr[selectedLang]||uiStr['English']||{};
  const l=allLangs.find(x=>x.name===selectedLang)||{code:'en'};
  document.getElementById('langChip').textContent=l.code.toUpperCase();
  const m={'dashboard':'nt-dash','alerts':'nt-alerts','guidelines':'nt-guide','maps':'nt-maps','live':'navLive','signout':'navSignout','shelter':'nt-shelter'};
  Object.entries(m).forEach(([k,id])=>{if(s[k]){const e=document.getElementById(id);if(e)e.textContent=s[k];}});
  const mi=document.getElementById('msgInput');if(mi&&s.askme)mi.placeholder=s.askme;
}

/* ═══ CLOCK ═══ */
function startClock(){setInterval(()=>{const e=document.getElementById('clockEl');if(e)e.textContent=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});},1000);}

/* ═══ PAGE NAV ═══ */
function goPage(id){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.mobile-nav-btn').forEach(t=>t.classList.remove('on'));
  const pg=document.getElementById('page'+id);
  if(pg)pg.classList.add('on');
  // Desktop nav
  const idx={Dash:0,Alerts:1,Guide:2,Maps:3,Shelter:4};
  const tabs=document.querySelectorAll('.nav-tab');
  if(tabs[idx[id]!==undefined?idx[id]:0])tabs[idx[id]!==undefined?idx[id]:0].classList.add('on');
  // Mobile bottom nav
  const mBtn=document.getElementById('mn-'+id);
  if(mBtn)mBtn.classList.add('on');
  if(id==='Alerts')loadAlerts();
  if(id==='Maps'){
    if(!mapInitialized)initMap();
    else{startMapRefresh();setTimeout(()=>{if(mapInstance)mapInstance.invalidateSize();},300);}
  }
  if(id==='Shelter'){
    if(!shelterMapInstance){initShelterMap();}
    else{setTimeout(()=>{if(shelterMapInstance)shelterMapInstance.invalidateSize();},300);}
  }
  // On mobile, scroll to top of page
  window.scrollTo({top:0,behavior:'smooth'});
}

/* ═══ SCROLL REVEAL ═══ */
let revealObserver=null;
function initScrollReveal(){
  if(revealObserver)return;
  revealObserver=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');revealObserver.unobserve(e.target);}});
  },{threshold:0.1,rootMargin:'0px 0px -30px 0px'});
  document.querySelectorAll('.reveal,.g-item,.ac').forEach(el=>revealObserver.observe(el));
}
function observeNew(el){if(revealObserver)revealObserver.observe(el);}

/* ═══ WEATHER ═══ */
function updateWeather(w,r,fc){
  if(!w||w.error)return;
  currentWeather=w;currentForecast=fc||[];
  document.getElementById('wSec').style.display='block';
  document.getElementById('wCity').textContent=w.city;
  document.getElementById('wCo').textContent=w.country;
  document.getElementById('wTemp').innerHTML=`${w.temp}<sup>°C</sup>`;
  document.getElementById('wIco').textContent=WICO[w.icon]||'🌤';
  document.getElementById('wDesc').textContent=w.desc;
  document.getElementById('wFeels').textContent=`Feels like ${w.feels_like}°C`;
  document.getElementById('wH').textContent=`${w.humidity}%`;
  document.getElementById('wW').textContent=`${w.wind_speed} m/s`;
  document.getElementById('wV').textContent=`${(w.visibility/1000).toFixed(1)} km`;
  document.getElementById('wP').textContent=`${w.pressure} hPa`;
  document.getElementById('wTime').textContent=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});
  document.getElementById('mapLoc').textContent=`${w.city}, ${w.country}`;
  document.getElementById('mapCoords').textContent=`${(w.lat||0).toFixed(2)}°N ${(w.lon||0).toFixed(2)}°E`;
  document.getElementById('mapTemp').textContent=`${w.temp}°C`;
  document.getElementById('mapTempR').textContent=`Min ${w.temp_min}° / Max ${w.temp_max}°`;
  document.getElementById('mapWind').textContent=`${w.wind_speed} m/s`;
  document.getElementById('mapWindD').textContent=`Dir: ${w.wind_deg}°`;
  document.getElementById('mapHumid').textContent=`${w.humidity}%`;
  updateTVBar(w,fc);
  if(r){updateRisk(r);document.getElementById('mapRisk').textContent=r.overall;}
  if(mapInstance&&w.lat)placeUserMarker(w.lat,w.lon,w,r);
  // Highlight quick action cards based on active risk
  highlightQuickActions(r,w);
}
function updateTVBar(w,fc){
  document.getElementById('tvLoc').textContent=`${w.city}, ${w.country}`;
  document.getElementById('tvTime').textContent=new Date().toLocaleString('en-IN',{weekday:'short',hour:'2-digit',minute:'2-digit'});
  document.getElementById('tvTemp').innerHTML=`${w.temp}<sup>°C</sup>`;
  document.getElementById('tvIco').textContent=WICO[w.icon]||'🌤';
  document.getElementById('tvDesc').textContent=w.desc;
  document.getElementById('tvFeels').textContent=`Feels ${w.feels_like}°C · ${w.temp_min}°–${w.temp_max}°`;
  document.getElementById('tvHumid').textContent=`${w.humidity}%`;
  document.getElementById('tvWind').textContent=w.wind_speed;
  document.getElementById('tvVis').textContent=(w.visibility/1000).toFixed(1);
  document.getElementById('tvRain').textContent=w.rain_1h;
  document.getElementById('tvPress').textContent=w.pressure;
  document.getElementById('tvFc').innerHTML=(fc||[]).slice(0,6).map(f=>`<div class="tv-fc"><div class="tv-fc-t">${f.time}</div><div class="tv-fc-i">${WICO[f.icon]||'🌤'}</div><div class="tv-fc-temp">${Math.round(f.temp)}°</div>${f.pop>0?`<div class="tv-fc-pop">💧${f.pop}%</div>`:''}</div>`).join('');
}

/* ═══ RISK BOX ═══ */
function updateRisk(r){
  const col=({NORMAL:'#4ade80',LOW:'#38bdf8',MODERATE:'#fcd34d',HIGH:'#f97316',CRITICAL:'#ef4444'})[r.overall]||'#4ade80';
  const rgb=RISK_COL_RGB[r.overall]||'74,222,128';
  const box=document.getElementById('sqRiskBox');
  ['lv-NORMAL','lv-LOW','lv-MODERATE','lv-HIGH','lv-CRITICAL'].forEach(c=>box.classList.remove(c));
  box.classList.add('lv-'+r.overall);
  box.style.setProperty('--gc-rgb',rgb);
  document.getElementById('sqLevel').textContent=r.overall;
  document.getElementById('sqLevel').style.color=col;
  const sb=document.getElementById('sqBadge');
  sb.textContent=`${r.max_score}/5`;
  sb.style.color=col;sb.style.borderColor=`rgba(${rgb},.3)`;sb.style.background=`rgba(${rgb},.08)`;
  const active=Object.entries(r.risks).filter(([,v])=>v>0);
  document.getElementById('sqSub').textContent=active.length?`${active.length} Active Hazard${active.length>1?'s':''}`:' No active hazards';
  document.getElementById('gaugeScore').textContent=`${r.max_score}/5`;
  const dotColors={1:'#38bdf8',2:'#fcd34d',3:'#f97316',4:'#f97316',5:'#ef4444'};
  for(let i=1;i<=5;i++){
    const d=document.getElementById('sqd'+i);
    if(r.max_score>=i){d.classList.add('lit');d.style.background=dotColors[i]||col;d.style.boxShadow=`0 0 6px ${dotColors[i]||col}`;}
    else{d.classList.remove('lit');d.style.background='';d.style.boxShadow='';}
  }
  const el=document.getElementById('riskMeters');el.innerHTML='';
  Object.entries(r.risks).forEach(([k,v])=>{
    const m=RISK_META[k]||{icon:'⚠️',l:k};
    const d=document.createElement('div');d.className=`rm s${v}`;
    d.innerHTML=`<div class="rm-h"><div class="rm-n"><span>${m.icon}</span>${m.l}</div><span class="rm-s">${v}/5</span></div><div class="rm-t"><div class="rm-f"></div></div>`;
    el.appendChild(d);
  });
}

function useMyLocation(){
  if(!navigator.geolocation)return;
  navigator.geolocation.getCurrentPosition(p=>{
    userLat=p.coords.latitude;userLon=p.coords.longitude;
    fetch('/weather',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:userLat,lon:userLon})})
      .then(r=>r.json()).then(d=>updateWeather(d.weather,d.risk,d.forecast));
  });
}
function loadCity(){
  const c=document.getElementById('cityInput').value.trim();if(!c)return;
  userLat=null;userLon=null;
  fetch('/weather',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city:c})})
    .then(r=>r.json()).then(d=>updateWeather(d.weather,d.risk,d.forecast));
}

/* ═══ MAPS — GOOGLE MAPS IMPLEMENTATION ═══ */
function addZoneCSS(){
  if(document.getElementById('zoneCSS'))return;
  const s=document.createElement('style');s.id='zoneCSS';
  s.textContent=`
    .zp-outer{border-radius:50%;border:1.5px solid;position:absolute;animation:zpulse 2.2s ease-out infinite;top:0;left:0;right:0;bottom:0}
    .zp-inner{border-radius:50%;border:1.5px dashed;position:absolute;animation:zpulse 2.2s ease-out .5s infinite;top:0;left:0;right:0;bottom:0}
    .leaflet-popup-content-wrapper{background:rgba(4,21,38,.97)!important;border:1px solid rgba(13,148,136,.35)!important;border-radius:6px!important;color:#dff4ff!important;}
    .leaflet-popup-tip{background:rgba(4,21,38,.97)!important;}
    .leaflet-popup-content{margin:10px 14px;font-size:11px;line-height:1.6;color:#dff4ff;}
    .leaflet-container{background:#020c1b!important;}
  `;
  document.head.appendChild(s);
}

function initMap(){
  if(mapInitialized||!document.getElementById('leafletMap'))return;
  addZoneCSS();
  mapInitialized=true;
  mapInstance=L.map('leafletMap',{
    center:[20.59,78.96],zoom:4,
    zoomControl:true,attributionControl:false,preferCanvas:true,
  });
  L.control.attribution({position:'bottomright',prefix:''}).addTo(mapInstance);
  applyMapMode('disaster');
  hideMapLoading();
  if(userLat&&currentWeather)placeUserMarker(userLat,userLon,currentWeather,null);
  startMapRefresh();
}

function hideMapLoading(){
  const el=document.getElementById('mapLoading');
  if(el){el.classList.add('done');setTimeout(()=>{el.style.display='none';},500);}
}

function clearMapLayers(){
  overlayLayers.forEach(l=>{try{mapInstance.removeLayer(l);}catch(e){}});
  overlayLayers=[];
  zoneMarkers.forEach(m=>{try{mapInstance.removeLayer(m);}catch(e){}});
  zoneMarkers=[];
  document.getElementById('tvBar').style.display='none';
}

function applyMapMode(mode){
  if(!mapInstance)return;
  currentMapType=mode;
  clearMapLayers();
  if(baseLayer){try{mapInstance.removeLayer(baseLayer);}catch(e){}}
  const badge=document.getElementById('mapModeBadge');

  if(mode==='disaster'){
    baseLayer=L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© CARTO',subdomains:'abcd',maxZoom:19}).addTo(mapInstance);
    badge.className='map-mode-badge disaster';badge.textContent='🚨 Live Disaster Alerts';
    updateLegend('disaster');
    const statEl=document.getElementById('mapRisk');
    statEl.textContent='Loading…';
    statEl.style.color='var(--fg2)';

    fetch('/api/gdacs-events')
      .then(r=>r.json())
      .then(data=>{
        // Abort if user switched away while fetching
        if(currentMapType!=='disaster'||!mapInstance)return;
        const events=data.events||[];

        if(!events.length){
          statEl.textContent='NO EVENTS';
          statEl.style.color='var(--emerald3)';
          const ic=L.divIcon({className:'',iconSize:[300,34],iconAnchor:[150,17],
            html:'<div style="background:rgba(2,12,27,.95);border:1px solid rgba(16,185,129,.4);border-radius:4px;padding:6px 14px;font-family:monospace;font-size:10px;color:#6ee7b7;text-align:center;">No active disaster events reported by GDACS right now</div>'});
          zoneMarkers.push(L.marker([20,0],{icon:ic}).addTo(mapInstance));
          return;
        }

        const hasRed=events.some(function(e){return e.alert==='Red';});
        const hasOrange=events.some(function(e){return e.alert==='Orange';});
        statEl.textContent=hasRed?'CRITICAL':hasOrange?'HIGH':'ACTIVE';
        statEl.style.color=hasRed?'#ef4444':hasOrange?'#f97316':'#22d3ee';

        const SZ={Red:20,Orange:16,Green:11};
        const SPEED={Red:'1s',Orange:'1.6s',Green:'3s'};

        events.forEach(function(ev){
          if(!mapInstance)return;
          var col=ev.color||'#22d3ee';
          var sz=SZ[ev.alert]||11;
          var speed=SPEED[ev.alert]||'3s';
          var dotSize=sz+'px';
          var boxSize=(sz*5)+'px';
          var fontSize=Math.round(sz*0.65)+'px';
          var glowSize=(sz*1.5)+'px';

          var iconHtml='<div style="width:'+boxSize+';height:'+boxSize+';position:relative;display:flex;align-items:center;justify-content:center;">'
            +'<div style="position:absolute;inset:0;border-radius:50%;border:1.5px solid '+col+';animation:zpulse '+speed+' ease-out infinite;"></div>'
            +'<div style="position:absolute;inset:0;border-radius:50%;border:1.5px dashed '+col+';animation:zpulse '+speed+' ease-out 0.5s infinite;"></div>'
            +'<div style="width:'+dotSize+';height:'+dotSize+';border-radius:3px;background:'+col+';box-shadow:0 0 '+glowSize+' '+col+';display:flex;align-items:center;justify-content:center;font-size:'+fontSize+';transform:rotate(45deg);position:relative;z-index:2;">'
            +'<span style="transform:rotate(-45deg);display:block;">'+ev.icon+'</span>'
            +'</div></div>';

          var icon=L.divIcon({className:'',iconSize:[sz*5,sz*5],iconAnchor:[sz*2.5,sz*2.5],html:iconHtml});
          var popupHtml='<div style="min-width:230px;max-width:290px;">'
            +'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding-bottom:7px;border-bottom:1px solid rgba(255,255,255,.1);">'
            +'<span style="font-size:22px;">'+ev.icon+'</span>'
            +'<div style="flex:1;"><div style="font-family:Rajdhani,sans-serif;font-size:14px;font-weight:700;color:'+col+';">'+ev.name+'</div>'
            +'<div style="font-size:8px;font-family:monospace;color:#94a3b8;">'+(ev.country?ev.country+' · ':'')+ev.date+'</div></div>'
            +'<span style="background:'+col+'22;border:1px solid '+col+'55;color:'+col+';padding:2px 7px;border-radius:2px;font-family:monospace;font-weight:700;font-size:10px;">'+ev.alert.toUpperCase()+'</span>'
            +'</div>'
            +'<div style="font-size:10px;color:#dff4ff;font-family:monospace;line-height:1.5;margin-bottom:7px;">'+ev.description+'</div>'
            +'<div style="font-size:8px;color:#64748b;font-family:monospace;margin-bottom:5px;">Source: GDACS (UN/EU) · Live</div>'
            +(ev.url?'<a href="'+ev.url+'" target="_blank" style="font-size:9px;color:#38bdf8;font-family:monospace;">Full Report</a>':'')
            +'</div>';

          var m=L.marker([ev.lat,ev.lon],{icon:icon}).addTo(mapInstance);
          m.bindPopup(popupHtml);
          zoneMarkers.push(m);
        });

        // Summary bar
        var rc=events.filter(function(e){return e.alert==='Red';}).length;
        var oc=events.filter(function(e){return e.alert==='Orange';}).length;
        var gc=events.filter(function(e){return e.alert==='Green';}).length;
        var parts=[];
        if(rc)parts.push('<span style="color:#ef4444;font-weight:700">Red: '+rc+'</span>');
        if(oc)parts.push('<span style="color:#f97316;font-weight:700">Orange: '+oc+'</span>');
        if(gc)parts.push('<span style="color:#22d3ee;font-weight:700">Green: '+gc+'</span>');
        var sumHtml='<div style="background:rgba(2,12,27,.95);border:1px solid rgba(255,255,255,.1);border-radius:4px;padding:4px 12px;font-family:monospace;font-size:9px;color:#94a3b8;text-align:center;">'+parts.join(' &nbsp;·&nbsp; ')+' &nbsp;·&nbsp; GDACS Live</div>';
        var sumIc=L.divIcon({className:'',iconSize:[300,26],iconAnchor:[150,13],html:sumHtml});
        zoneMarkers.push(L.marker([-55,0],{icon:sumIc,zIndexOffset:1000,interactive:false}).addTo(mapInstance));

        // Fit bounds
        try{
          var lats=events.map(function(e){return e.lat;});
          var lons=events.map(function(e){return e.lon;});
          mapInstance.fitBounds([[Math.min.apply(null,lats)-8,Math.min.apply(null,lons)-8],[Math.max.apply(null,lats)+8,Math.max.apply(null,lons)+8]],{padding:[40,40],maxZoom:4});
        }catch(e){mapInstance.setView([20,0],2);}
      })
      .catch(function(err){
        console.error('[GDACS]',err);
        if(currentMapType==='disaster'){statEl.textContent='FEED ERROR';statEl.style.color='var(--rose3)';}
      });

  }else if(mode==='weather'){
    const loadEl=document.getElementById('mapLoading');
    if(loadEl){loadEl.style.display='flex';loadEl.classList.remove('done');}
    baseLayer=L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',{attribution:'© CARTO',subdomains:'abcd',maxZoom:19}).addTo(mapInstance);
    const addOWM=(layer,op)=>{const t=L.tileLayer(`https://tile.openweathermap.org/map/${layer}/{z}/{x}/{y}.png?appid=${OWM_KEY}`,{opacity:op,maxZoom:19});t.on('tileerror',()=>{});t.addTo(mapInstance);overlayLayers.push(t);};
    addOWM('temp_new',.75);addOWM('precipitation_new',.6);addOWM('clouds_new',.3);addOWM('wind_new',.4);
    const tLbl=L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png',{subdomains:'abcd',opacity:.75}).addTo(mapInstance);
    overlayLayers.push(tLbl);
    CITY_STATIONS.forEach(city=>{
      fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${city.lat}&lon=${city.lon}&appid=${OWM_KEY}&units=metric`)
        .then(r=>r.json()).then(d=>{
          if(!d.main)return;
          const t=Math.round(d.main.temp);
          const tc=t>=40?'#ef4444':t>=35?'#f97316':t>=28?'#fcd34d':t>=20?'#4ade80':t>=10?'#38bdf8':'#818cf8';
          const ci=L.divIcon({className:'',iconSize:[68,24],iconAnchor:[34,12],html:`<div style="background:rgba(4,21,38,.92);border:1px solid ${tc}44;border-radius:3px;padding:2px 5px;font-family:monospace;font-size:9px;white-space:nowrap;"><span style="color:${tc};font-weight:700">${t}°</span> ${WICO[d.weather[0].main]||'🌤'} <span style="color:#64748b;font-size:8px">${city.name}</span></div>`});
          const m=L.marker([city.lat,city.lon],{icon:ci,zIndexOffset:100}).addTo(mapInstance);
          m.bindTooltip(`<strong>${city.name}</strong><br>🌡 ${t}°C | 💧 ${d.main.humidity}%`,{direction:'top'});
          zoneMarkers.push(m);
        }).catch(()=>{});
    });
    document.getElementById('tvBar').style.display='block';
    badge.className='map-mode-badge weather';badge.textContent='🌦 TV Weather Live';
    updateLegend('weather');
    setTimeout(hideMapLoading,3500);

  }else if(mode==='risk'){
    baseLayer=L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© CARTO',subdomains:'abcd',maxZoom:19}).addTo(mapInstance);
    const tWind=L.tileLayer(`https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${OWM_KEY}`,{opacity:.45}).addTo(mapInstance);
    overlayLayers.push(tWind);
    badge.className='map-mode-badge risk';badge.textContent='📊 Live Risk Analysis';
    updateLegend('risk');
    const statEl=document.getElementById('mapRisk');
    statEl.textContent='Loading…';

    // ── Fetch live weather risk for major Indian cities ──
    fetch('/api/india-weather-risk')
      .then(r=>r.json())
      .then(data=>{
        const cities=data.cities||[];
        let maxLevel='NORMAL';
        const riskOrder={NORMAL:0,LOW:1,MODERATE:2,HIGH:3,CRITICAL:4};

        if(!cities.length){
          statEl.textContent='NORMAL';
          statEl.style.color='var(--emerald3)';
          const ic=L.divIcon({className:'',iconSize:[280,34],iconAnchor:[140,17],
            html:`<div style="background:rgba(2,12,27,.95);border:1px solid rgba(16,185,129,.4);border-radius:4px;padding:6px 14px;font-family:monospace;font-size:10px;color:#6ee7b7;text-align:center;">✅ No HIGH/CRITICAL weather risk across major Indian cities</div>`});
          zoneMarkers.push(L.marker([22,80],{icon:ic}).addTo(mapInstance));
          setTimeout(hideMapLoading,500);
          return;
        }

        cities.forEach(city=>{
          if(riskOrder[city.level]>riskOrder[maxLevel])maxLevel=city.level;
          const col=city.color||'#f97316';
          const isRed=city.level==='CRITICAL';
          const speed=isRed?'1s':'1.8s';
          const sz=isRed?20:15;
          const radiusKm=isRed?200:150;

          const blob=L.circle([city.lat,city.lon],{radius:radiusKm*1000,fillColor:col,color:col,fillOpacity:.07,weight:.8,opacity:.25}).addTo(mapInstance);
          const core=L.circle([city.lat,city.lon],{radius:radiusKm*400,fillColor:col,color:'transparent',fillOpacity:.13}).addTo(mapInstance);

          const hazardStr=city.hazards.map(h=>`${h.icon} ${h.label} <strong style="color:${col}">${h.score}/5</strong>`).join('<br>');

          const dotIcon=L.divIcon({className:'',iconSize:[sz*5,sz*5],iconAnchor:[sz*2.5,sz*2.5],
            html:`<div style="width:${sz*5}px;height:${sz*5}px;position:relative;display:flex;align-items:center;justify-content:center">
              <div class="zp-outer" style="border-color:${col};animation-duration:${speed}"></div>
              <div class="zp-inner" style="border-color:${col};animation-duration:${speed}"></div>
              <div style="width:${sz}px;height:${sz}px;border-radius:3px;background:${col};opacity:.95;box-shadow:0 0 ${sz*1.5}px ${col};display:flex;align-items:center;justify-content:center;font-size:${Math.round(sz*.65)}px;position:relative;z-index:2;transform:rotate(45deg)">
                <span style="transform:rotate(-45deg)">⚠️</span>
              </div>
            </div>`});

          const dot=L.marker([city.lat,city.lon],{icon:dotIcon}).addTo(mapInstance);
          dot.bindPopup(`<div style="min-width:220px;">
            <div style="font-family:Rajdhani,sans-serif;font-size:16px;font-weight:700;color:${col};margin-bottom:5px;">📍 ${city.name}</div>
            <div style="display:inline-block;background:${col}22;border:1px solid ${col}55;color:${col};padding:2px 9px;border-radius:2px;font-family:monospace;font-weight:700;font-size:11px;margin-bottom:8px;">${city.level} RISK</div>
            <div style="font-size:9px;color:#94a3b8;font-family:monospace;margin-bottom:6px;">🌡 ${city.temp}°C · 💧 ${city.humidity}% · 💨 ${city.wind} m/s${city.rain>0?` · 🌧 ${city.rain}mm`:''}</div>
            <div style="font-size:9px;color:#64748b;font-family:monospace;margin-bottom:4px;font-style:italic;">${city.desc}</div>
            ${city.hazards.length?`<div style="font-size:9px;color:#dff4ff;font-family:monospace;line-height:2;border-top:1px solid rgba(255,255,255,.08);padding-top:6px;"><strong style="color:${col};">Active Hazards:</strong><br>${hazardStr}</div>`:''}
            <div style="font-size:7px;color:#475569;font-family:monospace;margin-top:6px;">Source: OpenWeatherMap live</div>
          </div>`);
          zoneMarkers.push(blob,core,dot);
        });

        statEl.textContent=maxLevel;
        statEl.style.color=RCOLORS[maxLevel]||'var(--emerald3)';
        setTimeout(hideMapLoading,500);
      })
      .catch(()=>{
        statEl.textContent='ERROR';
        statEl.style.color='var(--rose3)';
        setTimeout(hideMapLoading,500);
      });
  }

  if(userMarkerRef){try{mapInstance.removeLayer(userMarkerRef);}catch(e){}}
  if(userLat&&currentWeather)placeUserMarker(userLat,userLon,currentWeather,null);
}

function addZoneMarker(z,type){
  const col=RCOLORS[z.risk]||'#eab308';
  const sz={CRITICAL:20,HIGH:16,MODERATE:13,LOW:11,NORMAL:9}[z.risk]||13;
  const speed={CRITICAL:'1s',HIGH:'1.6s',MODERATE:'2.2s',LOW:'3s'}[z.risk]||'2.2s';
  const icon=L.divIcon({className:'',iconSize:[sz*5,sz*5],iconAnchor:[sz*2.5,sz*2.5],
    html:`<div style="width:${sz*5}px;height:${sz*5}px;position:relative;display:flex;align-items:center;justify-content:center"><div class="zp-outer" style="border-color:${col};animation-duration:${speed}"></div><div class="zp-inner" style="border-color:${col};animation-duration:${speed}"></div><div style="width:${sz}px;height:${sz}px;border-radius:3px;background:${col};opacity:.95;box-shadow:0 0 ${sz*1.5}px ${col};display:flex;align-items:center;justify-content:center;font-size:${Math.round(sz*.65)}px;position:relative;z-index:2;transform:rotate(45deg)"><span style="transform:rotate(-45deg)">${type==='world'?'🌍':(z.flag||z.icon)}</span></div></div>`});
  const m=L.marker([z.lat,z.lon],{icon}).addTo(mapInstance);
  m.bindPopup(`<div style="min-width:190px"><div style="display:flex;align-items:center;gap:7px;margin-bottom:6px">${z.flag?`<span style="font-size:18px">${z.flag}</span>`:''}<div><div style="font-family:Rajdhani,sans-serif;font-size:15px;font-weight:700;color:${col}">${z.name}</div>${z.country?`<div style="font-size:9px;color:#64748b;font-family:monospace">${z.country}</div>`:''}</div></div><div style="font-size:10px;color:#94a3b8;margin-bottom:5px;font-family:monospace">⚠️ ${z.type}</div><span style="background:${col}22;border:1px solid ${col}55;color:${col};padding:2px 8px;border-radius:2px;font-family:monospace;font-weight:700;font-size:10px">${z.risk}</span>${type==='world'?'<span style="font-size:8px;color:#f59e0b;font-family:monospace;margin-left:5px;padding:1px 5px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:2px">WORLD</span>':''}${type==='neighbour'?'<span style="font-size:8px;color:#a78bfa;font-family:monospace;margin-left:5px;padding:1px 5px;background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.2);border-radius:2px">NEIGHBOUR</span>':''}</div>`);
  zoneMarkers.push(m);
}

function updateLegend(mode){
  const legends={
    disaster:`<div class="ml-title">Live Alerts</div>
      <div class="ml-item"><div class="ml-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444"></div>🔴 Red — Critical danger</div>
      <div class="ml-item"><div class="ml-dot" style="background:#f97316;box-shadow:0 0 6px #f97316"></div>🟠 Orange — Serious hazard</div>
      <div class="ml-item"><div class="ml-dot" style="background:#22d3ee"></div>🟢 Green — Active, monitor</div>
      <div style="margin-top:7px;padding-top:7px;border-top:1px solid rgba(255,255,255,.08);font-size:8px;color:#475569;font-family:monospace">📡 Source: GDACS (UN/EU)</div>
      <div style="margin-top:3px;font-size:8px;color:#475569;font-family:monospace">Real coordinates · Live data</div>`,
    weather:`<div class="ml-title">Weather Layers</div>
      <div class="ml-item"><div class="ml-sq" style="background:linear-gradient(135deg,#ef4444,#f97316)"></div>High Temp Zone</div>
      <div class="ml-item"><div class="ml-sq" style="background:linear-gradient(135deg,#3b82f6,#06b6d4)"></div>Low Temp Zone</div>
      <div class="ml-item"><div class="ml-sq" style="background:linear-gradient(135deg,#7c3aed,#1d4ed8)"></div>Heavy Rain</div>
      <div class="ml-item"><div class="ml-sq" style="background:rgba(255,255,255,.3)"></div>Cloud Cover</div>
      <div class="ml-item"><div class="ml-line" style="background:linear-gradient(90deg,#38bdf8,transparent)"></div>Wind Patterns</div>
      <div class="ml-item"><div class="ml-dot" style="background:#38bdf8"></div>City Stations</div>
      <div class="ml-item"><div class="ml-dot" style="background:#4ade80;box-shadow:0 0 6px #4ade80"></div>📍 Your Location</div>`,
    risk:`<div class="ml-title">Live Risk Zones</div>
      <div class="ml-item"><div class="ml-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444"></div>Critical — weather risk ≥4/5</div>
      <div class="ml-item"><div class="ml-dot" style="background:#f97316"></div>High — weather risk ≥3/5</div>
      <div style="margin-top:7px;padding-top:7px;border-top:1px solid rgba(255,255,255,.08);font-size:8px;color:#475569;font-family:monospace">Source: OpenWeatherMap live data</div>
      <div style="margin-top:4px;font-size:8px;color:#475569;font-family:monospace">MODERATE/LOW/NORMAL hidden</div>`
  };
  document.getElementById('mapLegend').innerHTML=legends[mode]||'';
}

function switchMap(el,mode){
  document.querySelectorAll('.map-tab').forEach(t=>t.classList.remove('on'));
  el.classList.add('on');
  if(mode!=='disaster'){
    const loadEl=document.getElementById('mapLoading');
    if(loadEl){loadEl.style.display='flex';loadEl.classList.remove('done');}
  }
  applyMapMode(mode);startMapRefresh();
}

function startMapRefresh(){
  if(mapRefTimer)clearInterval(mapRefTimer);
  triggerRefBar();
  mapRefTimer=setInterval(()=>{
    if(currentMapType==='weather')applyMapMode('weather');
    triggerRefBar();updateMapRefTime();
  },300000);
  updateMapRefTime();
}
function triggerRefBar(){
  const f=document.getElementById('rfFill');if(!f)return;
  f.classList.remove('active');void f.offsetWidth;f.classList.add('active');
}
function updateMapRefTime(){const e=document.getElementById('mapRefT');if(e)e.textContent=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});}

function placeUserMarker(lat,lon,w,r){
  if(!mapInstance)return;
  if(userMarkerRef){try{mapInstance.removeLayer(userMarkerRef);}catch(e){}}
  const col=r?RCOLORS[r.overall]||'#4ade80':'#4ade80';
  const icon=L.divIcon({className:'',iconSize:[34,34],iconAnchor:[17,17],
    html:`<div style="width:34px;height:34px;position:relative;display:flex;align-items:center;justify-content:center"><div style="position:absolute;inset:0;border:1.5px solid ${col};border-radius:4px;animation:zpulse 2s ease-out infinite;opacity:.5"></div><div style="width:14px;height:14px;border-radius:3px;background:${col};box-shadow:0 0 14px ${col};border:2px solid rgba(255,255,255,.9);position:relative;z-index:2;transform:rotate(45deg)"></div></div>`});
  userMarkerRef=L.marker([lat,lon],{icon,zIndexOffset:1000}).addTo(mapInstance);
  userMarkerRef.bindPopup(`<div style="min-width:175px"><div style="font-family:Rajdhani,sans-serif;font-size:14px;font-weight:700;color:${col}">📍 ${w.city}, ${w.country}</div><div style="font-size:10px;color:#94a3b8;margin:4px 0">🌡 ${w.temp}°C · Feels ${w.feels_like}°C</div><div style="font-size:10px;color:#94a3b8">💨 ${w.wind_speed} m/s | 💧 ${w.humidity}%</div>${r?`<div style="font-size:11px;font-weight:700;color:${col};margin-top:5px;border-top:1px solid rgba(255,255,255,.08);padding-top:4px">🚨 Risk: ${r.overall}</div>`:''}</div>`);
  if(currentMapType!=='risk')mapInstance.setView([lat,lon],7,{animate:true,duration:1.2});
}

/* ═══ NEWS — REGION-SORTED ═══ */
async function loadNews(){
  document.getElementById('newsBox').innerHTML='<div class="news-empty">Fetching official sources…</div>';
  try{
    const r=await fetch('/api/news');const d=await r.json();renderNewsSorted(d.news||[]);
  }catch(e){document.getElementById('newsBox').innerHTML='<div class="news-empty">Failed. Check connection.</div>';}
}

function getAlertLevel(text){
  const t=text.toLowerCase();
  if(t.includes('critical')||t.includes('red alert')||t.includes('extreme'))return'critical';
  if(t.includes('warning')||t.includes('severe')||t.includes('high')||t.includes('cyclone')||t.includes('tsunami'))return'high';
  if(t.includes('watch')||t.includes('moderate')||t.includes('flood')||t.includes('storm'))return'moderate';
  return'low';
}
function getDisasterType(text){
  const t=text.toLowerCase();
  if(t.includes('cyclone')||t.includes('hurricane')||t.includes('typhoon'))return{ico:'🌀',label:'CYCLONE'};
  if(t.includes('flood'))return{ico:'🌊',label:'FLOOD'};
  if(t.includes('earthquake')||t.includes('seismic'))return{ico:'🏚',label:'EARTHQUAKE'};
  if(t.includes('tsunami'))return{ico:'🌊',label:'TSUNAMI'};
  if(t.includes('drought'))return{ico:'🏜',label:'DROUGHT'};
  if(t.includes('fire')||t.includes('wildfire'))return{ico:'🔥',label:'WILDFIRE'};
  if(t.includes('landslide'))return{ico:'⛰',label:'LANDSLIDE'};
  if(t.includes('heat'))return{ico:'🌡',label:'HEATWAVE'};
  if(t.includes('volcano')||t.includes('eruption'))return{ico:'🌋',label:'VOLCANIC'};
  return{ico:'⚠️',label:'DISASTER'};
}
function isIndiaRelated(item){
  const loc=detectLocationFromText((item.title||'')+' '+(item.desc||'')+' '+(item.source||''));
  return loc.isIndia||(loc.country==='India');
}

function renderNewsSorted(items){
  const el=document.getElementById('newsBox');
  if(!items.length){el.innerHTML='<div class="news-empty">No news from official sources.</div>';return;}
  const india=items.filter(isIndiaRelated);
  const world=items.filter(i=>!isIndiaRelated(i));
  el.innerHTML='';
  if(india.length){
    const hdr=document.createElement('div');hdr.className='news-region-hdr';
    hdr.innerHTML=`<span class="news-region-flag">🇮🇳</span><span class="news-region-label india">INDIA</span><span class="news-region-count india">${india.length} alerts</span>`;
    el.appendChild(hdr);
    india.forEach((n,i)=>el.appendChild(createNewsItem(n,i,'india')));
  }
  if(world.length){
    const hdr2=document.createElement('div');hdr2.className='news-region-hdr';
    hdr2.innerHTML=`<span class="news-region-flag">🌍</span><span class="news-region-label world">WORLD</span><span class="news-region-count world">${world.length} alerts</span>`;
    el.appendChild(hdr2);
    world.forEach((n,i)=>el.appendChild(createNewsItem(n,i,'world')));
  }
}

function createNewsItem(n,i,region){
  const div=document.createElement('div');
  div.className=`ni ${region==='world'?'world-item':''}`;
  div.style.animationDelay=`${i*0.05}s`;
  const level=getAlertLevel(n.title+(n.desc||''));
  const dtype=getDisasterType(n.title+(n.desc||''));
  const loc=detectLocationFromText((n.title||'')+' '+(n.desc||''));
  const isIndia=region==='india';
  const areaDisplay=loc.region||(isIndia?'India':'International');
  const flagDisplay=loc.flag||(isIndia?'🇮🇳':'🌍');
  div.innerHTML=`
    <div class="ni-location">
      <span class="ni-flag">${flagDisplay}</span>
      <span class="ni-geo ${isIndia?'india-geo':'world-geo'}">${areaDisplay}</span>
    </div>
    <div class="ni-alert-type ${level}">${dtype.ico} ${dtype.label}</div>
    <div class="ni-title">${n.title}</div>
    ${n.desc?`<div class="ni-desc">${n.desc.substring(0,130)}${n.desc.length>130?'…':''}</div>`:''}
    <div class="ni-src"><span class="ni-source">${n.source}</span><span class="ni-date">${n.date||''}</span></div>
  `;
  if(n.link)div.onclick=()=>window.open(n.link,'_blank');
  return div;
}

/* ═══ LOCATION INTELLIGENCE ═══ */

// Comprehensive country database with flags for accurate detection
const COUNTRY_FLAGS={
  'Indonesia':'🇮🇩','Philippines':'🇵🇭','Japan':'🇯🇵','China':'🇨🇳',
  'Turkey':'🇹🇷','Syria':'🇸🇾','Iran':'🇮🇷','Iraq':'🇮🇶',
  'Pakistan':'🇵🇰','Bangladesh':'🇧🇩','Nepal':'🇳🇵','Sri Lanka':'🇱🇰',
  'Myanmar':'🇲🇲','Bhutan':'🇧🇹','Maldives':'🇲🇻','Afghanistan':'🇦🇫',
  'Papua New Guinea':'🇵🇬','Vanuatu':'🇻🇺','Fiji':'🇫🇯','Solomon Islands':'🇸🇧',
  'Tonga':'🇹🇴','Samoa':'🇼🇸','New Zealand':'🇳🇿','Australia':'🇦🇺',
  'Vietnam':'🇻🇳','Thailand':'🇹🇭','Malaysia':'🇲🇾','Cambodia':'🇰🇭',
  'Laos':'🇱🇦','Taiwan':'🇹🇼','South Korea':'🇰🇷','North Korea':'🇰🇵',
  'Russia':'🇷🇺','Ukraine':'🇺🇦','Greece':'🇬🇷','Italy':'🇮🇹',
  'Mexico':'🇲🇽','Guatemala':'🇬🇹','El Salvador':'🇸🇻','Honduras':'🇭🇳',
  'Costa Rica':'🇨🇷','Colombia':'🇨🇴','Peru':'🇵🇪','Ecuador':'🇪🇨',
  'Chile':'🇨🇱','Argentina':'🇦🇷','Brazil':'🇧🇷','Haiti':'🇭🇹',
  'Yemen':'🇾🇪','Somalia':'🇸🇴','Ethiopia':'🇪🇹','Sudan':'🇸🇩',
  'Morocco':'🇲🇦','Algeria':'🇩🇿','Libya':'🇱🇾','Egypt':'🇪🇬',
  'USA':'🇺🇸','United States':'🇺🇸','Canada':'🇨🇦','France':'🇫🇷',
  'Spain':'🇪🇸','Portugal':'🇵🇹','Germany':'🇩🇪','UK':'🇬🇧',
  'Kenya':'🇰🇪','Tanzania':'🇹🇿','Madagascar':'🇲🇬','Mozambique':'🇲🇿',
  'Zimbabwe':'🇿🇼','Malawi':'🇲🇼','Zambia':'🇿🇲','Congo':'🇨🇩',
  'West Papua':'🇮🇩','Sulawesi':'🇮🇩','Sumatra':'🇮🇩','Java':'🇮🇩',
  'Lombok':'🇮🇩','Timor':'🇮🇩','Celebes':'🇮🇩','Borneo':'🇲🇾',
  'Luzon':'🇵🇭','Mindanao':'🇵🇭','Visayas':'🇵🇭',
  'Hokkaido':'🇯🇵','Honshu':'🇯🇵','Kyushu':'🇯🇵',
  'Anatolia':'🇹🇷','Aegean':'🇬🇷','Caucasus':'🇬🇪',
};

// India states and cities for detection
const INDIA_PLACES_SET=new Set([
  'india','indian','assam','odisha','kerala','maharashtra','tamil','karnataka',
  'gujarat','rajasthan','bengal','bihar','uttarakhand','himachal','jammu','kashmir',
  'telangana','andhra','punjab','haryana','uttar pradesh','madhya pradesh','jharkhand',
  'chhattisgarh','manipur','nagaland','mizoram','tripura','meghalaya','arunachal',
  'sikkim','goa','delhi','mumbai','chennai','kolkata','hyderabad','bengaluru',
  'ahmedabad','jaipur','pune','surat','lucknow','guwahati','bhopal','patna',
  'bhubaneswar','visakhapatnam','vizag','kochi','thiruvananthapuram','chandigarh',
  'ndma','imd','ndrf','emri','imf india','relief india',
]);

function detectLocationFromText(text){
  if(!text)return{country:null,region:null,isIndia:false,flag:'🌍'};
  const raw=text;
  const tl=text.toLowerCase();

  // 1. Check for explicit India mentions first
  if(tl.includes('india')){
    // Extract specific Indian state from text
    const indiaState=extractIndiaState(raw);
    return{country:'India',region:indiaState||'India',isIndia:true,flag:indiaState?'🇮🇳':'🇮🇳'};
  }
  for(const place of INDIA_PLACES_SET){
    if(tl.includes(place)&&place!=='india'){
      return{country:'India',region:capitalizeFirst(place),isIndia:true,flag:'🇮🇳'};
    }
  }

  // 2. Check for known non-India countries — these are WORLD alerts
  for(const [country,flag] of Object.entries(COUNTRY_FLAGS)){
    if(raw.includes(country)||tl.includes(country.toLowerCase())){
      // Extract sub-region if possible (e.g. "in Sulawesi, Indonesia")
      const subRegion=extractSubRegion(raw,country);
      return{country,region:subRegion||country,isIndia:false,flag};
    }
  }

  // 3. Pattern: "in [PLACE]" — grab the word after "in"
  const inMatch=raw.match(/\bin\s+([A-Z][a-zA-Z\s\-]{2,28}?)(?:\s*[,.(]|$)/);
  if(inMatch){
    const place=inMatch[1].trim();
    if(place&&place!=='India')return{country:place,region:place,isIndia:false,flag:'🌍'};
    if(place==='India')return{country:'India',region:'India',isIndia:true,flag:'🇮🇳'};
  }

  return{country:null,region:null,isIndia:false,flag:'🌍'};
}

function extractIndiaState(text){
  const stateMap={
    'Assam':'Assam','Odisha':'Odisha','Kerala':'Kerala','Maharashtra':'Maharashtra',
    'Tamil Nadu':'Tamil Nadu','Gujarat':'Gujarat','Rajasthan':'Rajasthan',
    'West Bengal':'West Bengal','Bihar':'Bihar','Uttarakhand':'Uttarakhand',
    'Himachal Pradesh':'Himachal Pradesh','Jammu':'Jammu & Kashmir',
    'Kashmir':'Jammu & Kashmir','Karnataka':'Karnataka','Telangana':'Telangana',
    'Andhra Pradesh':'Andhra Pradesh','Punjab':'Punjab','Haryana':'Haryana',
    'Uttar Pradesh':'Uttar Pradesh','Madhya Pradesh':'Madhya Pradesh',
    'Jharkhand':'Jharkhand','Chhattisgarh':'Chhattisgarh','Manipur':'Manipur',
    'Arunachal':'Arunachal Pradesh','Meghalaya':'Meghalaya','Nagaland':'Nagaland',
    'Mizoram':'Mizoram','Tripura':'Tripura','Sikkim':'Sikkim','Goa':'Goa',
    'Delhi':'Delhi','Mumbai':'Maharashtra','Chennai':'Tamil Nadu',
    'Kolkata':'West Bengal','Hyderabad':'Telangana','Bengaluru':'Karnataka',
    'Ahmedabad':'Gujarat','Jaipur':'Rajasthan','Pune':'Maharashtra',
  };
  for(const [k,v] of Object.entries(stateMap)){if(text.includes(k))return v;}
  return null;
}

function extractSubRegion(text,country){
  // e.g. "in Sulawesi, Indonesia" → "Sulawesi"
  const re=new RegExp(`([A-Z][a-zA-Z\\s\\-]{2,20}),\\s*${country}`,'i');
  const m=text.match(re);
  if(m)return m[1].trim()+', '+country;
  return null;
}

function capitalizeFirst(s){return s.charAt(0).toUpperCase()+s.slice(1);}

function extractAreaFromText(text){
  const loc=detectLocationFromText(text);
  return loc.region||'';
}
function extractLocation(text){
  const loc=detectLocationFromText(text);
  return loc.region||'';
}

/* ═══ ALERTS PAGE — REGION-SORTED ═══ */
async function loadAlerts(){
  document.getElementById('alertsScroll').innerHTML='<div style="padding:60px;text-align:center;font-size:12px;color:var(--fg3);font-family:var(--mono)">Fetching verified alerts from official channels…</div>';
  try{
    const r=await fetch('/api/alerts');const d=await r.json();renderAlertsSorted(d.alerts||[]);
  }catch(e){document.getElementById('alertsScroll').innerHTML='<div style="padding:40px;text-align:center;color:var(--rose3);font-family:var(--mono);font-size:11px">Failed to load.</div>';}
}

const STATE_FLAGS={'Tamil Nadu':'🌊','Odisha':'🌀','West Bengal':'🌊','Maharashtra':'🌧',
  'Kerala':'🌊','Assam':'🌊','Bihar':'🌊','Uttarakhand':'⛰','Himachal Pradesh':'⛰',
  'Rajasthan':'🌡','Andhra Pradesh':'🌀','Gujarat':'🌀','Karnataka':'🌧','Telangana':'🌊','India':'🇮🇳'};

function renderAlertsSorted(alerts){
  const el=document.getElementById('alertsScroll');el.innerHTML='';
  if(!alerts.length){
    el.innerHTML='<div style="padding:60px;text-align:center;font-size:13px;color:var(--emerald2);font-family:var(--mono)">✅ No critical alerts from official sources at this time.</div>';
    return;
  }
  // Re-classify every alert by parsing actual message content
  const enriched=alerts.map(a=>{
    const loc=detectLocationFromText((a.message||'')+(a.title||''));
    return{...a,_loc:loc};
  });
  const indiaAlerts=enriched.filter(a=>a._loc.isIndia||(a._loc.country==='India'));
  const worldAlerts=enriched.filter(a=>!a._loc.isIndia&&a._loc.country!=='India');

  if(indiaAlerts.length){
    const sep=document.createElement('div');sep.className='alerts-region-sep india-sep';
    sep.innerHTML=`<span class="ars-icon">🇮🇳</span><span class="ars-title india">India Alerts</span><span class="ars-count india">${indiaAlerts.length} verified</span><span class="ars-line"></span>`;
    el.appendChild(sep);
    const grid=document.createElement('div');grid.className='alerts-section-body';
    indiaAlerts.forEach((a,i)=>grid.appendChild(createAlertCard(a,i,'india')));
    el.appendChild(grid);
  }
  if(worldAlerts.length){
    const sep2=document.createElement('div');sep2.className='alerts-region-sep world-sep';
    sep2.innerHTML=`<span class="ars-icon">🌍</span><span class="ars-title world">Global Alerts</span><span class="ars-count world">${worldAlerts.length} verified</span><span class="ars-line world"></span>`;
    el.appendChild(sep2);
    const grid2=document.createElement('div');grid2.className='alerts-section-body';
    worldAlerts.forEach((a,i)=>grid2.appendChild(createAlertCard(a,i,'world')));
    el.appendChild(grid2);
  }
  // If nothing classified to India, everything goes to world section
  if(!indiaAlerts.length&&!worldAlerts.length&&enriched.length){
    const sep3=document.createElement('div');sep3.className='alerts-region-sep world-sep';
    sep3.innerHTML=`<span class="ars-icon">🌍</span><span class="ars-title world">Global Alerts</span><span class="ars-count world">${enriched.length} verified</span><span class="ars-line world"></span>`;
    el.appendChild(sep3);
    const grid3=document.createElement('div');grid3.className='alerts-section-body';
    enriched.forEach((a,i)=>grid3.appendChild(createAlertCard(a,i,'world')));
    el.appendChild(grid3);
  }
  setTimeout(()=>{document.querySelectorAll('.ac').forEach(el=>observeNew(el));initScrollReveal();},100);
}

function createAlertCard(a,i,region){
  const card=document.createElement('div');
  card.className=`ac ${a.level||'MODERATE'} reveal`;
  card.style.transitionDelay=`${i*0.06}s`;
  card.style.animationDelay=`${i*0.06}s`;

  // Use parsed location — never blindly trust backend's "India" for all
  const loc=a._loc||detectLocationFromText(a.message||'');
  const isIndia=region==='india';
  const flag=isIndia?(loc.flag||'🇮🇳'):(loc.flag||'🌍');
  const displayRegion=loc.region||(isIndia?'India':'International');
  const countryLine=isIndia?'🇮🇳 India':`${loc.flag||'🌍'} ${loc.country||'International'}`;
  const dtype=getDisasterType(a.message||a.type||'');
  const level=a.level||'MODERATE';

  card.innerHTML=`
    <div class="ac-accent"></div>
    <div class="ac-inner">
      <div class="ac-location-row">
        <div class="ac-location-left">
          <div class="ac-flag-big">${flag}</div>
          <div class="ac-geo-info">
            <div class="ac-state-name">${displayRegion}</div>
            <div class="ac-country-name">${countryLine}</div>
          </div>
        </div>
        <div class="ac-lvl-badge">${level}</div>
      </div>
      <div class="ac-type-row">
        <div class="ac-type-badge">${dtype.ico} ${dtype.label}</div>
        ${!isIndia?`<div style="font-size:7px;font-family:var(--mono);color:var(--amber3);padding:1px 5px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:2px;letter-spacing:.5px">GLOBAL</div>`:''}
      </div>
      <div class="ac-msg">${a.message||''}</div>
      <div class="ac-foot">
        <span class="ac-source">✅ ${a.issued||'Official'}</span>
        ${a.link?`<a class="ac-link" href="${a.link}" target="_blank" onclick="event.stopPropagation()">View →</a>`:''}
      </div>
    </div>
  `;
  if(a.link)card.onclick=()=>window.open(a.link,'_blank');
  return card;
}

/* ═══ GUIDELINES ═══ */
async function loadGuide(type,btn){
  document.querySelectorAll('.gnbtn').forEach(b=>b.classList.remove('on'));
  if(btn)btn.classList.add('on');
  const el=document.getElementById('guideContent');
  el.innerHTML='<div style="padding:28px;color:var(--fg3);font-family:var(--mono);font-size:10px">Loading…</div>';
  try{
    const r=await fetch(`/api/guidelines/${type}`);const g=await r.json();
    if(g.error){el.innerHTML=`<div style="padding:20px;color:var(--rose3);font-family:var(--mono)">Not found: ${type}</div>`;return;}
    el.innerHTML=`<h1 class="g-title">${g.title}</h1><div class="g-src">Source: ${g.source}</div>${gSec(g.before,'before','📋 Before','var(--sky3)')}${gSec(g.during,'during','⚡ During','var(--rose3)')}${gSec(g.after,'after','✅ After','var(--emerald3)')}`;
    el.querySelectorAll('.g-item').forEach((item,i)=>{setTimeout(()=>{item.classList.add('visible');},i*45+50);observeNew(item);});
  }catch(e){el.innerHTML='<div style="padding:20px;color:var(--rose3);font-family:var(--mono)">Failed to load.</div>';}
}
function gSec(items,cls,label,col){
  if(!items||!items.length)return'';
  return`<div class="g-section"><div class="g-sec-ttl" style="color:${col}">${label}</div><div class="g-items">${items.map((item,i)=>`<div class="g-item ${cls}" style="transition-delay:${i*0.04}s"><span class="g-item-n">${String(i+1).padStart(2,'0')}</span><span>${item}</span></div>`).join('')}</div></div>`;
}

/* ═══ CHAT ═══ */
function clearWelcome(){const w=document.getElementById('welcomeEl');if(w)w.remove();}
function addMsg(text,role){
  clearWelcome();
  const box=document.getElementById('msgBox');
  const now=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});
  const row=document.createElement('div');row.className=`mrow ${role}`;
  const av=document.createElement('div');av.className=`mav ${role}`;av.textContent=role==='user'?(document.getElementById('tAv').textContent||'U'):'🛡';
  const body=document.createElement('div');body.className='mbody';
  const meta=document.createElement('div');meta.className='mmeta';meta.textContent=role==='user'?`YOU · ${now}`:`RAKSHA · ${now}`;
  const bub=document.createElement('div');bub.className=`mbub ${role}`;bub.textContent=text;
  body.appendChild(meta);body.appendChild(bub);row.appendChild(av);row.appendChild(body);
  box.appendChild(row);box.scrollTop=box.scrollHeight;
}
function showAB(r){
  if(!r||r.overall==='NORMAL')return;
  const box=document.getElementById('msgBox');
  const active=Object.entries(r.risks).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).map(([k,v])=>{const m=RISK_META[k]||{icon:'⚠️',l:k};return`${m.icon} ${m.l.padEnd(14)} ${'█'.repeat(v)}${'░'.repeat(5-v)} ${v}/5`;}).join('\n');
  const b=document.createElement('div');b.className=`abanner ${r.overall}`;
  b.innerHTML=`<div class="ab-t">🚨 NDMA — ${r.overall}</div><pre>${active}</pre>`;
  box.appendChild(b);box.scrollTop=box.scrollHeight;
}
function showTyping(){
  clearWelcome();
  const box=document.getElementById('msgBox');
  const r=document.createElement('div');r.className='trow';r.id='trow';
  r.innerHTML=`<div class="mav bot">🛡</div><div class="tbub"><div class="td"></div><div class="td"></div><div class="td"></div></div>`;
  box.appendChild(r);box.scrollTop=box.scrollHeight;
}
function hideTyping(){const t=document.getElementById('trow');if(t)t.remove();}
async function sendMessage(){
  if(loading)return;
  const inp=document.getElementById('msgInput');const text=inp.value.trim();if(!text)return;
  loading=true;document.getElementById('sendBtn').disabled=true;
  inp.value='';inp.style.height='';
  addMsg(text,'user');chatHistory.push({role:'user',content:text});showTyping();
  const body={message:text,history:chatHistory.slice(-8)};
  if(userLat){body.lat=userLat;body.lon=userLon;}
  else if(currentWeather&&currentWeather.city){
    // No GPS location but user searched a city — send it so the backend uses it
    body.city=currentWeather.city;
    // Also send coords from weather so weather context is accurate
    if(currentWeather.lat&&currentWeather.lon){
      body.lat=currentWeather.lat;
      body.lon=currentWeather.lon;
    }
  }
  try{
    const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await res.json();hideTyping();
    if(data.risk&&data.risk.overall!=='NORMAL')showAB(data.risk);
    if(data.weather)updateWeather(data.weather,data.risk,currentForecast);
    addMsg(data.reply||'⚠️ No response.','bot');
    chatHistory.push({role:'assistant',content:data.reply});
  }catch(e){hideTyping();addMsg('⚠️ Connection error: '+e.message,'bot');}
  loading=false;document.getElementById('sendBtn').disabled=false;
}
function sq(t){goPage('Dash');document.getElementById('msgInput').value=t;sendMessage();}
function handleKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}}
function autoResize(el){el.style.height='';el.style.height=Math.min(el.scrollHeight,85)+'px';}
function resetChat(){chatHistory=[];const b=document.getElementById('msgBox');if(b)b.innerHTML=`<div class="welcome"><div class="w-em">🛡</div><div class="w-title">RAKSHA</div></div>`;}

/* ═══ VOICE ═══ */
const LANG_SPEECH_CODES={
  'English':'en-IN','Tamil':'ta-IN','Hindi':'hi-IN','Telugu':'te-IN',
  'Malayalam':'ml-IN','Kannada':'kn-IN','Bengali':'bn-IN','Marathi':'mr-IN',
  'Gujarati':'gu-IN','Punjabi':'pa-IN','Odia':'or-IN','Assamese':'as-IN',
  'Urdu':'ur-IN','Sanskrit':'sa-IN','Nepali':'ne-IN',
};

function startVoice(){
  const Rec=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!Rec){showToast('Voice not supported. Use Chrome or Edge.','error',4000);return;}
  if(isRec)return;

  const btn=document.getElementById('voiceBtn');
  const inp=document.getElementById('msgInput');
  isRec=true;
  btn.classList.add('rec');
  btn.textContent='⏹';
  inp.placeholder='🎤 Listening…';

  const rec=new Rec();
  rec.lang=LANG_SPEECH_CODES[selectedLang]||'en-IN';
  rec.continuous=false;
  rec.interimResults=false;
  rec.maxAlternatives=1;

  let resultReceived=false;

  rec.onresult=function(e){
    resultReceived=true;
    const transcript=e.results[0][0].transcript.trim();
    const confidence=Math.round(e.results[0][0].confidence*100);
    if(transcript){
      inp.value=transcript;
      inp.placeholder='Ask me anything in your language…';
      // Small delay so user can see what was transcribed before it sends
      setTimeout(()=>sendMessage(),300);
    }
  };

  rec.onend=function(){
    isRec=false;
    btn.classList.remove('rec');
    btn.textContent='🎤';
    inp.placeholder='Ask me anything in your language…';
    if(!resultReceived){
      showToast('No speech detected. Try again.','info',2500);
    }
  };

  rec.onerror=function(e){
    isRec=false;
    btn.classList.remove('rec');
    btn.textContent='🎤';
    inp.placeholder='Ask me anything in your language…';
    const errMap={
      'not-allowed':'Microphone access denied. Allow mic in browser settings.',
      'no-speech':'No speech detected. Try again.',
      'network':'Network error. Check your connection.',
      'audio-capture':'No microphone found.',
      'aborted':'Voice input cancelled.',
    };
    const msg=errMap[e.error]||'Voice error: '+e.error;
    showToast(msg,'warning',4000);
  };

  try{
    rec.start();
  }catch(e){
    isRec=false;
    btn.classList.remove('rec');
    btn.textContent='🎤';
    showToast('Could not start voice: '+e.message,'error');
  }
}

/* ═══ SHELTER FINDER ENGINE — Google Maps ═══ */
let shelterMapInstance=null,shelterUserMarker=null,shelterMarkers=[];
let shelterDirectionsRenderer=null,shelterDirectionsService=null,shelterDistanceService=null;
let allShelters=[],filteredShelters=[];
let shelterUserLat=null,shelterUserLon=null;
let currentShelterRadius=5000,currentShelterFilter='all',shelterSortMode='distance';
let selectedShelterCard=null;

const SHELTER_META={
  school:          {icon:'🏫',label:'School / College',   color:'#14b8a6',capacity:'1000–3000 people',  priority:'HIGH'},
  hospital:        {icon:'🏥',label:'Hospital / Medical', color:'#f43f5e',capacity:'100–500 beds',      priority:'CRITICAL'},
  community_centre:{icon:'🏛',label:'Community Hall',      color:'#7c3aed',capacity:'2000–5000 people',  priority:'HIGH'},
  place_of_worship:{icon:'🛕',label:'Religious Site',      color:'#f59e0b',capacity:'1000–3000 people',  priority:'MODERATE'},
  government:      {icon:'🏢',label:'Govt Building',       color:'#0ea5e9',capacity:'500–800 people',    priority:'HIGH'},
  default:         {icon:'🏠',label:'Shelter',             color:'#10b981',capacity:'Varies',            priority:'MODERATE'},
};

function haversineKm(lat1,lon1,lat2,lon2){
  const R=6371,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180;
  const a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}

function fmtDist(km){return km<1?Math.round(km*1000)+' m':km.toFixed(1)+' km';}
function fmtTime(sec){if(sec<60)return Math.round(sec)+'s';if(sec<3600)return Math.round(sec/60)+' min';return(sec/3600).toFixed(1)+' hr';}

function initShelterMap(){
  if(shelterMapInstance)return;
  shelterMapInstance=L.map('shelterMap',{center:[20.59,78.96],zoom:13,zoomControl:true,attributionControl:false,preferCanvas:true});
  L.control.attribution({position:'bottomright',prefix:''}).addTo(shelterMapInstance);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© CARTO',subdomains:'abcd',maxZoom:19}).addTo(shelterMapInstance);
}

async function initShelterPage(){
  if(!shelterMapInstance)initShelterMap();
  const overlay=document.getElementById('shelterMapOverlay');
  if(overlay)overlay.style.display='none';
  document.getElementById('shelterLoading').style.display='flex';
  document.getElementById('shelterList').style.display='none';
  document.getElementById('shelterCount').textContent='Detecting location…';
  navigator.geolocation.getCurrentPosition(async pos=>{
    shelterUserLat=pos.coords.latitude;
    shelterUserLon=pos.coords.longitude;
    if(shelterUserMarker){try{shelterMapInstance.removeLayer(shelterUserMarker);}catch(e){}}
    const uIcon=L.divIcon({className:'',iconSize:[28,28],iconAnchor:[14,14],
      html:`<div style="width:28px;height:28px;display:flex;align-items:center;justify-content:center;position:relative;"><div style="position:absolute;inset:0;border:2px solid #4ade80;border-radius:50%;animation:zpulse 2s ease-out infinite;opacity:.5;"></div><div style="width:12px;height:12px;border-radius:50%;background:#4ade80;border:2px solid #fff;box-shadow:0 0 10px #4ade80;"></div></div>`});
    shelterUserMarker=L.marker([shelterUserLat,shelterUserLon],{icon:uIcon,zIndexOffset:2000}).addTo(shelterMapInstance);
    shelterUserMarker.bindPopup('<div style="font-family:Rajdhani,sans-serif;font-size:14px;font-weight:700;color:#4ade80;">📍 Your Location</div>');
    shelterMapInstance.setView([shelterUserLat,shelterUserLon],14,{animate:true});
    // Fresh location — clear the shelter cache so we start clean
    _shelterCache=new Map();
    await fetchNearbyShelters();
  },err=>{
    document.getElementById('shelterLoading').innerHTML=`<div style="font-family:var(--mono);font-size:10px;color:var(--rose3);text-align:center;padding:20px;">Location access denied.<br>Enable location in browser settings.<br><br><button onclick="initShelterPage()" style="padding:7px 14px;background:var(--teal);border:none;border-radius:2px;color:#fff;font-family:var(--mono);font-size:10px;cursor:pointer;margin-top:8px;">Try Again</button></div>`;
  },{enableHighAccuracy:true,timeout:12000});
}

async function fetchNearbyShelters(){
  document.getElementById('shelterCount').textContent='Finding nearby shelters…';
  document.getElementById('shelterLoading').style.display='flex';
  document.getElementById('shelterList').style.display='none';
  const r=currentShelterRadius;
  const lat=shelterUserLat,lon=shelterUserLon;

  // ── Strategy 1: Nominatim (fast, reliable, no API key) ──
  try{
    document.getElementById('shelterCount').textContent='Searching via OpenStreetMap…';
    const controller=new AbortController();
    const tid=setTimeout(()=>controller.abort(),20000);
    const resp=await fetch('/api/nearby-shelters',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lat,lon,radius:r}),
      signal:controller.signal
    });
    clearTimeout(tid);
    if(resp.ok){
      const data=await resp.json();
      if(data.elements&&data.elements.length>0){
        processShelterData(data.elements);
        return;
      }
    }
  }catch(e){console.warn('[Nominatim]',e);}

  // ── Strategy 2: Overpass fallback (tries mirrors + Nominatim internally) ──
  const query=`[out:json][timeout:25];(node["amenity"~"school|hospital|community_centre|place_of_worship|fire_station|police|clinic|college|townhall|university"](around:${r},${lat},${lon});way["amenity"~"school|hospital|community_centre|place_of_worship|fire_station|police|clinic|college|townhall|university"](around:${r},${lat},${lon}););out center tags;`;
  for(let attempt=1;attempt<=2;attempt++){
    try{
      document.getElementById('shelterCount').textContent=attempt===1?'Trying alternate source…':`Retrying (${attempt}/2)…`;
      const controller=new AbortController();
      const tid=setTimeout(()=>controller.abort(),25000);
      const resp=await fetch('/api/overpass',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query}),signal:controller.signal});
      clearTimeout(tid);
      if(!resp.ok)throw new Error(`HTTP ${resp.status}`);
      const data=await resp.json();
      if(data.error)throw new Error(data.error);
      if(data.elements&&data.elements.length>0){processShelterData(data.elements);return;}
    }catch(e){
      if(attempt<2)await new Promise(res=>setTimeout(res,1500));
    }
  }

  // ── All failed ──
  document.getElementById('shelterLoading').innerHTML=`
    <div style="font-family:var(--mono);font-size:11px;color:var(--rose3);text-align:center;padding:30px 20px;">
      <div style="font-size:32px;margin-bottom:12px;">⚠️</div>
      <div style="font-weight:700;margin-bottom:8px;color:var(--fg);">Could not load shelters</div>
      <div style="font-size:9px;color:var(--fg3);margin-bottom:16px;">Check your internet connection and try again.</div>
      <button onclick="fetchNearbyShelters()" style="padding:9px 16px;background:linear-gradient(135deg,var(--teal),var(--sky));border:none;border-radius:2px;color:#fff;font-family:var(--display);font-size:12px;font-weight:600;cursor:pointer;letter-spacing:1px;text-transform:uppercase;">🔄 Try Again</button>
    </div>`;
  document.getElementById('shelterLoading').style.display='flex';
  document.getElementById('shelterList').style.display='none';
}

// Persistent shelter cache — survives radius changes
// Key: "lat_lon_name", Value: shelter object
let _shelterCache = new Map();

function _buildShelterFromElement(el){
  const elLat=el.lat||(el.center&&el.center.lat);
  const elLon=el.lon||(el.center&&el.center.lon);
  if(!elLat||!elLon)return null;
  const tags=el.tags||{};
  const name=tags.name||null;
  if(!name)return null;
  const am=tags.amenity||'';const bld=tags.building||'';const off=tags.office||'';
  let metaKey='default';
  if(am==='school'||bld==='school'||am==='college'||am==='university')metaKey='school';
  else if(am==='hospital'||am==='clinic'||am==='doctors')metaKey='hospital';
  else if(am==='community_centre'||am==='townhall')metaKey='community_centre';
  else if(am==='place_of_worship')metaKey='place_of_worship';
  else if(bld==='civic'||bld==='government'||off==='government'||am==='fire_station'||am==='police')metaKey='government';
  const meta={...SHELTER_META[metaKey],key:metaKey};
  const distKm=haversineKm(shelterUserLat,shelterUserLon,elLat,elLon);
  const amenities=[];
  if(tags.toilets==='yes')amenities.push('🚻 Toilets');
  if(tags.drinking_water==='yes')amenities.push('💧 Water');
  if(tags.wheelchair==='yes')amenities.push('♿ Accessible');
  if(amenities.length===0)amenities.push('Contact for details');
  return {
    id:el.id, lat:elLat, lon:elLon, name, meta, distKm, tags,
    walkMin:null, driveMin:null, gmLoaded:false,
    address: tags.full_address
             || [tags['addr:street'],tags['addr:city']].filter(Boolean).join(', ')
             || '',
    phone:   tags.phone || tags['contact:phone'] || '',
    website: tags.website || tags['contact:website'] || '',
    email:   tags.email  || tags['contact:email']  || '',
    openHours:  tags.opening_hours || '24/7 during emergencies',
    // Real OSM capacity preferred; fall back to type-based estimate
    capacity:   tags.capacity
                ? tags.capacity + (isNaN(tags.capacity)?'':' people')
                : meta.capacity,
    operatedBy: tags.operator || 'Local Authority / NDMA',
    wheelchair: tags.wheelchair || 'unknown',
    amenities,
  };
}

function processShelterData(elements){
  // 1. Add new elements to the persistent cache (never remove existing ones)
  elements.forEach(el=>{
    const s=_buildShelterFromElement(el);
    if(!s)return;
    const key=`${Math.round(s.lat*1000)}_${Math.round(s.lon*1000)}_${s.name}`;
    if(!_shelterCache.has(key)){
      _shelterCache.set(key,s);
    }
  });

  // 2. Rebuild allShelters from cache — only those within current radius
  const radiusKm=currentShelterRadius/1000;
  allShelters=[];
  _shelterCache.forEach(s=>{
    // Recalculate distance in case user location changed
    s.distKm=haversineKm(shelterUserLat,shelterUserLon,s.lat,s.lon);
    if(s.distKm<=radiusKm+0.3)allShelters.push(s);
  });

  allShelters.sort((a,b)=>a.distKm-b.distKm);
  filteredShelters=[...allShelters];

  // 3. Clear all map markers and re-add from allShelters
  shelterMarkers.forEach(m=>{try{shelterMapInstance.removeLayer(m);}catch(e){}});
  shelterMarkers=[];
  clearShelterRoute();

  allShelters.forEach(s=>addShelterMarker(s));
  applyShelterFilter(currentShelterFilter);
  document.getElementById('shelterLoading').style.display='none';
  document.getElementById('shelterList').style.display='block';
  document.getElementById('shelterCount').textContent=`${allShelters.length} shelters within ${radiusKm} km — loading road distances…`;
  _loadGMDistances();
}

async function _loadGMDistances(){
  if(!shelterUserLat||!allShelters.length)return;

  // ── Single call: OSRM Table API (driving) — returns drive distance + walk estimate ──
  try{
    const resp=await fetch('/api/osrm-table',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        user_lat:shelterUserLat,user_lon:shelterUserLon,
        shelters:allShelters.map(s=>({id:s.id,lat:s.lat,lon:s.lon}))
      })
    });
    if(resp.ok){
      const data=await resp.json();
      (data.results||[]).forEach(r=>{
        const s=allShelters.find(x=>String(x.id)===String(r.id));
        if(s&&r.drive_m>0){
          s.distKm=r.drive_m/1000;
          s.driveMin=r.drive_sec!=null?Math.round(r.drive_sec/60):null;
          s.walkMin=r.walk_sec!=null?Math.round(r.walk_sec/60):null;
          s.gmLoaded=true;
        }
      });
    }
  }catch(e){console.warn('[OSRM Table]',e);}

  if(shelterSortMode==='distance'){
    filteredShelters.sort((a,b)=>a.distKm-b.distKm);
    allShelters.sort((a,b)=>a.distKm-b.distKm);
  }
  renderShelterList(filteredShelters);
  document.getElementById('shelterCount').textContent=`${allShelters.length} shelters found — road distances loaded ✓`;
}

function addShelterMarker(s){
  const ic=L.divIcon({className:'',iconSize:[34,34],iconAnchor:[17,17],
    html:`<div style="width:34px;height:34px;display:flex;align-items:center;justify-content:center;"><div style="width:28px;height:28px;border-radius:5px;background:${s.meta.color}22;border:2px solid ${s.meta.color};display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 0 12px ${s.meta.color}55;">${s.meta.icon}</div></div>`});
  const m=L.marker([s.lat,s.lon],{icon:ic}).addTo(shelterMapInstance);
  m.on('popupopen',()=>m.setPopupContent(buildShelterPopup(s)));
  m.bindPopup('',{maxWidth:290});
  m.on('click',()=>selectShelter(s.id));
  shelterMarkers.push(m);
  s._marker=m;
}

function buildShelterPopup(s){
  return `<div style="font-family:'IBM Plex Sans',sans-serif;min-width:260px;max-width:300px;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,.1);">
      <span style="font-size:20px;">${s.meta.icon}</span>
      <div style="flex:1;">
        <div style="font-family:Rajdhani,sans-serif;font-size:15px;font-weight:700;color:${s.meta.color};">${s.name}</div>
        <div style="font-size:8px;font-family:monospace;color:#94a3b8;">${s.meta.label.toUpperCase()} · ${s.meta.priority}</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px;">
      <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:3px;padding:5px 7px;">
        <div style="font-size:7px;color:#64748b;font-family:monospace;">${s.gmLoaded?'ROAD DIST':'DISTANCE'}</div>
        <div style="font-size:13px;font-weight:700;color:${s.meta.color};font-family:monospace;">${fmtDist(s.distKm)}</div>
      </div>
      <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:3px;padding:5px 7px;">
        <div style="font-size:7px;color:#64748b;font-family:monospace;">WALK${s.walkMin!=null?'':' (EST)'}</div>
        <div style="font-size:13px;font-weight:700;color:#fcd34d;font-family:monospace;">${s.walkMin!=null?s.walkMin+' min':'~'+Math.round(s.distKm*15)+' min'}</div>
      </div>
      <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:3px;padding:5px 7px;">
        <div style="font-size:7px;color:#64748b;font-family:monospace;">CAPACITY</div>
        <div style="font-size:10px;font-weight:600;color:#dff4ff;font-family:monospace;">${s.capacity}</div>
      </div>
      <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:3px;padding:5px 7px;">
        <div style="font-size:7px;color:#64748b;font-family:monospace;">TYPE</div>
        <div style="font-size:10px;font-weight:600;color:${s.meta.color};font-family:monospace;">${s.meta.priority}</div>
      </div>
    </div>
    ${s.address?`<div style="font-size:9px;color:#94a3b8;margin-bottom:8px;font-family:monospace;">📍 ${s.address}</div>`:''}
    <div style="display:flex;gap:5px;">
      <button onclick="getRouteToShelter('${s.id}')" style="flex:1;padding:8px;background:linear-gradient(135deg,#0d9488,#0284c7);border:none;border-radius:3px;color:#fff;font-family:monospace;font-size:9px;font-weight:700;cursor:pointer;">🗺 GET ROUTE</button>
      <button onclick="openGoogleMapsNav(${s.lat},${s.lon})" style="padding:8px 11px;background:rgba(14,165,233,.1);border:1px solid rgba(14,165,233,.25);border-radius:3px;color:#38bdf8;font-family:monospace;font-size:9px;cursor:pointer;">↗ Navigate</button>
    </div>
  </div>`;
}

function renderShelterList(shelters){
  const el=document.getElementById('shelterList');
  el.innerHTML='';
  if(!shelters.length){
    el.innerHTML=`<div style="padding:24px;text-align:center;font-family:var(--mono);font-size:10px;color:var(--fg3);">No shelters found within ${fmtDist(currentShelterRadius/1000)}.<br>Try a larger radius.</div>`;
    return;
  }
  document.getElementById('shelterCount').textContent=`${shelters.length} shelters found`;
  shelters.forEach((s,i)=>{
    const card=document.createElement('div');
    card.className=`sh-card type-${s.meta.key}`;
    card.id=`shcard-${s.id}`;
    card.style.animationDelay=`${i*0.04}s`;
    const dc=s.distKm<1?'#4ade80':s.distKm<5?'#14b8a6':s.distKm<10?'#f59e0b':'#f97316';
    const pc=s.meta.priority==='CRITICAL'?'#fda4af':s.meta.priority==='HIGH'?'#6ee7b7':'#fcd34d';
    const pbg=s.meta.priority==='CRITICAL'?'rgba(244,63,94,.12)':s.meta.priority==='HIGH'?'rgba(16,185,129,.1)':'rgba(245,158,11,.1)';

    card.innerHTML=`
      <div class="sh-card-top">
        <div class="sh-card-name">${s.meta.icon} ${s.name}</div>
        <div class="sh-dist-badge" style="background:${dc}18;color:${dc};border:1px solid ${dc}44;">
          ${fmtDist(s.distKm)}
          <div style="font-size:6px;opacity:.7;">${s.gmLoaded?'road':'direct'}</div>
        </div>
      </div>
      <div class="sh-type-row">
        <div class="sh-type-badge" style="background:${s.meta.color}18;color:${s.meta.color};border:1px solid ${s.meta.color}33;">${s.meta.label}</div>
        <div class="sh-type-badge" style="background:${pbg};color:${pc};border:1px solid ${pc}44;">${s.meta.priority}</div>
      </div>
      <div class="sh-card-details">
        <div class="sh-detail"><div class="sh-detail-label">Walk</div><div class="sh-detail-val">${s.walkMin!=null?s.walkMin+' min':'~'+Math.round(s.distKm*15)+' min'}</div></div>
        <div class="sh-detail"><div class="sh-detail-label">${s.driveMin!=null?'Drive':'Hours'}</div><div class="sh-detail-val">${s.driveMin!=null?s.driveMin+' min':s.openHours}</div></div>
        <div class="sh-detail"><div class="sh-detail-label">Capacity</div><div class="sh-detail-val" style="font-size:9px;">${s.capacity}</div></div>
      </div>
      ${s.address?`<div style="font-size:9px;color:var(--fg3);font-family:var(--mono);margin-bottom:6px;">📍 ${s.address}</div>`:''}
      <div class="sh-card-footer">
        <button class="sh-route-btn" onclick="getRouteToShelter('${s.id}')">🗺 Get Route</button>
        <button class="sh-nav-btn" onclick="openGoogleMapsNav(${s.lat},${s.lon})">↗ Navigate</button>
      </div>`;
    card.addEventListener('click',e=>{if(!e.target.closest('button,a'))selectShelter(s.id);});
    el.appendChild(card);
  });
}

function selectShelter(id){
  if(selectedShelterCard)selectedShelterCard.classList.remove('selected');
  const card=document.getElementById(`shcard-${id}`);
  if(card){card.classList.add('selected');card.scrollIntoView({behavior:'smooth',block:'nearest'});selectedShelterCard=card;}
  const s=allShelters.find(x=>String(x.id)===String(id));
  if(s){shelterMapInstance.setView([s.lat,s.lon],16,{animate:true,duration:.8});s._marker&&s._marker.openPopup();}
}

async function getRouteToShelter(id){
  // id may come in as string from onclick — coerce to match allShelters
  const s=allShelters.find(x=>String(x.id)===String(id));
  if(!s||!shelterUserLat)return;
  selectShelter(s.id);
  const badge=document.getElementById('routeInfoBadge');
  badge.style.display='flex';
  document.getElementById('routeDistance').textContent='…';
  document.getElementById('routeTimeFoot').textContent='…';
  document.getElementById('routeTimeCar').textContent='…';
  document.getElementById('routeMode').textContent='Calculating…';

  // Clear previous route polylines
  if(window._routePolylines){window._routePolylines.forEach(p=>{try{shelterMapInstance.removeLayer(p);}catch(e){}});}
  window._routePolylines=[];

  const base={method:'POST',headers:{'Content-Type':'application/json'}};

  // Fetch driving route (OSRM)
  let driveData=null;
  try{
    const r=await fetch('/api/osrm-route',{...base,body:JSON.stringify({
      profile:'driving',
      user_lat:shelterUserLat,user_lon:shelterUserLon,
      dest_lat:s.lat,dest_lon:s.lon
    })});
    const j=await r.json();
    if(j.code==='Ok'&&j.routes&&j.routes[0])driveData=j.routes[0];
  }catch(e){console.warn('[OSRM drive]',e);}

  if(driveData&&driveData.geometry){
    const latlngs=driveData.geometry.coordinates.map(c=>[c[1],c[0]]);
    const poly=L.polyline(latlngs,{color:'#38bdf8',weight:5,opacity:.9}).addTo(shelterMapInstance);
    window._routePolylines.push(poly);
    // Real road distance and drive time from OSRM
    s.distKm=driveData.distance/1000;
    s.driveMin=Math.round(driveData.duration/60);
    // Walk time estimate: road distance ÷ walking speed (5 km/h = 12 min/km)
    s.walkMin=Math.round(s.distKm*12);
    s.gmLoaded=true;
    document.getElementById('routeDistance').textContent=fmtDist(s.distKm);
    document.getElementById('routeTimeCar').textContent=s.driveMin<1?'<1 min':s.driveMin+' min';
    document.getElementById('routeTimeFoot').textContent=s.walkMin+' min';
    document.getElementById('routeMode').textContent=s.name.length>20?s.name.substring(0,20)+'…':s.name;
    shelterMapInstance.fitBounds(poly.getBounds(),{padding:[50,50]});
    renderShelterList(filteredShelters);
    if(s._marker)s._marker.setPopupContent(buildShelterPopup(s));
  }else{
    // OSRM failed — show haversine fallback
    s.walkMin=Math.round(s.distKm*12);
    document.getElementById('routeDistance').textContent=fmtDist(s.distKm)+' (est.)';
    document.getElementById('routeTimeCar').textContent='—';
    document.getElementById('routeTimeFoot').textContent=s.walkMin+' min (est.)';
    document.getElementById('routeMode').textContent='Route unavailable';
    // Draw straight line as fallback
    const poly=L.polyline([[shelterUserLat,shelterUserLon],[s.lat,s.lon]],{color:'#f59e0b',weight:3,opacity:.6,dashArray:'8 6'}).addTo(shelterMapInstance);
    window._routePolylines.push(poly);
    shelterMapInstance.fitBounds(poly.getBounds(),{padding:[50,50]});
  }
}

function clearShelterRoute(){
  if(window._routePolylines){window._routePolylines.forEach(p=>{try{shelterMapInstance.removeLayer(p);}catch(e){}});window._routePolylines=[];}
  const b=document.getElementById('routeInfoBadge');if(b)b.style.display='none';
}

function openGoogleMapsNav(lat,lon){
  window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}&travelmode=driving`,'_blank');
}

function setShelterFilter(type,btn){
  document.querySelectorAll('.sh-filter-btn').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');currentShelterFilter=type;applyShelterFilter(type);
}

function applyShelterFilter(type){
  filteredShelters=type==='all'?[...allShelters]:allShelters.filter(s=>s.meta.key===type);
  renderShelterList(filteredShelters);
  allShelters.forEach(s=>{
    if(!s._marker||!shelterMapInstance)return;
    const show=type==='all'||s.meta.key===type;
    try{
      if(show&&!shelterMapInstance.hasLayer(s._marker))s._marker.addTo(shelterMapInstance);
      if(!show&&shelterMapInstance.hasLayer(s._marker))shelterMapInstance.removeLayer(s._marker);
    }catch(e){}
  });
}

function filterShelterList(q){
  const tl=q.toLowerCase().trim();
  renderShelterList(tl?filteredShelters.filter(s=>s.name.toLowerCase().includes(tl)||s.meta.label.toLowerCase().includes(tl)||s.address.toLowerCase().includes(tl)):filteredShelters);
}

function sortShelterList(){
  shelterSortMode=shelterSortMode==='distance'?'priority':'distance';
  if(shelterSortMode==='priority'){const o={CRITICAL:0,HIGH:1,MODERATE:2,LOW:3};filteredShelters.sort((a,b)=>o[a.meta.priority]-o[b.meta.priority]||a.distKm-b.distKm);}
  else filteredShelters.sort((a,b)=>a.distKm-b.distKm);
  renderShelterList(filteredShelters);
}

function changeShelterRadius(val){
  const newRadius=parseInt(val);
  const oldRadius=currentShelterRadius;
  currentShelterRadius=newRadius;
  if(!shelterUserLat){initShelterPage();return;}

  if(newRadius<=oldRadius){
    // Radius shrunk — just filter from cache, no API call needed
    const radiusKm=newRadius/1000;
    allShelters=[];
    _shelterCache.forEach(s=>{
      s.distKm=haversineKm(shelterUserLat,shelterUserLon,s.lat,s.lon);
      if(s.distKm<=radiusKm+0.3)allShelters.push(s);
    });
    allShelters.sort((a,b)=>a.distKm-b.distKm);
    filteredShelters=[...allShelters];
    shelterMarkers.forEach(m=>{try{shelterMapInstance.removeLayer(m);}catch(e){}});
    shelterMarkers=[];
    allShelters.forEach(s=>addShelterMarker(s));
    applyShelterFilter(currentShelterFilter);
    document.getElementById('shelterCount').textContent=`${allShelters.length} shelters within ${radiusKm} km`;
    renderShelterList(filteredShelters);
  }else{
    // Radius grew — fetch new outer ring (cache keeps inner ones)
    fetchNearbyShelters();
  }
}
function refreshShelters(){
  if(!shelterUserLat){initShelterPage();return;}
  // Full refresh — clear cache and re-fetch everything
  _shelterCache=new Map();
  fetchNearbyShelters();
}

/* ═══ BOOT ═══ */
(async()=>{await initLangs();checkSession();})();
