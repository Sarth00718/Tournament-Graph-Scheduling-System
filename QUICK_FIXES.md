# 🔧 Quick Fixes - Apply These Now

## Priority 1: Critical Fixes (15 minutes)

### Fix #1: Add Date Range Validation
**File:** `backend/schedule_generator.py`  
**Line:** After line 50

```python
# Add this after: match_date = start_date + timedelta(days=date_index)

if match_date > rules["end_date"]:
    days_needed = date_index + 1
    days_available = (rules["end_date"] - start_date).days + 1
    raise ValueError(
        f"Cannot fit schedule in date range. "
        f"Need {days_needed} days but only {days_available} available. "
        f"Solutions: (1) Increase end_date, (2) Add more time_slots per day, "
        f"(3) Reduce rest_days_between_matches, or (4) Add more stadiums."
    )
```

---

### Fix #2: Add Stadium Capacity Validation
**File:** `backend/main.py`  
**Line:** After line 110 (after color_groups calculation)

```python
# Add this after: color_groups = coloring_summary(coloring)

# Validate stadium capacity
stadium_count = len(stadiums)
for color, match_ids in color_groups.items():
    if len(match_ids) > stadium_count:
        raise ValueError(
            f"Time slot group {color} has {len(match_ids)} matches "
            f"but only {stadium_count} stadiums available. "
            f"Solutions: (1) Add more stadiums, (2) Increase date range, "
            f"or (3) Reduce rest_days_between_matches."
        )
```

---

### Fix #3: Add Lat/Lng Validation
**File:** `backend/data_loader.py`  
**Line:** After line 45 (after lat/lng parsing)

```python
# Replace these lines:
lat = float(s["lat"])
lng = float(s["lng"])

# With:
try:
    lat = float(s["lat"])
    lng = float(s["lng"])
except (KeyError, ValueError, TypeError) as exc:
    raise ValueError(
        f"Stadium '{name}' must have numeric lat and lng."
    ) from exc

# Add validation:
if not (-90 <= lat <= 90):
    raise ValueError(
        f"Stadium '{name}' latitude must be between -90 and 90, got {lat}"
    )
if not (-180 <= lng <= 180):
    raise ValueError(
        f"Stadium '{name}' longitude must be between -180 and 180, got {lng}"
    )
```

---

## Priority 2: Safety Fixes (10 minutes)

### Fix #4: Haversine Safety
**File:** `backend/travel_optimizer.py`  
**Line:** 42

```python
# Replace:
a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2

# With:
a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
a = min(1.0, a)  # Prevent floating point errors
```

---

### Fix #5: Better Loop Termination
**File:** `backend/schedule_generator.py`  
**Line:** Around line 145 (in _enforce_rest_days)

```python
# Add after the while not found loop:
if not found:
    # Could not find valid slot - log warning and accept violation
    import logging
    logging.warning(
        f"Could not enforce {rest_days} rest days for match {curr['match']} "
        f"after checking {lookahead} days. Constraint may be impossible."
    )
    # Keep original assignment rather than infinite loop
    break
```

---

## Priority 3: Production Fixes (5 minutes)

### Fix #6: CORS Security
**File:** `backend/main.py`  
**Line:** 35

```python
# Replace:
allow_origins=["*"],

# With:
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    # Add your production domain here
],
```

---

### Fix #7: Environment Variables for Frontend
**File:** Create `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
```

**Then update all frontend files:**

Replace:
```javascript
const API_BASE = 'http://localhost:8000'
```

With:
```javascript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```

Files to update:
- `frontend/src/components/Dashboard.jsx`
- `frontend/src/components/ConflictGraph.jsx`
- `frontend/src/components/TravelReport.jsx`
- `frontend/src/components/AdjacencyMatrix.jsx`
- `frontend/src/components/TournamentTree.jsx`

---

## Testing After Fixes

### Test 1: Date Overflow
```python
# Should now show clear error message
POST /generate_schedule
{
  "teams": ["A", "B", "C", "D", "E", "F"],
  "stadiums": [...],  # 5 stadiums
  "rules": {
    "start_date": "2024-06-01",
    "end_date": "2024-06-02",  # Only 2 days!
    "time_slots": ["Morning"],
    "rest_days_between_matches": 2
  }
}

Expected: ValueError with helpful message
```

### Test 2: Stadium Capacity
```python
# Should now show clear error message
POST /generate_schedule
{
  "teams": ["A", "B", "C", "D", "E", "F", "G", "H"],  # 8 teams = 28 matches
  "stadiums": [...],  # Only 2 stadiums
  "rules": {
    "start_date": "2024-06-01",
    "end_date": "2024-06-30",
    "time_slots": ["Morning"],
    "rest_days_between_matches": 1
  }
}

Expected: ValueError about stadium capacity
```

### Test 3: Invalid Coordinates
```python
# Should now show clear error message
POST /generate_schedule
{
  "teams": ["A", "B"],
  "stadiums": [
    {"name": "Stadium1", "lat": 200, "lng": 500}  # Invalid!
  ],
  "rules": {...}
}

Expected: ValueError about lat/lng range
```

---

## Verification Checklist

After applying fixes, verify:

- [ ] Date overflow shows helpful error message
- [ ] Stadium capacity violation detected
- [ ] Invalid lat/lng rejected
- [ ] Haversine doesn't crash on edge cases
- [ ] Rest day enforcement doesn't hang
- [ ] CORS only allows specified origins
- [ ] Frontend uses environment variable for API URL
- [ ] All existing tests still pass
- [ ] Error messages are user-friendly

---

## Estimated Time

- **Priority 1 fixes:** 15 minutes
- **Priority 2 fixes:** 10 minutes
- **Priority 3 fixes:** 5 minutes
- **Testing:** 10 minutes

**Total: 40 minutes** to make your project production-ready! 🚀
