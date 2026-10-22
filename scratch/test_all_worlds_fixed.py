import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import pygame
pygame.init()
from main import GameApp
from visual.celestial_renderer import CelestialRenderer

for world_idx in range(10):
    CelestialRenderer._EDGE_WOBBLE_CACHE.clear()
    app = GameApp()
    app.load_world(world_idx)
    
    from dsa.mst import kruskal_steps
    edges_with_cost = [
        (u, v, app.state.compute_edge_cost(u, v, w))
        for u, v, w in app.state.edges
    ]
    gen = kruskal_steps(list(app.state.stars.keys()), edges_with_cost)
    for u, v, cost, accepted, _ in gen:
        if accepted:
            app.state.selected_edges.append((u, v, cost))
    
    app.starfield.elapsed = 10.0
    app.draw(0.016)
    out_path = f"assets/images/test_fixed_world_{world_idx+1}.png"
    pygame.image.save(pygame.display.get_surface(), out_path)
    print(f"Saved {out_path} for Sector {world_idx+1}")

