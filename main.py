import math
import sys
import ctypes

import pygame

from dsa.mst import kruskal_steps
from engine.game_state import GameState
from engine.level_loader import load_level_from_json
from engine.sound_engine import SoundEngine
from visual.celestial_renderer import CelestialRenderer
from visual.starfield import ParallaxStarfield
from visual.ui_hud import UIHud

pygame.init()
WIDTH, HEIGHT = 1100, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
pygame.display.set_caption("StarLink | Constellation Weaver")
logo = pygame.Surface((64, 64), pygame.SRCALPHA)
pygame.draw.circle(logo, (15, 65, 112), (32, 32), 29)
pygame.draw.circle(logo, (55, 190, 245), (32, 32), 25, 2)
for a, b in [((17, 38), (30, 20)), ((30, 20), (47, 30)), ((17, 38), (37, 46)), ((37, 46), (47, 30))]:
    pygame.draw.line(logo, (114, 220, 255), a, b, 2)
for x, y in [(17, 38), (30, 20), (47, 30), (37, 46)]:
    pygame.draw.circle(logo, (238, 250, 255), (x, y), 3)
pygame.display.set_icon(logo)
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Segoe UI", 15)
SMALL = pygame.font.SysFont("Segoe UI", 12)
MEDIUM = pygame.font.SysFont("Segoe UI", 17, bold=True)
TITLE = pygame.font.SysFont("Segoe UI", 23, bold=True)
FONT_HERO = pygame.font.SysFont("Segoe UI", 46, bold=True)

REAL_SKY_NOTES = {
    1: "The named stars are real, but they belong to different constellations and are not a Solar System pattern. Sirius is in Canis Major; Vega is in Lyra.",
    2: "Alnitak, Alnilam and Mintaka form Orion's Belt. Mintaka is a multiple-star system; the Orion Nebula lies in the Sword below the Belt.",
    3: "Cygnus X-1 is a real X-ray binary in Cygnus. Its X-rays come from hot material falling toward a compact object identified as a black-hole candidate.",
    4: "The Pleiades (M45) is a real open cluster in Taurus, with over a thousand stars. Its brightest members formed together; it is a cluster, not a constellation.",
    5: "M31 is the Andromeda Galaxy, a separate galaxy visible in the direction of the Andromeda constellation. It is not a star in the constellation's pattern.",
    6: "Vega, Deneb and Altair make the Summer Triangle asterism, spanning Lyra, Cygnus and Aquila. It is a useful seasonal sky landmark, not an official constellation.",
    7: "Draco is a winding northern-sky constellation. Its star Thuban was close to the north celestial pole thousands of years ago; Earth's axial precession changes the pole star.",
    8: "Carina is a southern-sky constellation. Canopus, in Carina, is the night sky's second-brightest star as seen from Earth; apparent brightness depends on distance as well as luminosity.",
    9: "Algol is an eclipsing multiple-star system in Perseus. Its changing brightness is a clue: repeated light measurements reveal the orbiting stars passing in front of one another.",
    10: "Sagittarius points toward the Milky Way's crowded central direction. The bright Milky Way band there contains dust clouds that hide much of the Galactic Centre in visible light.",
}

MISSION_QUOTES = {
    5: "A precise map turns distant light into a route through the unknown.",
    4: "Every great discovery begins with a signal worth measuring.",
    3: "The stars reward patient observers and careful instruments.",
    2: "Curiosity is the first instrument; evidence is the navigation system.",
    1: "Spaceflight advances one lesson at a time: study the data, improve the design, try again.",
    0: "A missed connection is useful data. Refine the plan, then launch again.",
}


def glass_panel(surface, rect, fill=(8, 16, 36, 220), border=(55, 106, 174), radius=12):
    panel = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (*border, 210), panel.get_rect(), 1, border_radius=radius)
    pygame.draw.line(panel, (100, 175, 255, 65), (radius, 1), (rect[2] - radius, 1))
    surface.blit(panel, rect[:2])


