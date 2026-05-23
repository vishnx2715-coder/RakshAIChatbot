/**
 * maps.js — Drop-in replacement snippets for Shelter Map,
 * Disaster Zones Map, and Risk Analysis Map templates.
 *
 * Key changes vs the old code:
 *  1. AbortController with 10s timeout on every fetch
 *  2. Retry logic (up to 2 retries with back-off)
 *  3. LOW / MODERATE markers are NEVER created (server already
 *     filters them; this is a safety-net layer)
 *  4. Legend only shows HIGH and CRITICAL entries
 *  5. Counts are derived from the server's `counts` field
 */

// ─── Shared fetch helper ───────────────────────────────────────
/**
 * Fetch with timeout + automatic retry.
 * @param {string} url
 * @param {object} opts   - standard fetch options
 * @param {number} timeout - ms before AbortController fires (default 10000)
 * @param {number} retries - number of additional attempts on failure (default 2)
 */
async function fetchWithTimeout(url, opts = {}, timeout = 10_000, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const res = await fetch(url, { ...opts, signal: controller.signal });
      clearTimeout(timer);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      if (attempt === retries) throw err;       // re-throw after final attempt
      await new Promise(r => setTimeout(r, 1000 * (attempt + 1))); // back-off
    }
  }
}

// ─── Marker colour helper ──────────────────────────────────────
function alertColour(level) {
  // ONLY two colours — CRITICAL and HIGH.
  // Any other level that somehow arrives is treated as null and skipped.
  if (level === 'CRITICAL') return '#DC2626';   // red
  if (level === 'HIGH')     return '#EA580C';   // orange
  return null;                                  // LOW / MODERATE → skip
}


// ══════════════════════════════════════════════════════════════
// 1. SHELTER MAP
//    Replace your existing initShelterMap() with this.
// ══════════════════════════════════════════════════════════════
async function initShelterMap(map) {
  const statusEl  = document.getElementById('shelter-status');
  const countEl   = document.getElementById('shelter-count');

  statusEl.textContent = 'Loading shelter locations…';

  let data;
  try {
    // /api/shelters is now a real endpoint (was missing → caused 404 → "Network error")
    data = await fetchWithTimeout('/api/shelters');
  } catch (err) {
    // User-visible error with actionable message
    statusEl.textContent = '⚠️ Could not load shelters. Check your connection and refresh.';
    console.error('[ShelterMap] fetch failed:', err);
    return;
  }

  const shelters = data.shelters || [];
  countEl.textContent = `${data.available_count} of ${data.total} shelters available`;
  statusEl.textContent = '';

  shelters.forEach(shelter => {
    const colour = shelter.available ? '#16A34A' : '#6B7280';   // green / grey
    const marker = L.circleMarker([shelter.lat, shelter.lon], {
      radius:      shelter.available ? 10 : 7,
      fillColor:   colour,
      color:       '#fff',
      weight:      2,
      opacity:     1,
      fillOpacity: 0.85,
    }).addTo(map);

    const facilitiesHtml = (shelter.facilities || [])
      .map(f => `<span class="badge">${f}</span>`).join(' ');

    marker.bindPopup(`
      <div class="shelter-popup">
        <strong>${shelter.name}</strong><br>
        <span class="status ${shelter.available ? 'open' : 'closed'}">
          ${shelter.available ? '✅ Open' : '🔴 Closed'}
        </span><br>
        Capacity: ${shelter.capacity} persons<br>
        District: ${shelter.district}<br>
        Contact: <a href="tel:${shelter.contact}">${shelter.contact}</a><br>
        Facilities: ${facilitiesHtml}
      </div>
    `);
  });

  // Shelter map DOES NOT show alert severity markers — it shows shelter availability only.
  // Alert overlays (if any) must only show HIGH and CRITICAL (see updateAlertOverlay below).
}


// ══════════════════════════════════════════════════════════════
// 2. DISASTER ZONES MAP
//    Replace your existing initDisasterZonesMap() / loadAlerts()
// ══════════════════════════════════════════════════════════════
async function initDisasterZonesMap(map) {
  const statusEl   = document.getElementById('zones-status');
  const countEl    = document.getElementById('zones-count');
  const legendEl   = document.getElementById('zones-legend');

  statusEl.textContent = 'Loading disaster zones…';

  let data;
  try {
    data = await fetchWithTimeout('/api/disaster-zones');
  } catch (err) {
    statusEl.textContent = '⚠️ Could not load disaster zones. Please refresh.';
    console.error('[DisasterZonesMap] fetch failed:', err);
    return;
  }

  const zones = data.zones || [];

  // ── COUNTS ────────────────────────────────────────────────
  // Only two counts exist — no LOW / MODERATE buckets at all
  countEl.innerHTML = `
    <span style="color:#DC2626">● Critical: ${data.critical_count}</span> &nbsp;
    <span style="color:#EA580C">● High: ${data.high_count}</span>
  `;
  statusEl.textContent = '';

  // ── LEGEND — only two entries ──────────────────────────────
  legendEl.innerHTML = '';   // clear any stale LOW/MODERATE entries
  (data.legend || []).forEach(entry => {
    const li = document.createElement('li');
    li.innerHTML = `<span style="background:${entry.color}" class="legend-dot"></span> ${entry.label}`;
    legendEl.appendChild(li);
  });

  // ── MARKERS ────────────────────────────────────────────────
  zones.forEach((zone, idx) => {
    const colour = alertColour(zone.level);
    if (!colour) return;   // safety net: never render LOW / MODERATE

    // Place markers near India's centre with small offsets since RSS
    // items don't carry precise coordinates.
    // In production, geocode zone.title or use a state-centroid lookup.
    const lat = 20.5937 + (Math.random() - 0.5) * 15;
    const lon = 78.9629 + (Math.random() - 0.5) * 20;

    const marker = L.circleMarker([lat, lon], {
      radius:      zone.level === 'CRITICAL' ? 14 : 10,
      fillColor:   colour,
      color:       '#fff',
      weight:      2,
      opacity:     1,
      fillOpacity: 0.8,
    }).addTo(map);

    marker.bindPopup(`
      <div class="zone-popup">
        <strong class="level-${zone.level.toLowerCase()}">${zone.level}</strong><br>
        ${zone.title}<br>
        <small>Source: ${zone.source}</small><br>
        ${zone.link ? `<a href="${zone.link}" target="_blank">Full details →</a>` : ''}
      </div>
    `);
  });
}


