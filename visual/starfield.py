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
        """Build a one-time, high-resolution painterly galaxy with spiral dust and brilliant core."""
        rng = random.Random(142)
        sky = pygame.Surface((width, height)).convert()
        for y in range(height):
            t = y / max(1, height - 1)
            pygame.draw.line(sky, (int(2 + 2*t), int(5 + 3*t), int(15 + 8*t)), (0, y), (width, y))

        sw, sh = max(1, width // 2), max(1, height // 2)
        clouds = pygame.Surface((sw, sh), pygame.SRCALPHA)
        cx, cy = sw * 0.50, sh * 0.48

        # Rich multi-color interstellar nebula clouds
        cloud_specs = [
            (0.15, 0.68, (28, 90, 175), 0.95),
            (0.35, 0.50, (65, 55, 180), 0.90),
            (0.50, 0.46, (40, 130, 200), 1.05),
            (0.65, 0.35, (120, 50, 170), 0.85),
            (0.82, 0.22, (45, 100, 180), 0.80),
            (0.72, 0.72, (150, 60, 95), 0.55),
        ]
        for px, py, color, strength in cloud_specs:
            patch = pygame.Surface((240, 120), pygame.SRCALPHA)
            for ring in range(32, 0, -1):
                rx = max(2, int(115 * ring / 32))
                ry = max(2, int(54 * ring / 32))
                alpha = max(1, int((33 - ring) * 0.32 * strength))
                pygame.draw.ellipse(patch, (*color, alpha), (120 - rx, 60 - ry, rx * 2, ry * 2))
            patch = pygame.transform.smoothscale(patch, (160, 75))
            patch = pygame.transform.rotate(patch, -25 + rng.uniform(-10, 10))
            clouds.blit(patch, (int(px * sw - patch.get_width() / 2), int(py * sh - patch.get_height() / 2)))

        # Dense 4-arm logarithmic spiral galaxy with star clusters
        arm_colors = [
            (170, 225, 255), (125, 160, 255), (225, 150, 235),
            (100, 215, 240), (255, 235, 200), (240, 248, 255)
        ]
        for arm in range(4):
            for _ in range(950):
                t = rng.random()
                angle = t * 4.6 + arm * (math.tau / 4)
                radius = 5 + t * min(sw, sh) * 0.58
                jitter = rng.gauss(0, 3 + t * 6)
                px = cx + math.cos(angle) * (radius + jitter)
                py = cy + math.sin(angle) * (radius * 0.50 + jitter)
                if not (0 <= px < sw and 0 <= py < sh):
                    continue
                color = rng.choice(arm_colors)
                alpha = rng.randint(20, 95)
                rad = 1 if rng.random() > 0.12 else 2
                pygame.draw.circle(clouds, (*color, alpha), (int(px), int(py)), rad)

        # Brilliant radiant golden-white galactic core (matching reference image)
        core_surf = pygame.Surface((180, 100), pygame.SRCALPHA)
        for ring in range(40, 0, -1):
            rx = int(85 * (ring / 40) ** 1.3)
            ry = int(42 * (ring / 40) ** 1.3)
            if rx < 1 or ry < 1:
                continue
            alpha = max(1, int((41 - ring) * 4.2))
            # Golden amber to brilliant white core
            t_col = (41 - ring) / 40.0
            r = int(240 + t_col * 15)
            g = int(190 + t_col * 60)
            b = int(120 + t_col * 135)
            pygame.draw.ellipse(core_surf, (r, g, b, min(220, alpha)), (90 - rx, 50 - ry, rx * 2, ry * 2))
        core_surf = pygame.transform.rotate(core_surf, -22)
        clouds.blit(core_surf, (int(cx - core_surf.get_width() / 2), int(cy - core_surf.get_height() / 2)))

        sky.blit(pygame.transform.smoothscale(clouds, (width, height)), (0, 0))

        # Distant planetary limb with atmospheric glow
        planet = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.circle(planet, (3, 10, 26, 240), (-24, height + 110), 280)
        pygame.draw.circle(planet, (32, 117, 184, 120), (-24, height + 110), 282, 2)
        pygame.draw.arc(planet, (94, 195, 245, 145), (-300, height - 175, 570, 570), 0.15, 2.35, 2)
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
