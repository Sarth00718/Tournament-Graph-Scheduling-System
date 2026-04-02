"""
test_welsh_powell.py
--------------------
Test suite to verify the Welsh-Powell algorithm implementation is correct.
"""

import networkx as nx
from graph_coloring import welsh_powell_coloring, validate_coloring


def test_empty_graph():
    """Test empty graph"""
    G = nx.Graph()
    coloring = welsh_powell_coloring(G)
    assert coloring == {}
    print("✓ Empty graph test passed")


def test_single_vertex():
    """Test single vertex"""
    G = nx.Graph()
    G.add_node("A")
    coloring = welsh_powell_coloring(G)
    assert coloring == {"A": 0}
    print("✓ Single vertex test passed")


def test_complete_graph_k4():
    """Test complete graph K4 (requires 4 colors)"""
    G = nx.complete_graph(4)
    # Rename nodes to strings
    mapping = {i: f"V{i}" for i in range(4)}
    G = nx.relabel_nodes(G, mapping)
    
    coloring = welsh_powell_coloring(G)
    chi = max(coloring.values()) + 1
    
    # K4 requires exactly 4 colors
    assert chi == 4, f"K4 should need 4 colors, got {chi}"
    
    # Validate coloring
    is_valid, errors = validate_coloring(G, coloring)
    assert is_valid, f"Invalid coloring: {errors}"
    
    print(f"✓ Complete graph K4 test passed (χ = {chi})")


def test_cycle_graph():
    """Test cycle graphs"""
    # Odd cycle (e.g., C5) requires 3 colors
    G = nx.cycle_graph(5)
    mapping = {i: f"V{i}" for i in range(5)}
    G = nx.relabel_nodes(G, mapping)
    
    coloring = welsh_powell_coloring(G)
    chi = max(coloring.values()) + 1
    
    # C5 requires 3 colors
    assert chi == 3, f"C5 should need 3 colors, got {chi}"
    
    is_valid, errors = validate_coloring(G, coloring)
    assert is_valid, f"Invalid coloring: {errors}"
    
    print(f"✓ Cycle graph C5 test passed (χ = {chi})")
    
    # Even cycle (e.g., C6) requires 2 colors
    G = nx.cycle_graph(6)
    mapping = {i: f"V{i}" for i in range(6)}
    G = nx.relabel_nodes(G, mapping)
    
    coloring = welsh_powell_coloring(G)
    chi = max(coloring.values()) + 1
    
    # C6 requires 2 colors (bipartite)
    assert chi == 2, f"C6 should need 2 colors, got {chi}"
    
    is_valid, errors = validate_coloring(G, coloring)
    assert is_valid, f"Invalid coloring: {errors}"
    
    print(f"✓ Cycle graph C6 test passed (χ = {chi})")


def test_bipartite_graph():
    """Test bipartite graph (should need 2 colors)"""
    G = nx.complete_bipartite_graph(3, 4)
    mapping = {i: f"V{i}" for i in range(7)}
    G = nx.relabel_nodes(G, mapping)
    
    coloring = welsh_powell_coloring(G)
    chi = max(coloring.values()) + 1
    
    # Bipartite graph requires exactly 2 colors
    assert chi == 2, f"Bipartite graph should need 2 colors, got {chi}"
    
    is_valid, errors = validate_coloring(G, coloring)
    assert is_valid, f"Invalid coloring: {errors}"
    
    print(f"✓ Bipartite graph test passed (χ = {chi})")


