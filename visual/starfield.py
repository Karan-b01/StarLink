import pygame
import random
import math

class ParallaxStarfield:
    def __init__(self, width=1100, height=720):
        self.width = width
        self.height = height
        self.elapsed = 0.0
        self.backdrop = self._build_galaxy_backdrop(width, height)
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

    @staticmethod
    def _build_galaxy_backdrop(width, height):
        """Build a one-time, high-resolution painterly galaxy with spiral dust."""
        rng = random.Random(142)
        sky = pygame.Surface((width, height)).convert()
        for y in range(height):
            t = y / max(1, height - 1)
            pygame.draw.line(sky, (int(3 + 2*t), int(6 + 3*t), int(17 + 7*t)), (0, y), (width, y))

        # The galactic plane is drawn at half resolution, then softened at full size.
        sw, sh = max(1, width // 2), max(1, height // 2)
        clouds = pygame.Surface((sw, sh), pygame.SRCALPHA)
        cloud_specs = [
            (0.12, .72, (34, 105, 180), 1.00),
            (.32, .52, (78, 72, 196), .88),
            (.50, .39, (36, 128, 190), .88),
            (.69, .31, (123, 57, 166), .82),
            (.88, .19, (47, 95, 177), .72),
            (.76, .77, (155, 66, 92), .48),
        ]
        for px, py, color, strength in cloud_specs:
            patch = pygame.Surface((220, 104), pygame.SRCALPHA)
            for ring in range(30, 0, -1):
                rx = max(2, int(108 * ring / 30))
                ry = max(2, int(49 * ring / 30))
                alpha = max(1, int((31 - ring) * .27 * strength))
                pygame.draw.ellipse(patch, (*color, alpha), (110-rx, 52-ry, rx*2, ry*2))
            patch = pygame.transform.smoothscale(patch, (150, 68))
            patch = pygame.transform.rotate(patch, -27 + rng.uniform(-12, 12))
            clouds.blit(patch, (int(px * sw - patch.get_width()/2), int(py * sh - patch.get_height()/2)))

        # Spiral arms are tiny scattered dust and gas points, not hard-edged blobs.
        cx, cy = sw * .51, sh * .47
        for arm in range(3):
            for i in range(680):
                t = rng.random()
                angle = t * 4.4 + arm * (math.tau / 3)
                radius = 7 + t * min(sw, sh) * .53
                jitter = rng.gauss(0, 4 + t * 5)
                px = cx + math.cos(angle) * (radius + jitter)
                py = cy + math.sin(angle) * (radius * .48 + jitter)
                if not (0 <= px < sw and 0 <= py < sh):
                    continue
                color = rng.choice(((100, 166, 255), (111, 117, 255), (211, 125, 218), (62, 190, 221)))
                alpha = rng.randint(14, 72)
                pygame.draw.circle(clouds, (*color, alpha), (int(px), int(py)), rng.choice((1, 1, 1, 2)))

        sky.blit(pygame.transform.smoothscale(clouds, (width, height)), (0, 0))

        # A distant planetary limb gives the playfield scale and a warm horizon.
        planet = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.circle(planet, (4, 12, 29, 235), (-24, height + 110), 275)
        pygame.draw.circle(planet, (32, 117, 184, 115), (-24, height + 110), 277, 2)
        pygame.draw.arc(planet, (94, 188, 235, 135), (-300, height-170, 560, 560), .15, 2.35, 2)
        sky.blit(planet, (0, 0))
        return sky.convert()

    def update_and_draw(self, surface, dt, clear=True):
        self.elapsed += dt
        if clear:
            surface.blit(self.backdrop, (0, 0))
        time_sec = self.elapsed

        for layer_idx, stars in enumerate(self.layers):
            speed = self.speeds[layer_idx]
            for star in stars:
                star[1] = (star[1] + speed * dt) % self.height
                # Twinkle calculation
                twinkle = (math.sin(time_sec * 3.0 + star[4]) + 1.0) * 0.5
                brightness = max(40, min(255, int(star[3] * (0.6 + 0.4 * twinkle))))
                color = (brightness, brightness, min(255, brightness + 30))
                pos = (int(star[0]), int(star[1]))
                if layer_idx == 2 and brightness > 180:
                    pygame.draw.circle(surface, (color[0] // 3, color[1] // 3, color[2] // 3), pos, star[2] + 4)
                    pygame.draw.line(surface, (*color,), (pos[0] - 5, pos[1]), (pos[0] + 5, pos[1]), 1)
                    pygame.draw.line(surface, (*color,), (pos[0], pos[1] - 5), (pos[0], pos[1] + 5), 1)
                pygame.draw.circle(surface, color, pos, star[2])
