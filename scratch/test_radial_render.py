import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import math
import pygame
pygame.init()
from theme import (
    BASE_WIDTH, BASE_HEIGHT,
    COLOR_BG, COLOR_PRIMARY, COLOR_ACCENT, COLOR_DANGER, COLOR_MUTED, COLOR_DIVIDER,
    font_title, font_subtitle, font_ledger_item, font_caption, font_button, font_mono
)

class AstrolabeRadialMenu:
    def __init__(self, cx=BASE_WIDTH // 2, cy=BASE_HEIGHT // 2):
        self.cx = cx
        self.cy = cy
        self.radius = 155
        self.is_open = False
        self.transition_t = 0.0
        self.hovered_index = None

        self.items = [
            {
                "id": "hint",
                "label": "Hint",
                "hotkey": "[H]",
                "glyph": "✧",
                "angle": -math.pi / 2, # North (Top)
                "desc": "MST Cut · Identifies the optimal greedy link",
                "action": "hint"
            },
            {
                "id": "solver",
                "label": "Solver",
                "hotkey": "[K]",
                "glyph": "⚙",
                "angle": -math.pi / 4, # North-East
                "desc": "Kruskal Algorithm · Step-by-step greedy spanning tree",
                "action": "solver"
            },
            {
                "id": "next",
                "label": "Next Sector",
                "hotkey": "[N]",
                "glyph": "➔",
                "angle": 0.0, # East (Right)
                "desc": "Next Sector · Advance toward Sagittarius Core",
                "action": "next"
            },
            {
                "id": "brief",
                "label": "Brief",
                "hotkey": "[B]",
                "glyph": "📜",
                "angle": math.pi / 4, # South-East
                "desc": "Mission Brief · Astronomical parameters & lore",
                "action": "brief"
            },
            {
                "id": "worlds",
                "label": "Sectors",
                "hotkey": "[W]",
                "glyph": "🗺",
                "angle": math.pi / 2, # South (Bottom)
                "desc": "Chart Index · Select from all 10 celestial sectors",
                "action": "worlds"
            },
            {
                "id": "protocols",
                "label": "Protocols",
                "hotkey": "[?]",
                "glyph": "ℹ",
                "angle": 3 * math.pi / 4, # South-West
                "desc": "Protocols · Special star mechanics & observatory rules",
                "action": "protocols"
            },
            {
                "id": "reset",
                "label": "Reset",
                "hotkey": "[R]",
                "glyph": "↺",
                "angle": math.pi, # West (Left)
                "desc": "Reset Sector · Reclaim reserve energy and clear links",
                "action": "reset"
            },
            {
                "id": "undo",
                "label": "Undo",
                "hotkey": "[Z]",
                "glyph": "↶",
                "angle": -3 * math.pi / 4, # North-West
                "desc": "Undo Link · Roll back the last established corridor",
                "action": "undo"
            },
        ]

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def toggle(self):
        self.is_open = not self.is_open

    def update(self, dt):
        if self.is_open:
            self.transition_t = min(1.0, self.transition_t + dt / 0.22)
        else:
            self.transition_t = max(0.0, self.transition_t - dt / 0.16)

    def draw(self, surface, mouse_pos):
        if self.transition_t <= 0.01:
            return

        # Smooth cubic ease-out
        s = 1.0 - (1.0 - self.transition_t) ** 3
        curr_r = self.radius * s
        rot_offset = (1.0 - s) * -0.35 # subtle rotation as it blooms outward

        # 1. Semi-transparent dark veil
        veil = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        veil_alpha = int(170 * s)
        veil.fill((14, 20, 32, veil_alpha))
        surface.blit(veil, (0, 0))

        # 2. Astrolabe Rings & Dial Geometry
        dial_surf = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        
        # Outer graduated astrolabe ring
        out_r = int(curr_r + 48)
        pygame.draw.circle(dial_surf, (*COLOR_ACCENT[:3], int(130 * s)), (self.cx, self.cy), out_r, 1)
        pygame.draw.circle(dial_surf, (*COLOR_ACCENT[:3], int(70 * s)), (self.cx, self.cy), out_r - 6, 1)
        
        # 36 degree ticks on outer ring
        num_ticks = 36
        for i in range(num_ticks):
            ta = i * (math.tau / num_ticks) + rot_offset
            t_len = 8 if (i % 3 == 0) else 4
            p1 = (self.cx + int((out_r - t_len) * math.cos(ta)), self.cy + int((out_r - t_len) * math.sin(ta)))
            p2 = (self.cx + int(out_r * math.cos(ta)), self.cy + int(out_r * math.sin(ta)))
            col = COLOR_ACCENT if (i % 3 == 0) else COLOR_MUTED
            pygame.draw.line(dial_surf, (*col[:3], int(150 * s)), p1, p2, 1)

        # Orbital ring passing through buttons
        pygame.draw.circle(dial_surf, (*COLOR_ACCENT[:3], int(90 * s)), (self.cx, self.cy), int(curr_r), 1)

        # 3. Calculate button positions and detect hover
        f_btn = font_ledger_item()
        f_mono = font_mono(12)
        f_cap = font_caption()
        
        self.hovered_index = None
        btn_rects = []
        
        bw, bh = 120, 36
        for idx, item in enumerate(self.items):
            angle = item["angle"] + rot_offset
            bx = self.cx + int(curr_r * math.cos(angle))
            by = self.cy + int(curr_r * math.sin(angle))
            rect = pygame.Rect(bx - bw // 2, by - bh // 2, bw, bh)
            btn_rects.append((rect, bx, by, angle))
            
            if rect.collidepoint(mouse_pos) and s > 0.7:
                self.hovered_index = idx

        # 4. Draw Leader Spokes from Center Hub
        for idx, item in enumerate(self.items):
            rect, bx, by, angle = btn_rects[idx]
            is_hover = (self.hovered_index == idx)
            spoke_col = COLOR_ACCENT if is_hover else COLOR_MUTED
            spoke_alpha = int(220 * s) if is_hover else int(90 * s)
            
            # Start slightly outside center hub
            h_rad = 34
            sp1 = (self.cx + int(h_rad * math.cos(angle)), self.cy + int(h_rad * math.sin(angle)))
            sp2 = (bx - int((bw // 2) * math.cos(angle) * 0.7), by - int((bh // 2) * math.sin(angle) * 0.7))
            
            if is_hover:
                pygame.draw.line(dial_surf, (*spoke_col[:3], spoke_alpha), sp1, sp2, 2)
            else:
                # Dashed leader line
                pygame.draw.line(dial_surf, (*spoke_col[:3], spoke_alpha), sp1, sp2, 1)

        surface.blit(dial_surf, (0, 0))

        # 5. Center Compass Hub
        hub_r = 30
        hub_hover = math.hypot(mouse_pos[0] - self.cx, mouse_pos[1] - self.cy) <= hub_r and s > 0.7
        pygame.draw.circle(surface, COLOR_BG, (self.cx, self.cy), hub_r)
        pygame.draw.circle(surface, (245, 230, 165) if hub_hover else COLOR_ACCENT, (self.cx, self.cy), hub_r, 1)
        pygame.draw.circle(surface, COLOR_ACCENT, (self.cx, self.cy), hub_r - 4, 1)
        
        # Center astrolabe crosshairs
        for d in [-1, 1]:
            pygame.draw.line(surface, COLOR_ACCENT, (self.cx + d * (hub_r - 4), self.cy), (self.cx + d * (hub_r + 6), self.cy), 1)
            pygame.draw.line(surface, COLOR_ACCENT, (self.cx, self.cy + d * (hub_r - 4)), (self.cx, self.cy + d * (hub_r + 6)), 1)

        # Center text / symbol
        c_sym = f_btn.render("✦", True, (245, 230, 165) if hub_hover else COLOR_ACCENT)
        surface.blit(c_sym, c_sym.get_rect(center=(self.cx, self.cy - 1)))

        # 6. Draw Buttons
        for idx, item in enumerate(self.items):
            rect, bx, by, angle = btn_rects[idx]
            is_hover = (self.hovered_index == idx)

            # Button container
            pygame.draw.rect(surface, COLOR_BG, rect)
            
            b_col = (245, 230, 165) if is_hover else COLOR_ACCENT
            pygame.draw.rect(surface, b_col, rect, 2 if is_hover else 1)
            
            # Subtle inner border for antique engraving look
            inner = rect.inflate(-6, -6)
            pygame.draw.rect(surface, (*b_col[:3], 140 if is_hover else 60), inner, 1)

            # Label + Hotkey badge
            lbl_surf = f_btn.render(item["label"], True, (255, 252, 240) if is_hover else COLOR_PRIMARY)
            hk_surf = f_mono.render(item["hotkey"], True, COLOR_ACCENT if is_hover else COLOR_MUTED)

            lw, lh = lbl_surf.get_size()
            hw, hh = hk_surf.get_size()
            total_w = lw + hw + 6

            start_tx = rect.centerx - total_w // 2
            surface.blit(lbl_surf, (start_tx, rect.centery - lh // 2))
            surface.blit(hk_surf, (start_tx + lw + 6, rect.centery - hh // 2 + 1))

            # Hover underline
            if is_hover:
                pygame.draw.line(surface, COLOR_ACCENT, (start_tx, rect.bottom - 5), (start_tx + total_w, rect.bottom - 5), 1)

        # 7. Scholarly Description Caption
        desc_text = "Select action or click center to return to star chart"
        if self.hovered_index is not None:
            desc_text = self.items[self.hovered_index]["desc"]
        elif hub_hover:
            desc_text = "Click center hub or press [ESC] to close Astrolabe"

        desc_surf = f_cap.render(desc_text, True, COLOR_ACCENT if self.hovered_index is not None else COLOR_MUTED)
        desc_rect = desc_surf.get_rect(center=(self.cx, self.cy + self.radius + 80))
        
        # Pill back for readable caption
        pill_rect = desc_rect.inflate(24, 8)
        pygame.draw.rect(surface, COLOR_BG, pill_rect)
        pygame.draw.rect(surface, COLOR_DIVIDER, pill_rect, 1)
        surface.blit(desc_surf, desc_rect)

# Test render
WIDTH, HEIGHT = 1024, 736
test_surf = pygame.Surface((WIDTH, HEIGHT))
test_surf.fill(COLOR_BG)

menu = AstrolabeRadialMenu()
menu.is_open = True
menu.transition_t = 1.0

# Simulate mouse hover on 'hint' (top item)
top_rect = pygame.Rect(menu.cx - 60, menu.cy - menu.radius - 18, 120, 36)
menu.draw(test_surf, (top_rect.centerx, top_rect.centery))

pygame.image.save(test_surf, "assets/images/test_radial_menu.png")
print("Saved assets/images/test_radial_menu.png")

