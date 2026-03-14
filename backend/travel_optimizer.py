"""
travel_optimizer.py
-------------------
Builds a spatial stadium graph and computes shortest travel routes
using DIJKSTRA'S ALGORITHM (exact implementation via NetworkX).

Spatial Graph
-------------
  Nodes  = Stadiums
  Edges  = All pairs of stadiums (complete graph)
  Weight = Haversine great-circle distance in kilometres

Dijkstra Usage
--------------
For each team, we know the list of stadiums they will visit
(derived from the generated schedule).  We compute the pairwise
shortest paths between consecutive stadiums using Dijkstra's
single-source shortest path; then we sum distances for a total
travel cost per team.
"""

from __future__ import annotations
import math
from typing import Any

import networkx as nx  # type: ignore[import]


# ─────────────────────────────────────────────────────────────────────────────
# Haversine distance
# ─────────────────────────────────────────────────────────────────────────────

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Compute the great-circle distance between two points on Earth.

    Parameters
    ----------
    lat1, lng1 : coordinates of point 1 (degrees)
    lat2, lng2 : coordinates of point 2 (degrees)

    Returns
    -------
    Distance in kilometres.
    """
    R = 6_371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2.0 * R * math.asin(math.sqrt(a))


# ─────────────────────────────────────────────────────────────────────────────
# Spatial graph construction
# ─────────────────────────────────────────────────────────────────────────────

def build_stadium_graph(stadiums: list[dict[str, Any]]) -> nx.Graph:
    """
    Create a complete weighted graph over stadiums.

    Node attributes : name, lat, lng
    Edge attribute  : weight (haversine km)
    """
    G = nx.Graph()
    for s in stadiums:
        G.add_node(s["name"], lat=float(s["lat"]), lng=float(s["lng"]))

    for i, s1 in enumerate(stadiums):
        for j, s2 in enumerate(stadiums):
            if j <= i:
                continue
            dist = haversine_km(
                float(s1["lat"]), float(s1["lng"]),
                float(s2["lat"]), float(s2["lng"]),
            )
            G.add_edge(s1["name"], s2["name"], weight=dist)

    return G


# ─────────────────────────────────────────────────────────────────────────────
# Dijkstra shortest-path computation
# ─────────────────────────────────────────────────────────────────────────────

def dijkstra_shortest_path(
    G: nx.Graph, source: str, target: str
) -> tuple:
    """
    Compute the shortest path (by km) between two stadium nodes using
    Dijkstra's algorithm.

    Returns
    -------
    (total_distance_km, [source, ..., target])
    """
    try:
        length, path = nx.single_source_dijkstra(G, source, target, weight="weight")
        return float(round(float(length), 2)), path
    except Exception:
        return float("inf"), []


# ─────────────────────────────────────────────────────────────────────────────
# Per-team travel report
# ─────────────────────────────────────────────────────────────────────────────

def compute_team_travel(
    schedule: list[dict[str, Any]],
    stadium_graph: nx.Graph,
) -> dict[str, dict[str, Any]]:
    """
    For every team, derive the order of stadiums they visit
    (sorted by date, then slot) and compute cumulative travel distance
    via Dijkstra between consecutive stadiums.

    Parameters
    ----------
    schedule      : list of schedule row dicts from schedule_generator
    stadium_graph : the spatial graph from build_stadium_graph()

    Returns
    -------
    {
        "TeamName": {
            "stadiums": ["StadiumA", "StadiumB", ...],
            "legs": [
                {"from": "StadiumA", "to": "StadiumB",
                 "path": [...], "distance_km": 123.4},
                ...
            ],
            "total_km": 246.8,
        },
        ...
    }
    """
    # Collect ordered stadium visits per team
    team_visits: dict[str, list] = {}

    SLOT_ORDER: dict[str, int] = {"Morning": 0, "Afternoon": 1, "Evening": 2}

    for row in schedule:
        date_val: str = str(row["date"])
        slot: str = str(row["time_slot"])
        stadium: str = str(row["stadium"])
        slot_rank: int = SLOT_ORDER.get(slot, 99)

        for team in [row["teamA"], row["teamB"]]:
            team_key = str(team)
            if team_key not in team_visits:
                team_visits[team_key] = []
            team_visits[team_key].append((date_val, slot_rank, slot, stadium))

    report: dict[str, dict[str, Any]] = {}
    for team, visits in team_visits.items():
        visits.sort(key=lambda x: (x[0], x[1]))
        ordered_stadiums = [v[3] for v in visits]

        legs: list[dict[str, Any]] = []
        total_km = 0.0
        for k in range(1, len(ordered_stadiums)):
            src = ordered_stadiums[k - 1]
            tgt = ordered_stadiums[k]
            if src == tgt:
                legs.append({"from": src, "to": tgt, "path": [src, tgt], "distance_km": 0.0})
            else:
                dist, path = dijkstra_shortest_path(stadium_graph, src, tgt)
                dist_float = float(dist) if dist != float("inf") else 0.0
                legs.append({"from": src, "to": tgt, "path": path, "distance_km": float(round(dist_float, 2))})
                if dist != float("inf"):
                    total_km += dist_float

        report[team] = {
            "stadiums": ordered_stadiums,
            "legs": legs,
            "total_km": float(round(total_km, 2)),
        }

    return report


# ─────────────────────────────────────────────────────────────────────────────
# Serialise stadium graph for API responses
# ─────────────────────────────────────────────────────────────────────────────

def stadium_graph_to_dict(G: nx.Graph) -> dict[str, Any]:
    """Return JSON-serialisable stadium graph."""
    nodes = [
        {"id": n, "lat": d["lat"], "lng": d["lng"]}
        for n, d in G.nodes(data=True)
    ]
    edges = [
        {"source": u, "target": v, "distance_km": float(round(float(d["weight"]), 2))}
        for u, v, d in G.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}
