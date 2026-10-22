with open("main.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add import
if "from visual.radial_menu import AstrolabeRadialMenu" not in code:
    code = code.replace("from visual.ui_hud import UIHud\n", "from visual.ui_hud import UIHud\nfrom visual.radial_menu import AstrolabeRadialMenu\n")
    code = code.replace("from visual.ui_hud import UIHud\r\n", "from visual.ui_hud import UIHud\r\nfrom visual.radial_menu import AstrolabeRadialMenu\r\n")

# 2. Add radial menu in __init__
old_init_buttons = '"hint": self.hud.btn_hint,\n        }'
new_init_buttons = '"hint": self.hud.btn_hint,\n            "radial": self.hud.btn_radial,\n        }\n        self.radial_menu = AstrolabeRadialMenu(cx=WIDTH // 2, cy=HEIGHT // 2)'

code = code.replace(old_init_buttons, new_init_buttons)
code = code.replace(old_init_buttons.replace("\n", "\r\n"), new_init_buttons.replace("\n", "\r\n"))

# 3. Add radial in activate_button
old_activate = 'elif name == "brief":'
new_activate = 'elif name == "radial":\n            self.radial_menu.toggle((WIDTH // 2, HEIGHT // 2))\n        elif name == "brief":'

code = code.replace(old_activate, new_activate)
code = code.replace(old_activate.replace("\n", "\r\n"), new_activate.replace("\n", "\r\n"))

# 4. Add update in update()
old_update = 'self.transition_timer = max(0.0, self.transition_timer - dt)'
new_update = 'self.transition_timer = max(0.0, self.transition_timer - dt)\n        self.radial_menu.update(dt)'

code = code.replace(old_update, new_update)
code = code.replace(old_update.replace("\n", "\r\n"), new_update.replace("\n", "\r\n"))

# 5. Add draw in draw()
old_draw = 'screen.blit(fade, (0, 0))\n\n    def _draw_intro_screen'
new_draw = 'screen.blit(fade, (0, 0))\n\n        # Astrolabe Radial Menu with animated transition\n        mouse_pos = pygame.mouse.get_pos()\n        self.radial_menu.draw(screen, mouse_pos)\n\n    def _draw_intro_screen'

code = code.replace(old_draw, new_draw)
code = code.replace(old_draw.replace("\n", "\r\n"), new_draw.replace("\n", "\r\n"))

# 6. Add event handling in run()
old_event_handling = 'for event in pygame.event.get():\n                if event.type == pygame.QUIT:'
new_event_handling = '''for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                # 1. Radial Menu Event Handler (Mouse click, hover selection, Hotkeys)
                if self.radial_menu.is_open or self.radial_menu.transition_t > 0.01:
                    rad_act = self.radial_menu.handle_event(event)
                    if rad_act:
                        if rad_act != "close":
                            self.activate_button(rad_act)
                        continue

                # 2. Right Click: toggle radial menu at cursor
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    if not self.show_intro and not self.sky_notes_open and not self.mission_brief_open:
                        self.radial_menu.toggle(event.pos)
                        continue

                # 3. Tab Key: toggle radial menu at screen center
                if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    if not self.show_intro and not self.sky_notes_open and not self.mission_brief_open:
                        self.activate_button("radial")
                        continue'''

code = code.replace(old_event_handling, new_event_handling)
code = code.replace(old_event_handling.replace("\n", "\r\n"), new_event_handling.replace("\n", "\r\n"))

with open("main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated main.py successfully")