// ══════════════════════════════════════════════════════════════
// 3. RISK ANALYSIS MAP
//    Replace your existing initRiskMap() / loadRiskData()
// ══════════════════════════════════════════════════════════════
async function initRiskAnalysisMap(map, lat = 20.5937, lon = 78.9629) {
  const statusEl  = document.getElementById('risk-status');
  const panelEl   = document.getElementById('risk-panel');
  const legendEl  = document.getElementById('risk-legend');

  statusEl.textContent = 'Analysing risk…';

  let data;
  try {
    data = await fetchWithTimeout('/api/risk-analysis', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ lat, lon }),
    });
  } catch (err) {
    statusEl.textContent = '⚠️ Risk analysis unavailable. Please refresh.';
    console.error('[RiskAnalysisMap] fetch failed:', err);
    return;
  }

  statusEl.textContent = '';

  const risk      = data.risk;
  const riskItems = data.risk_items || [];   // only HIGH / CRITICAL hazards
  const rssAlerts = data.rss_alerts || [];   // only HIGH / CRITICAL RSS alerts
  const weather   = data.weather || {};

  // ── SUMMARY PANEL ─────────────────────────────────────────
  if (risk) {
    const overallColour = alertColour(risk.overall) || '#16A34A';  // green if NORMAL/LOW/MOD
    panelEl.innerHTML = `
      <div class="risk-overall" style="border-left: 4px solid ${overallColour}">
        <strong>Overall risk: ${risk.overall}</strong><br>
        <small>${weather.city || ''}, ${weather.temp || ''}°C, ${weather.desc || ''}</small>
      </div>
    `;

    // Only render hazard rows for HIGH / CRITICAL items
    if (riskItems.length === 0) {
      panelEl.innerHTML += `<p class="no-risk">No HIGH or CRITICAL hazards detected at this location.</p>`;
    } else {
      riskItems.forEach(item => {
        panelEl.innerHTML += `
          <div class="hazard-row" style="border-left: 3px solid ${item.color}">
            <span class="hazard-name">${item.hazard.replace('_', ' ')}</span>
            <span class="hazard-score" style="color:${item.color}">${item.level} (${item.score}/5)</span>
          </div>
        `;
      });
    }
  }

  // ── LEGEND — only two entries ──────────────────────────────
  legendEl.innerHTML = '';
  (data.legend || []).forEach(entry => {
    const li = document.createElement('li');
    li.innerHTML = `<span style="background:${entry.color}" class="legend-dot"></span> ${entry.label}`;
    legendEl.appendChild(li);
  });

  // ── MAP MARKERS — HIGH / CRITICAL hazard zones only ────────
  riskItems.forEach(item => {
    const colour = alertColour(item.level);
    if (!colour) return;  // safety net

    // One marker per hazard type, slightly offset from centre
    const jLat = lat + (Math.random() - 0.5) * 2;
    const jLon = lon + (Math.random() - 0.5) * 2;

    L.circleMarker([jLat, jLon], {
      radius:      item.level === 'CRITICAL' ? 14 : 10,
      fillColor:   colour,
      color:       '#fff',
      weight:      2,
      fillOpacity: 0.8,
    })
    .addTo(map)
    .bindPopup(`
      <strong>${item.level}: ${item.hazard.replace('_', ' ')}</strong><br>
      Score: ${item.score}/5
    `);
  });

  // ── RSS ALERT OVERLAY ──────────────────────────────────────
  // Shows official alerts — already filtered to HIGH/CRITICAL by server
  rssAlerts.forEach(alert => {
    const colour = alertColour(alert.level);
    if (!colour) return;   // safety net
    // Append to the panel list, not as map markers (no coordinates)
    panelEl.innerHTML += `
      <div class="rss-alert-row" style="border-left: 3px solid ${colour}">
        <span class="level-tag" style="color:${colour}">${alert.level}</span>
        ${alert.title}
        <small>${alert.source}</small>
      </div>
    `;
  });
}


