from conflict_graph import generate_matches, build_conflict_graph, graph_to_dict  # type: ignore[import-not-found]
from graph_coloring import welsh_powell_coloring, chromatic_number, coloring_summary  # type: ignore[import-not-found]
from schedule_generator import generate_schedule  # type: ignore[import-not-found]
from travel_optimizer import build_stadium_graph, compute_team_travel, stadium_graph_to_dict  # type: ignore[import-not-found]
from visualization import build_adjacency_matrix, build_tournament_tree, graph_statistics  # type: ignore[import-not-found]
from data_loader import parse_payload  # type: ignore[import-not-found]

print("All module imports OK")

# Test full pipeline
teams_raw = ['TeamA', 'TeamB', 'TeamC', 'TeamD']
stadiums_raw = [
    {'name': 'StadiumX', 'lat': 18.9, 'lng': 72.8},
    {'name': 'StadiumY', 'lat': 22.5, 'lng': 88.3}
]
rules_raw = {
    'start_date': '2024-06-01',
    'end_date': '2024-06-30',
    'time_slots': ['Morning', 'Evening'],
    'rest_days_between_matches': 1
}

payload = {'teams': teams_raw, 'stadiums': stadiums_raw, 'rules': rules_raw}
t, s, r = parse_payload(payload)
matches = generate_matches(t)
G = build_conflict_graph(t, matches, r['rest_days'])
coloring = welsh_powell_coloring(G)
chi = chromatic_number(coloring)
color_groups = coloring_summary(coloring)
schedule = generate_schedule(matches, coloring, s, r)
stadium_graph = build_stadium_graph(s)
travel = compute_team_travel(schedule, stadium_graph)
adj = build_adjacency_matrix(G)
tree = build_tournament_tree(t)
stats = graph_statistics(G, coloring)
graph_dict = graph_to_dict(G, coloring)

print(f"Teams: {len(t)}, Matches: {len(matches)}, chi(G)={chi}")
print(f"Schedule rows: {len(schedule)}")
print(f"Travel teams: {list(travel.keys())}")
print(f"Adjacency matrix: {len(adj['matrix'])}x{len(adj['matrix'][0])}")
print(f"Tournament tree nodes: {len(tree['nodes'])}")
print(f"Graph dict nodes: {len(graph_dict['nodes'])}")
print("ALL TESTS PASSED")
