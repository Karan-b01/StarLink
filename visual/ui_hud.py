import pygame

class GlassPanel:
    @staticmethod
    def draw(surface, rect, border_color=(39, 117, 170), bg_color=(5, 12, 27, 226), border_radius=12, glow=False):
        x, y, w, h = rect
        if glow:
            glow_surf = pygame.Surface((w + 14, h + 14), pygame.SRCALPHA)
            bc = border_color[:3]
            pygame.draw.rect(glow_surf, (*bc, 38), (0, 0, w + 14, h + 14), border_radius=border_radius + 4)
            surface.blit(glow_surf, (x - 7, y - 7))

        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, bg_color, (0, 0, w, h), border_radius=border_radius)
        pygame.draw.rect(panel_surf, border_color, (0, 0, w, h), 1, border_radius=border_radius)
        pygame.draw.line(panel_surf, (140, 220, 255, 80), (border_radius, 1), (w - border_radius, 1), 1)
        surface.blit(panel_surf, (x, y))

class UIHud:
    def __init__(self, width=1100, height=720):
        self.width = width
        self.height = height

        self.font_logo = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI", 12)
        self.font_section = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 14)
        self.font_btn = pygame.font.SysFont("Segoe UI", 15, bold=True)

        # Top Right Quick Buttons (matching reference image)
        self.btn_undo = pygame.Rect(752, 18, 54, 38)
        self.btn_redo = pygame.Rect(812, 18, 54, 38)
        self.btn_settings = pygame.Rect(872, 18, 60, 38)   # RESET
        self.btn_sound = pygame.Rect(938, 18, 44, 38)      # SFX / Sound
        self.btn_music = pygame.Rect(988, 18, 44, 38)      # Music
        self.btn_maximize = pygame.Rect(1038, 18, 44, 38)   # ⛶ Fullscreen / Maximize

        # Bottom Bar Navigation Buttons (matching reference image)
        self.btn_brief = pygame.Rect(18, height - 58, 240, 42)
        self.btn_worlds = pygame.Rect(276, height - 54, 96, 38)
        self.btn_algo = pygame.Rect(380, height - 54, 98, 38)
        self.btn_hint = pygame.Rect(486, height - 54, 104, 38)
        self.btn_next = pygame.Rect(598, height - 54, 126, 38)
        self.btn_sky_info = pygame.Rect(732, height - 54, 110, 38)

        # Worlds Selection Drawer
        self.show_worlds_drawer = False
        self.drawer_progress = 0.0
        self.world_option_rects = [
            pygame.Rect(343 + (index // 5) * 214, height - 255 + (index % 5) * 36, 204, 30)
            for index in range(10)
        ]

    def draw_top_bar(self, surface, state, is_muted, is_music_muted=False, display_energy=None):
        # 1. StarLink Logo Capsule
        GlassPanel.draw(surface, (18, 16, 175, 52), border_color=(45, 110, 180), border_radius=14)
        cx, cy = 42, 42
        pulse = .5 + .5 * pygame.math.Vector2(1, 0).rotate(pygame.time.get_ticks() * .12).y
        pygame.draw.circle(surface, (20, 104, 173), (cx, cy), 18)
        pygame.draw.circle(surface, (50, 192, 248), (cx, cy), 14 + int(pulse * 2), 1)
        logo_points = [(cx - 9, cy + 4), (cx - 2, cy - 8), (cx + 9, cy - 3), (cx + 5, cy + 9)]
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
            pygame.draw.line(surface, (144, 229, 255), logo_points[a], logo_points[b], 1)
        for point in logo_points:
            pygame.draw.circle(surface, (233, 249, 255), point, 2)
        surface.blit(self.font_logo.render("StarLink", True, (240, 248, 255)), (66, 22))
        surface.blit(self.font_sub.render("CONSTELLATION PUZZLE", True, (115, 180, 220)), (68, 47))

        # 2. Sector Mission Capsule
        GlassPanel.draw(surface, (202, 16, 260, 52), border_color=(45, 110, 180), border_radius=14)
        world_title = state.name.split(" - ")[-1].upper()
        if len(world_title) > 22:
            world_title = world_title[:19] + "..."
        sector_caption = f"ACTIVE SECTOR  (SECTOR {state.world_id:02} / {state.difficulty})"
        surface.blit(self.font_sub.render(sector_caption, True, (120, 180, 220)), (218, 20))
        # Glowing yellow/amber status orb matching reference
        pygame.draw.circle(surface, (255, 200, 80), (225, 47), 5)
        pygame.draw.circle(surface, (255, 240, 180), (225, 47), 2)
        surface.blit(self.font_section.render(world_title, True, (235, 245, 255)), (237, 37))

        # 3. Energy Bar Capsule
        GlassPanel.draw(surface, (470, 16, 262, 52), border_color=(45, 120, 200), border_radius=14)
        # Cyan Lightning Bolt
        pygame.draw.polygon(surface, (60, 215, 255), [(488, 23), (480, 39), (487, 39), (483, 55), (497, 35), (490, 35)])
        disp_e = state.energy if display_energy is None else display_energy
        e_text = f"ENERGY  {int(disp_e)} / {state.max_energy}"
        surface.blit(self.font_section.render(e_text, True, (230, 245, 255)), (504, 20))

        # Energy Glowing Gradient Bar (Cyan -> Purple with leading spark)
        bar_x, bar_y, bar_w, bar_h = 504, 43, 215, 12
        pygame.draw.rect(surface, (10, 20, 35), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pct = max(0.0, min(1.0, disp_e / state.max_energy if state.max_energy > 0 else 0))
        if pct > 0:
            cur_w = max(4, int(bar_w * pct))
            bar_surf = pygame.Surface((cur_w, bar_h), pygame.SRCALPHA)
            for bx in range(cur_w):
                t_grad = bx / max(1, bar_w)
                r = int(45 + t_grad * 140)
                g = int(210 - t_grad * 120)
                b = 255
                pygame.draw.line(bar_surf, (r, g, b, 240), (bx, 0), (bx, bar_h))
            surface.blit(bar_surf, (bar_x, bar_y))
            pygame.draw.circle(surface, (255, 255, 255), (bar_x + cur_w - 2, bar_y + bar_h // 2), 4)

        # 4. Top Right Quick Buttons (matching reference image)
        mouse_pos = pygame.mouse.get_pos()
        buttons = [
            (self.btn_undo, "UNDO", False),
            (self.btn_redo, "REDO", False),
            (self.btn_settings, "RESET", False),
            (self.btn_sound, "MUTE" if is_muted else "SFX", is_muted),
            (self.btn_music, "♫ OFF" if is_music_muted else "♫", is_music_muted),
            (self.btn_maximize, "⛶", False),
        ]
        for rect, label, active in buttons:
            hover = rect.collidepoint(mouse_pos)
            bg = (24, 48, 80) if hover else (12, 22, 38)
            border = (80, 185, 245) if hover else (45, 95, 160)
            GlassPanel.draw(surface, rect, border_color=border, bg_color=(*bg, 235), border_radius=10, glow=hover)
            txt = self.font_sub.render(label, True, (240, 248, 255) if hover else (190, 220, 245))
            surface.blit(txt, txt.get_rect(center=rect.center))

    def draw_left_stars_panel(self, surface, stars):
        """Draws the star roster panel on the left."""
        roster_height = min(290, 46 + len(stars) * 20 + 66)
        GlassPanel.draw(surface, (18, 92, 136, roster_height))
        surface.blit(self.font_section.render("STAR ROSTER", True, (121, 204, 239)), (30, 103))
        pygame.draw.line(surface, (36, 67, 91), (30, 126), (142, 126), 1)

        y = 132
        for s in stars:
            color = self._star_color(s.name, s.type)
            glow_color = tuple(channel // 4 for channel in color)
            pygame.draw.circle(surface, glow_color, (38, y + 5), 7)
            pygame.draw.circle(surface, color, (38, y + 5), 4)
            pygame.draw.circle(surface, (235, 248, 255), (38, y + 5), 1)
            label = self.fit_text(s.name.upper(), self.font_body, 98)
            surface.blit(self.font_body.render(label, True, (204, 222, 239)), (51, y - 2))
            y += 20

        y += 3
        pygame.draw.line(surface, (36, 67, 91), (30, y), (142, y), 1)
        legend = [
            ("POWER: half cost", (85, 207, 255)),
            ("ENERGY: +5 reserve", (89, 232, 183)),
            ("UNSTABLE: timed link", (255, 119, 112)),
        ]
        for label, color in legend:
            surface.blit(self.font_sub.render(self.fit_text(label, self.font_sub, 112), True, color), (30, y + 5))
            y += 15

    @staticmethod
    def fit_text(text, font, max_width):
        """Ellipsize labels to their actual pixel width, not an arbitrary character count."""
        if font.size(text)[0] <= max_width:
            return text
        suffix = "…"
        while text and font.size(text + suffix)[0] > max_width:
            text = text[:-1]
        return text + suffix

    @staticmethod
    def _star_color(name, star_type="NORMAL"):
        named = {
            "Sol": (255, 190, 77), "Sirius": (89, 195, 255),
            "Vega": (207, 229, 255), "Rigel": (157, 119, 255),
            "Betelgeuse": (255, 111, 85),
        }
        type_colors = {
            "POWER": (85, 207, 255), "ENERGY": (89, 232, 183),
            "UNSTABLE": (255, 119, 112), "NORMAL": (173, 206, 246),
        }
        return named.get(name, type_colors.get(star_type, (109, 208, 246)))

    def draw_kruskal_inspector(self, surface, state):
        """Draws the live Kruskal's algorithm list on the right side."""
        panel_rect = (920, 92, 164, 332)
        GlassPanel.draw(surface, panel_rect, border_color=(45, 95, 175))

        surface.blit(self.font_section.render("KRUSKAL", True, (121, 204, 239)), (932, 104))
        surface.blit(self.font_sub.render("EDGES  /  LOWEST WEIGHT", True, (115, 153, 183)), (932, 125))
        pygame.draw.line(surface, (36, 67, 91), (932, 145), (1072, 145), 1)

        sorted_edges = sorted(
            state.edges,
            key=lambda edge: state.compute_edge_cost(edge[0], edge[1], edge[2]),
        )
        y = 153
        for idx, (u, v, w) in enumerate(sorted_edges[:7]):
            u_name = state.stars[u].name
            v_name = state.stars[v].name
            display_weight = state.compute_edge_cost(u, v, w)

            is_picked = any(e[0] == min(u, v) and e[1] == max(u, v) for e in state.selected_edges)
            txt_color = (94, 232, 208) if is_picked else (177, 199, 220)

            # Numbered pill badge
            pygame.draw.circle(surface, (59, 123, 159) if is_picked else (26, 42, 64), (940, y + 8), 9)
            n = self.font_sub.render(f"{idx+1:02}", True, (220, 240, 255) if is_picked else (140, 180, 210))
            surface.blit(n, n.get_rect(center=(940, y + 8)))

            # Weight & Edge Name
            surface.blit(self.font_body.render(f"{display_weight}", True, (89, 195, 235)), (955, y))
            line_str = self.fit_text(f"{u_name}-{v_name}", self.font_sub, 92)
            edge_label = self.font_sub.render(line_str, True, txt_color)
            surface.blit(edge_label, (972, y + 1))

            # Vertical indicator status tag on right edge
            tag_color = (70, 235, 150) if is_picked else (40, 70, 95)
            pygame.draw.rect(surface, tag_color, (1072, y + 2, 4, 15), border_radius=2)

            y += 21

        pygame.draw.line(surface, (36, 67, 91), (932, y + 3), (1072, y + 3), 1)
        surface.blit(self.font_sub.render("RESTORED LINKS", True, (121, 204, 239)), (932, y + 10))

        sel_y = y + 30
        for u, v, w in state.selected_edges[:4]:
            u_name = state.stars[u].name
            v_name = state.stars[v].name
            link_label = self.fit_text(f"⚡{w}  {u_name} - {v_name}", self.font_sub, 140)
            surface.blit(self.font_sub.render(link_label, True, (116, 224, 197)), (932, sel_y))
            sel_y += 17

    def draw_controls_panel(self, surface):
        """Draws the controls guide panel."""
        GlassPanel.draw(surface, (920, 434, 164, 178))
        surface.blit(self.font_section.render("FLIGHT CONTROLS", True, (121, 204, 239)), (932, 446))
        pygame.draw.line(surface, (36, 67, 91), (932, 470), (1072, 470), 1)

        controls = [
            ("CLICK TWO STARS", "Create a connection"),
            ("H", "Algorithm Hint (MST Cut)"),
            ("Z   /   Y", "Undo   /   redo"),
            ("K", "Animate Kruskal"),
            ("M   /   P", "Sound effects / music"),
            ("R", "Restart sector"),
        ]
        y = 472
        for key_text, desc in controls:
            surface.blit(self.font_body.render(key_text, True, (207, 227, 243)), (932, y))
            surface.blit(self.font_sub.render(desc, True, (132, 165, 191)), (932, y + 12))
            y += 24

    def draw_bottom_dock(self, surface, state, is_maximized=False):
        """Draws the bottom status capsule and action buttons."""
        mouse_pos = pygame.mouse.get_pos()
        brief_hover = self.btn_brief.collidepoint(mouse_pos)
        GlassPanel.draw(surface, self.btn_brief, border_color=(80, 190, 250) if brief_hover else (45, 110, 180), glow=brief_hover)

        # Planet horizon / galaxy slice emblem
        bx, by = self.btn_brief.x + 22, self.btn_brief.centery
        pygame.draw.circle(surface, (15, 35, 75), (bx, by), 15)
        pygame.draw.circle(surface, (45, 120, 210), (bx, by), 15, 1)
        pygame.draw.arc(surface, (120, 220, 255), (bx - 14, by - 14, 28, 28), 0.2, 2.9, 2)
        pygame.draw.circle(surface, (230, 245, 255), (bx + 4, by - 5), 2)

        # Brief text
        surface.blit(self.font_sub.render("MISSION BRIEF", True, (120, 205, 245)), (self.btn_brief.x + 44, self.btn_brief.y + 4))
        title = state.name if len(state.name) < 22 else state.name[:19] + "..."
        surface.blit(self.font_body.render(title, True, (230, 245, 255)), (self.btn_brief.x + 44, self.btn_brief.y + 19))
        info_color = (170, 230, 255) if brief_hover else (110, 170, 210)
        info_mark = self.font_sub.render("OPEN ›", True, info_color)
        surface.blit(info_mark, (self.btn_brief.right - 46, self.btn_brief.centery - 6))

        # Worlds Button (Pill shape)
        hover_w = self.btn_worlds.collidepoint(mouse_pos)
        w_bg = (25, 52, 85) if hover_w else (12, 24, 42)
        w_bc = (80, 190, 250) if hover_w else (45, 100, 165)
        GlassPanel.draw(surface, self.btn_worlds, border_color=w_bc, bg_color=(*w_bg, 245), border_radius=19, glow=hover_w)
        t_w = self.font_btn.render("WORLDS", True, (240, 248, 255) if hover_w else (190, 220, 245))
        surface.blit(t_w, t_w.get_rect(center=self.btn_worlds.center))

        # Algorithm Solver Replay Button (Pill shape)
        hover_a = self.btn_algo.collidepoint(mouse_pos)
        a_bg = (25, 52, 85) if hover_a else (12, 24, 42)
        a_bc = (80, 190, 250) if hover_a else (45, 100, 165)
        GlassPanel.draw(surface, self.btn_algo, border_color=a_bc, bg_color=(*a_bg, 245), border_radius=19, glow=hover_a)
        t_a = self.font_btn.render("SOLVER K", True, (240, 248, 255) if hover_a else (190, 220, 245))
        surface.blit(t_a, t_a.get_rect(center=self.btn_algo.center))

        # Algorithm Hint Button (Emerald Green Pill matching reference mockup)
        hover_h = self.btn_hint.collidepoint(mouse_pos)
        h_bg = (24, 72, 48) if hover_h else (16, 44, 30)
        h_bc = (80, 255, 165) if hover_h else (50, 210, 130)
        GlassPanel.draw(surface, self.btn_hint, border_color=h_bc, bg_color=(*h_bg, 250), border_radius=19, glow=hover_h)
        t_h = self.font_btn.render("HINT [H]", True, (230, 255, 240) if hover_h else (190, 255, 215))
        surface.blit(t_h, t_h.get_rect(center=self.btn_hint.center))

        # Next World Button (Electric Blue/Cyan Pill matching reference mockup)
        hover_n = self.btn_next.collidepoint(mouse_pos)
        n_bg = (18, 135, 215) if hover_n else (10, 85, 150)
        n_bc = (120, 230, 255) if hover_n else (70, 195, 245)
        GlassPanel.draw(surface, self.btn_next, border_color=n_bc, bg_color=(*n_bg, 255), border_radius=19, glow=hover_n)
        t_n = self.font_btn.render("NEXT SECTOR  >", True, (255, 255, 255))
        surface.blit(t_n, t_n.get_rect(center=self.btn_next.center))

        # Star Info Button (Pill shape)
        info_hover = self.btn_sky_info.collidepoint(mouse_pos)
        info_bg = (25, 52, 85) if info_hover else (12, 24, 42)
        info_bc = (80, 190, 250) if info_hover else (45, 100, 165)
        GlassPanel.draw(surface, self.btn_sky_info, border_color=info_bc, bg_color=(*info_bg, 245), border_radius=19, glow=info_hover)
        info_text = self.font_btn.render("STAR INFO [I]", True, (240, 248, 255) if info_hover else (190, 220, 245))
        surface.blit(info_text, info_text.get_rect(center=self.btn_sky_info.center))

        # Worlds Selection Drawer
        self.drawer_progress = min(1.0, self.drawer_progress + 0.12) if self.show_worlds_drawer else max(0.0, self.drawer_progress - 0.16)
        if self.show_worlds_drawer:
            progress = self.drawer_progress
            drawer_rect = pygame.Rect(330, self.height - 265 + int((1 - progress) * 90), 432, 205)
            GlassPanel.draw(surface, drawer_rect, border_color=(60, 130, 230), bg_color=(12, 18, 38, 245), border_radius=8)
            world_names = [
                "01  Alpha Centauri  /  EASY",
                "02  Star Nursery  /  EASY",
                "03  Event Horizon  /  MEDIUM",
                "04  Seven Sisters  /  MEDIUM",
                "05  Great Spiral  /  HARD",
                "06  Lyra Relay  /  EASY",
                "07  Draco Nebula  /  EASY",
                "08  Carina Keel  /  MEDIUM",
                "09  Perseus Cluster  /  MEDIUM",
                "10  Sagittarius Core  /  HARD",
            ]
            for idx, r in enumerate(self.world_option_rects):
                base_y = self.height - 255 + (idx % 5) * 36
                entry_progress = max(0.0, min(1.0, progress * 1.7 - (idx % 5) * .09))
                y_offset = int((1 - entry_progress) * 22)
                r.y = base_y + int((1 - progress) * 90) + y_offset
                h = r.collidepoint(mouse_pos)
                selected = state.world_id == idx + 1
                col = (94, 195, 255) if h or selected else (180, 210, 245)
                lbl = self.font_body.render(world_names[idx], True, col)
                surface.blit(lbl, (r.x + 8, r.y + 8))
                if selected and entry_progress > .8:
                    pygame.draw.circle(surface, (91, 201, 255), (r.right - 12, r.centery), 3)
