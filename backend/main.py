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
from typing import Any, Optional
import traceback

from data_loader import parse_payload  # type: ignore[import-not-found]
from conflict_graph import generate_matches, build_conflict_graph, graph_to_dict  # type: ignore[import-not-found]
from graph_coloring import welsh_powell_coloring, chromatic_number, coloring_summary  # type: ignore[import-not-found]
from travel_optimizer import build_stadium_graph, compute_team_travel, stadium_graph_to_dict  # type: ignore[import-not-found]
from schedule_generator import generate_schedule  # type: ignore[import-not-found]
from visualization import build_adjacency_matrix, build_tournament_tree, graph_statistics  # type: ignore[import-not-found]


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
    allow_origins=["*"],
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
        raw = payload.model_dump()
        teams, stadiums, rules = parse_payload(raw)

        # Step 1: Generate all round-robin matches
        matches = generate_matches(teams)

        # Step 2: Build conflict graph
        G = build_conflict_graph(teams, matches, rules["rest_days"])

        # Step 3: Welsh-Powell graph coloring
        stadium_count = len(stadiums)
        coloring = welsh_powell_coloring(G, max_color_capacity=stadium_count)
        chi = chromatic_number(coloring)
        color_groups = coloring_summary(coloring)

        # Step 4: Generate master schedule
        schedule = generate_schedule(matches, coloring, stadiums, rules)

        # Step 5: Dijkstra travel optimization
        stadium_graph = build_stadium_graph(stadiums)
        travel_report = compute_team_travel(schedule, stadium_graph)

        # Step 6: Adjacency matrix
        adj_matrix = build_adjacency_matrix(G, matches, schedule, rules["rest_days"])

        # Step 7: Tournament tree
        tournament_tree = build_tournament_tree(teams)

        # Step 8: Graph data with colors
        graph_data = graph_to_dict(G, coloring)

        # Step 9: Statistics
        stats = graph_statistics(G, coloring)

        # Store in state for GET endpoints
        STATE.update({
            "graph_data": graph_data,
            "travel_report": travel_report,
            "adj_matrix": adj_matrix,
            "tournament_tree": tournament_tree,
            "schedule": schedule,
            "stats": stats,
            "stadium_graph": stadium_graph_to_dict(stadium_graph),
            "coloring": coloring,
            "chromatic_number": chi,
            "color_groups": {str(k): v for k, v in color_groups.items()},
            "teams": teams,
            "stadiums": [s["name"] for s in stadiums],  # type: ignore[misc]
        })

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
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal error: {traceback.format_exc()}")


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
        "stadium_graph": STATE.get("stadium_graph", {}),
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
