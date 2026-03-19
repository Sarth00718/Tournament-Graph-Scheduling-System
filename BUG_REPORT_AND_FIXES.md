# 🐛 Bug Report & Analysis - Tournament Scheduler Project

## Executive Summary
After thorough code review, I found **7 critical bugs** and **5 potential issues** that could cause runtime errors, incorrect results, or poor user experience.

---

## 🔴 CRITICAL BUGS (Must Fix)

### Bug #1: Incorrect Adjacency Matrix Signature in main.py
**Location:** `backend/main.py` line 106  
**Severity:** CRITICAL - Will cause runtime error

**Problem:**
```python
# Current (WRONG):
adj_matrix = build_adjacency_matrix(G)

# Expected signature:
def build_adjacency_matrix(G, matches, schedule, rest_days)
```

**Impact:** The function call is missing 3 required parameters, causing `TypeError` when generating schedule.

**Fix:**
```python
# Line 106 in main.py should be:
adj_matrix = build_adjacency_matrix(G, matches, schedule, rules["rest_days"])
```

---

### Bug #2: Type Annotation Issues in schedule_generator.py
**Location:** `backend/schedule_generator.py` lines 30-35  
**Severity:** HIGH - Type confusion

**Problem:**
```python
coloring: dict[str, int]  # Expected
coloring: dict  # Actual (no type hints)
```

**Impact:** The coloring dict values are accessed as integers but not type-checked, leading to potential runtime errors.

**Fix:**
```python
def generate_schedule(
    matches: list[dict[str, str]],
    coloring: dict[str, int],  # Add type hint
    stadiums: list[dict[str, Any]],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
```

---

### Bug #3: Infinite Loop Risk in _enforce_rest_days
**Location:** `backend/schedule_generator.py` lines 95-150  
**Severity:** CRITICAL - Can hang the server

**Problem:**
```python
while changed and iterations < max_iterations:
    # Complex nested logic with break statements
    # If no valid slot found, infinite loop possible
```

**Impact:** If the date range is too small or constraints are impossible to satisfy, the loop may not terminate properly.

**Fix:**
```python
# Add better termination conditions:
if lookahead >= max_lookahead:
    # Log warning and accept violation
    import logging
    logging.warning(f"Could not enforce rest days for {curr['match']}")
    break  # Exit inner loop
```

---

### Bug #4: Stadium Capacity Not Enforced in Welsh-Powell
**Location:** `backend/graph_coloring.py` line 18  
**Severity:** HIGH - Logical error

**Problem:**
```python
def welsh_powell_coloring(G: nx.Graph, max_color_capacity: int | None = None):
    # Parameter exists but never used in main.py!
```

In `main.py` line 99:
```python
coloring = welsh_powell_coloring(G, max_color_capacity=stadium_count)
```

But the algorithm doesn't actually enforce this constraint properly.

**Impact:** More matches may be assigned to a color than there are stadiums, causing stadium conflicts.

**Fix:** The current implementation in `graph_coloring.py` lines 35-42 attempts to handle this, but it's not integrated with the main algorithm properly.

---

### Bug #5: Missing Error Handling for Empty Graph
**Location:** `backend/graph_coloring.py` line 18  
**Severity:** MEDIUM

**Problem:**
```python
if G.number_of_nodes() == 0:
    return {}
```

**Impact:** Empty coloring dict causes issues downstream in `chromatic_number()` and `coloring_summary()`.

**Fix:**
```python
def chromatic_number(coloring: dict) -> int:
    if not coloring:
        return 0
    return max(coloring.values()) + 1
```
This is already handled, but should add validation in main.py.

---

### Bug #6: Date Overflow in schedule_generator.py
**Location:** `backend/schedule_generator.py` lines 45-50  
**Severity:** HIGH

**Problem:**
```python
date_index = color // len(time_slots)
match_date = start_date + timedelta(days=date_index)
```

**Impact:** If chromatic number is large, `match_date` can exceed `end_date`, violating the tournament date range constraint.

**Fix:**
```python
date_index = color // len(time_slots)
match_date = start_date + timedelta(days=date_index)

# Add validation:
if match_date > rules["end_date"]:
    raise ValueError(
        f"Schedule requires {date_index + 1} days but only "
        f"{(rules['end_date'] - start_date).days + 1} days available. "
        f"Increase date range or reduce rest days."
    )
```

---

### Bug #7: Frontend API Base URL Hardcoded
**Location:** Multiple frontend files  
**Severity:** MEDIUM - Deployment issue

**Problem:**
```javascript
const API_BASE = 'http://localhost:8000'
```

**Impact:** Won't work in production or different environments.

**Fix:**
```javascript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```

