import pygame
import random
import math

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'radius', 'life', 'max_life', 'decay')

    def __init__(self, x, y, vx, vy, color, radius, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.life = life
        self.max_life = life
        self.decay = 1.0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.94
        self.vy *= 0.94
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        if self.life <= 0:
            return
        pct = max(0.0, self.life / self.max_life)
        alpha = int(255 * pct)
        cur_radius = max(1, int(self.radius * pct))
        
        # Draw soft glow particle
        s = pygame.Surface((cur_radius * 4 + 2, cur_radius * 4 + 2), pygame.SRCALPHA)
        center = cur_radius * 2 + 1
        pygame.draw.circle(s, (*self.color, alpha), (center, center), cur_radius)
        if cur_radius > 1:
            pygame.draw.circle(s, (255, 255, 255, int(alpha * 0.8)), (center, center), max(1, cur_radius // 2))
        surface.blit(s, (int(self.x - center), int(self.y - center)), special_flags=pygame.BLEND_ADD)


class ParticleSystem:
    """High-performance procedural stardust and energy corridor particle manager."""
    def __init__(self):
        self.particles = []

    def emit_star_burst(self, x, y, color=(80, 210, 255), count=16):
        """Emits radial stellar sparkles when a star is selected or linked."""
        for _ in range(count):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(30, 160)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.35, 0.75)
            rad = random.randint(2, 4)
            self.particles.append(Particle(x, y, vx, vy, color, rad, life))

    def emit_link_corridor(self, p1, p2, color=(60, 200, 255), count=25):
        """Emits light motes along a newly activated laser corridor."""
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        nx, ny = -dy / dist, dx / dist

        for _ in range(count):
            t = random.uniform(0.0, 1.0)
            cx = p1[0] + dx * t
            cy = p1[1] + dy * t
            side = random.choice([-1, 1]) * random.uniform(20, 80)
            vx = nx * side + random.uniform(-15, 15)
            vy = ny * side + random.uniform(-15, 15)
            life = random.uniform(0.4, 0.85)
            rad = random.randint(2, 5)
            self.particles.append(Particle(cx, cy, vx, vy, color, rad, life))

    def emit_cycle_rejection(self, p1, p2, count=24):
        """Emits fiery red sparks when Union-Find rejects a cycle."""
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        for _ in range(count):
            t = random.uniform(0.0, 1.0)
            cx = p1[0] + dx * t
            cy = p1[1] + dy * t
            angle = random.uniform(0, 6.283)
            speed = random.uniform(40, 140)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(cx, cy, vx, vy, (255, 60, 80), random.randint(2, 4), random.uniform(0.3, 0.6)))

    def emit_victory_cascade(self, stars, count=60):
        """Spawns radiant golden stardust cascade when constellation is completed."""
        for _ in range(count):
            star = random.choice(stars)
            angle = random.uniform(0, 6.283)
            speed = random.uniform(20, 180)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(20, 60)
            color = random.choice([(255, 215, 80), (140, 240, 255), (255, 255, 255), (255, 180, 100)])
            self.particles.append(Particle(star.x, star.y, vx, vy, color, random.randint(2, 5), random.uniform(0.6, 1.4)))

    def update(self, dt):
        """Updates physics of all active particles."""
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        """Renders all particles onto the given surface."""
        for p in self.particles:
            p.draw(surface)
