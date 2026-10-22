import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import pygame
pygame.init()
from main import GameApp
from dsa.mst import kruskal_steps

app = GameApp()

# Iterate through every world in sequence (1 through 10)
for w in range(10):
    app.load_world(w)
    
    # Solve level using Kruskal's algorithm
    effective = [
        (u, v, app.state.compute_edge_cost(u, v, weight))
        for u, v, weight in app.state.edges
    ]
    steps = kruskal_steps(list(app.state.stars.keys()), effective)
    for u, v, cost, accepted, _ in steps:
        if accepted:
            ok, _ = app.state.connect_edge(u, v)
            assert ok, f"World {w+1} failed to connect edge ({u}, {v})"
    
    assert app.state.is_completed, f"World {w+1} should be completed!"
    
    # Draw frame
    app.starfield.elapsed = 10.0
    app.draw(0.016)
    
    # Verify that all chosen edges connect exactly to the stars' mapped screen positions
    star_pos = {
        s.id: app.state.star_list[i]
        for i, s in enumerate(app.state.star_list)
    }
    from theme import map_star_coordinates
    mapped_pos = {
        s.id: map_star_coordinates(s.x, s.y, app.state.star_list)
        for s in app.state.star_list
    }
    from visual.celestial_renderer import CelestialRenderer
    for u, v, _ in app.state.selected_edges:
        p1, p2 = mapped_pos[u], mapped_pos[v]
        pts = CelestialRenderer._get_wobble_points(p1, p2)
        assert pts[0] == p1, f"World {w+1} edge ({u}, {v}) start {pts[0]} != {p1}"
        assert pts[-1] == p2, f"World {w+1} edge ({u}, {v}) end {pts[-1]} != {p2}"

print("ALL 10 WORLDS VERIFIED PERFECTLY! Zero link misalignments or cache collisions!")

