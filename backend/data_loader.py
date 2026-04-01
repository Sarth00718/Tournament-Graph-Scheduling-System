"""
data_loader.py
--------------
Parse and validate JSON payloads from the frontend.
Returns clean Python structures used by all other modules.

IMPROVEMENTS:
- Added comprehensive input validation
- Latitude/longitude range checks
- Team name length validation
- Date range sanity checks
- Better error messages
"""

from __future__ import annotations
from typing import Any
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

# Constants for validation
MAX_TEAM_NAME_LENGTH = 100
MIN_TEAM_NAME_LENGTH = 1
MAX_STADIUM_NAME_LENGTH = 200
MAX_DATE_RANGE_DAYS = 3650  # ~10 years


def load_teams(raw: list[str]) -> list[str]:
    """
    Validate and return a deduplicated list of team names.
    
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(raw, list):
        raise ValueError("Teams must be provided as a list.")
    
    # Filter out empty/whitespace strings
    original_count = len(raw)
    teams = [t.strip() for t in raw if isinstance(t, str) and t.strip()]
    
    # Log if any teams were filtered out
    filtered_count = original_count - len(teams)
    if filtered_count > 0:
        logger.warning(f"Filtered out {filtered_count} empty/whitespace team names")
    
    if len(teams) < 2:
        raise ValueError("At least 2 teams are required to generate a tournament schedule.")
    
    if len(teams) != len(set(teams)):
        duplicates = [t for t in teams if teams.count(t) > 1]
        raise ValueError(f"Duplicate team names are not allowed. Found duplicates: {set(duplicates)}")
    
    # Validate team name lengths
    for team in teams:
        if len(team) < MIN_TEAM_NAME_LENGTH:
            raise ValueError(f"Team name cannot be empty.")
        if len(team) > MAX_TEAM_NAME_LENGTH:
            raise ValueError(
                f"Team name '{team[:50]}...' exceeds maximum length of {MAX_TEAM_NAME_LENGTH} characters."
            )
    
    logger.info(f"Loaded {len(teams)} teams successfully")
    return teams


def load_stadiums(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Validate and return stadiums with comprehensive checks.

    Each stadium dict must have:
        name (str), lat (float), lng (float)
    
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(raw, list):
        raise ValueError("Stadiums must be provided as a list.")
    
    if not raw:
        raise ValueError("At least one stadium is required.")
    
    stadiums = []
    seen: set[str] = set()
    
    for idx, s in enumerate(raw):
        if not isinstance(s, dict):
            raise ValueError(f"Stadium at index {idx} must be a dictionary.")
        
        # Validate name
        name = str(s.get("name", "")).strip()
        if not name:
            raise ValueError(f"Stadium at index {idx} must have a non-empty name.")
        
        if len(name) > MAX_STADIUM_NAME_LENGTH:
            raise ValueError(
                f"Stadium name '{name[:50]}...' exceeds maximum length of {MAX_STADIUM_NAME_LENGTH} characters."
            )
        
        if name in seen:
            raise ValueError(f"Duplicate stadium name: '{name}'")
        seen.add(name)
        
        # Validate and parse coordinates
        try:
            lat = float(s["lat"])
            lng = float(s["lng"])
        except KeyError as exc:
            raise ValueError(
                f"Stadium '{name}' is missing required field: {exc.args[0]}"
            ) from exc
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Stadium '{name}' has invalid lat/lng values. Both must be numeric."
            ) from exc
        
        # Validate coordinate ranges
        if not (-90 <= lat <= 90):
            raise ValueError(
                f"Stadium '{name}' has invalid latitude {lat}. "
                f"Latitude must be between -90 and 90 degrees."
            )
        
        if not (-180 <= lng <= 180):
            raise ValueError(
                f"Stadium '{name}' has invalid longitude {lng}. "
                f"Longitude must be between -180 and 180 degrees."
            )
        
        stadiums.append({"name": name, "lat": lat, "lng": lng})
    
    logger.info(f"Loaded {len(stadiums)} stadiums successfully")
    return stadiums


def load_rules(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Parse and validate scheduling rules.

    Expected keys:
        start_date   : "YYYY-MM-DD"
        end_date     : "YYYY-MM-DD"
        time_slots   : list[str]  e.g. ["Morning", "Afternoon", "Evening"]
        rest_days    : int  (mandatory rest days between a team's matches)
    
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(raw, dict):
        raise ValueError("Rules must be provided as a dictionary.")
    
    # Parse dates
    try:
        start = date.fromisoformat(raw["start_date"])
        end = date.fromisoformat(raw["end_date"])
    except KeyError as exc:
        raise ValueError(
            f"Missing required date field: {exc.args[0]}. "
            f"Both start_date and end_date must be provided in 'YYYY-MM-DD' format."
        ) from exc
    except ValueError as exc:
        raise ValueError(
            f"Invalid date format. Dates must be in 'YYYY-MM-DD' format. Error: {exc}"
        ) from exc

    # Validate date range
    if end < start:
        raise ValueError(
            f"end_date ({end}) must be on or after start_date ({start})."
        )
    
    date_range_days = (end - start).days + 1
    if date_range_days > MAX_DATE_RANGE_DAYS:
        raise ValueError(
            f"Date range is too large ({date_range_days} days). "
            f"Maximum allowed is {MAX_DATE_RANGE_DAYS} days."
        )
    
    # Validate time slots
    time_slots = raw.get("time_slots", ["Morning", "Afternoon", "Evening"])
    if not isinstance(time_slots, list):
        raise ValueError("time_slots must be a list of strings.")
    
    time_slots = [str(slot).strip() for slot in time_slots if slot]
    if not time_slots:
        raise ValueError("At least one time slot is required per day.")
    
    if len(time_slots) != len(set(time_slots)):
        raise ValueError("Duplicate time slot names are not allowed.")
    
    # Validate rest days
    try:
        rest_days = int(raw.get("rest_days_between_matches", 1))
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"rest_days_between_matches must be a non-negative integer. Error: {exc}"
        ) from exc
    
    if rest_days < 0:
        raise ValueError(
            f"rest_days_between_matches must be non-negative, got {rest_days}."
        )
    
    if rest_days > date_range_days:
        logger.warning(
            f"rest_days ({rest_days}) exceeds date range ({date_range_days} days). "
            f"This may make scheduling impossible."
        )

    # Build sorted list of (date, slot) combinations available
    available_slots: list[tuple[date, str]] = []
    current = start
    while current <= end:
        for slot in time_slots:
            available_slots.append((current, slot))
        current += timedelta(days=1)

    logger.info(
        f"Loaded rules: {date_range_days} days, {len(time_slots)} slots/day, "
        f"{rest_days} rest days = {len(available_slots)} total slots"
    )

    return {
        "start_date": start,
        "end_date": end,
        "time_slots": time_slots,
        "rest_days": rest_days,
        "available_slots": available_slots,
    }


def parse_payload(payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    """
    Top-level entry point for parsing and validating tournament configuration.

    Returns:
        (teams, stadiums, rules)
    
    Raises:
        ValueError: If any validation fails
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")
    
    try:
        teams = load_teams(payload.get("teams", []))
        stadiums = load_stadiums(payload.get("stadiums", []))
        rules = load_rules(payload.get("rules", {}))
        
        # Cross-validation: Check if schedule is theoretically possible
        num_matches = len(teams) * (len(teams) - 1) // 2
        num_slots = len(rules["available_slots"])
        
        logger.info(
            f"Configuration: {len(teams)} teams → {num_matches} matches, "
            f"{num_slots} available slots, {len(stadiums)} stadiums"
        )
        
        # Warn if slots seem insufficient (rough heuristic)
        if num_matches > num_slots * len(stadiums):
            logger.warning(
                f"Potential scheduling issue: {num_matches} matches but only "
                f"{num_slots} slots × {len(stadiums)} stadiums = {num_slots * len(stadiums)} capacity. "
                f"Consider increasing date range or stadiums."
            )
        
        return teams, stadiums, rules
        
    except ValueError as exc:
        logger.error(f"Validation failed: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Unexpected error during payload parsing: {exc}")
        raise ValueError(f"Failed to parse tournament configuration: {exc}") from exc
