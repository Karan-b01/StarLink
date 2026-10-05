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

    adj = {v: [] for v in vertices}
    for u, v, _ in edges:
        adj[u].append(v)
        adj[v].append(u)

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