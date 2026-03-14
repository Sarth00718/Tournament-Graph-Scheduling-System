"""
visualization.py
----------------
Generates adjacency matrix data and tournament tree structure
for the API responses.
"""

from __future__ import annotations
from typing import Any
from itertools import combinations
from datetime import date
import math

import networkx as nx  # type: ignore[import]


# ─────────────────────────────────────────────────────────────────────────────
# Adjacency Matrix
# ─────────────────────────────────────────────────────────────────────────────

def build_adjacency_matrix(
    G: nx.Graph,
    matches: list[dict[str, str]],
    schedule: list[dict[str, Any]],
    rest_days: int
) -> dict[str, Any]:
    """
    Build the adjacency matrix for the conflict graph showing different types:
    1: Same team conflict
    2: Rest-day violation conflict
    3: Stadium conflict
    """
    sorted_matches = sorted(matches, key=lambda m: int(m["id"][1:]))
    n = len(sorted_matches)
    idx = {m["id"]: i for i, m in enumerate(sorted_matches)}

    mat = [[0] * n for _ in range(n)]

    sched_map = {row["match"]: row for row in schedule}

    # 1. First, mark all same_team conflicts as 1
    # 2. Check for rest-day conflicts (gap < rest_days) on top of same-team
    # 3. Check for stadium conflicts (same date, same slot, same stadium)
    for u, v in combinations(sorted_matches, 2):
        u_id = u["id"]
        v_id = v["id"]
        i, j = idx[u_id], idx[v_id]
        
        # Check Stadium conflict
        if u_id in sched_map and v_id in sched_map:
            su = sched_map[u_id]
            sv = sched_map[v_id]
            if su["date"] == sv["date"] and su["time_slot"] == sv["time_slot"] and su["stadium"] == sv["stadium"]:
                mat[i][j] = mat[j][i] = 3
                continue

        # Check Same-Team
        share_team = bool({u["teamA"], u["teamB"]} & {v["teamA"], v["teamB"]})
        if share_team:
            mat[i][j] = mat[j][i] = 1
            
            # Check Rest-Day violation
            if u_id in sched_map and v_id in sched_map:
                su = sched_map[u_id]
                sv = sched_map[v_id]
                du = date.fromisoformat(su["date"])
                dv = date.fromisoformat(sv["date"])
                gap = abs((du - dv).days)
                if gap < rest_days:
                    mat[i][j] = mat[j][i] = 2

    labels = []
    for m in sorted_matches:
        labels.append({
            "id": m["id"],
            "label": f'{m["teamA"]} vs {m["teamB"]}',
        })

    return {
        "labels": labels,
        "matrix": mat,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tournament Tree (Knockout Bracket)
# ─────────────────────────────────────────────────────────────────────────────

def generate_seeds(k: int) -> list[int]:
    """Generate perfect knockout bracket seeding for 2^k teams."""
    if k == 0:
        return [0]
    if k == 1:
        return [0, 1]
    prev = generate_seeds(k - 1)
    size = 2 ** k
    res = []
    for p in prev:
        res.append(p)
        res.append(size - 1 - p)
    return res

def build_tournament_tree(teams: list[str]) -> dict[str, Any]:
    """
    Build a single-elimination knockout tournament tree.
    If team_count not power of 2: add BYE nodes.
    Seeding must follow: 1 vs N, 2 vs N-1, etc.
    """
    n = len(teams)
    if n < 2:
        return {"nodes": [], "edges": [], "rounds": 0}

    # Number of rounds
    num_rounds = math.ceil(math.log2(n))
    bracket_size = 2 ** num_rounds

    # "BYE" are added to the weakest seeds, so they are placed at the end of the original list
    padded = list(teams)
    while len(padded) < bracket_size:
        padded.append("BYE")

    seed_order = generate_seeds(num_rounds)
    seeded_teams = [padded[s] for s in seed_order]

    T = nx.DiGraph()
    node_counter = [0]

    def new_node_id() -> str:
        nid = f"N{node_counter[0]}"
        node_counter[0] += 1
        return nid

    # Round 1 leaf nodes (seeded)
    round1_nodes = []
    for team in seeded_teams:
        nid = new_node_id()
        T.add_node(nid, label=team, round=1, type="team" if team != "BYE" else "bye")
        round1_nodes.append(nid)

    current_round_nodes = round1_nodes
    round_num: int = 1

    while len(current_round_nodes) > 1:
        next_round_nodes = []
        round_num = round_num + 1  # type: ignore[operator]
        for i in range(0, len(current_round_nodes), 2):
            left = current_round_nodes[i]
            right = current_round_nodes[i + 1]

            parent_label = f"Winner R{round_num - 1}" if round_num <= num_rounds else "Champion"
            if round_num == num_rounds + 1:  # type: ignore[operator]
                parent_label = "🏆 Champion"

            parent_id = new_node_id()
            T.add_node(parent_id, label=parent_label, round=round_num, type="match")
            T.add_edge(left, parent_id, round=round_num - 1)
            T.add_edge(right, parent_id, round=round_num - 1)
            next_round_nodes.append(parent_id)

        current_round_nodes = next_round_nodes

    nodes = [
        {"id": nid, "label": d["label"], "round": d["round"], "type": d["type"]}
        for nid, d in T.nodes(data=True)
    ]
    edges = [
        {"source": u, "target": v, "round": d.get("round", 0)}
        for u, v, d in T.edges(data=True)
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "rounds": num_rounds,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Statistics helper
# ─────────────────────────────────────────────────────────────────────────────

def graph_statistics(G: nx.Graph, coloring: dict) -> dict[str, Any]:
    n = G.number_of_nodes()
    m = G.number_of_edges()
    chi = (int(max(coloring.values())) + 1) if coloring else 0
    degrees: dict = dict(G.degree())
    avg_deg = float(f"{sum(degrees.values()) / n:.2f}") if n else 0.0
    max_deg = int(max(degrees.values())) if n else 0
    density = float(round(nx.density(G), 4))
    is_connected: bool = bool(nx.is_connected(G)) if n > 0 else False

    return {
        "num_vertices": n,
        "num_edges": m,
        "chromatic_number": chi,
        "min_time_slots_required": chi,
        "avg_degree": avg_deg,
        "max_degree": max_deg,
        "density": density,
        "is_connected": is_connected,
    }
