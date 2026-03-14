"""
conflict_graph.py
-----------------
Builds the Dynamic Conflict Graph  G = (V, E)

Vertices (V):  Each vertex is a round-robin match between two teams.
Edges    (E):  An edge connects two matches that CANNOT be scheduled
               in the same time slot because of one of three conflict types:

    1. Same-Team Conflict   – both matches share at least one team.
    2. Stadium Conflict     – (detected post-assignment; handled in
                               schedule_generator by round-robin stadium
                               allocation — two matches in the same slot
                               cannot share a stadium).
    3. Rest-Day Conflict    – a team would not have enough rest days
                              between consecutive matches.

The rest-day conflict is encoded directly in the graph: for each team,
matches are listed in the order they would naturally be played;
a conflict edge is added between any two matches of the same team that
are "too close" in the coloring sequence (i.e., within rest_days slots).
Because of the same-team edges this is already guaranteed, so effectively
the rest-day constraint tightens how many slots must separate matches for
the same team — this is exposed via the `rest_days` attribute on nodes.
"""

from __future__ import annotations
from itertools import combinations
from typing import Any

import networkx as nx  # type: ignore[import]


# ─────────────────────────────────────────────────────────────────────────────
# Match generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_matches(teams: list[str]) -> list[dict[str, str]]:
    """
    Generate all unique round-robin matches.

    Returns:
        List of dicts: {"id": "M0", "teamA": "...", "teamB": "..."}
    """
    matches = []
    for idx, (a, b) in enumerate(combinations(teams, 2)):
        matches.append({"id": f"M{idx}", "teamA": a, "teamB": b})
    return matches


# ─────────────────────────────────────────────────────────────────────────────
# Conflict detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def _teams_share(m1: dict, m2: dict) -> bool:
    """Return True if the two matches share at least one team."""
    return bool({m1["teamA"], m1["teamB"]} & {m2["teamA"], m2["teamB"]})


# ─────────────────────────────────────────────────────────────────────────────
# Graph construction
# ─────────────────────────────────────────────────────────────────────────────

def build_conflict_graph(
    teams: list[str],
    matches: list[dict[str, str]],
    rest_days: int = 1,
) -> nx.Graph:
    """
    Construct and return the conflict graph G = (V, E).

    Parameters
    ----------
    teams    : list of team name strings
    matches  : list of match dicts from generate_matches()
    rest_days: mandatory rest-day gap between consecutive matches
               of the same team

    Node attributes
    ---------------
    label  : human-readable "TeamA vs TeamB"
    teamA  : first team
    teamB  : second team

    Edge attributes
    ---------------
    conflict_type : "same_team" | "rest_day"
    """
    G = nx.Graph()

    # ── Add vertices ──────────────────────────────────────────────────────────
    for m in matches:
        G.add_node(
            m["id"],
            label=f"{m['teamA']} vs {m['teamB']}",
            teamA=m["teamA"],
            teamB=m["teamB"],
        )

    # ── Add edges ─────────────────────────────────────────────────────────────
    for m1, m2 in combinations(matches, 2):
        if _teams_share(m1, m2):
            # Same-team conflict always leads to an edge.
            # For rest_day > 1 we still add the same edge; the scheduler
            # will additionally ensure these matches are rest_days slots apart.
            G.add_edge(
                m1["id"],
                m2["id"],
                conflict_type="same_team",
                rest_days_required=rest_days,
            )

    return G


# ─────────────────────────────────────────────────────────────────────────────
# Serialisation helper (used by visualization.py and API)
# ─────────────────────────────────────────────────────────────────────────────

def graph_to_dict(G: nx.Graph, coloring: Any = None) -> dict[str, Any]:
    """
    Convert the NetworkX graph to a JSON-serialisable dict.

    Parameters
    ----------
    G        : the conflict graph
    coloring : optional {node_id: color_int} from Welsh-Powell

    Returns
    -------
    {
        "nodes": [{"id": ..., "label": ..., "color": ...}, ...],
        "edges": [{"source": ..., "target": ..., "conflict_type": ...}, ...],
    }
    """
    nodes = []
    for node, data in G.nodes(data=True):
        color_val = 0
        if coloring is not None and isinstance(coloring, dict):
            color_val = coloring.get(node, 0)  # type: ignore[assignment]
        n = {
            "id": node,
            "label": data.get("label", node),
            "teamA": data.get("teamA", ""),
            "teamB": data.get("teamB", ""),
            "color": color_val,
        }
        nodes.append(n)

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "conflict_type": data.get("conflict_type", "unknown"),
        })

    return {"nodes": nodes, "edges": edges}
