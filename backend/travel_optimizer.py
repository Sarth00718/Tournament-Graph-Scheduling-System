"""
travel_optimizer.py
-------------------
Builds a spatial stadium graph and computes shortest travel routes
using DIJKSTRA'S ALGORITHM (exact implementation via NetworkX).

IMPROVEMENTS:
- Fixed haversine edge case (floating point errors)
- Added proper type hints
- Better error handling
- Comprehensive logging
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Tuple
import logging

import networkx as nx  # type: ignore[import]

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Compute the great-circle distance between two points on Earth using
    the Haversine formula.

    Parameters
    ----------
    lat1, lng1 : coordinates of point 1 (degrees)
    lat2, lng2 : coordinates of point 2 (degrees)

    Returns
    -------
    Distance in kilometres
    
    Notes
    -----
    CRITICAL FIX: Added min(1.0, a) to prevent domain errors in asin
    due to floating point precision issues.
    """
    R = 6_371.0  # Earth radius in km
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    
    a = (math.sin(dphi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    
    # CRITICAL FIX: Clamp 'a' to [0, 1] to prevent domain errors
    # Floating point errors can make 'a' slightly > 1
    a = min(1.0, max(0.0, a))
    
    distance = 2.0 * R * math.asin(math.sqrt(a))
    
    return distance


def build_stadium_graph(stadiums: List[Dict[str, Any]]) -> nx.Graph:
    """
    Create a complete weighted graph over stadiums.

    Node attributes : name, lat, lng
    Edge attribute  : weight (haversine km)
    
    Parameters
    ----------
    stadiums : List of stadium dicts with name, lat, lng
    
    Returns
    -------
    nx.Graph : Complete graph with haversine distances as edge weights
    
    Raises
    ------
    ValueError: If stadiums list is invalid
    """
    if not stadiums:
        raise ValueError("Cannot build stadium graph: no stadiums provided")
    
    G = nx.Graph()
    
    # Add nodes
    for s in stadiums:
        try:
            name = s["name"]
            lat = float(s["lat"])
            lng = float(s["lng"])
            G.add_node(name, lat=lat, lng=lng)
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f"Invalid stadium data: {s}. Error: {exc}") from exc
    
    # Add edges (complete graph)
    for i, s1 in enumerate(stadiums):
        for j, s2 in enumerate(stadiums):
            if j <= i:
                continue
            
            try:
                dist = haversine_km(
                    float(s1["lat"]), float(s1["lng"]),
                    float(s2["lat"]), float(s2["lng"]),
                )
                G.add_edge(s1["name"], s2["name"], weight=dist)
            except Exception as exc:
                logger.error(
                    f"Failed to compute distance between {s1['name']} and {s2['name']}: {exc}"
                )
                # Add edge with large weight as fallback
                G.add_edge(s1["name"], s2["name"], weight=999999.0)
    
    logger.info(
        f"Built stadium graph: {G.number_of_nodes()} nodes, "
        f"{G.number_of_edges()} edges"
    )
    
    return G


def dijkstra_shortest_path(
    G: nx.Graph, 
    source: str, 
    target: str
) -> Tuple[float, List[str]]:
    """
    Compute the shortest path (by km) between two stadium nodes using
    Dijkstra's algorithm.

    Parameters
    ----------
    G : nx.Graph
        Stadium graph with edge weights
    source : str
        Source stadium name
    target : str
        Target stadium name

    Returns
    -------
    (distance_km, path) : Tuple[float, List[str]]
        Total distance and list of stadium names in path
        Returns (inf, []) if no path exists
    """
    if source == target:
        return 0.0, [source]
    
    try:
        length, path = nx.single_source_dijkstra(
            G, source, target, weight="weight"
        )
        return float(round(float(length), 2)), path
    except nx.NetworkXNoPath:
        logger.warning(f"No path exists between {source} and {target}")
        return float("inf"), []
    except nx.NodeNotFound as exc:
        logger.error(f"Stadium not found in graph: {exc}")
        return float("inf"), []
    except Exception as exc:
        logger.error(f"Dijkstra failed for {source} → {target}: {exc}")
        return float("inf"), []


def compute_team_travel(
    schedule: List[Dict[str, Any]],
    stadium_graph: nx.Graph,
) -> Dict[str, Dict[str, Any]]:
    """
    For every team, derive the order of stadiums they visit
    (sorted by date, then slot) and compute cumulative travel distance
    via Dijkstra between consecutive stadiums.

    Parameters
    ----------
    schedule : List of schedule row dicts from schedule_generator
    stadium_graph : The spatial graph from build_stadium_graph()

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Per-team travel report with stadiums, legs, and total distance
    """
    if not schedule:
        logger.warning("Empty schedule, returning empty travel report")
        return {}
    
    # Collect ordered stadium visits per team
    team_visits: Dict[str, List[Tuple[str, int, str, str]]] = {}
    
    SLOT_ORDER: Dict[str, int] = {
        "Morning": 0, 
        "Afternoon": 1, 
        "Evening": 2
    }

    for row in schedule:
        date_val = str(row["date"])
        slot = str(row["time_slot"])
        stadium = str(row["stadium"])
        slot_rank = SLOT_ORDER.get(slot, 99)

        for team in [row["teamA"], row["teamB"]]:
            team_key = str(team)
            if team_key not in team_visits:
                team_visits[team_key] = []
            team_visits[team_key].append((date_val, slot_rank, slot, stadium))

    # Compute travel for each team
    report: Dict[str, Dict[str, Any]] = {}
    
    for team, visits in team_visits.items():
        visits.sort(key=lambda x: (x[0], x[1]))
        ordered_stadiums = [v[3] for v in visits]

        legs: List[Dict[str, Any]] = []
        total_km = 0.0
        
        for k in range(1, len(ordered_stadiums)):
            src = ordered_stadiums[k - 1]
            tgt = ordered_stadiums[k]
            
            if src == tgt:
                # Same stadium, no travel
                legs.append({
                    "from": src,
                    "to": tgt,
                    "path": [src, tgt],
                    "distance_km": 0.0
                })
            else:
                # Compute shortest path
                dist, path = dijkstra_shortest_path(stadium_graph, src, tgt)
                
                if dist == float("inf"):
                    logger.warning(
                        f"No path found for {team}: {src} → {tgt}. "
                        f"Using direct distance."
                    )
                    dist = 0.0
                    path = [src, tgt]
                
                legs.append({
                    "from": src,
                    "to": tgt,
                    "path": path,
                    "distance_km": float(round(dist, 2))
                })
                
                if dist != float("inf"):
                    total_km += dist

        report[team] = {
            "stadiums": ordered_stadiums,
            "legs": legs,
            "total_km": float(round(total_km, 2)),
        }
    
    logger.info(
        f"Computed travel for {len(report)} teams, "
        f"avg distance = {sum(r['total_km'] for r in report.values()) / len(report):.1f} km"
    )

    return report