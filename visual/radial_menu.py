"""
StarLink: Constellation Weaver
Antique Star Atlas - Astrolabe Radial Menu System

An authentic observatory astrolabe radial wheel:
- Single-trigger expansion with cubic ease-out transition
- Concentric astronomical dial rings & 36-degree graduation ticks
- Radial leader spokes connecting center compass hub to 8 cardinal/ordinal actions
- Antique brass engraving, warm parchment typography & golden glow hover states
- Rich scholarly action descriptions
"""

import math
import pygame
from theme import (
    BASE_WIDTH,
    BASE_HEIGHT,
    COLOR_BG,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    COLOR_DANGER,
    COLOR_MUTED,
    COLOR_DIVIDER,
    font_ledger_item,
    font_mono,
    font_caption,
    font_button,
)

class AstrolabeRadialMenu:
    """Radial astrolabe dial menu for seamless, tactile observatory command execution."""

    def __init__(self, cx=BASE_WIDTH // 2, cy=BASE_HEIGHT // 2):
        self.cx = cx
        self.cy = cy
        self.radius = 180
        self.is_open = False
        self.transition_t = 0.0
        self.hovered_index = None

        # 8 Cardinal & Ordinal Astronomical Actions
        self.items = [
            {
                "id": "hint",
                "label": "Hint",
                "hotkey": "[H]",
                "angle": -math.pi / 2, # North (270°)
                "desc": "MST Cut · Identifies the lowest-cost spanning corridor",
                "action": "hint",
                "key_code": pygame.K_h,
            },
            {
                "id": "solver",
                "label": "Solver",
                "hotkey": "[K]",
                "angle": -math.pi / 4, # North-East (315°)
                "desc": "Kruskal Algorithm · Step-by-step greedy spanning tree",
                "action": "solver",
                "key_code": pygame.K_k,
            },
            {
                "id": "next",
                "label": "Next Sector",
                "hotkey": "[N]",
                "angle": 0.0, # East (0°)
                "desc": "Next Sector · Advance toward Sagittarius Core",
                "action": "next",
                "key_code": pygame.K_n,
            },
            {
                "id": "brief",
                "label": "Brief",
                "hotkey": "[B]",
                "angle": math.pi / 4, # South-East (45°)
                "desc": "Mission Brief · Astronomical parameters & sector lore",
                "action": "brief",
                "key_code": pygame.K_b,
            },
            {
                "id": "worlds",
                "label": "Sectors",
                "hotkey": "[W]",
                "angle": math.pi / 2, # South (90°)
                "desc": "Chart Index · Select from all 10 celestial sectors",
                "action": "worlds",
                "key_code": pygame.K_w,
            },
            {
                "id": "sky_info",
                "label": "Star Info",
                "hotkey": "[I]",
                "angle": 3 * math.pi / 4, # South-West (135°)
                "desc": "Star Notes · Kruskal rules and sector nodes",
                "action": "sky_info",
                "key_code": pygame.K_i,
            },
            {
                "id": "reset",
                "label": "Reset",
                "hotkey": "[R]",
                "angle": math.pi, # West (180°)
                "desc": "Reset Sector · Reclaim reserve energy and clear links",
                "action": "reset",
                "key_code": pygame.K_r,
            },
            {
                "id": "undo",
                "label": "Undo",
                "hotkey": "[Z]",
                "angle": -3 * math.pi / 4, # North-West (225°)
                "desc": "Undo Link · Roll back the last established corridor",
                "action": "undo",
                "key_code": pygame.K_z,
            },
        ]

    def open(self, center=None):
        if center:
            self.cx, self.cy = center
        self.is_open = True

    def close(self):
        self.is_open = False

    def toggle(self, center=None):
        if self.is_open:
            self.close()
        else:
            self.open(center)

    def update(self, dt):
        """Animates radial expansion and contraction with cubic easing."""
        if self.is_open:
            self.transition_t = min(1.0, self.transition_t + dt / 0.22)
        else:
            self.transition_t = max(0.0, self.transition_t - dt / 0.16)

    def handle_event(self, event):
        """
        Processes mouse and keyboard events when menu is active.
        Returns the action identifier string if an option was clicked, or None.
        """
        if not self.is_open and self.transition_t <= 0.01:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.transition_t > 0.65:
                if self.hovered_index is not None:
                    action = self.items[self.hovered_index]["action"]
                    self.close()
                    return action

                # Center hub click or outside click closes menu
                hub_r = 34
                dist = math.hypot(event.pos[0] - self.cx, event.pos[1] - self.cy)
                if dist <= hub_r or dist > self.radius + 110:
                    self.close()
                    return "close"

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                self.close()
                return "close"

            # Direct action hotkeys while radial is open
            for item in self.items:
                if event.key == item.get("key_code"):
                    self.close()
                    return item["action"]

        return None

    def draw(self, surface, mouse_pos):
        """Renders the complete animated radial astrolabe dial."""
        if self.transition_t <= 0.01:
            return

        w, h = surface.get_size()

        # Smooth cubic ease-out
        s = 1.0 - (1.0 - self.transition_t) ** 3
        curr_r = self.radius * s
        rot_offset = (1.0 - s) * -0.32  # Subtle astronomical rotation during fan-out

        # 1. Soft dark veil over background chart
        veil = pygame.Surface((w, h), pygame.SRCALPHA)
        veil_alpha = int(180 * s)
        veil.fill((14, 20, 32, veil_alpha))
        surface.blit(veil, (0, 0))

        # 2. Astrolabe Rings & Dial Geometry Surface
        dial_surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Outer graduated astrolabe ring
        out_r = int(curr_r + 48)
        pygame.draw.circle(dial_surf, (*COLOR_ACCENT[:3], int(140 * s)), (self.cx, self.cy), out_r, 1)
        pygame.draw.circle(dial_surf, (*COLOR_ACCENT[:3], int(75 * s)), (self.cx, self.cy), out_r - 6, 1)

        # 36 degree ticks on outer ring (mariner's compass style)
        num_ticks = 36
        for i in range(num_ticks):
            ta = i * (math.tau / num_ticks) + rot_offset
            t_len = 8 if (i % 3 == 0) else 4
            p1 = (self.cx + int((out_r - t_len) * math.cos(ta)), self.cy + int((out_r - t_len) * math.sin(ta)))
            p2 = (self.cx + int(out_r * math.cos(ta)), self.cy + int(out_r * math.sin(ta)))
            col = COLOR_ACCENT if (i % 3 == 0) else COLOR_MUTED
            pygame.draw.line(dial_surf, (*col[:3], int(150 * s)), p1, p2, 1)

        # Orbital ring passing through buttons
        pygame.draw.circle(dial_surf, (*COLOR_ACCENT[:3], int(95 * s)), (self.cx, self.cy), int(curr_r), 1)

        # 3. Calculate button positions and detect hover
        f_btn = font_ledger_item()
        f_mono = font_mono(12)
        f_cap = font_caption()

        self.hovered_index = None
        btn_rects = []

        bw, bh = 124, 38
        for idx, item in enumerate(self.items):
            angle = item["angle"] + rot_offset
            bx = self.cx + int(curr_r * math.cos(angle))
            by = self.cy + int(curr_r * math.sin(angle))
            rect = pygame.Rect(bx - bw // 2, by - bh // 2, bw, bh)
            btn_rects.append((rect, bx, by, angle))

            if rect.collidepoint(mouse_pos) and s > 0.65:
                self.hovered_index = idx

        # 4. Draw Radial Leader Spokes from Center Hub
        for idx, item in enumerate(self.items):
            rect, bx, by, angle = btn_rects[idx]
            is_hover = (self.hovered_index == idx)
            spoke_col = (245, 230, 165) if is_hover else COLOR_MUTED
            spoke_alpha = int(230 * s) if is_hover else int(90 * s)

            h_rad = 34
            sp1 = (self.cx + int(h_rad * math.cos(angle)), self.cy + int(h_rad * math.sin(angle)))
            sp2 = (bx - int((bw // 2) * math.cos(angle) * 0.75), by - int((bh // 2) * math.sin(angle) * 0.75))

            if is_hover:
                pygame.draw.line(dial_surf, (*spoke_col[:3], spoke_alpha), sp1, sp2, 2)
            else:
                pygame.draw.line(dial_surf, (*spoke_col[:3], spoke_alpha), sp1, sp2, 1)

        surface.blit(dial_surf, (0, 0))

        # 5. Center Astrolabe Compass Rose Hub
        hub_r = 30
        hub_hover = math.hypot(mouse_pos[0] - self.cx, mouse_pos[1] - self.cy) <= hub_r and s > 0.65
        pygame.draw.circle(surface, COLOR_BG, (self.cx, self.cy), hub_r)
        pygame.draw.circle(surface, (245, 230, 165) if hub_hover else COLOR_ACCENT, (self.cx, self.cy), hub_r, 1)
        pygame.draw.circle(surface, COLOR_ACCENT, (self.cx, self.cy), hub_r - 4, 1)

        # Engraved brass celestial compass rose in center
        c_col = (245, 230, 165) if hub_hover else COLOR_ACCENT
        pygame.draw.circle(surface, c_col, (self.cx, self.cy), 3)
        pygame.draw.circle(surface, c_col, (self.cx, self.cy), 8, 1)
        pygame.draw.line(surface, c_col, (self.cx - 16, self.cy), (self.cx + 16, self.cy), 1)
        pygame.draw.line(surface, c_col, (self.cx, self.cy - 16), (self.cx, self.cy + 16), 1)
        diag = 10
        pygame.draw.line(surface, c_col, (self.cx - diag, self.cy - diag), (self.cx + diag, self.cy + diag), 1)
        pygame.draw.line(surface, c_col, (self.cx - diag, self.cy + diag), (self.cx + diag, self.cy - diag), 1)

        # 6. Draw Action Buttons
        for idx, item in enumerate(self.items):
            rect, bx, by, angle = btn_rects[idx]
            is_hover = (self.hovered_index == idx)

            # Button container
            pygame.draw.rect(surface, COLOR_BG, rect)

            b_col = (245, 230, 165) if is_hover else COLOR_ACCENT
            pygame.draw.rect(surface, b_col, rect, 2 if is_hover else 1)

            # Subtle inner border for antique engraving look
            inner = rect.inflate(-6, -6)
            pygame.draw.rect(surface, b_col, inner, 1)

            # Corner tick accents
            for cx_c, cy_c, dx, dy in [
                (rect.left + 3, rect.top + 3, 1, 1),
                (rect.right - 3, rect.top + 3, -1, 1),
                (rect.left + 3, rect.bottom - 3, 1, -1),
                (rect.right - 3, rect.bottom - 3, -1, -1),
            ]:
                pygame.draw.line(surface, b_col, (cx_c, cy_c), (cx_c + dx * 4, cy_c), 1)
                pygame.draw.line(surface, b_col, (cx_c, cy_c), (cx_c, cy_c + dy * 4), 1)

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

        # 7. Scholarly Description Caption Pill
        desc_text = "Select an astrolabe action or click center hub to dismiss"
        if self.hovered_index is not None:
            desc_text = self.items[self.hovered_index]["desc"]
        elif hub_hover:
            desc_text = "Click center hub or press [ESC] to return to star chart"

        desc_surf = f_cap.render(desc_text, True, COLOR_ACCENT if self.hovered_index is not None else COLOR_MUTED)
        desc_rect = desc_surf.get_rect(center=(self.cx, self.cy + self.radius + 76))

        pill_rect = desc_rect.inflate(32, 10)
        pygame.draw.rect(surface, COLOR_BG, pill_rect)
        pygame.draw.rect(surface, COLOR_ACCENT if self.hovered_index is not None else COLOR_DIVIDER, pill_rect, 1)
        surface.blit(desc_surf, desc_rect)
