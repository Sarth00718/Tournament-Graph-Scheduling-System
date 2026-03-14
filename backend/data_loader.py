"""
data_loader.py
--------------
Parse and validate JSON payloads from the frontend.
Returns clean Python structures used by all other modules.
"""

from __future__ import annotations
from typing import Any
from datetime import date, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# Public helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_teams(raw: list[str]) -> list[str]:
    """Validate and return a deduplicated list of team names."""
    teams = [t.strip() for t in raw if t.strip()]
    if len(teams) < 2:
        raise ValueError("At least 2 teams are required.")
    if len(teams) != len(set(teams)):
        raise ValueError("Duplicate team names are not allowed.")
    return teams


def load_stadiums(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Validate and return stadiums.

    Each stadium dict must have:
        name (str), lat (float), lng (float)
    """
    stadiums = []
    seen: set[str] = set()
    for s in raw:
        name = str(s.get("name", "")).strip()
        if not name:
            raise ValueError("Stadium must have a name.")
        if name in seen:
            raise ValueError(f"Duplicate stadium name: {name}")
        seen.add(name)
        try:
            lat = float(s["lat"])
            lng = float(s["lng"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(
                f"Stadium '{name}' must have numeric lat and lng."
            ) from exc
        stadiums.append({"name": name, "lat": lat, "lng": lng})
    if not stadiums:
        raise ValueError("At least one stadium is required.")
    return stadiums


def load_rules(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Parse scheduling rules.

    Expected keys:
        start_date   : "YYYY-MM-DD"
        end_date     : "YYYY-MM-DD"
        time_slots   : list[str]  e.g. ["Morning", "Afternoon", "Evening"]
        rest_days    : int  (mandatory rest days between a team's matches)
    """
    try:
        start = date.fromisoformat(raw["start_date"])
        end = date.fromisoformat(raw["end_date"])
    except (KeyError, ValueError) as exc:
        raise ValueError("start_date and end_date must be 'YYYY-MM-DD' strings.") from exc

    if end < start:
        raise ValueError("end_date must be >= start_date.")

    time_slots = raw.get("time_slots", ["Morning", "Afternoon", "Evening"])
    if not time_slots:
        raise ValueError("At least one time slot is required.")

    rest_days = int(raw.get("rest_days_between_matches", 1))
    if rest_days < 0:
        raise ValueError("rest_days_between_matches must be non-negative.")

    # Build sorted list of (date, slot) combinations available
    available_slots: list[tuple[date, str]] = []
    current = start
    while current <= end:
        for slot in time_slots:
            available_slots.append((current, slot))
        current += timedelta(days=1)

    return {
        "start_date": start,
        "end_date": end,
        "time_slots": time_slots,
        "rest_days": rest_days,
        "available_slots": available_slots,
    }


def parse_payload(payload: dict[str, Any]) -> tuple[list, list, dict]:
    """
    Top-level entry point.

    Returns:
        (teams, stadiums, rules)
    """
    teams = load_teams(payload.get("teams", []))
    stadiums = load_stadiums(payload.get("stadiums", []))
    rules = load_rules(payload.get("rules", {}))
    return teams, stadiums, rules
