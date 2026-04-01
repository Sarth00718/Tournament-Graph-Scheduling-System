"""
graph_coloring.py
-----------------
Implements the EXACT Welsh-Powell Graph Coloring Algorithm.

IMPROVEMENTS:
- Added proper type hints throughout
- Better handling of empty graphs
- Improved stadium capacity enforcement
- Added logging for debugging
- Better documentation
"""

from __future__ import annotations
from typing import Dict, List
import networkx as nx  # type: ignore[import]
import logging

logger = logging.getLogger(__name__)


def welsh_powell_coloring(
    G: nx.Graph, 
    max_color_capacity: int | None = None
) -> Dict[str, int]:
    """
    Apply the Welsh-Powell algorithm and return a vertex coloring.
    
    Algorithm:
    1. Sort vertices by degree (descending)
    2. For each vertex, assign the smallest color that:
       - Is not used by any neighbor (conflict-free)
       - Does not exceed capacity limit (if specified)
    
    Parameters
    ----------
    G : nx.Graph
        The conflict graph where nodes are matches
    max_color_capacity : int | None
        Maximum number of vertices per color (e.g., stadium count).
        If None, no capacity limit is enforced.

    Returns
    -------
    coloring : Dict[str, int]
        Mapping from vertex ID to color (0-indexed).
        Chromatic number = max(coloring.values()) + 1
    
    Raises
    ------
    ValueError: If graph is invalid
    """
    # Handle empty graph
    if G is None:
        logger.warning("Received None graph, returning empty coloring")
        return {}
    
    num_nodes = G.number_of_nodes()
    if num_nodes == 0:
        logger.info("Empty graph, returning empty coloring")
        return {}

    # Step 1: Compute degrees
    degree_map: Dict[str, int] = dict(G.degree())
    
    # Step 2: Sort vertices by descending degree, then by ID for determinism
    sorted_vertices: List[str] = sorted(
        G.nodes(),
        key=lambda v: (-degree_map[v], str(v)),
    )
    
    logger.info(
        f"Welsh-Powell: Coloring {num_nodes} vertices, "
        f"max degree = {max(degree_map.values()) if degree_map else 0}"
    )

    # Step 3: Greedy coloring with capacity constraints
    coloring: Dict[str, int] = {}
    color_counts: Dict[int, int] = {}

    for vertex in sorted_vertices:
        # Collect colors already used by neighbors
        neighbour_colors: set[int] = {
            coloring[nbr]
            for nbr in G.neighbors(vertex)
            if nbr in coloring
        }

        # Find the smallest valid color
        color = 0
        while True:
            # Check conflict constraint: adjacent vertices must have different colors
            if color in neighbour_colors:
                color += 1
                continue
            
            # Check capacity constraint: no color should exceed max_color_capacity
            if max_color_capacity is not None:
                current_count = color_counts.get(color, 0)
                if current_count >= max_color_capacity:
                    color += 1
                    continue
            
            # Valid color found
            break

        coloring[vertex] = color
        color_counts[color] = color_counts.get(color, 0) + 1

    # Log results
    chi = max(coloring.values()) + 1 if coloring else 0
    logger.info(
        f"Welsh-Powell complete: χ(G) = {chi}, "
        f"color distribution = {dict(sorted(color_counts.items()))}"
    )
    
    # Warn if capacity was exceeded (shouldn't happen with correct algorithm)
    if max_color_capacity is not None:
        for color, count in color_counts.items():
            if count > max_color_capacity:
                logger.error(
                    f"BUG: Color {color} has {count} vertices but capacity is {max_color_capacity}"
                )

    return coloring


def chromatic_number(coloring: Dict[str, int]) -> int:
    """
    Return the chromatic number (minimum time slots required).
    
    Parameters
    ----------
    coloring : Dict[str, int]
        Vertex coloring from welsh_powell_coloring
    
    Returns
    -------
    int : Chromatic number (number of colors used)
    """
    if not coloring:
        return 0
    return max(coloring.values()) + 1


def coloring_summary(coloring: Dict[str, int]) -> Dict[int, List[str]]:
    """
    Group vertices by color (time slot group).
    
    Parameters
    ----------
    coloring : Dict[str, int]
        Vertex coloring from welsh_powell_coloring

    Returns
    -------
    Dict[int, List[str]]
        Mapping from color to list of vertex IDs with that color
    """
    groups: Dict[int, List[str]] = {}
    for vertex, color in coloring.items():
        groups.setdefault(color, []).append(vertex)
    return groups


def validate_coloring(G: nx.Graph, coloring: Dict[str, int]) -> tuple[bool, List[str]]:
    """
    Validate that a coloring is valid (no adjacent vertices share a color).
    
    Parameters
    ----------
    G : nx.Graph
        The conflict graph
    coloring : Dict[str, int]
        Vertex coloring to validate
    
    Returns
    -------
    (is_valid, errors) : tuple[bool, List[str]]
        True if valid, False otherwise, plus list of error messages
    """
    errors: List[str] = []
    
    # Check all vertices are colored
    for node in G.nodes():
        if node not in coloring:
            errors.append(f"Vertex {node} is not colored")
    
    # Check no adjacent vertices share a color
    for u, v in G.edges():
        if u in coloring and v in coloring:
            if coloring[u] == coloring[v]:
                errors.append(
                    f"Adjacent vertices {u} and {v} both have color {coloring[u]}"
                )
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info("Coloring validation: PASSED")
    else:
        logger.error(f"Coloring validation: FAILED with {len(errors)} errors")
        for error in errors[:5]:  # Log first 5 errors
            logger.error(f"  - {error}")
    
    return is_valid, errors
