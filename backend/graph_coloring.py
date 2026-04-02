"""
graph_coloring.py
-----------------
Implements the TRUE Welsh-Powell Graph Coloring Algorithm.

The Welsh-Powell algorithm is a greedy graph coloring algorithm that:
1. Sorts vertices by degree in descending order
2. Assigns colors by processing each color class completely before moving to next
3. For each color, assigns it to all non-adjacent vertices in order

This implementation includes an optional capacity constraint for practical scheduling.

IMPROVEMENTS:
- Correct Welsh-Powell algorithm implementation
- Added proper type hints throughout
- Better handling of empty graphs
- Optional stadium capacity enforcement
- Added logging for debugging
- Comprehensive documentation
"""

from __future__ import annotations
from typing import Dict, List, Set
import networkx as nx  # type: ignore[import]
import logging

logger = logging.getLogger(__name__)


def welsh_powell_coloring(
    G: nx.Graph, 
    max_color_capacity: int | None = None
) -> Dict[str, int]:
    """
    Apply the TRUE Welsh-Powell algorithm and return a vertex coloring.
    
    ALGORITHM (Welsh-Powell):
    1. Sort all vertices by degree in descending order
    2. Assign color 0 to the first vertex
    3. Go through the sorted list and assign color 0 to all vertices 
       that are NOT adjacent to any vertex already colored with color 0
    4. Repeat step 3 for color 1, 2, 3... until all vertices are colored
    
    CAPACITY CONSTRAINT (Extension):
    If max_color_capacity is specified, no color can be assigned to more
    than that many vertices. This ensures each time slot doesn't exceed
    stadium capacity.
    
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

    # Step 1: Compute degrees and sort vertices
    degree_map: Dict[str, int] = dict(G.degree())
    
    # Sort vertices by descending degree, then by ID for determinism
    sorted_vertices: List[str] = sorted(
        G.nodes(),
        key=lambda v: (-degree_map[v], str(v)),
    )
    
    logger.info(
        f"Welsh-Powell: Coloring {num_nodes} vertices, "
        f"max degree = {max(degree_map.values()) if degree_map else 0}"
    )

    # Step 2: Welsh-Powell coloring algorithm
    coloring: Dict[str, int] = {}
    color_counts: Dict[int, int] = {}
    uncolored: Set[str] = set(sorted_vertices)
    current_color = 0

    while uncolored:
        # Start a new color class
        color_class: List[str] = []
        vertices_to_remove: List[str] = []
        
        for vertex in sorted_vertices:
            # Skip if already colored
            if vertex not in uncolored:
                continue
            
            # Check capacity constraint
            if max_color_capacity is not None:
                if len(color_class) >= max_color_capacity:
                    break  # This color is at capacity, move to next color
            
            # Check if vertex can use current color
            # (must not be adjacent to any vertex already in this color class)
            can_use_color = True
            for colored_vertex in color_class:
                if G.has_edge(vertex, colored_vertex):
                    can_use_color = False
                    break
            
            if can_use_color:
                # Assign current color to this vertex
                coloring[vertex] = current_color
                color_class.append(vertex)
                vertices_to_remove.append(vertex)
        
        # Remove colored vertices from uncolored set
        for vertex in vertices_to_remove:
            uncolored.remove(vertex)
        
        # Update color count
        color_counts[current_color] = len(color_class)
        
        logger.debug(
            f"Color {current_color}: assigned to {len(color_class)} vertices"
        )
        
        # Move to next color
        current_color += 1
        
        # Safety check: prevent infinite loop
        if current_color > num_nodes:
            logger.error(
                f"Welsh-Powell exceeded {num_nodes} colors. This should never happen!"
            )
            break

    # Log results
    chi = max(coloring.values()) + 1 if coloring else 0
    logger.info(
        f"Welsh-Powell complete: χ(G) = {chi}, "
        f"color distribution = {dict(sorted(color_counts.items()))}"
    )
    
    # Validate capacity constraint
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
