import pygame
import math
import os

class CelestialRenderer:
    # Star Spectrum Palettes: Name -> (Core RGB, Halo RGB, Has Rings)
    STAR_STYLES = {
        "Sol": ((255, 220, 100), (255, 160, 30), True),
        "Sirius": ((140, 230, 255), (50, 140, 255), True),
        "Vega": ((230, 245, 255), (100, 180, 255), True),
        "Rigel": ((215, 175, 255), (145, 75, 255), False),
        "Betelgeuse": ((255, 120, 60), (235, 50, 20), True)
    }

    _bg_image = None
    _cached_size = None

    @classmethod
    def load_background(cls, width, height):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "assets", "images", "world_bg.jpg")

        if os.path.exists(path):
            raw = pygame.image.load(path).convert()
            cls._bg_image = pygame.transform.smoothscale(raw, (width, height))
            # Subtle dimming layer to enhance laser filament contrast
            dim = pygame.Surface((width, height))
            dim.fill((4, 7, 18))
            dim.set_alpha(60)
            cls._bg_image.blit(dim, (0, 0))
        else:
            cls._bg_image = pygame.Surface((width, height)).convert()
            cls._bg_image.fill((6, 9, 20))

        cls._cached_size = (width, height)

    @classmethod
    def draw_background(cls, surface, width, height):
        if cls._bg_image is None or cls._cached_size != (width, height):
            cls.load_background(width, height)
        surface.blit(cls._bg_image, (0, 0))

    @staticmethod
    def draw_orbital_rings(surface, cx, cy, rx, ry, color):
        """Draws subtle elliptical orbital perspective tracks."""
        ring_surf = pygame.Surface((rx * 2 + 16, ry * 2 + 16), pygame.SRCALPHA)
        ox, oy = rx + 8, ry + 8

        # Faint outer track
        pygame.draw.ellipse(ring_surf, (*color, 50), (ox - rx, oy - ry, rx * 2, ry * 2), 1)
        # Brighter inner track
        irx, iry = int(rx * 0.74), int(ry * 0.74)
        pygame.draw.ellipse(ring_surf, (*color, 95), (ox - irx, oy - iry, irx * 2, iry * 2), 1)

        surface.blit(ring_surf, (cx - ox, cy - oy), special_flags=pygame.BLEND_ADD)

    @classmethod
    def draw_star(cls, surface, star, is_selected, now_sec, font):
        """Draw a compact, bright star with a restrained colored corona."""
        core_c, halo_c, _ = cls.STAR_STYLES.get(star.name, ((235, 247, 255), (91, 163, 236), False))
        if star.type == "POWER":
            core_c, halo_c = (151, 239, 255), (41, 166, 255)
        elif star.type == "ENERGY":
            core_c, halo_c = (169, 255, 210), (39, 208, 153)
        elif star.type == "UNSTABLE":
            core_c, halo_c = (255, 183, 150), (255, 81, 90)
        x, y = int(star.x), int(star.y)
        pulse = (math.sin(now_sec * 3.0 + star.id) + 1) * .5

        # Alpha falloff keeps each star luminous without washing out the galaxy.
        halo = pygame.Surface((96, 96), pygame.SRCALPHA)
        center = (48, 48)
        pygame.draw.circle(halo, (*halo_c, 4), center, 45)
        pygame.draw.circle(halo, (*halo_c, 7), center, 36)
        pygame.draw.circle(halo, (*halo_c, 13), center, 27)
        pygame.draw.circle(halo, (*halo_c, 28), center, 19)
        pygame.draw.circle(halo, (*core_c, 88), center, 12)
        surface.blit(halo, (x - 48, y - 48))

        orbit = pygame.Surface((98, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(orbit, (*halo_c, 45), (2, 6, 94, 32), 1)
        pygame.draw.ellipse(orbit, (*halo_c, 82), (12, 10, 74, 24), 1)
        surface.blit(orbit, (x - 49, y - 22))

        orbit_angle = now_sec * 1.2 + star.id * 1.7
        satellite = (int(x + math.cos(orbit_angle) * 43), int(y + math.sin(orbit_angle) * 14))
        pygame.draw.circle(surface, halo_c, satellite, 3)
        pygame.draw.circle(surface, (238, 250, 255), satellite, 1)

        # Tiny four point flare and crisp stellar core.
        flare = 11 + int(pulse * 5)
        pygame.draw.line(surface, core_c, (x - flare, y), (x + flare, y), 2)
        pygame.draw.line(surface, core_c, (x, y - flare), (x, y + flare), 2)
        pygame.draw.circle(surface, core_c, (x, y), 9)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 4)

        if is_selected:
            pygame.draw.circle(surface, (52, 190, 255), (x, y), int(20 + pulse * 5), 2)
            pygame.draw.circle(surface, (105, 222, 255), (x, y), 29, 1)

        # Dark label chip stays legible against both stars and nebula.
        lbl = font.render(star.name, True, (245, 245, 255))
        label_x = x + 11
        if label_x + lbl.get_width() + 12 > surface.get_width() - 185:
            label_x = x - lbl.get_width() - 17
        label_rect = pygame.Rect(label_x, y - 12, lbl.get_width() + 12, 23)
        chip = pygame.Surface(label_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(chip, (4, 9, 23, 205), chip.get_rect(), border_radius=7)
        pygame.draw.rect(chip, (*halo_c, 100), chip.get_rect(), 1, border_radius=7)
        surface.blit(chip, label_rect.topleft)
        surface.blit(lbl, (label_rect.x + 6, label_rect.y + 3))

    @staticmethod
    def draw_laser_corridor(surface, p1, p2, cost, font, is_selected=False, is_cycle=False):
        """Draws candidate and active laser corridors with edge weight badges."""
        if is_cycle:
            pygame.draw.line(surface, (255, 45, 45), p1, p2, 4)
            pygame.draw.line(surface, (255, 210, 210), p1, p2, 2)
        elif is_selected:
            # Outer cyan bloom
            pygame.draw.line(surface, (30, 140, 255), p1, p2, 5)
            # Inner cyan core
            pygame.draw.line(surface, (140, 235, 255), p1, p2, 2)
            # Center white wire
            pygame.draw.line(surface, (255, 255, 255), p1, p2, 1)
        else:
            # Subtle candidate edge
            pygame.draw.line(surface, (45, 75, 125), p1, p2, 2)

        # Edge cost pill background to keep text sharp against background stars
        mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        pill_surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (10, 16, 30, 200), (0, 0, 18, 18), border_radius=4)
        surface.blit(pill_surf, (mid[0] - 9, mid[1] - 9))

        txt_col = (230, 245, 255) if is_selected else (140, 185, 230)
        lbl = font.render(str(cost), True, txt_col)
        surface.blit(lbl, (mid[0] - 4, mid[1] - 8))
