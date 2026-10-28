import heapq
import itertools

from dsa.graph import is_fully_connected
from dsa.history_stack import ActionHistory
from dsa.mst import kruskal_mst
from dsa.union_find import UnionFind


class GameState:
    """Game rules for connecting stars with low-cost, cycle-free links."""

    def __init__(self, level_data):
        self.load_level(level_data)

    def load_level(self, level_data):
        self.world_id = level_data["world_id"]
        self.name = level_data["name"]
        self.story = level_data["story"]
        self.difficulty = level_data.get("difficulty", "MEDIUM")
        self.stars = {star.id: star for star in level_data["stars"]}
        self.star_list = level_data["stars"]
        self.edges = level_data["edges"]
        self.edge_index = {
            (min(u, v), max(u, v)): index
            for index, (u, v, _cost) in enumerate(self.edges)
        }
        self.edge_rules = {}
        for rule in level_data.get("edge_rules", []):
            u, v = rule["edge"]
            pair = (min(u, v), max(u, v))
            if pair not in self.edge_index:
                raise ValueError(f"Unstable link {pair} is not in {self.name}.")
            deadline = int(rule["collapse_after"])
            if deadline < 1:
                raise ValueError("A collapse timer must allow at least one move.")
            self.edge_rules[self.edge_index[pair]] = deadline

        self.turns_elapsed = 0  # Counts successful link actions, including redos.
        self.expired_edges = set()
        self._plan_cache = {}
        self.moves_made = 0
        self.max_energy = level_data["energy_budget"]
        self.energy = self.max_energy
        self.selected_edges = []
        self.history = ActionHistory()
        self.resonance_streak = 0

        # DSA: ordinary levels use Kruskal; timed levels need a shortest legal plan.
        _kruskal_edges, _kruskal_cost, self.solver_history = kruskal_mst(
            list(self.stars), self.edges
        )
        self.optimal_cost, self.optimal_plan = self._find_best_completion(0, 0)
        if self.optimal_cost == float("inf"):
            raise ValueError(f"No legal completion exists for {self.name}.")
        self.mst_edges = [self.edges[index] for index in self.optimal_plan]
        if len(self.mst_edges) != len(self.stars) - 1:
            raise ValueError(f"Level graph is disconnected: {self.name}.")
        self.mst_pairs = {(min(u, v), max(u, v)) for u, v, _ in self.mst_edges}

        self.status_message = "Select stars or edges to restore the constellation."
        self.notification_message = None
        self.cycle_edge_flash = None
        self.is_completed = False
        self.is_failed = False
        self.earned_stars = 0

    @property
    def has_timed_edges(self):
        return bool(self.edge_rules)

    def _find_best_completion(self, start_mask, start_turn):
        """Dijkstra search over selected-link sets and elapsed move counts."""
        cache_key = (start_mask, start_turn)
        if cache_key in self._plan_cache:
            return self._plan_cache[cache_key]

        # DSA: without deadlines, ordinary Kruskal is enough to finish the tree.
        if not self.edge_rules:
            components = UnionFind(list(self.stars))
            for index, (u, v, _cost) in enumerate(self.edges):
                if start_mask & (1 << index):
                    components.union(u, v)
            total = 0
            plan = []
            for index in sorted(range(len(self.edges)), key=lambda i: self.edges[i][2]):
                if start_mask & (1 << index):
                    continue
                u, v, cost = self.edges[index]
                if components.union(u, v):
                    total += cost
                    plan.append(index)
            answer = (total, tuple(plan))
            if components.num_components > 1:
                answer = (float("inf"), ())
            self._plan_cache[cache_key] = answer
            return answer

        start = (start_mask, start_turn)
        queue = [(0, 0, start)]
        sequence = itertools.count(1)
        best_cost = {start: 0}
        previous = {}
        answer = (float("inf"), ())

        while queue:
            cost_so_far, _order, state = heapq.heappop(queue)
            if cost_so_far != best_cost.get(state):
                continue
            mask, turns = state
            components = UnionFind(list(self.stars))
            for index, (u, v, _cost) in enumerate(self.edges):
                if mask & (1 << index):
                    components.union(u, v)

            if components.num_components == 1:
                plan = []
                cursor = state
                while cursor != start:
                    cursor, edge_index = previous[cursor]
                    plan.append(edge_index)
                answer = (cost_so_far, tuple(reversed(plan)))
                break

            for index, (u, v, weight) in enumerate(self.edges):
                edge_bit = 1 << index
                if mask & edge_bit:
                    continue
                deadline = self.edge_rules.get(index)
                if deadline is not None and turns >= deadline:
                    continue
                if components.find(u) == components.find(v):
                    continue

                next_state = (mask | edge_bit, turns + 1)
                next_cost = cost_so_far + weight
                if next_cost < best_cost.get(next_state, float("inf")):
                    best_cost[next_state] = next_cost
                    previous[next_state] = (state, index)
                    heapq.heappush(queue, (next_cost, next(sequence), next_state))

        self._plan_cache[cache_key] = answer
        return answer

    def _current_mask(self):
        mask = 0
        for u, v, _ in self.selected_edges:
            mask |= 1 << self.edge_index[(min(u, v), max(u, v))]
        return mask

    def _expire_due_edges(self):
        selected = {self.edge_index[(min(u, v), max(u, v))] for u, v, _ in self.selected_edges}
        newly_expired = []
        for index, deadline in self.edge_rules.items():
            if deadline <= self.turns_elapsed and index not in selected and index not in self.expired_edges:
                self.expired_edges.add(index)
                newly_expired.append(index)
        if newly_expired:
            names = [f"{self.stars[self.edges[i][0]].name}–{self.stars[self.edges[i][1]].name}" for i in newly_expired]
            self.notification_message = "Unstable link expired: " + ", ".join(names)
        return newly_expired

    def _completion_plan(self):
        return self._find_best_completion(self._current_mask(), self.turns_elapsed)

    def get_current_plan(self):
        """Return the best legal remaining link order for the current timers."""
        return self._completion_plan()[1]

    def get_post_level_analysis(self):
        """Compare the completed network with the best legal move sequence."""
        player_cost = sum(cost for _, _, cost in self.selected_edges)
        divergence = None
        moves = [action["edge"] for action in self.history.undo_stack]
        for index, edge in enumerate(moves):
            if index >= len(self.optimal_plan):
                break
            planned = self.edges[self.optimal_plan[index]]
            pair = (min(edge[0], edge[1]), max(edge[0], edge[1]))
            if pair != (min(planned[0], planned[1]), max(planned[0], planned[1])):
                divergence = {
                    "move": index + 1,
                    "edge": edge,
                    "alternative": planned,
                }
                break
        return {
            "player_cost": player_cost,
            "optimal_cost": self.optimal_cost,
            "wasted_energy": player_cost - self.optimal_cost if self.is_completed else None,
            "divergence": divergence,
        }

    def connect_edge(self, u, v):
        """Connect an active corridor and advance every unstable link's timer."""
        u, v = min(u, v), max(u, v)
        pair = (u, v)
        if any((min(a, b), max(a, b)) == pair for a, b, _ in self.selected_edges):
            return False, "Edge already linked."
        edge_index = self.edge_index.get(pair)
        if edge_index is None:
            self.resonance_streak = 0
            return False, "No valid corridor between these stars."
        if edge_index in self.expired_edges:
            self.status_message = "This unstable link has expired."
            self.notification_message = self.status_message
            return False, self.status_message

        # DSA: Union-Find prevents cycles by checking the endpoints' components.
        components = UnionFind(list(self.stars))
        for a, b, _ in self.selected_edges:
            components.union(a, b)
        if not components.union(u, v):
            self.resonance_streak = 0
            self.cycle_edge_flash = pair
            self.status_message = f"Cycle detected. Union-Find rejected link {pair}."
            return False, "Cycle detected."

        cost = self.edges[edge_index][2]
        if self.energy < cost:
            self.status_message = f"Insufficient energy. This link costs {cost}."
            self.notification_message = self.status_message
            return False, "Out of energy."

        previous_streak = self.resonance_streak
        optimal_pick = pair in self.mst_pairs
        self.energy -= cost
        action_edge = (u, v, cost)
        self.selected_edges.append(action_edge)
        self.turns_elapsed += 1
        self.moves_made = self.turns_elapsed
        self.history.record_action(action_edge, cost, {
            "previous_streak": previous_streak,
            "is_optimal_pick": optimal_pick,
        })
        self.resonance_streak = previous_streak + 1 if optimal_pick else 0
        self.status_message = f"Linked {self.stars[u].name} to {self.stars[v].name}; spent {cost} energy."

        self._expire_due_edges()
        self._check_victory()
        if not self.is_completed:
            self.check_failure()
        return True, "Success."

    def can_still_complete(self):
        if self.is_completed or self.is_failed:
            return False
        minimum_cost, _plan = self._completion_plan()
        return minimum_cost <= self.energy

    def check_failure(self):
        if self.is_completed or self.is_failed or self.can_still_complete():
            return False
        minimum_cost, _plan = self._completion_plan()
        self.is_failed = True
        if minimum_cost == float("inf"):
            self.status_message = "No route remains. An unstable link expired; reset the sector to retry."
        else:
            self.status_message = f"Not enough energy to finish. At least {minimum_cost} more energy is needed; reset to retry."
        self.notification_message = self.status_message
        return True

    def _check_victory(self):
        # DSA: BFS verifies that the selected links connect every star.
        if is_fully_connected(list(self.stars), self.selected_edges):
            self.is_completed = True
            player_cost = sum(cost for _, _, cost in self.selected_edges)
            difference = player_cost - self.optimal_cost
            self.earned_stars = 5 if difference <= 0 else max(1, 5 - (difference + 1) // 2)
            self.status_message = (
                f"Constellation Restored! Rating: {'★' * self.earned_stars} "
                f"(Your Cost: {player_cost} | Optimal: {self.optimal_cost})"
            )

    def undo(self):
        action = self.history.undo()
        if not action:
            return
        u, v, _ = action["edge"]
        pair = (min(u, v), max(u, v))
        self.selected_edges = [edge for edge in self.selected_edges if (edge[0], edge[1]) != pair]
        self.energy = min(self.max_energy, self.energy + action["cost"])
        # Undo removes the link, but never rewinds timers already advanced.
        self._expire_due_edges()
        self.resonance_streak = action["meta"].get("previous_streak", 0)
        self.is_completed = self.is_failed = False
        self.status_message = "Last move undone. Energy restored; link timers keep moving."
        self.check_failure()

    def redo(self):
        if not self.history.redo_stack:
            return
        action = self.history.redo_stack[-1]
        u, v, cost = action["edge"]
        pair = (min(u, v), max(u, v))
        edge_index = self.edge_index[pair]
        if edge_index in self.expired_edges:
            self.status_message = "This unstable link expired, so it cannot be redone."
            self.notification_message = self.status_message
            return
        if self.energy < cost:
            self.status_message = f"Insufficient energy. This link costs {cost}."
            return
        action = self.history.redo()
        self.selected_edges.append(action["edge"])
        self.energy -= action["cost"]
        self.turns_elapsed += 1
        self.moves_made = self.turns_elapsed
        self.resonance_streak = action["meta"].get("previous_streak", 0) + int(action["meta"].get("is_optimal_pick", False))
        self.is_completed = self.is_failed = False
        self.status_message = f"Redid link ({u}, {v}); timers advanced."
        self._expire_due_edges()
        self._check_victory()
        if not self.is_completed:
            self.check_failure()

    def get_algorithm_hint(self):
        if self.is_completed:
            return None, "Constellation already fully restored!"
        remaining_cost, plan = self._completion_plan()
        if not plan:
            return None, "No legal route remains. Reset the sector to retry."
        edge_index = plan[0]
        u, v, cost = self.edges[edge_index]
        deadline = self.edge_rules.get(edge_index)
        if deadline is not None:
            message = f"Connect {self.stars[u].name}–{self.stars[v].name} now; it expires after move {deadline}."
        else:
            message = f"Kruskal's next link: {self.stars[u].name}–{self.stars[v].name}, cost {cost}."
        message += f" Best completion costs {remaining_cost} more energy."
        return (u, v, cost), message
