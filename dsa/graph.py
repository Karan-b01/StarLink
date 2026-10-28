from collections import deque

def is_fully_connected(vertices, edges):
    """
    BFS traversal.
    Time Complexity: O(V + E)
    Returns True if all vertices belong to a single connected component.
    """
    if not vertices:
        return True
    if len(edges) < len(vertices) - 1:
        return False

    # Convert the edge list into an adjacency list for quick neighbor lookups.
    adj = {v: [] for v in vertices}
    for u, v, _ in edges:
        adj[u].append(v)
        adj[v].append(u)

    # BFS uses a queue to visit each reachable vertex in turn.
    visited = set()
    queue = deque([vertices[0]])
    visited.add(vertices[0])

    while queue:
        curr = queue.popleft()
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return len(visited) == len(vertices)
