
def dijkstra_shortest_path(vertices, adj_list, source, target):
    # Initial table
    known = {v: 0 for v in vertices}
    dist = {v: float('inf') for v in vertices}
    prev = {v: None for v in vertices}

    dist[source] = 0

    while True:
        v = None
        

        # Find the unknown vertex with minimum distance
        for node in vertices:
            if known[node] == 0:
                if v is None or dist[node] < dist[v]:
                    v = node

        # Stop if no reachable vertex remains
        if v is None or dist[v] == float('inf'):
            break

        known[v] = 1

        # Stop when the target is processed
        if v == target:
            break

        # Update adjacent vertices
        for w, cost in adj_list.get(v, []):
            if known[w] == 0:
                new_dist = dist[v] + cost

                if new_dist < dist[w]:
                    dist[w] = new_dist
                    prev[w] = v

    # No path exists
    if dist[target] == float('inf'):
        return float('inf'), []

    # Reconstruct the shortest path
    path = []
    curr = target

    while curr is not None:
        path.append(curr)
        curr = prev[curr]

    path.reverse()

    return dist[target], path
