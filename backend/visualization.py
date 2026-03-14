"""
visualization.py
----------------
Generates adjacency matrix data and tournament tree structure
for the API responses.
"""

from __future__ import annotations
from typing import Any
from itertools import combinations
import math

import networkx as nx  # type: ignore[import]


# ─────────────────────────────────────────────────────────────────────────────
# Adjacency Matrix (pure Python — no numpy dependency)
# ─────────────────────────────────────────────────────────────────────────────

def build_adjacency_matrix(G: nx.Graph) -> dict[str, Any]:
    """
    Build the adjacency matrix for the conflict graph.

    Returns
    -------
    {
        "labels": [...],          # ordered list of node ids
        "matrix": [[0,1,...], ...]  # 2D adjacency matrix (0/1 integers)
    }
    """
    nodes = sorted(G.nodes())
    n = len(nodes)
    idx = {node: i for i, node in enumerate(nodes)}

    # Build matrix using plain Python lists (no numpy required)
    mat = [[0] * n for _ in range(n)]

    for u, v in G.edges():
        mat[idx[u]][idx[v]] = 1
        mat[idx[v]][idx[u]] = 1

    labels = []
    for node, data in G.nodes(data=True):
        labels.append({
            "id": node,
            "label": data.get("label", node),
        })
    # Sort labels to match matrix row order
    labels.sort(key=lambda x: x["id"])

    return {
        "labels": labels,
        "matrix": mat,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tournament Tree (Knockout Bracket)
# ─────────────────────────────────────────────────────────────────────────────

def build_tournament_tree(teams: list[str]) -> dict[str, Any]:
    """
    Build a single-elimination knockout tournament tree
    as a directed rooted tree (nx.DiGraph).

    The tree is returned as JSON-serialisable node/edge lists
    suitable for rendering a bracket in the frontend.

    Round 1 seeds teams by natural order.
    Bye nodes are created if the number of teams is not a power of 2.

    Returns
    -------
    {
        "nodes": [{"id": ..., "label": ..., "round": int, "type": ...}, ...],
        "edges": [{"source": ..., "target": ..., "round": int}, ...],
        "rounds": int,
    }
    """
    n = len(teams)
    if n < 2:
        return {"nodes": [], "edges": [], "rounds": 0}

    # Number of rounds
    num_rounds = math.ceil(math.log2(n))
    bracket_size = 2 ** num_rounds

    # Pad with "BYE" entries
    padded = list(teams) + ["BYE"] * (bracket_size - n)

    T = nx.DiGraph()
    node_counter = [0]

    def new_node_id() -> str:
        nid = f"N{node_counter[0]}"
        node_counter[0] = node_counter[0] + 1
        return nid

    # Round 1 leaf nodes (actual teams)
    round1_nodes = []
    for team in padded:
        nid = new_node_id()
        T.add_node(nid, label=team, round=1, type="team" if team != "BYE" else "bye")
        round1_nodes.append(nid)

    current_round_nodes = round1_nodes
    round_num = 1

    while len(current_round_nodes) > 1:
        next_round_nodes = []
        round_num += 1
        for i in range(0, len(current_round_nodes), 2):
            left = current_round_nodes[i]
            right = current_round_nodes[i + 1] if i + 1 < len(current_round_nodes) else None

            parent_label = f"Winner R{round_num - 1}" if round_num <= num_rounds else "Champion"
            if round_num == num_rounds + 1:
                parent_label = "🏆 Champion"

            parent_id = new_node_id()
            T.add_node(parent_id, label=parent_label, round=round_num, type="match")
            T.add_edge(left, parent_id, round=round_num - 1)
            if right:
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
    """Return key graph-theory metrics for display in the frontend."""
    n = G.number_of_nodes()
    m = G.number_of_edges()
    chi = (max(coloring.values()) + 1) if coloring else 0
    degrees: dict = dict(G.degree())
    avg_deg = float(round(sum(degrees.values()) / n, 2)) if n else 0.0
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
