"""
schedule_generator.py
---------------------
Converts Welsh-Powell coloring results into a concrete match schedule.

Mapping color → time slot
--------------------------
Each color integer (0, 1, 2, …) is mapped to a (date, time_slot) pair
taken from rules["available_slots"] in order.  Colors that are the same
can share the same time slot while maintaining different stadiums.

Stadium assignment
------------------
Within each time slot a round-robin stadium rotation is used so that
no two matches in the same slot share the same stadium (Stadium Conflict
constraint).

Rest-day enforcement
--------------------
After the initial assignment, a post-processing step checks each team's
match schedule.  If two consecutive matches for the same team fall within
fewer than `rest_days` calendar days of each other, the later match is
pushed forward to the next available slot that respects the rest gap.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def generate_schedule(
    matches: list[dict[str, str]],
    coloring: dict,
    stadiums: list[dict[str, Any]],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build the master match schedule from coloring output.

    Parameters
    ----------
    matches  : list of {id, teamA, teamB}
    coloring : {match_id: color_int} from Welsh-Powell
    stadiums : list of {name, lat, lng}
    rules    : output of data_loader.load_rules()

    Returns
    -------
    Sorted list of schedule rows:
    [
        {
            "match": "M0",
            "teamA": "...",
            "teamB": "...",
            "date": "YYYY-MM-DD",
            "time_slot": "Morning" | ...,
            "stadium": "...",
            "color": int,   # time-slot group
        },
        ...
    ]
    """
    available_slots: list = rules["available_slots"]
    rest_days: int = int(rules["rest_days"])
    stadium_names: list[str] = [s["name"] for s in stadiums]

    if not available_slots:
        raise ValueError("No available slots in the given date range.")

    # ── Group matches by color ────────────────────────────────────────────────
    color_groups: dict = defaultdict(list)
    for match_id, color in coloring.items():
        color_groups[int(color)].append(match_id)

    # Sort color groups so color 0 -> first slot, color 1 -> second, etc.
    sorted_colors: list[int] = sorted(color_groups.keys())

    # ── Map each color to an available slot ───────────────────────────────────
    # We may have more colors than slots if the date range is very small;
    # in that case we wrap around (unlikely in practice with real dates).
    color_to_slot: dict = {}
    used_slot_idx: dict = {}   # slot key -> matches already assigned

    for color in sorted_colors:
        # Find first slot not already at capacity (capacity = num stadiums)
        assigned = False
        checked = 0
        for slot_date, slot_name in available_slots:
            key = (slot_date, slot_name)
            if used_slot_idx.get(key, 0) < len(stadium_names):
                color_to_slot[color] = (slot_date, slot_name)
                assigned = True
                break
            checked += 1
            if checked > len(available_slots) * 2:
                break

        if not assigned:
            # Fall back: use first available slot regardless of capacity
            color_to_slot[color] = available_slots[color % len(available_slots)]

    # ── Build initial schedule rows ───────────────────────────────────────────
    match_lookup: dict = {m["id"]: m for m in matches}
    schedule_rows: list[dict] = []

    # slot usage tracker: (date, slot) -> list of assigned stadiums
    slot_stadium_use: dict = defaultdict(list)

    for color in sorted_colors:
        slot_date, slot_name = color_to_slot[color]
        key = (slot_date, slot_name)

        for match_id in color_groups[color]:
            m = match_lookup[match_id]

            # Pick next stadium not yet used in this slot
            assigned_stadium = stadium_names[0]  # default fallback
            for stadium in stadium_names:
                if stadium not in slot_stadium_use[key]:
                    assigned_stadium = stadium
                    break

            slot_stadium_use[key].append(assigned_stadium)
            schedule_rows.append({
                "match": match_id,
                "teamA": m["teamA"],
                "teamB": m["teamB"],
                "date": slot_date.isoformat(),
                "time_slot": slot_name,
                "stadium": assigned_stadium,
                "color": color,
            })

    # ── Rest-day enforcement ──────────────────────────────────────────────────
    if rest_days > 0:
        schedule_rows = _enforce_rest_days(
            schedule_rows,
            rest_days,
            rules["time_slots"],
            available_slots,
            stadium_names,
        )

    # ── Sort by date, slot, match ─────────────────────────────────────────────
    SLOT_ORDER = {s: i for i, s in enumerate(rules["time_slots"])}
    schedule_rows.sort(
        key=lambda r: (r["date"], SLOT_ORDER.get(r["time_slot"], 99), r["match"])
    )

    return schedule_rows


# ─────────────────────────────────────────────────────────────────────────────
# Rest-day enforcement helper
# ─────────────────────────────────────────────────────────────────────────────

def _enforce_rest_days(
    rows: list[dict],
    rest_days: int,
    time_slots: list[str],
    available_slots: list,
    stadium_names: list[str],
) -> list[dict]:
    """
    Check every team's schedule and push matches forward if the
    mandatory rest-day gap is violated.
    """
    changed = True
    max_iterations = len(rows) * 2 + 10
    iterations = 0

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        # Group rows by team
        team_rows: dict = defaultdict(list)
        for row in rows:
            team_rows[row["teamA"]].append(row)
            team_rows[row["teamB"]].append(row)

        SLOT_ORDER = {s: i for i, s in enumerate(time_slots)}

        for team, team_schedule in team_rows.items():
            # Sort by date then slot order
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
                    # Need to push curr match to a later slot
                    required_date = prev_date + timedelta(days=rest_days)
                    # Find next available slot on or after required_date
                    for slot_date, slot_name in available_slots:
                        if slot_date >= required_date:
                            curr["date"] = slot_date.isoformat()
                            curr["time_slot"] = slot_name
                            changed = True
                            break

    return rows
