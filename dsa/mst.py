import heapq
from dsa.union_find import UnionFind

def kruskal_mst(vertices, edges):
    """
    Kruskal's MST algorithm.
    Time Complexity: O(E log E)
    edges: list of (u, v, weight)
    Returns: (mst_edges, total_cost, history_steps)
    """
    # Kruskal considers the cheapest edge first (greedy algorithm).
    sorted_edges = sorted(edges, key=lambda edge: edge[2])
    uf = UnionFind(vertices)
    mst = []
    history = []
    total_cost = 0

    for u, v, weight in sorted_edges:
        # Union-Find accepts an edge only when its endpoints are in different groups.
        if uf.union(u, v):
            mst.append((u, v, weight))
            total_cost += weight
            history.append({'edge': (u, v, weight), 'action': 'ACCEPT', 'reason': 'Minimum valid edge'})
        else:
            history.append({'edge': (u, v, weight), 'action': 'REJECT', 'reason': 'Cycle detected'})

        # A spanning tree with V vertices always contains V - 1 edges.
        if len(mst) == len(vertices) - 1:
            break

    return mst, total_cost, history

def prims_mst(vertices, adj_list, start_vertex=None):
    """
    Prim's MST algorithm with min-heap.
    Time Complexity: O(E log V)
    adj_list: dict where adj_list[u] = [(v, weight), ...]
    Returns: (mst_edges, total_cost)
    """
    if not vertices:
        return [], 0

    start = vertices[0] if start_vertex is None else start_vertex
    visited = {start}
    mst = []
    total_cost = 0
    heap = []

    # The min-heap lets us quickly choose the cheapest edge leaving the visited group.
    for neighbor, weight in adj_list.get(start, []):
        heapq.heappush(heap, (weight, start, neighbor))

    while heap and len(visited) < len(vertices):
        weight, u, v = heapq.heappop(heap)
        # Ignore edges that lead to a vertex already in the tree.
        if v in visited:
            continue

        visited.add(v)
        mst.append((u, v, weight))
        total_cost += weight

        for neighbor, next_w in adj_list.get(v, []):
            if neighbor not in visited:
                heapq.heappush(heap, (next_w, v, neighbor))

    return mst, total_cost
def kruskal_steps(vertices, edges):
    """
    Generator that yields each edge inspection step of Kruskal's algorithm.
    Yields: (u, v, weight, accepted: bool, reason: str)
    """
    from dsa.union_find import UnionFind
    sorted_edges = sorted(edges, key=lambda x: x[2])
    uf = UnionFind(vertices)
    edges_accepted = 0
    target_edges = len(vertices) - 1

    for u, v, weight in sorted_edges:
        if edges_accepted >= target_edges:
            break

        if uf.union(u, v):
            edges_accepted += 1
            yield (u, v, weight, True, "Minimum non-cyclic corridor")
        else:
            yield (u, v, weight, False, "Forms cycle (Union-Find rejected)")
