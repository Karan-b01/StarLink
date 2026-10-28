class UnionFind:
    """Track which vertices belong to the same connected group."""

    def __init__(self, elements):
        # Every element starts in its own group. These dictionaries are hash maps.
        self.parent = {elem: elem for elem in elements}
        self.rank = {elem: 0 for elem in elements}
        self.num_components = len(elements)

    def find(self, i):
        """Return the group's representative, shortening the path as we go."""
        if self.parent[i] != i:
            # Path compression makes future lookups faster.
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, u, v):
        """
        Unites components containing u and v.
        Returns False if a cycle is detected, True on success.
        """
        root_u = self.find(u)
        root_v = self.find(v)

        if root_u == root_v:
            return False  # Same group: adding this edge would create a cycle.

        # Union by rank attaches the shorter tree below the taller one.
        if self.rank[root_u] < self.rank[root_v]:
            self.parent[root_u] = root_v
        elif self.rank[root_u] > self.rank[root_v]:
            self.parent[root_v] = root_u
        else:
            self.parent[root_v] = root_u
            self.rank[root_u] += 1

        self.num_components -= 1
        return True

    def connected(self, u, v):
        return self.find(u) == self.find(v)