class GameApp:
    def __init__(self):
        self.starfield = ParallaxStarfield(WIDTH, HEIGHT)
        self.hud = UIHud(WIDTH, HEIGHT)
        self.sound = SoundEngine(enabled=True)
        self.world_files = [
            f"levels/world{i}.json"
            for i in range(1, 11)
        ]
        self.world_idx = 0
        self.buttons = {
            "sound": self.hud.btn_sound,
            "music": self.hud.btn_music,
            "undo": self.hud.btn_undo,
            "redo": self.hud.btn_redo,
            "reset": self.hud.btn_settings,
            "worlds": self.hud.btn_worlds,
            "solver": self.hud.btn_algo,
            "next": self.hud.btn_next,
            "sky_info": self.hud.btn_sky_info,
            "maximize": self.hud.btn_maximize,
            "brief": self.hud.btn_brief,
        }
        self.result_buttons = {
            "retry": pygame.Rect(WIDTH // 2 - 178, 438, 160, 48),
            "next": pygame.Rect(WIDTH // 2 + 18, 438, 160, 48),
        }
        self.show_intro = True
        self.toast_message = None
        self.toast_timer = 0.0
        self.play_button = pygame.Rect(WIDTH // 2 - 112, 520, 224, 56)
        self.intro_sfx_button = pygame.Rect(WIDTH // 2 - 174, 612, 160, 36)
        self.intro_music_button = pygame.Rect(WIDTH // 2 + 14, 612, 160, 36)
        self.intro_maximize_button = pygame.Rect(WIDTH // 2 + 202, 612, 160, 36)
        self.window_maximized = False
        self.sky_notes_open = False
        self.mission_brief_open = False
        self.sky_notes_button = pygame.Rect(WIDTH // 2 - 190, 470, 150, 38)
        self.result_brief_button = pygame.Rect(WIDTH // 2 + 40, 470, 150, 38)
        self.result_started_at = 0.0
        self.transition_timer = 0.0
        self.load_world(self.world_idx)

    def load_world(self, idx):
        self.world_idx = idx % len(self.world_files)
        self.state = GameState(load_level_from_json(self.world_files[self.world_idx]))
        self.selected_star = None
        self.flash_cycle = None
        self.flash_timer = 0.0
        self.win_sound_played = False
        self.stepper_gen = None
        self.stepper_timer = 0.0
        self.stepper_edges = []
        self.stepper_active = False
        self.result_started_at = 0.0
        self.sky_notes_open = False
        self.mission_brief_open = False
        self.transition_timer = 0.42

    def handle_star_click(self, star_id):
        if self.selected_star is None:
            self.selected_star = star_id
            self.state.status_message = f"Star {self.state.stars[star_id].name} selected — choose a connected star."
            return
        if self.selected_star != star_id:
            ok, _ = self.state.connect_edge(self.selected_star, star_id)
            if not ok and self.state.cycle_edge_flash:
                self.flash_cycle = self.state.cycle_edge_flash
                self.flash_timer = 0.7
                self.sound.play("cycle")
            elif ok:
                self.sound.play("link")
        self.selected_star = None

    def trigger_kruskal_stepper(self):
        effective_edges = [
            (u, v, self.state.compute_edge_cost(u, v, weight))
            for u, v, weight in self.state.edges
        ]
        self.stepper_gen = kruskal_steps(list(self.state.stars.keys()), effective_edges)
        self.stepper_edges = []
        self.stepper_active = True
        self.stepper_timer = 0.0
        self.toast_message = "Kruskal preview: gold = accepted, red dashed × = cycle rejected. Your links are unchanged."
        self.toast_timer = 4.5

    @staticmethod
    def draw_dashed_line(surface, color, start, end, width=2, dash_length=8, gap_length=6):
        dx, dy = end[0] - start[0], end[1] - start[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
        ux, uy = dx / distance, dy / distance
        offset = 0
        while offset < distance:
            finish = min(offset + dash_length, distance)
            p1 = (round(start[0] + ux * offset), round(start[1] + uy * offset))
            p2 = (round(start[0] + ux * finish), round(start[1] + uy * finish))
            pygame.draw.line(surface, color, p1, p2, width)
            offset = finish + gap_length

    def activate_button(self, name):
        if name == "sound":
            self.sound.enabled = not self.sound.enabled
        elif name == "music":
            self.sound.set_music(not self.sound.music_enabled)
        elif name == "undo":
            self.state.undo()
            self.sound.play("undo")
        elif name == "redo":
            self.state.redo()
            self.sound.play("undo")
        elif name == "reset":
            self.load_world(self.world_idx)
        elif name == "solver":
            self.trigger_kruskal_stepper()
        elif name == "next":
            self.load_world(self.world_idx + 1)
        elif name == "worlds":
            self.hud.show_worlds_drawer = not self.hud.show_worlds_drawer
        elif name == "sky_info":
            self.sky_notes_open = not self.sky_notes_open
            if self.sky_notes_open:
                self.mission_brief_open = False
        elif name == "maximize":
            self.toggle_maximize_window()
        elif name == "brief":
            self.mission_brief_open = not self.mission_brief_open
            if self.mission_brief_open:
                self.sky_notes_open = False

    def toggle_maximize_window(self):
        try:
            if sys.platform == "win32":
                hwnd = pygame.display.get_wm_info().get("window")
                if not hwnd:
                    raise RuntimeError("Windows did not provide a game window handle.")
                command = 9 if self.window_maximized else 3  # SW_RESTORE / SW_MAXIMIZE
                show_window = ctypes.windll.user32.ShowWindow
                show_window.argtypes = (ctypes.c_void_p, ctypes.c_int)
                show_window.restype = ctypes.c_bool
                show_window(ctypes.c_void_p(hwnd), command)
            else:
                from pygame._sdl2.video import Window
                window = Window.from_display_module()
                if self.window_maximized:
                    window.restore()
                else:
                    window.maximize()
            self.window_maximized = not self.window_maximized
        except (ImportError, OSError, AttributeError, TypeError, pygame.error, RuntimeError) as exc:
            self.toast_message = f"Window maximize unavailable: {exc}"
            self.toast_timer = 4.0

    def update(self, dt):
        self.transition_timer = max(0.0, self.transition_timer - dt)
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - dt)
            if self.toast_timer == 0:
                self.toast_message = None
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_cycle = None
        if (self.state.is_completed or self.state.is_failed) and not self.result_started_at:
            self.result_started_at = self.starfield.elapsed
        if self.state.is_completed and not self.win_sound_played:
            self.sound.play("win")
            self.win_sound_played = True
        if not self.state.is_completed and not self.state.is_failed:
            self.state.check_failure()
        if self.state.notification_message:
            self.toast_message = self.state.notification_message
            self.toast_timer = 3.2
            self.state.notification_message = None
        if self.stepper_active and self.stepper_gen:
            self.stepper_timer += dt
            if self.stepper_timer >= 0.52:
                self.stepper_timer = 0.0
                try:
                    step = next(self.stepper_gen)
                    self.stepper_edges.append(step)
                    self.sound.play("link" if step[3] else "cycle")
                except StopIteration:
                    self.stepper_active = False
                    self.stepper_gen = None

    def draw_action_button(self, rect, label, accent=False):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if accent:
            fill = (22, 110, 194, 245) if not hover else (38, 145, 225, 255)
            border = (92, 195, 255)
        else:
            fill = (20, 35, 65, 235) if not hover else (35, 62, 103, 250)
            border = (69, 119, 183)
        glass_panel(screen, rect, fill, border, 9)
        text = SMALL.render(label, True, (235, 245, 255))
        screen.blit(text, text.get_rect(center=rect.center))

    def draw(self, dt):
        self.starfield.update_and_draw(screen, dt)
        now = self.starfield.elapsed

        if self.show_intro:
            self._draw_intro_screen(now)
            return

        # Thin constellation guide lines and active energy corridors.
        for u, v, base_cost in self.state.edges:
            a, b = self.state.stars[u], self.state.stars[v]
            p1, p2 = (int(a.x), int(a.y)), (int(b.x), int(b.y))
            selected = any(e[0] == min(u, v) and e[1] == max(u, v) for e in self.state.selected_edges)
            cycle = self.flash_cycle == (min(u, v), max(u, v)) if self.flash_cycle else False
            cost = self.state.compute_edge_cost(u, v, base_cost)
            if cycle:
                pygame.draw.line(screen, (255, 65, 95), p1, p2, 5)
                pygame.draw.line(screen, (255, 210, 220), p1, p2, 1)
            elif selected:
                remaining = self.state.decay_counters.get((min(u, v), max(u, v)))
                warning = remaining == 1
                if warning:
                    flash = (math.sin(now * 12) + 1) * .5
                    core = (255, int(105 + flash * 110), 104)
                    pygame.draw.line(screen, (112, 30, 53), p1, p2, 8)
                    pygame.draw.line(screen, core, p1, p2, 4)
                else:
                    pygame.draw.line(screen, (13, 74, 150), p1, p2, 8)
                    pygame.draw.line(screen, (45, 174, 245), p1, p2, 4)
                    shimmer = (math.sin(now * 4 + u + v) + 1) * .5
                    pygame.draw.line(screen, (int(130 + shimmer * 100), 245, 255), p1, p2, 1)
                # A traveling pulse makes restored connections feel powered.
                travel = (now * .42 + (u + v) * .173) % 1.0
                spark = (int(p1[0] + (p2[0] - p1[0]) * travel),
                         int(p1[1] + (p2[1] - p1[1]) * travel))
                pygame.draw.circle(screen, (25, 110, 190), spark, 7)
                pygame.draw.circle(screen, (210, 250, 255), spark, 2)
            else:
                pygame.draw.line(screen, (39, 77, 116), p1, p2, 1)
            mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            pygame.draw.circle(screen, (7, 15, 34), mid, 12)
            pygame.draw.circle(screen, (53, 90, 145), mid, 12, 1)
            label = SMALL.render(str(cost), True, (179, 213, 247) if not selected else (220, 250, 255))
            screen.blit(label, label.get_rect(center=mid))

        for step in self.stepper_edges:
            u, v, _, accepted, _ = step
            a, b = self.state.stars[u], self.state.stars[v]
            p1, p2 = (int(a.x), int(a.y)), (int(b.x), int(b.y))
            mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            if accepted:
                pygame.draw.line(screen, (255, 206, 85), p1, p2, 3)
            else:
                # A dashed red corridor with an X means Kruskal inspected it
                # and rejected it; it is never part of the resulting MST.
                self.draw_dashed_line(screen, (255, 83, 105), p1, p2, 3)
                pygame.draw.circle(screen, (18, 12, 29), mid, 10)
                pygame.draw.circle(screen, (255, 100, 120), mid, 9, 1)
                pygame.draw.line(screen, (255, 135, 150), (mid[0] - 4, mid[1] - 4), (mid[0] + 4, mid[1] + 4), 2)
                pygame.draw.line(screen, (255, 135, 150), (mid[0] + 4, mid[1] - 4), (mid[0] - 4, mid[1] + 4), 2)

        for star in self.state.star_list:
            CelestialRenderer.draw_star(screen, star, self.selected_star == star.id, now, FONT)

        # Overlay panels follow the compact constellation-dashboard layout.
        self.hud.draw_top_bar(screen, self.state, not self.sound.enabled, not self.sound.music_enabled)
        self.hud.draw_left_stars_panel(screen, self.state.star_list)
        self.hud.draw_kruskal_inspector(screen, self.state)
        self.hud.draw_controls_panel(screen)
        self.hud.draw_bottom_dock(screen, self.state, self.window_maximized)

        if self.toast_message and self.toast_timer > 0:
            toast_w = min(620, max(330, FONT.size(self.toast_message)[0] + 48))
            toast_rect = pygame.Rect((WIDTH - toast_w) // 2, HEIGHT - 112, toast_w, 42)
            warning = "Warning:" in self.toast_message or "collapsed" in self.toast_message
            accent = (255, 133, 116) if warning else (255, 196, 91)
            glass_panel(screen, toast_rect, (12, 20, 39, 242), accent, 10)
            pygame.draw.circle(screen, accent, (toast_rect.x + 18, toast_rect.centery), 4)
            toast_text = SMALL.render(self.toast_message, True, (232, 241, 250))
            screen.blit(toast_text, toast_text.get_rect(midleft=(toast_rect.x + 31, toast_rect.centery)))

        if self.state.is_completed or self.state.is_failed:
            self._draw_result_modal()
        if self.sky_notes_open:
            self._draw_sky_notes()
        if self.mission_brief_open:
            self._draw_mission_brief()
        if self.transition_timer > 0:
            fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fade.fill((2, 8, 24, int(150 * self.transition_timer / .42)))
            screen.blit(fade, (0, 0))

    def _draw_intro_screen(self, now):
        # Keep the galaxy moving behind the briefing, but hold back the puzzle nodes.
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((2, 7, 19, 112))
        screen.blit(veil, (0, 0))

        eyebrow = SMALL.render("CONSTELLATION PUZZLE", True, (99, 194, 229))
        screen.blit(eyebrow, eyebrow.get_rect(center=(WIDTH // 2, 74)))
        pygame.draw.circle(screen, (37, 137, 205), (WIDTH // 2, 111), 22, 1)
        logo_nodes = [(WIDTH // 2 - 13, 115), (WIDTH // 2 - 2, 101), (WIDTH // 2 + 14, 109), (WIDTH // 2 + 7, 124)]
        for i, j in [(0, 1), (1, 2), (2, 3), (0, 3)]:
            pygame.draw.line(screen, (108, 212, 255), logo_nodes[i], logo_nodes[j], 2)
        for point in logo_nodes:
            pygame.draw.circle(screen, (236, 249, 255), point, 3)
        title = FONT_HERO.render("STARLINK", True, (237, 248, 255))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 151)))
        subtitle = FONT.render("Reconnect the stars using the least possible energy.", True, (166, 198, 222))
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 190)))

        cards = [
            (95, "01", "CONNECT THE STARS", "Click two stars joined by a corridor to create a link.", (78, 198, 247)),
            (405, "02", "AVOID CYCLES", "Build one connected network. A cycle is rejected by Union-Find.", (158, 143, 255)),
            (715, "03", "SAVE YOUR ENERGY", "Choose low-cost links. Your final network is scored out of five stars.", (87, 226, 190)),
        ]
        for x, number, heading, copy, accent in cards:
            rect = pygame.Rect(x, 226, 290, 205)
            glass_panel(screen, rect, (5, 15, 34, 224), accent)
            pygame.draw.circle(screen, tuple(channel // 4 for channel in accent), (x + 34, 267), 20)
            number_text = MEDIUM.render(number, True, accent)
            screen.blit(number_text, number_text.get_rect(center=(x + 34, 267)))
            head = SMALL.render(heading, True, (218, 237, 250))
            screen.blit(head, (x + 20, 306))
            words = copy.split()
            lines = []
            line = ""
            for word in words:
                attempt = f"{line} {word}".strip()
                if FONT.size(attempt)[0] > 247 and line:
                    lines.append(line)
                    line = word
                else:
                    line = attempt
            if line:
                lines.append(line)
            for i, line in enumerate(lines[:3]):
                surface_text = FONT.render(line, True, (150, 183, 209))
                screen.blit(surface_text, (x + 20, 337 + i * 23))

        special = "POWER: half link cost     ENERGY: +5 reserve     UNSTABLE: link collapses after 3 moves"
        special_text = SMALL.render(special, True, (141, 177, 205))
        screen.blit(special_text, special_text.get_rect(center=(WIDTH // 2, 472)))
        self.draw_action_button(self.intro_sfx_button, "SFX  ON" if self.sound.enabled else "SFX  OFF", self.sound.enabled)
        self.draw_action_button(self.intro_music_button, "MUSIC  ON" if self.sound.music_enabled else "MUSIC  OFF", self.sound.music_enabled)
        self.draw_action_button(self.intro_maximize_button,
                                "RESTORE WINDOW" if self.window_maximized else "MAXIMIZE WINDOW",
                                self.window_maximized)
        controls = "Z  Undo     Y  Redo     K  Kruskal solver     M  SFX     P  Music     R  Restart"
        controls_text = SMALL.render(controls, True, (105, 145, 178))
        screen.blit(controls_text, controls_text.get_rect(center=(WIDTH // 2, 675)))

        hover = self.play_button.collidepoint(pygame.mouse.get_pos())
        pulse = (math.sin(now * 3) + 1) * .5
        fill = (18, 135, 206, 252) if hover else (10, 93 + int(pulse * 17), 157, 245)
        glass_panel(screen, self.play_button, fill, (79, 203, 255), 14)
        play = MEDIUM.render("PLAY", True, (246, 252, 255))
        screen.blit(play, play.get_rect(center=(self.play_button.centerx, self.play_button.centery - 2)))
        hint = SMALL.render("Press ENTER to begin", True, (173, 215, 239))
        screen.blit(hint, hint.get_rect(center=(self.play_button.centerx, self.play_button.bottom + 17)))

    @staticmethod
    def _star_points(cx, cy, outer, inner):
        points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            radius = outer if i % 2 == 0 else inner
            points.append((int(cx + math.cos(angle) * radius), int(cy + math.sin(angle) * radius)))
        return points

    def _draw_result_modal(self):
        success = self.state.is_completed
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((1, 4, 15, 205))
        screen.blit(overlay, (0, 0))
        box = pygame.Rect(WIDTH // 2 - 290, 138, 580, 470)
        border = (77, 190, 230) if success else (194, 91, 116)
        glass_panel(screen, box, (5, 15, 35, 252), border, 20)
        eyebrow = SMALL.render("SECTOR REPORT", True, (110, 177, 208))
        screen.blit(eyebrow, eyebrow.get_rect(center=(WIDTH // 2, 218)))
        final_sector = self.world_idx == len(self.world_files) - 1
        title_text = ("CAMPAIGN COMPLETE" if final_sector else "CONSTELLATION RESTORED") if success else "SIGNAL LOST"
        title_color = (231, 248, 255) if success else (255, 190, 190)
        title = TITLE.render(title_text, True, title_color)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 255)))

        now = self.starfield.elapsed
        spacing = 48
        first_x = WIDTH // 2 - spacing * 2
        for i in range(5):
            earned = success and i < self.state.earned_stars
            reveal = min(1.0, max(0.0, (now - self.result_started_at - i * .22) / .32)) if success else 0.0
            bob = math.sin(now * 3 + i * .65) * 2 if earned else 0
            cx, cy = first_x + i * spacing, int(310 + bob)
            if earned:
                glow = pygame.Surface((46, 46), pygame.SRCALPHA)
                glow_alpha = int((15 + (math.sin(now * 3 + i) + 1) * 8) * reveal)
                pygame.draw.circle(glow, (255, 187, 63, glow_alpha), (23, 23), 21)
                screen.blit(glow, (cx - 23, cy - 23))
            radius = (17 if earned else 15) * (0.3 + reveal * .7) if success else 15
            points = self._star_points(cx, cy, radius, radius * .42)
            fill = (255, 202, 91) if earned else (24, 39, 61)
            outline = (255, 229, 157) if earned else (62, 89, 119)
            pygame.draw.polygon(screen, fill, points)
            pygame.draw.polygon(screen, outline, points, 2)

        cost = sum(c for _, _, c in self.state.selected_edges)
        if success:
            detail = FONT.render(f"Network cost  {cost}     |     Optimal network  {self.state.optimal_cost}", True, (177, 207, 230))
            rating = f"EFFICIENCY RATING  {self.state.earned_stars} / 5"
            if self.state.earned_stars >= 4:
                hint_text = "Excellent energy planning. Your route is close to the optimum."
                hint_color = (115, 222, 199)
            elif self.state.earned_stars >= 2:
                hint_text = "Network restored. Review the energy costs to improve your score."
                hint_color = (255, 205, 129)
            else:
                hint_text = "Network restored, with high energy use. Retry to aim for more stars."
                hint_color = (255, 172, 142)
        else:
            detail = FONT.render(f"Energy remaining  {self.state.energy}     |     Links restored  {len(self.state.selected_edges)}", True, (218, 182, 191))
            rating = "A few more links need a larger energy reserve."
            hint_text = "Retry the sector or continue to the next one."
            hint_color = (238, 158, 168)
        screen.blit(detail, detail.get_rect(center=(WIDTH // 2, 356)))
        rating_surface = SMALL.render(rating, True, (137, 176, 204))
        screen.blit(rating_surface, rating_surface.get_rect(center=(WIDTH // 2, 386)))
        hint = SMALL.render(hint_text, True, hint_color)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 410)))
        quote = MISSION_QUOTES[self.state.earned_stars if success else 0]
        quote_surface = SMALL.render(quote, True, (157, 199, 226))
        quote_label = SMALL.render("MISSION QUOTE", True, (105, 160, 196))
        screen.blit(quote_label, quote_label.get_rect(center=(WIDTH // 2, 430)))
        screen.blit(quote_surface, quote_surface.get_rect(center=(WIDTH // 2, 449)))
        self.draw_action_button(self.sky_notes_button, "STAR INFO  I", False)
        self.draw_action_button(self.result_brief_button, "MISSION BRIEF  B", False)
        self.result_buttons["retry"] = pygame.Rect(WIDTH // 2 - 178, 526, 160, 48)
        self.result_buttons["next"] = pygame.Rect(WIDTH // 2 + 18, 526, 160, 48)
        self.draw_action_button(self.result_buttons["retry"], "RETRY SECTOR", False)
        next_label = "REPLAY CAMPAIGN" if success and final_sector else "NEXT WORLD  >"
        self.draw_action_button(self.result_buttons["next"], next_label, True)

    def _draw_sky_notes(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((1, 4, 15, 232))
        screen.blit(veil, (0, 0))
        note_box = pygame.Rect(95, 64, 910, 592)
        glass_panel(screen, note_box, (5, 15, 35, 252), (88, 184, 227), 20)
        heading = TITLE.render("STAR & PATTERN FIELD GUIDE", True, (229, 246, 255))
        screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 100)))
        subheading = SMALL.render("REAL STAR NAMES • PUZZLE ROUTES ARE SCHEMATIC, NOT MEASURED SKY POSITIONS", True, (129, 175, 204))
        screen.blit(subheading, subheading.get_rect(center=(WIDTH // 2, 124)))

        left_x, right_x = 125, 575
        screen.blit(MEDIUM.render("STARS IN THIS SECTOR", True, (121, 204, 239)), (left_x, 154))
        screen.blit(MEDIUM.render("REAL SKY PATTERN", True, (121, 204, 239)), (right_x, 154))
        pygame.draw.line(screen, (36, 67, 91), (left_x, 180), (535, 180), 1)
        pygame.draw.line(screen, (36, 67, 91), (right_x, 180), (975, 180), 1)

        role = {
            "NORMAL": "Standard link node",
            "POWER": "Halves link cost",
            "ENERGY": "Restores up to 5 energy",
            "UNSTABLE": "Link expires after 3 moves",
        }
        for i, star in enumerate(self.state.star_list):
            y = 194 + i * 42
            dot_color = self.hud._star_color(star.name, star.type)
            pygame.draw.circle(screen, dot_color, (left_x + 7, y + 7), 4)
            name = self.hud.fit_text(star.name, FONT, 330)
            screen.blit(FONT.render(name, True, (210, 228, 242)), (left_x + 20, y))
            desc = role.get(star.type, "Star") + " • real object name; schematic game position"
            desc = self.hud.fit_text(desc, SMALL, 390)
            screen.blit(SMALL.render(desc, True, (133, 169, 194)), (left_x + 20, y + 18))

        fact = REAL_SKY_NOTES.get(self.world_idx + 1, "These names refer to real sky objects. Astronomers plot them with measured coordinates; this puzzle rearranges them to teach network planning.")
        wrapped = self.wrap_text(fact, FONT, 395)
        for i, line in enumerate(wrapped):
            screen.blit(FONT.render(line, True, (185, 211, 229)), (right_x, 196 + i * 25))

        expert_notes = [
            "How pros map stars:",
            "• Parallax gives distance from apparent annual shift.",
            "• Spectra reveal temperature, chemistry and radial motion.",
            "• Repeated brightness readings expose eclipses and variability.",
            "Sources: IAU constellation guide • ESA Gaia • NASA Science",
        ]
        notes_y = max(350, 212 + len(wrapped) * 25 + 22)
        for i, line in enumerate(expert_notes):
            rendered = SMALL.render(line, True, (145, 189, 215) if i < 4 else (105, 150, 180))
            screen.blit(rendered, (right_x, notes_y + i * 26))
        self.draw_action_button(pygame.Rect(WIDTH // 2 - 70, 602, 140, 38), "BACK", True)

    def _draw_mission_brief(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((1, 4, 15, 232))
        screen.blit(veil, (0, 0))
        box = pygame.Rect(170, 120, 760, 490)
        glass_panel(screen, box, (5, 15, 35, 252), (88, 184, 227), 20)
        heading = TITLE.render("MISSION BRIEFING", True, (229, 246, 255))
        screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 160)))
        name = FONT_HERO.render(self.state.name, True, (223, 241, 252))
        if name.get_width() > 700:
            name = FONT.render(self.state.name, True, (223, 241, 252))
        screen.blit(name, name.get_rect(center=(WIDTH // 2, 203)))
        sector = f"SECTOR {self.state.world_id:02}   •   {self.state.difficulty}   •   ENERGY RESERVE {self.state.max_energy}"
        screen.blit(MEDIUM.render(sector, True, (118, 195, 228)), MEDIUM.render(sector, True, (118, 195, 228)).get_rect(center=(WIDTH // 2, 240)))
        stats = f"{len(self.state.stars)} stars   •   {len(self.state.edges)} possible corridors   •   Target: one connected, cycle-free network"
        stats_surface = SMALL.render(stats, True, (155, 190, 214))
        screen.blit(stats_surface, stats_surface.get_rect(center=(WIDTH // 2, 269)))

        screen.blit(MEDIUM.render("MISSION DISPATCH", True, (121, 204, 239)), (220, 304))
        story_lines = self.wrap_text(self.state.story, FONT, 660)
        for i, line in enumerate(story_lines[:3]):
            screen.blit(FONT.render(line, True, (194, 216, 232)), (220, 331 + i * 22))

        objective_y = 338 + min(3, len(story_lines)) * 22
        screen.blit(MEDIUM.render("OBJECTIVE & FIELD RULES", True, (121, 204, 239)), (220, objective_y))
        rules = [
            "Link all stars through listed corridors. Union-Find rejects any link that creates a cycle.",
            "Spend carefully: the final network is rated against this sector's minimum-cost spanning tree.",
            "POWER halves a link cost   •   ENERGY restores up to 5   •   UNSTABLE links expire after 3 moves.",
        ]
        for i, line in enumerate(rules):
            y = objective_y + 27 + i * 22
            screen.blit(SMALL.render(self.hud.fit_text(line, SMALL, 680), True, (155, 190, 214)), (220, y))
        self.draw_action_button(pygame.Rect(WIDTH // 2 - 84, 550, 168, 40), "RETURN TO SECTOR", True)

    @staticmethod
    def wrap_text(text, font, max_width):
        lines, current = [], ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            if current and font.size(trial)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        return lines

    def run(self):
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.WINDOWMAXIMIZED:
                    self.window_maximized = True
                elif event.type == pygame.WINDOWRESTORED:
                    self.window_maximized = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.show_intro:
                        if self.play_button.collidepoint(event.pos):
                            self.show_intro = False
                        elif self.intro_sfx_button.collidepoint(event.pos):
                            self.activate_button("sound")
                        elif self.intro_music_button.collidepoint(event.pos):
                            self.activate_button("music")
                        elif self.intro_maximize_button.collidepoint(event.pos):
                            self.activate_button("maximize")
                        continue
                    if self.sky_notes_open:
                        self.sky_notes_open = False
                        continue
                    if self.mission_brief_open:
                        self.mission_brief_open = False
                        continue
                    if self.state.is_completed or self.state.is_failed:
                        if self.sky_notes_button.collidepoint(event.pos):
                            self.sky_notes_open = True
                            continue
                        if self.result_brief_button.collidepoint(event.pos):
                            self.mission_brief_open = True
                            continue
                        if self.result_buttons["retry"].collidepoint(event.pos):
                            self.load_world(self.world_idx)
                        elif self.result_buttons["next"].collidepoint(event.pos):
                            self.load_world(0 if self.state.is_completed and self.world_idx == len(self.world_files) - 1
                                            else self.world_idx + 1)
                        continue
                    drawer_choice = None
                    if self.hud.show_worlds_drawer:
                        drawer_choice = next((i for i, rect in enumerate(self.hud.world_option_rects)
                                              if rect.collidepoint(event.pos)), None)
                    if drawer_choice is not None:
                        self.load_world(drawer_choice)
                        self.hud.show_worlds_drawer = False
                    else:
                        button = next((name for name, rect in self.buttons.items() if rect.collidepoint(event.pos)), None)
                        if button:
                            self.activate_button(button)
                        elif not self.state.is_completed and not self.state.is_failed:
                            roster_height = min(290, 46 + len(self.state.star_list) * 20 + 66)
                            blocked_panels = [pygame.Rect(18, 92, 136, roster_height), pygame.Rect(920, 92, 164, 520)]
                            if any(panel.collidepoint(event.pos) for panel in blocked_panels):
                                continue
                            for star in self.state.star_list:
                                if math.hypot(event.pos[0] - star.x, event.pos[1] - star.y) <= 25:
                                    self.handle_star_click(star.id)
                                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.sky_notes_open:
                            self.sky_notes_open = False
                        elif self.mission_brief_open:
                            self.mission_brief_open = False
                        else:
                            running = False
                    elif event.key == pygame.K_F11:
                        self.toggle_maximize_window()
                    elif event.key == pygame.K_i and not self.show_intro:
                        self.activate_button("sky_info")
                    elif event.key == pygame.K_b and not self.show_intro:
                        self.activate_button("brief")
                    elif self.show_intro:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.show_intro = False
                        elif event.key == pygame.K_m:
                            self.activate_button("sound")
                        elif event.key == pygame.K_p:
                            self.activate_button("music")
                    elif self.state.is_completed or self.state.is_failed:
                        if event.key == pygame.K_r:
                            self.load_world(self.world_idx)
                        elif event.key == pygame.K_n:
                            self.load_world(self.world_idx + 1)
                    elif event.key == pygame.K_z:
                        self.activate_button("undo")
                    elif event.key == pygame.K_y:
                        self.activate_button("redo")
                    elif event.key == pygame.K_k:
                        self.activate_button("solver")
                    elif event.key == pygame.K_n:
                        self.activate_button("next")
                    elif event.key == pygame.K_r:
                        self.activate_button("reset")
                    elif event.key == pygame.K_m:
                        self.activate_button("sound")
                    elif event.key == pygame.K_p:
                        self.activate_button("music")
            self.update(dt)
            self.draw(dt)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameApp().run()
