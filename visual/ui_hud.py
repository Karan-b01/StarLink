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

        self.font_sub = pygame.font.SysFont("Segoe UI", 12)
        self.font_section = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 14)
        self.font_btn = pygame.font.SysFont("Segoe UI", 15, bold=True)

        # Top Right Quick Buttons (matching reference image)
        self.btn_undo = pygame.Rect(752, 18, 54, 38)
        self.btn_redo = pygame.Rect(812, 18, 54, 38)
        self.btn_settings = pygame.Rect(872, 18, 60, 38)   # RESET
        self.btn_maximize = pygame.Rect(938, 18, 44, 38)

        # Bottom Bar Navigation Buttons (matching reference image)
        self.btn_worlds = pygame.Rect(259, height - 54, 96, 38)
        self.btn_algo = pygame.Rect(367, height - 54, 98, 38)
        self.btn_hint = pygame.Rect(477, height - 54, 104, 38)
        self.btn_next = pygame.Rect(593, height - 54, 126, 38)
        self.btn_sky_info = pygame.Rect(731, height - 54, 110, 38)

        # Worlds Selection Drawer
        self.show_worlds_drawer = False
        self.drawer_progress = 0.0
        self.world_option_rects = [
            pygame.Rect(343 + (index // 7) * 214, height - 320 + (index % 7) * 34, 204, 30)
            for index in range(13)
        ]

    def draw_top_bar(self, surface, state, display_energy=None):
        # Start the sector and energy panels at the left edge after removing the logo capsule.
        GlassPanel.draw(surface, (18, 16, 260, 52), border_color=(45, 110, 180), border_radius=14)
        world_title = state.name.split(" - ")[-1].upper()
        if len(world_title) > 22:
            world_title = world_title[:19] + "..."
        sector_caption = f"ACTIVE SECTOR  (SECTOR {state.world_id:02} / {state.difficulty})"
        surface.blit(self.font_sub.render(sector_caption, True, (120, 180, 220)), (34, 20))
        # Glowing yellow/amber status orb matching reference
        pygame.draw.circle(surface, (255, 200, 80), (41, 47), 5)
        pygame.draw.circle(surface, (255, 240, 180), (41, 47), 2)
        surface.blit(self.font_section.render(world_title, True, (235, 245, 255)), (53, 37))

        # Energy bar uses the open space left by the removed logo.
        GlassPanel.draw(surface, (290, 16, 442, 52), border_color=(45, 120, 200), border_radius=14)
        # Cyan Lightning Bolt
        pygame.draw.polygon(surface, (60, 215, 255), [(308, 23), (300, 39), (307, 39), (303, 55), (317, 35), (310, 35)])
        disp_e = state.energy if display_energy is None else display_energy
        e_text = f"ENERGY  {int(disp_e)} / {state.max_energy}"
        surface.blit(self.font_section.render(e_text, True, (230, 245, 255)), (324, 20))
        move_text = self.font_sub.render(f"MOVES  {state.moves_made}", True, (165, 195, 218))
        surface.blit(move_text, (620, 22))

        # Energy Glowing Gradient Bar (Cyan -> Purple with leading spark)
        bar_x, bar_y, bar_w, bar_h = 324, 43, 390, 12
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
            (self.btn_maximize, "FULL", False),
        ]
        for rect, label, active in buttons:
            hover = rect.collidepoint(mouse_pos)
            bg = (24, 48, 80) if hover else (12, 22, 38)
            border = (80, 185, 245) if hover else (45, 95, 160)
            GlassPanel.draw(surface, rect, border_color=border, bg_color=(*bg, 235), border_radius=10, glow=hover)
            txt = self.font_sub.render(label, True, (240, 248, 255) if hover else (190, 220, 245))
            surface.blit(txt, txt.get_rect(center=rect.center))

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
    def _star_color(name):
        named = {
            "Sol": (255, 190, 77), "Sirius": (89, 195, 255),
            "Vega": (207, 229, 255), "Rigel": (157, 119, 255),
            "Betelgeuse": (255, 111, 85),
        }
        return named.get(name, (173, 206, 246))

    def draw_kruskal_inspector(self, surface, state):
        """Show corridors in Kruskal's increasing-cost order."""
        panel_rect = (920, 92, 164, 332)
        GlassPanel.draw(surface, panel_rect, border_color=(45, 95, 175))

        title = "TIMED PLAN" if state.has_timed_edges else "KRUSKAL"
        subtitle = "SAFE MOVE ORDER" if state.has_timed_edges else "EDGES / LOWEST WEIGHT"
        surface.blit(self.font_section.render(title, True, (121, 204, 239)), (932, 104))
        surface.blit(self.font_sub.render(subtitle, True, (115, 153, 183)), (932, 125))
        streak = self.font_sub.render(f"RESONANCE  x{state.resonance_streak}", True,
                                      (94, 232, 208) if state.resonance_streak else (115, 153, 183))
        surface.blit(streak, (932, 142))
        pygame.draw.line(surface, (36, 67, 91), (932, 158), (1072, 158), 1)

        if state.has_timed_edges:
            plan = state.get_current_plan() or state.optimal_plan
            sorted_edges = [state.edges[index] for index in plan]
        else:
            sorted_edges = sorted(state.edges, key=lambda edge: edge[2])
        y = 163
        for idx, (u, v, w) in enumerate(sorted_edges[:6]):
            u_name = state.stars[u].name
            v_name = state.stars[v].name
            display_weight = w

            pair = (min(u, v), max(u, v))
            is_picked = any(e[0] == pair[0] and e[1] == pair[1] for e in state.selected_edges)
            edge_idx = state.edge_index.get(pair)
            deadline = state.edge_rules.get(edge_idx) if edge_idx is not None else None
            is_unstable = (deadline is not None) and not is_picked
            moves_left = max(0, deadline - state.turns_elapsed) if deadline is not None else 0

            if is_picked:
                txt_color = (94, 232, 208)
            elif is_unstable and moves_left <= 1:
                txt_color = (255, 115, 95)
            elif is_unstable:
                txt_color = (255, 205, 110)
            else:
                txt_color = (177, 199, 220)

            # Numbered pill badge
            pygame.draw.circle(surface, (59, 123, 159) if is_picked else (26, 42, 64), (940, y + 8), 9)
            n = self.font_sub.render(f"{idx+1:02}", True, (220, 240, 255) if is_picked else (140, 180, 210))
            surface.blit(n, n.get_rect(center=(940, y + 8)))

            # Weight & Edge Name
            surface.blit(self.font_body.render(f"{display_weight}", True, (89, 195, 235)), (955, y))
            display_str = f"{u_name}-{v_name}"
            if is_unstable:
                display_str += f" [{moves_left}m]"
            line_str = self.fit_text(display_str, self.font_sub, 92)
            edge_label = self.font_sub.render(line_str, True, txt_color)
            surface.blit(edge_label, (972, y + 1))

            # Vertical indicator status tag on right edge
            if is_picked:
                tag_color = (70, 235, 150)
            elif is_unstable and moves_left <= 1:
                tag_color = (255, 80, 70)
            elif is_unstable:
                tag_color = (245, 180, 60)
            else:
                tag_color = (40, 70, 95)
            pygame.draw.rect(surface, tag_color, (1072, y + 2, 4, 15), border_radius=2)

            y += 21

        pygame.draw.line(surface, (36, 67, 91), (932, y + 3), (1072, y + 3), 1)
        surface.blit(self.font_sub.render("RESTORED LINKS", True, (121, 204, 239)), (932, y + 10))

        sel_y = y + 30
        visible_links = state.selected_edges[-3:]
        if len(state.selected_edges) > len(visible_links):
            more = self.font_sub.render(f"+{len(state.selected_edges) - len(visible_links)} earlier", True, (115, 153, 183))
            surface.blit(more, (932, sel_y))
            sel_y += 16
        for u, v, w in visible_links:
            u_name = state.stars[u].name
            v_name = state.stars[v].name
            link_label = self.fit_text(f"{w}  {u_name} - {v_name}", self.font_sub, 140)
            surface.blit(self.font_sub.render(link_label, True, (116, 224, 197)), (932, sel_y))
            sel_y += 17

    def draw_bottom_dock(self, surface, state, is_maximized=False):
        """Draws the centered bottom action buttons."""
        mouse_pos = pygame.mouse.get_pos()
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
            drawer_rect = pygame.Rect(330, self.height - 330 + int((1 - progress) * 90), 432, 270)
            GlassPanel.draw(surface, drawer_rect, border_color=(60, 130, 230), bg_color=(12, 18, 38, 245), border_radius=8)
            world_names = [
                "01  Big Dipper  /  EASY",
                "02  Orion  /  EASY",
                "03  Cygnus  /  MEDIUM",
                "04  Pleiades  /  MEDIUM",
                "05  Andromeda  /  HARD",
                "06  Summer Triangle  /  EASY",
                "07  Draco  /  EASY",
                "08  Carina  /  MEDIUM",
                "09  Perseus  /  MEDIUM",
                "10  Sagittarius  /  HARD",
                "11  Orion's Frame  /  MEDIUM",
                "12  Seven Sisters  /  HARD",
                "13  Northern Cross  /  HARD",
            ]
            for idx, r in enumerate(self.world_option_rects):
                row = idx % 7
                base_y = self.height - 320 + row * 34
                entry_progress = max(0.0, min(1.0, progress * 1.7 - row * .06))
                y_offset = int((1 - entry_progress) * 22)
                r.y = base_y + int((1 - progress) * 90) + y_offset
                h = r.collidepoint(mouse_pos)
                selected = state.world_id == idx + 1
                col = (94, 195, 255) if h or selected else (180, 210, 245)
                lbl = self.font_body.render(world_names[idx], True, col)
                surface.blit(lbl, (r.x + 8, r.y + 8))
                if selected and entry_progress > .8:
                    pygame.draw.circle(surface, (91, 201, 255), (r.right - 12, r.centery), 3)
