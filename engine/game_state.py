from dsa.union_find import UnionFind
from dsa.mst import kruskal_mst, prims_mst
from dsa.graph import is_fully_connected
from dsa.history_stack import ActionHistory

class GameState:
    def __init__(self, level_data):
        self.load_level(level_data)

    def load_level(self, level_data):
        self.world_id = level_data["world_id"]
        self.name = level_data["name"]
        self.story = level_data["story"]
        self.difficulty = level_data.get("difficulty", "MEDIUM")
        self.stars = {s.id: s for s in level_data["stars"]}
        self.star_list = level_data["stars"]
        self.edges = level_data["edges"]
        self.wormhole_pairs = [tuple(sorted(pair)) for pair in level_data.get("wormhole_pairs", [])]
        
        self.max_energy = level_data["energy_budget"]
        self.energy = self.max_energy
        self.selected_edges = [(u, v, 0) for u, v in self.wormhole_pairs]
        self.history = ActionHistory()
        self.resonance_streak = 0
        
        # Precompute Kruskal's MST baseline
        vertex_ids = list(self.stars.keys())
        effective_edges = [(u, v, 0) for u, v in self.wormhole_pairs] + [
            (u, v, self.compute_edge_cost(u, v, weight))
            for u, v, weight in self.edges
        ]
        self.mst_edges, self.optimal_cost, self.solver_history = kruskal_mst(vertex_ids, effective_edges)
        self.mst_pairs = {(min(u, v), max(u, v)) for u, v, _ in self.mst_edges}
        
        # Status / Feedback
        self.status_message = "Select stars or edges to restore the constellation."
        self.notification_message = None
        self.cycle_edge_flash = None  # Holds edge to flash red on cycle rejection
        self.is_completed = False
        self.is_failed = False
        self.earned_stars = 0

    def compute_edge_cost(self, u, v, base_cost):
        """Power Star halves cost: floor(cost / 2)."""
        if self.stars[u].type == "POWER" or self.stars[v].type == "POWER":
            return max(1, base_cost // 2)
        return base_cost

    def connect_edge(self, u, v):
        """
        Attempts to add an edge between star u and v.
        Runs Union-Find cycle rejection.
        """
        # 1. Normalize orientation
        u, v = min(u, v), max(u, v)

        # 2. Check if already connected
        if any(e[0] == u and e[1] == v for e in self.selected_edges):
            return False, "Edge already linked."

        # 3. Find edge base cost
        edge_entry = next((e for e in self.edges if (e[0] == u and e[1] == v) or (e[0] == v and e[1] == u)), None)
        if not edge_entry:
            self.resonance_streak = 0
            return False, "No valid corridor between these stars."

        base_cost = edge_entry[2]
        effective_cost = self.compute_edge_cost(u, v, base_cost)

        # 4. Check Union-Find for cycles
        uf = UnionFind(list(self.stars.keys()))
        for su, sv, _ in self.selected_edges:
            uf.union(su, sv)

        if not uf.union(u, v):
            self.resonance_streak = 0
            self.cycle_edge_flash = (u, v)
            self.status_message = f"Cycle Detected! Union-Find rejected link ({u}-{v})."
            return False, "Cycle Detected"

        # 5. Energy Budget Check
        if self.energy < effective_cost:
            self.status_message = f"Insufficient Energy! Requires {effective_cost}."
            return False, "Out of Energy"

        previous_streak = self.resonance_streak
        previous_energy = self.energy
        self.energy -= effective_cost
        actual_deduction = previous_energy - self.energy

        added_edge = (u, v, effective_cost)
        self.selected_edges.append(added_edge)
        self.history.record_action(added_edge, actual_deduction, {"previous_streak": previous_streak})
        self.status_message = f"Linked Star {u} to Star {v} (Cost: {effective_cost})."

        if (u, v) in self.mst_pairs:
            self.resonance_streak += 1
        else:
            self.resonance_streak = 0

        self._check_victory()
        return True, "Success"

    def can_still_complete(self):
        """Return whether an affordable edge can still join two components."""
        if self.is_completed or self.is_failed:
            return False
        uf = UnionFind(list(self.stars.keys()))
        for u, v, _ in self.selected_edges:
            uf.union(u, v)
        for u, v, base_cost in self.edges:
            a, b = min(u, v), max(u, v)
            if any(e[0] == a and e[1] == b for e in self.selected_edges):
                continue
            if uf.find(u) != uf.find(v) and self.compute_edge_cost(u, v, base_cost) <= self.energy:
                return True
        return False

    def check_failure(self):
        """Lock the level once no remaining affordable link can join components."""
        if not self.is_completed and not self.is_failed and not self.can_still_complete():
            self.is_failed = True
            self.status_message = "Signal lost. Not enough energy to restore the constellation."
            return True
        return False

    def _check_victory(self):
        """Uses BFS to check if the full graph is spanning and connected."""
        vertex_ids = list(self.stars.keys())
        if is_fully_connected(vertex_ids, self.selected_edges):
            self.is_completed = True
            player_cost = sum(c for _, _, c in self.selected_edges)
            diff = player_cost - self.optimal_cost

            # Five-star rating based on added cost over the effective-cost MST.
            if diff <= 0:
                self.earned_stars = 5
            elif diff <= 2:
                self.earned_stars = 4
            elif diff <= 4:
                self.earned_stars = 3
            elif diff <= 6:
                self.earned_stars = 2
            else:
                self.earned_stars = 1

            self.status_message = (
                f"Constellation Restored! Rating: {'★' * self.earned_stars} "
                f"(Your Cost: {player_cost} | Optimal MST: {self.optimal_cost})"
            )

    def undo(self):
        action = self.history.undo()
        if action:
            edge = action["edge"]
            self.selected_edges = [e for e in self.selected_edges if not (e[0] == edge[0] and e[1] == edge[1])]
            self.energy = min(self.max_energy, self.energy + action["cost"])
            self.resonance_streak = action.get("meta", {}).get("previous_streak", 0)
            self.status_message = f"Undid link ({edge[0]}, {edge[1]}). Energy restored."
            self.is_completed = False

    def redo(self):
        action = self.history.redo()
        if action:
            edge = action["edge"]
            self.selected_edges.append(edge)
            self.energy -= action["cost"]
            u, v, _ = edge
            previous_streak = action.get("meta", {}).get("previous_streak", 0)
            self.resonance_streak = previous_streak + 1 if (min(u, v), max(u, v)) in self.mst_pairs else 0
            self.status_message = f"Redid link ({edge[0]}, {edge[1]})."
            self._check_victory()

    def get_algorithm_hint(self):
        """
        Computes the next optimal algorithmic corridor using the MST Cut Property.
        Returns: ((u, v, cost), explanation_str) or (None, reason_str)
        """
        if self.is_completed:
            return None, "Constellation already fully restored!"

        uf = UnionFind(list(self.stars.keys()))
        for u, v, _ in self.selected_edges:
            uf.union(u, v)

        sorted_candidates = sorted(
            self.edges,
            key=lambda e: self.compute_edge_cost(e[0], e[1], e[2])
        )

        mst_pairs = self.mst_pairs
        for u, v, base_cost in sorted_candidates:
            a, b = min(u, v), max(u, v)
            if any(e[0] == a and e[1] == b for e in self.selected_edges):
                continue
            if uf.find(a) != uf.find(b) and (a, b) in mst_pairs:
                eff_cost = self.compute_edge_cost(a, b, base_cost)
                return (a, b, eff_cost), f"MST Cut Hint: Corridor ({self.stars[a].name} - {self.stars[b].name}, cost {eff_cost}) is an optimal greedy choice."

        for u, v, base_cost in sorted_candidates:
            a, b = min(u, v), max(u, v)
            if any(e[0] == a and e[1] == b for e in self.selected_edges):
                continue
            if uf.find(a) != uf.find(b):
                eff_cost = self.compute_edge_cost(a, b, base_cost)
                return (a, b, eff_cost), f"Greedy Bridge: Corridor ({self.stars[a].name} - {self.stars[b].name}, cost {eff_cost}) safely joins star groups."

        return None, "No remaining valid corridors found."
