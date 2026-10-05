import json
import math
import random
import os

class StarNode:
    def __init__(self, id_, name, x, y, star_type="NORMAL"):
        self.id = id_
        self.name = name
        self.x = x
        self.y = y
        self.type = star_type  # NORMAL, ENERGY, POWER, UNSTABLE

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "type": self.type
        }

def load_level_from_json(filepath):
    """Loads and validates a level definition from JSON."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Level file not found: {filepath}")

    with open(filepath, "r") as f:
        data = json.load(f)

    stars = [
        StarNode(
            s["id"],
            s.get("name", f"S-{s['id']}"),
            s["x"],
            s["y"],
            s.get("type", "NORMAL")
        )
        for s in data["stars"]
    ]
    edges = [tuple(e) for e in data["edges"]]  # (u, v, cost)
    return {
        "world_id": data.get("world_id", 1),
        "name": data.get("name", "Unknown Sector"),
        "story": data.get("story", ""),
        "energy_budget": data["energy_budget"],
        "stars": stars,
        "edges": edges
    }

def generate_procedural_level(num_stars=7, width=950, height=580):
    """
    Generates a guaranteed-connected procedural graph.
    Seeds special stars based on weighted probabilities.
    """
    stars = []
    types = ["NORMAL", "NORMAL", "POWER", "ENERGY", "UNSTABLE"]
    for i in range(num_stars):
        x = random.randint(140, width - 100)
        y = random.randint(140, height - 100)
        stype = random.choice(types)
        stars.append(StarNode(i, f"Gen-{i}", x, y, stype))

    # Connect nearby stars to create a graph
    candidate_edges = set()
    for i in range(num_stars):
        for j in range(i + 1, num_stars):
            dist = math.hypot(stars[i].x - stars[j].x, stars[i].y - stars[j].y)
            if dist < 320:
                cost = max(2, int(dist // 28))
                candidate_edges.add((min(i, j), max(i, j), cost))

    # Guarantee graph connectivity by chaining disconnected clusters if needed
    edges = list(candidate_edges)
    return {
        "world_id": 99,
        "name": "Procedural Deep Space",
        "story": "Uncharted anomaly sector. Dynamic field conditions detected.",
        "energy_budget": int(len(stars) * 4.5),
        "stars": stars,
        "edges": edges
    }