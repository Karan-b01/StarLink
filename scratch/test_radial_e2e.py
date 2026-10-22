import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import pygame
pygame.init()
from main import GameApp

app = GameApp()
app.show_intro = False
app.starfield.elapsed = 10.0

# 1. Closed state with the single trigger button on bottom dock
app.draw(0.016)
pygame.image.save(pygame.display.get_surface(), "assets/images/radial_test_closed_hud.png")
print("Saved radial_test_closed_hud.png")

# 2. Trigger the 1 button: radial menu opens
app.activate_button("radial")
assert app.radial_menu.is_open

# Animate to t = 0.3 (early expansion)
app.radial_menu.transition_t = 0.3
app.draw(0.016)
pygame.image.save(pygame.display.get_surface(), "assets/images/radial_test_expanding.png")
print("Saved radial_test_expanding.png")

# Animate to t = 1.0 with mouse hovering over 'solver' button (North-East, idx 1)
app.radial_menu.transition_t = 1.0
solver_x = app.radial_menu.cx + int(app.radial_menu.radius * 0.707)
solver_y = app.radial_menu.cy - int(app.radial_menu.radius * 0.707)

surf = pygame.display.get_surface()
app.draw(0.016)
app.radial_menu.draw(surf, (solver_x, solver_y))
pygame.image.save(surf, "assets/images/radial_test_open_hover.png")
print("Saved radial_test_open_hover.png")

# 3. Simulate clicking the hovered 'hint' option
click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (app.radial_menu.cx, app.radial_menu.cy - app.radial_menu.radius)})
app.radial_menu.hovered_index = 0 # Hint
action = app.radial_menu.handle_event(click_event)
print("Radial menu clicked action returned:", action)
assert action == "hint"
app.activate_button(action)
assert app.active_hint_edge is not None
print("Hint triggered successfully! Active hint edge:", app.active_hint_edge)
