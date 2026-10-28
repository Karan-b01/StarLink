import heapq

def dijkstra_shortest_path(vertices, adj_list, source, target):
    """
    Dijkstra's shortest path algorithm.
    Time Complexity: O((V + E) log V)
    """
    # Store the best known distance and previous vertex for each destination.
    distances = {v: float('inf') for v in vertices}
    previous = {v: None for v in vertices}
    distances[source] = 0
    # A min-heap always gives us the not-yet-checked vertex with the lowest cost.
    pq = [(0, source)]

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if curr_dist > distances[u]:
            continue
        if u == target:
            break

        for v, weight in adj_list.get(u, []):
            # Replace a route only when the new route is shorter.
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                previous[v] = u
                heapq.heappush(pq, (distances[v], v))

    if distances[target] == float('inf'):
        return float('inf'), []

    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = previous[curr]
    path.reverse()

    return distances[target], path
