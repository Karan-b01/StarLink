import heapq

def dijkstra_shortest_path(vertices, adj_list, source, target):
    """
    Dijkstra's shortest path algorithm.
    Time Complexity: O((V + E) log V)
    """
    distances = {v: float('inf') for v in vertices}
    previous = {v: None for v in vertices}
    distances[source] = 0
    pq = [(0, source)]

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if curr_dist > distances[u]:
            continue
        if u == target:
            break

        for v, weight in adj_list.get(u, []):
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                previous[v] = u
                heapq.heappush(pq, (distances[v], v))

    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = previous[curr]
    path.reverse()

    return distances[target], path