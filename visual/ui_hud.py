import pygame

class GlassPanel:
    @staticmethod
    def draw(surface, rect, border_color=(39, 117, 170), bg_color=(5, 12, 27, 226), border_radius=10):
        x, y, w, h = rect
        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, bg_color, (0, 0, w, h), border_radius=border_radius)
        pygame.draw.rect(panel_surf, border_color, (0, 0, w, h), 1, border_radius=border_radius)
        pygame.draw.line(panel_surf, (91, 188, 235, 100), (border_radius, 1), (w - border_radius, 1), 1)
        surface.blit(panel_surf, (x, y))

class UIHud:
    def __init__(self, width=1100, height=720):
        self.width = width
        self.height = height

        self.font_logo = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI", 11)
        self.font_section = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 12)
        self.font_btn = pygame.font.SysFont("Segoe UI", 14, bold=True)

        # Top Right Quick Buttons
        self.btn_sound = pygame.Rect(824, 18, 47, 46)
        self.btn_music = pygame.Rect(875, 18, 47, 46)
        self.btn_undo = pygame.Rect(926, 18, 47, 46)
        self.btn_redo = pygame.Rect(977, 18, 47, 46)
        self.btn_settings = pygame.Rect(1028, 18, 48, 46)

        # Bottom Bar Navigation Buttons
        self.btn_worlds = pygame.Rect(340, height - 54, 105, 36)
        self.btn_algo = pygame.Rect(455, height - 54, 115, 36)
        self.btn_next = pygame.Rect(580, height - 54, 145, 36)
        self.btn_sky_info = pygame.Rect(740, height - 54, 112, 36)
        self.btn_maximize = pygame.Rect(864, height - 54, 145, 36)
        self.btn_brief = pygame.Rect(18, height - 82, 275, 66)

        # Worlds Selection Drawer
        self.show_worlds_drawer = False
        self.drawer_progress = 0.0
        self.world_option_rects = [
            pygame.Rect(343 + (index // 5) * 214, height - 255 + (index % 5) * 36, 204, 30)
            for index in range(10)
        ]

    def draw_top_bar(self, surface, state, is_muted, is_music_muted=False):
        # 1. StarLink Logo Capsule
        GlassPanel.draw(surface, (18, 16, 178, 52))
        cx, cy = 43, 42
        pulse = .5 + .5 * pygame.math.Vector2(1, 0).rotate(pygame.time.get_ticks() * .12).y
        pygame.draw.circle(surface, (20, 104, 173), (cx, cy), 19)
        pygame.draw.circle(surface, (50, 192, 248), (cx, cy), 14 + int(pulse * 2), 1)
        logo_points = [(cx - 10, cy + 4), (cx - 2, cy - 9), (cx + 10, cy - 3), (cx + 5, cy + 10)]
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
            pygame.draw.line(surface, (144, 229, 255), logo_points[a], logo_points[b], 1)
        for point in logo_points:
            pygame.draw.circle(surface, (233, 249, 255), point, 2)
        surface.blit(self.font_logo.render("StarLink", True, (239, 248, 255)), (68, 23))
        surface.blit(self.font_sub.render("CONSTELLATION PUZZLE", True, (117, 177, 211)), (70, 48))

        # 2. Sector Mission Capsule
        GlassPanel.draw(surface, (206, 16, 285, 52))
        world_title = state.name.split(" - ")[-1].upper()
        if len(world_title) > 24:
            world_title = world_title[:21] + "..."
        sector_caption = f"ACTIVE SECTOR  {state.world_id:02}  /  {state.difficulty}"
        surface.blit(self.font_sub.render(sector_caption, True, (112, 174, 207)), (220, 20))
        title = self.font_section.render(world_title, True, (228, 240, 251))
        surface.blit(title, (220, 39))

        # 3. Energy Bar Capsule
        GlassPanel.draw(surface, (500, 16, 164, 52))
        pygame.draw.polygon(surface, (99, 222, 255), [(520, 23), (511, 40), (518, 40), (514, 57), (529, 36), (522, 36)])
        e_text = f"ENERGY  {state.energy}/{state.max_energy}"
        surface.blit(self.font_section.render(e_text, True, (224, 242, 255)), (535, 20))
        
        # Energy Fill Gauge
        bar_x, bar_y, bar_w, bar_h = 535, 44, 113, 9
        pygame.draw.rect(surface, (14, 27, 43), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        pct = max(0.0, min(1.0, state.energy / state.max_energy if state.max_energy > 0 else 0))
        fill_color = (45, 202, 246) if pct > 0.3 else (255, 120, 103)
        if pct > 0:
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=4)

        # 4. Edges Selected Tracker
        GlassPanel.draw(surface, (674, 16, 148, 52))
        target_edges = max(1, len(state.stars) - 1)
        cur_edges = len(state.selected_edges)
        cur_cost = sum(c for _, _, c in state.selected_edges)
        surface.blit(self.font_sub.render(f"LINKS  {cur_edges} / {target_edges}", True, (165, 203, 230)), (688, 23))
        surface.blit(self.font_sub.render(f"LINK COST  {cur_cost}", True, (165, 203, 230)), (688, 45))

        # 5. Top Right Quick Buttons
        buttons = [
            (self.btn_sound, "SFX OFF" if is_muted else "SFX ON"),
            (self.btn_music, "MUS OFF" if is_music_muted else "MUS ON"),
            (self.btn_undo, "UNDO"),
            (self.btn_redo, "REDO"),
            (self.btn_settings, "RESET")
        ]
        for rect, label in buttons:
            GlassPanel.draw(surface, rect, border_color=(50, 95, 170), border_radius=6)
            txt = self.font_sub.render(label, True, (210, 230, 255))
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
            ("UNSTABLE: 3 moves", (255, 119, 112)),
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
            pygame.draw.circle(surface, (59, 123, 159) if is_picked else (34, 54, 75), (940, y+8), 9)
            n = self.font_sub.render(f"{idx+1:02}", True, (202, 228, 242))
            surface.blit(n, n.get_rect(center=(940, y+8)))
            surface.blit(self.font_body.render(f"{display_weight}", True, (89, 195, 235)), (957, y))
            line_str = self.fit_text(f"{u_name} - {v_name}", self.font_sub, 98)
            edge_label = self.font_sub.render(line_str, True, txt_color)
            surface.blit(edge_label, (974, y+1))
            y += 21

        pygame.draw.line(surface, (36, 67, 91), (932, y + 3), (1072, y + 3), 1)
        surface.blit(self.font_sub.render("RESTORED LINKS", True, (121, 204, 239)), (932, y + 10))

        sel_y = y + 32
        for u, v, w in state.selected_edges[:4]:
            u_name = state.stars[u].name
            v_name = state.stars[v].name
            link_label = self.fit_text(f"{w}  {u_name} - {v_name}", self.font_sub, 140)
            surface.blit(self.font_sub.render(link_label, True, (116, 224, 197)), (932, sel_y))
            sel_y += 17

    def draw_controls_panel(self, surface):
        """Draws the controls guide panel."""
        GlassPanel.draw(surface, (920, 434, 164, 178))
        surface.blit(self.font_section.render("FLIGHT CONTROLS", True, (121, 204, 239)), (932, 446))
        pygame.draw.line(surface, (36, 67, 91), (932, 470), (1072, 470), 1)

        controls = [
            ("CLICK TWO STARS", "Create a connection"),
            ("Z   /   Y", "Undo   /   redo"),
            ("K", "Animate Kruskal"),
            ("M   /   P", "Sound effects / music"),
            ("R", "Restart sector"),
        ]
        y = 472
        for key_text, desc in controls:
            surface.blit(self.font_body.render(key_text, True, (207, 227, 243)), (932, y))
            surface.blit(self.font_sub.render(desc, True, (132, 165, 191)), (932, y + 13))
            y += 26

    def draw_bottom_dock(self, surface, state, is_maximized=False):
        """Draws the bottom status capsule and action buttons."""
        brief_hover = self.btn_brief.collidepoint(pygame.mouse.get_pos())
        GlassPanel.draw(surface, self.btn_brief, border_color=(84, 173, 222) if brief_hover else (39, 117, 170))
        pygame.draw.circle(surface, (68, 87, 184), (48, self.height - 49), 20)
        pygame.draw.circle(surface, (183, 200, 255), (48, self.height - 49), 8, 1)
        pygame.draw.circle(surface, (224, 238, 255), (48, self.height - 49), 3)
        surface.blit(self.font_section.render("MISSION BRIEF", True, (148, 210, 239)), (78, self.height - 72))
        title = state.name if len(state.name) < 27 else state.name[:24] + "..."
        surface.blit(self.font_body.render(title, True, (224, 237, 250)), (78, self.height - 50))
        story = state.story.split(".")[0]
        if len(story) > 36:
            story = story[:33] + "..."
        surface.blit(self.font_sub.render(story, True, (135, 172, 197)), (78, self.height - 31))
        info_color = (166, 220, 247) if brief_hover else (105, 164, 197)
        info_mark = self.font_sub.render("OPEN  ›", True, info_color)
        surface.blit(info_mark, (self.btn_brief.right - 54, self.height - 71))

        mouse_pos = pygame.mouse.get_pos()

        # Worlds Button
        hover_w = self.btn_worlds.collidepoint(mouse_pos)
        w_bg = (27, 54, 78) if hover_w else (12, 25, 42)
        GlassPanel.draw(surface, self.btn_worlds, border_color=(48, 131, 174), bg_color=(*w_bg, 245), border_radius=12)
        t_w = self.font_btn.render("WORLDS", True, (197, 226, 245))
        surface.blit(t_w, t_w.get_rect(center=self.btn_worlds.center))

        # Algorithm Button
        hover_a = self.btn_algo.collidepoint(mouse_pos)
        a_bg = (27, 54, 78) if hover_a else (12, 25, 42)
        GlassPanel.draw(surface, self.btn_algo, border_color=(48, 131, 174), bg_color=(*a_bg, 245), border_radius=12)
        t_a = self.font_btn.render("ALGORITHM", True, (197, 226, 245))
        surface.blit(t_a, t_a.get_rect(center=self.btn_algo.center))

        # Next World Button
        hover_n = self.btn_next.collidepoint(mouse_pos)
        n_bg = (15, 132, 205) if hover_n else (10, 88, 151)
        GlassPanel.draw(surface, self.btn_next, border_color=(72, 194, 244), bg_color=(*n_bg, 250), border_radius=12)
        t_n = self.font_btn.render("NEXT SECTOR  >", True, (242, 251, 255))
        surface.blit(t_n, t_n.get_rect(center=self.btn_next.center))

        info_hover = self.btn_sky_info.collidepoint(mouse_pos)
        info_bg = (27, 54, 78) if info_hover else (12, 25, 42)
        GlassPanel.draw(surface, self.btn_sky_info, border_color=(75, 156, 197), bg_color=(*info_bg, 245), border_radius=12)
        info_text = self.font_btn.render("STAR INFO  I", True, (197, 226, 245))
        surface.blit(info_text, info_text.get_rect(center=self.btn_sky_info.center))

        maximize_hover = self.btn_maximize.collidepoint(mouse_pos)
        maximize_bg = (27, 54, 78) if maximize_hover else (12, 25, 42)
        GlassPanel.draw(surface, self.btn_maximize, border_color=(75, 156, 197), bg_color=(*maximize_bg, 245), border_radius=12)
        maximize_label = self.font_btn.render("RESTORE WINDOW" if is_maximized else "MAXIMIZE WINDOW", True, (197, 226, 245))
        surface.blit(maximize_label, maximize_label.get_rect(center=self.btn_maximize.center))

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
