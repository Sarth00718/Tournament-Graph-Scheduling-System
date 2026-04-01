"""
Test script to verify validation error messages
"""
import requests
import json

API_BASE = "http://localhost:8000"

# Test Case 1: Impossible rest day constraint (like your screenshot)
print("=" * 80)
print("TEST 1: Impossible Rest Day Constraint (6 teams, 2 days, rest_days=2)")
print("=" * 80)

payload1 = {
    "teams": ["TeamA", "TeamB", "TeamC", "TeamD", "TeamE", "TeamF"],
    "stadiums": [
        {"name": "Wankhede Stadium", "lat": 18.9388, "lng": 72.8258},
        {"name": "Eden Gardens", "lat": 22.5645, "lng": 88.3434},
        {"name": "Chinnaswamy Stadium", "lat": 12.9790, "lng": 77.5985}
    ],
    "rules": {
        "start_date": "2024-06-01",
        "end_date": "2024-06-02",  # Only 2 days!
        "time_slots": ["Morning", "Afternoon", "Evening"],
        "rest_days_between_matches": 2
    }
}

try:
    response = requests.post(f"{API_BASE}/generate_schedule", json=payload1)
    if response.status_code == 422:
        print("✅ Validation caught the error!")
        print(f"\nError Message:\n{response.json()['detail']}\n")
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test Case 2: Valid constraint (should work)
print("\n" + "=" * 80)
print("TEST 2: Valid Constraint (6 teams, 10 days, rest_days=2)")
print("=" * 80)

payload2 = {
    "teams": ["TeamA", "TeamB", "TeamC", "TeamD", "TeamE", "TeamF"],
    "stadiums": [
        {"name": "Wankhede Stadium", "lat": 18.9388, "lng": 72.8258},
        {"name": "Eden Gardens", "lat": 22.5645, "lng": 88.3434},
        {"name": "Chinnaswamy Stadium", "lat": 12.9790, "lng": 77.5985}
    ],
    "rules": {
        "start_date": "2024-06-01",
        "end_date": "2024-06-10",  # 10 days - should work!
        "time_slots": ["Morning", "Afternoon", "Evening"],
        "rest_days_between_matches": 2
    }
}

try:
    response = requests.post(f"{API_BASE}/generate_schedule", json=payload2)
    if response.status_code == 200:
        data = response.json()
        print("✅ Schedule generated successfully!")
        print(f"  • Total matches: {data['total_matches']}")
        print(f"  • Chromatic number: {data['chromatic_number']}")
        print(f"  • Min time slots: {data['min_time_slots']}")
        
        # Check for rest day violations
        schedule = data['schedule']
        print(f"\n  Checking rest day violations...")
        
        team_matches = {}
        for match in schedule:
            for team in [match['teamA'], match['teamB']]:
                if team not in team_matches:
                    team_matches[team] = []
                team_matches[team].append(match['date'])
        
        violations = 0
        for team, dates in team_matches.items():
            dates_sorted = sorted(dates)
            for i in range(1, len(dates_sorted)):
                from datetime import date
                d1 = date.fromisoformat(dates_sorted[i-1])
                d2 = date.fromisoformat(dates_sorted[i])
                gap = (d2 - d1).days
                if gap < 2:
                    violations += 1
                    print(f"  ⚠️ {team}: {dates_sorted[i-1]} to {dates_sorted[i]} = {gap} days (needs 2)")
        
        if violations == 0:
            print(f"  ✅ No rest day violations found!")
        else:
            print(f"  ❌ Found {violations} rest day violations!")
            
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test Case 3: Not enough time slots
print("\n" + "=" * 80)
print("TEST 3: Not Enough Time Slots (10 teams, 2 days)")
print("=" * 80)

payload3 = {
    "teams": [f"Team{i}" for i in range(10)],  # 10 teams = 45 matches
    "stadiums": [
        {"name": "Stadium1", "lat": 18.9388, "lng": 72.8258},
        {"name": "Stadium2", "lat": 22.5645, "lng": 88.3434}
    ],
    "rules": {
        "start_date": "2024-06-01",
        "end_date": "2024-06-02",  # Only 2 days = 6 slots
        "time_slots": ["Morning", "Afternoon", "Evening"],
        "rest_days_between_matches": 0
    }
}

try:
    response = requests.post(f"{API_BASE}/generate_schedule", json=payload3)
    if response.status_code == 422:
        print("✅ Validation caught the error!")
        print(f"\nError Message:\n{response.json()['detail']}\n")
    else:
        print(f"❌ Unexpected response: {response.status_code}")
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "=" * 80)
print("TESTS COMPLETE")
print("=" * 80)
