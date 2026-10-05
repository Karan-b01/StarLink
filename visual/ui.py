import pygame

class Button:
    def __init__(self, rect, text, bg_color=(35, 45, 80), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.hovered = False

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def draw(self, surface, font):
        color = (min(255, self.bg_color[0] + 30), min(255, self.bg_color[1] + 30), min(255, self.bg_color[2] + 40)) if self.hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (70, 90, 140), self.rect, 1, border_radius=6)
        txt = font.render(self.text, True, self.text_color)
        t_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, t_rect)

class UIOverlay:
    @staticmethod
    def draw_energy_bar(surface, font, current, max_val, pos=(30, 60), size=(220, 20)):
        x, y = pos
        w, h = size
        pct = max(0.0, min(1.0, current / max_val if max_val > 0 else 0))
        # Background bar
        pygame.draw.rect(surface, (30, 40, 60), (x, y, w, h), border_radius=4)
        # Dynamic colored fill (cyan -> orange -> red when low)
        fill_color = (60, 220, 240) if pct > 0.4 else ((240, 180, 50) if pct > 0.2 else (240, 60, 60))
        pygame.draw.rect(surface, fill_color, (x, y, int(w * pct), h), border_radius=4)
        pygame.draw.rect(surface, (120, 150, 190), (x, y, w, h), 1, border_radius=4)

        lbl = font.render(f"ENERGY: {current}/{max_val}", True, (240, 240, 255))
        surface.blit(lbl, (x + w + 15, y + 2))

    @staticmethod
    def draw_victory_modal(surface, font_large, font_small, stars_earned, player_cost, optimal_cost, screen_w, screen_h):
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((5, 10, 25, 200))
        surface.blit(overlay, (0, 0))

        box_rect = pygame.Rect(screen_w // 2 - 250, screen_h // 2 - 160, 500, 320)
        pygame.draw.rect(surface, (20, 28, 55), box_rect, border_radius=12)
        pygame.draw.rect(surface, (100, 140, 220), box_rect, 2, border_radius=12)

        title = font_large.render("CONSTELLATION RESTORED!", True, (255, 230, 100))
        surface.blit(title, title.get_rect(center=(screen_w // 2, screen_h // 2 - 100)))

        # Animated stars
        star_str = "★ " * stars_earned + "☆ " * (3 - stars_earned)
        stars_surface = font_large.render(star_str.strip(), True, (255, 215, 0))
        surface.blit(stars_surface, stars_surface.get_rect(center=(screen_w // 2, screen_h // 2 - 40)))

        detail = font_small.render(f"Your Energy Cost: {player_cost} | Optimal MST: {optimal_cost}", True, (200, 220, 255))
        surface.blit(detail, detail.get_rect(center=(screen_w // 2, screen_h // 2 + 10)))

        hint = font_small.render("Press 'N' for Next Level | 'R' to Replay", True, (150, 255, 180))
        surface.blit(hint, hint.get_rect(center=(screen_w // 2, screen_h // 2 + 70)))