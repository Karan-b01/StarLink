import pygame

class KruskalAnimator:
    """Animates Kruskal's algorithm step-by-step for evaluators."""
    def __init__(self, solver_history, star_lookup):
        self.history = solver_history
        self.stars = star_lookup
        self.current_step = 0
        self.is_active = False
        self.last_step_time = 0
        self.step_delay_ms = 700  # Interval between algorithm choices

    def start(self):
        self.current_step = 0
        self.is_active = True
        self.last_step_time = pygame.time.get_ticks()

    def stop(self):
        self.is_active = False

    def update(self):
        if not self.is_active or self.current_step >= len(self.history):
            return
        now = pygame.time.get_ticks()
        if now - self.last_step_time >= self.step_delay_ms:
            self.current_step += 1
            self.last_step_time = now

    def draw(self, surface, font):
        if not self.is_active:
            return

        for idx in range(min(self.current_step, len(self.history))):
            step = self.history[idx]
            u, v, _ = step['edge']
            p1 = (self.stars[u].x, self.stars[u].y)
            p2 = (self.stars[v].x, self.stars[v].y)

            if step['action'] == 'ACCEPT':
                pygame.draw.line(surface, (255, 215, 0), p1, p2, 4)  # Gold
            elif step['action'] == 'REJECT':
                pygame.draw.line(surface, (255, 60, 60), p1, p2, 2)   # Red rejection

        # Show current algorithm explanation at top center
        if 0 < self.current_step <= len(self.history):
            curr = self.history[self.current_step - 1]
            u, v, w = curr['edge']
            txt = f"Kruskal Step {self.current_step}/{len(self.history)}: Edge ({u}-{v}, w={w}) -> {curr['action']} ({curr['reason']})"
            lbl = font.render(txt, True, (255, 240, 100))
            pygame.draw.rect(surface, (20, 25, 45), (180, 50, 740, 28), border_radius=4)
            surface.blit(lbl, (200, 54))