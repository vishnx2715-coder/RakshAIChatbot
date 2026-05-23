# Distance Calculation Debug Guide

## Problem Statement
User reported that "Texcity College of Nursing" shows:
- **Side panel card**: 4.4 km
- **Map route badge**: 6.0 km  
- **Google Maps (correct)**: 5.0 km

All three displays should show **5.0 km** (the Google Maps verified distance).

---

## How Distance Calculation Works

### 1. Initial Load (Haversine)
When shelters are first loaded, they get a **straight-line distance** (haversine formula):
```javascript
// In fetchNearbyShelters()
s.distKm = haversineDistance(shelterUserLat, shelterUserLon, s.lat, s.lon);
```

### 2. OSRM Table API Update (Road Distance)
After initial load, `_loadOSRMDistances()` calls the backend `/api/osrm-table` endpoint:
- Backend calls OSRM with **driving profile first** (shortest road route)
- Backend calls OSRM with **foot profile second** (walking time)
- Frontend updates `s.distKm` with **driving distance** (matches Google Maps)
- Frontend updates `s.walkMin` with **foot duration** (accurate walking time)

### 3. Three Display Locations
All three should use `s.distKm` (which gets updated to driving distance):

1. **Side Panel Card** (`renderShelterList()` line ~2512):
   ```javascript
   ${fmtDist(s.distKm)}
   ```

2. **Map Popup** (`buildShelterPopup()` line ~2500):
   ```javascript
   ${fmtDist(s.distKm)}
   ```

3. **Route Badge** (`getRouteToShelter()` line ~2565):
   ```javascript
   document.getElementById('routeDistance').textContent=fmtDist(drive.distance/1000);
   ```
   **Note**: Route badge uses OSRM Route API (different from Table API), but should match.

---

## Debug Logging Added

### Backend Logging (`app.py`)
```python
# Line ~530: Per-shelter distance logging
print(f"[OSRM] {profile} - Shelter {s['id']}: {dist_m}m ({dist_m/1000:.2f}km), {dur_s}s")
```

**What to look for:**
- Check if "Texcity College of Nursing" shows `drive_m: 5000` (5.0 km)
- Verify both `driving` and `foot` profiles complete successfully

### Frontend Logging (`templates/index.html`)

#### 1. OSRM Table API Call (line ~2385)
```javascript
console.log(`[OSRM Table] Starting distance calculation for ${allShelters.length} shelters...`);
console.log(`[OSRM Table] Attempt ${attempt}/2: Sending request to /api/osrm-table`);
console.log(`[OSRM Table] Response status: ${resp.status}`);
console.log(`[OSRM Table] Received ${data.results.length} results from backend`);
```

**What to look for:**
- Verify API call succeeds (status 200)
- Verify results array is not empty

#### 2. Distance Update Processing (line ~2420)
```javascript
console.log(`[OSRM] Processing ${data.results.length} results from backend`);
console.log(`[OSRM] Processing ${s.name}:`, {
  id: r.id,
  haversine_km: haversine.toFixed(2),
  drive_m: r.drive_m,
  drive_km: r.drive_m ? (r.drive_m/1000).toFixed(2) : 'null',
  walk_m: r.walk_m,
  walk_km: r.walk_m ? (r.walk_m/1000).toFixed(2) : 'null',
  drive_sec: r.drive_sec,
  walk_sec: r.walk_sec
});
console.log(`[OSRM] ✓ Updated ${s.name}: ${oldDist.toFixed(2)}km → ${roadKm.toFixed(2)}km (drive: ${s.driveMin}min)`);
```

**What to look for:**
- For "Texcity College of Nursing":
  - `drive_km` should be `"5.00"` (or close to 5.0)
  - `haversine_km` might be `"4.40"` (straight-line)
  - Should see "✓ Updated" message showing `4.40km → 5.00km`

#### 3. Card Rendering (line ~2505)
```javascript
console.log(`[Card Render] ${s.name}: distKm=${s.distKm.toFixed(2)}, osrmLoaded=${s.osrmLoaded}, driveMin=${s.driveMin}, walkMin=${s.walkMin}`);
```

**What to look for:**
- `distKm` should be `5.00` (not 4.40)
- `osrmLoaded` should be `true`

#### 4. Popup Rendering (line ~2493)
```javascript
console.log(`[Popup] ${s.name}: distKm=${s.distKm.toFixed(2)}, osrmLoaded=${s.osrmLoaded}`);
```

**What to look for:**
- `distKm` should be `5.00` (not 4.40)

