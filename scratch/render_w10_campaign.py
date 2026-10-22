import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import pygame
pygame.init()
from main import GameApp
from dsa.mst import kruskal_steps

app = GameApp()
# Play world 1 through 9
for w in range(9):
    app.load_world(w)
    effective = [(u, v, app.state.compute_edge_cost(u, v, weight)) for u, v, weight in app.state.edges]
    steps = kruskal_steps(list(app.state.stars.keys()), effective)
    for u, v, cost, accepted, _ in steps:
        if accepted:
            app.state.connect_edge(u, v)

# Now load world 10 (idx=9)
app.load_world(9)
# Connect the exact edges that the user connected in the uploaded screenshot:
# (3, 4), (4, 5), (4, 8), (5, 6), (2, 3)
app.state.connect_edge(3, 4)
app.state.connect_edge(4, 5)
app.state.connect_edge(4, 8)
app.state.connect_edge(5, 6)
app.state.connect_edge(2, 3)

app.starfield.elapsed = 10.0
app.draw(0.016)
pygame.image.save(pygame.display.get_surface(), "assets/images/world_10_after_campaign_test.png")
print("Saved assets/images/world_10_after_campaign_test.png")

