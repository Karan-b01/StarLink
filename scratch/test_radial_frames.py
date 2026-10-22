import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import pygame
pygame.init()
from main import GameApp
from scratch.test_radial_render import AstrolabeRadialMenu

app = GameApp()
# Draw base game screen on Sector 5
app.starfield.elapsed = 10.0
app.draw(0.016)
base_screen = pygame.display.get_surface().copy()

menu = AstrolabeRadialMenu(cx=512, cy=355)
menu.is_open = True

# Frame 1: t = 0.35 (expanding outward)
menu.transition_t = 0.35
surf1 = base_screen.copy()
menu.draw(surf1, (0, 0))
pygame.image.save(surf1, "assets/images/radial_anim_frame1.png")
print("Saved radial_anim_frame1.png")

# Frame 2: t = 0.75 (almost fully open)
menu.transition_t = 0.75
surf2 = base_screen.copy()
menu.draw(surf2, (0, 0))
pygame.image.save(surf2, "assets/images/radial_anim_frame2.png")
print("Saved radial_anim_frame2.png")

# Frame 3: t = 1.0 (fully open, hovering 'solver')
menu.transition_t = 1.0
surf3 = base_screen.copy()
# Hover on solver (NE button)
bx = menu.cx + int(menu.radius * 0.707)
by = menu.cy - int(menu.radius * 0.707)
menu.draw(surf3, (bx, by))
pygame.image.save(surf3, "assets/images/radial_anim_frame3.png")
print("Saved radial_anim_frame3.png")

