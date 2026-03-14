"""
graph_coloring.py
-----------------
Implements the EXACT Welsh-Powell Graph Coloring Algorithm.
"""

from __future__ import annotations
import networkx as nx  # type: ignore[import]


# ─────────────────────────────────────────────────────────────────────────────
# Welsh-Powell Coloring
# ─────────────────────────────────────────────────────────────────────────────

def welsh_powell_coloring(G: nx.Graph, max_color_capacity: int | None = None) -> dict:
    """
    Apply the Welsh-Powell algorithm and return a vertex coloring.
    If max_color_capacity is provided, it guarantees no color is assigned
    to more than `max_color_capacity` vertices (e.g., stadium count).

    Returns
    -------
    coloring : dict[node_id, color_int]
        Mapping from vertex to its assigned color (0-indexed).
    """
    if G.number_of_nodes() == 0:
        return {}

    # 1. Compute degrees
    degree_map: dict = dict(G.degree())

    # 2. Sort descending
    sorted_vertices: list = sorted(
        G.nodes(),
        key=lambda v: (-degree_map[v], str(v)),
    )

    # 3. Greedy coloring
    coloring: dict = {}
    color_counts: dict = {}

    for vertex in sorted_vertices:
        neighbour_colors: set = {
            coloring[nbr]
            for nbr in G.neighbors(vertex)
            if nbr in coloring
        }

        color = 0
        while True:
            # 4. Ensure adjacent vertices never share color
            if color in neighbour_colors:
                color += 1
                continue
            
            # Ensure stadium capacity limit
            if max_color_capacity is not None and color_counts.get(color, 0) >= max_color_capacity:
                color += 1
                continue
                
            # Valid color found
            break

        coloring[vertex] = color
        color_counts[color] = color_counts.get(color, 0) + 1

    return coloring


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def chromatic_number(coloring: dict) -> int:
    """Return the chromatic number (minimum slots required)."""
    if not coloring:
        return 0
    return max(coloring.values()) + 1


def coloring_summary(coloring: dict) -> dict:
    """Group vertices by color (time slot group)."""
    groups: dict = {}
    for vertex, color in coloring.items():
        groups.setdefault(color, []).append(vertex)
    return groups