#### 5. Route Badge (line ~2555)
```javascript
console.log(`[Route Badge] ${s.name}:`, {
  shelter_distKm: s.distKm.toFixed(2),
  shelter_osrmLoaded: s.osrmLoaded,
  walk_distance_m: walk?.distance,
  walk_distance_km: walk ? (walk.distance/1000).toFixed(2) : 'null',
  drive_distance_m: drive?.distance,
  drive_distance_km: drive ? (drive.distance/1000).toFixed(2) : 'null'
});
console.log(`[Route Badge] Using drive distance: ${badgeDistKm.toFixed(2)}km`);
```

**What to look for:**
- `drive_distance_km` should be `"5.00"` (or close)
- Badge should use this value, not walk distance

---

## Testing Steps

1. **Open browser console** (F12 → Console tab)
2. **Clear console** to start fresh
3. **Allow location access** when prompted
4. **Wait for shelters to load**
5. **Look for "Texcity College of Nursing"** in the logs

### Expected Log Sequence

```
[OSRM Table] Starting distance calculation for X shelters from (lat, lon)
[OSRM Table] Attempt 1/2: Sending request to /api/osrm-table
[OSRM Table] Response status: 200
[OSRM Table] Received X results from backend
[OSRM] Processing X results from backend
[OSRM] Processing Texcity College of Nursing: {
  id: ...,
  haversine_km: "4.40",
  drive_m: 5000,
  drive_km: "5.00",
  walk_m: 6000,
  walk_km: "6.00",
  drive_sec: 600,
  walk_sec: 1200
}
[OSRM] ✓ Updated Texcity College of Nursing: 4.40km → 5.00km (drive: 10min)
[OSRM] ✓ Walk time for Texcity College of Nursing: 20min
[OSRM] Updated X/X shelters with road distances
[Card Render] Texcity College of Nursing: distKm=5.00, osrmLoaded=true, driveMin=10, walkMin=20
```

6. **Click on "Texcity College of Nursing"** card
7. **Check popup** - should show 5.0 km
8. **Click "Get Route"** button
9. **Check route badge** - should show 5.0 km

---

## Possible Issues & Solutions

### Issue 1: Backend returns wrong distance
**Symptom**: `drive_km` in logs shows wrong value (not 5.0)
**Cause**: OSRM routing error or wrong coordinates
**Solution**: Verify shelter coordinates in `users.json`

### Issue 2: Frontend rejects distance
**Symptom**: See "✗ Rejected drive distance" warning
**Cause**: Sanity check failed (distance too different from haversine)
**Solution**: Adjust sanity check thresholds in `_loadOSRMDistances()` (line ~2430)

### Issue 3: Card shows old distance
**Symptom**: Card shows 4.4 km even after "✓ Updated" log
**Cause**: Card rendered before OSRM update completed
**Solution**: Already fixed - `renderShelterList()` is called after update

### Issue 4: Route badge shows different distance
**Symptom**: Route badge shows 6.0 km instead of 5.0 km
**Cause**: OSRM Route API returns different path than Table API
**Solution**: This is expected - Route API gives full geometry, Table API gives matrix. Small differences (±0.5 km) are normal due to different routing algorithms.

### Issue 5: OSRM Table API fails
**Symptom**: "All attempts failed, keeping haversine distances"
**Cause**: Network error, OSRM server down, or timeout
**Solution**: Check backend logs, verify OSRM mirrors are accessible

---

## Key Code Locations

| Component | File | Line | Function |
|-----------|------|------|----------|
| Backend OSRM Table | `app.py` | 483-560 | `osrm_table()` |
| Frontend OSRM Table | `templates/index.html` | 2382-2463 | `_loadOSRMDistances()` |
| Card Rendering | `templates/index.html` | 2500-2540 | `renderShelterList()` |
| Popup Rendering | `templates/index.html` | 2492-2500 | `buildShelterPopup()` |
| Route Badge | `templates/index.html` | 2545-2580 | `getRouteToShelter()` |

---

## Success Criteria

✅ All three displays show **5.0 km** for "Texcity College of Nursing"
✅ Console logs show `drive_km: "5.00"` from backend
✅ Console logs show `✓ Updated ... 4.40km → 5.00km`
✅ Card badge shows "5.0 km" with "road" label
✅ Map popup shows "5.0 km" with "ROAD DISTANCE" label
✅ Route badge shows "5.0 km" (±0.5 km tolerance for Route API)

---

## Next Steps

1. **Test with actual location** - Use real GPS coordinates
2. **Check console logs** - Follow the expected log sequence above
3. **Report findings** - Share console logs if distances still don't match
4. **Verify coordinates** - If backend returns wrong distance, check shelter coordinates in `users.json`
