import heapq
from dsa.union_find import UnionFind

def kruskal_mst(vertices, edges):
    """
    Kruskal's MST algorithm.
    Time Complexity: O(E log E)
    edges: list of (u, v, weight)
    Returns: (mst_edges, total_cost, history_steps)
    """
    sorted_edges = sorted(edges, key=lambda x: x[2])
    uf = UnionFind(vertices)
    mst = []
    history = []
    total_cost = 0

    for u, v, weight in sorted_edges:
        if not uf.connected(u, v):
            uf.union(u, v)
            mst.append((u, v, weight))
            total_cost += weight
            history.append({'edge': (u, v, weight), 'action': 'ACCEPT', 'reason': 'Minimum valid edge'})
        else:
            history.append({'edge': (u, v, weight), 'action': 'REJECT', 'reason': 'Cycle detected'})

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

    for neighbor, weight in adj_list.get(start, []):
        heapq.heappush(heap, (weight, start, neighbor))

    while heap and len(visited) < len(vertices):
        weight, u, v = heapq.heappop(heap)
        if v in visited:
            continue

        visited.add(v)
        mst.append((u, v, weight))
        total_cost += weight

        for neighbor, next_w in adj_list.get(v, []):
            if neighbor not in visited:
                heapq.heappush(heap, (next_w, v, neighbor))

    return mst, total_cost