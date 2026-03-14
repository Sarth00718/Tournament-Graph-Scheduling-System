from conflict_graph import generate_matches, build_conflict_graph, graph_to_dict  # type: ignore[import-not-found]
from graph_coloring import welsh_powell_coloring, chromatic_number, coloring_summary  # type: ignore[import-not-found]
from schedule_generator import generate_schedule  # type: ignore[import-not-found]
from travel_optimizer import build_stadium_graph, compute_team_travel, stadium_graph_to_dict  # type: ignore[import-not-found]
from visualization import build_adjacency_matrix, build_tournament_tree, graph_statistics  # type: ignore[import-not-found]
from data_loader import parse_payload  # type: ignore[import-not-found]

print("All module imports OK")

def test_teams_count(num_teams):
    print(f"\n--- Testing with {num_teams} teams ---")
    teams_raw = [f'Team{chr(65+i)}' for i in range(num_teams)]
    stadiums_raw = [
        {'name': 'StadiumA', 'lat': 18.9, 'lng': 72.8},
        {'name': 'StadiumB', 'lat': 22.5, 'lng': 88.3},
        {'name': 'StadiumC', 'lat': 12.9, 'lng': 77.5}
    ]
    rules_raw = {
        'start_date': '2024-06-01',
        'end_date': '2024-06-30',
        'time_slots': ['Morning', 'Afternoon', 'Evening'],
        'rest_days_between_matches': 1
    }

    payload = {'teams': teams_raw, 'stadiums': stadiums_raw, 'rules': rules_raw}
    t, s, r = parse_payload(payload)
    matches = generate_matches(t)
    G = build_conflict_graph(t, matches, r['rest_days'])
    coloring = welsh_powell_coloring(G, max_color_capacity=len(s))
    chi = chromatic_number(coloring)
    schedule = generate_schedule(matches, coloring, s, r)
    stadium_graph = build_stadium_graph(s)
    travel = compute_team_travel(schedule, stadium_graph)
    adj = build_adjacency_matrix(G, matches, schedule, r['rest_days'])
    tree = build_tournament_tree(t)
    
    # Check Rest Days
    from datetime import date
    for team, travel_data in travel.items():
        team_matches = [m for m in schedule if m['teamA'] == team or m['teamB'] == team]
        team_matches.sort(key=lambda m: m['date'])
        for i in range(1, len(team_matches)):
            d1 = date.fromisoformat(team_matches[i-1]['date'])
            d2 = date.fromisoformat(team_matches[i]['date'])
            assert (d2 - d1).days >= r['rest_days'], f"Rest day violation for {team}"
            
    # Check No Concurrent Same Stadium
    slot_stadium = set()
    for m in schedule:
        key = (m['date'], m['time_slot'], m['stadium'])
        assert key not in slot_stadium, f"Stadium collision: {key}"
        slot_stadium.add(key)
        
    print(f"Teams: {num_teams}, Matches: {len(schedule)}, Slots needed (chromatic_number): {chi}")
    print(f"Tournament rounds: {tree['rounds']}")
    print("Test passed without errors or conflicts")


for count in [4, 6, 10, 20]:
    test_teams_count(count)

print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY.")
