"""
graph_coloring.py
-----------------
Implements the EXACT Welsh-Powell Graph Coloring Algorithm.

Algorithm
---------
1. Compute the degree of every vertex.
2. Sort vertices in DESCENDING order of degree
   (ties broken by vertex id for determinism).
3. Iterate through the sorted list:
      a. If the vertex has no color yet, assign it the lowest
         non-negative integer that does not appear among any
         already-colored NEIGHBOUR.
4. Return {vertex: color} for all vertices.

The chromatic number χ(G) = max(coloring.values()) + 1,
representing the MINIMUM number of time slots required.
"""

from __future__ import annotations
import networkx as nx  # type: ignore[import]


# ─────────────────────────────────────────────────────────────────────────────
# Welsh-Powell Coloring
# ─────────────────────────────────────────────────────────────────────────────

def welsh_powell_coloring(G: nx.Graph) -> dict:
    """
    Apply the Welsh-Powell algorithm and return a vertex coloring.

    Parameters
    ----------
    G : networkx.Graph
        The conflict graph where each node is a match.

    Returns
    -------
    coloring : dict[node_id, color_int]
        Mapping from vertex to its assigned color (0-indexed).
        The chromatic number is  max(coloring.values()) + 1.
    """
    if G.number_of_nodes() == 0:
        return {}

    # ── STEP 1: Compute degrees ───────────────────────────────────────────────
    degree_map: dict = dict(G.degree())

    # ── STEP 2: Sort vertices by descending degree, then by id for stability ──
    sorted_vertices: list = sorted(
        G.nodes(),
        key=lambda v: (-degree_map[v], str(v)),
    )

    # ── STEP 3: Greedy coloring on sorted list ────────────────────────────────
    coloring: dict = {}

    for vertex in sorted_vertices:
        # Collect colors already used by neighbours
        neighbour_colors: set = {
            coloring[nbr]
            for nbr in G.neighbors(vertex)
            if nbr in coloring
        }

        # Assign the smallest non-negative color not in neighbour_colors
        color = 0
        while color in neighbour_colors:
            color += 1

        coloring[vertex] = color

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
    """
    Group vertices by color (time slot group).

    Returns
    -------
    {color_int: [vertex_id, ...], ...}
    """
    groups: dict = {}
    for vertex, color in coloring.items():
        groups.setdefault(color, []).append(vertex)
    return groups
