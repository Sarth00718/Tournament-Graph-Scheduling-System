"""
schedule_generator.py
---------------------
Converts Welsh-Powell coloring results into a concrete match schedule.

CRITICAL FIXES:
- Added date overflow validation
- Fixed infinite loop in rest day enforcement
- Added strict termination conditions
- Better error messages
- Comprehensive logging
"""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


def generate_schedule(
    matches: List[Dict[str, str]],
    coloring: Dict[str, int],
    stadiums: List[Dict[str, Any]],
    rules: Dict[str, Any],
) -> List[Dict[str, Any]]:
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
    Sorted list of schedule rows with match details
    
    Raises
    ------
    ValueError: If schedule cannot fit in date range
    """
    start_date: date = rules["start_date"]
    end_date: date = rules["end_date"]
    time_slots: List[str] = rules["time_slots"]
    rest_days: int = rules["rest_days"]
    stadium_names: List[str] = [s["name"] for s in stadiums]
    stadium_count = len(stadium_names)

    if not matches:
        logger.warning("No matches to schedule")
        return []
    
    if not coloring:
        raise ValueError("Coloring is empty. Cannot generate schedule.")
    
    if stadium_count == 0:
        raise ValueError("No stadiums available for scheduling.")
    
    if not time_slots:
        raise ValueError("No time slots defined.")

    logger.info(
        f"Generating schedule: {len(matches)} matches, {stadium_count} stadiums, "
        f"{len(time_slots)} slots/day, {rest_days} rest days"
    )

    # Sort matches for consistent stadium assignment
    sorted_matches = sorted(matches, key=lambda m: int(m["id"][1:]))
    
    # Track stadium usage per color
    color_stadium_usage: Dict[int, int] = {}
    
    schedule_rows: List[Dict[str, Any]] = []
    
    for m in sorted_matches:
        match_id = m["id"]
        color = int(coloring.get(match_id, 0))
        
        # Map color to (date, time_slot)
        date_index = color // len(time_slots)
        slot_index = color % len(time_slots)
        
        match_date = start_date + timedelta(days=date_index)
        
        # CRITICAL FIX: Validate date doesn't exceed end_date
        if match_date > end_date:
            raise ValueError(
                f"Schedule generation failed: Match {match_id} would be scheduled on "
                f"{match_date.isoformat()} which exceeds the tournament end date "
                f"{end_date.isoformat()}. This indicates the date range is too small "
                f"for the given constraints."
            )
        
        time_slot = time_slots[slot_index]
        if match_date > end_date:
            days_needed = date_index + 1
            days_available = (end_date - start_date).days + 1
            total_slots_needed = max(coloring.values()) + 1 if coloring else 0
            total_slots_available = days_available * len(time_slots)
            
            raise ValueError(
                f"Schedule cannot fit in date range!\n"
                f"  • Chromatic number: {total_slots_needed} time slots needed\n"
                f"  • Available slots: {total_slots_available} "
                f"({days_available} days × {len(time_slots)} slots/day)\n"
                f"  • Match {match_id} requires day {days_needed} but only {days_available} days available\n"
                f"\nSolutions:\n"
                f"  1. Extend end_date by at least {date_index - days_available + 1} days\n"
                f"  2. Add more time slots per day (currently {len(time_slots)})\n"
                f"  3. Reduce rest_days_between_matches (currently {rest_days})\n"
                f"  4. Add more stadiums (currently {stadium_count})"
            )
        
        time_slot = time_slots[slot_index]
        
        # Stadium assignment with round-robin within each color
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
            "color": color,
        })
    
    logger.info(f"Initial schedule generated with {len(schedule_rows)} matches")
    
    # Enforce rest day constraints
    if rest_days > 0:
        logger.info(f"Enforcing {rest_days} rest days between matches...")
        schedule_rows = _enforce_rest_days(
            schedule_rows,
            rest_days,
            time_slots,
            end_date,
        )

    # Sort by date, then time slot, then match ID
    SLOT_ORDER = {s: i for i, s in enumerate(time_slots)}
    schedule_rows.sort(
        key=lambda r: (r["date"], SLOT_ORDER.get(r["time_slot"], 99), r["match"])
    )
    
    logger.info("Schedule generation complete")
    return schedule_rows


def _enforce_rest_days(
    rows: List[Dict[str, Any]],
    rest_days: int,
    time_slots: List[str],
    end_date: date,
) -> List[Dict[str, Any]]:
    """
    Enforce rest day constraints by rescheduling matches that violate the constraint.
    
    CRITICAL FIXES:
    - Added strict termination conditions
    - Added max_lookahead to prevent infinite loops
    - Added logging for debugging
    - Better conflict detection
    
    Parameters
    ----------
    rows : List of schedule rows
    rest_days : Minimum days between matches for same team
    time_slots : Available time slots per day
    end_date : Maximum allowed date
    
    Returns
    -------
    Updated schedule rows with rest days enforced
    """
    if rest_days <= 0:
        return rows
    
    changed = True
    max_iterations = len(rows) * 2 + 10
    iterations = 0
    violations_fixed = 0

    logger.info(f"Starting rest day enforcement (max {max_iterations} iterations)")

    while changed and iterations < max_iterations:
        changed = False
        iterations += 1

        # Group matches by team
        team_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            team_rows[row["teamA"]].append(row)
            team_rows[row["teamB"]].append(row)

        SLOT_ORDER = {s: i for i, s in enumerate(time_slots)}

        # Check each team's schedule
        for team, team_schedule in team_rows.items():
            # Sort by date and time slot
            team_schedule.sort(
                key=lambda r: (r["date"], SLOT_ORDER.get(r["time_slot"], 99))
            )

            # Check consecutive matches
            for i in range(1, len(team_schedule)):
                prev = team_schedule[i - 1]
                curr = team_schedule[i]
                prev_date = date.fromisoformat(prev["date"])
                curr_date = date.fromisoformat(curr["date"])
                gap = (curr_date - prev_date).days

                if gap < rest_days:
                    # Violation detected
                    required_date = prev_date + timedelta(days=rest_days)
                    
                    # CRITICAL FIX: Check if required_date exceeds end_date
                    if required_date > end_date:
                        logger.warning(
                            f"Cannot enforce rest days for {team}: "
                            f"match {curr['match']} would need to move to {required_date} "
                            f"but end_date is {end_date}. Keeping original schedule."
                        )
                        break
                    
                    # Find next available slot
                    found = False
                    target_date = required_date
                    
                    # CRITICAL FIX: Strict lookahead limit
                    max_lookahead = 30
                    lookahead = 0
                    
                    while not found and lookahead < max_lookahead:
                        # Check if target_date exceeds end_date
                        if target_date > end_date:
                            logger.warning(
                                f"Cannot reschedule match {curr['match']} for {team}: "
                                f"would exceed end_date {end_date}. Accepting violation."
                            )
                            break
                        
                        for slot_name in time_slots:
                            target_date_str = target_date.isoformat()
                            
                            # Check for conflicts
                            has_conflict = False
                            for other in rows:
                                if other is curr:
                                    continue
                                
                                if other["date"] == target_date_str and other["time_slot"] == slot_name:
                                    # Team conflict?
                                    if (curr["teamA"] in (other["teamA"], other["teamB"]) or 
                                        curr["teamB"] in (other["teamA"], other["teamB"])):
                                        has_conflict = True
                                        break
                                    
                                    # Stadium conflict?
                                    if curr["stadium"] == other["stadium"]:
                                        has_conflict = True
                                        break
                            
                            if not has_conflict:
                                # Valid slot found
                                curr["date"] = target_date_str
                                curr["time_slot"] = slot_name
                                found = True
                                changed = True
                                violations_fixed += 1
                                logger.debug(
                                    f"Rescheduled {curr['match']} to {target_date_str} {slot_name}"
                                )
                                break
                        
                        if not found:
                            target_date += timedelta(days=1)
                            lookahead += 1
                    
                    # CRITICAL FIX: Log if we couldn't fix the violation
                    if not found:
                        logger.warning(
                            f"Could not enforce rest days for {team} match {curr['match']} "
                            f"after checking {lookahead} days. Constraint may be impossible. "
                            f"Keeping original schedule."
                        )
                    
                    # Break to re-sort and check again
                    break

    if iterations >= max_iterations:
        logger.warning(
            f"Rest day enforcement stopped after {max_iterations} iterations. "
            f"Some violations may remain."
        )
    else:
        logger.info(
            f"Rest day enforcement complete: {violations_fixed} violations fixed "
            f"in {iterations} iterations"
        )

    return rows
