import pygame
import random
import math

class ParallaxStarfield:
    def __init__(self, width=1100, height=720):
        self.width = width
        self.height = height
        # Layer speeds in pixels per second:
        # Layer 0 (distant): 12 px/sec (~0.2 px/frame at 60 FPS)
        # Layer 1 (mid):     30 px/sec (~0.5 px/frame at 60 FPS)
        # Layer 2 (near):    54 px/sec (~0.9 px/frame at 60 FPS)
        self.speeds = [12.0, 30.0, 54.0]
        
        # Each star: [x, y, radius, base_brightness, phase]
        self.layers = [
            [[random.uniform(0, width), random.uniform(0, height), 1, random.randint(80, 140), random.uniform(0, 6.28)] for _ in range(90)],
            [[random.uniform(0, width), random.uniform(0, height), 2, random.randint(140, 200), random.uniform(0, 6.28)] for _ in range(45)],
            [[random.uniform(0, width), random.uniform(0, height), 3, random.randint(210, 255), random.uniform(0, 6.28)] for _ in range(16)]
        ]

    def update_and_draw(self, surface, dt):
        surface.fill((8, 11, 24))  # Dark cosmic blue
        time_sec = pygame.time.get_ticks() / 1000.0

        for layer_idx, stars in enumerate(self.layers):
            speed = self.speeds[layer_idx]
            for star in stars:
                star[1] = (star[1] + speed * dt) % self.height
                # Twinkle calculation
                twinkle = (math.sin(time_sec * 3.0 + star[4]) + 1.0) * 0.5
                brightness = max(40, min(255, int(star[3] * (0.6 + 0.4 * twinkle))))
                color = (brightness, brightness, min(255, brightness + 20))
                pygame.draw.circle(surface, color, (int(star[0]), int(star[1])), star[2])