"""
main.py
-------
FastAPI server exposing the tournament scheduling REST API.

Endpoints
---------
POST /generate_schedule   – Full pipeline: returns schedule + stats
GET  /conflict_graph      – Graph nodes/edges/colors (requires prior POST)
GET  /travel_report       – Per-team travel routes (requires prior POST)
GET  /adjacency_matrix    – Matrix data (requires prior POST)
GET  /tournament_tree     – Knockout bracket tree (requires prior POST)
GET  /health              – Server health check
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from pydantic import BaseModel  # type: ignore[import]
from typing import Any
import traceback
import logging

from data_loader import parse_payload  # type: ignore[import-not-found]
from conflict_graph import generate_matches, build_conflict_graph, graph_to_dict  # type: ignore[import-not-found]
from graph_coloring import welsh_powell_coloring, chromatic_number, coloring_summary, validate_coloring  # type: ignore[import-not-found]
from travel_optimizer import build_stadium_graph, compute_team_travel  # type: ignore[import-not-found]
from schedule_generator import generate_schedule  # type: ignore[import-not-found]
from visualization import build_adjacency_matrix, build_tournament_tree, graph_statistics  # type: ignore[import-not-found]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# App initialisation
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Tournament Scheduler API",
    description="Constraint-Based Multi-Stadium Sports Tournament Scheduling with Graph Theory",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://tournament-graph-scheduling-system.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory session store (single-user demo)
# ─────────────────────────────────────────────────────────────────────────────

STATE: dict[str, Any] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    teams: list[str]
    stadiums: list[dict[str, Any]]
    rules: dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "message": "Tournament Scheduler API is running."}


# ─────────────────────────────────────────────────────────────────────────────
# Validation Helper
# ─────────────────────────────────────────────────────────────────────────────

def _validate_scheduling_constraints(teams: list[str], stadiums: list[dict], rules: dict[str, Any]) -> None:
    """
    Validate that the scheduling constraints are mathematically feasible.
    Raises ValueError with user-friendly message if constraints are impossible.
    """
    from datetime import timedelta
    
    num_teams = len(teams)
    num_stadiums = len(stadiums)
    rest_days = rules["rest_days"]
    start_date = rules["start_date"]
    end_date = rules["end_date"]
    time_slots = rules["time_slots"]
    
    # Calculate available slots
    available_days = (end_date - start_date).days + 1
    slots_per_day = len(time_slots)
    total_slots = available_days * slots_per_day
    
    # Calculate requirements
    total_matches = (num_teams * (num_teams - 1)) // 2
    matches_per_team = num_teams - 1
    
    # Constraint 1: Minimum days needed for rest days
    # Each team plays (n-1) matches with rest_days between them
    # Formula: Match on day 0, then need (rest_days + 1) days to next match
    # Example: 3 matches, 2 rest days → Day 0, Day 3, Day 6 → needs 7 days total
    # Formula: 1 + (matches_per_team - 1) * (rest_days + 1)
    min_days_per_team = 1 + (matches_per_team - 1) * (rest_days + 1)
    
    if min_days_per_team > available_days:
        suggested_end_date = start_date + timedelta(days=min_days_per_team - 1)
        raise ValueError(
            f"❌ Impossible Schedule: Rest day constraint cannot be satisfied!\n\n"
            f"📊 Current Configuration:\n"
            f"  • Teams: {num_teams} (each plays {matches_per_team} matches)\n"
            f"  • Rest days required: {rest_days} days between matches\n"
            f"  • Date range: {available_days} days ({start_date} to {end_date})\n\n"
            f"⚠️ Problem:\n"
            f"  Each team needs at least {min_days_per_team} days to play {matches_per_team} matches\n"
            f"  with {rest_days} rest days between them.\n\n"
            f"✅ Solutions:\n"
            f"  1. Increase end date to at least {suggested_end_date.strftime('%Y-%m-%d')} ({min_days_per_team} days)\n"
            f"  2. Reduce rest days to {max(0, available_days // matches_per_team)} or less\n"
            f"  3. Reduce number of teams to {max(2, int((available_days / rest_days) ** 0.5) + 1)} or fewer"
        )
    
    # Constraint 2: Enough total slots for all matches
    if total_matches > total_slots:
        raise ValueError(
            f"❌ Impossible Schedule: Not enough time slots!\n\n"
            f"📊 Current Configuration:\n"
            f"  • Total matches: {total_matches}\n"
            f"  • Available slots: {total_slots} ({available_days} days × {slots_per_day} slots/day)\n\n"
            f"✅ Solutions:\n"
            f"  1. Increase date range (need at least {(total_matches + slots_per_day - 1) // slots_per_day} days)\n"
            f"  2. Add more time slots per day (Morning, Afternoon, Evening)\n"
            f"  3. Reduce number of teams"
        )
    
    # Constraint 3: Stadium capacity warning (not fatal, but warn)
    # With Welsh-Powell, we might need more colors than ideal
    # Rough estimate: chromatic number ≈ max_degree + 1 = num_teams
    estimated_chromatic = num_teams
    max_matches_per_slot = (total_matches + estimated_chromatic - 1) // estimated_chromatic
    
    if max_matches_per_slot > num_stadiums:
        # This is a warning, not an error - the algorithm will try to work around it
        import logging
        logging.warning(
            f"Stadium capacity may be tight: Estimated {max_matches_per_slot} matches per slot "
            f"but only {num_stadiums} stadiums. Consider adding more stadiums."
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /generate_schedule
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/generate_schedule")
def generate_schedule_endpoint(payload: ScheduleRequest) -> dict[str, Any]:
    """
    Full scheduling pipeline:
    1. Parse input
    2. Generate matches
    3. Build conflict graph G=(V,E)
    4. Apply Welsh-Powell coloring
    5. Generate schedule from coloring
    6. Compute travel routes (Dijkstra)
    7. Build adjacency matrix
    8. Build tournament tree
    9. Return everything
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting schedule generation")
        
        raw = payload.model_dump()
        teams, stadiums, rules = parse_payload(raw)
        
        # Validate constraints before generating schedule
        logger.info("Validating scheduling constraints...")
        _validate_scheduling_constraints(teams, stadiums, rules)
        logger.info("✓ Constraints validated successfully")

        # Step 1: Generate all round-robin matches
        logger.info("Step 1: Generating matches")
        matches = generate_matches(teams)
        logger.info(f"Generated {len(matches)} matches")

        # Step 2: Build conflict graph
        logger.info("Step 2: Building conflict graph")
        G = build_conflict_graph(teams, matches, rules["rest_days"])
        logger.info(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Step 3: Welsh-Powell graph coloring
        logger.info("Step 3: Applying Welsh-Powell coloring")
        stadium_count = len(stadiums)
        time_slots_count = len(rules["time_slots"])
        
        # CRITICAL FIX: Remove stadium capacity constraint from coloring
        # The stadium capacity should be enforced during schedule generation,
        # not during graph coloring. This allows the algorithm to find the
        # true chromatic number and distribute colors more evenly.
        coloring = welsh_powell_coloring(G, max_color_capacity=None)
        chi = chromatic_number(coloring)
        color_groups = coloring_summary(coloring)
        
        logger.info(f"Chromatic number χ(G) = {chi}")
        logger.info(f"Color distribution: {[(c, len(matches)) for c, matches in sorted(color_groups.items())[:10]]}")
        
        # CRITICAL FIX: Validate stadium capacity
        logger.info("Step 3.5: Validating stadium capacity")
        for color, match_ids in color_groups.items():
            if len(match_ids) > stadium_count:
                raise ValueError(
                    f"Stadium capacity exceeded!\n"
                    f"  • Time slot group {color} has {len(match_ids)} matches\n"
                    f"  • Only {stadium_count} stadiums available\n"
                    f"  • {len(match_ids) - stadium_count} matches cannot be assigned\n"
                    f"\nSolutions:\n"
                    f"  1. Add at least {len(match_ids) - stadium_count} more stadiums\n"
                    f"  2. Increase date range to spread matches across more time slots\n"
                    f"  3. Reduce rest_days_between_matches to allow tighter scheduling"
                )
        
        # Validate coloring correctness
        is_valid, errors = validate_coloring(G, coloring)
        if not is_valid:
            logger.error(f"Coloring validation failed: {errors[:3]}")
            raise ValueError(f"Graph coloring produced invalid result: {errors[0]}")

        # Step 4: Generate master schedule
        logger.info("Step 4: Generating schedule")
        schedule = generate_schedule(matches, coloring, stadiums, rules)
        logger.info(f"Schedule generated with {len(schedule)} entries")

        # Step 5: Dijkstra travel optimization
        logger.info("Step 5: Computing travel routes")
        stadium_graph = build_stadium_graph(stadiums)
        travel_report = compute_team_travel(schedule, stadium_graph)

        # Step 6: Adjacency matrix
        logger.info("Step 6: Building adjacency matrix")
        adj_matrix = build_adjacency_matrix(G, matches, schedule, rules["rest_days"])

        # Step 7: Tournament tree
        logger.info("Step 7: Building tournament tree")
        tournament_tree = build_tournament_tree(teams)

        # Step 8: Graph data with colors
        logger.info("Step 8: Preparing graph visualization data")
        graph_data = graph_to_dict(G, coloring)

        # Step 9: Statistics
        logger.info("Step 9: Computing statistics")
        stats = graph_statistics(G, coloring)

        # Store in state for GET endpoints
        STATE.update({
            "graph_data": graph_data,
            "travel_report": travel_report,
            "adj_matrix": adj_matrix,
            "tournament_tree": tournament_tree,
            "schedule": schedule,
            "stats": stats,
            "coloring": coloring,
            "chromatic_number": chi,
            "color_groups": {str(k): v for k, v in color_groups.items()},
            "teams": teams,
            "stadiums": [s["name"] for s in stadiums],
        })

        logger.info("Schedule generation complete!")
        logger.info("=" * 80)

        return {
            "success": True,
            "schedule": schedule,
            "chromatic_number": chi,
            "min_time_slots": chi,
            "total_matches": len(matches),
            "total_teams": len(teams),
            "stats": stats,
            "color_groups": {str(k): v for k, v in color_groups.items()},
        }

    except ValueError as exc:
        logger.error(f"Validation error: {exc}")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"Internal error: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error. Check logs for details."
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /conflict_graph
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/conflict_graph")
def get_conflict_graph() -> dict[str, Any]:
    """Return conflict graph nodes and edges with color assignments."""
    if "graph_data" not in STATE:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /generate_schedule first.",
        )
    return {
        "success": True,
        "graph": STATE["graph_data"],
        "chromatic_number": STATE.get("chromatic_number", 0),
        "color_groups": STATE.get("color_groups", {}),
        "stats": STATE.get("stats", {}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /travel_report
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/travel_report")
def get_travel_report() -> dict[str, Any]:
    """Return per-team Dijkstra travel routes and distances."""
    if "travel_report" not in STATE:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /generate_schedule first.",
        )
    return {
        "success": True,
        "travel_report": STATE["travel_report"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /adjacency_matrix
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/adjacency_matrix")
def get_adjacency_matrix() -> dict[str, Any]:
    """Return the conflict graph's adjacency matrix."""
    if "adj_matrix" not in STATE:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /generate_schedule first.",
        )
    return {
        "success": True,
        "adjacency_matrix": STATE["adj_matrix"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /tournament_tree
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/tournament_tree")
def get_tournament_tree() -> dict[str, Any]:
    """Return the knockout tournament tree structure."""
    if "tournament_tree" not in STATE:
        raise HTTPException(
            status_code=404,
            detail="No schedule generated yet. Call POST /generate_schedule first.",
        )
    return {
        "success": True,
        "tournament_tree": STATE["tournament_tree"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn  # type: ignore[import]
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
