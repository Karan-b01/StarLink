import json
import math
import os
import random
from dsa.union_find import UnionFind


class StarNode:
    def __init__(self, id_, name, x, y):
        self.id = id_
        self.name = name
        self.x = x
        self.y = y

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
        }


def load_level_from_json(filepath):
    """Loads and validates a level definition from JSON."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Level file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    stars = [
        StarNode(
            s["id"],
            s.get("name", f"S-{s['id']}"),
            s["x"],
            s["y"],
        )
        for s in data["stars"]
    ]
    edges = [tuple(e) for e in data["edges"]]  # (u, v, cost)
    return {
        "world_id": data.get("world_id", 1),
        "name": data.get("name", "Unknown Sector"),
        "story": data.get("story", ""),
        "difficulty": data.get("difficulty", "MEDIUM"),
        "energy_budget": data["energy_budget"],
        "stars": stars,
        "edges": edges,
        "edge_rules": data.get("edge_rules", []),
    }


def generate_procedural_level(num_stars=7, width=950, height=580):
    """
    Generates a guaranteed-connected procedural graph with unstable corridors.
    """
    stars = []
    for i in range(num_stars):
        x = random.randint(140, width - 100)
        y = random.randint(140, height - 100)
        stars.append(StarNode(i, f"Gen-{i}", x, y))

    # Connect nearby stars to create a graph
    candidate_edges = set()
    for i in range(num_stars):
        for j in range(i + 1, num_stars):
            dist = math.hypot(stars[i].x - stars[j].x, stars[i].y - stars[j].y)
            if dist < 340:
                cost = max(2, int(dist // 28))
                candidate_edges.add((min(i, j), max(i, j), cost))

    # Guarantee graph connectivity using Disjoint Set Union
    uf = UnionFind([s.id for s in stars])
    for u, v, _ in candidate_edges:
        uf.union(u, v)

    while uf.num_components > 1:
        best_pair = None
        best_dist = float("inf")
        for i in range(num_stars):
            for j in range(i + 1, num_stars):
                if uf.find(i) != uf.find(j):
                    d = math.hypot(stars[i].x - stars[j].x, stars[i].y - stars[j].y)
                    if d < best_dist:
                        best_dist = d
                        best_pair = (i, j)
        i, j = best_pair
        cost = max(2, int(best_dist // 28))
        candidate_edges.add((min(i, j), max(i, j), cost))
        uf.union(i, j)

    edges = list(candidate_edges)
    sorted_edges = sorted(edges, key=lambda e: e[2])
    edge_rules = []
    if len(sorted_edges) >= 2:
        edge_rules = [
            {"edge": [sorted_edges[0][0], sorted_edges[0][1]], "collapse_after": 3},
            {"edge": [sorted_edges[1][0], sorted_edges[1][1]], "collapse_after": 5}
        ]
    elif len(sorted_edges) == 1:
        edge_rules = [
            {"edge": [sorted_edges[0][0], sorted_edges[0][1]], "collapse_after": 3}
        ]

    budget = sum(e[2] for e in sorted_edges[:num_stars - 1]) + int(num_stars * 2.5)
    return {
        "world_id": 99,
        "name": "Procedural Deep Space",
        "story": "Chart uncharted stars before unstable navigation corridors collapse.",
        "difficulty": "DYNAMIC",
        "energy_budget": max(25, budget),
        "stars": stars,
        "edges": edges,
        "edge_rules": edge_rules,
    }
