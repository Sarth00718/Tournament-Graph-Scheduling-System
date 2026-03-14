"""
schedule_generator.py
---------------------
Converts Welsh-Powell coloring results into a concrete match schedule.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

def generate_schedule(
    matches: list[dict[str, str]],
    coloring: dict,
    stadiums: list[dict[str, Any]],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    start_date = rules["start_date"]
    time_slots = rules["time_slots"]
    rest_days = int(rules["rest_days"])
    stadium_names: list[str] = [s["name"] for s in stadiums]
    stadium_count = len(stadium_names)

    schedule_rows: list[dict] = []
    
    # Sort matches to have a consistent index for stadium assignment
    sorted_matches = sorted(matches, key=lambda m: int(m["id"][1:]))
    
    color_stadium_usage: dict[int, int] = {}
    
    for i, m in enumerate(sorted_matches):
        match_id = m["id"]
        color = int(coloring.get(match_id, 0))
        
        # Phase 3 mapping:
        date_index = color // len(time_slots)
        slot_index = color % len(time_slots)
        
        match_date = start_date + timedelta(days=date_index)
        time_slot = time_slots[slot_index]
        
        # Phase 4 stadium assignment (robust tracking within color group)
        current_usage = color_stadium_usage.get(color, 0)
        stadium_idx = current_usage % stadium_count
        color_stadium_usage[color] = current_usage + 1
        stadium = stadium_names[stadium_idx]
        
        schedule_rows.append({
            "match": match_id,
            "teamA": m["teamA"],
            "teamB": m["teamB"],
            "date": match_date.isoformat(),
            "time_slot": time_slot,
            "stadium": stadium,
            "color": int(color),
        })
        
    # Phase 5: Rest-day validation
    if rest_days > 0:
        schedule_rows = _enforce_rest_days(
            schedule_rows,
            rest_days,
            time_slots,
        )

    # Sort
    SLOT_ORDER = {s: i for i, s in enumerate(time_slots)}
    schedule_rows.sort(
        key=lambda r: (r["date"], SLOT_ORDER.get(r["time_slot"], 99), r["match"])
    )

    return schedule_rows

def _enforce_rest_days(
    rows: list[dict],
    rest_days: int,
    time_slots: list[str],
) -> list[dict]:
    # Check team matches, if violation, reassign time slot (by pushing date forward)
    changed = True
    max_iterations = len(rows) * 2 + 10
    iterations = 0

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        team_rows: dict = defaultdict(list)
        for row in rows:
            team_rows[row["teamA"]].append(row)
            team_rows[row["teamB"]].append(row)

        SLOT_ORDER = {s: i for i, s in enumerate(time_slots)}

        for team, team_schedule in team_rows.items():
            team_schedule.sort(
                key=lambda r: (r["date"], SLOT_ORDER.get(r["time_slot"], 99))
            )

            for i in range(1, len(team_schedule)):
                prev = team_schedule[i - 1]
                curr = team_schedule[i]
                prev_date = date.fromisoformat(prev["date"])
                curr_date = date.fromisoformat(curr["date"])
                gap = (curr_date - prev_date).days

                if gap < rest_days:
                    # violation occurs -> reassign time slot (push forward)
                    required_date = prev_date + timedelta(days=rest_days)
                    
                    # Find the first available (date, time_slot) >= required_date
                    # that does NOT conflict with existing team matches or stadiums
                    found = False
                    target_date: date = required_date
                    
                    # Prevent infinite loops in edge cases
                    max_lookahead = 30 
                    lookahead: int = 0
                    
                    while not found and lookahead < max_lookahead:
                        for slot_name in time_slots:
                            team_conflict = False
                            stadium_conflict = False
                            target_date_str = target_date.isoformat()  # type: ignore
                            
                            for other in rows:
                                if other is curr:
                                    continue
                                
                                other_date = str(other.get("date", ""))
                                other_slot = str(other.get("time_slot", ""))
                                if other_date == target_date_str and other_slot == slot_name:
                                    other_teamA = str(other.get("teamA", ""))
                                    other_teamB = str(other.get("teamB", ""))
                                    curr_teamA = str(curr.get("teamA", ""))
                                    curr_teamB = str(curr.get("teamB", ""))
                                    
                                    # Team conflict?
                                    if curr_teamA in (other_teamA, other_teamB) or curr_teamB in (other_teamA, other_teamB):
                                        team_conflict = True
                                    
                                    # Stadium conflict?
                                    if str(curr.get("stadium", "")) == str(other.get("stadium", "")):
                                        stadium_conflict = True
                                        
                            if not team_conflict and not stadium_conflict:
                                curr["date"] = target_date_str
                                curr["time_slot"] = slot_name
                                found = True
                                changed = True
                                break
                                
                        if not found:
                            target_date = target_date + timedelta(days=1)  # type: ignore[operator]
                            lookahead = lookahead + 1  # type: ignore[operator]
                            
                    break

    return rows