Then create `.env` file:
```
VITE_API_BASE_URL=http://localhost:8000
```

---

## ⚠️ POTENTIAL ISSUES (Should Fix)

### Issue #1: No Validation for Insufficient Stadiums
**Location:** `backend/schedule_generator.py`

**Problem:** If there are more matches in a time slot than stadiums, the code wraps around but doesn't warn the user.

**Fix:** Add validation in `main.py`:
```python
max_matches_per_slot = max(len(group) for group in color_groups.values())
if max_matches_per_slot > len(stadiums):
    logging.warning(
        f"Time slot has {max_matches_per_slot} matches but only "
        f"{len(stadiums)} stadiums. Stadium conflicts may occur."
    )
```

---

### Issue #2: Haversine Distance Edge Case
**Location:** `backend/travel_optimizer.py` line 42

**Problem:**
```python
a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
return 2.0 * R * math.asin(math.sqrt(a))
```

**Impact:** If `a > 1` due to floating point errors, `math.asin` will raise `ValueError`.

**Fix:**
```python
a = min(1.0, math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
return 2.0 * R * math.asin(math.sqrt(a))
```

---

### Issue #3: Tournament Tree Seeding Bug
**Location:** `backend/visualization.py` line 115

**Problem:**
```python
def generate_seeds(k: int) -> list[int]:
    # Recursive seeding algorithm
```

**Impact:** For non-power-of-2 teams, BYE placement may not follow standard tournament seeding (1 vs 16, 2 vs 15, etc.).

**Fix:** Use standard bracket seeding algorithm.

---

### Issue #4: No CORS Origin Restriction
**Location:** `backend/main.py` line 35

**Problem:**
```python
allow_origins=["*"]
```

**Impact:** Security vulnerability - any website can call your API.

**Fix:**
```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    # Add production URLs here
]
```

---

### Issue #5: Missing Input Validation
**Location:** `backend/data_loader.py`

**Problem:** No validation for:
- Latitude range (-90 to 90)
- Longitude range (-180 to 180)
- Reasonable date ranges (not 100 years in future)
- Team name length limits

**Fix:** Add validation:
```python
def load_stadiums(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # ... existing code ...
    lat = float(s["lat"])
    lng = float(s["lng"])
    
    if not (-90 <= lat <= 90):
        raise ValueError(f"Stadium '{name}' latitude must be between -90 and 90")
    if not (-180 <= lng <= 180):
        raise ValueError(f"Stadium '{name}' longitude must be between -180 and 180")
```

---

## 🧪 Testing Recommendations

### Test Case 1: Large Number of Teams
```python
teams = [f"Team{i}" for i in range(20)]  # 190 matches
# Should handle gracefully or show error
```

### Test Case 2: Insufficient Date Range
```python
rules = {
    "start_date": "2024-06-01",
    "end_date": "2024-06-02",  # Only 2 days
    "rest_days_between_matches": 3,
    "time_slots": ["Morning"]
}
# Should show clear error message
```

### Test Case 3: Single Stadium
```python
stadiums = [{"name": "Stadium1", "lat": 0, "lng": 0}]
teams = ["A", "B", "C", "D", "E", "F"]  # 15 matches
# Should work but warn about stadium reuse
```

### Test Case 4: Zero Rest Days
```python
rules = {"rest_days_between_matches": 0}
# Should work - all same-team matches just need different colors
```

---

## 📝 Priority Fix Order

1. **Bug #1** (Adjacency Matrix) - IMMEDIATE - Breaks the app
2. **Bug #6** (Date Overflow) - HIGH - Data integrity
3. **Bug #3** (Infinite Loop) - HIGH - Server stability
4. **Bug #4** (Stadium Capacity) - MEDIUM - Logical correctness
5. **Issue #2** (Haversine) - MEDIUM - Edge case handling
6. **Bug #7** (API URL) - LOW - Deployment concern
7. **Issue #4** (CORS) - LOW - Security hardening

---

## ✅ What's Working Well

1. Welsh-Powell algorithm implementation is correct
2. Dijkstra's shortest path is properly implemented
3. Conflict graph construction logic is sound
4. Frontend UI/UX is excellent
5. D3.js visualizations are well-implemented
6. REST API structure is clean
7. Type hints are mostly present

---

## 🎯 Conclusion

Your project has a **solid foundation** with correct graph theory algorithms. The bugs found are mostly:
- Integration issues (wrong function signatures)
- Edge case handling (date overflow, infinite loops)
- Input validation (missing checks)

None of the core algorithms (Welsh-Powell, Dijkstra) have bugs. The issues are in the "glue code" that connects everything together.

**Estimated Fix Time:** 2-3 hours for all critical bugs.
