import pygame
import sys
import math
from visual.starfield import ParallaxStarfield
from engine.level_loader import load_level_from_json
from engine.game_state import GameState
from engine.sound_engine import SoundEngine
from dsa.mst import kruskal_steps

pygame.init()
WIDTH, HEIGHT = 1100, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("StarLink - Constellation Weaver")
clock = pygame.time.Clock()

font_ui = pygame.font.SysFont("Trebuchet MS", 16)
font_bold = pygame.font.SysFont("Trebuchet MS", 18, bold=True)
font_title = pygame.font.SysFont("Trebuchet MS", 26, bold=True)

class GameApp:
    def __init__(self):
        self.starfield = ParallaxStarfield(WIDTH, HEIGHT)
        self.sound = SoundEngine(enabled=True)
        self.world_files = ["levels/world1.json", "levels/world2.json", "levels/world3.json"]
        self.world_idx = 0
        self.load_world(self.world_idx)

    def load_world(self, idx):
        data = load_level_from_json(self.world_files[idx])
        self.state = GameState(data)
        self.selected_star = None
        self.flash_cycle = None
        self.flash_timer = 0.0
        self.win_sound_played = False

        # Kruskal generator state
        self.stepper_gen = None
        self.stepper_timer = 0.0
        self.stepper_edges = []
        self.stepper_active = False

    def handle_star_click(self, star_id):
        if self.selected_star is None:
            self.selected_star = star_id
            self.state.status_message = f"Selected Star {star_id}. Choose an adjacent corridor."
        else:
            if self.selected_star != star_id:
                u, v = self.selected_star, star_id
                ok, msg = self.state.connect_edge(u, v)
                if not ok:
                    if self.state.cycle_edge_flash:
                        self.flash_cycle = self.state.cycle_edge_flash
                        self.flash_timer = 0.7
                        self.sound.play("cycle")
                else:
                    self.sound.play("link")
            self.selected_star = None

    def trigger_kruskal_stepper(self):
        v_ids = list(self.state.stars.keys())
        self.stepper_gen = kruskal_steps(v_ids, self.state.edges)
        self.stepper_edges = []
        self.stepper_active = True
        self.stepper_timer = 0.0

    def update(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_cycle = None

        # Check win condition audio trigger
        if self.state.is_completed and not self.win_sound_played:
            self.sound.play("win")
            self.win_sound_played = True

        # Kruskal Stepper progression (~400 ms interval)
        if self.stepper_active and self.stepper_gen:
            self.stepper_timer += dt
            if self.stepper_timer >= 0.4:
                self.stepper_timer = 0.0
                try:
                    step = next(self.stepper_gen)
                    self.stepper_edges.append(step)
                    u, v, w, accepted, reason = step
                    status = "ACCEPTED" if accepted else "REJECTED"
                    self.state.status_message = f"Kruskal Step: Edge ({u}-{v}, w={w}) -> {status}: {reason}"
                    if accepted:
                        self.sound.play("link")
                    else:
                        self.sound.play("cycle")
                except StopIteration:
                    self.stepper_active = False
                    self.stepper_gen = None

    def draw(self, dt):
        self.starfield.update_and_draw(screen, dt)
        now_sec = pygame.time.get_ticks() / 1000.0

        # Draw Candidate Edges
        for u, v, base_cost in self.state.edges:
            s1 = self.state.stars[u]
            s2 = self.state.stars[v]
            color = (50, 70, 110)
            width = 1

            # Connected edge
            if any((e[0] == min(u, v) and e[1] == max(u, v)) for e in self.state.selected_edges):
                color = (70, 240, 200)
                width = 3

            # Cycle rejection red flash
            if self.flash_cycle and (self.flash_cycle == (min(u, v), max(u, v))):
                color = (255, 45, 45)
                width = 4

            pygame.draw.line(screen, color, (s1.x, s1.y), (s2.x, s2.y), width)
            
            # Show edge cost
            cost = self.state.compute_edge_cost(u, v, base_cost)
            cost_str = str(cost) if cost == base_cost else f"{cost}*"
            mid = ((s1.x + s2.x) // 2, (s1.y + s2.y) // 2)
            lbl = font_ui.render(cost_str, True, (180, 200, 230))
            screen.blit(lbl, mid)

        # Draw Kruskal Stepper Overlay
        for step in self.stepper_edges:
            u, v, _, accepted, _ = step
            s1, s2 = self.state.stars[u], self.state.stars[v]
            step_color = (255, 215, 0) if accepted else (255, 50, 50)
            pygame.draw.line(screen, step_color, (s1.x, s1.y), (s2.x, s2.y), 3 if accepted else 2)

        # Draw Stars
        pulse = math.sin(now_sec * 4.0) * 2.0
        for s in self.state.star_list:
            color = (255, 255, 255)
            if s.type == "ENERGY": color = (80, 245, 120)
            elif s.type == "POWER": color = (255, 215, 60)
            elif s.type == "UNSTABLE": color = (220, 80, 240)

            # Highlight selected star
            if self.selected_star == s.id:
                pygame.draw.circle(screen, (255, 255, 100), (s.x, s.y), int(18 + pulse), 2)

            pygame.draw.circle(screen, (*color, 50), (s.x, s.y), int(12 + pulse))
            pygame.draw.circle(screen, color, (s.x, s.y), 7)
            label = font_bold.render(f"{s.name}", True, (240, 240, 255))
            screen.blit(label, (s.x + 12, s.y - 10))

        # HUD: Title & Energy Bar
        title_txt = f"WORLD {self.state.world_id}: {self.state.name}"
        screen.blit(font_title.render(title_txt, True, (240, 240, 255)), (30, 20))

        pct = max(0.0, self.state.energy / self.state.max_energy)
        bar_color = (60, 220, 240) if pct > 0.4 else ((240, 180, 50) if pct > 0.2 else (240, 60, 60))
        pygame.draw.rect(screen, (35, 45, 65), (30, 60, 220, 18), border_radius=4)
        pygame.draw.rect(screen, bar_color, (30, 60, int(220 * pct), 18), border_radius=4)
        screen.blit(font_bold.render(f"ENERGY: {self.state.energy}/{self.state.max_energy}", True, (255, 255, 255)), (265, 60))

        # Status text
        pygame.draw.rect(screen, (20, 26, 45), (30, 90, 840, 26), border_radius=4)
        screen.blit(font_ui.render(self.state.status_message, True, (200, 225, 255)), (38, 93))

        # Controls & Audio Indicator
        audio_state = "ON" if self.sound.enabled else "OFF"
        controls = f"Z: Undo | Y: Redo | K: Kruskal Solver | N: Next World | R: Reset | M: Audio ({audio_state})"
        screen.blit(font_ui.render(controls, True, (150, 170, 200)), (30, 680))

        # Victory Modal Overlay
        if self.state.is_completed:
            self._draw_victory_modal()

    def _draw_victory_modal(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 25, 210))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect(WIDTH // 2 - 240, HEIGHT // 2 - 140, 480, 280)
        pygame.draw.rect(screen, (22, 30, 55), box, border_radius=12)
        pygame.draw.rect(screen, (100, 140, 220), box, 2, border_radius=12)

        t1 = font_title.render("CONSTELLATION RESTORED!", True, (255, 230, 100))
        screen.blit(t1, t1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

        stars_str = "★ " * self.state.earned_stars + "☆ " * (3 - self.state.earned_stars)
        t_stars = font_title.render(stars_str.strip(), True, (255, 215, 0))
        screen.blit(t_stars, t_stars.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25)))

        cost = sum(c for _, _, c in self.state.selected_edges)
        t2 = font_ui.render(f"Your Energy: {cost} | Optimal MST Cost: {self.state.optimal_cost}", True, (200, 220, 255))
        screen.blit(t2, t2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

        t3 = font_bold.render("Press 'N' for Next Sector | 'R' to Replay", True, (120, 255, 180))
        screen.blit(t3, t3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))

    def run(self):
        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for s in self.state.star_list:
                        if math.hypot(event.pos[0] - s.x, event.pos[1] - s.y) <= 18:
                            self.handle_star_click(s.id)
                            break

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.state.undo()
                        self.sound.play("undo")
                    elif event.key == pygame.K_y:
                        self.state.redo()
                        self.sound.play("undo")
                    elif event.key == pygame.K_k:
                        self.trigger_kruskal_stepper()
                    elif event.key == pygame.K_n:
                        self.world_idx = (self.world_idx + 1) % len(self.world_files)
                        self.load_world(self.world_idx)
                    elif event.key == pygame.K_r:
                        self.load_world(self.world_idx)
                    elif event.key == pygame.K_m:
                        self.sound.enabled = not self.sound.enabled
                        st = "Active" if self.sound.enabled else "Muted"
                        self.state.status_message = f"Audio System {st}"

            self.update(dt)
            self.draw(dt)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = GameApp()
    app.run()