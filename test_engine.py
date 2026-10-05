from engine.level_loader import load_level_from_json
from engine.game_state import GameState

def test_engine():
    level_data = load_level_from_json("levels/world1.json")
    state = GameState(level_data)

    print(f"Loaded: {state.name}")
    print(f"Precomputed Kruskal MST Cost: {state.optimal_cost}")

    # Connect edge (3, 4) -> valid
    ok, msg = state.connect_edge(3, 4)
    assert ok is True

    # Connect edge (0, 1) -> valid
    ok, msg = state.connect_edge(0, 1)
    assert ok is True

    # Undo edge (0, 1)
    state.undo()
    assert len(state.selected_edges) == 1
    print("[PASS] Game Engine State & Move Management")

if __name__ == "__main__":
    test_engine()