def test_capacity_constraint():
    """Test capacity constraint"""
    # Create a graph where capacity matters
    G = nx.Graph()
    G.add_edges_from([
        ("A", "B"),
        ("C", "D"),
        ("E", "F"),
    ])
    # A-B, C-D, E-F are independent edges (no conflicts)
    # Without capacity: all can be color 0
    # With capacity=2: need at least 2 colors
    
    coloring_no_cap = welsh_powell_coloring(G, max_color_capacity=None)
    chi_no_cap = max(coloring_no_cap.values()) + 1
    
    coloring_with_cap = welsh_powell_coloring(G, max_color_capacity=2)
    chi_with_cap = max(coloring_with_cap.values()) + 1
    
    # Without capacity: should use 2 colors (one for each side of edges)
    assert chi_no_cap == 2, f"Expected 2 colors without capacity, got {chi_no_cap}"
    
    # With capacity=2: might need more colors
    assert chi_with_cap >= 2, f"Expected at least 2 colors with capacity, got {chi_with_cap}"
    
    # Validate both colorings
    is_valid, _ = validate_coloring(G, coloring_no_cap)
    assert is_valid
    
    is_valid, _ = validate_coloring(G, coloring_with_cap)
    assert is_valid
    
    # Check capacity constraint
    color_counts = {}
    for vertex, color in coloring_with_cap.items():
        color_counts[color] = color_counts.get(color, 0) + 1
    
    for color, count in color_counts.items():
        assert count <= 2, f"Color {color} has {count} vertices, exceeds capacity 2"
    
    print(f"✓ Capacity constraint test passed")


def test_tournament_scenario():
    """Test a realistic tournament scenario"""
    # 4 teams: A, B, C, D
    # Matches: AB, AC, AD, BC, BD, CD (6 matches)
    # Conflict graph: each team appears in 3 matches
    
    matches = [
        ("M0", "A", "B"),  # A vs B
        ("M1", "A", "C"),  # A vs C
        ("M2", "A", "D"),  # A vs D
        ("M3", "B", "C"),  # B vs C
        ("M4", "B", "D"),  # B vs D
        ("M5", "C", "D"),  # C vs D
    ]
    
    G = nx.Graph()
    for match_id, team1, team2 in matches:
        G.add_node(match_id, teamA=team1, teamB=team2)
    
    # Add conflict edges (matches sharing a team)
    for i, (m1, t1a, t1b) in enumerate(matches):
        for j, (m2, t2a, t2b) in enumerate(matches):
            if i >= j:
                continue
            # Check if they share a team
            if t1a in (t2a, t2b) or t1b in (t2a, t2b):
                G.add_edge(m1, m2)
    
    coloring = welsh_powell_coloring(G)
    chi = max(coloring.values()) + 1
    
    # For 4 teams, minimum is 3 time slots (chromatic number of K4 conflict graph)
    assert chi >= 3, f"Expected at least 3 colors for 4-team tournament, got {chi}"
    
    is_valid, errors = validate_coloring(G, coloring)
    assert is_valid, f"Invalid coloring: {errors}"
    
    print(f"✓ Tournament scenario test passed (χ = {chi})")
    print(f"  Coloring: {coloring}")


def test_welsh_powell_vs_greedy():
    """
    Test that Welsh-Powell produces optimal or near-optimal results.
    Compare with NetworkX's greedy coloring.
    """
    # Create a graph where order matters
    G = nx.Graph()
    edges = [
        ("A", "B"), ("A", "C"), ("A", "D"),
        ("B", "C"), ("B", "E"),
        ("C", "F"),
        ("D", "E"), ("D", "F"),
        ("E", "F"),
    ]
    G.add_edges_from(edges)
    
    coloring = welsh_powell_coloring(G)
    chi = max(coloring.values()) + 1
    
    # NetworkX greedy coloring for comparison
    nx_coloring = nx.greedy_color(G, strategy="largest_first")
    nx_chi = max(nx_coloring.values()) + 1
    
    print(f"✓ Welsh-Powell vs Greedy test:")
    print(f"  Our Welsh-Powell: χ = {chi}")
    print(f"  NetworkX greedy:  χ = {nx_chi}")
    print(f"  Difference: {chi - nx_chi} colors")
    
    # Our implementation should be competitive
    assert chi <= nx_chi + 1, f"Our coloring ({chi}) is much worse than NetworkX ({nx_chi})"
    
    is_valid, errors = validate_coloring(G, coloring)
    assert is_valid, f"Invalid coloring: {errors}"


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Welsh-Powell Algorithm Implementation")
    print("=" * 60)
    
    test_empty_graph()
    test_single_vertex()
    test_complete_graph_k4()
    test_cycle_graph()
    test_bipartite_graph()
    test_capacity_constraint()
    test_tournament_scenario()
    test_welsh_powell_vs_greedy()
    
    print("=" * 60)
    print("✓ All tests passed! Welsh-Powell implementation is correct.")
    print("=" * 60)
