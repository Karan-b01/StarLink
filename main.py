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
from visual.particle_system import ParticleSystem
from visual.sky_patterns import PATTERNS, WORLD_PATTERN

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

FONT = pygame.font.SysFont("Segoe UI", 17)
SMALL = pygame.font.SysFont("Segoe UI", 14)
MEDIUM = pygame.font.SysFont("Segoe UI", 17, bold=True)
TITLE = pygame.font.SysFont("Segoe UI", 23, bold=True)
FONT_HERO = pygame.font.SysFont("Segoe UI", 46, bold=True)
INTRO_TITLE = pygame.font.SysFont("Space Grotesk", 68, bold=True)
INTRO_BODY = pygame.font.SysFont("Inter", 18)
INTRO_SMALL = pygame.font.SysFont("Inter", 15)

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
        self.world_files = []
        for world_number in range(1, 14):
            self.world_files.append(f"levels/world{world_number}.json")
        self.world_idx = 0
        self.buttons = {
            "undo": self.hud.btn_undo,
            "redo": self.hud.btn_redo,
            "reset": self.hud.btn_settings,
            "worlds": self.hud.btn_worlds,
            "solver": self.hud.btn_algo,
            "next": self.hud.btn_next,
            "sky_info": self.hud.btn_sky_info,
            "maximize": self.hud.btn_maximize,
            "hint": self.hud.btn_hint,
        }
        self.particles = ParticleSystem()
        self.active_hint_edge = None
        self.hint_timer = 0.0
        self.victory_burst_done = False
        self.display_energy = 0.0
        self.active_plasma_beams = []
        self.result_buttons = {
            "retry": pygame.Rect(WIDTH // 2 - 178, 438, 160, 48),
            "next": pygame.Rect(WIDTH // 2 + 18, 438, 160, 48),
        }
        self.show_intro = True
        self.show_intro_rules = False
        self.intro_focus_how = False
        self.toast_message = None
        self.toast_timer = 0.0
        self.play_button = pygame.Rect(WIDTH // 2 - 112, HEIGHT // 2 + 36, 224, 54)
        self.how_to_button = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 112, 180, 34)
        self.window_maximized = False
        self.sky_notes_open = False
        self.mission_brief_open = False
        self.sky_notes_button = pygame.Rect(WIDTH // 2 - 190, 470, 150, 38)
        self.result_brief_button = pygame.Rect(WIDTH // 2 + 40, 470, 150, 38)
        self.result_started_at = 0.0
        self.result_analysis = None
        self.transition_timer = 0.0
        self.load_world(self.world_idx)

    def load_world(self, idx):
        self.world_idx = idx % len(self.world_files)
        self.state = GameState(load_level_from_json(self.world_files[self.world_idx]))
        self.toast_message = None
        self.toast_timer = 0.0
        self.selected_star = None
        self.flash_cycle = None
        self.flash_timer = 0.0
        self.active_hint_edge = None
        self.hint_timer = 0.0
        self.victory_burst_done = False
        self.win_sound_played = False
        self.stepper_gen = None
        self.stepper_timer = 0.0
        self.stepper_edges = []
        self.stepper_active = False
        self.result_started_at = 0.0
        self.result_analysis = None
        self.sky_notes_open = False
        self.mission_brief_open = False
        self.transition_timer = 0.42
        self.display_energy = float(self.state.energy)
        self.active_plasma_beams = []

    def handle_star_click(self, star_id):
        if self.selected_star is None:
            self.selected_star = star_id
            s = self.state.stars[star_id]
            self.particles.emit_star_burst(s.x, s.y, (85, 215, 255), 16)
            self.state.status_message = f"Star {s.name} selected — choose a connected star."
            return
        if self.selected_star != star_id:
            u, v = self.selected_star, star_id
            s1, s2 = self.state.stars[u], self.state.stars[v]
            ok, _ = self.state.connect_edge(u, v)
            if not ok and self.state.cycle_edge_flash:
                self.flash_cycle = self.state.cycle_edge_flash
                self.flash_timer = 0.7
                self.sound.play("cycle")
                self.particles.emit_cycle_rejection((s1.x, s1.y), (s2.x, s2.y), 26)
            elif ok:
                if self.state.resonance_streak:
                    self.sound.play_resonance(self.state.resonance_streak)
                else:
                    self.sound.play("cycle")
                self.active_plasma_beams.append({
                    'p1': (s1.x, s1.y),
                    'p2': (s2.x, s2.y),
                    'progress': 0.0,
                    'speed': 3.6,
                })
                self.particles.emit_link_corridor((s1.x, s1.y), (s2.x, s2.y), (60, 215, 255), 24)
                self.particles.emit_star_burst(s1.x, s1.y, (130, 235, 255), 14)
                self.particles.emit_star_burst(s2.x, s2.y, (130, 235, 255), 14)
                if self.state.is_completed:
                    self.particles.emit_victory_cascade(self.state.star_list, 80)
        self.selected_star = None

    def trigger_hint(self):
        hint_edge, explanation = self.state.get_algorithm_hint()
        if hint_edge:
            self.active_hint_edge = hint_edge
            self.hint_timer = 4.5
            self.toast_message = explanation
            self.toast_timer = 4.5
            self.sound.play("hint")
            u, v, _ = hint_edge
            s1, s2 = self.state.stars[u], self.state.stars[v]
            self.particles.emit_star_burst(s1.x, s1.y, (255, 225, 90), 18)
            self.particles.emit_star_burst(s2.x, s2.y, (255, 225, 90), 18)
        else:
            self.toast_message = explanation
            self.toast_timer = 3.0

    def trigger_kruskal_stepper(self):
        if self.state.has_timed_edges:
            self.stepper_gen = iter(
                (*self.state.edges[index], True, "best legal move")
                for index in self.state.get_current_plan()
            )
            self.toast_message = "This plan connects unstable links before they expire."
        else:
            vertices = list(self.state.stars.keys())
            self.stepper_gen = kruskal_steps(vertices, self.state.edges)
            self.toast_message = "Kruskal checks edges from lowest cost upward and skips cycles."
        self.stepper_edges = []
        self.stepper_active = True
        self.stepper_timer = 0.0
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
        if name == "undo":
            self.state.undo()
            self.sound.play("undo")
        elif name == "redo":
            self.state.redo()
            self.sound.play("undo")
        elif name == "reset":
            self.load_world(self.world_idx)
        elif name == "solver":
            self.trigger_kruskal_stepper()
        elif name == "hint":
            self.trigger_hint()
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
        self.particles.update(dt)

        # Smooth fluid energy bar interpolation and particle spill
        if abs(self.display_energy - self.state.energy) > 0.05:
            old_e = self.display_energy
            self.display_energy += (self.state.energy - self.display_energy) * min(1.0, dt * 7.5)
            if old_e > self.display_energy + 0.12:
                pct = max(0.0, min(1.0, self.display_energy / self.state.max_energy if self.state.max_energy > 0 else 0))
                spark_x = 504 + int(215 * pct)
                self.particles.emit_energy_spill(spark_x, 49, count=2)
        else:
            self.display_energy = float(self.state.energy)

        # Update active plasma laser corridors
        for beam in self.active_plasma_beams[:]:
            beam['progress'] = min(1.0, beam['progress'] + dt * beam['speed'])
            p1, p2 = beam['p1'], beam['p2']
            tip_x = p1[0] + (p2[0] - p1[0]) * beam['progress']
            tip_y = p1[1] + (p2[1] - p1[1]) * beam['progress']
            self.particles.emit_plasma_tip(tip_x, tip_y, count=2)
            if beam['progress'] >= 1.0:
                self.active_plasma_beams.remove(beam)

        if self.hint_timer > 0:
            self.hint_timer = max(0.0, self.hint_timer - dt)
            if self.hint_timer == 0:
                self.active_hint_edge = None
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
            self.result_analysis = self.state.get_post_level_analysis()
        if self.state.is_completed and not self.win_sound_played:
            self.sound.play("win")
            self.win_sound_played = True
            if not self.victory_burst_done:
                self.particles.emit_victory_cascade(self.state.star_list, 80)
                self.victory_burst_done = True
        if not self.state.is_completed and not self.state.is_failed:
            self.state.check_failure()
        if self.state.notification_message:
            self.toast_message = self.state.notification_message
            self.toast_timer = 3.5
            if "expired" in self.state.notification_message.lower():
                self.sound.play("cycle")
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

        # A quiet, dark playfield keeps the constellation readable over the
        # animated nebula while leaving the side panels clear.
        playfield = pygame.Surface((760, 548), pygame.SRCALPHA)
        pygame.draw.rect(playfield, (2, 7, 19, 112), playfield.get_rect(), border_radius=18)
        pygame.draw.rect(playfield, (56, 112, 159, 105), playfield.get_rect(), 1, border_radius=18)
        screen.blit(playfield, (155, 82))

        # Thin constellation guide lines and active energy corridors.
        selected_pairs = {
            (min(edge[0], edge[1]), max(edge[0], edge[1]))
            for edge in self.state.selected_edges
        }
        edge_labels = []
        for edge_i, (u, v, base_cost) in enumerate(self.state.edges):
            if edge_i in self.state.expired_edges:
                continue
            a, b = self.state.stars[u], self.state.stars[v]
            p1, p2 = (int(a.x), int(a.y)), (int(b.x), int(b.y))
            pair = (min(u, v), max(u, v))
            selected = pair in selected_pairs
            deadline = self.state.edge_rules.get(edge_i)
            cycle = self.flash_cycle == (min(u, v), max(u, v)) if self.flash_cycle else False
            cost = base_cost
            if cycle:
                pygame.draw.line(screen, (255, 65, 95), p1, p2, 5)
                pygame.draw.line(screen, (255, 210, 220), p1, p2, 1)
            elif selected:
                pygame.draw.line(screen, (13, 74, 150), p1, p2, 8)
                pygame.draw.line(screen, (45, 174, 245), p1, p2, 4)
                shimmer = (math.sin(now * 4 + u + v) + 1) * .5
                pygame.draw.line(screen, (int(130 + shimmer * 100), 245, 255), p1, p2, 1)
                # A traveling pulse marks a restored connection.
                travel = (now * .42 + (u + v) * .173) % 1.0
                spark = (int(p1[0] + (p2[0] - p1[0]) * travel),
                         int(p1[1] + (p2[1] - p1[1]) * travel))
                pygame.draw.circle(screen, (25, 110, 190), spark, 7)
                pygame.draw.circle(screen, (210, 250, 255), spark, 2)
            elif deadline is not None:
                moves_left = max(0, deadline - self.state.turns_elapsed)
                if moves_left <= 1:
                    urgent_pulse = (math.sin(now * 8) + 1) * 0.5
                    alert_color = (
                        int(235 + urgent_pulse * 20),
                        int(85 + urgent_pulse * 40),
                        int(70 + urgent_pulse * 30)
                    )
                    self.draw_dashed_line(screen, alert_color, p1, p2, width=3, dash_length=8, gap_length=5)
                else:
                    self.draw_dashed_line(screen, (224, 173, 92), p1, p2, width=2, dash_length=9, gap_length=6)
            else:
                pygame.draw.line(screen, (39, 77, 116), p1, p2, 1)
            mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            label_text = str(cost)
            timer_text = None
            if deadline is not None and not selected:
                moves_left = max(0, deadline - self.state.turns_elapsed)
                timer_text = f"{moves_left} MOVE" if moves_left == 1 else f"{moves_left} MOVES"
            edge_labels.append((u, v, mid, label_text, selected, timer_text))
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

        if self.active_hint_edge and self.hint_timer > 0:
            hu, hv, _ = self.active_hint_edge
            ha, hb = self.state.stars[hu], self.state.stars[hv]
            hp1, hp2 = (int(ha.x), int(ha.y)), (int(hb.x), int(hb.y))
            pulse = (math.sin(now * 10) + 1) * 0.5
            pygame.draw.line(screen, (255, int(180 + pulse * 60), 60), hp1, hp2, 6)
            pygame.draw.line(screen, (255, 255, 220), hp1, hp2, 2)
            pygame.draw.circle(screen, (255, 215, 60), hp1, int(15 + pulse * 4), 2)
            pygame.draw.circle(screen, (255, 215, 60), hp2, int(15 + pulse * 4), 2)

        self.particles.draw(screen)

        # Draw active progressive plasma laser corridor draws
        for beam in self.active_plasma_beams:
            bp1, bp2 = beam['p1'], beam['p2']
            prog = beam['progress']
            tip = (bp1[0] + (bp2[0] - bp1[0]) * prog, bp1[1] + (bp2[1] - bp1[1]) * prog)
            pygame.draw.line(screen, (30, 110, 220), bp1, tip, 8)
            pygame.draw.line(screen, (80, 220, 255), bp1, tip, 4)
            pygame.draw.line(screen, (255, 255, 255), bp1, tip, 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(tip[0]), int(tip[1])), 5)
            pygame.draw.circle(screen, (100, 230, 255), (int(tip[0]), int(tip[1])), 9, 2)

        # Candidate neighbor pulsing radar rings when a star is selected
        if self.selected_star is not None:
            cand_neighbors = set()
            for edge_i, (u, v, _) in enumerate(self.state.edges):
                if edge_i in self.state.expired_edges:
                    continue
                if u == self.selected_star and not any(e[0] == min(u, v) and e[1] == max(u, v) for e in self.state.selected_edges):
                    cand_neighbors.add(v)
                elif v == self.selected_star and not any(e[0] == min(u, v) and e[1] == max(u, v) for e in self.state.selected_edges):
                    cand_neighbors.add(u)
            for neighbor_id in cand_neighbors:
                n_star = self.state.stars[neighbor_id]
                for ring_i in range(2):
                    ring_phase = (now * 2.2 + neighbor_id * 0.5 + ring_i * 0.5) % 1.0
                    ring_r = int(14 + ring_phase * 20)
                    ring_alpha = int((1.0 - ring_phase) * 160)
                    ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (80, 220, 255, ring_alpha), (ring_r + 2, ring_r + 2), ring_r, 2)
                    screen.blit(ring_surf, (int(n_star.x - ring_r - 2), int(n_star.y - ring_r - 2)))

        occupied_labels = []
        for star in self.state.star_list:
            occupied_labels.extend(CelestialRenderer.draw_star(
                screen, star, self.selected_star == star.id, now, FONT,
                all_stars=self.state.star_list,
                edges=self.state.edges,
                placed_labels=occupied_labels,
            ))

        # Put corridor costs and timer badges in clean non-overlapping positions
        def draw_edge_badge(u, v, mid, cost_text, selected, timer_text, occupied):
            cost_color = (220, 250, 255) if selected else (179, 213, 247)
            cost_surf = SMALL.render(cost_text, True, cost_color)

            is_urgent = timer_text and timer_text.startswith("1 ")
            if timer_text:
                timer_fg = (255, 115, 95) if is_urgent else (255, 211, 144)
                timer_surf = SMALL.render(timer_text, True, timer_fg)
                dot_surf = SMALL.render(" • ", True, (120, 145, 175))
                total_w = cost_surf.get_width() + dot_surf.get_width() + timer_surf.get_width() + 18
                total_h = max(cost_surf.get_height(), timer_surf.get_height()) + 8

                badge_img = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
                bg_color = (38, 14, 18, 240) if is_urgent else (10, 18, 32, 240)
                border_color = (255, 85, 75) if is_urgent else (210, 165, 80)
                pygame.draw.rect(badge_img, bg_color, badge_img.get_rect(), border_radius=6)
                pygame.draw.rect(badge_img, border_color, badge_img.get_rect(), 1, border_radius=6)

                cx = 9
                badge_img.blit(cost_surf, (cx, (total_h - cost_surf.get_height()) // 2))
                cx += cost_surf.get_width()
                badge_img.blit(dot_surf, (cx, (total_h - dot_surf.get_height()) // 2))
                cx += dot_surf.get_width()
                badge_img.blit(timer_surf, (cx, (total_h - timer_surf.get_height()) // 2))
            else:
                total_w = cost_surf.get_width() + 14
                total_h = cost_surf.get_height() + 8
                badge_img = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
                bg_color = (8, 16, 32, 230)
                border_color = (60, 140, 215) if selected else (45, 85, 135)
                pygame.draw.rect(badge_img, bg_color, badge_img.get_rect(), border_radius=6)
                pygame.draw.rect(badge_img, border_color, badge_img.get_rect(), 1, border_radius=6)
                badge_img.blit(cost_surf, (7, (total_h - cost_surf.get_height()) // 2))

            a, b = self.state.stars[u], self.state.stars[v]
            dx, dy = b.x - a.x, b.y - a.y
            length = max(1.0, math.hypot(dx, dy))
            normal = (-dy / length, dx / length)

            candidates = []
            for fraction in (0.50, 0.40, 0.60, 0.30, 0.70, 0.22, 0.78):
                base_x = a.x + dx * fraction
                base_y = a.y + dy * fraction
                for offset in (0, 18, -18, 30, -30, 42, -42):
                    pos = (round(base_x + normal[0] * offset), round(base_y + normal[1] * offset))
                    rect = badge_img.get_rect(center=pos)
                    if rect.left < 10 or rect.right > WIDTH - 185 or rect.top < 75 or rect.bottom > HEIGHT - 85:
                        continue
                    if any(math.hypot(rect.centerx - s.x, rect.centery - s.y) < 24 for s in self.state.star_list):
                        continue
                    if any(rect.colliderect(old.inflate(2, 2)) for old in occupied):
                        continue
                    score = abs(fraction - 0.5) * 100 + abs(offset)
                    candidates.append((score, rect))

            if candidates:
                candidates.sort(key=lambda item: item[0])
                best_rect = candidates[0][1]
            else:
                best_rect = badge_img.get_rect(center=mid)

            screen.blit(badge_img, best_rect.topleft)
            occupied.append(best_rect)

        for u, v, mid, text, selected, timer_text in edge_labels:
            draw_edge_badge(u, v, mid, text, selected, timer_text, occupied_labels)

        # Real-time star hover analysis & trajectory preview
        mouse_pos = pygame.mouse.get_pos()
        in_hud = (
            mouse_pos[1] <= 70 or mouse_pos[1] >= HEIGHT - 85 or
            pygame.Rect(920, 92, 164, 520).collidepoint(mouse_pos)
        )
        hovered_star = None
        if not in_hud and not self.state.is_completed and not self.state.is_failed:
            hovered_star = next((s for s in self.state.star_list if math.hypot(mouse_pos[0] - s.x, mouse_pos[1] - s.y) <= 24), None)

        if hovered_star:
            hx, hy = int(hovered_star.x), int(hovered_star.y)
            ring_r = int(22 + (math.sin(now * 6) + 1) * 2)
            pygame.draw.circle(screen, (80, 210, 255), (hx, hy), ring_r, 1)

            if self.selected_star is not None and self.selected_star != hovered_star.id:
                sel_star = self.state.stars[self.selected_star]
                sp1 = (int(sel_star.x), int(sel_star.y))
                sp2 = (hx, hy)
                u, v = min(self.selected_star, hovered_star.id), max(self.selected_star, hovered_star.id)
                edge_entry = next((e for e in self.state.edges if (e[0] == u and e[1] == v) or (e[0] == v and e[1] == u)), None)
                if edge_entry:
                    edge_i = self.state.edge_index[(u, v)]
                    from dsa.union_find import UnionFind
                    uf = UnionFind(list(self.state.stars.keys()))
                    for su, sv, _ in self.state.selected_edges:
                        uf.union(su, sv)
                    is_cycle = (uf.find(u) == uf.find(v))
                    mid = ((sp1[0] + sp2[0]) // 2, (sp1[1] + sp2[1]) // 2)
                    if edge_i in self.state.expired_edges:
                        self.draw_dashed_line(screen, (255, 70, 90), sp1, sp2, width=3, dash_length=8, gap_length=5)
                        warn_pill = SMALL.render("LINK EXPIRED", True, (255, 150, 150))
                        pill_rect = warn_pill.get_rect(center=(mid[0], mid[1] - 18))
                        glass_panel(screen, pill_rect.inflate(14, 8), fill=(30, 8, 14, 235), border=(255, 70, 90), radius=5)
                        screen.blit(warn_pill, pill_rect)
                    elif is_cycle:
                        self.draw_dashed_line(screen, (255, 70, 90), sp1, sp2, width=3, dash_length=8, gap_length=5)
                        warn_pill = SMALL.render("CYCLE REJECTED", True, (255, 130, 140))
                        pill_rect = warn_pill.get_rect(center=(mid[0], mid[1] - 18))
                        glass_panel(screen, pill_rect.inflate(14, 8), fill=(30, 8, 14, 235), border=(255, 70, 90), radius=5)
                        screen.blit(warn_pill, pill_rect)
                    else:
                        cost = edge_entry[2]
                        self.draw_dashed_line(screen, (80, 230, 255), sp1, sp2, width=3, dash_length=8, gap_length=5)
                        cost_text = f"LINK COST: {cost}"
                        cost_pill = SMALL.render(cost_text, True, (190, 245, 255))
                        pill_rect = cost_pill.get_rect(center=(mid[0], mid[1] - 18))
                        glass_panel(screen, pill_rect.inflate(14, 8), fill=(8, 25, 45, 235), border=(70, 190, 245), radius=5)
                        screen.blit(cost_pill, pill_rect)
            elif self.selected_star is None:
                card_w, card_h = 220, 52
                # Keep hover details in the clear strip below the top bar,
                # away from corridor costs and star-name labels.
                card_x = (WIDTH - card_w) // 2
                card_y = 76
                t_col, t_desc = (180, 215, 245), "STAR: standard corridor cost"
                card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
                glass_panel(screen, card_rect, fill=(6, 14, 32, 235), border=t_col, radius=8)
                name_text = self.hud.fit_text(hovered_star.name.upper(), SMALL, card_w - 16)
                name_lbl = SMALL.render(name_text, True, (240, 248, 255))
                screen.blit(name_lbl, (card_x + 8, card_y + 6))
                role_font = pygame.font.SysFont("Segoe UI", 10)
                role_lbl = role_font.render(self.hud.fit_text(t_desc, role_font, card_w - 16), True, t_col)
                screen.blit(role_lbl, (card_x + 8, card_y + 26))

        ghost_elapsed = self.starfield.elapsed - self.result_started_at if self.state.is_completed else -1
        if self.state.is_completed and 0 <= ghost_elapsed < 3.2:
            self._draw_ghost_replay(ghost_elapsed)

        # Overlay panels follow the compact constellation-dashboard layout.
        self.hud.draw_top_bar(screen, self.state, display_energy=self.display_energy)
        self.hud.draw_kruskal_inspector(screen, self.state)
        self.hud.draw_bottom_dock(screen, self.state, self.window_maximized)

        if self.toast_message and self.toast_timer > 0:
            toast_w = min(620, max(330, FONT.size(self.toast_message)[0] + 48))
            toast_rect = pygame.Rect((WIDTH - toast_w) // 2, HEIGHT - 112, toast_w, 42)
            warning = "Warning:" in self.toast_message or "bridge" in self.toast_message.lower() or "expired" in self.toast_message.lower()
            accent = (255, 133, 116) if warning else (255, 196, 91)
            glass_panel(screen, toast_rect, (12, 20, 39, 242), accent, 10)
            pygame.draw.circle(screen, accent, (toast_rect.x + 18, toast_rect.centery), 4)
            toast_text = SMALL.render(self.hud.fit_text(self.toast_message, SMALL, toast_w - 42), True, (232, 241, 250))
            screen.blit(toast_text, toast_text.get_rect(midleft=(toast_rect.x + 31, toast_rect.centery)))

        if self.state.is_failed or (self.state.is_completed and ghost_elapsed >= 3.2):
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
        # Use a quiet navy background, a soft center light, and a few dim stars.
        screen.fill((5, 8, 14))
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for radius in range(420, 0, -20):
            alpha = int(24 * (1 - radius / 440))
            pygame.draw.circle(glow, (34, 38, 44, alpha), (WIDTH // 2, HEIGHT // 2 - 10), radius)
        screen.blit(glow, (0, 0))

        # Sparse, gently twinkling stars and two faint constellation strokes.
        star_points = []
        for index in range(42):
            x = (index * 193 + 73) % WIDTH
            y = (index * 317 + 41) % HEIGHT
            phase = index * 1.71
            brightness = int(48 + 28 * (0.5 + 0.5 * math.sin(now * 0.7 + phase)))
            star_points.append((x, y))
            pygame.draw.circle(screen, (brightness, brightness, brightness + 5), (x, y), 1 if index % 5 else 2)

        faint = (32, 35, 38)
        for pairs in ((1, 7, 12, 18), (25, 31, 36, 40)):
            for first, second in zip(pairs, pairs[1:]):
                pygame.draw.line(screen, faint, star_points[first], star_points[second], 1)

        center_x = WIDTH // 2
        fade = lambda start: max(0, min(255, int((now - start) * 520)))

        # Small line-art constellation mark, drawn without a surrounding badge.
        logo_y = HEIGHT // 2 - 150
        logo_points = [(center_x - 15, logo_y + 10), (center_x - 3, logo_y - 10),
                       (center_x + 15, logo_y - 4), (center_x + 7, logo_y + 15)]
        logo_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for first, second in ((0, 1), (1, 2), (2, 3)):
            pygame.draw.line(logo_layer, (201, 162, 74, 210), logo_points[first], logo_points[second], 2)
        for point in logo_points:
            pygame.draw.circle(logo_layer, (245, 239, 218, 235), point, 3)
        logo_layer.set_alpha(fade(0.0))
        screen.blit(logo_layer, (0, 0))

        title_text = "STARLINK"
        title_spacing = 6
        title_width = sum(INTRO_TITLE.size(char)[0] for char in title_text) + title_spacing * (len(title_text) - 1)
        title_x = center_x - title_width // 2
        for char in title_text:
            glyph = INTRO_TITLE.render(char, True, (248, 247, 242))
            glyph.set_alpha(fade(0.12))
            screen.blit(glyph, (title_x, HEIGHT // 2 - 65 - glyph.get_height() // 2))
            title_x += glyph.get_width() + title_spacing

        tagline = INTRO_BODY.render("Connect the stars. Spend less energy.", True, (205, 207, 208))
        tagline.set_alpha(fade(0.28))
        screen.blit(tagline, tagline.get_rect(center=(center_x, HEIGHT // 2 - 5)))

        hover = self.play_button.collidepoint(pygame.mouse.get_pos())
        button_color = (224, 190, 112) if hover else (201, 162, 74)
        button_layer = pygame.Surface(self.play_button.size, pygame.SRCALPHA)
        pygame.draw.rect(button_layer, (*button_color, 255), button_layer.get_rect(), border_radius=13)
        label = INTRO_BODY.render("Play", True, (24, 22, 18))
        button_layer.blit(label, label.get_rect(center=button_layer.get_rect().center))
        button_layer.set_alpha(fade(0.42))
        screen.blit(button_layer, (self.play_button.left, self.play_button.top))
        if not self.intro_focus_how and fade(0.42) > 0:
            pygame.draw.rect(screen, (246, 224, 171), self.play_button.inflate(6, 6), 2, border_radius=16)

        link_color = (145, 147, 149) if not self.how_to_button.collidepoint(pygame.mouse.get_pos()) else (224, 222, 215)
        link = INTRO_SMALL.render("How to play", True, link_color)
        link.set_alpha(fade(0.55))
        screen.blit(link, link.get_rect(center=self.how_to_button.center))
        if self.how_to_button.collidepoint(pygame.mouse.get_pos()) or self.intro_focus_how:
            pygame.draw.line(screen, (201, 162, 74), (self.how_to_button.left + 28, self.how_to_button.bottom - 2),
                             (self.how_to_button.right - 28, self.how_to_button.bottom - 2), 1)

        if self.show_intro_rules:
            self._draw_intro_rules()

    def _draw_intro_rules(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((2, 4, 8, 210))
        screen.blit(veil, (0, 0))

        box = pygame.Rect(WIDTH // 2 - 320, HEIGHT // 2 - 200, 640, 400)
        pygame.draw.rect(screen, (13, 17, 22), box, border_radius=14)
        pygame.draw.rect(screen, (68, 65, 55), box, 1, border_radius=14)
        heading = TITLE.render("How to play", True, (248, 247, 242))
        screen.blit(heading, heading.get_rect(center=(box.centerx, box.top + 46)))

        rules = [
            "Select two stars joined by a corridor to connect them.",
            "Each corridor costs energy. Stay within the sector reserve.",
            "Union-Find rejects links that create a cycle.",
            "Every move advances the collapse timer: amber dashed links disappear permanently when their countdown reaches zero.",
            "Some unstable links are vital to connect distant stars cheaply, while others are tempting shortcuts—plan ahead!",
        ]
        y = box.top + 104
        for rule in rules:
            for line in self.wrap_text(rule, INTRO_BODY, box.width - 72):
                rendered = INTRO_BODY.render(line, True, (218, 219, 216))
                screen.blit(rendered, (box.left + 36, y))
                y += 26
            y += 10

        close_text = INTRO_SMALL.render("Press Esc or click to close", True, (154, 155, 153))
        screen.blit(close_text, close_text.get_rect(center=(box.centerx, box.bottom - 32)))

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
        box = pygame.Rect(WIDTH // 2 - 330, 64, 660, 590)
        border = (77, 190, 230) if success else (194, 91, 116)
        glass_panel(screen, box, (5, 15, 35, 252), border, 20)
        eyebrow = SMALL.render("SECTOR REPORT", True, (110, 177, 208))
        screen.blit(eyebrow, eyebrow.get_rect(center=(WIDTH // 2, 96)))
        final_sector = self.world_idx == len(self.world_files) - 1
        if success:
            title_text = "CAMPAIGN COMPLETE" if final_sector else "CONSTELLATION RESTORED"
        else:
            title_text = "SIGNAL LOST"
        title_color = (231, 248, 255) if success else (255, 190, 190)
        title = TITLE.render(title_text, True, title_color)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 130)))

        now = self.starfield.elapsed
        spacing = 48
        first_x = WIDTH // 2 - spacing * 2
        for i in range(5):
            earned = success and i < self.state.earned_stars
            reveal = min(1.0, max(0.0, (now - self.result_started_at - i * .22) / .32)) if success else 0.0
            bob = math.sin(now * 3 + i * .65) * 2 if earned else 0
            cx, cy = first_x + i * spacing, int(184 + bob)
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

        analysis = self.result_analysis or self.state.get_post_level_analysis()
        total_cost = analysis["player_cost"]
        optimal_cost = analysis["optimal_cost"]
        if success and self.state.earned_stars >= 4:
            hint_text, hint_color = "Excellent energy planning. Your route is close to the optimum.", (115, 222, 199)
        elif success and self.state.earned_stars >= 2:
            hint_text, hint_color = "Review the extra energy to improve your score.", (255, 205, 129)
        elif success:
            hint_text, hint_color = "Retry the sector to use fewer extra links.", (255, 172, 142)
        else:
            hint_text, hint_color = "Retry and compare the edge weights before choosing.", (238, 158, 168)
            if self.state.status_message.startswith("Not enough energy"):
                hint_text = self.state.status_message

        # Present the three energy values as aligned columns for quick comparison.
        columns = [
            ("YOUR TOTAL", f"{total_cost} energy", (205, 218, 229)),
            ("OPTIMAL", f"{optimal_cost} energy", (137, 208, 184)),
            ("WASTED", f"{analysis['wasted_energy']} energy" if success else "—", (255, 205, 129)),
        ]
        for index, (label, value, color) in enumerate(columns):
            cx = WIDTH // 2 - 190 + index * 190
            label_surface = SMALL.render(label, True, (137, 176, 204))
            value_surface = MEDIUM.render(value, True, color)
            screen.blit(label_surface, label_surface.get_rect(center=(cx, 229)))
            screen.blit(value_surface, value_surface.get_rect(center=(cx, 253)))
        pygame.draw.line(screen, (40, 67, 91), (box.left + 34, 278), (box.right - 34, 278), 1)

        divergence = analysis["divergence"]
        if divergence:
            u, v, cost = divergence["edge"]
            lines = [f"Move {divergence['move']}: You chose {self.state.stars[u].name} – {self.state.stars[v].name} ({cost} energy)."]
            alternative = divergence["alternative"]
            if alternative:
                a, b, alt_cost = alternative
                route_name = "Best legal plan" if self.state.has_timed_edges else "Kruskal's tree"
                lines.append(f"{route_name} chose {self.state.stars[a].name} - {self.state.stars[b].name} ({alt_cost} energy).")
            divergence_color = (255, 190, 157)
        elif success:
            lines = ["No divergence: your links match a minimum-cost tree."]
            divergence_color = (137, 208, 184)
        else:
            lines = ["No off-optimal move yet."]
            divergence_color = (177, 207, 230)
        label = SMALL.render("FIRST DIVERGENCE", True, (137, 176, 204))
        screen.blit(label, label.get_rect(midleft=(box.left + 38, 298)))
        content_y = 322
        for line in lines:
            for wrapped in self.wrap_text(line, SMALL, box.width - 76):
                line_surface = SMALL.render(wrapped, True, divergence_color)
                screen.blit(line_surface, line_surface.get_rect(midleft=(box.left + 38, content_y)))
                content_y += 20

        rating = f"EFFICIENCY RATING  {self.state.earned_stars} / 5" if success else "NETWORK INCOMPLETE"
        rating_surface = SMALL.render(rating, True, (137, 176, 204))
        screen.blit(rating_surface, rating_surface.get_rect(center=(WIDTH // 2, 390)))
        hint_surface = SMALL.render(self.hud.fit_text(hint_text, SMALL, box.width - 76), True, hint_color)
        screen.blit(hint_surface, hint_surface.get_rect(center=(WIDTH // 2, 414)))

        self.sky_notes_button = pygame.Rect(WIDTH // 2 - 198, 452, 180, 38)
        self.result_brief_button = pygame.Rect(WIDTH // 2 + 18, 452, 180, 38)
        self.draw_action_button(self.sky_notes_button, "STAR INFO  I", False)
        self.draw_action_button(self.result_brief_button, "MISSION BRIEF  B", False)
        self.result_buttons["retry"] = pygame.Rect(WIDTH // 2 - 210, 514, 196, 48)
        self.result_buttons["next"] = pygame.Rect(WIDTH // 2 + 14, 514, 196, 48)
        self.draw_action_button(self.result_buttons["retry"], "RETRY SECTOR", False)
        next_label = "REPLAY CAMPAIGN" if success and final_sector else "NEXT WORLD  >"
        self.draw_action_button(self.result_buttons["next"], next_label, True)

    def _draw_ghost_replay(self, elapsed):
        """Replay Kruskal as a faint route over the finished player network."""
        replay_count = min(len(self.state.mst_edges), int(elapsed * len(self.state.mst_edges) / 3.0) + 1)
        replay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        selected_pairs = {(min(u, v), max(u, v)) for u, v, _ in self.state.selected_edges}
        for u, v, _ in self.state.mst_edges[:replay_count]:
            a, b = self.state.stars[u], self.state.stars[v]
            color = (85, 236, 220, 150) if (min(u, v), max(u, v)) in selected_pairs else (125, 208, 255, 190)
            pygame.draw.line(replay, color, (int(a.x), int(a.y)), (int(b.x), int(b.y)), 5)
        for u, v, _ in self.state.selected_edges:
            if (min(u, v), max(u, v)) not in self.state.mst_pairs:
                a, b = self.state.stars[u], self.state.stars[v]
                pygame.draw.line(replay, (255, 174, 83, 190), (int(a.x), int(a.y)), (int(b.x), int(b.y)), 5)
        screen.blit(replay, (0, 0))
        label_text = "TIMED PLAN GHOST" if self.state.has_timed_edges else "KRUSKAL GHOST"
        label = SMALL.render(f"{label_text}  |  CYAN: optimal route  |  AMBER: alternate link", True, (205, 235, 250))
        card = label.get_rect(center=(WIDTH // 2, 88)).inflate(24, 12)
        glass_panel(screen, card, (5, 16, 34, 230), (73, 178, 220), 8)
        screen.blit(label, label.get_rect(center=card.center))

    def _draw_sky_notes(self):
        """Show real star facts and a chart made from catalog sky positions."""
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((1, 4, 15, 232))
        screen.blit(veil, (0, 0))
        note_box = pygame.Rect(95, 64, 910, 592)
        glass_panel(screen, note_box, (5, 15, 35, 252), (88, 184, 227), 20)

        pattern = PATTERNS[WORLD_PATTERN[self.state.world_id]]
        heading = TITLE.render("STAR INFORMATION", True, (229, 246, 255))
        screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 100)))
        left_x, right_x = 125, 575
        screen.blit(MEDIUM.render("STARS IN THIS SECTOR", True, (121, 204, 239)), (left_x, 145))
        screen.blit(MEDIUM.render("ACTUAL SKY PATTERN", True, (121, 204, 239)), (right_x, 145))
        pygame.draw.line(screen, (36, 67, 91), (left_x, 171), (535, 171), 1)
        pygame.draw.line(screen, (36, 67, 91), (right_x, 171), (975, 171), 1)

        # Give each game star its real position in the named sky pattern.
        row_gap = min(43, 365 / max(1, len(self.state.star_list)))
        for index, star in enumerate(self.state.star_list):
            y = round(185 + index * row_gap)
            color = self.hud._star_color(star.name)
            pygame.draw.circle(screen, color, (left_x + 7, y + 8), 5)
            name = self.hud.fit_text(star.name, FONT, 330)
            screen.blit(FONT.render(name, True, (218, 228, 238)), (left_x + 22, y - 1))
            fact = pattern["facts"].get(star.name, f"A named star in {pattern['name']}")
            fact = self.hud.fit_text(fact, SMALL, 390)
            screen.blit(SMALL.render(fact, True, (145, 169, 190)), (left_x + 22, y + 19))

        # Project J2000 right ascension and declination into a north-up sky chart.
        chart = pygame.Rect(right_x + 10, 235, 380, 285)
        chart_stars = pattern["stars"]
        coordinates = list(chart_stars.values())
        mean_dec = math.radians(sum(dec for _ra, dec in coordinates) / len(coordinates))
        projected_x = {name: ra * 15 * math.cos(mean_dec) for name, (ra, _dec) in chart_stars.items()}
        min_x, max_x = min(projected_x.values()), max(projected_x.values())
        min_y = min(dec for _ra, dec in coordinates)
        max_y = max(dec for _ra, dec in coordinates)
        pad = 28
        span_x = max(0.01, max_x - min_x)
        span_y = max(0.01, max_y - min_y)
        scale = min((chart.width - pad * 2) / span_x, (chart.height - pad * 2) / span_y)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        def chart_point(name):
            ra, dec = chart_stars[name]
            # Star charts put east on the left, so right ascension runs backwards.
            x = chart.centerx - (projected_x[name] - center_x) * scale
            y = chart.centery - (dec - center_y) * scale
            return round(x), round(y)

        for first, second in pattern["lines"]:
            if first in chart_stars and second in chart_stars:
                pygame.draw.line(screen, (104, 137, 164), chart_point(first), chart_point(second), 2)

        active_names = {star.name for star in self.state.star_list}
        used_labels = []
        for name in chart_stars:
            point = chart_point(name)
            active = name in active_names
            dot_color = self.hud._star_color(name) if active else (111, 132, 151)
            pygame.draw.circle(screen, (8, 16, 31), point, 8 if active else 6)
            pygame.draw.circle(screen, dot_color, point, 5 if active else 3)

            if not active:
                continue
            label = SMALL.render(name, True, (196, 210, 222))
            candidates = [
                label.get_rect(topleft=(point[0] + 8, point[1] - 8)),
                label.get_rect(topright=(point[0] - 8, point[1] - 8)),
                label.get_rect(midtop=(point[0], point[1] + 8)),
                label.get_rect(midbottom=(point[0], point[1] - 8)),
            ]
            label_rect = next((candidate for candidate in candidates
                               if chart.contains(candidate) and not any(candidate.colliderect(old) for old in used_labels)), None)
            if label_rect:
                used_labels.append(label_rect)
                screen.blit(label, label_rect)

        pattern_name = MEDIUM.render(pattern["name"], True, (220, 230, 239))
        screen.blit(pattern_name, pattern_name.get_rect(center=(chart.centerx, 190)))
        pattern_kind = self.hud.fit_text(pattern["kind"], SMALL, chart.width)
        kind_image = SMALL.render(pattern_kind, True, (153, 177, 196))
        screen.blit(kind_image, kind_image.get_rect(center=(chart.centerx, 210)))
        description = self.hud.fit_text(pattern["description"], SMALL, chart.width)
        desc_image = SMALL.render(description, True, (145, 169, 190))
        screen.blit(desc_image, desc_image.get_rect(center=(chart.centerx, 545)))
        chart_note = self.hud.fit_text("Real sky positions (J2000); puzzle board positions are schematic.", SMALL, chart.width)
        note_image = SMALL.render(chart_note, True, (114, 143, 166))
        screen.blit(note_image, note_image.get_rect(center=(chart.centerx, 566)))

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
            "Corridor weights are base energy costs. Stay within the sector reserve.",
        ]
        if self.state.has_timed_edges:
            rules.append("Every move advances the collapse timer: dashed amber links expire after countdown.")
            rules.append("Essential links vs tempting shortcuts: plan your move sequence to preserve connectivity.")
        else:
            rules.append("Kruskal's algorithm finds the minimum-cost spanning tree; consecutive optimal picks build resonance.")
        for i, line in enumerate(rules):
            y = objective_y + 27 + i * 18
            screen.blit(SMALL.render(self.hud.fit_text(line, SMALL, 680), True, (155, 190, 214)), (220, y))
        self.draw_action_button(pygame.Rect(WIDTH // 2 - 84, 566, 168, 40), "RETURN TO SECTOR", True)

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
                        if self.show_intro_rules:
                            self.show_intro_rules = False
                        elif self.play_button.collidepoint(event.pos):
                            self.show_intro = False
                        elif self.how_to_button.collidepoint(event.pos):
                            self.show_intro_rules = True
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
                            blocked_panels = [pygame.Rect(920, 92, 164, 520)]
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
                        if self.show_intro_rules:
                            continue
                        if event.key == pygame.K_TAB:
                            self.intro_focus_how = not self.intro_focus_how
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.intro_focus_how:
                                self.show_intro_rules = True
                            else:
                                self.show_intro = False
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
                    elif event.key == pygame.K_h:
                        self.activate_button("hint")
                    elif event.key == pygame.K_n:
                        self.activate_button("next")
                    elif event.key == pygame.K_r:
                        self.activate_button("reset")
            self.update(dt)
            self.draw(dt)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameApp().run()
