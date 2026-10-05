# test_dsa.py
from dsa.union_find import UnionFind
from dsa.mst import kruskal_mst, prims_mst
from dsa.graph import is_fully_connected
from dsa.history_stack import ActionHistory
from dsa.dijkstra import dijkstra_shortest_path

def test_union_find():
    uf = UnionFind([0, 1, 2, 3])
    assert uf.union(0, 1) is True
    assert uf.union(1, 2) is True
    # Cycle test
    assert uf.union(0, 2) is False, "Cycle detection failed!"
    assert uf.connected(0, 2) is True
    print("[PASS] Union-Find & Cycle Rejection")

def test_mst_parity():
    vertices = [0, 1, 2, 3]
    edges = [
        (0, 1, 1),
        (1, 2, 2),
        (2, 3, 3),
        (0, 2, 4),
        (1, 3, 5)
    ]
    adj = {0: [(1, 1), (2, 4)], 1: [(0, 1), (2, 2), (3, 5)], 2: [(1, 2), (0, 4), (3, 3)], 3: [(2, 3), (1, 5)]}

    k_mst, k_cost, _ = kruskal_mst(vertices, edges)
    p_mst, p_cost = prims_mst(vertices, adj)

    assert k_cost == p_cost == 6, f"MST Cost mismatch: Kruskal={k_cost}, Prim={p_cost}"
    print("[PASS] MST Algorithms (Kruskal & Prim Parity)")

def test_connectivity():
    vertices = [0, 1, 2, 3]
    valid_edges = [(0, 1, 1), (1, 2, 2), (2, 3, 3)]
    disconnected_edges = [(0, 1, 1), (2, 3, 3)]

    assert is_fully_connected(vertices, valid_edges) is True
    assert is_fully_connected(vertices, disconnected_edges) is False
    print("[PASS] BFS Connectivity Verification")

def test_history_stacks():
    history = ActionHistory()
    history.record_action((0, 1, 5), 5)
    history.record_action((1, 2, 3), 3)

    undone = history.undo()
    assert undone['edge'] == (1, 2, 3)
    redone = history.redo()
    assert redone['edge'] == (1, 2, 3)
    print("[PASS] Undo/Redo Stacks")

def test_dijkstra():
    vertices = [0, 1, 2, 3]
    adj = {
        0: [(1, 2), (2, 5)],
        1: [(0, 2), (2, 1), (3, 4)],
        2: [(0, 5), (1, 1), (3, 1)],
        3: [(1, 4), (2, 1)]
    }
    dist, path = dijkstra_shortest_path(vertices, adj, 0, 3)
    assert dist == 4 and path == [0, 1, 2, 3], f"Dijkstra failed: {dist}, {path}"
    print("[PASS] Dijkstra Shortest Path")

if __name__ == "__main__":
    print("--- Running StarLink DSA Test Suite ---")
    test_union_find()
    test_mst_parity()
    test_connectivity()
    test_history_stacks()
    test_dijkstra()
    print("--- ALL ALGORITHMIC TESTS PASSED PERFECTLY ---")