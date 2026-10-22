with open("visual/ui_hud.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace button definition in __init__
old_init_buttons = """        # Bottom Bar Navigation Buttons (matching reference image)
        self.btn_brief = pygame.Rect(18, height - 58, 240, 42)
        self.btn_worlds = pygame.Rect(276, height - 54, 96, 38)
        self.btn_algo = pygame.Rect(380, height - 54, 98, 38)
        self.btn_hint = pygame.Rect(486, height - 54, 104, 38)
        self.btn_next = pygame.Rect(598, height - 54, 126, 38)
        self.btn_sky_info = pygame.Rect(732, height - 54, 110, 38)"""

new_init_buttons = """        # Bottom Bar: The 1 Primary Radial Astrolabe Trigger Button
        self.btn_radial = pygame.Rect(self.width // 2 - 140, height - 54, 280, 40)
        self.btn_brief = pygame.Rect(18, height - 54, 230, 40)
        self.btn_worlds = pygame.Rect(self.width // 2 - 140, height - 54, 280, 40)
        self.btn_algo = pygame.Rect(self.width // 2 - 140, height - 54, 280, 40)
        self.btn_hint = pygame.Rect(self.width // 2 - 140, height - 54, 280, 40)
        self.btn_next = pygame.Rect(self.width - 160, height - 54, 142, 40)
        self.btn_sky_info = pygame.Rect(self.width // 2 - 140, height - 54, 280, 40)"""

content = content.replace(old_init_buttons.replace("\r\n", "\n"), new_init_buttons)
content = content.replace(old_init_buttons, new_init_buttons)

# Replace draw_bottom_dock
old_dock = """    def draw_bottom_dock(self, surface, state, is_maximized=False):
        \"\"\"Draws the bottom status capsule and action buttons.\"\"\"
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
        surface.blit(info_text, info_text.get_rect(center=self.btn_sky_info.center))"""

new_dock = """    def draw_bottom_dock(self, surface, state, is_maximized=False):
        \"\"\"Draws the bottom status bar and the 1 primary Astrolabe radial menu trigger.\"\"\"
        from theme import COLOR_BG, COLOR_PRIMARY, COLOR_ACCENT, COLOR_MUTED, COLOR_DIVIDER, font_button, font_caption, font_mono

        mouse_pos = pygame.mouse.get_pos()

        # 1. Left Sector Status Caption
        brief_hover = self.btn_brief.collidepoint(mouse_pos)
        pygame.draw.rect(surface, COLOR_BG, self.btn_brief)
        b_col = COLOR_ACCENT if brief_hover else COLOR_DIVIDER
        pygame.draw.rect(surface, b_col, self.btn_brief, 1)
        
        # Astrolabe mini-emblem
        bx, by = self.btn_brief.x + 20, self.btn_brief.centery
        pygame.draw.circle(surface, COLOR_ACCENT, (bx, by), 8, 1)
        pygame.draw.circle(surface, COLOR_PRIMARY, (bx, by), 2)
        pygame.draw.line(surface, COLOR_ACCENT, (bx - 11, by), (bx + 11, by), 1)
        pygame.draw.line(surface, COLOR_ACCENT, (bx, by - 11), (bx, by + 11), 1)

        b_title = state.name.split(' - ')[-1]
        t_surf = font_caption().render(f"Sector {state.world_id} · {b_title}", True, COLOR_PRIMARY if brief_hover else COLOR_MUTED)
        surface.blit(t_surf, (self.btn_brief.x + 36, self.btn_brief.centery - t_surf.get_height() // 2))

        # 2. THE 1 PRIMARY RADIAL ASTROLABE TRIGGER BUTTON
        rad_hover = self.btn_radial.collidepoint(mouse_pos)
        pygame.draw.rect(surface, COLOR_BG, self.btn_radial)
        
        gold_col = (245, 230, 165) if rad_hover else COLOR_ACCENT
        pygame.draw.rect(surface, gold_col, self.btn_radial, 2 if rad_hover else 1)
        inner_r = self.btn_radial.inflate(-6, -6)
        pygame.draw.rect(surface, gold_col, inner_r, 1)

        # Corner ticks
        for cx_c, cy_c, dx, dy in [
            (self.btn_radial.left + 3, self.btn_radial.top + 3, 1, 1),
            (self.btn_radial.right - 3, self.btn_radial.top + 3, -1, 1),
            (self.btn_radial.left + 3, self.btn_radial.bottom - 3, 1, -1),
            (self.btn_radial.right - 3, self.btn_radial.bottom - 3, -1, -1),
        ]:
            pygame.draw.line(surface, gold_col, (cx_c, cy_c), (cx_c + dx * 5, cy_c), 1)
            pygame.draw.line(surface, gold_col, (cx_c, cy_c), (cx_c, cy_c + dy * 5), 1)

        rad_text = font_button().render("✦  ASTROLABE MENU", True, (255, 252, 240) if rad_hover else COLOR_PRIMARY)
        tab_tag = font_mono(12).render("[TAB]", True, COLOR_ACCENT if rad_hover else COLOR_MUTED)
        
        tw = rad_text.get_width() + tab_tag.get_width() + 8
        tx = self.btn_radial.centerx - tw // 2
        surface.blit(rad_text, (tx, self.btn_radial.centery - rad_text.get_height() // 2))
        surface.blit(tab_tag, (tx + rad_text.get_width() + 8, self.btn_radial.centery - tab_tag.get_height() // 2 + 1))
        
        if rad_hover:
            pygame.draw.line(surface, COLOR_ACCENT, (tx, self.btn_radial.bottom - 7), (tx + tw, self.btn_radial.bottom - 7), 1)

        # 3. Right Next Sector Shortcut
        next_hover = self.btn_next.collidepoint(mouse_pos)
        pygame.draw.rect(surface, COLOR_BG, self.btn_next)
        n_col = (245, 230, 165) if next_hover else COLOR_ACCENT
        pygame.draw.rect(surface, n_col, self.btn_next, 1)
        next_surf = font_button().render("Next sector →", True, n_col)
        surface.blit(next_surf, next_surf.get_rect(center=self.btn_next.center))
        if next_hover:
            pygame.draw.line(surface, COLOR_ACCENT, (self.btn_next.centerx - next_surf.get_width() // 2, self.btn_next.bottom - 7), (self.btn_next.centerx + next_surf.get_width() // 2, self.btn_next.bottom - 7), 1)"""

content = content.replace(old_dock.replace("\r\n", "\n"), new_dock)
content = content.replace(old_dock, new_dock)

# Update drawer styling to Antique Star Atlas
old_drawer = """            GlassPanel.draw(surface, drawer_rect, border_color=(60, 130, 230), bg_color=(12, 18, 38, 245), border_radius=8)"""
new_drawer = """            from theme import COLOR_BG, COLOR_PRIMARY, COLOR_ACCENT, COLOR_MUTED
            pygame.draw.rect(surface, COLOR_BG, drawer_rect)
            pygame.draw.rect(surface, COLOR_ACCENT, drawer_rect, 1)
            pygame.draw.rect(surface, COLOR_ACCENT, drawer_rect.inflate(-6, -6), 1)"""

content = content.replace(old_drawer.replace("\r\n", "\n"), new_drawer)
content = content.replace(old_drawer, new_drawer)

old_col = """                col = (94, 195, 255) if h or selected else (180, 210, 245)"""
new_col = """                col = (245, 230, 165) if h or selected else (COLOR_PRIMARY if selected else COLOR_MUTED)"""

content = content.replace(old_col.replace("\r\n", "\n"), new_col)
content = content.replace(old_col, new_col)

with open("visual/ui_hud.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated visual/ui_hud.py successfully")

